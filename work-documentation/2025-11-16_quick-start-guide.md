# Quick Start Guide

**Date**: 2025-11-16  
**Component**: Getting started with OLPS dashboard  
**Status**: Ready for development

## Overview

This guide helps you quickly set up and start working with the OLPS research dashboard project.

## Prerequisites

- macOS with Homebrew installed
- Git repository cloned
- pyenv and pyenv-virtualenv installed (already configured)

## Quick Start (3 Steps)

### 1. Activate Environment

```bash
source activate_olps.sh
```

You should see:
```
✓ olps environment activated successfully
  Python: Python 3.11.9
  Path: /Users/[username]/.pyenv/versions/olps/bin/python
```

### 2. Download Price Data

```bash
python scripts/download_data.py
```

This will:
- Load 100 instruments from the universe CSV
- Map ISINs to Yahoo Finance tickers
- Download 10 years of daily price data
- Save to Parquet files in `data/` directory

**Expected time**: 5-15 minutes  
**Expected failures**: ~13-20 tickers (delisted/unavailable)

### 3. Verify Installation

```bash
# Test universe loader
python -c "from backend.data.universe import Universe; u = Universe(); print(f'✓ Loaded {len(u.get_all())} instruments')"

# Test price data exists
ls data/processed/
```

You should see:
- `prices_*.parquet` (price matrix)
- `ticker_mapping.csv` (ISIN to ticker mappings)

## Project Structure

```
portfolioManagement/
├── documents/                      # Input data and research papers
│   └── etf_universe_full_clean.csv # 100 ETFs/ETCs
├── backend/                        # Python backend
│   ├── data/                       # Data layer
│   │   ├── universe.py             # Universe loader
│   │   ├── mapper.py               # ISIN→ticker mapping
│   │   └── prices.py               # Price fetcher
│   └── strategies/                 # Strategy implementations
│       └── base.py                 # Strategy interface
├── scripts/                        # Utility scripts
│   └── download_data.py            # Data pipeline
├── work-documentation/             # Technical documentation
├── activate_olps.sh                # Environment activation
└── pyproject.toml                  # Dependencies
```

## Next Development Tasks

### Phase 1: Baseline Strategies (Next)

Create `backend/strategies/baseline.py` with:
- Equal Weight (EW)
- Buy & Hold (BH)
- Constant Rebalanced Portfolio (CRP)

### Phase 2: Cost Model

Create `backend/backtest/costs.py` with Maxblue fee structure:
- Commission rate: 0.25% of trade volume
- Min commission: €8.90
- Max commission: €58.90
- Exchange fee: €2.00 per trade

### Phase 3: Rebalancing Engine

Create `backend/backtest/rebalance.py` supporting:
- Daily (1D)
- Weekly (1W)
- Monthly (1M)
- Custom N-day intervals

### Phase 4: FastAPI Backend

Create API endpoints:
- `GET /api/universe` - List instruments
- `GET /api/strategies` - List strategies
- `POST /api/backtests` - Run backtest
- `GET /api/backtests/{id}` - Get results

## Common Commands

### Environment Management

```bash
# Activate environment
source activate_olps.sh

# Verify Python version
python --version

# Check installed packages
pip list

# Install new package
pip install <package-name>
```

### Data Management

```bash
# Download all data (last 10 years)
python scripts/download_data.py

# Download specific date range
python scripts/download_data.py --start-date 2015-01-01 --end-date 2025-01-01

# Download specific sectors only
python scripts/download_data.py --sectors "Global Equity" "EM Equity"

# Force re-download (ignore cache)
python scripts/download_data.py --force
```

### Development

```bash
# Run Python REPL with environment
python

# Run a specific script
python scripts/your_script.py

# Run tests (when implemented)
pytest

# Format code (when configured)
black backend/ scripts/
```

## Troubleshooting

### Environment Not Activating

**Symptom**: `pyenv: command not found`

**Solution**:
```bash
source activate_olps.sh
```

This script handles all initialization automatically.

### Wrong Python Version

**Symptom**: `python --version` shows wrong version

**Solution**:
```bash
# Reactivate environment
source activate_olps.sh

# Verify
python --version  # Should show 3.11.9
```

### Data Download Fails

**Symptom**: Many tickers fail to download

**Expected**: ~13-20 failures (delisted/unavailable tickers)

**If too many fail**:
1. Check internet connection
2. Try again later (Yahoo Finance may have rate limits)
3. Check `data/prices/` for successful downloads

### Import Errors

**Symptom**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall in development mode
pip install -e .
```

## Key Documentation Files

- **Architecture**: `work-documentation/2025-11-16_backend-architecture-data-pipeline.md`
- **Environment**: `work-documentation/2025-11-16_environment-setup.md`
- **AI Instructions**: `.github/copilot-instructions.md`
- **Dependencies**: `pyproject.toml`

## Getting Help

1. Check documentation in `work-documentation/`
2. Review `.github/copilot-instructions.md` for AI agent guidance
3. Check research papers in `documents/` for strategy details

## Development Workflow

1. **Start session**: `source activate_olps.sh`
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Develop and test**: Edit code, run tests
4. **Document changes**: Add to `work-documentation/YYYY-MM-DD_description.md`
5. **Commit**: `git add .` and `git commit -m "Description"`
6. **Push**: `git push origin feature/your-feature`

## Status Checklist

- ✅ Python 3.11.9 environment created
- ✅ Dependencies installed
- ✅ Backend structure scaffolded
- ✅ Data pipeline implemented
- ✅ Activation script working
- ⏳ Price data (run `python scripts/download_data.py`)
- ⏳ Baseline strategies (to be implemented)
- ⏳ Cost model (to be implemented)
- ⏳ API backend (to be implemented)
- ⏳ Dashboard frontend (to be implemented)
