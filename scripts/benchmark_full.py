
import sys
import os
import time
from datetime import datetime
import logging

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.election_engine import VectorizedElectionFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_benchmark():
    logger.info("🏎️  STARTING 100-YEAR ELECTIONAL BENCHMARK (THE CENTURY RUN)")
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2125, 1, 1) # 100 Years
    
    finder = VectorizedElectionFinder()
    
    start_time = time.time()
    
    # Run Search
    df = finder.find_elections(start_date, end_date, topic="trabajo", interval_minutes=30)
    
    duration = time.time() - start_time
    
    # Stats
    total_moments = int((end_date - start_date).total_seconds() / (30*60))
    selected = len(df)
    percent = (selected / total_moments) * 100
    
    logger.info("-" * 40)
    logger.info(f"🏁 BENCHMARK COMPLETE")
    logger.info(f"   Time Range: 100 Years ({total_moments:,} moments analyzed)")
    logger.info(f"   Execution Time: {duration:.4f} seconds")
    logger.info(f"   Speed: {total_moments / duration:,.0f} moments/second")
    logger.info(f"   Candidates Found: {selected:,} ({percent:.2f}%)")
    logger.info("-" * 40)
    
    # Save sample
    if not df.empty:
        sample_path = 'benchmark_results_sample.csv'
        df.head(100).to_csv(sample_path)
        logger.info(f"   Saved top 100 candidates to {sample_path}")

if __name__ == "__main__":
    run_benchmark()
