## OLPS research dashboard – AI agent instructions

## 1. Overview

### 1.1 Purpose

This project builds a **research-grade Online Portfolio Selection (OLPS) platform** with a web dashboard front-end.

The platform will:

- Use a curated ETF/ETC universe (provided via CSV).
- Fetch and maintain historical price data.
- Implement multiple **OLPS strategies from the academic literature** (research PDFs provided).
- Optionally **reuse and extend third-party OLPS/portfolio libraries** (e.g. Hudson & Thames).
- Simulate **rebalancing with realistic Maxblue transaction costs**.
- Allow interactive comparison of:
  - Different strategies (baseline + paper-based).
  - Different **rebalancing frequencies** (1d / 1w / 1m / custom).
  - Performance **net of transaction costs**.

The goal is to create an internal **research and decision-support tool** to explore OLPS algorithms and identify robust, cost-aware strategies suitable for a Maxblue depot.

### 1.2 Context

- Broker: **Maxblue Depot** (Deutsche Bank).
- Investment universe: primarily **UCITS ETFs/ETCs** (plus optionally some stocks), all tradeable in a German retail brokerage account.
- Data: daily OHLC / adjusted close from a free or low-cost data source (e.g. Yahoo Finance or similar).
- Research inputs:
  - A collection of **recent OLPS research papers** (PDFs, stored in an internal folder/repo).
  - External library references such as **Hudson & Thames** (e.g. `mlfinlab` / OLPS modules), used as inspiration or integrated where licensing permits.

---

## 2. Scope

### 2.1 In Scope (MVP)

1. **Dashboard-First Workflow**
   - Single web dashboard where the user can:
     - Configure backtests (universe, strategies, rebalancing frequencies, cost model).
     - Run backtests.
     - Compare results visually and in tables.

2. **Universe & Data**
   - Read curated **CSV universe** (provided).
   - Map ISIN → data-provider ticker.
   - Download and store **daily historical price data**.

3. **OLPS Strategy Engine**
   - Implement a **pluggable strategy framework**.
   - Include:
     - Baseline strategies (Equal Weight, Buy & Hold, CRP).
     - OLPS strategies implemented **from research papers**.
     - Optionally, wrappers/integration for external libraries (Hudson & Thames etc.) where licensing allows.

4. **Rebalancing Frequency**
   - Support:
     - Daily (1d)
     - Weekly (1w)
     - Monthly (1m)
     - Configurable N-day interval.

5. **Maxblue-Aware Transaction Cost Model**
   - Apply Maxblue-like fees per trade to each rebalance.
   - Show **gross** vs **net** performance and fee breakdown.

6. **Research & Experiment Management**
   - Ability to tag strategies and backtests with:
     - Paper reference (e.g. DOI, short name).
     - Implementation version.
     - Parameter sets.
   - Ability to re-run and compare backtests for different hyperparameters.

### 2.2 Out of Scope (for MVP)

- Live trading / order routing to Maxblue.
- Intraday/HFT or crypto data.
- Tax modeling.
- Complex multi-currency hedging.
- Mobile native app (web-only).

---

## 3. Stakeholders

- **Product Owner / Research Quant**  
  Defines universe, strategy priorities, paper list, evaluation metrics.

- **Data Engineering**  
  Data ingestion, ISIN→ticker mapping, storage, scheduled refresh.

- **Backend Team**  
  Strategy engine, backtesting logic, cost model, experiment tracking, APIs.

- **Frontend Team**  
  Dashboard UI, charts, interaction.

- **DevOps**  
  Deployment, monitoring, secrets management, scheduled jobs.

---

## 4. Key Concepts

- **Universe CSV**: An input file listing ETFs/ETCs (and possibly stocks) with metadata. ISIN is the primary ID.
- **Research Strategy**: An OLPS algorithm specifically derived from a research paper, implemented with documented assumptions.
- **External Library Strategy**: A strategy whose implementation uses or wraps external code (e.g. `mlfinlab`), with clear abstraction and licensing-awareness.
- **Rebalancing Frequency**: Interval at which portfolio weights are applied and trades occur (1 day, 1 week, 1 month, etc.).
- **Maxblue Cost Model**: Commission structure approximating Maxblue’s real transaction fees.
- **Experiment / Backtest**: A run specifying universe subset, strategies, date range, rebalance frequency, cost model, and hyperparameters.

---

## 5. User Stories

### 5.1 Quant / Researcher

