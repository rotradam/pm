from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.data.models import Asset, AssetMapping, MarketData, Source
from backend.data.database import SessionLocal

class AssetService:
    def __init__(self, db: Session):
        self.db = db

    def get_asset_universe(self, limit: int = 100, offset: int = 0, category: str = None, region: str = None, exchange: str = None) -> List[Dict[str, Any]]:
        """
        Returns a paginated list of assets with default market data.
        """
        query = self.db.query(Asset)
        
        if category:
            query = query.filter(Asset.type == category.upper())
            
        # Region and Exchange filters would require more complex joins or fields on Asset/Source
        # For now, we'll skip them or implement basic placeholder logic if needed.
        
        assets = query.offset(offset).limit(limit).all()
        results = []
        
        for asset in assets:
            price_data = self.get_asset_price(asset.id) # Uses default source logic
            results.append({
                "id": asset.id,
                "ticker": asset.symbol, # Frontend expects 'ticker'
                "name": asset.name,
                "category": asset.type.title(), # Frontend expects 'category' in Title Case
                "price": price_data['price'] if price_data else None,
                "change_24h": price_data['change_24h'] if price_data else 0.0, 
                "region": "Global", # Placeholder
                "logo_url": None # Placeholder
            })
            
        return results

    def search_assets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search assets by symbol or name.
        """
        assets = self.db.query(Asset).filter(
            (Asset.symbol.ilike(f"%{query}%")) | (Asset.name.ilike(f"%{query}%"))
        ).limit(limit).all()
        
        results = []
        for asset in assets:
            price_data = self.get_asset_price(asset.id)
            results.append({
                "id": asset.id,
                "ticker": asset.symbol,
                "name": asset.name,
                "category": asset.type.title(),
                "price": price_data['price'] if price_data else None,
                "change_24h": price_data['change_24h'] if price_data else 0.0,
                "region": "Global",
                "logo_url": None
            })
        return results

    def get_asset_details(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details for a specific asset.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            asset = self.db.query(Asset).filter(Asset.symbol == asset_id).first()
            
        if not asset:
            return None
            
        price_data = self.get_asset_price(asset.id)
        
        return {
            "id": asset.id,
            "ticker": asset.symbol,
            "name": asset.name,
            "category": asset.type.title(),
            "subcategory": None, # Placeholder
            "region": "Global", # Placeholder
            "exchange": None, # Placeholder
            "currency": "USD", # Placeholder
            "price": price_data['price'] if price_data else None,
            "change_24h": price_data['change_24h'] if price_data else 0.0,
            "logo_url": None
        }

    def get_asset_price(self, asset_id: str, user_connected_sources: List[str] = None) -> Dict[str, Any]:
        """
        Get the latest price for an asset.
        Implements the conflict resolution logic:
        1. Check if user has a connected source for this asset.
        2. If yes, use that source.
        3. If no, use the asset's default source.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None

        selected_source_id = asset.default_source_id
        
        # Conflict Resolution Logic
        if user_connected_sources:
            # Find if any of the user's sources map to this asset
            user_mapping = self.db.query(AssetMapping).filter(
                AssetMapping.asset_id == asset.id,
                AssetMapping.source_id.in_(user_connected_sources)
            ).first()
            
            if user_mapping:
                selected_source_id = user_mapping.source_id

        # Get the mapping for the selected source
        mapping = self.db.query(AssetMapping).filter(
            AssetMapping.asset_id == asset.id,
            AssetMapping.source_id == selected_source_id
        ).first()

        if not mapping:
            return {"error": "No data source found for this asset"}

        # Get latest market data (fetch last 2 for change calc)
        market_data = self.db.query(MarketData).filter(
            MarketData.asset_mapping_id == mapping.id
        ).order_by(MarketData.date.desc()).limit(2).all()

        # Fallback: If no data for this source, try to find ANY source with data
        if not market_data:
            # Find a mapping that has market data
            alternative_mapping = self.db.query(AssetMapping).join(MarketData).filter(
                AssetMapping.asset_id == asset.id
            ).first()
            
            if alternative_mapping:
                # The original instruction was slightly malformed, assuming 'mappings' was defined.
                # To make it syntactically correct and functional, we'll fetch all mappings for the asset
                # and then apply the debug logic to find the best one.
                print(f"DEBUG: Initial mapping {mapping.remote_ticker} (ID: {mapping.id}) has no market data. Searching for alternatives.")
                
                all_asset_mappings = self.db.query(AssetMapping).filter(AssetMapping.asset_id == asset.id).all()
                
                best_mapping = None
                latest_date = None

                for m in all_asset_mappings:
                    last_point = self.db.query(MarketData.date).filter(
                        MarketData.asset_mapping_id == m.id
                    ).order_by(MarketData.date.desc()).first()
                    
                    if last_point:
                        print(f"DEBUG: Mapping {m.remote_ticker} (ID: {m.id}) has data. Latest: {last_point.date}")
                        if latest_date is None or last_point.date > latest_date:
                            latest_date = last_point.date
                            best_mapping = m
                    else:
                        print(f"DEBUG: Mapping {m.remote_ticker} (ID: {m.id}) has NO data")
                
                if best_mapping:
                    mapping = best_mapping
                    print(f"DEBUG: Selected fallback mapping: {mapping.remote_ticker} (ID: {mapping.id})")
                    market_data = self.db.query(MarketData).filter(
                        MarketData.asset_mapping_id == mapping.id
                    ).order_by(MarketData.date.desc()).limit(2).all()
                else:
                    print(f"DEBUG: No alternative mapping with market data found for asset {asset.symbol}.")


        latest_data = market_data[0] if market_data else None
        prev_data = market_data[1] if len(market_data) > 1 else None
        
        change_24h = 0.0
        if latest_data and prev_data and prev_data.close:
            change_24h = ((latest_data.close - prev_data.close) / prev_data.close) * 100

        return {
            "asset": asset.symbol,
            "source": mapping.source.name,
            "price": latest_data.close if latest_data else None,
            "change_24h": change_24h,
            "date": latest_data.date if latest_data else None
        }

    def get_asset_history(self, asset_id: str, period: str = "1y", source_id: str = None) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV data for an asset.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        # If passed a ticker instead of UUID, try to find it
        if not asset:
            asset = self.db.query(Asset).filter(Asset.symbol == asset_id).first()
            
        if not asset:
            return []

        # Determine source
        selected_source_id = source_id if source_id else asset.default_source_id
        
        # Get all mappings for this source
        mappings = self.db.query(AssetMapping).filter(
            AssetMapping.asset_id == asset.id,
            AssetMapping.source_id == selected_source_id
        ).all()

        mapping = None
        if mappings:
            # Find the mapping with the most recent market data
            best_mapping = None
            latest_date = None
            
            for m in mappings:
                last_point = self.db.query(MarketData.date).filter(
                    MarketData.asset_mapping_id == m.id
                ).order_by(MarketData.date.desc()).first()
                
                if last_point:
                    if latest_date is None or last_point.date > latest_date:
                        latest_date = last_point.date
                        best_mapping = m
            
            mapping = best_mapping if best_mapping else mappings[0]

        # Fallback if specific source has no mapping (only if source wasn't explicitly requested)
        if not mapping and not source_id:
             mapping = self.db.query(AssetMapping).filter(AssetMapping.asset_id == asset.id).first()

        if not mapping:
            return []

        # Date filtering logic (simplified)
        start_date = datetime.now() - timedelta(days=365) # Default 1y
        if period == "1m":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "3m":
            start_date = datetime.now() - timedelta(days=90)
        
        history = self.db.query(MarketData).filter(
            MarketData.asset_mapping_id == mapping.id,
            MarketData.date >= start_date
        ).order_by(MarketData.date.asc()).all()

        # Fallback: If no history for this source, try to find ANY source with data
        if not history and not source_id:
            # Find a mapping that has market data
            alternative_mapping = self.db.query(AssetMapping).join(MarketData).filter(
                AssetMapping.asset_id == asset.id
            ).first()
            
            if alternative_mapping:
                mapping = alternative_mapping
                history = self.db.query(MarketData).filter(
                    MarketData.asset_mapping_id == mapping.id,
                    MarketData.date >= start_date
                ).order_by(MarketData.date.asc()).all()

        return [{
            "date": h.date.isoformat(),
            "open": h.open,
            "high": h.high,
            "low": h.low,
            "close": h.close,
            "volume": h.volume
        } for h in history]

    def get_asset_sources(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Get all sources available for an asset.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            asset = self.db.query(Asset).filter(Asset.symbol == asset_id).first()
            
        if not asset:
            return []
            
        mappings = self.db.query(AssetMapping).filter(AssetMapping.asset_id == asset.id).all()
        
        unique_sources = {}
        for m in mappings:
            if m.source.id not in unique_sources:
                unique_sources[m.source.id] = m.source
                
        return [{
            "id": s.id,
            "name": s.name,
            "type": s.type
        } for s in unique_sources.values() if s.name != "CoinGecko"]
