import yfinance as yf
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.data.ingestion.base import DataIngestionService
from backend.data.models import SourceType

class YFinanceDataIngestionService(DataIngestionService):
    def __init__(self):
        pass

    @property
    def source_name(self) -> str:
        return "yahoo_finance"

    @property
    def source_type(self) -> str:
        return "AGGREGATOR"

    def fetch_assets(self) -> List[Dict[str, Any]]:
        """
        YFinance doesn't have a simple 'list all' method.
        We typically rely on a seed list or search.
        For now, this might return an empty list or be used with a specific list of tickers.
        """
        # TODO: Implement a way to load a seed list of tickers (e.g. S&P 500, NASDAQ 100)
        return []

    def fetch_ohlcv(self, symbol: str, start_date: datetime, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetches OHLCV data using yfinance.
        """
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval="1d")
        
        data = []
        for index, row in df.iterrows():
            data.append({
                "date": index.to_pydatetime(),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })
        return data

    def get_source_details(self) -> Dict[str, Any]:
        return {
            "name": "Yahoo Finance",
            "type": SourceType.AGGREGATOR,
            "api_url": "https://finance.yahoo.com"
        }
