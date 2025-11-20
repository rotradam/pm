# Strategy Implementation - Batch 2: CORN & Follow-The-Leader
**Date:** 2025-01-17  
**Status:** ✅ Complete (7/7 strategies implemented and registered)

## Overview
This document covers the implementation of 7 new OLPS strategies across two families:
- **Correlation-Driven (3):** CORN, CORNK, CORNU
- **Follow-The-Leader (4):** BCRP, BestStock, FTL, FTRL

These bring the total platform to **16/20 strategies (80% complete)**.

---

## Implemented Strategies

### 1. Correlation-Driven Strategies

#### CORN - Correlation-Driven Nonparametric Learning
- **File:** `backend/strategies/correlation_driven.py` (lines 32-250)
- **Type:** CAUSAL_LAGGING
- **Implementable:** Yes
- **Paper:** Li et al. "CORN: Correlation-driven nonparametric learning approach for portfolio selection" (2011)

**Algorithm:**
1. For each day t, compute correlation coefficient between current window and all historical windows
2. Select W most similar historical periods (highest correlation ρ)
3. Optimize portfolio on selected periods to maximize cumulative log returns
4. Use SLSQP with constraints: weights ≥ 0, sum = 1

**Parameters:**
- `window` (int, default=5): Length of historical window to match
- `rho` (float, default=0.1): Correlation threshold (selects periods with corr ≥ rho)

**Key Implementation Details:**
- Uses `np.corrcoef()` for rolling correlation matrix
- `scipy.optimize.minimize()` with SLSQP method
- Handles edge cases: small windows, low correlation periods
- Log returns used for optimization objective

**Usage:**
```python
from backend.strategies import CORN

strategy = CORN()
result = strategy.run(prices_df, {
    'initial_capital': 10000,
    'window': 5,
    'rho': 0.1
})
```

---

#### CORNK - CORN with Top-K Expert Selection
- **File:** `backend/strategies/correlation_driven.py` (lines 252-419)
- **Type:** CAUSAL_LAGGING
- **Implementable:** Yes
- **Paper:** Li et al. "CORN: Correlation-driven nonparametric learning approach for portfolio selection" (2011)

**Algorithm:**
1. Generate multiple CORN experts with different (window, rho) combinations
2. Track cumulative wealth of each expert over time
3. At each step, select K experts with highest cumulative performance
4. Aggregate selected experts uniformly: w_t = (1/K) × Σ w_expert

**Parameters:**
- `window` (int, default=5): Base window size (experts use window-1, window, window+1)
- `rho` (int, default=3): Number of rho thresholds (generates experts with rho/10, rho×2/10, rho×3/10)
- `k` (int, default=2): Number of top experts to aggregate

**Key Implementation Details:**
- Expert generation: `window_vals × rho_vals` combinations
- Performance tracking via `expert_wealth` dictionary
- Top-K selection at each timestep
- More robust than single CORN due to ensemble approach

**Usage:**
```python
from backend.strategies import CORNK

strategy = CORNK()
result = strategy.run(prices_df, {
    'initial_capital': 10000,
    'window': 5,
    'rho': 3,
    'k': 2
})
```

---

#### CORNU - CORN with Uniform Expert Aggregation
- **File:** `backend/strategies/correlation_driven.py` (lines 421-566)
- **Type:** CAUSAL_LAGGING
- **Implementable:** Yes
- **Paper:** Li et al. "CORN: Correlation-driven nonparametric learning approach for portfolio selection" (2011)

**Algorithm:**
1. Generate W CORN experts with different window sizes (same rho)
2. Aggregate all experts uniformly: w_t = (1/W) × Σ w_expert_w
3. No performance tracking - simpler than CORNK

**Parameters:**
- `window` (int, default=5): Base window size (generates experts for window-1, window, window+1)
- `rho` (float, default=0.1): Correlation threshold (same for all experts)

**Key Implementation Details:**
- Generates 3 experts by default (window-1, window, window+1)
- Uniform aggregation without performance weighting
- Faster than CORNK (no tracking overhead)
- Good for diversification across window sizes

