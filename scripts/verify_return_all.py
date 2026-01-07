
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

def verify_return_all():
    # Setup
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # 24 hours window
    start = datetime(2026, 6, 17, 0, 0)
    end = datetime(2026, 6, 18, 0, 0)
    
    finder = VectorizedElectionFinder()
    
    # 1. Standard (Strict) Search
    df_strict = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=60, return_all=False)
    count_strict = len(df_strict)
    
    # 2. Return All (Relaxed) Search
    df_all = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=60, return_all=True)
    count_all = len(df_all)
    
    # Analyze Logic
    df_rejected = df_all[df_all['is_valid'] == False]
    count_rejected = len(df_rejected)
    
    print(f"\n🧪 TEST RETURN_ALL PARAMETER (24hs Window)")
    print(f"Strict Mode Matches: {count_strict}")
    print(f"Relaxed Mode Matches: {count_all} (Should be 24 or 25)")
    print(f"Rejected Moments: {count_rejected}")
    
    if not df_rejected.empty:
        sample = df_rejected.iloc[0]
        print(f"\n🔍 Ejemplo de Rechazado (Visible en Gráfico Rojo):")
        print(f"Timestamp: {sample['timestamp']}")
        print(f"Valid: {sample['is_valid']}")
        print(f"Flags: {sample['flags']}")
        print(f"Score: {sample['score_normalized']}% (Aunque rechazado, tiene puntaje)")

    if count_all > count_strict:
        print("\n✅ Funcionalidad verificada: return_all devuelve más datos (incluyendo rechazados).")
    else:
        print("\n⚠️ Alerta: No se encontraron diferencias. ¿Día demasiado perfecto?")

if __name__ == "__main__":
    verify_return_all()
