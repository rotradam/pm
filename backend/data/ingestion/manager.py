from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.data.ingestion.base import DataIngestionService
from backend.data.models import Asset, Source, AssetMapping, MarketData
from backend.data.database import SessionLocal

class IngestionManager:
    def __init__(self, services: List[DataIngestionService]):
        self.services = services

    def run_discovery(self, discovery_only: bool = False):
        """
        Runs the discovery process for all registered services.
        If discovery_only is True, only Assets, Sources, and AssetMappings are populated,
        and market data fetching is skipped.
        """
        db: Session = SessionLocal()
        try:
            for service in self.services:
                print(f"Running discovery for {service.source_name}...")
                
                # Get or create Source
                source_details = service.get_source_details()
                source = db.query(Source).filter(Source.name == source_details['name']).first()
                if not source:
                    source = Source(
                        name=source_details['name'],
                        type=source_details['type'],
                        api_url=source_details.get('url')
                    )
                    db.add(source)
                    db.commit()
                    db.refresh(source)

                # Fetch assets from source
                assets = service.fetch_assets()
                
                for asset_data in assets:
                    # Check if asset exists (by symbol/identifiers)
                    # For CoinGecko, we trust it as a primary source for "Asset" creation
                    asset = db.query(Asset).filter(Asset.symbol == asset_data['symbol']).first()
                    
                    if not asset:
                        asset = Asset(
                            type=asset_data['type'],
                            symbol=asset_data['symbol'],
                            name=asset_data['name'],
                            identifiers=asset_data.get('identifiers'),
                            default_source_id=source.id 
                        )
                        db.add(asset)
                        db.commit()
                        db.refresh(asset)
                    
                    # Create Mapping
                    mapping = db.query(AssetMapping).filter(
                        AssetMapping.source_id == source.id,
                        AssetMapping.remote_ticker == asset_data['remote_ticker']
                    ).first()

                    if not mapping:
                        mapping = AssetMapping(
                            asset_id=asset.id,
                            source_id=source.id,
                            remote_ticker=asset_data['remote_ticker'],
                            remote_id=asset_data.get('identifiers', {}).get('id')
                        )
                        db_mapping = mapping
                        db.add(mapping)
                        db.commit()
                        db.refresh(mapping)
                    else:
                        db_mapping = mapping

                    # Fetch Market Data (Only if NOT CoinGecko/Aggregator or if explicitly implemented)
                    # We skip market data fetch for Aggregators in this specific flow if they return empty OHLCV
                    # But let's keep the try-catch block
                    if not discovery_only and service.source_type != "AGGREGATOR":
                        print(f"Fetching data for {asset.symbol}...")
                        try:
                            ohlcv = service.fetch_ohlcv(
                                asset_data['remote_ticker'], 
                                start_date=datetime.now() - timedelta(days=365) 
                            )
                            for candle in ohlcv:
                                exists = db.query(MarketData).filter(
                                    MarketData.asset_mapping_id == db_mapping.id,
                                    MarketData.date == candle['date']
                                ).first()
                                if not exists:
                                    md = MarketData(
                                        asset_mapping_id=db_mapping.id,
                                        date=candle['date'],
                                        open=candle['open'],
                                        high=candle['high'],
                                        low=candle['low'],
                                        close=candle['close'],
                                        volume=candle['volume']
                                    )
                                    db.add(md)
                            db.commit()
                        except Exception as e:
                            print(f"Failed to fetch data for {asset.symbol}: {e}")
                
                db.commit()
                print(f"Discovery for {service.source_name} complete.")
                
        finally:
            db.close()

    def update_market_data(self, symbol: str):
        """
        Updates market data for a specific asset across all mapped sources.
        """
        # Implementation for updating market data
        pass