1. **Backtest multiple OLPS papers**
   - “I want to select several OLPS strategies (each linked to a research paper) and run them on the same universe and time period, so I can compare them fairly.”

2. **Compare different rebalancing frequencies**
   - “I want to run a strategy with daily, weekly, and monthly rebalancing and see how transaction costs change the ranking of strategies.”

3. **Reference the underlying research**
   - “For each strategy, I want to see which paper it’s based on, and a short description of the algorithm and hyperparameters.”

4. **Hyperparameter experiments**
   - “I want to run the same strategy with different parameter sets (e.g. window length, learning rate) and see which configuration is most robust.”

5. **Cost-aware evaluation**
   - “I want to see performance both before and after Maxblue-style fees, and understand the total costs paid over time.”

6. **Result reproducibility**
   - “I want to be able to re-run an experiment later and get the same results for the same data and configuration.”

### 5.2 Engineer

1. **Add a new paper-based strategy**
   - “Given a new PDF paper, I want a clear template for adding a new strategy (math, config, implementation, tests, documentation).”

2. **Wrap existing libraries**
   - “I want to be able to add an adapter around an external package (e.g. Hudson & Thames / mlfinlab) without rewriting the engine.”

3. **Debug / Inspect**
   - “I need to be able to view intermediate outputs (e.g. signals, raw weights) for a specific strategy to debug behavior.”

---

## 6. Strategy & Research Requirements

### 6.1 Strategy Interface

Define a standard Python interface for strategies:

