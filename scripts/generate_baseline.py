
import sys
import os
import json
import logging
from datetime import datetime, timedelta
import numpy as np

# Add parent directory to path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.algoritmo_busqueda import AlgoritmoBusqueda, procesar_momento_fase1_estatico
from core.legacy_wrapper import LegacyAstroWrapper

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_baseline():
    """
    Generates baseline truth data for August 2025, Buenos Aires.
    Captures:
    1. Phase 1 filtering results (Pass/Fail + Reason) for every 30 mins.
    2. Detailed Phase 2 scores for passing moments.
    """
    
    # 1. Configuration
    start_date = datetime(2025, 8, 1, 0, 0)
    end_date = datetime(2025, 8, 31, 23, 59)
    lat = -34.6037
    lon = -58.3816
    topic = "trabajo" # Default topic
    
    # Dummy natal chart (needed for initialization but not used for general planetary positions)
    carta_natal_A = {
        "fecha_nacimiento": datetime(1990, 1, 1),
        "lat_nacimiento": lat,
        "lon_nacimiento": lon
    }

    logger.info(f"🚀 Starting Baseline Generation: {start_date} to {end_date}")
    logger.info(f"📍 Location: Lat {lat}, Lon {lon}")

    # 2. Iterate Phase 1 (Scalar Loop Simulation)
    # We re-implement the loop to capture data, instead of calling the class method which just filters
    
    baseline_data = []
    
    current_time = start_date
    count = 0
    
    while current_time <= end_date:
        count += 1
        if count % 100 == 0:
            logger.info(f"Processed {count} moments...")

        # Create wrapper
        # We need to capture exact positions here if possible, but LegacyAstroWrapper hides them inside objects
        # For now, we capture the Pass/Fail verdict
        
        is_valid = True
        reject_reason = None
        
        try:
            wrapper = LegacyAstroWrapper(current_time, lat, lon)
            is_rejected, reason = wrapper.es_momento_critico_descalificado()
            
            if is_rejected:
                is_valid = False
                reject_reason = reason
            
            # If Valid, get detailed score (Simulate Phase 2)
            score_data = {}
            if is_valid:
                # We instantiate AlgoritmoBusqueda just to access helper methods if needed
                # But here we can use the wrapper's detail methods
                luna_res = wrapper.evaluar_luna_completo()
                
                pass # TODO: Capture more details if needed
                
            entry = {
                "timestamp": current_time.isoformat(),
                "is_valid_phase1": is_valid,
                "reject_reason": reject_reason
            }
            
            # OPTIONAL: Capture Raw Moon Longitude for calibration
            # This requires peeking into the wrapper internals
            try:
                # Access internal moon object from immanuel
                moon_obj = wrapper.moon_module.object_json['3000001'] # Moon ID in Immanuel? No, check moon_aptitude
                # Actually legacy_wrapper exposes objects_json
                # Moon ID is usually 3000001 or similar in Immanuel consts
                pass
            except:
                pass

            baseline_data.append(entry)

        except Exception as e:
            logger.error(f"Error processing {current_time}: {e}")
            
        current_time += timedelta(minutes=30)

    # 3. Save to File
    output_file = os.path.join(os.path.dirname(__file__), 'baseline_truth_phase1.json')
    with open(output_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
        
    logger.info(f"✅ Baseline generated with {len(baseline_data)} records.")
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    generate_baseline()
