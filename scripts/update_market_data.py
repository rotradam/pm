import pandas as pd
import requests
import sys
import time
import json
import yfinance as yf
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data.database import AssetDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_crypto_data(db):
    """Update crypto assets using CoinGecko API."""
    logger.info("Updating Crypto data...")
    
    # Get all crypto assets with coingecko_id
    assets = db.get_assets_by_category("Crypto")
    if assets.empty:
        logger.info("No crypto assets found.")
        return

    # CoinGecko allows 250 ids per call
    ids = assets['coingecko_id'].dropna().tolist()
    chunk_size = 250
    chunk_size = 250
    
    updated_assets = []
    
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        id_str = ",".join(chunk)
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": id_str,
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "true",
            "price_change_percentage": "24h"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:
                logger.warning("Rate limited by CoinGecko. Waiting 60s...")
                time.sleep(60)
                response = requests.get(url, params=params)
                
            response.raise_for_status()
            data = response.json()
            
            for coin in data:
                # Find matching ticker in our DB
                # We stored it as SYMBOL-USD usually, but let's match by ID
                match = assets[assets['coingecko_id'] == coin['id']]
                if match.empty:
                    continue
                    
                ticker = match.iloc[0]['ticker']
                
                # Process sparkline
                sparkline = coin.get('sparkline_in_7d', {}).get('price', [])
                # Downsample sparkline to save space (e.g. take every 4th point)
                sparkline_short = sparkline[::4] if sparkline else []
                
                # Preserve existing fields
                row = match.iloc[0]
                
                updated_assets.append({
                    "ticker": ticker,
                    "name": row['name'],
                    "category": row['category'],
                    "subcategory": row['subcategory'],
                    "region": row['region'],
                    "currency": row['currency'],
                    "exchange": row['exchange'],
                    "coingecko_id": row['coingecko_id'],
                    "price": coin['current_price'],
                    "change_24h": coin['price_change_percentage_24h'],
                    "logo_url": coin['image'],
                    "sparkline_7d": json.dumps(sparkline_short),
                    "last_updated": datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error fetching crypto chunk {i}: {e}")
            
    if updated_assets:
        df = pd.DataFrame(updated_assets)
        db.add_assets(df)
        logger.info(f"Updated {len(df)} crypto assets.")

def update_stock_data(db):
    """Update stock/ETF data using yfinance bulk download."""
    logger.info("Updating Stock/ETF/Bond/Commodity data...")
    
    categories = ["Stock", "ETF", "Bond", "Commodity"]
    all_assets_dict = {}
    
    for cat in categories:
        df = db.get_assets_by_category(cat)
        if not df.empty:
            for _, row in df.iterrows():
                all_assets_dict[row['ticker']] = row.to_dict()
            
    if not all_assets_dict:
        logger.info("No stock assets found.")
        return

    all_tickers = list(all_assets_dict.keys())
    
    # yfinance download is efficient, but let's chunk to 500 to avoid massive memory usage or timeouts
    chunk_size = 500
    
    updated_assets = []
    
    for i in range(0, len(all_tickers), chunk_size):
        chunk = all_tickers[i:i+chunk_size]
        logger.info(f"Fetching chunk {i//chunk_size + 1} ({len(chunk)} tickers)...")
        
        try:
            # Download 5d history for all tickers in chunk
            # threads=True enables parallel downloading
            data = yf.download(chunk, period="5d", group_by='ticker', threads=True, progress=False)
            
            # Data is a MultiIndex DataFrame: (Ticker, PriceField)
            # If only 1 ticker, it's just (PriceField)
            
            for ticker in chunk:
                try:
                    # Extract data for this ticker
                    if len(chunk) == 1:
                        ticker_data = data
                    else:
                        if ticker not in data.columns.levels[0]:
                            continue
                        ticker_data = data[ticker]
                    
                    if ticker_data.empty:
                        continue
                        
                    # Get latest price and change
                    # 'Close' is a Series
                    closes = ticker_data['Close'].dropna()
                    if closes.empty:
                        continue
                        
                    current_price = closes.iloc[-1]
                    
                    # Calculate 24h change
                    if len(closes) >= 2:
                        prev_close = closes.iloc[-2]
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                    else:
                        change_pct = 0.0
                        
                    # Sparkline (last 7 days or whatever we got)
                    sparkline = closes.tolist()
                    
                    # Preserve existing fields
                    original_asset = all_assets_dict.get(ticker, {})
                    
                    updated_assets.append({
                        "ticker": ticker,
                        "name": original_asset.get('name'),
                        "category": original_asset.get('category'),
                        "subcategory": original_asset.get('subcategory'),
                        "region": original_asset.get('region'),
                        "currency": original_asset.get('currency'),
                        "exchange": original_asset.get('exchange'),
                        "coingecko_id": original_asset.get('coingecko_id'),
                        "logo_url": original_asset.get('logo_url'), # Keep existing logo if any
                        "price": float(current_price),
                        "change_24h": float(change_pct),
                        "sparkline_7d": json.dumps(sparkline),
                        "last_updated": datetime.now()
                    })
                    
                except Exception as e:
                    # logger.warning(f"Error processing {ticker}: {e}")
                    pass
                    
        except Exception as e:
            logger.error(f"Error fetching stock chunk {i}: {e}")
            
    if updated_assets:
        df = pd.DataFrame(updated_assets)
        db.add_assets(df)
        logger.info(f"Updated {len(df)} stock assets.")

def main():
    db = AssetDatabase()
    
    update_crypto_data(db)
    update_stock_data(db)
    
    logger.info("Market data update complete!")

if __name__ == "__main__":
    main()
