
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

def verify_normalized():
    # Setup
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # 17 Jun 2026 17:00 was 25.0
    start = datetime(2026, 6, 17, 16, 30)
    end = datetime(2026, 6, 17, 17, 30)
    
    finder = VectorizedElectionFinder()
    df = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=30)
    
    if df.empty: return

    row = df.loc[df['score_total'].idxmax()]
    
    print("\n🌟 VERIFICACIÓN DE UX HUMANIZADO")
    print(f"Timestamp: {row['timestamp']}")
    print(f"Raw Score: {row['score_total']}")
    
    print("-" * 40)
    print(f"Normalized: {row['score_normalized']}%")
    print(f"Label:      {row['label']}")
    print(f"Stars:      {'⭐' * int(row['stars'])}")
    print("-" * 40)
    
    if row['label'] == "Excelente" and row['stars'] == 5:
        print("✅ Lógica de normalización correcta.")
    else:
        print("⚠️ Revisar umbrales.")

if __name__ == "__main__":
    verify_normalized()