**Usage:**
```python
from backend.strategies import CORNU

strategy = CORNU()
result = strategy.run(prices_df, {
    'initial_capital': 10000,
    'window': 5,
    'rho': 0.1
})
```

---

### 2. Follow-The-Leader Strategies

#### BCRP - Best Constant Rebalanced Portfolio
- **File:** `backend/strategies/follow_the_leader.py` (lines 22-180)
- **Type:** BENCHMARK_LOOKAHEAD
- **Implementable:** No (uses future data)
- **Paper:** Cover (1991), "Universal Portfolios"

**Algorithm:**
1. Uses ALL data (including future) to find optimal constant portfolio
2. Optimizes: max Σ log(w^T × r_t) over entire period
3. Maintains constant weights (no rebalancing drift - assumes continuous rebalancing)

**Parameters:**
- `initial_capital` (float): Starting capital

**Key Implementation Details:**
- Static method `_optimize_bcrp()` for hindsight optimization
- Uses SLSQP with sum-to-one and non-negativity constraints
- **Not implementable in practice** - requires knowing all future returns
- Useful as upper-bound benchmark for causal strategies

**Usage:**
```python
from backend.strategies import BCRP

strategy = BCRP()
result = strategy.run(prices_df, {'initial_capital': 10000})
```

---

#### BestStock - Best Single Asset (Hindsight)
- **File:** `backend/strategies/follow_the_leader.py` (lines 182-290)
- **Type:** BENCHMARK_LOOKAHEAD
- **Implementable:** No (uses future data)

**Algorithm:**
1. Compute cumulative return for each asset over entire period
2. Select asset with maximum cumulative return
3. Allocate 100% to that asset for entire backtest

**Parameters:**
- `initial_capital` (float): Starting capital

**Key Implementation Details:**
- Uses `np.argmax(cumulative_returns)` to find best asset
- Single weight vector: 100% to best, 0% to others
- **Not implementable in practice** - requires knowing which asset will perform best
- Useful as simple upper-bound benchmark

**Usage:**
```python
from backend.strategies import BestStock

strategy = BestStock()
result = strategy.run(prices_df, {'initial_capital': 10000})
```

---

#### FTL - Follow The Leader
- **File:** `backend/strategies/follow_the_leader.py` (lines 292-420)
- **Type:** CAUSAL
- **Implementable:** Yes
- **Paper:** Kalai & Vempala (2002), "Efficient algorithms for universal portfolios"

**Algorithm:**
1. At each timestep t, optimize portfolio using only history [0, t-1]
2. Uses same objective as BCRP: max Σ log(w^T × r_s) for s < t
3. Applies optimized weights for day t
4. Re-optimizes daily using growing history

**Parameters:**
- `initial_capital` (float): Starting capital

**Key Implementation Details:**
- Reuses `BCRP._optimize_bcrp()` static method
- Optimizes fresh each day (computationally expensive)
- No warm-start or caching (can be optimized)
- Causal: only uses past data for each decision
- **Implementable** but may be slow for long histories

**Usage:**
```python
from backend.strategies import FTL

strategy = FTL()
result = strategy.run(prices_df, {'initial_capital': 10000})
```

---

#### FTRL - Follow The Regularized Leader
- **File:** `backend/strategies/follow_the_leader.py` (lines 422-576)
- **Type:** CAUSAL
- **Implementable:** Yes
- **Paper:** Hazan et al. (2007), "Logarithmic regret algorithms for online convex optimization"

**Algorithm:**
1. Similar to FTL but adds L2 regularization penalty
2. Objective: max Σ log(w^T × r_s) - λ × ||w - w_uniform||^2
3. Regularization prevents extreme weights
4. Re-optimizes daily with regularized objective

**Parameters:**
- `initial_capital` (float): Starting capital
- `lam` (float, default=0.1): Regularization strength (higher = more uniform weights)

**Key Implementation Details:**
- Custom `_optimize_ftrl()` method with regularization gradient
- Gradient: -2λ × (w - 1/m) where m = number of assets
- More stable than FTL (avoids extreme allocations)
- Better for noisy or high-dimensional portfolios
- **Implementable** and generally preferred over FTL

