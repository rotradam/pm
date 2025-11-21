# Portfolio Builder - Architecture & Vision Roadmap

## 1. Vision Overview
**"Linear for Portfolio Management"**

The Portfolio Builder is designed to be a premium, "Linear-like" interface for exploring assets, building strategies, and eventually executing trades via smart contracts.

**Core Value Proposition:**
- **For Users:** A single, unified dashboard to manage assets across CEXs and DEXs, backtest strategies, and automate rebalancing.
- **For Exchanges:** Increased trade volume driven by the platform's rebalancing logic.
- **Revenue Model:** The platform collects maker/taker fees during rebalancing via its smart contract layer.

## 2. System Architecture

The system is divided into three main layers: **Presentation (Frontend)**, **Core Logic (Backend)**, and **Execution (Smart Contracts/Connectors)**.

### A. Presentation Layer (Frontend)
**Stack:** Next.js (App Router), TypeScript, Tailwind CSS, Shadcn UI, TanStack Query.

*   **Dashboard:** Visualizes asset universe, portfolio performance, and strategy metrics.
*   **Strategy Builder:** UI for users to define parameters (e.g., "Top 10 Crypto by Market Cap", "Rebalance Monthly").
*   **Wallet Integration (Future):** Web3 connection (MetaMask, Rabby, etc.) for signing transactions.
*   **Execution Monitor (Future):** Real-time status of rebalancing trades and smart contract interactions.

### B. Core Logic Layer (Backend)
**Stack:** FastAPI, Python, SQLite (Metadata), Pandas/NumPy (Analysis).

*   **Data Service (Current):**
    *   `backend/data/`: Manages asset universe (Stocks, Crypto, ETFs).
    *   `backend/api/`: Serves historical data and asset details.
*   **Strategy Engine (Current):**
    *   `backend/strategies/`: Runs backtests (DOLPS, WAEG, etc.) and calculates target portfolio weights.
*   **Execution Engine (Future):**
    *   `backend/execution/`: Translates target weights into specific trade orders (Buy/Sell).
    *   `backend/connectors/`: Standardized interfaces for CEX APIs (Binance, Kraken) and DEX SDKs.

### C. Execution Layer (Future)
**Stack:** Solidity (EVM), Rust (Solana/Near), CCIP (Cross-Chain).

*   **Portfolio Smart Contracts:**
    *   **Non-custodial contracts** that execute swaps based on the Backend's signals.
    *   **Fee Collection:** Automatically deducts a small fee from the rebalancing volume.
*   **Routing:**
    *   **CEX:** API keys managed securely (or via MPC) to execute trades on centralized exchanges.
    *   **DEX:** Smart contracts route swaps through aggregators (1inch, Jupiter) or direct pools (Uniswap, Hyperliquid).

## 3. Scalability Roadmap

### Phase 1: MVP (Current)
*   **Goal:** Exploration & Backtesting.
*   **Features:**
    *   Asset Universe (Stocks + Crypto).
    *   Strategy Backtesting (Historical performance).
    *   "Linear-like" UI for browsing and analysis.
*   **Data Flow:** `External APIs (Yahoo/CoinGecko) -> Backend DB -> Frontend`.

### Phase 2: Portfolio Management (Next)
*   **Goal:** User Portfolios & Simulation.
*   **Features:**
    *   User Accounts (Supabase/Auth0).
    *   Create "Virtual Portfolios" to track performance without real money.
    *   Save custom strategies.

### Phase 3: Execution & Integration (Future)
*   **Goal:** Live Trading & Revenue.
*   **Features:**
    *   **Wallet Connect:** Users connect their wallets.
    *   **Exchange Connectors:** Users add API keys for CEXs.
    *   **Smart Contract Deployment:** Deploy the fee-collecting contracts.
    *   **Live Rebalancing:** One-click rebalance execution.

## 4. Directory Structure for Scaling

To support this vision, we will structure the codebase as follows:

```text
portfolioManagement/
├── frontend/               # Next.js App
│   ├── src/app/            # Pages
│   ├── src/components/     # UI Components
│   └── src/features/       # Feature-based modules (e.g., /trading, /wallet)
│
├── backend/                # FastAPI App
│   ├── api/                # REST Endpoints
│   ├── data/               # Data Fetching & Storage
│   ├── strategies/         # Quant Logic (Backtesting)
│   ├── execution/          # [FUTURE] Order Management System (OMS)
│   └── connectors/         # [FUTURE] Exchange Integrations (CEX/DEX)
│
└── contracts/              # [FUTURE] Smart Contracts (Solidity/Rust)
```
