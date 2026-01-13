
import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import swisseph as swe

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports
from core.algoritmo_busqueda import AlgoritmoBusqueda
from core.legacy_wrapper import LegacyAstroWrapper
from core.election_engine import VectorizedElectionFinder
from core.vectorized_logic import VectorizedLogic
from core.vectorized_ephemeris import VectorizedEphemeris
from core.vectorized_houses import VectorizedHouses
from core.vectorized_natal import VectorizedNatal

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def compare_engines():
    print("⚔️  COMPARATIVA: LEGACY vs V2 (VECTORIZADO)")
    print("-------------------------------------------")
    
    # 1. Configuración del Usuario y Búsqueda
    # 26/12/1964 21:12 Buenos Aires
    dob = datetime(1964, 12, 26, 21, 12)
    lat, lon = -34.6037, -58.3816 # Buenos Aires
    
    start_date = datetime(2025, 8, 1, 0, 0)
    end_date = datetime(2025, 8, 30, 0, 0)
    topic = "trabajo"
    
    print(f"👤 Usuario: {dob} (BA)")
    print(f"📅 Fecha: {start_date.date()} - {end_date.date()}")
    print(f"🎯 Tema: {topic.upper()}")
    print("-------------------------------------------")

    # 2. Ejecutar LEGACY
    print("\n🐢 Ejecutando LEGACY (Algoritmo Viejo)...")
    t0 = datetime.now()
    
    # Legacy setup
    wrapper = LegacyAstroWrapper(dob, lat, lon)
    carta_natal_legacy = wrapper.get_chart_data_for_enraizamiento()
    
    legacy_algo = AlgoritmoBusqueda(carta_natal_legacy, topic, lat, lon)
    # Legacy often runs internally with 15 or 30 min steps depending on logic
    legacy_results = legacy_algo.buscar_mejores_momentos(start_date, end_date)
    
    t_legacy = (datetime.now() - t0).total_seconds()
    print(f"   ✅ Legacy encontró {len(legacy_results)} candidatos en {t_legacy:.2f}s")
    
    if len(legacy_results) > 0:
        print(f"   Ejemplo Legacy: {legacy_results[0]['fecha_hora']}")

    # 3. Ejecutar V2 (New)
    print("\n🚀 Ejecutando V2 (Nuevo Algoritmo)...")
    t0 = datetime.now()
    
    # V2 Setup (Swisseph direct for speed logic)
    # DOB -> UTC
    dob_utc = dob + timedelta(hours=3) # BA is GMT-3
    t_utc = dob_utc.hour + dob_utc.minute/60.0
    jd_natal = swe.julday(dob_utc.year, dob_utc.month, dob_utc.day, t_utc)
    
    natal_chart_v2 = {}
    for b in [0, 1, 2, 3, 4, 5, 6]:
        xx, _ = swe.calc_ut(jd_natal, b)
        natal_chart_v2[b] = xx[0]
        
    finder = VectorizedElectionFinder()
    df_v2 = finder.find_elections(
        start_date, end_date, lat, lon, 
        natal_chart=natal_chart_v2,
        topic=topic,
        interval_minutes=30
    )
    
    t_v2 = (datetime.now() - t0).total_seconds()
    print(f"   ✅ V2 encontró {len(df_v2)} candidatos en {t_v2:.2f}s")
    
    # Sort V2 by Score descending
    if not df_v2.empty and 'score_total' in df_v2.columns:
        df_v2 = df_v2.sort_values('score_total', ascending=False).reset_index(drop=True)
        print("\n🏆 Top 5 V2 Candidates:")
        for i, row in df_v2.head(5).iterrows():
            print(f"   {i+1}. {row['timestamp']} | Score: {row['score_total']:.1f} (Moon: {row['score_moon']:.1f}, Asc: {row['score_r_asc']:.1f}, H10: {row['score_r_h10']:.1f}, Nat: {row.get('score_natal', 0):.1f}, Comb: {row.get('score_comb', 0):.1f})")

    # 4. ANÁLISIS DE DISCREPANCIAS
    print("\n🕵️  ANÁLISIS DE DISCREPANCIAS & SCORES")
    print("-------------------------------------------")
    
    # Check overlap
    timestamps_legacy = set([r['fecha_hora'] for r in legacy_results])
    timestamps_v2 = set(df_v2['timestamp'])
    
    common = timestamps_legacy.intersection(timestamps_v2)
    missing_in_v2 = timestamps_legacy - timestamps_v2
    extra_in_v2 = timestamps_v2 - timestamps_legacy
    
    print(f"ℹ️  Legacy: {len(legacy_results)} vs V2: {len(df_v2)}")
    print(f"✅ Coincidencias Exactas: {len(common)} / {len(legacy_results)}")
    
    if len(common) > 0:
        print("\n📊 Rango de los candidatos Legacy dentro de V2 (Ordenado por Score):")
        ranks = []
        for ts in common:
            # Find rank in sorted V2
            match = df_v2[df_v2['timestamp'] == ts]
            if not match.empty:
                rank = match.index[0] + 1
                score = match.iloc[0]['score_total']
                ranks.append((rank, ts, score))
        
        ranks.sort()
        # Show top 5 ranks of legacy matches
        for r, ts, s in ranks[:5]:
            print(f"   Rank #{r} in V2: {ts} (Score: {s:.1f})")
        if len(ranks) > 5:
            print(f"   ... y {len(ranks)-5} más.")
            
    if missing_in_v2:
        print(f"\n❌ Faltan en V2 ({len(missing_in_v2)}):")
        for ts in list(missing_in_v2)[:5]:
            print(f"   - {ts}")
        print("   -> Analizando MOTIVO de rechazo del primero...")
        candidate = list(missing_in_v2)[0]
        analyze_rejection(candidate, lat, lon, natal_chart_v2, topic, finder)

    elif len(legacy_results) > 0 and len(df_v2) == 0:
        print("🚨 El Viejo Algoritmo permite fechas que el Nuevo bloquea.")


