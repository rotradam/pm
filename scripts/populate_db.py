import pandas as pd
import requests
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data.database import AssetDatabase
from scripts.data.asset_lists import BOND_ETFS, COMMODITY_ETFS, EQUITY_ETFS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_crypto_assets():
    """Fetch top 500 crypto assets from CoinGecko."""
    logger.info("Fetching Crypto assets from CoinGecko...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    all_coins = []
    
    # Fetch 2 pages of 250 coins each = 500 coins
    for page in range(1, 3):
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": "false"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for coin in data:
                # Yahoo Finance usually uses symbol-USD for crypto
                ticker = f"{coin['symbol'].upper()}-USD"
                all_coins.append({
                    "ticker": ticker,
                    "name": coin['name'],
                    "category": "Crypto",
                    "subcategory": "Top 500",
                    "region": "Global",
                    "currency": "USD",
                    "exchange": "CCC", # CryptoCompare/CoinGecko generic
                    "coingecko_id": coin['id']
                })
        except Exception as e:
            logger.error(f"Error fetching crypto page {page}: {e}")
            
    return pd.DataFrame(all_coins)

def fetch_sp500_assets():
    """Fetch S&P 500 companies from Wikipedia."""
    logger.info("Fetching S&P 500 assets from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = pd.read_html(response.text)
        
        df = pd.DataFrame()
        for table in tables:
            if 'Symbol' in table.columns and 'Security' in table.columns:
                df = table
                break
        
        if df.empty:
            logger.error("Could not find S&P 500 table")
            return pd.DataFrame()
            
        logger.info(f"S&P 500 Table columns: {df.columns.tolist()}")
        
        assets = []
        for _, row in df.iterrows():
            ticker = row['Symbol'].replace('.', '-') # BRK.B -> BRK-B
            assets.append({
                "ticker": ticker,
                "name": row['Security'],
                "category": "Stock", # Changed from Equities
                "subcategory": "US Large Cap (S&P 500)",
                "region": "USA",
                "currency": "USD",
                "exchange": "US"
            })
        return pd.DataFrame(assets)
    except Exception as e:
        logger.error(f"Error fetching S&P 500: {e}")
        return pd.DataFrame()

def fetch_nasdaq100_assets():
    """Fetch NASDAQ 100 companies from Wikipedia."""
    logger.info("Fetching NASDAQ 100 assets from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = pd.read_html(response.text)
        # Table index might vary, usually it's the 4th table (index 4) or check columns
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                df = table
                break
        else:
            logger.error("Could not find NASDAQ 100 table")
            return pd.DataFrame()
            
        col_name = 'Ticker' if 'Ticker' in df.columns else 'Symbol'
        company_col = 'Company' if 'Company' in df.columns else 'Security'
        
        assets = []
        for _, row in df.iterrows():
            ticker = row[col_name].replace('.', '-')
            assets.append({
                "ticker": ticker,
                "name": row[company_col],
                "category": "Stock", # Changed from Equities
                "subcategory": "US Tech (NASDAQ 100)",
                "region": "USA",
                "currency": "USD",
                "exchange": "NASDAQ"
            })
        return pd.DataFrame(assets)
    except Exception as e:
        logger.error(f"Error fetching NASDAQ 100: {e}")
        return pd.DataFrame()

def load_csv_etfs():
    """Load ETFs from the CSV file."""
    logger.info("Loading ETFs from CSV...")
    csv_path = Path(__file__).parent.parent / "documents" / "etf_universe_with_tickers.csv"
    if not csv_path.exists():
        logger.warning("ETF CSV not found.")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(csv_path)
        assets = []
        for _, row in df.iterrows():
            ticker = row['ticker']
            if pd.isna(ticker):
                continue
                
            # Determine category based on sector
            sector = str(row['sector'])
            category = "ETF"
            if "Bond" in sector:
                category = "Bond"
            elif any(x in sector for x in ["Commodity", "Gold", "Silver", "Oil", "Wheat", "Copper"]):
                category = "Commodity"
                
            assets.append({
                "ticker": ticker,
                "name": row['name'],
                "category": category,
                "subcategory": sector,
                "region": row['domicile'] if not pd.isna(row['domicile']) else "Global",
                "currency": row['currency'] if not pd.isna(row['currency']) else "USD",
                "exchange": "Global" # Simplified
            })
        return pd.DataFrame(assets)
    except Exception as e:
        logger.error(f"Error loading ETF CSV: {e}")
        return pd.DataFrame()

def get_curated_lists():
    """Return curated lists of assets."""
    logger.info("Adding curated asset lists...")
    
    # Process lists
    all_assets = []
    
    for item in BOND_ETFS:
        item["category"] = "Bond"
        item["currency"] = "USD"
        item["exchange"] = "US"
        all_assets.append(item)
        
    for item in COMMODITY_ETFS:
        item["category"] = "Commodity"
        item["currency"] = "USD"
        item["exchange"] = "US"
        all_assets.append(item)
        
    for item in EQUITY_ETFS:
        item["category"] = "ETF"
        item["currency"] = "USD"
        item["exchange"] = "US"
        all_assets.append(item)
        
    return pd.DataFrame(all_assets)

def main():
    db = AssetDatabase()
    
    # 1. Crypto
    crypto_df = fetch_crypto_assets()
    if not crypto_df.empty:
        db.add_assets(crypto_df)
        
    # 2. S&P 500
    sp500_df = fetch_sp500_assets()
    if not sp500_df.empty:
        db.add_assets(sp500_df)
        
    # 3. NASDAQ 100
    nasdaq_df = fetch_nasdaq100_assets()
    if not nasdaq_df.empty:
        db.add_assets(nasdaq_df)
        
    # 4. CSV ETFs
    csv_etf_df = load_csv_etfs()
    if not csv_etf_df.empty:
        db.add_assets(csv_etf_df)
        
    # 5. Curated Lists (Bonds, Commodities, ETFs)
    curated_df = get_curated_lists()
    if not curated_df.empty:
        db.add_assets(curated_df)
        
    logger.info("Database population complete!")

if __name__ == "__main__":
    main()
