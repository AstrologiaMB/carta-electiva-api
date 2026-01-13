
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder
from scripts.v2_year_demo import get_natal_chart

def compare_models():
    # Setup
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # Analyze 5 days
    start = datetime(2026, 6, 15, 0, 0)
    end = datetime(2026, 6, 20, 0, 0)
    
    finder = VectorizedElectionFinder()
    
    # We need to hack the finder to return columns logic if possible, 
    # but the finder already returns broken down scores in 'score_natal' etc.
    # We just need to analyze the DF.
    
    df = finder.find_elections(start, end, lat, lon, natal_chart=natal_chart, interval_minutes=20)
    
    if df.empty:
        print("No candidates found.")
        return

    # Model A: Current (Total Sum)
    print(f"\n🧪 ANALIZANDO {len(df)} MOMENTOS CANDIDATOS...\n")
    
    # Sort by Total Score (Current V2)
    top_general = df.sort_values('score_total', ascending=False).head(3)
    
    # Sort by Natal Score (Enraizamiento Only)
    top_natal = df.sort_values('score_natal', ascending=False).head(3)
    
    def print_row(r, title):
        print(f"[{title}] {r['timestamp']} | Total: {r['score_total']:.1f} | Natal: {r['score_natal']:.1f} | General: {r['score_total'] - r['score_natal']:.1f}")
        # Components breakdown for Natal
        comps = r['components']
        nat_comps = {k:v for k,v in comps.items() if 'natal' in k}
        print(f"   ↳ Natal Factors: {nat_comps}")

    print("--- 🏆 TOP 3 SEGÚN MODELO GENERAL (V2 Actual) ---")
    for i, r in top_general.iterrows():
        print_row(r, f"#{i}")

    print("\n--- 🌳 TOP 3 SEGÚN MODELO ENRAIZAMIENTO (Tu Propuesta) ---")
    for i, r in top_natal.iterrows():
        print_row(r, f"#{i}")
        
    # Check divergence
    best_gen_idx = top_general.index[0]
    best_nat_idx = top_natal.index[0]
    
    if best_gen_idx == best_nat_idx:
        print("\n✅ CONCLUSIÓN: Ambos modelos coinciden en el mejor momento.")
    else:
        print("\n⚡ CONCLUSIÓN: Divergencia encontrada. El modelo de Enraizamiento prefiere un momento distinto.")
        print(f"   Diferencia de Score Natal: {df.loc[best_nat_idx]['score_natal']} vs {df.loc[best_gen_idx]['score_natal']}")
        print(f"   Diferencia de Score General: {(df.loc[best_nat_idx]['score_total'] - df.loc[best_nat_idx]['score_natal'])} vs {(df.loc[best_gen_idx]['score_total'] - df.loc[best_gen_idx]['score_natal'])}")

if __name__ == "__main__":
    compare_models()
