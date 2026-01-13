
import sys
import os
import logging
import numpy as np
from datetime import datetime, timedelta

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.election_engine import VectorizedElectionFinder
from core.astro_config import AstroConfig
from core.theme_config import get_theme_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def debug_v2():
    logger.info("🐞 DEBUG V2 FILTERS")
    
    start_date = datetime(2025, 8, 15, 0, 0)
    end_date = datetime(2025, 8, 17, 0, 0) # 2 days
    
    # Buenos Aires
    lat, lon = -34.6037, -58.3816
    
    # NO Natal Chart
    natal_chart = None
    
    engine = VectorizedElectionFinder()
    
    # Manually run flow
    interval_minutes = 60
    total_time = end_date - start_date
    total_intervals = int(total_time.total_seconds() / (interval_minutes * 60))
    timestamps = [start_date + timedelta(minutes=i*interval_minutes) for i in range(total_intervals)]
    times_arr = np.array(timestamps)
    
    logger.info(f"Analyzing {len(times_arr)} moments...")
    
    # 1. Ephemeris
    bodies = [0, 1, 2, 3, 4, 5, 6, 10]
    positions = engine.ephemeris.calculate_positions(times_arr, bodies)
    longitudes = engine.ephemeris.get_longitudes(positions)
    
    # 2. Moon Filters
    moon_longs = longitudes[1]
    sun_longs = longitudes[0]
    
    mask_sign = engine.logic.mask_signs(moon_longs, [7, 9])
    mask_phase = engine.logic.mask_phase(sun_longs, moon_longs)
    mask_voc = engine.logic.mask_void_of_course(times_arr, moon_longs, longitudes)
    
    rejected_moon = mask_sign | mask_phase | mask_voc
    
    logger.info(f"Moon Rejections: {np.sum(rejected_moon)}/{len(times_arr)}")
    logger.info(f"  - Cap/Esc: {np.sum(mask_sign)}")
    logger.info(f"  - Phase:   {np.sum(mask_phase)}")
    logger.info(f"  - VoC:     {np.sum(mask_voc)}")
    
    # 3. Ruler Filters (Trabajo = House 10)
    cusps, ascmc = engine.houses.calculate_houses(times_arr, lat, lon)
    target_house = 10 
    cusp_longs = cusps[:, target_house - 1]
    cusp_signs = engine.logic.get_sign_indices(cusp_longs)
    
    is_bad_ruler = np.zeros(len(times_arr), dtype=bool)
    
    logger.info("Ruler Analysis (Trabajo/H10):")
    
    unique_signs = np.unique(cusp_signs)
    for s_idx in unique_signs:
        count = np.sum(cusp_signs == s_idx)
        ruler_id = engine.logic.get_ruler_for_sign(s_idx)
        logger.info(f"  - Cusp in Sign {s_idx} (Ruler {ruler_id}): {count} moments")
        
        # Check debility
        mask_times = (cusp_signs == s_idx)
        ruler_longs_subset = longitudes[ruler_id][mask_times]
        debility = engine.logic.mask_debility(ruler_id, ruler_longs_subset)
        
        bad_count = np.sum(debility)
        logger.info(f"    -> Ruler Debility: {bad_count}/{count}")
        
        is_bad_ruler[mask_times] = debility

    logger.info(f"Total Ruler Rejections: {np.sum(is_bad_ruler)}/{len(times_arr)}")
    
    # Final
    total_rejected = rejected_moon | is_bad_ruler
    passed = len(times_arr) - np.sum(total_rejected)
    
    logger.info(f"Total Passed: {passed}")

if __name__ == "__main__":
    debug_v2()
