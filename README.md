# OLPS Research Dashboard

Research-grade Online Portfolio Selection (OLPS) platform with Maxblue cost-aware backtesting and interactive web dashboard.

**Status:** 16/20 Strategies Implemented (80% Complete) ✅

## Features

- 🎯 **16 OLPS Strategies** across 5 families (Baseline, Momentum, Mean Reversion, Correlation-Driven, Follow-The-Leader)
- 📊 **Interactive Dashboard** with Streamlit for strategy comparison and visualization
- 💰 **Maxblue Cost Model** (planned) for realistic transaction cost simulation
- 📈 **67 ETFs/ETCs** covering global equities, sectors, commodities, and precious metals
- 🔬 **Research-Grade** implementations from academic papers with full documentation

## Quick Start

### 1. Activate Environment

```bash
source activate_olps.sh
```

This activates the pyenv `olps` virtual environment (Python 3.11.9).

### 2. Run Dashboard

```bash
streamlit run dashboard_enhanced.py --server.port 8502
```

Navigate to: **http://localhost:8502**

### 3. Run Tests

```bash
python test_strategies.py
```

Expected: `7/7 tests passed (100.0%) 🎉`

## Data Pipeline

### Download Historical Prices

```bash
python scripts/download_data.py
```

**Options:**
- `--start-date YYYY-MM-DD` – Start date (default: 2015-01-01)
- `--end-date YYYY-MM-DD` – End date (default: today)
- `--sectors "Global Equity" "EM Equity"` – Filter by sectors
- `--force` – Force re-download

**Example:**
```bash
python scripts/download_data.py --start-date 2020-01-01 --sectors "Global Equity" "US Equity"
```

### 4. Verify Installation

```bash
python -c "from backend.data.universe import Universe; u = Universe(); print(f'Loaded {len(u.get_all())} instruments')"
```

## Implemented Strategies (16/20)

### Baseline (3/3) ✅
- **EW** - Equal Weight
- **BAH** - Buy and Hold  
- **CRP** - Constant Rebalanced Portfolio

### Momentum (2/2) ✅
- **EG** - Exponential Gradient
- **UP** - Universal Portfolio

### Mean Reversion (4/4) ✅
- **OLMAR** - Online Moving Average Reversion
- **PAMR** - Passive Aggressive Mean Reversion
- **CWMR** - Confidence Weighted Mean Reversion
- **RMR** - Robust Median Reversion

### Correlation-Driven (3/7) 🟡
- **CORN** - Correlation-Driven Nonparametric Learning
- **CORNK** - CORN with Top-K Expert Selection
- **CORNU** - CORN with Uniform Aggregation
- ⏳ *SCORN, SCORNK, FCORN, FCORNK (deferred)*

### Follow-The-Leader (4/4) ✅
- **BCRP** - Best Constant Rebalanced Portfolio (benchmark)
- **BestStock** - Best Single Asset (benchmark)
- **FTL** - Follow The Leader
- **FTRL** - Follow The Regularized Leader

## Project Structure

```
portfolioManagement/
├── backend/                         # Core strategy engine
│   ├── data/
│   │   ├── universe.py              # ETF universe loader
│   │   ├── mapper.py                # ISIN→ticker mapping
│   │   ├── prices.py                # Price data fetcher
│   │   └── isin_resolver.py         # OpenFIGI resolver
│   └── strategies/                  # 16 OLPS strategies
│       ├── base.py                  # Strategy interface
│       ├── baseline.py              # EW, BAH, CRP
│       ├── momentum.py              # EG, UP
│       ├── mean_reversion.py        # OLMAR, PAMR, CWMR, RMR
│       ├── correlation_driven.py    # CORN, CORNK, CORNU
│       ├── follow_the_leader.py     # BCRP, BestStock, FTL, FTRL
│       └── utils.py                 # Helper functions
├── dashboard_enhanced.py            # Interactive Streamlit dashboard
├── test_strategies.py               # Strategy test suite
├── data/
│   ├── prices/                      # Individual ticker parquets (67 files)
│   └── processed/                   # Consolidated price matrices
├── documents/
│   ├── etf_universe_full_clean.csv  # 67 ETFs/ETCs
│   └── [Research PDFs]              # OLPS papers
├── scripts/
│   ├── download_data.py             # Data pipeline
│   └── resolve_isins_openfigi.py    # ISIN resolver
├── work-documentation/              # Implementation guides
│   ├── 2025-01-17_strategy-summary.md
│   └── 2025-01-17_batch2-corn-ftl-implementation.md
└── pyproject.toml                   # Package metadata
```

