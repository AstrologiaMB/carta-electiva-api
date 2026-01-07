
import sys
import os
import numpy as np
import logging
from datetime import datetime, timedelta
import pandas as pd
import json

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vectorized_ephemeris import VectorizedEphemeris
from core.legacy_wrapper import LegacyAstroWrapper
from immanuel.const import chart as immanuel_chart

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_core():
    logger.info("🔭 Starting Verification: Vectorized Core vs Legacy Engine")
    
    # 1. Setup Sample Data (100 random moments in Aug 2025)
    start_date = datetime(2025, 8, 1)
    moments = [start_date + timedelta(minutes=np.random.randint(0, 44000)) for _ in range(50)]
    moments = sorted(moments)
    
    times_arr = np.array(moments)
    
    # 2. Run Vectorized Engine
    logger.info(f"⚡ Running Vectorized Engine for {len(moments)} moments...")
    ve = VectorizedEphemeris()
    
    # Calculate for Sun(0) and Moon(1)
    bodies = [0, 1] 
    
    
    # ADJUSTMENT: Legacy Engine treats input datetime as Local Time (Buenos Aires UTC-3)
    # Vectorized Engine expects UTC (or whatever is passed).
    # So if we pass 12:00 to Legacy, it thinks 15:00 UTC.
    # We must pass 15:00 UTC to Vectorized to match.
    # Buenos Aires is UTC-3.
    # Convert numpy array of objects back to simple list for arithmetic if needed or use pandas
    # Simplest: List comprehension
    utc_shifted = [t + timedelta(hours=3) for t in times_arr]
    times_arr_utc = np.array(utc_shifted)
    
    start_time = datetime.now()
    vec_results = ve.calculate_positions(times_arr_utc, bodies)
    vec_duration = (datetime.now() - start_time).total_seconds()
    
    vec_sun_longs = vec_results[0][:, 0]
    vec_moon_longs = vec_results[1][:, 0]
    
    logger.info(f"   Vectorized Time: {vec_duration:.4f}s")
    
    # 3. Run Legacy Engine (Ground Truth)
    logger.info(f"🐢 Running Legacy Engine (Scalar Loop)...")
    
    legacy_sun_longs = []
    legacy_moon_longs = []
    
    start_time = datetime.now()
    lat, lon = -34.6037, -58.3816
    
    for t in moments:
        # Legacy wrapper instantiation
        wrapper = LegacyAstroWrapper(t, lat, lon)
        
        # Access internal immanuel objects
        # Sun = 3000000, Moon = 3000001
        # NOTE: Immanuel might store them as strings or ints depending on version.
        # Checking `moonAptitude` used `chart.SUN` which maps to key.
        
        # Look into objects_json which is what legacy wrapper prepares
        # It is stored in moon_module
        sun_data = wrapper.moon_module.object_json[str(immanuel_chart.SUN)]
        moon_data = wrapper.moon_module.object_json[str(immanuel_chart.MOON)]
        
        legacy_sun_longs.append(sun_data['longitude']['raw'])
        legacy_moon_longs.append(moon_data['longitude']['raw'])
        
    legacy_duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"   Legacy Time: {legacy_duration:.4f}s")
    
    # 4. Compare
    logger.info("\n📊 Comparison Results (Sun & Moon):")
    
    legacy_sun_arr = np.array(legacy_sun_longs)
    legacy_moon_arr = np.array(legacy_moon_longs)
    
    # Circular Difference Logic (0-360 wrap)
    diff_sun = np.abs(vec_sun_longs - legacy_sun_arr)
    diff_sun = np.minimum(diff_sun, 360 - diff_sun)
    
    diff_moon = np.abs(vec_moon_longs - legacy_moon_arr)
    diff_moon = np.minimum(diff_moon, 360 - diff_moon)
    
    max_diff_sun = np.max(diff_sun)
    max_diff_moon = np.max(diff_moon)
    
    logger.info(f"   Max Diff Sun:  {max_diff_sun:.6f}°")
    logger.info(f"   Max Diff Moon: {max_diff_moon:.6f}°")
    
    TOLERANCE = 0.0001
    
    if max_diff_sun < TOLERANCE and max_diff_moon < TOLERANCE:
        logger.info("\n✅ SUCCESS: Vectorized Engine matches Legacy within tolerance.")
        logger.info(f"   Speedup Factor: {legacy_duration / vec_duration:.1f}x (on sample)")
        return True
    else:
        logger.error("\n❌ FAILURE: Differences exceed tolerance!")
        # Print first mismatch
        for i in range(len(moments)):
            if diff_moon[i] > TOLERANCE:
                logger.error(f"   Mismatch at {moments[i]}: Vec={vec_moon_longs[i]} vs Legacy={legacy_moon_longs[i]}")
                break
        return False

if __name__ == "__main__":
    validate_core()
