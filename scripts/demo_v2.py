
import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.election_engine import VectorizedElectionFinder

import swisseph as swe

# Configure logging to show only results
logging.basicConfig(level=logging.ERROR)

def demo():
    print("🔮 DEMO MOTOR ELECTIVO V2 (Vectorizado)")
    print("---------------------------------------")
    
    # Configurar Búsqueda (Futura)
    start_date = datetime(2026, 2, 1, 0, 0)
    end_date = datetime(2026, 6, 1, 0, 0) # 4 meses para asegurar resultados
    topic = "amor" # Casa 7 (Venus)
    lat, lon = -34.6037, -58.3816 # Buenos Aires
    
    # Carta Natal Real (Usuario)
    # 26/12/1964 21:12 Buenos Aires (-3)
    # Convertimos a UTC para SwissEph
    # 21:12 Local = 00:12 UTC (del día 27)
    dob_local = datetime(1964, 12, 26, 21, 12)
    dob_utc = dob_local + timedelta(hours=3)
    
    # Calcular Julian Day
    t_utc = dob_utc.hour + dob_utc.minute/60.0
    jd_natal = swe.julday(dob_utc.year, dob_utc.month, dob_utc.day, t_utc)
    
    print(f"👤 Natal: {dob_local} (BA)")
    print("   Calculando posiciones natales...", end="")
    
    natal_chart = {}
    bodies = [0, 1, 2, 3, 4, 5, 6] # Sun..Sat
    for body in bodies:
        xx, _ = swe.calc_ut(jd_natal, body)
        natal_chart[body] = xx[0]
        
    print(" OK")
    # Debug: Mostrar Sol Natal
    print(f"   Sol Natal: {natal_chart[0]:.2f}°")
    
    print(f"📅 Rango Búsqueda: {start_date.date()} al {end_date.date()}")
    print(f"🎯 Tema: {topic.upper()}")
    print("---------------------------------------")
    
    # PASS 1: GENERIC (Sin Natal)
    print("\n🔎 PASO 1: Búsqueda Genérica (Sin carta natal)...")
    print("   (Busca buenos momentos 'para todo el mundo')")
    
    start_time = datetime.now()
    finder = VectorizedElectionFinder()
    df_generic = finder.find_elections(
        start_date, end_date, lat, lon, 
        natal_chart=None, # Sin natal
        topic=topic,
        interval_minutes=60 # Más rápido
    )
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"   ✅ Encontrados: {len(df_generic)} candidatos ({elapsed:.3f}s)")
    
    if not df_generic.empty:
        print("   Ejemplo: ", df_generic.iloc[0]['timestamp'])

    # PASS 2: PERSONALIZED
    print("\n🔎 PASO 2: Búsqueda Personalizada (Con tu carta)...")
    print("   (Filtra momentos peligrosos para TU mapa: e.g. Saturno Transitando vs Sol Natal)")
    
    start_time = datetime.now()
    df_person = finder.find_elections(
        start_date, end_date, lat, lon, 
        natal_chart=natal_chart,
        topic=topic,
        interval_minutes=60
    )
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"   ✅ Encontrados: {len(df_person)} candidatos ({elapsed:.3f}s)")
    
    if len(df_person) == 0 and len(df_generic) > 0:
        print("   ⚠️  NOTA: El sistema eliminó todos los candidatos genéricos por seguridad.")
        print("       Probable Causa: Saturno en Aries (2025/26) hace cuadratura a tu Sol en Capricornio.")
        print("       El motor te está protegiendo de iniciar en un momento de tensión vital.")
    
    print("---------------------------------------")

if __name__ == "__main__":
    demo()
