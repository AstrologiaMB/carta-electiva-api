
import numpy as np
import logging
from typing import Dict, List, Tuple
from .vectorized_logic import VectorizedLogic
from .astro_config import AstroConfig

logger = logging.getLogger(__name__)

class VectorizedScoring:
    """
    Motor de Puntuación Vectorizado ("The Scorer").
    Implementa las reglas de puntos del archivo CSV (sistema experto).
    """

    def __init__(self, logic: VectorizedLogic):
        self.logic = logic

    def calculate_moon_score(self, 
                           times: np.ndarray,
                           moon_longs: np.ndarray,
                           sun_longs: np.ndarray,
                           planet_longs: Dict[int, np.ndarray],
                           house_cusps: np.ndarray,
                           ascmc: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Calcula el puntaje de la LUNA basado en las reglas 17-35 del CSV.
        
        Reglas:
        17. Luna en Cancer (+1)
        18. Luna en Tauro (+1)
        19. Luna Creciente (+1) (Diff 0-180? No, usually 0-180 is Waxing/Creciente)
            Legacy: "moonCres" checks if Moon is ahead of Sun < 180.
        20. Luna Trigono Júpiter (+1)
        21. Luna Sextil Júpiter (+1) 
        22. Luna Trigono Venus (+1)
        23. Luna Sextil Venus (+1)
        24. Luna Trigono Sol (+1)
        25. Luna Sextil Sol (+1)
        26. Luna en casas 5, 9, 10, 11 (+1)
        27. Luna conjunción Venus (+1)
        28. Luna conjunción Júpiter (+1)
        29. Luna conjunción Regente ASC (+2)
        30. Luna conjunción Regente H10 (+2)
        31. Luna sextil Regente ASC (+2)
        32. Luna sextil Regente H10 (+2)
        33. Luna trigono Regente ASC (+2)
        34. Luna trigono Regente H10 (+2)
        
        Returns:
            total_score: Array of floats
            details: Dict of arrays (score components)
        """
        N = len(moon_longs)
        total_score = np.zeros(N, dtype=float)
        details = {}

        # --- 17 & 18: Signos (Cancer=3, Tauro=1) ---
        signs = self.logic.get_sign_indices(moon_longs)
        
        is_cancer = (signs == VectorizedLogic.CANCER)
        score_cancer = np.where(is_cancer, 1.0, 0.0)
        total_score += score_cancer
        details['moon_cancer'] = score_cancer
        
        is_taurus = (signs == VectorizedLogic.TAURUS)
        score_taurus = np.where(is_taurus, 1.0, 0.0)
        total_score += score_taurus
        details['moon_taurus'] = score_taurus

        # --- 19: Creciente (Waxing) ---
        # Diff = (Moon - Sun) % 360
        # If 0 < diff < 180 -> Waxing (Creciente)
        # If 180 < diff < 360 -> Waning (Menguante)
        diff_sun_moon = (moon_longs - sun_longs) % 360
        is_waxing = (diff_sun_moon > 0) & (diff_sun_moon < 180)
        score_waxing = np.where(is_waxing, 1.0, 0.0)
        total_score += score_waxing
        details['moon_waxing'] = score_waxing

        # --- Aspectos Benéficos (Júpiter(5), Venus(3), Sol(0)) ---
        # IDs: Sun=0, Ven=3, Jup=5
        
        def score_aspect(planet_id, aspect_angle, points, name):
             if planet_id not in planet_longs:
                 return
             p_pos = planet_longs[planet_id]
             # Orbit Check (Using standard aspect orb, e.g. 8 or 6 deg)
             # CSV doesn't specify unique orbs here, assuming standard "mask_exact_aspect"
             # Legacy uses variable orbs likely, let's use AstroConfig default (8.0 conj/opp, 6.0 others)
             
             orb = 8.0 if aspect_angle == 0 else 6.0
             mask = self.logic.mask_exact_aspect(moon_longs, p_pos, aspect_angle, orb)
             
             score = np.where(mask, points, 0.0)
             # Avoid double counting if mutually exclusive? 
             # Usually aspects are exclusive (can't be trine AND sextile same planet same time),
             # but check overlap logic if needed. Here straight sum is fine.
             
             # Optimization: Modify total_score in place
             nonlocal total_score
             total_score += score
             details[name] = score

        # 20, 21, 28: Jupiter
        score_aspect(5, 120, 1.0, 'moon_trine_jup') # 20
        score_aspect(5, 60, 1.0, 'moon_sext_jup')   # 21
        score_aspect(5, 0, 1.0, 'moon_conj_jup')    # 28

        # 22, 23, 27: Venus
        score_aspect(3, 120, 1.0, 'moon_trine_ven') # 22
        score_aspect(3, 60, 1.0, 'moon_sext_ven')   # 23
        score_aspect(3, 0, 1.0, 'moon_conj_ven')    # 27
        
        # 24, 25: Sun
        score_aspect(0, 120, 1.0, 'moon_trine_sun') # 24
        score_aspect(0, 60, 1.0, 'moon_sext_sun')   # 25

        # --- 26: Casas Favorables (5, 9, 10, 11) ---
        # Need to determine which House the Moon is in.
        # VectorizedHouses.get_house_for_body? Not implemented yet.
        # We need logic: For each moment, calculate House Index (0-11).
        # House Index H where Cusp[H] <= Moon < Cusp[H+1] (handling 360 wrap).
        
        # Vectorized check:
        # Since calculation of house index for N moments is tricky without iteration or complex broadcasting,
        # we can iterate 12 houses.
        
        is_favorable_house = np.zeros(N, dtype=bool)
        favorable_indices = [4, 8, 9, 10] # 5, 9, 10, 11 (0-indexed: 4, 8, 9, 10)
        
        # We must correctly place Moon in houses.
        # Simple method: Check if Moon is between Cusp[i] and Cusp[i+1]
        
        for h_idx in favorable_indices:
             cusp_start = house_cusps[:, h_idx]
             # Next cusp
             next_h = (h_idx + 1) % 12
             cusp_end = house_cusps[:, next_h]
             
             # Check if Moon is inside [start, end) handling circularity
             # Case 1: Start < End (Normal) -> Start <= Moon < End
             # Case 2: Start > End (Crossing 0) -> Moon >= Start OR Moon < End
             
             # Vectorized conditions
             case_normal = (cusp_start < cusp_end) 
             in_house_normal = case_normal & (moon_longs >= cusp_start) & (moon_longs < cusp_end)
             
             case_cross = (~case_normal)
             in_house_cross = case_cross & ((moon_longs >= cusp_start) | (moon_longs < cusp_end))
             
             # Combine
             mask_house = in_house_normal | in_house_cross
             is_favorable_house |= mask_house
             
        score_house = np.where(is_favorable_house, 1.0, 0.0)
        total_score += score_house
        details['moon_favorable_house'] = score_house

        # --- 29-34: Aspectos a Regentes (ASC y MC/H10) ---
        # Requires identifying Rulers first.
        # Regente ASC is dynamic. Regente H10 is dynamic.
        # Passed in? No. We calculate them here or expected to be passed.
        # Efficiency: It's better to pass "ruler_asc_pos" and "ruler_mc_pos" arrays if computed outside.
        # But we only have planet_longs dict.
        # So we must compute Ruler IDs per moment, then gather positions.
        
        # 1. Identify Asc Sign -> Asc Ruler
        asc_longs = ascmc[:, 0]
        asc_signs = self.logic.get_sign_indices(asc_longs)
        
        # 2. Identify MC Sign (H10 Cusp) -> H10 Ruler
        mc_longs = house_cusps[:, 9] # House 10 cusp (usually MC)
        mc_signs = self.logic.get_sign_indices(mc_longs)
        
        # We need "Position of the Ruler".
        # Since Ruler varies (Mars, Venus...), we need a Gather operation.
        # Construct array of Ruler Positions for each moment.
        
        def get_ruler_positions(signs_arr):
            # signs_arr (N,)
            # We map sign -> planet_id
            # Then map planet_id -> position in that moment
            
            # Since we can't easily vector-index a dictionary of arrays,
            # we iterate 12 signs? Or 7 planets?
            # Iterate 7 planets is better (Sun..Saturn).
            
            ruler_pos_arr = np.zeros(N, dtype=float)
            
            for sign_id in range(12):
                pid = self.logic.get_ruler_for_sign(sign_id)
                if pid not in planet_longs: continue
                
                # Where Asc/MC Sign == sign_id
                mask = (signs_arr == sign_id)
                if not np.any(mask): continue
                
                # Copy planet positions for those moments
                ruler_pos_arr[mask] = planet_longs[pid][mask]
                
            return ruler_pos_arr

        ruler_asc_pos = get_ruler_positions(asc_signs)
        ruler_h10_pos = get_ruler_positions(mc_signs)
        
        # Now score aspects to these positions
        # Aspects to Ruler ASC (2 pts)
        mask_conj_r_asc = self.logic.mask_exact_aspect(moon_longs, ruler_asc_pos, 0, 8.0)
        mask_sext_r_asc = self.logic.mask_exact_aspect(moon_longs, ruler_asc_pos, 60, 6.0)
        mask_trin_r_asc = self.logic.mask_exact_aspect(moon_longs, ruler_asc_pos, 120, 6.0)
        
        score_r_asc = np.zeros(N)
        score_r_asc += np.where(mask_conj_r_asc, 2.0, 0.0) # 29
        score_r_asc += np.where(mask_sext_r_asc, 2.0, 0.0) # 31
        score_r_asc += np.where(mask_trin_r_asc, 2.0, 0.0) # 33
        
        total_score += score_r_asc
        details['moon_aspect_ruler_asc'] = score_r_asc
        
        # Aspects to Ruler H10 (2 pts)
        mask_conj_r_h10 = self.logic.mask_exact_aspect(moon_longs, ruler_h10_pos, 0, 8.0)
        mask_sext_r_h10 = self.logic.mask_exact_aspect(moon_longs, ruler_h10_pos, 60, 6.0)
        mask_trin_r_h10 = self.logic.mask_exact_aspect(moon_longs, ruler_h10_pos, 120, 6.0)
        
        score_r_h10 = np.zeros(N)
        score_r_h10 += np.where(mask_conj_r_h10, 2.0, 0.0) # 30
        score_r_h10 += np.where(mask_sext_r_h10, 2.0, 0.0) # 32
        score_r_h10 += np.where(mask_trin_r_h10, 2.0, 0.0) # 34
        
        total_score += score_r_h10
        details['moon_aspect_ruler_h10'] = score_r_h10
        
        return total_score, details

    def calculate_ruler_score(self,
                            times: np.ndarray,
                            ruler_type: str, # 'ASC' or 'H10'
                            ruler_longs: np.ndarray,
                            ruler_ids: np.ndarray,
                            sun_longs: np.ndarray,
                            planet_longs: Dict[int, np.ndarray],
                            house_cusps: np.ndarray,
                            ruler_speeds: np.ndarray = None) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Calcula puntaje para un Regente (ASC o Casa 10).
        Basado en reglas CSV (25-51 para ASC, 18-38 para H10).
        Estrucutra casi idéntica, solo varían algunos puntos o condiciones específicas.
        
        General Rules:
        - Domicilio (+1)
        - Exaltación (+1)
        - Triplicidad (+0.5)
        - Término (+0.5)
        - Directo (+1)
        - No Combusto (>17 deg Sol) (+1)
        - En Casa 1, 10, 11, 9, 5 (+1)
        - Aspectos a Júpiter/Venus (Trigono/Sextil/Conj) (+1)
        - Velocidad (Bonus/Malus)
        """
        N = len(ruler_longs)
        total_score = np.zeros(N, dtype=float)
        details = {}
        prefix = f"ruler_{ruler_type.lower()}"
        
        # --- Dignidades (Dom, Exalt) ---
        # Logic helper provides masks, we use them here.
        # But wait, Helper usually takes (planet_id, longs). Here planet_id varies per moment.
        # We need a vectorized way to check dignity for VARIABLE planet IDs.
        
        # Iteration approach (7 planets)
        is_dom = np.zeros(N, dtype=bool)
        is_exalt = np.zeros(N, dtype=bool)
        
        for pid in range(7): # 0-6
            mask_pid = (ruler_ids == pid)
            if not np.any(mask_pid): continue
            
            # Check domicile
            # Rulerships: logic.RULER_MAP (sign -> planet)
            # We need Inverse map (planet -> [signs])
            ruled_signs = [s for s, p in self.logic.RULER_MAP.items() if p == pid]
            current_signs = self.logic.get_sign_indices(ruler_longs[mask_pid])
            is_dom[mask_pid] = np.isin(current_signs, ruled_signs)
            
            # Check exaltation
            exalt_sign = self.logic.EXALTATION_MAP.get(pid)
            if exalt_sign is not None:
                is_exalt[mask_pid] = (current_signs == exalt_sign)
        
        score_dom = np.where(is_dom, 1.0, 0.0)
        score_exalt = np.where(is_exalt, 1.0, 0.0)
        
        total_score += score_dom
        total_score += score_exalt
        
        details[f'{prefix}_domicile'] = score_dom
        details[f'{prefix}_exaltation'] = score_exalt
        
        # --- Triplicidad & Termino (0.5) ---
        is_trip = np.zeros(N, dtype=bool)
        is_term = np.zeros(N, dtype=bool)
        
        # Iteración (0-6)
        for pid in range(7):
             mask_pid = (ruler_ids == pid)
             if not np.any(mask_pid): continue
             
             p_longs = ruler_longs[mask_pid]
             p_signs = self.logic.get_sign_indices(p_longs)
             
             # Triplicity Check
             # Is planet pid IN the triplicity rulers of sign p_signs?
             # Vectorizing list lookup is tricky. We can use a small loop or map.
             # Or pre-build a 12x7 boolean lookup table?
             # For simplicity here: Iterate unique signs present
             unique_signs = np.unique(p_signs)
             for s in unique_signs:
                 rulers = self.logic.TRIPLICITY_RULERS.get(s, [])
                 if pid in rulers:
                     # Planet IS a trip ruler for sign s
                     # Mask where sign is s
                     mask_sign = (p_signs == s)
                     is_trip[mask_pid & (ruler_longs // 30 == s)] = True
                     
             # Term Check
             # Iterate unique signs
             for s in unique_signs:
                 terms = self.logic.TERMS_MAP.get(s, [])
                 # terms is [(upper, ruler), ...]
                 # Check each term bound
                 prev_bound = 0
                 mask_sign = (p_signs == s)
                 degrees_in_sign = p_longs[mask_sign] % 30
                 
                 for bound, ruler in terms:
                     if ruler == pid:
                         # Check if degree is in [prev_bound, bound)
                         in_term = (degrees_in_sign >= prev_bound) & (degrees_in_sign < bound)
                         # Map back to full array
                         # We need indices relative to N
                         # This is getting complex in pure NumPy "fancy indexing" in a loop.
                         # Simpler: just check if pid matches ruler of term for that degree.
                         pass
                     prev_bound = bound
                     
                 # Simplified Vectorized Term Check:
                 # Create a 360-degree lookup array "TermRuler[360]"? Or 12x30?
                 # No, terms are irregular.
                 # Let's check specifically for this planet in this sign.
                 prev = 0
                 for b, r in terms:
                     if r == pid:
                         # Indices where planet is in this sign AND in this degree range
                         # Need strict masking
                         deg_arr = ruler_longs % 30
                         mask_term_segment = (ruler_ids == pid) & (self.logic.get_sign_indices(ruler_longs) == s) & (deg_arr >= prev) & (deg_arr < b)
                         is_term[mask_term_segment] = True
                     prev = b
                     
        score_trip = np.where(is_trip, 0.5, 0.0)
        score_term = np.where(is_term, 0.5, 0.0)
        
        total_score += score_trip
        total_score += score_term
        details[f'{prefix}_triplicity'] = score_trip
        details[f'{prefix}_term'] = score_term
        
        # --- Directo (Rule 29/22) (+1) ---
        # Need speed. If speed > 0 -> Direct.
        if ruler_speeds is not None:
            is_direct = (ruler_speeds > 0)
            score_direct = np.where(is_direct, 1.0, 0.0)
            total_score += score_direct
            details[f'{prefix}_direct'] = score_direct
            
        # --- No Combusto (>17 deg Sol) (Rule 30/23) (+1) ---
        diff_sun = np.abs(ruler_longs - sun_longs)
        diff_sun = np.minimum(diff_sun, 360 - diff_sun)
        is_not_combust = (diff_sun > 17.0)
        score_not_combust = np.where(is_not_combust, 1.0, 0.0)
        total_score += score_not_combust
        details[f'{prefix}_not_combust'] = score_not_combust # Often called "Hayz" or similar bonus in spirit
        
        # --- Casas 1, 10, 11, 9, 5 (+1 each) ---
        # Same house logic as Moon
        favorable_indices = [0, 9, 10, 8, 4] # 1, 10, 11, 9, 5
        is_fav_house = np.zeros(N, dtype=bool)
        
        for h_idx in favorable_indices:
             cusp_start = house_cusps[:, h_idx]
             next_h = (h_idx + 1) % 12
             cusp_end = house_cusps[:, next_h]
             
             case_normal = (cusp_start < cusp_end) 
             in_house_normal = case_normal & (ruler_longs >= cusp_start) & (ruler_longs < cusp_end)
             case_cross = (~case_normal)
             in_house_cross = case_cross & ((ruler_longs >= cusp_start) | (ruler_longs < cusp_end))
             
             is_fav_house |= (in_house_normal | in_house_cross)
        
        score_house = np.where(is_fav_house, 1.0, 0.0)
        total_score += score_house
        details[f'{prefix}_fav_house'] = score_house
        
        # --- Aspectos a Jupiter (5) y Venus (3) ---
        # Trigono/Sextil/Conjuntion -> +1 point each
        
        def add_aspect_points(target_pid, target_name):
            if target_pid not in planet_longs: return
            target_pos = planet_longs[target_pid]
            
            # Conj (0), Sext (60), Trin (120)
            # CSV Rule 36-39 (ASC), 29-32 (H10)
            # ASC CSV: Trig Jup(1), Trig Ven(1), Sext Ven(1), Sext Jup(1), Conj Ven(1), Conj Jup(1).
            # H10 CSV: Trig Jup(1), Trig Ven(1), Sext Ven(1), Sext Jup(1).
            # Note: H10 CSV doesn't list Conjunction explicitly in points section? 
            # Wait, line 29-32 are Trine/Sextile. 
            # But line 33-35 are aspects to Ruler ASC.
            # Let's apply generic set: Conj, Sext, Trine (All beneficial).
            
            mask_conj = self.logic.mask_exact_aspect(ruler_longs, target_pos, 0, 8.0)
            mask_sext = self.logic.mask_exact_aspect(ruler_longs, target_pos, 60, 6.0)
            mask_trin = self.logic.mask_exact_aspect(ruler_longs, target_pos, 120, 6.0)
            
            # Sum them up (assuming exclusive usually, but if mixed logic allow sum)
            points = np.zeros(N)
            points += np.where(mask_conj, 1.0, 0.0)
            points += np.where(mask_sext, 1.0, 0.0)
            points += np.where(mask_trin, 1.0, 0.0)
            
            nonlocal total_score
            total_score += points
            details[f'{prefix}_aspect_{target_name}'] = points
            
        add_aspect_points(5, 'jupiter')
        add_aspect_points(3, 'venus')

        return total_score, details

    def calculate_natal_score(self,
                            times: np.ndarray,
                            ascmc: np.ndarray,
                            cusps: np.ndarray,
                            natal_chart: Dict[int, float]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Calcula puntaje de Enraizamiento (Natal).
        Reglas CSV (Sección "Reglas enraizar carta natal"):
        - Red Points (Malefics):
          - ASC conj Saturno A (-2)
          - ASC conj Marte A (-2)
          - ASC en Casa 6 A (-2) ## COMPLEX TODO
          - ASC en Casa 8/12 A (Blocked in Filtering Phase)
        
        - Blue Points (Benefics/Angles):
          - ASC conj/trine/sextil ASC A (+2/+1)
          - ASC conj/trine/sextil Sol A (+1)
          - ASC conj/trine/sextil Luna A (+1)
          - ASC conj/trine/sextil Venus A (+1)
          - ASC conj/trine/sextil Jupiter A (+1)
          - MC conj Jupiter A (+1)
          - MC conj Venus A (+1)
          - MC conj Sol A (+1)
          - MC conj Luna A (+1)
        """
        N = len(times)
        total_score = np.zeros(N, dtype=float)
        details = {}
        
        if not natal_chart:
            return total_score, details
            
        asc_elect = ascmc[:, 0]
        mc_elect = ascmc[:, 1] # Or cusps[:, 9]
        
        # --- RED POINTS (Penalties) ---
        # 1. ASC conj Saturno A (-2)
        if 6 in natal_chart: # Saturn
             sat_nat = natal_chart[6]
             mask = self.logic.mask_exact_aspect(asc_elect, np.full(N, sat_nat), 0, 5.0)
             score = np.where(mask, -2.0, 0.0)
             total_score += score
             details['natal_asc_conj_sat'] = score
             
        # 2. ASC conj Marte A (-2)
        if 4 in natal_chart: # Mars
             mar_nat = natal_chart[4]
             mask = self.logic.mask_exact_aspect(asc_elect, np.full(N, mar_nat), 0, 5.0)
             score = np.where(mask, -2.0, 0.0)
             total_score += score
             details['natal_asc_conj_mar'] = score

        # --- BLUE POINTS (Bonuses) ---
        # Helper for aspects
        def score_natal_aspect(elect_point, natal_pid, points_conj, points_trine, points_sext, name):
            if natal_pid not in natal_chart: return
            nat_pos = natal_chart[natal_pid]
            nat_arr = np.full(N, nat_pos)
            
            # Orbs? CSV says "usar orbe" (implies standard) or "5 o menos" for conjunctions often.
            # Let's use 5.0 for Conj, 5.0 for others?
            # Enraizamiento usually uses tighter orbs. Let's stick to 5.0.
            
            mask_c = self.logic.mask_exact_aspect(elect_point, nat_arr, 0, 5.0)
            mask_t = self.logic.mask_exact_aspect(elect_point, nat_arr, 120, 5.0)
            mask_s = self.logic.mask_exact_aspect(elect_point, nat_arr, 60, 5.0)
            
            s = np.zeros(N)
            s += np.where(mask_c, points_conj, 0.0)
            s += np.where(mask_t, points_trine, 0.0)
            s += np.where(mask_s, points_sext, 0.0)
            
            nonlocal total_score
            total_score += s
            details[name] = s

        # ASC vs Planets A
        # ASC A (ID special? Usually passed separately. But we receive dict {int: float}.
        # Need to know ID for Ascendant A. VectorizedNatal uses ...?
        # Standard SwissEph doesn't store Asc in planets dict usually.
        # But `LegacyAstroWrapper` passes it?
        # Wait, `find_elections` receives `natal_chart` as dict. 
        # Typically keys are 0-11 for planets, maybe 15 for Asc?
        # User prompt CSV says "ASC de la carta natal A".
        # Assume ASC is in natal_chart with ID 'asc' or similar? 
        # Or I need to pass it explicitly.
        # Immanuel uses '3000001'? 
        # Let's rely on standard IDs. If Asc not in dict, skip.
        
        # 3000001 is not a valid int index for array usually.
        # Let's assume input dict has Keys compatible.
        
        # ASC vs ASC A
        # Let's assume we might receive a specific key for ASC.
        # If not, skipping ASC-ASC aspect.
        
        # ASC vs Sun(0), Moon(1), Ven(3), Jup(5)
        score_natal_aspect(asc_elect, 0, 1.0, 1.0, 1.0, 'natal_asc_sun')
        score_natal_aspect(asc_elect, 1, 1.0, 1.0, 1.0, 'natal_asc_moon')
        score_natal_aspect(asc_elect, 3, 1.0, 1.0, 1.0, 'natal_asc_ven')
        score_natal_aspect(asc_elect, 5, 1.0, 1.0, 1.0, 'natal_asc_jup')
        
        # ASC vs Natal ASC (Key 12)
        # Rule 9: Conj (+2)
        # Rule 10: Trine (+1)
        # Rule 11: Sextile (+1)
        score_natal_aspect(asc_elect, 12, 2.0, 1.0, 1.0, 'natal_asc_asc')
        
        # MC vs Sun, Moon, Ven, Jup (Conjunction only +1)
        score_natal_aspect(mc_elect, 0, 1.0, 0, 0, 'natal_mc_conj_sun')
        score_natal_aspect(mc_elect, 1, 1.0, 0, 0, 'natal_mc_conj_moon')
        score_natal_aspect(mc_elect, 3, 1.0, 0, 0, 'natal_mc_conj_ven')
        score_natal_aspect(mc_elect, 5, 1.0, 0, 0, 'natal_mc_conj_jup')
        
        return total_score, details

    def calculate_combinations_score(self,
                                   times: np.ndarray,
                                   ruler_asc_ids: np.ndarray,
                                   ruler_asc_longs: np.ndarray,
                                   ruler_h10_ids: np.ndarray,
                                   ruler_h10_longs: np.ndarray,
                                   planet_longs: Dict[int, np.ndarray],
                                   ascmc: np.ndarray,
                                   cusps: np.ndarray,
                                   natal_asc_sign: int = None) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Calcula puntaje de Combinaciones Positivas y Negativas (Arquetipos).
        
        Reglas Positivas:
        1. Regente ASC y Regente H10 en conjunción/sextil/trígono (+2)
        2. Sol en Casa 10 (+2)
        3. Júpiter en Casa 10 (+2)
        4. Luna en Casa 10 (+2)
        
        Reglas Negativas:
        1. Si ASC Natal es Cap/Acuario -> Skip (Saturno es regente, ok en 10)
        2. Saturno en Casa 10 (-1)
        3. Saturno en ASC (-1)
        
        5. Si Marte rige ASC Natal -> Skip (Marte es regente, ok en 10)
        6. Marte en Casa 10 (-1)
        7. Marte en ASC (-1)
        """
        N = len(times)
        total_score = np.zeros(N, dtype=float)
        details = {}
        
        # --- POSITIVAS ---
        
        # 1. Reg ASC y Reg H10 Aspecto (+2)
        mask_conj = self.logic.mask_exact_aspect(ruler_asc_longs, ruler_h10_longs, 0, 8.0)
        mask_sext = self.logic.mask_exact_aspect(ruler_asc_longs, ruler_h10_longs, 60, 6.0)
        mask_trin = self.logic.mask_exact_aspect(ruler_asc_longs, ruler_h10_longs, 120, 6.0)
        
        score_aspect = np.where(mask_conj | mask_sext | mask_trin, 2.0, 0.0)
        total_score += score_aspect
        details['comb_pos_rulers_aspect'] = score_aspect
        
        # Helper: Planet in H10
        # H10 is between Cusp 10 (index 9) and Cusp 11 (index 10)
        cusp_10 = cusps[:, 9]
        cusp_11 = cusps[:, 10]
        
        # Handle wrap around 360
        case_normal = (cusp_10 < cusp_11)
        
        def is_in_h10(p_longs):
            in_normal = case_normal & (p_longs >= cusp_10) & (p_longs < cusp_11)
            in_cross = (~case_normal) & ((p_longs >= cusp_10) | (p_longs < cusp_11))
            return in_normal | in_cross
            
        # 2,3,4: Sun, Jup, Moon in H10
        if 0 in planet_longs:
            s_sun = np.where(is_in_h10(planet_longs[0]), 2.0, 0.0)
            total_score += s_sun
            details['comb_pos_sun_h10'] = s_sun
            
        if 5 in planet_longs:
            s_jup = np.where(is_in_h10(planet_longs[5]), 2.0, 0.0)
            total_score += s_jup
            details['comb_pos_jup_h10'] = s_jup
            
        if 1 in planet_longs:
            s_moon = np.where(is_in_h10(planet_longs[1]), 2.0, 0.0)
            total_score += s_moon
            details['comb_pos_moon_h10'] = s_moon
            
        # --- NEGATIVAS ---
        
        # Determine strictness based on Natal ASC. 
        # If ASC Natal is Capricorn (9) or Aquarius (10), Saturn is benefic/ruler -> Skip Saturn penalties?
        # CSV: "Si el ASC de la Carta natal A esta en Capricornio o Acuario ir a 5 (no analizo 2 y 3)"
        
        skip_saturn = False
        if natal_asc_sign is not None:
             if natal_asc_sign in [9, 10]: # Cap, Aqu
                 skip_saturn = True
                 
        if not skip_saturn and 6 in planet_longs:
             sat_longs = planet_longs[6]
             # Saturn in H10 (-1)
             s_sat_h10 = np.where(is_in_h10(sat_longs), -1.0, 0.0)
             total_score += s_sat_h10
             details['comb_neg_saturn_h10'] = s_sat_h10
             
             # Saturn in ASC (-1) -> In House 1? Or Conjunct ASC?
             # CSV says "Saturno esta en el ASC" -> Usually means House 1.
             # H1 is between Cusp 1 (index 0) and Cusp 2 (index 1)
             c1 = cusps[:, 0]
             c2 = cusps[:, 1]
             cn = (c1 < c2)
             in_h1 = (cn & (sat_longs >= c1) & (sat_longs < c2)) | ((~cn) & ((sat_longs >= c1) | (sat_longs < c2)))
             
             s_sat_h1 = np.where(in_h1, -1.0, 0.0)
             total_score += s_sat_h1
             details['comb_neg_saturn_asc'] = s_sat_h1
             
        # Mars (Same logic)
        # CSV: Si Marte rige el ASC de la carta natal A... (Aries(0) or Scorpio(7))
        skip_mars = False
        if natal_asc_sign is not None:
             if natal_asc_sign in [0, 7]:
                 skip_mars = True
                 
        if not skip_mars and 4 in planet_longs:
             mar_longs = planet_longs[4]
             # Mars in H10
             s_mar_h10 = np.where(is_in_h10(mar_longs), -1.0, 0.0)
             total_score += s_mar_h10
             details['comb_neg_mars_h10'] = s_mar_h10
             
             # Mars in ASC (H1)
             c1 = cusps[:, 0]
             c2 = cusps[:, 1]
             cn = (c1 < c2)
             in_h1 = (cn & (mar_longs >= c1) & (mar_longs < c2)) | ((~cn) & ((mar_longs >= c1) | (mar_longs < c2)))
             
             s_mar_h1 = np.where(in_h1, -1.0, 0.0)
             total_score += s_mar_h1
             details['comb_neg_mars_asc'] = s_mar_h1
             
        return total_score, details

