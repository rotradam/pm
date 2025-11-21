import pandas as pd
import requests
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data.database import AssetDatabase

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
                    "exchange": "CCC" # CryptoCompare/CoinGecko generic
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
        tables = pd.read_html(response.text, header=0)
        df = tables[0]
        logger.info(f"S&P 500 Table columns: {df.columns.tolist()}")
        
        # Find symbol column
        symbol_col = next((col for col in df.columns if 'Symbol' in col or 'Ticker' in col), None)
        security_col = next((col for col in df.columns if 'Security' in col or 'Company' in col), None)
        
        if not symbol_col or not security_col:
            logger.error(f"Could not find Symbol or Security column. Available: {df.columns}")
            return pd.DataFrame()
            
        assets = []
        for _, row in df.iterrows():
            ticker = row[symbol_col].replace('.', '-') # BRK.B -> BRK-B
            assets.append({
                "ticker": ticker,
                "name": row[security_col],
                "category": "Equities",
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
                "category": "Equities",
                "subcategory": "US Tech (NASDAQ 100)",
                "region": "USA",
                "currency": "USD",
                "exchange": "NASDAQ"
            })
        return pd.DataFrame(assets)
    except Exception as e:
        logger.error(f"Error fetching NASDAQ 100: {e}")
        return pd.DataFrame()

def get_manual_etfs():
    """Return a manually curated list of major ETFs."""
    logger.info("Adding curated ETFs...")
    etfs = [
        # US Equity
        {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "category": "ETF", "subcategory": "US Equity", "region": "USA"},
        {"ticker": "IVV", "name": "iShares Core S&P 500 ETF", "category": "ETF", "subcategory": "US Equity", "region": "USA"},
        {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "category": "ETF", "subcategory": "US Equity", "region": "USA"},
        {"ticker": "QQQ", "name": "Invesco QQQ Trust", "category": "ETF", "subcategory": "US Equity", "region": "USA"},
        {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "category": "ETF", "subcategory": "US Equity", "region": "USA"},
        
        # International Equity
        {"ticker": "VXUS", "name": "Vanguard Total International Stock ETF", "category": "ETF", "subcategory": "International Equity", "region": "Global"},
        {"ticker": "EFA", "name": "iShares MSCI EAFE ETF", "category": "ETF", "subcategory": "International Equity", "region": "Developed Markets"},
        {"ticker": "EEM", "name": "iShares MSCI Emerging Markets ETF", "category": "ETF", "subcategory": "International Equity", "region": "Emerging Markets"},
        
        # Fixed Income
        {"ticker": "AGG", "name": "iShares Core U.S. Aggregate Bond ETF", "category": "ETF", "subcategory": "Fixed Income", "region": "USA"},
        {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "category": "ETF", "subcategory": "Fixed Income", "region": "USA"},
        {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "category": "ETF", "subcategory": "Fixed Income", "region": "USA"},
        {"ticker": "LQD", "name": "iShares iBoxx $ Inv Grade Corporate Bond ETF", "category": "ETF", "subcategory": "Fixed Income", "region": "USA"},
        {"ticker": "HYG", "name": "iShares iBoxx $ High Yield Corporate Bond ETF", "category": "ETF", "subcategory": "Fixed Income", "region": "USA"},
        
        # Commodities & Real Estate
        {"ticker": "GLD", "name": "SPDR Gold Shares", "category": "ETF", "subcategory": "Commodities", "region": "Global"},
        {"ticker": "SLV", "name": "iShares Silver Trust", "category": "ETF", "subcategory": "Commodities", "region": "Global"},
        {"ticker": "USO", "name": "United States Oil Fund", "category": "ETF", "subcategory": "Commodities", "region": "Global"},
        {"ticker": "VNQ", "name": "Vanguard Real Estate ETF", "category": "ETF", "subcategory": "Real Estate", "region": "USA"},
    ]
    
    # Add defaults
    for etf in etfs:
        etf["currency"] = "USD"
        etf["exchange"] = "US"
        
    return pd.DataFrame(etfs)

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
        
    # 4. ETFs
    etf_df = get_manual_etfs()
    if not etf_df.empty:
        db.add_assets(etf_df)
        
    logger.info("Database population complete!")

if __name__ == "__main__":
    main()
