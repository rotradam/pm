"""
Universe loader for ETF/ETC/Stock instruments.

Reads and validates the curated universe CSV and provides filtering capabilities.
"""

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class Universe:
    """
    Manages the investment universe loaded from CSV.
    
    The universe CSV should have columns: sector, name, isin, wkn, notes.
    ISIN is treated as the primary unique identifier.
    """
    
    def __init__(self, csv_path: str = "documents/etf_universe_full_clean.csv"):
        """
        Load and validate the universe CSV.
        
        Args:
            csv_path: Path to the universe CSV file (relative to project root)
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Universe CSV not found at {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        self._validate()
        
        # Store manually added tickers
        self.manual_tickers = []
        
        logger.info(f"Loaded universe with {len(self.df)} instruments across "
                   f"{self.df['sector'].nunique()} sectors")
    
    def _validate(self):
        """Validate required columns and uniqueness constraints."""
        required_cols = {"sector", "name", "isin"}
        missing = required_cols - set(self.df.columns)
        if missing:
            raise ValueError(f"Missing required columns in universe CSV: {missing}")
        
        # Check for duplicate ISINs
        dupes = self.df[self.df["isin"].duplicated(keep=False)]
        if not dupes.empty:
            logger.warning(f"Found {len(dupes)} duplicate ISINs:")
            logger.warning(dupes[["isin", "name"]].to_string())
        
        # Drop any rows with missing ISIN
        missing_isin = self.df["isin"].isna().sum()
        if missing_isin > 0:
            logger.warning(f"Dropping {missing_isin} rows with missing ISIN")
            self.df = self.df.dropna(subset=["isin"])
    
    def get_all(self) -> pd.DataFrame:
        """Return the full universe DataFrame, including manual tickers."""
        df = self.df.copy()
        
        if self.manual_tickers:
            manual_df = pd.DataFrame(self.manual_tickers)
            df = pd.concat([df, manual_df], ignore_index=True)
            
        return df

    def add_manual_tickers(self, tickers: List[str]):
        """
        Add manual tickers to the universe.
        
        Args:
            tickers: List of ticker strings
        """
        new_tickers = []
        existing_tickers = set(self.df["isin"].tolist()) # Assuming ISIN column holds tickers for now, or we map later.
        # Wait, the CSV has 'isin', but manual tickers are 'tickers'.
        # The system maps ISIN -> Ticker later.
        # For manual tickers, we can assume ISIN=Ticker for simplicity in this context, 
        # or we need to handle the 'ticker' column if it exists.
        # Let's check if 'ticker' column exists in self.df.
        # The csv has 'sector', 'name', 'isin', 'wkn', 'notes'.
        # The mapping happens in 'mapper.py'.
        
        # To make this work seamlessly, I'll add them as rows with isin=ticker, name=ticker, sector='Manual'.
        
        for t in tickers:
            # Check if already in manual list
            if any(d['isin'] == t for d in self.manual_tickers):
                continue
            
            new_tickers.append({
                "sector": "Manual",
                "name": t,
                "isin": t, # Treat ticker as ISIN for manual entries
                "wkn": "MANUAL",
                "notes": "User added"
            })
            
        self.manual_tickers.extend(new_tickers)
        logger.info(f"Added {len(new_tickers)} manual tickers")
    
    def filter_by_sector(self, sectors: List[str]) -> pd.DataFrame:
        """
        Filter universe by one or more sectors.
        
        Args:
            sectors: List of sector names (e.g., ['Global Equity', 'EM Equity'])
        
        Returns:
            Filtered DataFrame containing only instruments in the specified sectors
        """
        filtered = self.df[self.df["sector"].isin(sectors)]
        logger.info(f"Filtered to {len(filtered)} instruments from sectors: {sectors}")
        return filtered.copy()
    
    def get_isins(self, sectors: Optional[List[str]] = None) -> List[str]:
        """
        Get list of ISINs, optionally filtered by sector.
        
        Args:
            sectors: Optional list of sectors to filter by
        
        Returns:
            List of ISIN strings
        """
        if sectors:
            df = self.filter_by_sector(sectors)
        else:
            df = self.df
        return df["isin"].tolist()
    
    def get_sectors(self) -> List[str]:
        """Return list of unique sectors in the universe."""
        return sorted(self.df["sector"].unique().tolist())


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    universe = Universe()
    print(f"\nTotal instruments: {len(universe.get_all())}")
    print(f"\nSectors: {universe.get_sectors()}")
    print(f"\nSample (first 5):")
    print(universe.get_all().head())