def analyze_rejection(target_time, lat, lon, natal_chart, topic, finder):
    """
    Runs V2 logic step-by-step for a SINGLE moment to find the rejection cause.
    """
    # 1. Ephemeris
    # Create single moment array (UTC)
    # Legacy target_time is usually naive or local? Assuming input to logic was naive representing local.
    # V2 uses naive as inputs.
    
    times_arr = [target_time]
    
    # Run Ephemeris
    bodies = [0, 1, 2, 3, 4, 5, 6, 10]
    positions = finder.ephemeris.calculate_positions(times_arr, bodies)
    longitudes = finder.ephemeris.get_longitudes(positions)
    
    moon_long = longitudes[1][0]
    sun_long = longitudes[0][0]
    
    # 2. Check Moon Logic
    logic = finder.logic
    
    # Sign
    sign_idx = int(moon_long // 30)
    sign_names = ["Aries", "Tauro", "Geminis", "Cancer", "Leo", "Virgo", "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
    print(f"   🌑 Estado Lunar:")
    print(f"      - Signo: {sign_names[sign_idx]} ({moon_long:.2f}°)")
    
    # Moon Dignity (Cap/Esc)
    mask_sign = logic.mask_signs(np.array([moon_long]), [7, 9]) # Scorp, Cap
    if mask_sign[0]:
        print("      ❌ RECHAZADO: Luna en Signo Debilitado (Escorpio/Capricornio)")
    else:
        print("      ✅ Signo OK")
        
    # Phase
    mask_phase = logic.mask_phase(np.array([sun_long]), np.array([moon_long]))
    if mask_phase[0]:
        print("      ❌ RECHAZADO: Fase Lunar Inadecuada (Nueva/Llena)")
    else:
        print("      ✅ Fase OK")
        
    # VoC
    # Need full context for VoC, usually checks next aspect.
    # Assuming finder.logic.mask_void_of_course works on single item arrays correctly if implemented safely.
    # It might require looking ahead. V2 VoC logic uses 'next aspect' relative to current pos.
    # Implementation detail: mask_void_of_course checks aspects in current day? 
    # Let's trust the mask.
    mask_voc = logic.mask_void_of_course(times_arr, np.array([moon_long]), longitudes)
    if mask_voc[0]:
        print("      ❌ RECHAZADO: Luna Vacía de Curso")
    else:
        print("      ✅ VoC OK")

    # 3. Check Ruler Logic
    print(f"   👑 Estado del Regente (Tema: {topic}):")
    # Calculate Houses
    houses = VectorizedHouses()
    cusps, ascmc = houses.calculate_houses(times_arr, lat, lon)
    
    # Trabjo = House 10
    h10_cusp = cusps[0][9] # Index 9 is H10
    h10_sign = int(h10_cusp // 30)
    h10_ruler_id = logic.get_ruler_for_sign(h10_sign)
    ruler_names = ["Sol", "Luna", "Mercurio", "Venus", "Marte", "Jupiter", "Saturno"]
    
    print(f"      - Casa 10 en {sign_names[h10_sign]} ({h10_cusp:.2f}°)")
    print(f"      - Regente: {ruler_names[h10_ruler_id]}")
    
    # Ruler Pos
    ruler_long = longitudes[h10_ruler_id][0]
    ruler_sign = int(ruler_long // 30)
    print(f"      - Posición Regente: {sign_names[ruler_sign]} ({ruler_long:.2f}°)")
    
    # Check Debility
    is_debilitated = logic.mask_debility(h10_ruler_id, np.array([ruler_long]))[0]
    
    if is_debilitated:
        print(f"      ❌ RECHAZADO: Regente en Debilidad (Exilio/Caída)")
        print(f"         (Probable Causa: Saturno en Aries o similar)")
    else:
        print("      ✅ Regente OK (Digno o Peregrino)")

    # 4. Check Natal Logic
    print(f"   🌳 Enraizamiento (Natal):")
    natal = VectorizedNatal()
    
    # Check Hard Aspects to Lights
    mask_natal = natal.mask_hard_aspects_to_natal_lights(longitudes, natal_chart)
    
    if mask_natal[0]:
        print("      ❌ RECHAZADO: Tránsito Tenso a Luminares Natales")
        
        # Dig Deeper: Who is hitting who?
        # Check Saturn (6) vs Sun (0)
        sat_long = longitudes[6][0] # Transit Saturn
        natal_sun = natal_chart[0]
        
        diff = abs(sat_long - natal_sun)
        diff = min(diff, 360 - diff)
        
        print(f"         - Saturno T ({sat_long:.2f}°) vs Sol N ({natal_sun:.2f}°)")
        print(f"         - Distancia: {diff:.2f}°")
        
        # Check standard aspects (0, 90, 180) with orb 8
        is_hard = False
        for asp in [0, 90, 180]:
            if abs(diff - asp) <= 8.0:
                print(f"         -> ASPECTO DURO DETECTADO: {asp}° (Orbe {abs(diff-asp):.2f}°)")
                is_hard = True
                
        if not is_hard:
             print("         (Otro planeta maléfico está haciendo aspecto)")
    else:
        print("      ✅ Enraizamiento OK")

if __name__ == "__main__":
    compare_engines()