## Usage Examples

### Single Strategy Backtest
```python
from backend.strategies import CORN
import pandas as pd

# Load data
prices = pd.read_parquet('data/processed/prices_2015-01-01_2025-11-16.parquet')

# Run CORN strategy
strategy = CORN()
result = strategy.run(prices.loc['2020':'2021'].iloc[:, :10], {
    'initial_capital': 10000,
    'window': 5,
    'rho': 0.1
})

print(f"Final Value: ${result.gross_portfolio_values.iloc[-1]:,.2f}")
print(f"Return: {(result.gross_portfolio_values.iloc[-1] / 10000 - 1) * 100:.2f}%")
```

### Strategy Comparison
```python
from backend.strategies import get_strategy

strategies = ['EW', 'CORN', 'FTRL', 'BCRP']
results = {}

for sid in strategies:
    strategy = get_strategy(sid)
    result = strategy.run(prices, {'initial_capital': 10000})
    results[sid] = result.gross_portfolio_values.iloc[-1]

# Show ranking
for sid, val in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{sid}: ${val:,.2f}")
```
- **Mappings**: Ticker mapping reference in `data/processed/ticker_mapping.csv`

Parquet format provides:
- Fast read/write (10-100x faster than CSV)
- Efficient compression
- Preserves data types

## Next Steps

### Phase 2: Strategy Engine

- Implement baseline strategies (EW, BH, CRP) in `backend/strategies/baseline.py`
- Port research strategies from `portfoliolab/` to new interface
- Add transaction cost model in `backend/backtest/costs.py`

### Phase 3: Backend API

- FastAPI app at `backend/api/` with endpoints:
  - `GET /api/universe` – list instruments
  - `GET /api/strategies` – list available strategies
  - `POST /api/backtests` – run backtest
  - `GET /api/backtests/{id}` – query results

### Phase 4: Frontend Dashboard

- React + TypeScript dashboard
- Universe view, strategy catalog, backtest config, results visualization

## Configuration

### Python Environment

- **Version**: Python 3.11.9
- **Env Name**: `olps`
- **Manager**: pyenv + pyenv-virtualenv

### Key Dependencies

- `pandas` – Data manipulation
- `numpy` – Numerical computing
- `yfinance` – Yahoo Finance data
- `pydantic` – Config validation
- `fastapi` – Backend API framework
- `sqlalchemy` – Database ORM (for experiment storage)

## Troubleshooting

### "Command not found: pyenv"

Ensure pyenv is in your PATH:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
source ~/.zshrc
```

### "No data returned for ticker"

Common causes:
1. Ticker not available on Yahoo Finance
2. Wrong exchange suffix (try `.L`, `.DE`, `.AS`, `.PA`)
3. US tickers may use symbol not ISIN
4. Delisted or very new instrument

**Solution**: Add manual override in `data/isin_ticker_overrides.json`

### Import Errors

Ensure package is installed in editable mode:

```bash
python -m pip install -e .
```

## License & Attribution

- **PortfolioLab**: Reference code from Hudson & Thames (to be refactored or replaced)
- **Strategy Implementations**: Based on academic research papers in `documents/`
- **Data**: Yahoo Finance (free tier, rate-limited)

## Documentation

See `work-documentation/` for:
- Architecture decisions
- Implementation notes
- Extension guides
