"""
ISIN to ticker mapping and resolution.

Uses verified mappings from a JSON file. Falls back to heuristics for unmapped ISINs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class IsinMapper:
    """
    Maps ISINs to Yahoo Finance ticker symbols.
    
    Uses a verified mapping file created by manual research or ISIN lookup services.
    Falls back to heuristic patterns for unmapped ISINs.
    """
    
    def __init__(
        self, 
        verified_path: str = "data/isin_ticker_mapping_verified.json",
        overrides_path: str = "data/isin_ticker_overrides.json"
    ):
        """
        Initialize mapper with verified mappings and optional overrides.
        
        Args:
            verified_path: Path to JSON file with verified ISIN→ticker mappings
            overrides_path: Path to JSON file with manual overrides (takes precedence)
        """
        self.verified_path = Path(verified_path)
        self.overrides_path = Path(overrides_path)
        self.verified: Dict[str, str] = {}
        self.overrides: Dict[str, str] = {}
        
        # Load verified mappings
        if self.verified_path.exists():
            with open(self.verified_path, "r") as f:
                self.verified = json.load(f)
            logger.info(f"Loaded {len(self.verified)} verified ISIN→ticker mappings")
        else:
            logger.warning(f"No verified mappings file found at {self.verified_path}")
        
        # Load manual overrides (takes precedence)
        if self.overrides_path.exists():
            with open(self.overrides_path, "r") as f:
                self.overrides = json.load(f)
            logger.info(f"Loaded {len(self.overrides)} manual ISIN→ticker overrides")
        else:
            logger.debug("No manual overrides file found")
    
    def map_isin(self, isin: str, name: Optional[str] = None) -> Optional[str]:
        """
        Map a single ISIN to a Yahoo Finance ticker.
        
        Args:
            isin: The ISIN code
            name: Optional instrument name (for logging)
        
        Returns:
            Yahoo Finance ticker symbol, or None if not found
        """
        # Check manual overrides first (highest priority)
        if isin in self.overrides:
            logger.debug(f"Using manual override for {isin}")
            return self.overrides[isin]
        
        # Check verified mappings
        if isin in self.verified:
            return self.verified[isin]
        
        # No mapping found - return None and log warning
        logger.warning(f"No mapping found for ISIN {isin} ({name or 'unknown'})")
        logger.warning(f"  Add to {self.verified_path} or search manually on https://finance.yahoo.com/")
        return None
    
    def map_universe(self, universe_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a 'ticker' column to universe DataFrame.
        
        Args:
            universe_df: DataFrame with at least 'isin' and 'name' columns
        
        Returns:
            DataFrame with additional 'ticker' column (None for unmapped ISINs)
        """
        df = universe_df.copy()
        df["ticker"] = df.apply(
            lambda row: self.map_isin(row["isin"], row.get("name")),
            axis=1
        )
        
        mapped_count = df["ticker"].notna().sum()
        total_count = len(df)
        logger.info(f"Mapped {mapped_count}/{total_count} ISINs to tickers")
        
        if mapped_count < total_count:
            unmapped = df[df["ticker"].isna()][["isin", "name"]]
            logger.warning(f"\n{total_count - mapped_count} ISINs have no mapping:")
            for _, row in unmapped.head(10).iterrows():
                logger.warning(f"  {row['isin']}: {row['name']}")
            if len(unmapped) > 10:
                logger.warning(f"  ... and {len(unmapped) - 10} more")
        
        return df
    
    def save_overrides(self, mappings: Dict[str, str]):
        """
        Save manual ISIN→ticker overrides to file.
        
        Args:
            mappings: Dict of {isin: ticker}
        """
        self.overrides_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.overrides_path, "w") as f:
            json.dump(mappings, f, indent=2)
        logger.info(f"Saved {len(mappings)} overrides to {self.overrides_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mapper = IsinMapper()
    
    # Test a few sample ISINs
    test_isins = [
        ("IE00B4L5Y983", "iShares Core MSCI World"),  # Irish ISIN
        ("DE000A0H0728", "iShares Diversified Commodity"),  # German ISIN
        ("LU0274209237", "Xtrackers MSCI Europe"),  # Luxembourg ISIN
    ]
    
    for isin, name in test_isins:
        ticker = mapper.map_isin(isin, name)
        print(f"{isin} ({name}) → {ticker}")
