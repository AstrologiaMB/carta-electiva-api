
import sys
import os
import logging
from datetime import datetime, timedelta
import pytz
import pandas as pd
import swisseph as swe
import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.election_engine import VectorizedElectionFinder, VectorizedEphemeris

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_natal_chart(birth_date_local, lat, lon):
    """Calcula carta natal (Planetas + ASC)"""
    # Convert Local to UTC
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    dt_local = tz.localize(birth_date_local)
    dt_utc = dt_local.astimezone(pytz.UTC)
    
    logger.info(f"🎂 Nacimiento: {dt_local} -> UTC: {dt_utc}")
    
    # JD
    hour = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)
    
    chart = {}
    
    # Planets (0-6)
    for i in range(7):
        res = swe.calc_ut(jd, i, swe.FLG_SWIEPH)[0]
        chart[i] = res[0] # Longitude
        
    # Houses (for ASC)
    h_res = swe.houses(jd, lat, lon, b'P')
    asc = h_res[1][0] # Ascendant is index 0 of ascmc tuple
    chart[12] = asc # Key 12 for Natal ASC
    
    logger.info(f"   ASC Natal: {asc:.2f}°")
    
    return chart

def run_simulation():
    # 1. Configuración
    dob = datetime(1964, 12, 26, 21, 12)
    lat = -34.6037
    lon = -58.3816
    
    # 2. Calcular Natal
    natal_chart = get_natal_chart(dob, lat, lon)
    
    # 3. Rango de Búsqueda (1 Año: 2025)
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2026, 1, 1, 0, 0, 0)
    
    logger.info(f"📅 Rango Simulación: {start_date} a {end_date}")
    
    # 4. Inicializar Motor
    finder = VectorizedElectionFinder()
    
    # 5. Ejecutar
    t0 = datetime.now()
    results_df = finder.find_elections(
        start_date, end_date, lat, lon,
        topic='trabajo',
        natal_chart=natal_chart,
        interval_minutes=60 # Cada hora
    )
    t1 = datetime.now()
    duration = (t1 - t0).total_seconds()
    
    print("\n" + "="*60)
    print(f"🚀 RESULTADOS V2 SIMULACIÓN 1 AÑO")
    print("="*60)
    print(f"⏱️  Tiempo Ejecución: {duration:.2f}s")
    print(f"📊 Candidatos Encontrados: {len(results_df)}")
    
    if not results_df.empty:
         # Sort by Total Score
         results_df = results_df.sort_values('score_total', ascending=False)
         
         print("\n🏆 TOP 20 MEJORES MOMENTOS:")
         print("-" * 120)
         print(f"{'FECHA':<20} | {'TOT':<5} | {'MON':<5} | {'ASC':<5} | {'H10':<5} | {'NAT':<5} | {'CMB':<5} | {'MOON SIGN'}")
         print("-" * 120)
         
         for i, row in results_df.head(20).iterrows():
             ts = row['timestamp']
             # Format nicely
             print(f"{ts} | {row['score_total']:<5.1f} | {row['score_moon']:<5.1f} | {row['score_r_asc']:<5.1f} | {row['score_r_h10']:<5.1f} | {row.get('score_natal',0):<5.1f} | {row.get('score_comb',0):<5.1f} | {row['moon_sign']}")
             
    else:
        print("❌ No se encontraron candidatos válidos.")

if __name__ == "__main__":
    run_simulation()
