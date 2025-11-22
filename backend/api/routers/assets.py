from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.data.database import get_db
from backend.data.asset_service import AssetService
from backend.data.models import Asset

router = APIRouter(
    prefix="/assets",
    tags=["assets"]
)

@router.get("", response_model=List[dict]) 
def get_assets(
    limit: int = 100, 
    offset: int = 0, 
    category: Optional[str] = None,
    region: Optional[str] = None,
    exchange: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = AssetService(db)
    assets = service.get_asset_universe(limit, offset, category, region, exchange)
    return assets

@router.get("/search", response_model=List[dict])
def search_assets(q: str, db: Session = Depends(get_db)):
    service = AssetService(db)
    assets = service.search_assets(q)
    return assets

@router.get("/{asset_id}", response_model=dict)
def get_asset_details(asset_id: str, db: Session = Depends(get_db)):
    service = AssetService(db)
    asset = service.get_asset_details(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.get("/{asset_id}/price")
def get_asset_price(asset_id: str, user_sources: Optional[str] = None, db: Session = Depends(get_db)):
    """
    user_sources: Comma separated list of source IDs connected by the user.
    """
    service = AssetService(db)
    sources_list = user_sources.split(",") if user_sources else None
    price_data = service.get_asset_price(asset_id, sources_list)
    if not price_data:
        raise HTTPException(status_code=404, detail="Asset not found")
    return price_data

@router.get("/{asset_id}/history")
def get_asset_history(asset_id: str, period: str = "1y", source: Optional[str] = None, db: Session = Depends(get_db)):
    service = AssetService(db)
    # If source name is provided (e.g. "binance"), we need to look up its ID or handle it in service
    # For now, let's assume the service handles ID lookup or we pass None to use default
    # TODO: Implement source name to ID lookup if needed, but for now let's stick to default logic
    return service.get_asset_history(asset_id, period, source)

@router.get("/{asset_id}/sources")
def get_asset_sources(asset_id: str, db: Session = Depends(get_db)):
    service = AssetService(db)
    return service.get_asset_sources(asset_id)
