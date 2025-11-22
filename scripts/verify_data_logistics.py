import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from backend.data.database import init_db, SessionLocal
from backend.data.ingestion.manager import IngestionManager
from backend.data.ingestion.crypto_ccxt import CCXTDataIngestionService
from backend.data.asset_service import AssetService

def run_verification():
    print("Initializing Database...")
    init_db()
    
    print("Setting up Ingestion Manager with Kraken (smaller than Binance for test)...")
    # Using Kraken as it's usually reliable and has fewer pairs than Binance for a quick test
    kraken_service = CCXTDataIngestionService("kraken")
    manager = IngestionManager([kraken_service])
    
    print("Running Discovery (this might take a moment)...")
    # We'll mock the fetch_assets to only return a few assets to avoid hitting rate limits or taking too long
    # Monkey patching for verification speed
    original_fetch = kraken_service.fetch_assets
    
    def mocked_fetch_assets():
        print("Using mocked fetch for speed...")
        return [
            {
                "symbol": "BTC",
                "remote_ticker": "BTC/USD",
                "name": "Bitcoin/USD",
                "type": "CRYPTO",
                "identifiers": {"id": "bitcoin"}
            },
            {
                "symbol": "ETH",
                "remote_ticker": "ETH/USD",
                "name": "Ethereum/USD",
                "type": "CRYPTO",
                "identifiers": {"id": "ethereum"}
            }
        ]
    
    kraken_service.fetch_assets = mocked_fetch_assets
    
    manager.run_discovery()
    
    print("Simulating Market Data Update...")
    # Manually add some market data for testing since we didn't implement the full update loop yet
    db = SessionLocal()
    from backend.data.models import AssetMapping, MarketData
    
    mapping = db.query(AssetMapping).filter(AssetMapping.remote_ticker == "BTC/USD").first()
    if mapping:
        data = MarketData(
            asset_mapping_id=mapping.id,
            date=datetime.now(),
            close=50000.0,
            volume=100.0
        )
        db.add(data)
        db.commit()
        print("Added dummy market data for BTC/USD")
    
    print("Testing Asset Service...")
    service = AssetService(db)
    
    print("1. Search 'Bitcoin':")
    results = service.search_assets("Bitcoin")
    for r in results:
        print(f" - Found: {r.symbol} ({r.name})")
        
    print("2. Get Price for BTC:")
    btc = results[0]
    price = service.get_asset_price(btc.id)
    print(f" - Price: {price}")
    
    db.close()
    print("Verification Complete!")

if __name__ == "__main__":
    run_verification()
