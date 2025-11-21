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
                coingecko_id TEXT,
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
        expected_cols = ['ticker', 'name', 'category', 'subcategory', 'region', 'currency', 'exchange', 'coingecko_id']
        for col in expected_cols:
            if col not in assets_df.columns:
                assets_df[col] = None
                
        # Upsert using pandas to_sql with replace is risky for existing data, 
        # but for this use case (re-populating), 'append' or manual upsert is better.
        # We'll use a loop for upsert to handle updates correctly.
        
        data = assets_df[expected_cols].to_dict('records')
        
        cursor = conn.cursor()
        
        # Check if column exists (migration hack for dev)
        try:
            cursor.execute("SELECT coingecko_id FROM assets LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migrating database: Adding coingecko_id column")
            cursor.execute("ALTER TABLE assets ADD COLUMN coingecko_id TEXT")
            conn.commit()
            
        cursor.executemany("""
            INSERT OR REPLACE INTO assets (ticker, name, category, subcategory, region, currency, exchange, coingecko_id)
            VALUES (:ticker, :name, :category, :subcategory, :region, :currency, :exchange, :coingecko_id)
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
        
    def get_asset_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Get a single asset by its ticker (exact match).
        """
        conn = self._get_conn()
        sql = "SELECT * FROM assets WHERE ticker = ? AND active = 1"
        df = pd.read_sql(sql, conn, params=(ticker,))
        conn.close()
        
        if df.empty:
            return None
            
        return df.iloc[0].to_dict()

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
            ORDER BY length(ticker) ASC, ticker ASC
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

    def get_filtered_assets(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        exchange: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0
    ) -> pd.DataFrame:
        """
        Get assets with multiple filters and sorting.
        """
        conn = self._get_conn()
        
        query = "SELECT * FROM assets WHERE active = 1"
        params = []
        
        if search:
            query += " AND (ticker LIKE ? OR name LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
            
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
            
        if region:
            query += " AND region = ?"
            params.append(region)
            
        if exchange:
            query += " AND exchange = ?"
            params.append(exchange)
            
        # Whitelist sort columns to prevent SQL injection
        valid_sort_cols = ["ticker", "name", "category", "subcategory", "region", "exchange"]
        if sort_by in valid_sort_cols:
            order = "DESC" if sort_order.lower() == "desc" else "ASC"
            query += f" ORDER BY {sort_by} {order}"
        else:
            query += " ORDER BY ticker ASC"
            
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