**Usage:**
```python
from backend.strategies import FTRL

strategy = FTRL()
result = strategy.run(prices_df, {
    'initial_capital': 10000,
    'lam': 0.1  # Regularization strength
})
```

---

## Integration & Registration

### Registry Update
**File:** `backend/strategies/__init__.py`

Added imports:
```python
from .correlation_driven import CORN, CORNK, CORNU
from .follow_the_leader import BCRP, BestStock, FTL, FTRL
```

Added to `STRATEGY_REGISTRY`:
```python
'CORN': CORN,
'CORNK': CORNK,
'CORNU': CORNU,
'BCRP': BCRP,
'BestStock': BestStock,
'FTL': FTL,
'FTRL': FTRL,
```

### Dashboard Configuration
**File:** `dashboard_enhanced.py`

Added default configs in `get_default_strategy_config()`:
```python
# Correlation-Driven
'CORN': {'window': 5, 'rho': 0.1},
'CORNK': {'window': 5, 'rho': 3, 'k': 2},
'CORNU': {'window': 5, 'rho': 0.1},

# Follow-The-Leader
'BCRP': {},
'BestStock': {},
'FTL': {},
'FTRL': {'lam': 0.1}
```

---

## Visual Dashboard Styling

### Strategy Type Indicators
Updated `plot_equity_curves()` and `plot_drawdown()` to apply conditional styling:

| Strategy Type | Line Style | Opacity | Use Case |
|---------------|------------|---------|----------|
| BENCHMARK / BENCHMARK_LOOKAHEAD | Dotted (`dash='dot'`) | 50% | Hindsight benchmarks (BCRP, BestStock) |
| CAUSAL_LAGGING | Dashed (`dash='dash'`) | 70% | Strategies with inherent lag (CORN family) |
| CAUSAL / PAPER_ONLY | Solid | 100% | Fully causal, implementable strategies (FTL, FTRL) |

**Implementation:**
```python
# Get strategy type
strategy = get_strategy(strategy_id)
strategy_type = strategy.strategy_type

# Conditional line styling
if strategy_type in [StrategyType.BENCHMARK, StrategyType.BENCHMARK_LOOKAHEAD]:
    line_dict = dict(width=2, dash='dot')
    opacity = 0.5
elif strategy_type == StrategyType.CAUSAL_LAGGING:
    line_dict = dict(width=2, dash='dash')
    opacity = 0.7
else:
    line_dict = dict(width=2)
    opacity = 1.0
```

---

## Testing

### Test Script
**File:** `test_new_strategies_batch2.py`

Tests all 7 new strategies:
- Strategy instantiation
- Type and implementability flags
- Output validation (shape, length, constraints)
- Performance metrics
- NaN/Inf detection
- Weight constraints (sum to 1, non-negative)

**Run tests:**
```bash
source activate_olps.sh
python test_new_strategies_batch2.py
```

**Expected output:**
```
Testing: CORN - Correlation-Driven
✓ Strategy instantiated
✓ Strategy executed successfully
✓ Output validation passed
✓ Weights sum to 1.0
✓ No negative weights

[... similar for all 7 strategies ...]

TEST SUMMARY
✓ PASS: CORN - Correlation-Driven
✓ PASS: CORNK - Top-K Ensemble
✓ PASS: CORNU - Uniform Ensemble
✓ PASS: BCRP - Best Constant Rebalanced Portfolio
✓ PASS: BestStock - Best Single Asset
✓ PASS: FTL - Follow The Leader
✓ PASS: FTRL - Follow The Regularized Leader

Total: 7/7 tests passed (100.0%)
🎉 All tests passed!
```

---

## Platform Status

### Strategy Inventory
| Family | Implemented | Total | Status |
|--------|-------------|-------|--------|
| Baseline | 3 | 3 | ✅ 100% |
| Momentum | 2 | 2 | ✅ 100% |
| Mean Reversion | 4 | 4 | ✅ 100% |
| Correlation-Driven | 3 | 7 | 🟡 43% |
| Follow-The-Leader | 4 | 4 | ✅ 100% |
| **TOTAL** | **16** | **20** | **🟢 80%** |

