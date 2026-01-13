
import sys
import os
import numpy as np
import logging

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vectorized_natal import VectorizedNatal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_natal():
    logger.info("🌳 Validando Integración Natal (Enraizamiento)")
    
    vn = VectorizedNatal()
    
    # Setup
    # Natal Sun at 0 Aries (0.0)
    natal_chart = {0: 0.0}
    
    # Transiting Saturn loops 350 -> 400 (350..360, 0..40)
    # Range covering Conjunction aspect (0)
    # Array from 350 to 370 (10 deg Aries) step 1
    t_saturn = np.arange(350, 370, 1.0) % 360
    
    # Dict of transits
    transits = {6: t_saturn} # 6=Saturn
    
    # Logic: Saturn Conjunct Sun is BAD (Hard Aspect to Light)
    # Orb is 8.0 (from Config).
    # So angles [352..360] and [0..8] should be BAD.
    # Angles [350..351] (Distance 9-10) should be GOOD (False).
    # Angles [9..10] should be GOOD (False).
    
    mask = vn.mask_hard_aspects_to_natal_lights(transits, natal_chart, malefics=[6])
    
    logger.info(f"   Natal Sun: 0.0")
    logger.info(f"   Transit Saturn: {t_saturn}")
    logger.info(f"   Hard Aspect Mask: {mask}")
    
    # Manual verification
    # Distances to 0:
    # 350 -> 10 (False)
    # 351 -> 9  (False)
    # 352 -> 8  (True) ... 
    # 0 -> 0 (True)
    # 8 -> 8 (True)
    # 9 -> 9 (False)
    
    indices_true = np.where(mask)[0]
    indices_false = np.where(~mask)[0]
    
    # Angles expected True: 352, 353... 359, 0, 1... 8.
    # From input array: 
    # 350(0), 351(1) -> False
    # 352(2) -> True
    # ...
    # 360=0(10) -> True
    # 8(18) -> True
    # 9(19) -> False
    
    idx_start_bad = 2 # 352
    idx_end_bad = 18 # 8
    
    passed = True
    if not np.all(mask[idx_start_bad:idx_end_bad+1]): 
        passed = False
        logger.error("   ❌ Expected range to be True")

    if mask[0]: passed = False; logger.error("   ❌ Index 0 should be False")
    if mask[-1]: passed = False; logger.error("   ❌ Index -1 should be False")
    
    if passed:
        logger.info("✅ Validación Exitosa: Máscara Natal detecta orbes correctamente.")
    else:
        logger.error("❌ Validación Fallida.")

if __name__ == "__main__":
    validate_natal()
