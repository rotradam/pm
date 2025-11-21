"""
Universe loader for ETF/ETC/Stock instruments.

Reads and validates the curated universe CSV and provides filtering capabilities.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd

from .database import AssetDatabase

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
        
        # Initialize database
        self.db = AssetDatabase()
        
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
        """
        Get the full universe as a DataFrame.
        Combines CSV universe, manual tickers, and DB assets.
        """
        # 1. Start with CSV universe
        combined_df = self.df.copy()
        
        # 2. Add DB assets
        try:
            db_assets = self.db.get_all_assets()
            if not db_assets.empty:
                # Map DB columns to Universe columns if needed, or just concat
                # Universe columns: sector, name, isin, wkn, notes
                # DB columns: ticker, name, category, subcategory, region, currency, exchange
                
                # We'll treat 'category' as 'sector'
                db_mapped = pd.DataFrame({
                    'sector': db_assets['category'],
                    'name': db_assets['name'],
                    'isin': db_assets['ticker'], # Using ticker as ISIN for now
                    'wkn': db_assets['ticker'],
                    'notes': db_assets['subcategory']
                })
                
                combined_df = pd.concat([combined_df, db_mapped], ignore_index=True)
        except Exception as e:
            logger.error(f"Error fetching assets from DB: {e}")
        
        # 3. Add manual tickers
        if self.manual_tickers:
            manual_df = pd.DataFrame(self.manual_tickers)
            combined_df = pd.concat([combined_df, manual_df], ignore_index=True)
            
        # Deduplicate by ISIN (Ticker)
        combined_df = combined_df.drop_duplicates(subset=['isin'], keep='last')
            
        return combined_df

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
