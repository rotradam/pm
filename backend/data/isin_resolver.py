"""
ISIN to Yahoo Finance ticker resolver.

Uses multiple strategies to find the correct Yahoo Finance ticker for an ISIN.
"""

import logging
from typing import Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class IsinTickerResolver:
    """
    Resolves ISINs to Yahoo Finance tickers using search and validation.
    """
    
    def __init__(self):
        # Manual overrides for known tickers (can be loaded from JSON)
        self.manual_overrides = {
            # Global Equity
            "IE00B4L5Y983": "IWDA.L",  # iShares Core MSCI World
            "IE00BJ0KDQ92": "XDWD.L",  # Xtrackers MSCI World
            "IE00BK5BQT80": "VWRL.L",  # Vanguard FTSE All-World
            "IE00B44Z5B48": "SPYY.L",  # SPDR MSCI ACWI
            "FR0010315770": "CW8.PA",  # Amundi MSCI World
            
            # Add more as needed...
        }
    
    def resolve(self, isin: str, name: str = "") -> Optional[str]:
        """
        Resolve ISIN to Yahoo Finance ticker.
        
        Strategy:
        1. Check manual overrides first
        2. Try to search Yahoo Finance
        3. Try common ticker patterns
        
        Args:
            isin: The ISIN code
            name: Optional instrument name for search
        
        Returns:
            Yahoo Finance ticker or None if not found
        """
        # Check manual overrides
        if isin in self.manual_overrides:
            ticker = self.manual_overrides[isin]
            logger.info(f"Using manual override for {isin}: {ticker}")
            return ticker
        
        # Try to search (this is a placeholder - Yahoo Finance doesn't have a good search API)
        # In production, you'd use OpenFIGI, Bloomberg, or similar services
        logger.warning(f"No mapping found for {isin} ({name})")
        return None
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Check if a ticker is valid by attempting to fetch recent data.
        
        Args:
            ticker: Yahoo Finance ticker symbol
        
        Returns:
            True if ticker is valid and has data
        """
        try:
            info = yf.Ticker(ticker).info
            return info is not None and len(info) > 0
        except Exception as e:
            logger.debug(f"Ticker {ticker} validation failed: {e}")
            return False


def create_manual_mapping_file():
    """
    Helper to create a starter manual mapping file.
    
    This should be expanded with real mappings from OpenFIGI or manual research.
    """
    import json
    from pathlib import Path
    
    # Known mappings (verified working on Yahoo Finance)
    known_mappings = {
        # Global Equity
        "IE00B4L5Y983": "IWDA.L",  # iShares Core MSCI World UCITS ETF
        "IE00BJ0KDQ92": "XDWD.L",  # Xtrackers MSCI World UCITS ETF 1C
        "IE00BK5BQT80": "VWRL.L",  # Vanguard FTSE All-World UCITS ETF
        "IE00B44Z5B48": "SPYY.L",  # SPDR MSCI ACWI UCITS ETF
        "FR0010315770": "CW8.PA",  # Amundi MSCI World UCITS ETF
        
        # Add more verified mappings here
        # Use: https://finance.yahoo.com/ to search by ISIN or name
    }
    
    output_file = Path("data/isin_ticker_mapping_verified.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(known_mappings, f, indent=2)
    
    print(f"Created {output_file} with {len(known_mappings)} verified mappings")
    print("\nTo add more mappings:")
    print("1. Search for the ETF on https://finance.yahoo.com/")
    print("2. Copy the ticker symbol (e.g., IWDA.L)")
    print("3. Add to the JSON file")


if __name__ == "__main__":
    # Create starter mapping file
    create_manual_mapping_file()
    
    # Test resolver
    resolver = IsinTickerResolver()
    test_isin = "IE00B4L5Y983"
    ticker = resolver.resolve(test_isin, "iShares Core MSCI World")
    print(f"\nTest: {test_isin} -> {ticker}")
    
    if ticker:
        is_valid = resolver.validate_ticker(ticker)
        print(f"Ticker {ticker} valid: {is_valid}")
