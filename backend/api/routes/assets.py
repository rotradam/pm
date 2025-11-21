from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
from backend.data.database import AssetDatabase
from backend.data.prices import PriceFetcher

router = APIRouter()
db = AssetDatabase()
price_fetcher = PriceFetcher()

# Pydantic Models
class Asset(BaseModel):
    ticker: str
    name: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    region: Optional[str]
    currency: Optional[str]
    exchange: Optional[str]

class AssetHistory(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

@router.get("/", response_model=List[Asset])
async def get_assets(
    search: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    exchange: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    limit: int = 100,
    offset: int = 0
):
    """
    Get a list of assets with optional filtering and search.
    """
    df = db.get_filtered_assets(
        search=search,
        category=category,
        region=region,
        exchange=exchange,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    # Convert NaNs to None for JSON compliance
    df = df.where(pd.notnull(df), None)
        
    return df.to_dict(orient="records")

@router.get("/{ticker}", response_model=Asset)
async def get_asset_details(ticker: str):
    """
    Get details for a specific asset.
    """
    asset = db.get_asset_by_ticker(ticker)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    # Handle NaNs
    for k, v in asset.items():
        if pd.isna(v):
            asset[k] = None
            
    return asset

@router.get("/{ticker}/history")
async def get_asset_history(ticker: str, period: str = "1y"):
    """
    Get historical price data for an asset.
    """
    try:
        # 1. Try yfinance first (preferred for stocks/ETFs and major crypto)
        import yfinance as yf
        
        # Map period to yfinance format if needed, but "1y" is standard
        
        hist = yf.Ticker(ticker).history(period=period)
        
        if not hist.empty:
            hist = hist.reset_index()
            hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
            
            # Rename cols to lowercase
            hist = hist.rename(columns={
                "Date": "date", 
                "Open": "open", 
                "High": "high", 
                "Low": "low", 
                "Close": "close", 
                "Volume": "volume"
            })
            return hist[['date', 'open', 'high', 'low', 'close', 'volume']].to_dict(orient="records")

        # 2. If yfinance fails, check if we have a CoinGecko ID
        # Fetch asset details from DB
        asset = db.get_asset_by_ticker(ticker)
        if asset:
            cg_id = asset.get('coingecko_id')
            
            if cg_id:
                # Fetch from CoinGecko
                import requests
                import time
                from datetime import datetime, timedelta
                
                # Map period to days
                days = "365"
                if period == "1d": days = "1"
                elif period == "1w": days = "7"
                elif period == "1mo": days = "30"
                elif period == "3mo": days = "90"
                elif period == "1y": days = "365"
                elif period == "max": days = "max"
                
                url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": days
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    prices = data.get('prices', [])
                    volumes = data.get('total_volumes', [])
                    
                    # CoinGecko returns [timestamp, value]
                    # We need to construct OHLCV. CoinGecko only gives price/volume points, not OHLC candles for this endpoint.
                    # We will approximate OHLC by using the price as Close, and maybe Open=PrevClose.
                    # Or just set O=H=L=C = Price.
                    
                    history = []
                    for i, (ts, price) in enumerate(prices):
                        date_str = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                        vol = 0
                        # Try to match volume
                        if i < len(volumes):
                            vol = volumes[i][1]
                            
                        history.append({
                            "date": date_str,
                            "open": price,
                            "high": price,
                            "low": price,
                            "close": price,
                            "volume": vol
                        })
                    
                    return history
                    
        raise HTTPException(status_code=404, detail="No history found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
