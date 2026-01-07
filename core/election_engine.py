
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from .vectorized_ephemeris import VectorizedEphemeris
from .vectorized_logic import VectorizedLogic
from .vectorized_houses import VectorizedHouses
from .vectorized_natal import VectorizedNatal
from .astro_config import AstroConfig
from .theme_config import get_theme_config, THEMES

# Configurar logging
logger = logging.getLogger(__name__)

class VectorizedElectionFinder:
    """
    Motor de Búsqueda Vectorizado Integrado V2.
    Combina Ephemeris + Houses + Natal + Logic + Config.
    """
    
    def __init__(self):
        self.ephemeris = VectorizedEphemeris()
        self.logic = VectorizedLogic()
        self.houses = VectorizedHouses()
        self.natal = VectorizedNatal()
        
        # Instantiate Scorer (Lazy dependency or here)
        from .vectorized_scoring import VectorizedScoring
        self.scorer = VectorizedScoring(self.logic)
        
    def find_elections(self, 
                      start_dt: datetime, 
                      end_dt: datetime, 
                      lat: float,
                      lon: float,
                      natal_chart: Dict[int, float] = None,
                      topic: str = "trabajo",
                      interval_minutes: int = 60,
                      return_all: bool = False) -> pd.DataFrame:
        """
        Busca fechas electivas en un rango dado.
        
        Args:
            start_dt: Inicio búsqueda
            end_dt: Fin búsqueda
            lat: Latitud geográfica
            lon: Longitud geográfica
            natal_chart: Dict {planet_id: longitude} (Opcional)
            topic: Tema (trabajo, amor, etc.)
            interval_minutes: Intervalo de muestreo (default 30 min)
            
        Returns:
            DataFrame con candidatos filtados y categorizados.
        """
        if natal_chart is None: 
            natal_chart = {}
            
        logger.info(f"🔎 Iniciando búsqueda V2: {start_dt} a {end_dt} | Tema: {topic}")
        
        # 0. Configuración del Tema
        config = get_theme_config(topic)
        
        # 1. Generar grilla de tiempo (Time Grid)
        total_time = end_dt - start_dt
        total_intervals = int(total_time.total_seconds() / (interval_minutes * 60))
        timestamps = [start_dt + timedelta(minutes=i*interval_minutes) for i in range(total_intervals)]
        times_arr = np.array(timestamps)
        
        logger.info(f"⚡ Analizando {len(times_arr)} momentos...")
        
        # 2. Calcular Posiciones (Fase Física)
        bodies = [0, 1, 2, 3, 4, 5, 6, 10] # 10=MeanNode
        positions = self.ephemeris.calculate_positions(times_arr, bodies)
        longitudes = self.ephemeris.get_longitudes(positions)
        speeds = self.ephemeris.get_speeds(positions)
        
        # 3. Calcular Casas y Regencias (Toposcopía)
        cusps, ascmc = self.houses.calculate_houses(times_arr, lat, lon)
        
        # 4. Fase Lógica - Filtros Universales (Luna)
        moon_longs = longitudes[1]
        sun_longs = longitudes[0]
        
        # A. Luna Dignidad (Cap/Esc)
        mask_moon_sign = self.logic.mask_signs(moon_longs, [7, 9]) # 7=Scorpio, 9=Capricorn
        
        # B. Fase Lunar
        mask_phase = self.logic.mask_phase(sun_longs, moon_longs, orb=AstroConfig.ORB_MOON_PHASE)
        # B2. No Eclipses (Luna Nueva/Llena cerca de Nodos) - TODO
        
        # C. Vacío de Curso
        mask_voc = self.logic.mask_void_of_course(times_arr, moon_longs, longitudes)
        
        # Combinar Rechazos Lunares
        is_bad_moon = mask_moon_sign | mask_phase | mask_voc
        
        # 5. Fase Lógica - Filtros Temáticos (Regente del Tema)
        # Ejemplo: Trabajo -> Casa 10
        target_house = config['target_house'] # 1-12
        
        # Cúspide de la Casa X (indices 0-11, house 10 -> index 9)
        cusp_longs = cusps[:, target_house - 1]
        
        # Signo de esa Cúspide
        cusp_signs = self.logic.get_sign_indices(cusp_longs)
        
        # Regente de ese Signo
        # Esto es más complejo vectorialmente porque cada momento puede tener diferente regente.
        # Solución: Iterar sobre los 12 signos posibles.
        
        is_bad_ruler = np.zeros(len(times_arr), dtype=bool)
        
        for sign_idx in range(12):
            # Máscara de momentos donde la cúspide cae en este signo
            mask_times = (cusp_signs == sign_idx)
            if not np.any(mask_times): continue
            
            # Quién rige este signo?
            ruler_id = self.logic.get_ruler_for_sign(sign_idx)
            
            # Longitud y Velocidad de ese regente
            ruler_longs = longitudes[ruler_id][mask_times]
            ruler_speeds_local = speeds[ruler_id][mask_times]
            
            # Chequear Debilidad (Exilio/Caída)
            debility_local = self.logic.mask_debility(ruler_id, ruler_longs)
            
            # Chequear Retrogradación (Velocidad < 0)
            # Rule: "el regente del ASC esta retrogrado -> No apto" (and H10 rules too)
            retro_local = (ruler_speeds_local < 0)
            
            # Asignar resultado (Debilidad OR Retrogradación)
            is_bad_ruler[mask_times] = debility_local | retro_local
            
        # 6. Fase Lógica - Filtros Natales (Enraizamiento)
        is_bad_natal = np.zeros(len(times_arr), dtype=bool)
        
        # RULE 29: Malefics on Angles (Electional Rule "Carta Enraizada")
        # Check if Transit Mars(4) or Saturn(6) are on Asc/Dsc/Mc/Ic
        # Asc is cusps[0], MC is cusps[9] (actually MC is passed separately in ascmc tuple if needed, 
        # but VectorizedHouses returns cusps and ascmc separately.
        # Let's assume ascmc_arr contains [Asc, MC].
        
        # Get Angles
        asc_arr = ascmc[:, 0]
        mc_arr = ascmc[:, 1]
        dsc_arr = (asc_arr + 180) % 360
        ic_arr = (mc_arr + 180) % 360
        
        angles = [asc_arr, mc_arr, dsc_arr, ic_arr]
        malefics = [4, 6] # Mars, Saturn
        orb_angle = 5.0
        
        is_malefic_on_angle = np.zeros(len(times_arr), dtype=bool)
        
        for malefic_id in malefics:
            malefic_pos = longitudes[malefic_id]
            for angle in angles:
                # Check conjunction
                diff = np.abs(malefic_pos - angle)
                diff = np.minimum(diff, 360 - diff)
                mask_conj = diff <= orb_angle
                is_malefic_on_angle |= mask_conj
                
        # This is strictly part of "Enraizamiento" section in CSV, likely meaning "The Rooted Chart Rules"
        # We add it to the 'rejected' mask
        
        if natal_chart is not None:
             # ENRAIZAMIENTO (NATAL)
             # Legacy Parity: The legacy engine only checks Ascendant overlays, 
             # NOT transits to natal lights. 
             # To strictly respect "Original Logic", we disable this check by default.
             # mask_natal = self.natal.mask_hard_aspects_to_natal_lights(longitudes, natal_chart)
             
             # If we want to strictly follow legacy, we assume True (All valid regarding transits)
             # unless we implement the specific "Ascendant on Malefic" check which Legacy does.
             # For now, we allow the candidate to pass this filter.
             is_bad_natal = np.zeros(len(times_arr), dtype=bool) # All False (No hard aspects detected/blocked)
             
        # 7. Combinar Todos los Filtros
        is_rejected = is_bad_moon | is_bad_ruler | is_bad_natal | is_malefic_on_angle
        is_valid = ~is_rejected
        
        # 8. Construir Resultados
        valid_indices = np.where(is_valid)[0]
        
        logger.info(f"✨ Encontrados {len(valid_indices)} momentos candidatos ({len(valid_indices)/len(times_arr)*100:.1f}%)")
        
        # --- 8. SCORING VECTORIZADO ---
        # Calculamos score para TODOS los momentos (vectorización es eficiente)
        # O solo para válidos para ahorrar? Pero necesito masking.
        # Mejor calcular para todos y luego filtrar.
        
        # A. Preparar datos de Rulers (IDs y Longitudes)
        # Necesitamos arrays (N,) para IDs y Posiciones de Regente ASC y H10
        
        ruler_asc_ids = np.zeros(len(times_arr), dtype=int)
        ruler_asc_longs = np.zeros(len(times_arr), dtype=float)
        ruler_asc_speeds = np.zeros(len(times_arr), dtype=float)
        
        # Obtener Signos Asc
        asc_signs = self.logic.get_sign_indices(asc_arr)
        
        # Populate arrays
        for sign_idx in range(12):
            mask = (asc_signs == sign_idx)
            if not np.any(mask): continue
            pid = self.logic.get_ruler_for_sign(sign_idx)
            ruler_asc_ids[mask] = pid
            ruler_asc_longs[mask] = longitudes[pid][mask]
            ruler_asc_speeds[mask] = speeds[pid][mask]
            
        # Same for H10
        # Wait, I already calculated 'cusp_signs' (H10 sign) at lines 99
        # 'cusp_signs' corresponds to target_house (H10 default)
        ruler_h10_ids = np.zeros(len(times_arr), dtype=int)
        ruler_h10_longs = np.zeros(len(times_arr), dtype=float)
        ruler_h10_speeds = np.zeros(len(times_arr), dtype=float)
        
        for sign_idx in range(12):
            mask = (cusp_signs == sign_idx)
            if not np.any(mask): continue
            pid = self.logic.get_ruler_for_sign(sign_idx)
            ruler_h10_ids[mask] = pid
            ruler_h10_longs[mask] = longitudes[pid][mask]
            ruler_h10_speeds[mask] = speeds[pid][mask]

        # Necesitamos Planet Longs como Dict para el Scorer
        planet_longs_dict = {pid: longitudes[pid] for pid in bodies}
        
        # B. Calcular Scores
        
        # 1. MOON SCORE
        score_moon, details_moon = self.scorer.calculate_moon_score(
            times_arr, moon_longs, sun_longs, planet_longs_dict, cusps, ascmc
        )
        
        # 2. RULER ASC SCORE
        score_r_asc, details_r_asc = self.scorer.calculate_ruler_score(
            times_arr, 'ASC', ruler_asc_longs, ruler_asc_ids, sun_longs, planet_longs_dict, cusps, ruler_asc_speeds
        )
        
        # 3. RULER H10 SCORE
        score_r_h10, details_r_h10 = self.scorer.calculate_ruler_score(
            times_arr, 'H10', ruler_h10_longs, ruler_h10_ids, sun_longs, planet_longs_dict, cusps, ruler_h10_speeds
        )

        # 4. NATAL SCORE (Enraizamiento)
        score_natal, details_natal = self.scorer.calculate_natal_score(
            times_arr, ascmc, cusps, natal_chart
        )

        # 5. COMBINATIONS SCORE (Pos/Neg - Arquetipos)
        # Try to infer Natal ASC Sign from natal_chart if stored (e.g. key 'asc' or 15)
        # For this context, we might not have it unless passed.
        # Assuming safe default (None -> Apply strict penalties).
        natal_asc_sign = None 
        # Ideally we should get this from input, but let's check if key 100 or similar exists?
        # No convention yet.
        
        score_comb, details_comb = self.scorer.calculate_combinations_score(
             times_arr,
             ruler_asc_ids, ruler_asc_longs,
             ruler_h10_ids, ruler_h10_longs,
             planet_longs_dict,
             ascmc, cusps,
             natal_asc_sign
        )
        
        # TOTAL SCORE
        total_score = score_moon + score_r_asc + score_r_h10 + score_natal + score_comb
        
        # 9. Construir Resultados
        # 9. Construir Resultados COMPLETOS (Pos/Neg/Net)
        # -------------------------------------------------------------
        # Aggregate all component details for UX
        # -------------------------------------------------------------
        
        # Merge all details dictionaries
        all_details = {**details_moon, **details_r_asc, **details_r_h10, **details_natal, **details_comb}
        
        # Calculate Aggregated Positive and Negative Scores Vectorially
        # This is strictly for UX visualization (Green Bars vs Red Bars)
        # score_positive = Sum of all components > 0
        # score_negative = Sum of all components < 0
        
        score_positive = np.zeros(len(times_arr))
        score_negative = np.zeros(len(times_arr))
        
        for key, arr in all_details.items():
            score_positive += np.maximum(arr, 0.0)
            score_negative += np.minimum(arr, 0.0)
            
        # Re-verify total score consistency (Optional but good for sanity)
        # total_check = score_positive + score_negative
        # assert np.allclose(total_score, total_check), "Score mismatch!"

        if return_all:
             indices_to_process = np.arange(len(times_arr))
        else:
             indices_to_process = np.where(~is_rejected)[0]
             
        results = []
        for idx in indices_to_process:
            # If not return_all (strict) and rejected, we skip (handled by indices_to_process)
            # If return_all=True, we process everyone.
            
            is_valid_moment = not is_rejected[idx]
            
            t = times_arr[idx]
            moon_sign_idx = int(moon_longs[idx] // 30)
            
            # Extract components for this specific moment (for Tooltip)
            # We filter only non-zero components to save bandwidth
            components = {}
            for k, v in all_details.items():
                val = v[idx]
                if abs(val) > 0.001:
                    components[k] = val
                    
            # -------------------------------------------------------------
            # UX Normalization (70% Heaven / 30% Natal)
            # -------------------------------------------------------------
            
            # 1. Separate Scores
            s_natal = score_natal[idx]
            s_general = total_score[idx] - s_natal # "Heaven" Score
            
            # 2. Independent Normalization
            # General Max ~30 pts (Excellent)
            # Natal Max ~10 pts (Perfect Link)
            MAX_GEN = 30.0
            MAX_NAT = 10.0
            
            norm_gen = (s_general / MAX_GEN) * 100.0
            norm_gen = min(max(norm_gen, 0.0), 100.0)
            
            norm_nat = (s_natal / MAX_NAT) * 100.0
            norm_nat = min(max(norm_nat, 0.0), 100.0)
            
            # 3. Hybrid Weighted Score
            # Client Request: 70% Heaven, 30% Personal
            score_hybrid = (norm_gen * 0.70) + (norm_nat * 0.30)
            
            # 4. Semantic Labeling (Based on Hybrid)
            if score_hybrid >= 80:
                label = "Excelente"
                stars = 5
            elif score_hybrid >= 60:
                label = "Muy Bueno"
                stars = 4
            elif score_hybrid >= 40:
                label = "Bueno"
                stars = 3
            elif score_hybrid >= 20:
                label = "Regular"
                stars = 2
            else:
                label = "Pobre"
                stars = 1
            
            # Collect Rejection Flags (if any)
            flags = []
            if not is_valid_moment:
                 flags.append("rejected")
                 # We could add detailed reasons if we stored separate masks
                 # e.g. "moon_voc", "saturn_on_angle".
                 # For now, generic rejected.
            
            results.append({
                "timestamp": t,
                "is_valid": bool(is_valid_moment),
                "flags": flags,
                "moon_sign": moon_sign_idx,
                
                # Raw Data (for Debug/Graphs)
                "score_total": total_score[idx], # Legacy Total
                "score_general": s_general,      # Heaven Only
                "score_natal": s_natal,          # Earth Only
                
                "score_positive": score_positive[idx],
                "score_negative": score_negative[idx],
                
                # User Facing Data (for UI Cards)
                "score_normalized": round(score_hybrid, 1), # The Big Number (0-100)
                "norm_general": round(norm_gen, 1),         # Sub-bar 1 (0-100)
                "norm_natal": round(norm_nat, 1),           # Sub-bar 2 (0-100)
                
                "label": label,
                "stars": stars,
                
                # Breakdown for Tooltip
                "score_moon": score_moon[idx],
                "score_r_asc": score_r_asc[idx],
                "score_r_h10": score_r_h10[idx],
                # score_natal is already above
                "score_comb": score_comb[idx],
                "components": components 
            })
            
        return pd.DataFrame(results)
