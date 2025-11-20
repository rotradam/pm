"""
Automated ISIN to Yahoo Finance ticker resolver using OpenFIGI API.

OpenFIGI is a free API that maps ISINs to ticker symbols across exchanges.
Rate limit: 25 requests per minute (free tier), 250/min with API key.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenFigiResolver:
    """
    Resolve ISINs to Yahoo Finance tickers using OpenFIGI API.
    
    OpenFIGI provides ISIN→ticker mappings for most global securities.
    Free tier: 25 requests/minute, no API key required.
    """
    
    BASE_URL = "https://api.openfigi.com/v3/mapping"
    RATE_LIMIT = 25  # requests per minute
    
    # Exchange mapping: OpenFIGI exchange → Yahoo Finance suffix
    EXCHANGE_SUFFIX = {
        "LN": ".L",      # London Stock Exchange
        "GY": ".DE",     # Xetra (Germany)
        "GR": ".DE",     # Deutsche Boerse Xetra
        "FP": ".PA",     # Euronext Paris
        "NA": ".AS",     # Euronext Amsterdam
        "SW": ".SW",     # SIX Swiss Exchange
        "IM": ".MI",     # Borsa Italiana (Milan)
        "SM": ".MC",     # Bolsa de Madrid
        "US": "",        # US exchanges (no suffix)
        "UN": "",        # NYSE
        "UW": "",        # Nasdaq
        "UP": "",        # NYSE Arca
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenFIGI resolver.
        
        Args:
            api_key: Optional API key for higher rate limits (250 req/min).
                     If not provided, will check OPENFIGI_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("OPENFIGI_API_KEY")
        if self.api_key:
            logger.info("Using OpenFIGI API key (250 req/min rate limit)")
            self.rate_limit = 250
        else:
            logger.info("No API key provided (25 req/min rate limit)")
            self.rate_limit = 25
        
        self.request_times: List[float] = []
        self.request_count = 0
        self.request_window_start = time.time()
        self.session = requests.Session()
        
        # Add API key to session headers if provided
        if self.api_key:
            self.session.headers.update({"X-OPENFIGI-APIKEY": self.api_key})
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        self.request_count += 1
        
        # Reset counter if more than 60 seconds have passed
        elapsed = time.time() - self.request_window_start
        if elapsed > 60:
            self.request_count = 1
            self.request_window_start = time.time()
            return
        
        # Wait if we've hit the rate limit
        if self.request_count >= self.rate_limit:
            wait_time = 60 - elapsed + 1  # Wait until next minute + 1 sec buffer
            logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            self.request_count = 1
            self.request_window_start = time.time()
            time.sleep(wait_time)
            self.request_count = 1
            self.request_window_start = time.time()
    
    def resolve_isin(self, isin: str) -> List[Dict]:
        """
        Resolve a single ISIN to ticker symbols.
        
        Args:
            isin: The ISIN code
        
        Returns:
            List of potential mappings with exchange, ticker, name, etc.
        """
        self._rate_limit()
        
        payload = [{
            "idType": "ID_ISIN",
            "idValue": isin
        }]
        
        try:
            response = self.session.post(
                self.BASE_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and "data" in data[0]:
                    return data[0]["data"]
                else:
                    logger.debug(f"No data returned for {isin}")
                    return []
            else:
                logger.warning(f"API error for {isin}: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error resolving {isin}: {e}")
            return []
    
    def resolve_to_yahoo_ticker(self, isin: str, name: str = "") -> Optional[str]:
        """
        Resolve ISIN to Yahoo Finance ticker format.
        
        Prefers liquid exchanges (London, Xetra, Paris) for European ETFs.
        
        Args:
            isin: The ISIN code
            name: Optional security name for better selection
        
        Returns:
            Yahoo Finance ticker or None
        """
        results = self.resolve_isin(isin)
        
        if not results:
            logger.warning(f"No mapping found for {isin} ({name})")
            return None
        
        # Prefer certain exchanges for ETFs
        preferred_exchanges = ["LN", "GY", "GR", "FP", "NA", "SW"]
        
        # Try to find a preferred exchange first
        for result in results:
            exchange_code = result.get("exchCode", "")
            ticker = result.get("ticker", "")
            security_type = result.get("securityType2", "")
            
            # For ETFs, prefer London or Xetra
            if security_type in ["ETF", "ETP"] and exchange_code in preferred_exchanges:
                suffix = self.EXCHANGE_SUFFIX.get(exchange_code, "")
                yahoo_ticker = f"{ticker}{suffix}"
                logger.info(f"✓ {isin} → {yahoo_ticker} ({exchange_code})")
                return yahoo_ticker
        
        # Fallback: use first result with a recognized exchange
        for result in results:
            exchange_code = result.get("exchCode", "")
            ticker = result.get("ticker", "")
            
            if exchange_code in self.EXCHANGE_SUFFIX:
                suffix = self.EXCHANGE_SUFFIX.get(exchange_code, "")
                yahoo_ticker = f"{ticker}{suffix}"
                logger.info(f"  {isin} → {yahoo_ticker} ({exchange_code})")
                return yahoo_ticker
        
        logger.warning(f"Could not map {isin} to Yahoo Finance format")
        return None
    
    def resolve_universe(
        self, 
        universe_df: pd.DataFrame,
        save_to: str = "data/isin_ticker_mapping_verified.json"
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Resolve all ISINs in a universe DataFrame.
        
        Args:
            universe_df: DataFrame with 'isin' and 'name' columns
            save_to: Path to save the mapping JSON
        
        Returns:
            Tuple of (DataFrame with 'ticker' column, mapping dict)
        """
        df = universe_df.copy()
        mappings = {}
        
        logger.info(f"Resolving {len(df)} ISINs...")
        
        for idx, row in df.iterrows():
            isin = row["isin"]
            name = row.get("name", "")
            
            # Check if already processed (for duplicates)
            if isin in mappings:
                logger.debug(f"Using cached mapping for {isin}")
                df.at[idx, "ticker"] = mappings[isin]
                continue
            
            ticker = self.resolve_to_yahoo_ticker(isin, name)
            if ticker:
                mappings[isin] = ticker
                df.at[idx, "ticker"] = ticker
            else:
                df.at[idx, "ticker"] = None
            
            # Progress update every 10 items
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx + 1}/{len(df)} ISINs processed")
        
        # Save mappings to JSON
        if save_to:
            output_path = Path(save_to)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump(mappings, f, indent=2, sort_keys=True)
            
            logger.info(f"Saved {len(mappings)} mappings to {output_path}")
        
        # Report statistics
        mapped_count = df["ticker"].notna().sum()
        logger.info(f"\n{'='*60}")
        logger.info(f"Mapping Results:")
        logger.info(f"  Total ISINs: {len(df)}")
        logger.info(f"  Successfully mapped: {mapped_count}")
        logger.info(f"  Failed: {len(df) - mapped_count}")
        logger.info(f"  Success rate: {mapped_count/len(df)*100:.1f}%")
        logger.info(f"{'='*60}\n")
        
        return df, mappings


def main():
    """Run the resolver on the universe CSV."""
    
    # Load universe
    universe_path = "documents/etf_universe_full_clean.csv"
    universe_df = pd.read_csv(universe_path)
    
    logger.info(f"Loaded {len(universe_df)} instruments from {universe_path}")
    logger.info(f"Unique ISINs: {universe_df['isin'].nunique()}")
    
    # Initialize resolver
    resolver = OpenFigiResolver()
    
    # Resolve all ISINs
    df_with_tickers, mappings = resolver.resolve_universe(
        universe_df,
        save_to="data/isin_ticker_mapping_verified.json"
    )
    
    # Save updated universe with tickers
    output_csv = "documents/etf_universe_with_tickers.csv"
    df_with_tickers.to_csv(output_csv, index=False)
    logger.info(f"Saved updated universe to {output_csv}")
    
    # Show unmapped ISINs
    unmapped = df_with_tickers[df_with_tickers["ticker"].isna()]
    if len(unmapped) > 0:
        logger.warning(f"\nUnmapped ISINs ({len(unmapped)}):")
        for _, row in unmapped.iterrows():
            logger.warning(f"  {row['isin']}: {row['name']}")
    
    return df_with_tickers, mappings


if __name__ == "__main__":
    df, mappings = main()
