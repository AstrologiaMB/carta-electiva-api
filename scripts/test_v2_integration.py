
import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.election_engine import VectorizedElectionFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_v2():
    logger.info("🛠️ TEST INTEGRACIÓN V2 (Houses + Ruler + Natal)")
    
    start_date = datetime(2025, 8, 1, 0, 0)
    end_date = datetime(2025, 8, 5, 0, 0) # 4 days
    
    # Buenos Aires
    lat, lon = -34.6037, -58.3816
    
    # Dummy Natal Chart (Asc=0 Aries, Sun=0 Aries)
    # This means Transit Saturn/Mars at 0 Aries/Cancer/Libra/Cap IS BAD.
    natal_chart = {0: 0.0} 
    
    finder = VectorizedElectionFinder()
    
    # Run 1: No Filters (Baselne for these days) via V1 calls internal? 
    # V2 always runs House/Moon filters.
    
    # Run Search
    # Try AMOR (House 7).
    df = finder.find_elections(
        start_date, datetime(2025, 8, 10, 0, 0), lat, lon, 
        natal_chart=natal_chart, 
        topic="amor", # Themes: House 7, Venus
        interval_minutes=60
    )
    
    logger.info("-" * 30)
    logger.info(f"Candidates Found: {len(df)}")
    
    if len(df) > 0:
        logger.info("Sample:")
        print(df.head())
        logger.info("✅ V2 Integration seems to generate DataFrame correctly.")
    else:
        logger.warning("⚠️ No candidates found (Filters might be too strict or input data issues).")

if __name__ == "__main__":
    test_v2()
