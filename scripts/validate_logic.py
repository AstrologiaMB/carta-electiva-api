
import sys
import os
import json
import numpy as np
import logging
from datetime import datetime, timedelta

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vectorized_ephemeris import VectorizedEphemeris
from core.vectorized_logic import VectorizedLogic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_logic():
    logger.info("🧠 Starting Logic Verification: Vectorized vs Legacy")
    
    # 1. Load Baseline Data
    baseline_path = os.path.join(os.path.dirname(__file__), 'baseline_truth_phase1.json')
    with open(baseline_path, 'r') as f:
        baseline_data = json.load(f)
        
    timestamps = [datetime.fromisoformat(d['timestamp']) for d in baseline_data]
    # Handle timezone again: Baseline timestamps are presumably correct inputs for vector engine if treated as UTC
    # Wait, in generate_baseline we used current_time as input. Legacy wrapper assumes Local.
    # So we must shift +3h.
    timestamps_utc = [t + timedelta(hours=3) for t in timestamps]
    times_arr = np.array(timestamps_utc)
    
    # 2. Vectorized Calculation
    logger.info(f"⚡ Calculating for {len(baseline_data)} moments...")
    
    ve = VectorizedEphemeris()
    vl = VectorizedLogic()
    
    # Needs Sun(0) to Saturn(6) and Moon(1)
    bodies = [0, 1, 2, 3, 4, 5, 6]
    positions = ve.calculate_positions(times_arr, bodies)
    longitudes = ve.get_longitudes(positions)
    
    # 3. Apply Filters
    # Filter 1: Signs (Moon in Cap/Esc)
    # Scorpio=7, Capricorn=9
    mask_sign = vl.mask_signs(longitudes[1], [7, 9])
    
    # Filter 2: Phase (New/Full Moon)
    mask_phase = vl.mask_phase(longitudes[0], longitudes[1], orb=8.0)
    
    # Filter 3: Void of Course
    # We use FULL planet list (legacy bug ignored).
    mask_voc = vl.mask_void_of_course(times_arr, longitudes[1], longitudes)
    
    # Combined Rejection (Any of these True -> Rejected)
    # EXCEPT: Legacy has exceptions.
    # Legacy: 
    # - Cap/Esc: Always Reject (unless mutual reception? Code said no).
    # - VoC: Reject UNLESS Taurus/Cancer.
    
    # Adjust VoC mask for exceptions (Taurus=1, Cancer=3)
    moon_signs = vl.get_sign_indices(longitudes[1])
    is_tau_canc = np.isin(moon_signs, [1, 3])
    # If Tau/Canc, then VoC is NOT a problem
    mask_voc_effective = mask_voc & (~is_tau_canc)
    
    # Final Vector Decision
    # Why is "luna_capricornio_escorpio" a reason?
    # Because mask_sign is True.
    
    vector_rejected = mask_sign | mask_phase | mask_voc_effective
    
    # 4. Compare with Baseline
    logger.info("\n📊 Comparison Analysis:")
    
    matches = 0
    false_positives = 0 # Vector rejected, Legacy accepted
    false_negatives = 0 # Vector accepted, Legacy rejected
    
    mismatches = []
    
    for i, entry in enumerate(baseline_data):
        legacy_valid = entry['is_valid_phase1']
        vector_valid = not vector_rejected[i]
        
        legacy_reason = entry['reject_reason']
        
        if legacy_valid == vector_valid:
            matches += 1
        else:
            # Diagnose mismatch
            diagnosis = ""
            if not vector_valid: # Vector Rejected
                if mask_sign[i]: diagnosis += "[Moon Sign] "
                if mask_phase[i]: diagnosis += "[Moon Phase] "
                if mask_voc_effective[i]: diagnosis += "[VoC] "
            
            mismatches.append({
                "time": timestamps[i].isoformat(),
                "legacy": f"{legacy_valid} ({legacy_reason})",
                "vector": f"{vector_valid} ({diagnosis})"
            })
            
            if vector_valid: false_negatives += 1
            else: false_positives += 1
            
    accuracy = (matches / len(baseline_data)) * 100
    logger.info(f"   Accuracy: {accuracy:.2f}%")
    logger.info(f"   Matches: {matches}/{len(baseline_data)}")
    logger.info(f"   False Positives (Vector Too Strict): {false_positives}")
    logger.info(f"   False Negatives (Vector Too Loose): {false_negatives}")
    
    if len(mismatches) > 0:
        logger.info("\n🔍 Top 10 Mismatches:")
        for m in mismatches[:10]:
            logger.info(f"   {m['time']}: Legacy={m['legacy']} vs Vector={m['vector']}")
            
    return accuracy > 95.0

if __name__ == "__main__":
    validate_logic()