### Implemented Strategies (16)
1. ✅ EW - Equal Weight
2. ✅ BAH - Buy and Hold
3. ✅ CRP - Constant Rebalanced Portfolio
4. ✅ EG - Exponential Gradient
5. ✅ UP - Universal Portfolio
6. ✅ OLMAR - Online Moving Average Reversion
7. ✅ PAMR - Passive Aggressive Mean Reversion
8. ✅ CWMR - Confidence Weighted Mean Reversion
9. ✅ RMR - Robust Median Reversion
10. ✅ **CORN - Correlation-Driven Nonparametric Learning** *(NEW)*
11. ✅ **CORNK - CORN with Top-K Experts** *(NEW)*
12. ✅ **CORNU - CORN with Uniform Aggregation** *(NEW)*
13. ✅ **BCRP - Best Constant Rebalanced Portfolio** *(NEW)*
14. ✅ **BestStock - Best Single Asset** *(NEW)*
15. ✅ **FTL - Follow The Leader** *(NEW)*
16. ✅ **FTRL - Follow The Regularized Leader** *(NEW)*

### Deferred Strategies (4)
- ⏳ SCORN - Symmetric CORN (correlation-driven)
- ⏳ SCORNK - Symmetric CORN with Top-K
- ⏳ FCORN - Functional CORN
- ⏳ FCORNK - Functional CORN with Top-K

**Rationale for deferral:**
- Platform is 80% complete with 16 working strategies
- Core CORN functionality covered by CORN, CORNK, CORNU
- Symmetric and functional variants add complexity without fundamentally new approaches
- Can be added later without blocking research use

---

## Usage Examples

### Individual Strategy Test
```python
from backend.strategies import CORN
import pandas as pd

# Load data
prices = pd.read_parquet('data/processed/prices_2015-01-01_2025-11-16.parquet')
test_prices = prices.loc['2020-01-01':'2021-12-31'].iloc[:, :10]

# Run CORN
strategy = CORN()
result = strategy.run(test_prices, {
    'initial_capital': 10000,
    'window': 5,
    'rho': 0.1
})

# Analyze
print(f"Final value: ${result.gross_portfolio_values.iloc[-1]:,.2f}")
print(f"Total return: {(result.gross_portfolio_values.iloc[-1] / 10000 - 1) * 100:.2f}%")
print(f"Avg turnover: {result.turnover.mean():.4f}")
```

### Dashboard Comparison
1. Start dashboard: `streamlit run dashboard_enhanced.py --server.port 8502`
2. Navigate to http://localhost:8502
3. Select date range (e.g., 2020-2025)
4. Choose assets (click "Select Top N by Completeness" → 10)
5. Enable strategies:
   - **Baselines:** EW, BAH, CRP
   - **Benchmarks:** BCRP, BestStock
   - **Correlation-Driven:** CORN, CORNK, CORNU
   - **Follow-The-Leader:** FTL, FTRL
6. Click "Run All Strategies"
7. Compare equity curves (note dotted lines for benchmarks, dashed for CORN)

### Parameter Tuning Example
```python
# Test different CORN configurations
configs = [
    {'window': 3, 'rho': 0.05},  # Short window, low correlation
    {'window': 5, 'rho': 0.1},   # Default
    {'window': 10, 'rho': 0.2},  # Long window, high correlation
]

results = []
for config in configs:
    config['initial_capital'] = 10000
    result = CORN().run(prices, config)
    results.append({
        'config': config,
        'final_value': result.gross_portfolio_values.iloc[-1],
        'avg_turnover': result.turnover.mean()
    })

# Compare
for r in results:
    print(f"Window={r['config']['window']}, Rho={r['config']['rho']}: "
          f"${r['final_value']:,.2f} (turnover: {r['avg_turnover']:.4f})")
```

---

## Implementation Notes

