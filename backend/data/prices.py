"""
Price data fetcher using Yahoo Finance.

Downloads and caches historical OHLC + adjusted close data for the universe.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class PriceFetcher:
    """
    Fetches and caches historical price data for a list of tickers.
    
    Uses yfinance to download daily OHLC data and stores it in Parquet format
    for fast subsequent reads.
    """
    
    def __init__(self, cache_dir: str = "data/prices"):
        """
        Initialize price fetcher with local cache directory.
        
        Args:
            cache_dir: Directory to store cached price data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Price cache directory: {self.cache_dir}")

    def check_ticker_availability(self, ticker: str) -> bool:
        """
        Check if a ticker is valid and has data available on Yahoo Finance.
        
        Args:
            ticker: Yahoo Finance ticker symbol
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to fetch 1 day of data
            t = yf.Ticker(ticker)
            # Fast check: history(period="1d")
            hist = t.history(period="1d")
            return not hist.empty
        except Exception as e:
            logger.warning(f"Ticker check failed for {ticker}: {e}")
            return False
    
    def fetch_ticker(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Fetch price data for a single ticker.
        
        Args:
            ticker: Yahoo Finance ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: If True, check cache before downloading
        
        Returns:
            DataFrame with columns [Open, High, Low, Close, Adj Close, Volume]
            indexed by date, or None if fetch fails
        """
        cache_file = self.cache_dir / f"{ticker.replace('/', '_')}_{start_date}_{end_date}.parquet"
        
        # Check cache
        if use_cache and cache_file.exists():
            logger.debug(f"Loading {ticker} from cache")
            return pd.read_parquet(cache_file)
        
        # Download from Yahoo Finance
        try:
            logger.info(f"Downloading {ticker} from {start_date} to {end_date}")
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return None
            
            # Save to cache
            df.to_parquet(cache_file)
            logger.debug(f"Cached {ticker} with {len(df)} rows")
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")
            return None
    
    def fetch_multiple(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch price data for multiple tickers.
        
        Args:
            tickers: List of Yahoo Finance ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: If True, check cache before downloading
        
        Returns:
            Dict mapping ticker → DataFrame; only includes successful fetches
        """
        results = {}
        failed = []
        
        logger.info(f"Fetching {len(tickers)} tickers from {start_date} to {end_date}")
        
        for i, ticker in enumerate(tickers, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(tickers)}")
            
            df = self.fetch_ticker(ticker, start_date, end_date, use_cache)
            if df is not None and not df.empty:
                results[ticker] = df
            else:
                failed.append(ticker)
        
        logger.info(f"Successfully fetched {len(results)}/{len(tickers)} tickers")
        if failed:
            logger.warning(f"Failed tickers ({len(failed)}): {', '.join(failed[:10])}"
                          + (f" and {len(failed)-10} more" if len(failed) > 10 else ""))
        
        return results
    
    def get_adjusted_close_matrix(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch adjusted close prices and return as a matrix.
        
        Args:
            tickers: List of Yahoo Finance ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: If True, check cache before downloading
        
        Returns:
            DataFrame indexed by date, columns = tickers, values = adjusted close prices
            Missing data is forward-filled then backward-filled
        """
        price_data = self.fetch_multiple(tickers, start_date, end_date, use_cache)
        
        if not price_data:
            raise ValueError("No price data could be fetched for any ticker")
        
        # Extract Adj Close for each ticker
        adj_close_dict = {}
        for ticker, df in price_data.items():
            if df is None or df.empty:
                continue
                
            # Handle multi-level columns (when yfinance returns them)
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(1, axis=1)
            
            if "Adj Close" in df.columns:
                adj_close_dict[ticker] = df["Adj Close"]
            elif "Close" in df.columns:
                # Fallback to Close if Adj Close not available
                logger.warning(f"{ticker}: Using Close instead of Adj Close")
                adj_close_dict[ticker] = df["Close"]
            else:
                logger.warning(f"{ticker}: No Close price column found")
        
        if not adj_close_dict:
            raise ValueError("No valid price data extracted from any ticker")
        
        # Combine into single DataFrame
        prices_df = pd.DataFrame(adj_close_dict)
        
        # Fill missing data (forward fill then backward fill)
        prices_df = prices_df.ffill().bfill()
        
        # Drop any columns that are still all NaN
        prices_df = prices_df.dropna(axis=1, how="all")
        
        logger.info(f"Price matrix shape: {prices_df.shape} "
                   f"({len(prices_df)} days × {len(prices_df.columns)} assets)")
        
        return prices_df

    def update_data(self, force: bool = False):
        """
        Trigger the data download process to update the cache.
        
        Args:
            force: If True, force re-download even if cached.
        """
        import subprocess
        import sys
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "download_data.py"
        logger.info(f"Running data update script: {script_path}")
        
        cmd = [sys.executable, str(script_path)]
        if force:
            cmd.append("--force")
            
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Data update completed successfully.")
            logger.debug(result.stdout)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Data update failed: {e}")
            logger.error(e.stderr)
            return False, e.stderr


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with a few sample tickers
    fetcher = PriceFetcher()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    test_tickers = ["IE00B4L5Y983.L", "DE000A0H0728.DE"]
    
    prices = fetcher.get_adjusted_close_matrix(test_tickers, start, end)
    print(f"\nFetched prices:\n{prices.head()}")
    print(f"\nShape: {prices.shape}")
