
import sys
import os
import numpy as np
import logging

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vectorized_logic import VectorizedLogic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_rulerships():
    logger.info("👑 Validando Lógica de Regencias y Dignidades")
    
    vl = VectorizedLogic()
    
    # Caso 1: Marte (ID 4)
    # Domicilios: Aries(0), Scorpio(7)
    # Exaltación: Capricorn(9)
    # Caída: Cancer(3)
    # Exilio: Libra(6), Taurus(1)
    
    # Test array: [Aries, Taurus, Cancer, Libra, Scorpio, Capricorn]
    # Degrees: 15, 45, 105, 195, 225, 285
    test_longitudes = np.array([15.0, 45.0, 105.0, 195.0, 225.0, 285.0])
    
    mars_id = 4
    
    dignity_mask = vl.mask_dignity(mars_id, test_longitudes)
    debility_mask = vl.mask_debility(mars_id, test_longitudes)
    
    # Expected Dignity (0=Aries, 4=Sco, 5=Cap) -> Indices 0, 4, 5 SHOULD BE TRUE
    expected_dignity = np.array([True, False, False, False, True, True])
    
    # Expected Debility (1=Tau, 2=Canc, 3=Lib) -> Indices 1, 2, 3 SHOULD BE TRUE
    expected_debility = np.array([False, True, True, True, False, False])
    
    logger.info(f"   Mars Dignity: {dignity_mask}")
    logger.info(f"   Expected:       {expected_dignity}")
    
    if np.array_equal(dignity_mask, expected_dignity):
         logger.info("   ✅ Dignity Logic OK")
    else:
         logger.error("   ❌ Dignity Logic FAILED")
         
    logger.info(f"   Mars Debility: {debility_mask}")
    logger.info(f"   Expected:        {expected_debility}")

    if np.array_equal(debility_mask, expected_debility):
         logger.info("   ✅ Debility Logic OK")
    else:
         logger.error("   ❌ Debility Logic FAILED")

if __name__ == "__main__":
    validate_rulerships()
