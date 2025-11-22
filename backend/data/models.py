from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class AssetType(str, Enum):
    CRYPTO = "CRYPTO"
    STOCK = "STOCK"
    ETF = "ETF"
    INDEX = "INDEX"
    FOREX = "FOREX"

class SourceType(str, Enum):
    EXCHANGE = "EXCHANGE"
    AGGREGATOR = "AGGREGATOR"
    BANK = "BANK"

class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)  # e.g., "Binance", "Yahoo", "CoinGecko"
    type = Column(SQLEnum(SourceType), nullable=False)
    api_url = Column(String, nullable=True)
    
    # Relationships
    asset_mappings = relationship("AssetMapping", back_populates="source")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(SQLEnum(AssetType), nullable=False)
    symbol = Column(String, nullable=False, index=True)  # Unified symbol, e.g., "BTC", "AAPL"
    name = Column(String, nullable=False)
    identifiers = Column(JSON, nullable=True)  # Store ISIN, CUSIP, CoinGeckoID, etc.
    
    # The default source to use for this asset if no user connection exists
    default_source_id = Column(String, ForeignKey("sources.id"), nullable=True)
    
    # Relationships
    default_source = relationship("Source")
    mappings = relationship("AssetMapping", back_populates="asset")

class AssetMapping(Base):
    """
    Maps a unified Asset to a specific Source with the source-specific identifier.
    Example: Asset(BTC) -> Source(Binance) -> RemoteTicker(BTC/USDT)
    """
    __tablename__ = "asset_mappings"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    remote_ticker = Column(String, nullable=False)  # e.g., "BTC/USDT", "AAPL.US"
    remote_id = Column(String, nullable=True) # e.g. "bitcoin" for coingecko
    
    # Relationships
    asset = relationship("Asset", back_populates="mappings")
    source = relationship("Source", back_populates="asset_mappings")
    market_data = relationship("MarketData", back_populates="mapping")

    __table_args__ = (
        UniqueConstraint('source_id', 'remote_ticker', name='uq_source_remote_ticker'),
    )

class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_mapping_id = Column(String, ForeignKey("asset_mappings.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    
    # Relationships
    mapping = relationship("AssetMapping", back_populates="market_data")

    __table_args__ = (
        UniqueConstraint('asset_mapping_id', 'date', name='uq_mapping_date'),
    )
