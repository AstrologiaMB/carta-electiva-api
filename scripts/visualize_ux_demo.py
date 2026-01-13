
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

def draw_bar(val, max_val, char='█', color_code=None):
    if max_val == 0: return ""
    # Normalize to max width of 20 chars
    width = int((val / max_val) * 20)
    bar = char * width
    if color_code:
        return f"{color_code}{bar}\033[0m"
    return bar

def visualize_day():
    # Setup
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # Target: June 17, 2026 (Found as best day previously)
    # Analyze 24 hours
    start = datetime(2026, 6, 17, 0, 0)
    end = datetime(2026, 6, 18, 0, 0)
    
    print(f"\n🔮 ANALIZANDO FLUJO DE ENERGÍA: {start.date()}")
    print("="*60)
    
    finder = VectorizedElectionFinder()
    try:
        df = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=60)
    except Exception as e:
        print(f"Error running engine: {e}")
        return

    if df.empty:
        print("No valid times found for this day (Strict Mode active?).")
        return

    # Determine scaling for display
    max_pos = df['score_positive'].max()
    max_neg = abs(df['score_negative'].min()) # min because it's negative numbers
    max_scale = max(max_pos, max_neg, 10.0)
    
    # Colors (ANSI)
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    print(f"\n{BOLD}{'HORA':^5} | {'NET':^5} | {'POSITIVE (Benefics)':<22} | {'NEGATIVE (Risks)':<22} | {'TREND'}{RESET}")
    print("-" * 80)

    for i, row in df.iterrows():
        ts = row['timestamp']
        time_str = ts.strftime("%H:%M")
        
        net = row['score_total']
        pos = row['score_positive']
        neg = abs(row['score_negative']) # Treat as positive magnitude for bar
        
        # Visual Bars
        bar_pos = draw_bar(pos, max_scale, '█', GREEN)
        bar_neg = draw_bar(neg, max_scale, '█', RED) # ░ for negative
        
        # Trend Icon
        trend = "⚪"
        if net > 15: trend = "🟢 EXCELENTE"
        elif net > 10: trend = "🟢 BUENO"
        elif net > 0: trend = "🟡 NORMAL"
        elif net < 0: trend = "🔴 RIESGO"
        
        # Highlight Peak
        highlight = ""
        if net == df['score_total'].max():
             highlight = "👈 PICO MÁXIMO"
             time_str = f"{BOLD}{time_str}{RESET}"

        print(f"{time_str} | {net:>5.1f} | {bar_pos:<30} | {bar_neg:<30} | {trend} {highlight}")

    # Best Moment Detail
    best = df.loc[df['score_total'].idxmax()]
    print("\n" + "="*60)
    print(f"🏆 MEJOR MOMENTO DEL DÍA: {best['timestamp']}")
    print("="*60)
    print(f"📈 Score Neto: {best['score_total']}")
    print(f"{GREEN}▲ Positivo:   {best['score_positive']}{RESET}")
    print(f"{RED}▼ Negativo:   {best['score_negative']}{RESET}")
    
    print("\n🔍 DESGLOSE DE COMPONENTES:")
    comps = best['components']
    
    # Sort by value
    sorted_comps = sorted(comps.items(), key=lambda x: x[1], reverse=True)
    
    for k, v in sorted_comps:
        val_str = f"{v:+.1f}"
        color = GREEN if v > 0 else RED
        print(f"   {color}{val_str:>6}{RESET} : {k}")

if __name__ == "__main__":
    visualize_day()
