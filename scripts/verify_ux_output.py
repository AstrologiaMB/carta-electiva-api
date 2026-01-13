
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

def verify_ux_output():
    # Setup
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # Run short search
    start = datetime(2026, 6, 17, 12, 0)
    end = datetime(2026, 6, 17, 18, 0)
    
    finder = VectorizedElectionFinder()
    df = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=30)
    
    if df.empty:
        print("No results found.")
        return

    # Sort
    df = df.sort_values('score_total', ascending=False)
    top = df.iloc[0]
    
    print("\n✅ VERIFICACIÓN DE OUTPUT UX")
    print(f"Timestamp: {top['timestamp']}")
    print(f"Total Score (NET): {top['score_total']}")
    print(f"Positive Score (GREEN): {top['score_positive']}")
    print(f"Negative Score (RED):   {top['score_negative']}")
    
    print("\n🔍 COMPONENTS DETAILED (Tooltip Data):")
    comps = top['components']
    # Print sorted by value desc
    for k, v in sorted(comps.items(), key=lambda item: item[1], reverse=True):
        print(f"   {k:<30}: {v:+}")

if __name__ == "__main__":
    verify_ux_output()
