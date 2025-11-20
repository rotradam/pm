# Backend Architecture & Data Pipeline

**Date**: 2025-11-16  
**Component**: Backend data layer and strategy framework  
**Status**: Implemented and tested

## Overview

This document describes the initial backend architecture for the OLPS research dashboard, focusing on the data pipeline and strategy interface.

## Key Design Decisions

### 1. Strategy Interface (backend/strategies/base.py)

**Decision**: Use an abstract base class with a standardized interface for all OLPS strategies.

**Rationale**: 
- Ensures consistent API across baseline, research, and external library strategies
- Enables pluggable strategy architecture for easy extension
- Separates strategy logic from backtesting engine

**Interface**:
```python
class OlpsStrategy(ABC):
    id: str                    # Unique identifier (e.g., "EW", "EG", "OLMAR")
    name: str                  # Human-readable name
    paper_ref: Optional[str]   # Research paper reference
    library_ref: Optional[str] # External library reference
    
    @abstractmethod
    def run(self, prices_df: pd.DataFrame, config: dict) -> StrategyResult:
        """
        prices_df: DataFrame with DatetimeIndex and asset columns (prices or returns)
        config: Strategy-specific hyperparameters
        Returns: StrategyResult with weights, values, turnover, metadata
        """
```

**StrategyResult** (dataclass):
- `weights`: DataFrame[date × asset] - Portfolio weights over time
- `gross_portfolio_values`: Series - Portfolio value before costs
- `net_portfolio_values`: Series - Portfolio value after transaction costs
- `turnover`: Series - Turnover at each rebalancing date
- `metadata`: dict - Additional info (hyperparams, signals, etc.)

### 2. Universe Management (backend/data/universe.py)

**Decision**: CSV-based universe with in-memory filtering and validation.

**Implementation**:
- Loads `documents/etf_universe_full_clean.csv` (100 instruments, 21 sectors)
- Validates ISIN uniqueness (logs duplicates, keeps first occurrence)
- Provides sector-based filtering
- Returns ISIN lists for downstream processing

**Key Methods**:
- `Universe.get_all()` - Returns all instruments as DataFrame
- `Universe.filter_by_sector(sectors: List[str])` - Filter by sector names
- `Universe.get_isins(sectors: Optional[List[str]])` - Get ISIN list for mapping

**Known Issue**: 20 duplicate ISINs detected (same ISIN for different product names). Current behavior: logs warning and keeps first occurrence.

### 3. ISIN→Ticker Mapping (backend/data/mapper.py)

**Decision**: Heuristic-based mapper with manual override support.

**Rationale**:
- External mapping APIs (OpenFIGI, etc.) require authentication and have rate limits
- Country code heuristics work for most UCITS ETFs/ETCs
- Manual overrides handle edge cases

**Mapping Logic** (by ISIN country code):
- `IE` → `.L` (London Stock Exchange)
- `DE` → `.DE` (Xetra)
- `LU` → `.DE` (Luxembourg funds often trade on Xetra)
- `FR` → `.PA` (Euronext Paris)
- `NL` → `.AS` (Amsterdam)
- `CH` → `.SW` (SIX Swiss Exchange)
- `US` → no suffix (NASDAQ/NYSE)
- Default → `.L` (fallback to London)

**Manual Overrides**: JSON file at `data/isin_ticker_overrides.json` for exceptions.

### 4. Price Fetcher (backend/data/prices.py)

**Decision**: Yahoo Finance with Parquet caching for reproducibility.

**Rationale**:
- Yahoo Finance is free and has good coverage for European ETFs
- Parquet format is efficient for time-series data
- Caching enables repeatable backtests without re-downloading

**Storage Structure**:
- Individual ticker files: `data/prices/{ticker}.parquet`
- Combined matrix: `data/processed/prices_{start}_{end}.parquet`
- Mapping reference: `data/processed/ticker_mapping.csv`

**Key Methods**:
- `fetch_ticker(ticker, start, end)` - Download single ticker with caching
- `fetch_multiple(tickers, start, end)` - Parallel download with progress
- `get_adjusted_close_matrix(tickers, start, end)` - Build aligned price matrix

**Error Handling**: Logs failed downloads, continues with successful tickers.

## How to Use

### 1. Loading the Universe

```python
from backend.data.universe import Universe

universe = Universe()
all_instruments = universe.get_all()
equity_isins = universe.get_isins(sectors=["Global Equity", "EM Equity"])
```

### 2. Mapping ISINs to Tickers

```python
from backend.data.mapper import IsinMapper

mapper = IsinMapper()
ticker = mapper.map_isin("IE00B4L5Y983")  # Returns "IWDA.L" or similar
```

