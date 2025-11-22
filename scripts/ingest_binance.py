import os
import sys
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.connectors.binance_connector import get_top_binance_spot_assets

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent.parent / 'frontend' / '.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Need service role for ingestion usually

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found. Please ensure NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in frontend/.env.local")
    sys.exit(1)

def ingest_binance_data():
    logger.info("Fetching top 100 Binance spot assets...")
    assets = get_top_binance_spot_assets(limit=100)
    
    if not assets:
        logger.warning("No assets fetched.")
        return

    logger.info(f"Fetched {len(assets)} assets. Upserting to Supabase...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates" # Upsert based on primary key or unique constraint
    }
    
    # Supabase REST API endpoint for assets table
    url = f"{SUPABASE_URL}/rest/v1/assets"
    
    # Batch insert/upsert
    try:
        response = requests.post(url, json=assets, headers=headers)
        response.raise_for_status()
        logger.info("Successfully ingested Binance data.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error ingesting data to Supabase: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")

if __name__ == "__main__":
    ingest_binance_data()
