
import sys
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import logging

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.election_engine import VectorizedElectionFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def search_august():
    logger.info("🇦🇷 BÚSQUEDA ELECTIVA: AGOSTO 2025 (BUENOS AIRES)")
    
    # 1. Configurar Fechas (Local Time -> UTC)
    # Buenos Aires es UTC-3
    ba_offset = 3 
    
    local_start = datetime(2025, 8, 1, 0, 0)
    local_end = datetime(2025, 8, 31, 23, 59)
    
    # Convertir a UTC para el motor (SwissEph usa UT)
    utc_start = local_start + timedelta(hours=ba_offset)
    utc_end = local_end + timedelta(hours=ba_offset)
    
    logger.info(f"   Rango Local: {local_start} -> {local_end}")
    logger.info(f"   Rango UTC:   {utc_start} -> {utc_end}")
    
    finder = VectorizedElectionFinder()
    
    # 2. Ejecutar Búsqueda
    start_time = time.time()
    
    # Intervalo 10 minutos para mayor precisión
    df = finder.find_elections(utc_start, utc_end, topic="trabajo", interval_minutes=30)
    
    duration = time.time() - start_time
    
    # 3. Presentar Resultados
    logger.info("-" * 40)
    logger.info(f"🚀 VELOCIDAD DE PROCESAMIENTO")
    logger.info(f"   Tiempo Real: {duration:.4f} segundos")
    
    total_minutes = (utc_end - utc_start).total_seconds() / 60
    points = total_minutes / 30
    logger.info(f"   Puntos Analizados: {int(points)}")
    logger.info(f"   Candidatos Encontrados: {len(df)}")
    
    if not df.empty:
        logger.info("-" * 40)
        logger.info(f"🏆 MEJORES MOMENTOS (Hora Local Buenos Aires)")
        logger.info(f"   (Filtros: No Cap/Esc, No Vacía, Fase OK)")
        
        # Convertir UTC back to Local
        df['local_time'] = df['timestamp'] - timedelta(hours=ba_offset)
        
        # Agrupar por bloques contiguos
        # Si la diferencia entre row N y N-1 es 30 min, es el mismo bloque
        df['delta'] = df['local_time'].diff()
        df['block_id'] = (df['delta'] > timedelta(minutes=30)).cumsum()
        
        # Mostrar resumen por bloques
        blocks = []
        for bid, group in df.groupby('block_id'):
            start_block = group['local_time'].iloc[0]
            end_block = group['local_time'].iloc[-1]
            duration_hours = (end_block - start_block).total_seconds() / 3600
            
            blocks.append({
                "Inicio": start_block,
                "Fin": end_block,
                "Duración": f"{duration_hours:.1f}h",
                "Luna": group['moon_sign'].iloc[0] # Sign index roughly check
            })
            
        # Imprimir bloques
        for b in blocks:
            logger.info(f"   ✅ {b['Inicio'].strftime('%Y-%m-%d %H:%M')} a {b['Fin'].strftime('%H:%M')} ({b['Duración']})")
    else:
        logger.warning("   ❌ No se encontraron momentos aptos estricamente con estos filtros.")

if __name__ == "__main__":
    search_august()
