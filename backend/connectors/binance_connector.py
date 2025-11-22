import requests
import logging

logger = logging.getLogger(__name__)

def get_top_binance_spot_assets(limit=100):
    """
    Fetch top spot assets from Binance by 24h quote volume (USDT pairs).
    """
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Filter for USDT pairs
        usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
        
        # Sort by quote volume (volume in USDT)
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        
        top_pairs = sorted_pairs[:limit]
        
        assets = []
        for pair in top_pairs:
            symbol = pair['symbol']
            # Remove USDT to get base asset
            base_asset = symbol[:-4]
            
            assets.append({
                "ticker": symbol, # e.g. BTCUSDT
                "name": base_asset, # e.g. BTC
                "category": "Crypto",
                "subcategory": "Spot",
                "region": "Global",
                "currency": "USDT",
                "exchange": "Binance",
                "price": float(pair['lastPrice']),
                "change_24h": float(pair['priceChangePercent']),
                "volume_24h": float(pair['quoteVolume']),
                "source": "binance",
                # Sparkline is not available in this endpoint, would need klines
                "sparkline_7d": "[]" 
            })
            
        return assets
    except Exception as e:
        logger.error(f"Error fetching Binance data: {e}")
        return []