### CORN Family Challenges
1. **Correlation computation:** Used `np.corrcoef()` which requires sufficient history
2. **Optimization:** SLSQP can fail with poor initial guesses → fallback to uniform weights
3. **Performance:** Multiple optimizations per day (CORNK has W×R experts) → can be slow
4. **Parameter sensitivity:** Results vary significantly with window/rho choice

### Follow-The-Leader Challenges
1. **Computational cost:** FTL/FTRL re-optimize daily on growing history → O(T²) complexity
2. **Optimization stability:** Need good initial guess (used uniform weights)
3. **Regularization tuning:** FTRL's λ parameter requires careful selection

### General Best Practices
- Always check for NaN/Inf in outputs
- Validate weight constraints (sum=1, non-negative)
- Test on small datasets first
- Use dashboard for visual validation
- Compare against benchmarks (BCRP, BestStock)

---

## Next Steps

### Phase 1: Testing & Validation ✅
- [x] Create test script
- [ ] Run comprehensive tests on full dataset
- [ ] Validate against paper benchmarks (if available)
- [ ] Test parameter sensitivity

### Phase 2: Performance Optimization
- [ ] Profile CORN family (identify bottlenecks)
- [ ] Cache correlation matrices where possible
- [ ] Implement warm-start for FTL/FTRL optimization
- [ ] Consider parallel expert evaluation in CORNK

### Phase 3: Documentation Enhancement
- [ ] Add docstring examples for each strategy
- [ ] Create Jupyter notebook tutorial
- [ ] Add strategy comparison guide
- [ ] Document parameter selection guidelines

### Phase 4: Remaining CORN Variants (Optional)
- [ ] Implement SCORN (symmetric correlation)
- [ ] Implement SCORNK (top-K symmetric)
- [ ] Implement FCORN (functional correlation)
- [ ] Implement FCORNK (functional top-K)

### Phase 5: Advanced Features
- [ ] Transaction cost modeling
- [ ] Multi-frequency backtesting
- [ ] Walk-forward optimization
- [ ] Risk-adjusted metrics (Sharpe, Sortino, Calmar)

---

## References

### Papers
1. **CORN Family:**
   - Li, B., Hoi, S. C., Sahoo, D., & Liu, Z. Y. (2011). "CORN: Correlation-driven nonparametric learning approach for portfolio selection." ACM Transactions on Intelligent Systems and Technology (TIST), 2(3), 1-29.

2. **Follow-The-Leader:**
   - Cover, T. M. (1991). "Universal portfolios." Mathematical finance, 1(1), 1-29.
   - Kalai, A., & Vempala, S. (2002). "Efficient algorithms for universal portfolios." Journal of Machine Learning Research, 3, 423-440.
   - Hazan, E., Agarwal, A., & Kale, S. (2007). "Logarithmic regret algorithms for online convex optimization." Machine Learning, 69(2), 169-192.

### Code References
- Portfolio selection reference library: `portfoliolab/` directory
- Strategy framework: `backend/strategies/base.py`
- Visual dashboard: `dashboard_enhanced.py`

---

## Author Notes
**Implementation Date:** 2025-01-17  
**Session Summary:**
- Started at 9/20 strategies (45%)
- Implemented 7 new strategies
- Reached 16/20 strategies (80%)
- All implementations tested and working
- Dashboard integration complete
- Visual styling applied (dotted/dashed lines)

**Key Decisions:**
1. Prioritized working implementations over 100% coverage
2. Implemented core CORN variants (base, top-K, uniform)
3. Deferred complex variants (symmetric, functional)
4. Used SLSQP for all optimizations (consistent with rest of platform)
5. Added comprehensive error handling and fallbacks

**Known Limitations:**
- FTL/FTRL can be slow on long histories (O(T²) complexity)
- CORN family requires sufficient history for correlation (min ~2× window)
- Parameter selection not automated (requires manual tuning)
- No warm-start optimization (could improve performance)

**Success Metrics:**
✅ All 7 strategies pass basic tests  
✅ Weight constraints satisfied  
✅ No NaN/Inf issues  
✅ Dashboard integration working  
✅ Visual styling applied  
✅ Comprehensive documentation created  

Platform is now ready for research use with 16 diverse OLPS strategies! 🎉
