import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.api.routes.assets import get_assets

async def main():
    print("Calling get_assets...")
    assets = await get_assets(search="AAVE", limit=1)
    print(f"Got {len(assets)} assets")
    if assets:
        print(assets[0])
    else:
        print("No assets found")

if __name__ == "__main__":
    asyncio.run(main())
