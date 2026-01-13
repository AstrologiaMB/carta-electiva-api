
import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytz

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def optimize_candidate(finder, center_time, lat, lon, natal_chart, topic='trabajo', window_minutes=60):
    """
    Refina un candidato buscando minuto a minuto alrededor de la hora detectada.
    """
    start_opt = center_time - timedelta(minutes=window_minutes//2)
    end_opt = center_time + timedelta(minutes=window_minutes//2)
    
    # Búsqueda fina (intervalo = 1 minuto)
    df_opt = finder.find_elections(
        start_opt, end_opt, lat, lon,
        natal_chart=natal_chart,
        topic=topic,
        interval_minutes=1 # <--- CLAVE: Alta resolución
    )
    
    if df_opt.empty:
        return None
        
    # Retornar el mejor momento exacto
    best = df_opt.loc[df_opt['score_total'].idxmax()]
    return best

def run_refinement_demo():
    # 1. Configuración Base
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    finder = VectorizedElectionFinder()
    
    # 2. Candidato "Grueso" (Ejemplo detectado antes: 17 Junio 2026 17:00)
    # Imaginemos que el barrido general nos dio las 17:00
    candidate_coarse = datetime(2026, 6, 17, 17, 0, 0)
    
    print(f"\n🔬 REFINANDO CANDIDATO DETECTADO: {candidate_coarse}")
    print("   Buscando el minuto exacto de mayor puntaje...")
    
    best_exact = optimize_candidate(finder, candidate_coarse, lat, lon, natal_chart)
    
    if best_exact is not None:
        print("\n✨ MOMENTO OPTIMIZADO ENCONTRADO:")
        print(f"   Hora Exacta: {best_exact['timestamp']}")
        print(f"   Score Final: {best_exact['score_total']:.2f}")
        print(f"   Desglose: Moon({best_exact['score_moon']}) Asc({best_exact['score_r_asc']}) H10({best_exact['score_r_h10']}) Comb({best_exact.get('score_comb',0)})")
        
        # Comparación
        diff = best_exact['score_total'] - 25.0 # 25 era el score grueso
        print(f"\n   Diferencia vs Hora en Punto: {diff:+.2f} puntos")
        if diff > 0:
            print("   ✅ Vale la pena la precisión: Se ganaron puntos extra.")
        else:
            print("   ℹ️  La hora en punto ya era óptima o muy cercana.")
            
    else:
        print("❌ No se pudo optimizar (quizás filtros bloquearon todo el rango).")

if __name__ == "__main__":
    run_refinement_demo()
