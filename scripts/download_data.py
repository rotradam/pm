"""
Automated data pipeline for OLPS dashboard.

Downloads historical price data for all instruments in the universe.
Run this script to populate the local price cache before running backtests.
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

from backend.data.mapper import IsinMapper
from backend.data.prices import PriceFetcher
from backend.data.universe import Universe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download historical price data for all universe instruments"
    )
    parser.add_argument(
        "--start-date",
        default=(datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d"),
        help="Start date for price history (default: 10 years ago)"
    )
    parser.add_argument(
        "--end-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date for price history (default: today)"
    )
    parser.add_argument(
        "--sectors",
        nargs="+",
        help="Limit to specific sectors (default: all sectors)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if cached"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("OLPS Data Pipeline")
    logger.info("="*60)
    logger.info(f"Date range: {args.start_date} to {args.end_date}")
    
    # Load universe
    logger.info("\n[1/4] Loading universe...")
    universe = Universe()
    
    if args.sectors:
        universe_df = universe.filter_by_sector(args.sectors)
        logger.info(f"Filtered to sectors: {args.sectors}")
    else:
        universe_df = universe.get_all()
        logger.info(f"Using full universe: {len(universe_df)} instruments")
    
    # Map ISINs to tickers
    logger.info("\n[2/4] Mapping ISINs to Yahoo Finance tickers...")
    mapper = IsinMapper()
    universe_df = mapper.map_universe(universe_df)
    
    # Filter out unmapped ISINs
    universe_df = universe_df[universe_df["ticker"].notna()].copy()
    
    if len(universe_df) == 0:
        logger.error("\n✗ No valid ticker mappings found!")
        logger.error("Please add mappings to data/isin_ticker_mapping_verified.json")
        logger.error("See backend/data/isin_resolver.py for instructions")
        return 1
    
    # Show sample
    logger.info(f"\nFound {len(universe_df)} mapped tickers. Sample:")
    for _, row in universe_df.head(5).iterrows():
        logger.info(f"  {row['isin']} ({row['name']}) → {row['ticker']}")
    
    tickers = universe_df["ticker"].tolist()
    
    # Fetch prices
    logger.info(f"\n[3/4] Fetching price data for {len(tickers)} tickers...")
    logger.info("This may take several minutes depending on network speed...")
    
    fetcher = PriceFetcher()
    price_data = fetcher.fetch_multiple(
        tickers,
        args.start_date,
        args.end_date,
        use_cache=not args.force
    )
    
    # Create combined price matrix
    logger.info("\n[4/4] Building price matrix...")
    try:
        prices_df = fetcher.get_adjusted_close_matrix(
            tickers,
            args.start_date,
            args.end_date,
            use_cache=not args.force
        )
        
        # Save combined matrix
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"prices_{args.start_date}_{args.end_date}.parquet"
        prices_df.to_parquet(output_file)
        
        logger.info(f"\n✓ Success! Price matrix saved to: {output_file}")
        logger.info(f"  Shape: {prices_df.shape[0]} days × {prices_df.shape[1]} assets")
        logger.info(f"  Date range: {prices_df.index[0]} to {prices_df.index[-1]}")
        logger.info(f"  Missing data: {prices_df.isna().sum().sum()} cells "
                   f"({prices_df.isna().sum().sum() / prices_df.size * 100:.2f}%)")
        
        # Save mapping for reference
        mapping_file = output_dir / "ticker_mapping.csv"
        universe_df[["isin", "name", "ticker", "sector"]].to_csv(mapping_file, index=False)
        logger.info(f"  Ticker mapping saved to: {mapping_file}")
        
    except Exception as e:
        logger.error(f"\n✗ Failed to create price matrix: {e}")
        logger.error("Check the warnings above for failed ticker downloads.")
        logger.error("You may need to add manual overrides in data/isin_ticker_overrides.json")
        return 1
    
    logger.info("\n" + "="*60)
    logger.info("Pipeline complete! You can now run backtests.")
    logger.info("="*60)
    return 0


if __name__ == "__main__":
    exit(main())
