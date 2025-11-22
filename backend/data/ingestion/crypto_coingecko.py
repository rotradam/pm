import requests
from typing import List, Dict, Any
from backend.data.ingestion.base import DataIngestionService

class CoinGeckoDiscoveryService(DataIngestionService):
    def __init__(self, limit: int = 200):
        self.limit = limit
        self.base_url = "https://api.coingecko.com/api/v3"

    @property
    def source_name(self) -> str:
        return "coingecko"

    @property
    def source_type(self) -> str:
        return "AGGREGATOR"

    def fetch_assets(self) -> List[Dict[str, Any]]:
        """
        Fetches top N coins by market cap.
        """
        print(f"Fetching top {self.limit} coins from CoinGecko...")
        try:
            # CoinGecko allows max 250 per page
            per_page = min(self.limit, 250)
            response = requests.get(
                f"{self.base_url}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": per_page,
                    "page": 1,
                    "sparkline": "false"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            assets = []
            for coin in data:
                assets.append({
                    "symbol": coin['symbol'].upper(),
                    "remote_ticker": coin['id'], # CoinGecko ID as remote ticker for this source
                    "name": coin['name'],
                    "type": "CRYPTO",
                    "identifiers": {
                        "coingecko_id": coin['id'],
                        "symbol": coin['symbol'].upper()
                    }
                })
            return assets
        except Exception as e:
            print(f"Error fetching from CoinGecko: {e}")
            return []

    def fetch_ohlcv(self, symbol: str, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        # We only use CoinGecko for discovery in this plan, but could implement history later
        return []

    def get_source_details(self) -> Dict[str, Any]:
        return {
            "name": "CoinGecko",
            "type": "AGGREGATOR",
            "url": "https://api.coingecko.com/api/v3"
        }
