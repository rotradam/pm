from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.data.models import Asset, MarketData, Source

class DataIngestionService(ABC):
    """
    Abstract base class for data ingestion services.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """
        Returns the type of source: 'EXCHANGE', 'AGGREGATOR', 'BANK'
        """
        pass

    @abstractmethod
    def fetch_assets(self) -> List[Dict[str, Any]]:
        """
        Discovers assets available from this source.
        Returns a list of dictionaries containing asset metadata.
        """
        pass

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, start_date: datetime, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetches OHLCV data for a specific asset.
        """
        pass
    
    @abstractmethod
    def get_source_details(self) -> Dict[str, Any]:
        """
        Returns details about the source (e.g., type, url).
        """
        pass
