import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class AssetDatabase:
    """
    Manages the SQLite database for the asset universe.
    """
    
    def __init__(self, db_path: str = "data/assets.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _get_conn(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Create assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                subcategory TEXT,
                region TEXT,
                currency TEXT,
                exchange TEXT,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        # Create indices for faster search
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON assets(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subcategory ON assets(subcategory)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON assets(name)")
        
        conn.commit()
        conn.close()
        
    def add_assets(self, assets_df: pd.DataFrame):
        """
        Add or update assets in the database.
        
        Args:
            assets_df: DataFrame with columns matching the table schema
        """
        conn = self._get_conn()
        # Ensure columns match
        expected_cols = ['ticker', 'name', 'category', 'subcategory', 'region', 'currency', 'exchange']
        for col in expected_cols:
            if col not in assets_df.columns:
                assets_df[col] = None
                
        # Upsert using pandas to_sql with replace is risky for existing data, 
        # but for this use case (re-populating), 'append' or manual upsert is better.
        # We'll use a loop for upsert to handle updates correctly.
        
        data = assets_df[expected_cols].to_dict('records')
        
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO assets (ticker, name, category, subcategory, region, currency, exchange)
            VALUES (:ticker, :name, :category, :subcategory, :region, :currency, :exchange)
        """, data)
        
        conn.commit()
        conn.close()
        logger.info(f"Added/Updated {len(assets_df)} assets in database.")
        
    def get_all_assets(self) -> pd.DataFrame:
        """Return all assets as a DataFrame."""
        conn = self._get_conn()
        df = pd.read_sql("SELECT * FROM assets WHERE active = 1", conn)
        conn.close()
        return df
        
    def search_assets(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Search assets by ticker or name.
        
        Args:
            query: Search string
            limit: Max results
        """
        conn = self._get_conn()
        sql = """
            SELECT * FROM assets 
            WHERE active = 1 AND (
                ticker LIKE ? OR 
                name LIKE ?
            )
            LIMIT ?
        """
        param = f"%{query}%"
        df = pd.read_sql(sql, conn, params=(param, param, limit))
        conn.close()
        return df
        
    def get_assets_by_category(self, category: str, subcategory: Optional[str] = None) -> pd.DataFrame:
        """Get assets filtered by category and optional subcategory."""
        conn = self._get_conn()
        if subcategory:
            sql = "SELECT * FROM assets WHERE active = 1 AND category = ? AND subcategory = ?"
            params = (category, subcategory)
        else:
            sql = "SELECT * FROM assets WHERE active = 1 AND category = ?"
            params = (category,)
            
        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        return df

    def get_categories(self) -> Dict[str, List[str]]:
        """Get a hierarchy of categories and subcategories."""
        conn = self._get_conn()
        df = pd.read_sql("SELECT DISTINCT category, subcategory FROM assets WHERE active = 1", conn)
        conn.close()
        
        result = {}
        for cat in df['category'].unique():
            subs = df[df['category'] == cat]['subcategory'].dropna().unique().tolist()
            result[cat] = subs
            
        return result