### 3. Fetching Price Data

```python
from backend.data.prices import PriceFetcher
from datetime import datetime

fetcher = PriceFetcher()

# Fetch single ticker
df = fetcher.fetch_ticker("IWDA.L", "2015-01-01", "2025-01-01")

# Fetch multiple tickers and build matrix
tickers = ["IWDA.L", "EIMI.L", "PHAU.L"]
prices_matrix = fetcher.get_adjusted_close_matrix(
    tickers, 
    start_date="2015-01-01",
    end_date="2025-01-01"
)
```

### 4. Running the Full Pipeline

```bash
# Activate environment
source activate_olps.sh

# Download all data (default: last 10 years)
python scripts/download_data.py

# Download specific date range
python scripts/download_data.py --start-date 2015-01-01 --end-date 2025-01-01

# Filter by sectors
python scripts/download_data.py --sectors "Global Equity" "EM Equity"

# Force re-download (ignore cache)
python scripts/download_data.py --force
```

## How to Extend

### Adding a New Strategy

1. Create a new file in `backend/strategies/` (e.g., `equal_weight.py`)
2. Subclass `OlpsStrategy` and implement `run()` method
3. Set `id`, `name`, `paper_ref`, `library_ref` attributes
4. Return a `StrategyResult` object

Example:
```python
from backend.strategies.base import OlpsStrategy, StrategyResult
import pandas as pd

class EqualWeight(OlpsStrategy):
    id = "EW"
    name = "Equal Weight"
    paper_ref = None
    library_ref = None
    
    def run(self, prices_df: pd.DataFrame, config: dict) -> StrategyResult:
        n_assets = len(prices_df.columns)
        weights = pd.DataFrame(
            1.0 / n_assets,
            index=prices_df.index,
            columns=prices_df.columns
        )
        # Calculate portfolio values, turnover, etc.
        return StrategyResult(
            weights=weights,
            gross_portfolio_values=gross_values,
            net_portfolio_values=net_values,
            turnover=turnover,
            metadata={"rebalance_frequency": config.get("frequency", "1D")}
        )
```

### Adding Manual ISIN→Ticker Overrides

1. Create `data/isin_ticker_overrides.json`:
```json
{
  "IE00B4L5Y983": "IWDA.AS",
  "IE00B4L5YC18": "EIMI.MI"
}
```

2. Mapper will automatically load and use these overrides.

### Extending the Universe

1. Add instruments to `documents/etf_universe_full_clean.csv`
2. Ensure columns: `sector`, `name`, `isin`, `wkn` (optional), `notes` (optional)
3. Reload with `Universe()` - no code changes needed

## Testing Notes

### Universe Loader
- ✅ Successfully loads 100 instruments from 21 sectors
- ⚠️ Logs 20 duplicate ISINs (expected behavior)
- ✅ Sector filtering works correctly

### Price Fetcher
- ✅ Yahoo Finance integration working
- ✅ Parquet caching operational
- ⚠️ Expected: ~13-20 tickers may fail (delisted/unavailable)
- ✅ Error handling prevents pipeline crashes

### Environment
- ✅ Python 3.11.9 with pyenv + pyenv-virtualenv
- ✅ All dependencies installed via `pip install -e .`
- ✅ `activate_olps.sh` script working

## Next Steps

1. **Baseline Strategies**: Implement EW, BH, CRP in `backend/strategies/baseline.py`
2. **Cost Model**: Create `backend/backtest/costs.py` with Maxblue fee structure
3. **Rebalancing Engine**: Create `backend/backtest/rebalance.py` with frequency support
4. **PortfolioLab Refactor**: Adapt strategies from `portfoliolab/` to new interface
5. **FastAPI Backend**: Create API endpoints for universe, strategies, backtests

## Dependencies

See `pyproject.toml` for full list. Key packages:
- pandas 2.3.3
- numpy 2.3.4
- yfinance 0.2.66
- pydantic 2.12.4
- pyarrow 22.0.0

## File Structure

```
backend/
├── __init__.py
├── data/
│   ├── __init__.py
│   ├── universe.py      # CSV loader with sector filtering
│   ├── mapper.py        # ISIN→ticker mapping
│   └── prices.py        # Yahoo Finance fetcher with Parquet caching
└── strategies/
    ├── __init__.py
    └── base.py          # OlpsStrategy interface + StrategyResult

scripts/
├── __init__.py
└── download_data.py     # Automated data pipeline CLI

data/                    # Created by pipeline (gitignored)
├── prices/              # Individual ticker Parquet files
└── processed/           # Combined matrices + mapping CSV
```
