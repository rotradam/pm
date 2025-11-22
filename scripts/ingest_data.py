import sys
import os
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from backend.data.database import init_db, SessionLocal
from backend.data.ingestion.manager import IngestionManager
from backend.data.ingestion.crypto_ccxt import CCXTDataIngestionService
from backend.data.ingestion.stocks_yfinance import YFinanceDataIngestionService

def load_stock_tickers() -> List[Dict[str, Any]]:
    """
    Loads stock tickers from the verified mapping file.
    """
    try:
        with open("data/isin_ticker_mapping_verified.json", "r") as f:
            mapping = json.load(f)
            
        assets = []
        for isin, ticker in mapping.items():
            assets.append({
                "symbol": ticker.split(".")[0], # Simple symbol extraction
                "remote_ticker": ticker,
                "name": ticker, # We don't have names in the mapping, using ticker as placeholder
                "type": "ETF" if "ETF" in ticker or "ISHARES" in ticker else "STOCK", # Simple heuristic
                "identifiers": {"isin": isin}
            })
        return assets
    except FileNotFoundError:
        print("Warning: Ticker mapping file not found. Skipping stocks.")
        return []

# Monkey patch YFinance fetch_assets to use our loaded list
def patched_fetch_assets(self) -> List[Dict[str, Any]]:
    return load_stock_tickers()

YFinanceDataIngestionService.fetch_assets = patched_fetch_assets

from backend.data.models import Base
from backend.data.database import engine

from backend.data.ingestion.crypto_coingecko import CoinGeckoDiscoveryService
from backend.data.models import Asset

def run_ingestion():
    print("Resetting Database...")
    Base.metadata.drop_all(bind=engine)
    print("Initializing Database...")
    init_db()
    
    # 1. CoinGecko Discovery (Top 200)
    print("Running CoinGecko Discovery...")
    cg_service = CoinGeckoDiscoveryService(limit=200)
    manager = IngestionManager([cg_service])
    manager.run_discovery()

    # 2. Crypto Exchanges (Filtered by Discovered Assets)
    print("Configuring Crypto Services...")
    exchanges = ["binance", "kraken", "coinbase", "bybit"]
    services = []
    
    # Get list of discovered crypto symbols to filter against
    db = SessionLocal()
    crypto_assets = db.query(Asset).filter(Asset.type == "CRYPTO").all()
    allowed_symbols = {a.symbol for a in crypto_assets}
    db.close()
    
    print(f"Found {len(allowed_symbols)} crypto assets from CoinGecko. Fetching market data...")

    for exchange_id in exchanges:
        try:
            service = CCXTDataIngestionService(exchange_id)
            
            # Monkey patch fetch_assets to only return assets that are in our allowed list
            original_fetch = service.fetch_assets
            def filtered_fetch():
                all_assets = original_fetch()
                # Filter: Must be in allowed_symbols AND be a major pair (USDT/USD)
                filtered = []
                for a in all_assets:
                    # Check if base symbol (e.g. BTC from BTC/USDT) is in allowed list
                    base = a['symbol'] # CCXT returns base symbol here usually? No, wait. 
                    # CCXT fetch_assets implementation returns dict with 'symbol' as base. Let's check implementation.
                    
                    if a['symbol'] in allowed_symbols:
                         # Expanded filter to include USDC and EUR
                         if any(q in a['remote_ticker'] for q in ["/USDT", "/USD", "/USDC", "/EUR"]):
                             filtered.append(a)
                return filtered
            
            service.fetch_assets = filtered_fetch
            services.append(service)
        except Exception as e:
            print(f"Skipping {exchange_id}: {e}")

    # 3. Stocks/ETFs
    print("Configuring Stock Service...")
    stock_service = YFinanceDataIngestionService()
    services.append(stock_service)
    
    print("Starting Market Data Ingestion...")
    manager = IngestionManager(services)
    manager.run_discovery()
    
    print("Ingestion Complete!")

if __name__ == "__main__":
    run_ingestion()
