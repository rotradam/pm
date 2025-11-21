import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data.categories import CATEGORIES
from backend.data.prices import PriceFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_categories():
    logger.info("Testing Category Definitions...")
    total_tickers = 0
    for cat, tickers in CATEGORIES.items():
        logger.info(f"Category: {cat} ({len(tickers)} assets)")
        total_tickers += len(tickers)
        
    logger.info(f"Total Categories: {len(CATEGORIES)}")
    logger.info(f"Total Tickers: {total_tickers}")
    
    # Test fetching a few random tickers
    fetcher = PriceFetcher()
    test_tickers = ["AAPL", "BTC-USD", "^GSPC"]
    
    logger.info("\nTesting Price Fetcher with sample tickers...")
    for t in test_tickers:
        avail = fetcher.check_ticker_availability(t)
        logger.info(f"Ticker {t}: {'Available' if avail else 'Not Available'}")
        
    logger.info("\nVerification Complete.")

if __name__ == "__main__":
    test_categories()
