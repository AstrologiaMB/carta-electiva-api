
import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import swisseph as swe
from collections import Counter

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports
from core.algoritmo_busqueda import AlgoritmoBusqueda
from core.legacy_wrapper import LegacyAstroWrapper
from core.election_engine import VectorizedElectionFinder
from core.vectorized_houses import VectorizedHouses
from core.vectorized_natal import VectorizedNatal

# Configure logging
logging.basicConfig(level=logging.ERROR)

def analyze_all_legacy():
    print("🕵️  ANÁLISIS DETALLADO: ¿POR QUÉ V2 RECHAZA A LEGACY?")
    print("-----------------------------------------------------")
    
    # 1. Setup Data
    dob = datetime(1964, 12, 26, 21, 12)
    lat, lon = -34.6037, -58.3816 # Buenos Aires
    start_date = datetime(2025, 8, 1, 0, 0)
    end_date = datetime(2025, 8, 30, 0, 0)
    topic = "trabajo"
    
    print(f"User: {dob} | Range: Aug 2025 | Topic: {topic}")
    
    # 2. Run Legacy to get candidates
    print("1️⃣  Ejecutando Legacy para obtener candidatos...")
    wrapper = LegacyAstroWrapper(dob, lat, lon)
    carta_natal_legacy = wrapper.get_chart_data_for_enraizamiento()
    legacy_algo = AlgoritmoBusqueda(carta_natal_legacy, topic, lat, lon)
    legacy_results = legacy_algo.buscar_mejores_momentos(start_date, end_date)
    
    if not legacy_results:
        print("❌ Legacy no encontró nada esta vez. Raro.")
        return
        
    print(f"✅ Legacy encontró {len(legacy_results)} momentos.")
    
    # 3. Setup V2 Tools
    # Calc Natal V2
    dob_utc = dob + timedelta(hours=3)
    t_utc = dob_utc.hour + dob_utc.minute/60.0
    jd_natal = swe.julday(dob_utc.year, dob_utc.month, dob_utc.day, t_utc)
    
    natal_chart = {}
    for b in range(7):
        xx, _ = swe.calc_ut(jd_natal, b)
        natal_chart[b] = xx[0]
        
    finder = VectorizedElectionFinder()
    logic = finder.logic
    ephem = finder.ephemeris
    natal_mod = VectorizedNatal() # Module
    
    # 4. Analyze Each Candidate
    print("\n2️⃣  Auditando cada momento con lógica V2...")
    print(f"{'FECHA':<20} | {'RAZÓN DE RECHAZO V2'}")
    print("-" * 60)
    
    rejection_reasons = []
    
    for mom in legacy_results:
        dt = mom['fecha_hora']
        
        # Calculate Logic V2 for this specific time
        # Prepare arrays
        times_arr = np.array([dt])
        
        # Ephemeris
        bodies = [0, 1, 2, 3, 4, 5, 6, 10]
        positions = ephem.calculate_positions(times_arr, bodies)
        longitudes = ephem.get_longitudes(positions)
        
        moon_long = longitudes[1][0]
        sun_long = longitudes[0][0]
        
        reason = "✅ APROBADO (V2 Coincide)"
        
        # Check 1: Moon Sign
        if logic.mask_signs(np.array([moon_long]), [7, 9])[0]:
            reason = "🌑 Luna en Signo (Esc/Cap)"
        
        # Check 2: Phase
        elif logic.mask_phase(np.array([sun_long]), np.array([moon_long]))[0]:
            reason = "🌑 Fase Lunar (Nueva/Llena)"
             
        # Check 3: VoC (Approximate check without full day sweep)
        # Skipping VoC exact check in single-point analysis as it requires context
        
        # Check 4: Ruler (H10)
        else:
            # Houses
            h = VectorizedHouses()
            cusps, _ = h.calculate_houses(times_arr, lat, lon)
            h10_cusp = cusps[0][9]
            h10_ruler = logic.get_ruler_for_sign(int(h10_cusp // 30))
            ruler_long = longitudes[h10_ruler][0]
            
            if logic.mask_debility(h10_ruler, np.array([ruler_long]))[0]:
                ruler_names = ["Sol", "Luna", "Mercurio", "Venus", "Marte", "Jupiter", "Saturno"]
                r_name = ruler_names[h10_ruler]
                reason = f"👑 Regente Debilitado ({r_name})"
            
            # Check 5: Natal (The Big One)
            else:
                if natal_mod.mask_hard_aspects_to_natal_lights(longitudes, natal_chart)[0]:
                    # Find who
                    details = []
                    # Check Saturn (6) vs Sun (0)
                    sat_t = longitudes[6][0]
                    sun_n = natal_chart[0]
                    diff = abs(sat_t - sun_n)
                    diff = min(diff, 360 - diff)
                    if abs(diff - 90) < 10:
                         details.append("Saturno(T) Quad Sol(N)")
                    elif abs(diff - 180) < 10:
                         details.append("Saturno(T) Opp Sol(N)")
                    elif abs(diff - 0) < 10:
                         details.append("Saturno(T) Conj Sol(N)")
                         
                    # Check Mars 
                    mars_t = longitudes[4][0]
                    diff_m = min(abs(mars_t - sun_n), 360 - abs(mars_t - sun_n))
                     # ... logic for Mars aspects ...
                    
                    if not details: details.append("Aspecto Tenso Genérico")
                    
                    reason = f"⚠️ Natal: {', '.join(details)}"
                    
        rejection_reasons.append(reason)
        print(f"{dt.strftime('%Y-%m-%d %H:%M')} | {reason}")
        
    # 5. Summary
    print("-" * 60)
    print("📊 RESUMEN DE RECHAZOS:")
    counts = Counter(rejection_reasons)
    for r, c in counts.items():
        print(f"   {r}: {c} casos")

if __name__ == "__main__":
    analyze_all_legacy()
