import ccxt
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.data.ingestion.base import DataIngestionService
from backend.data.models import SourceType

class CCXTDataIngestionService(DataIngestionService):
    def __init__(self, exchange_id: str):
        self.exchange_id = exchange_id
        try:
            self.exchange = getattr(ccxt, exchange_id)()
        except AttributeError:
            raise ValueError(f"Exchange {exchange_id} not found in ccxt")

    @property
    def source_name(self) -> str:
        return self.exchange_id

    @property
    def source_type(self) -> str:
        return "EXCHANGE"

    def fetch_assets(self) -> List[Dict[str, Any]]:
        """
        Fetches all markets from the exchange.
        """
        self.exchange.load_markets()
        assets = []
        for symbol, market in self.exchange.markets.items():
            assets.append({
                "symbol": market['base'],  # e.g., BTC
                "remote_ticker": symbol,   # e.g., BTC/USDT
                "name": f"{market['base']}/{market['quote']}",
                "type": "CRYPTO",
                "identifiers": {"symbol": symbol, "base": market['base'], "quote": market['quote']}
            })
        return assets

    def fetch_ohlcv(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetches OHLCV data for a symbol.
        Handles pagination to ensure we get data up to the present.
        """
        if not self.exchange.has['fetchOHLCV']:
            return []

        timeframe = '1d'
        since = int(start_date.timestamp() * 1000) if start_date else None
        all_candles = []
        
        while True:
            try:
                candles = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # If we got fewer candles than limit, we probably reached the end
                # Some exchanges return exactly limit even if there is more, so we check timestamp
                if len(candles) < 1: 
                    break
                    
                # Update 'since' to the timestamp of the last candle + 1 timeframe
                last_timestamp = candles[-1][0]
                since = last_timestamp + 1
                
                # Safety break if we have enough data or if latest candle is recent
                last_date = datetime.fromtimestamp(last_timestamp / 1000)
                if last_date >= datetime.now() - timedelta(days=1):
                    break
                    
                # Coinbase specific: limit is 300. If we got 300, we need to loop.
                if len(candles) < 300: # Assuming 300 is a common low limit
                     if len(candles) < 1000: # If we asked for 1000 and got less (but not 0), we might be done
                        # But for coinbase specifically, it enforces 300.
                        # So if we got 300, we continue. If we got 299, we are done.
                        pass
            except Exception as e:
                print(f"Error fetching OHLCV for {symbol} from {self.exchange_id}: {e}")
                break

        # Format data
        data = []
        for candle in all_candles:
            # CCXT returns [timestamp, open, high, low, close, volume]
            # Timestamp is in milliseconds
            dt = datetime.fromtimestamp(candle[0] / 1000)
            if start_date and dt < start_date:
                continue
            if end_date and dt > end_date:
                continue
                
            data.append({
                "date": dt,
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5]
            })
            
        return data

    def get_source_details(self) -> Dict[str, Any]:
        api_urls = self.exchange.urls.get('api')
        if isinstance(api_urls, dict):
            api_url = api_urls.get('public')
            if isinstance(api_url, list): # Sometimes it's a list
                 api_url = api_url[0]
        else:
            api_url = api_urls

        return {
            "name": self.exchange_id,
            "type": SourceType.EXCHANGE,
            "api_url": api_url
        }