```python
class OlpsStrategy:
    id: str                    # unique identifier
    name: str                  # human-readable name
    paper_ref: str | None      # reference to research paper (e.g. "Huang et al. 2013")
    library_ref: str | None    # e.g. "mlfinlab.olps.eg"

    def run(self, prices_df, config) -> "StrategyResult":
        """
        prices_df: DataFrame indexed by date, columns = assets (prices or returns)
        config: strategy-specific configuration (hyperparameters)
        returns: StrategyResult
        """
````

`StrategyResult` should include:

* `weights` (DataFrame: date × asset)
* `gross_portfolio_values` (Series)
* `net_portfolio_values` (Series, after costs)
* `turnover` (Series)
* `metadata` (dict: any extra info, e.g. hyperparams, intermediate signals)

### 6.2 Strategy Types

#### 6.2.1 Baseline Strategies (MVP)

* **Equal Weight (EW)** – Rebalanced at chosen frequency.
* **Buy & Hold (BH)** – Initial equal weights, no rebalancing.
* **Constant Rebalanced Portfolio (CRP)** – Fixed target weights, rebalanced with specified frequency.

#### 6.2.2 Research Strategies (from PDFs)

At least the following:

* **Exponential Gradient (EG)** – classic OLPS algorithm.
* **One or more advanced OLPS strategies** from recent papers (to be selected by the quant, e.g. OLMAR, ROLMAR, CORN-K, etc.).

Requirements:

* RS-1: Each research strategy must have:

  * `paper_ref` (e.g. title + year).
  * Documented math and pseudocode in an internal markdown or docstring.
  * Config struct with validated hyperparameters.
* RS-2: Implementation should be **from scratch** unless explicitly decided otherwise, using the paper as the reference.
* RS-3: Where an external library is used as reference, code should be adapted and documented, not blindly copy-pasted (respect licensing).

#### 6.2.3 External Library Strategies (Optional)

* Wrap strategies from external libraries (e.g. Hudson & Thames / `mlfinlab`), if licensing and access allow.

Requirements:

* EL-1: External libraries must be isolated behind an adapter layer.
* EL-2: There must be a clear documentation of:

  * Library name and version.
  * License compatibility.
* EL-3: If the library is not available in some environments, the adapter must fail gracefully (strategy marked “unavailable”).

---

## 7. Rebalancing & Cost Model

### 7.1 Rebalancing Frequency

Supported values:

* `1D` – Every trading day.
* `1W` – Weekly (first trading day of each week).
* `1M` – Monthly (first trading day of each month).
* `N_DAYS` – Custom integer frequency (e.g. every 5 trading days).

Requirements:

* RF-1: The backtest config must specify `rebalance_frequency`.
* RF-2: The engine must only execute trades on rebalancing dates.
* RF-3: Turnover and costs must be computed **only** on those dates.

### 7.2 Maxblue Cost Model

Configurable parameters (defaults approximating Maxblue):

* `commission_rate`: e.g. `0.0025` (0.25% of trade volume).
* `commission_min`: e.g. `8.90 EUR`.
* `commission_max`: e.g. `58.90 EUR`.
* `exchange_fee`: e.g. `2.00 EUR` per order.
* `currency`: e.g. `EUR`.

Per trade:

```text
trade_notional = abs(shares_traded * price)
commission_raw = commission_rate * trade_notional
commission = min(max(commission_raw, commission_min), commission_max)
total_fee = commission + exchange_fee
```

Requirements:

* CM-1: Cost parameters must be stored in a config (or DB) and editable via admin UI.
* CM-2: Backtest must be run in two modes:

  * **Gross**: ignore costs.
  * **Net**: subtract costs from portfolio cash.
* CM-3: Summary metrics must include:

  * Total commissions, total exchange fees.
  * Average fee per rebalance.
  * Difference between gross and net terminal value.

---

## 8. Data Layer

### 8.1 Universe CSV

Required columns:

* `sector`
* `name`
* `isin`
* `wkn` (optional)
* `notes` (optional)

Requirements:

* DU-1: Validate uniqueness and presence of `isin`.
* DU-2: Provide a simple admin function to reload/refresh the universe from CSV.
* DU-3: Allow filtering by `sector` in backend and UI.

### 8.2 ISIN → Ticker Mapping

* Use an external mapper (e.g. OpenFIGI or similar).
* Store mapping in DB table: `isin`, `ticker`, `exchange`, `provider`, `last_updated`.

Requirements:

* IM-1: Job to populate missing mappings.
* IM-2: Allow manual override in an admin screen or config file.
* IM-3: Backtest must ignore instruments with no valid ticker mapping (log a warning).

### 8.3 Historical Prices

* Frequency: daily.
* Fields:

  * `date`
  * `ticker`
  * `adj_close` (preferred)
  * Optional: `open`, `high`, `low`, `volume`.

Requirements:

* MD-1: Implement a fetcher that can download price history for all mapped tickers over a specified date range.
* MD-2: Implement storage (DB or files) and retrieval for efficient backtesting.
* MD-3: Implement a scheduled job (cron) to refresh last N days each day.

---

## 9. Backtest & Experiment Management

### 9.1 Backtest Config

A backtest is defined by:

* Universe:

  * Selected sectors and/or explicit asset list.
* Time range:

  * `start_date`, `end_date`.
* Strategies:

  * List of strategy IDs plus per-strategy hyperparameters.
* Rebalancing:

  * One or more frequencies: `["1D", "1W", "1M"]`.
* Cost model:

  * Parameters described in section 7.2, plus `enabled` flag.
* Meta:

  * `name`, `description`, `tags` (e.g. paper IDs).

Example (JSON):

```json
{
  "name": "eg_vs_crp_2015_2025",
  "start_date": "2015-01-01",
  "end_date": "2025-01-01",
  "universe_filter": {
    "sectors": ["Global Equity", "EM Equity", "Precious Metals"]
  },
  "strategies": [
    {
      "id": "EW",
      "params": {}
    },
    {
      "id": "CRP",
      "params": {"target_weights": "equal"}
    },
    {
      "id": "EG",
      "params": {"eta": 0.05}
    }
  ],
  "rebalance_frequencies": ["1D", "1W", "1M"],
  "cost_model": {
    "enabled": true,
    "commission_rate": 0.0025,
    "commission_min": 8.90,
    "commission_max": 58.90,
    "exchange_fee": 2.0
  },
  "initial_capital": 100000,
  "tags": ["EG-paper-2013", "maxblue-cost"]
}
```

### 9.2 Storage of Results

For each `(strategy, frequency)` pair:

* Store:

  * Summary metrics.
  * Equity curve (gross and net).
  * Turnover.
  * Total costs.
  * Weights over time.

Also store:

* Backtest config.
* Creation time and user.

Requirements:

* BE-1: Expose API to create and query backtests.
* BE-2: Provide a list of past backtests with summary metrics for quick comparison.
* BE-3: Use stable IDs so experiments can be referenced in documentation or commits.

---

## 10. Backend API

### 10.1 Example Endpoints

* `GET /api/universe`

  * Returns list of instruments with sector, ISIN, ticker.

* `GET /api/strategies`

  * Returns:

    * Strategy ID
    * Name
    * Type (baseline / research / external_library)
    * Paper reference
    * Short description
    * Default parameters

* `POST /api/backtests`

  * Accepts backtest config, returns a backtest ID.

* `GET /api/backtests`

  * Returns list of backtests with summary metrics.

* `GET /api/backtests/{id}`

  * Returns full result (config, metrics, time-series, weight matrices).

---

## 11. Dashboard / Frontend

### 11.1 Screens

1. **Universe View**

   * Table with filtering by sector.
   * Show: `name`, `sector`, `isin`, `ticker`, `notes`.

2. **Strategies Overview**

   * List all strategies:

     * Name
     * Type (Baseline, Research, Library)
     * Paper reference with link (if available)
     * Short description
     * Default hyperparameters.

3. **Backtest Configuration**

   * Controls:

     * Date range picker.
     * Universe filter (sectors).
     * Strategy selection with parameter fields.
     * Rebalancing frequencies (multi-select).
     * Cost model toggle + fields (commission, min/max, exchange fee).
   * Button to run backtest.

4. **Backtest Results**

   * **Summary table**:

     * Rows: `(strategy, frequency)` pairs.
     * Columns: Gross CAGR, Net CAGR, Net Sharpe, Max Drawdown, Total Fees, Turnover.
   * **Equity curves**:

     * Plot of gross vs net equity for selected combinations.
   * **Drawdown chart**.
   * **Weights heatmap**:

     * Select strategy + frequency.
   * **Fee diagnostics**:

     * Bar or line chart of fees over time.
     * Optional breakdown by asset or year.

5. **Backtest History**

   * List of previous backtests, searchable by tags and name.
   * Click-through to results.

---

## 12. Non-Functional Requirements

### 12.1 Performance

* Target: Backtest with ~20–60 assets, 5–10 years of daily data, 3–5 strategies, 3 frequencies:

  * Should complete within **< 10 seconds** on a standard backend node.

### 12.2 Reliability

* If data is missing for a ticker, log and skip that asset for the backtest.
* External API failures (mapping/price) must not crash the server.

### 12.3 Extensibility

* Adding a new research strategy should:

  * Require minimal boilerplate.
  * Include a single registration step so the UI picks it up automatically.

### 12.4 Licensing & Third-Party Code

* All external libraries must be:

  * Logged in a dependency file.
  * Reviewed for licensing compatibility (especially if wrapping Hudson & Thames code).
* When in doubt, **prefer implementing strategies from the paper**.

---

## 13. Implementation Sketch (Non-binding)

* **Backend**:

  * Python (FastAPI).
  * Core libs: numpy, pandas, pydantic.
  * Optional: `mlfinlab` / other libraries if licensed.

* **Data Storage**:

  * Postgres for:

    * Universe.
    * Mappings.
    * Backtests & metadata.
  * Parquet/CSV for price time series.

* **Frontend**:

  * React + TypeScript.
  * Charting: Recharts / Plotly / ECharts.

* **Deployment**:

  * Docker containers.
  * Cron or scheduler for daily data refresh.

---

## 14. Phased Plan

### Phase 1 – Data & Infrastructure

* Universe ingestion.
* ISIN→ticker mapping.
* Price fetcher & storage.
* Basic experiment storage.

### Phase 2 – Strategy Engine (Baselines)

* Implement EW, BH, CRP.
* Implement cost model & rebalancing.
* Build basic API and CLI backtester.

### Phase 3 – Research Strategies

* Implement first 1–2 paper-based OLPS strategies from PDFs.
* Add strategy metadata & documentation.
* Optionally add 1 external library-based strategy (adapter).

### Phase 4 – Dashboard

* Universe & strategy views.
* Backtest config UI.
* Results visualization.
* Backtest history.

### Phase 5 – Extensions

* More strategies from new papers.
* Enhanced diagnostics.
* Advanced hyperparameter sweeps.

---

These instructions are for AI coding agents working in this repo to build a research-grade OLPS (Online Portfolio Selection) backtesting + dashboard stack.

### Architecture & key directories

- This repo is currently a **skeleton**: PRD lives in `.github/copilot-instructions.md`, raw inputs live under `documents/`.
- `documents/etf_universe_full_clean.csv` – curated ETF/ETC universe; treat `isin` as primary key, `sector` as main filter.
- `documents/*.pdf` – OLPS research papers; implementations must follow the papers, not copy any third-party source.
- Target architecture (to align new code with):
  - **Backend**: Python (FastAPI), strategy engine + backtester, Maxblue cost model, experiment storage.
  - **Data**: Postgres for universe/mappings/backtests, Parquet/CSV for price time series.
  - **Frontend**: React + TypeScript, dashboard for universe, strategy catalog, backtest config & results.

### Python environment & tooling

- Use **pyenv** and create a virtualenv named **`olps`** (Python 3.11+ preferred).
- Assume core libs: `numpy`, `pandas`, `pydantic`, `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`; add `yfinance` or similar for prices if needed.
- When adding Python modules, also add a top-level `pyproject.toml` or `requirements.txt` and keep them in sync with imports.

### Strategy engine conventions

- Implement strategies as Python classes following this interface (in a module like `backend/strategies/base.py`):
  ```python
  class OlpsStrategy:
      id: str
      name: str
      paper_ref: str | None
      library_ref: str | None

      def run(self, prices_df, config) -> "StrategyResult":
          """prices_df: index=date, columns=assets; returns StrategyResult."""
  ```
- `StrategyResult` should at least expose: `weights` (DataFrame), `gross_portfolio_values` (Series), `net_portfolio_values` (Series), `turnover` (Series), `metadata` (dict).
- Provide **baseline strategies first**: Equal Weight (EW), Buy & Hold (BH), Constant Rebalanced Portfolio (CRP) in e.g. `backend/strategies/baseline.py`.
- For research strategies (EG, OLMAR variants, etc.), add 1 file per paper with:
  - `paper_ref` field (e.g. "Huang et al. 2013 – Exponential Gradient").
  - Short docstring summarizing the math + key hyperparameters.

### Rebalancing & Maxblue cost model

- Implement a reusable rebalancing engine (e.g. `backend/backtest/rebalance.py`) that:
  - Supports frequencies: `"1D"`, `"1W"`, `"1M"`, and custom `N_DAYS`.
  - Only trades on rebalance dates and computes turnover there.
- Implement Maxblue-like cost calculation in one place (e.g. `backend/backtest/costs.py`):
  ```text
  commission_raw = commission_rate * trade_notional
  commission = min(max(commission_raw, commission_min), commission_max)
  total_fee = commission + exchange_fee
  ```
- Backtests should be able to run **gross** and **net** modes; always store both equity curves.

### Data ingestion & universe handling

- Write a loader (e.g. `backend/data/universe.py`) that reads `documents/etf_universe_full_clean.csv`, validates `isin` uniqueness, and exposes filters by `sector`.
- Price history: design a fetcher abstraction (e.g. `backend/data/prices.py`) that can:
  - Take a list of tickers and a date range, download daily OHLC/adj_close.
  - Persist to disk (Parquet/CSV) for repeatable backtests.
- ISIN→ticker mapping should live in a dedicated table or file; backtests must skip instruments without a valid ticker but log them.

### Backtests, experiments, and API

- Represent a backtest config close to the JSON in the PRD (name, date range, universe filter, strategies, frequencies, cost model, initial capital, tags).
- Implement a FastAPI app with at least:
  - `GET /api/universe` – list universe entries.
  - `GET /api/strategies` – list registered strategies and default params.
  - `POST /api/backtests` – submit a new backtest, return an ID.
  - `GET /api/backtests` and `GET /api/backtests/{id}` – query summaries and full results.
- Store per-(strategy, frequency) metrics plus weight matrices so the frontend can plot equity, drawdown, and weights heatmaps.

### Frontend expectations

- Frontend stack: React + TypeScript; choose a chart lib (Recharts/Plotly/ECharts) and keep all backtest data coming from the API (no CSV parsing in the UI).
- Provide screens for: Universe view, Strategies overview, Backtest configuration form, Backtest results (equity/drawdown/fees/weights), and Backtest history.

### Licensing & external libraries

- When referencing external OLPS libraries (e.g. `mlfinlab`), isolate them under an adapter module (e.g. `backend/strategies/external/`) and fail gracefully if missing.
- Do **not** copy code from proprietary or unclear-license sources; implement algorithms from the papers and document any deviations.


## work-documentation
Every new code addition must be documented either in a folder named work-documentation  Documentation should include:
- Key design decisions
- Instructions on how to use or extend the code
The file should be saved in the folder with the date and a brief description of the content as follows: YYYY-MM-DD_brief-description.md


## Setting up pyenv and virtualenv
The olps virtualenv has been created with Python 3.11.9. To activate it:

```bash
# In each new terminal session, run:
source activate_olps.sh

# Or, for permanent activation, add to ~/.zshrc:
eval "$(/opt/homebrew/bin/brew shellenv)"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

**Note**: If you accidentally run `pyenv shell <other-version>`, simply run `source activate_olps.sh` again to reactivate the olps environment.

Always ensure the olps virtualenv is active (prompt shows `(olps)`) when working on this repo.
