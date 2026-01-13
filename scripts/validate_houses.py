
import sys
import os
import numpy as np
import logging
from datetime import datetime
import swisseph as swe

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vectorized_houses import VectorizedHouses
from core.astro_config import AstroConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_houses():
    logger.info("🏠 Verificando VectorizedHouses vs Direct SwissEph Call")
    
    # Config
    lat, lon = -34.6037, -58.3816 # Buenos Aires
    times = [datetime(2025, 8, 1, 12, 0, 0)] # 12:00 UTC (Local 9:00)
    
    vh = VectorizedHouses()
    
    # Calculate
    cusps, ascmc = vh.calculate_houses(np.array(times), lat, lon, system='P')
    
    asc_vec = ascmc[0][0]
    mc_vec = ascmc[0][1]
    
    logger.info(f"   ASC: {asc_vec:.6f}")
    logger.info(f"   MC:  {mc_vec:.6f}")
    
    # Verify logic manually (Direct check)
    jd = swe.julday(2025, 8, 1, 12.0)
    direct_cusps, direct_ascmc = swe.houses(jd, lat, lon, b'P')
    
    logger.info(f"   Direct ASC: {direct_ascmc[0]:.6f}")
    logger.info(f"   Direct MC:  {direct_ascmc[1]:.6f}")
    
    diff_asc = abs(asc_vec - direct_ascmc[0])
    
    if diff_asc < 0.000001:
        logger.info("✅ Validación Exitosa: Cúspides coinciden.")
    else:
        logger.error(f"❌ Validación Fallida: Diferencia {diff_asc}")

if __name__ == "__main__":
    validate_houses()
