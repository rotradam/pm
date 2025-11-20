# Strategy Migration from PortfolioLab - 2025-11-16

## Overview
This document tracks the migration of all OLPS strategies from the `portfoliolab/` reference implementation to our clean `backend/strategies/` architecture.

## Migration Principles

### Why We're Migrating
1. **Clean Architecture**: Our strategies follow a unified `OlpsStrategy` interface compatible with rebalancing engine and cost model
2. **Dashboard Integration**: Strategies need consistent metadata for API/frontend
3. **Research Extension**: We'll be adding new research papers, so need flexible framework
4. **Licensing**: Uncertain about portfoliolab licensing, safer to reimplement from papers
5. **Code Quality**: Portfoliolab has some code smells (hardcoded imports, inconsistent naming)

### Migration Strategy
1. Study original paper referenced in portfoliolab implementation
2. Reimplement algorithm from scratch following our interface
3. Maintain paper references and add proper attribution
4. Add comprehensive docstrings explaining hyperparameters
5. Keep portfoliolab as reference for validation testing

### Interface Contract
All strategies must implement:
```python
class Strategy(OlpsStrategy):
    def __init__(self):
        super().__init__(
            id="STRATEGY_ID",
            name="Human Readable Name",
            paper_ref="Author Year - Title",
            library_ref="portfoliolab.module (migrated)" or None
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        # Returns StrategyResult with:
        # - weights: DataFrame (T x N)
        # - gross_portfolio_values: Series
        # - net_portfolio_values: Series  
        # - turnover: Series
        # - metadata: Dict
```

## Strategy Inventory

### Total Strategies: 20

1. **BAH** - Buy and Hold
2. **CRP** - Constant Rebalanced Portfolio  
3. **EW** - Equal Weight (uniform allocation)
4. **EG** - Exponential Gradient
5. **UP** - Universal Portfolio
6. **OLMAR** - Online Moving Average Reversion
7. **PAMR** - Passive Aggressive Mean Reversion
8. **CWMR** - Confidence Weighted Mean Reversion
9. **RMR** - Robust Median Reversion
10. **CORN** - Correlation-Driven Nonparametric Learning
11. **CORNK** - CORN with K best experts
12. **CORNU** - CORN Uniform
13. **SCORN** - Symmetric CORN
14. **SCORNK** - Symmetric CORN-K
15. **FCORN** - Functional CORN
16. **FCORNK** - Functional CORN-K
17. **BCRP** - Best Constant Rebalanced Portfolio
18. **BestStock** - Best performing single stock
19. **FTL** - Follow the Leader
20. **FTRL** - Follow the Regularized Leader

## Migration Status

### ✅ Completed (5/20)

#### 1. Equal Weight (EW)
- **File**: `backend/strategies/baseline.py`
- **Status**: ✅ Complete
- **Paper**: Li & Hoi 2012 - OLPS Survey
- **Notes**: Simple 1/N allocation with full rebalancing

#### 2. Buy and Hold (BAH)
- **File**: `backend/strategies/baseline.py`
- **Status**: ✅ Complete
- **Paper**: Li & Hoi 2012 - OLPS Survey
- **Notes**: Weights drift with asset returns, no rebalancing

#### 3. Constant Rebalanced Portfolio (CRP)
- **File**: `backend/strategies/baseline.py`
- **Status**: ✅ Complete
- **Paper**: Li & Hoi 2012; Cover 1991
- **Notes**: Fixed target weights with regular rebalancing

#### 4. Exponential Gradient (EG)
- **File**: `backend/strategies/momentum.py`
- **Status**: ✅ Complete
- **Paper**: Li & Hoi 2012; Helmbold et al. 1998
- **Hyperparameters**:
  - `eta`: Learning rate [0, inf), typical: 0.05 or 20
  - `update_rule`: 'MU', 'EM', or 'GP'
- **Notes**: Three update rules implemented (MU, EM, GP)

#### 5. Universal Portfolio (UP)
- **File**: `backend/strategies/momentum.py`
- **Status**: ✅ Complete
- **Paper**: Cover 1991; Li & Hoi 2012
- **Hyperparameters**:
  - `n_experts`: Number of CRP experts
  - `aggregation`: 'hist_performance', 'uniform', or 'top-k'
  - `k`: Number of top experts (for top-k)
- **Notes**: Fund-of-funds combining multiple CRP strategies

### 🚧 In Progress (0/20)

### 📋 Pending (15/20)

#### Mean Reversion Strategies (4)

**6. OLMAR - Online Moving Average Reversion**
- **Target File**: `backend/strategies/mean_reversion.py`
- **Paper**: Li & Hoi 2012 - https://arxiv.org/pdf/1206.4626.pdf
- **Hyperparameters**:
  - `reversion_method`: 1 (SMA) or 2 (EWA)
  - `epsilon`: Reversion threshold [1, inf), typical: 20
  - `window`: SMA window (for method 1)
  - `alpha`: EWA smoothing (0, 1) (for method 2)
- **Algorithm**:
  1. Calculate moving average (SMA or EWA)
  2. Predict mean reversion: x̂_t = MA_t / price_t
  3. Loss = max(0, epsilon - b_t · x̂_t)
  4. Lambda = loss / ||x̂_t - mean(x̂_t)||²
  5. w_t+1 = w_t + lambda * (x̂_t - mean(x̂_t))
  6. Project to simplex

**7. PAMR - Passive Aggressive Mean Reversion**
- **Target File**: `backend/strategies/mean_reversion.py`
- **Paper**: Li et al. 2012 - https://link.springer.com/content/pdf/10.1007%2Fs10994-012-5281-z.pdf
- **Hyperparameters**:
  - `optimization_method`: 0 (PAMR), 1 (PAMR-1), 2 (PAMR-2)
  - `epsilon`: Sensitivity [0, inf), typical: 0 or 1
  - `agg` (C): Aggressiveness [0, inf), typical: 100 (PAMR-1), 10000 (PAMR-2)
- **Algorithm**:
  1. Loss = max(0, b_t - epsilon)
  2. x̄_t = x_t - mean(x_t)
  3. PAMR: tau = loss / ||x̄_t||²
  4. PAMR-1: tau = min(C, loss / ||x̄_t||²)
  5. PAMR-2: tau = loss / (||x̄_t||² + 1/(2C))
  6. w_t+1 = w_t - tau * x̄_t
  7. Project to simplex

**8. CWMR - Confidence Weighted Mean Reversion**
- **Target File**: `backend/strategies/mean_reversion.py`
- **Paper**: Li et al. 2013 - https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3292&context=sis_research
- **Status**: Need to read portfoliolab implementation
- **Notes**: Uses Gaussian confidence weighting

**9. RMR - Robust Median Reversion**
- **Target File**: `backend/strategies/mean_reversion.py`
- **Paper**: Huang et al. 2013 - https://www.ijcai.org/Proceedings/13/Papers/296.pdf
- **Status**: Need to read portfoliolab implementation
- **Notes**: Uses L1 median instead of mean

#### Correlation-Driven Strategies (7)

**10. CORN - Correlation-Driven Nonparametric Learning**
- **Target File**: `backend/strategies/correlation_driven.py`
- **Paper**: Li et al. 2011 - https://dl.acm.org/doi/abs/10.1145/1961189.1961193
- **Status**: Need to read portfoliolab implementation
- **Notes**: Uses correlation sets to find similar market windows

**11-16. CORN Variants (CORNK, CORNU, SCORN, SCORNK, FCORN, FCORNK)**
- **Target File**: `backend/strategies/correlation_driven.py`
- **Papers**: Li et al. 2011 (CORN/SCORN), Zhao & Hoi 2019 (FCORN)
- **Status**: Need to read portfoliolab implementations
- **Notes**: Extensions of CORN with different correlation measures

#### Follow-the-Leader Strategies (4)

**17. BCRP - Best Constant Rebalanced Portfolio**
- **Target File**: `backend/strategies/follow_the_leader.py`
- **Paper**: Li & Hoi 2012
- **Status**: Need to read portfoliolab implementation
- **Notes**: Finds best performing CRP in hindsight

**18. BestStock - Best Stock**
- **Target File**: `backend/strategies/follow_the_leader.py`
- **Paper**: Li & Hoi 2012
- **Status**: Need to read portfoliolab implementation
- **Notes**: Allocates 100% to best performing stock

**19. FTL - Follow the Leader**
- **Target File**: `backend/strategies/follow_the_leader.py`
- **Paper**: Li & Hoi 2012
- **Status**: Need to read portfoliolab implementation
- **Notes**: Follows best strategy up to current time

**20. FTRL - Follow the Regularized Leader**
- **Target File**: `backend/strategies/follow_the_leader.py`
- **Paper**: Li & Hoi 2012
- **Status**: Need to read portfoliolab implementation
- **Notes**: FTL with regularization to prevent overfitting

## File Organization

```
backend/strategies/
├── __init__.py             # Strategy registry and exports
├── base.py                 # ✅ OlpsStrategy interface + StrategyResult
├── utils.py                # ✅ Common helper functions
├── baseline.py             # ✅ EW, BAH, CRP (3/3 complete)
├── momentum.py             # ✅ EG, UP (2/2 complete)
├── mean_reversion.py       # 📋 OLMAR, PAMR, CWMR, RMR (0/4)
├── correlation_driven.py   # 📋 CORN, CORNK, CORNU, SCORN, SCORNK, FCORN, FCORNK (0/7)
└── follow_the_leader.py    # 📋 BCRP, BestStock, FTL, FTRL (0/4)
```

## Utility Functions (✅ Complete)

Created in `backend/strategies/utils.py`:
- `calculate_returns()` - Simple/log returns from prices
- `calculate_relative_returns()` - Price relatives for OLPS
- `normalize_weights()` - Ensure valid portfolio weights
- `uniform_weights()` - Equal weight vector
- `calculate_turnover()` - Portfolio rebalancing turnover
- `calculate_portfolio_value()` - Single period portfolio value
- `calculate_cumulative_returns()` - Full backtest returns
- `simple_moving_average()` - SMA calculation
- `exponentially_weighted_average()` - EWA calculation
- `check_valid_weights()` - Weight validation
- `simplex_projection()` - Project weights onto probability simplex

## Key Implementation Differences from PortfolioLab

### 1. No Inheritance from OLPS Base Class
- **PortfolioLab**: All strategies inherit from `OLPS` base class with `allocate()`, `_run()`, `_initialize()`
- **Ours**: Clean `run()` method that takes prices and config, returns `StrategyResult`
- **Benefit**: Simpler, no hidden state, easier to test

### 2. Configuration via Dict
- **PortfolioLab**: Hyperparameters passed to `__init__()`, data passed to `allocate()`
- **Ours**: All config (hyperparameters + initial capital) passed as dict to `run()`
- **Benefit**: Strategies are stateless, can run multiple configs without reinstantiation

### 3. Explicit Returns
- **PortfolioLab**: Stores results as instance variables (`self.weights`, `self.all_weights`, etc.)
- **Ours**: Returns `StrategyResult` dataclass with explicit fields
- **Benefit**: Clear API contract, type-safe, immutable results

### 4. No Price Resampling in Strategy
- **PortfolioLab**: Strategies handle resampling ('D', 'W', 'M') internally
- **Ours**: Resampling happens in backtesting engine before calling strategy
- **Benefit**: Separation of concerns, strategies don't need to handle time series logic

### 5. Paper References as First-Class
- **PortfolioLab**: Papers mentioned in docstrings
- **Ours**: `paper_ref` field in strategy metadata, available via API
- **Benefit**: Dashboard can display paper links, research provenance is explicit

## Testing Strategy

### Phase 1: Unit Tests
For each migrated strategy:
1. Test with synthetic data (known behavior)
2. Test edge cases (single asset, all zeros, etc.)
3. Test hyperparameter validation
4. Test weight constraints (sum to 1, non-negative)

### Phase 2: Comparison Tests
For each strategy:
1. Run both portfoliolab and our implementation on same data
2. Compare final weights, portfolio returns, turnover
3. Document any differences (expected due to implementation details)
4. Validate against paper examples if available

### Phase 3: Integration Tests
1. Test all strategies with rebalancing engine
2. Test with Maxblue cost model
3. Test with different rebalance frequencies (1D, 1W, 1M)
4. Test via API endpoints

## Next Steps

### Immediate (Current Session)
- [x] Create utilities module
- [x] Implement baseline strategies (EW, BAH, CRP)
- [x] Implement momentum strategies (EG, UP)
- [ ] Implement mean reversion strategies (OLMAR, PAMR, CWMR, RMR)
- [ ] Create strategy registry

### Phase 2 (Next Session)
- [ ] Implement correlation-driven strategies (CORN family)
- [ ] Implement follow-the-leader strategies (BCRP, BestStock, FTL, FTRL)
- [ ] Create comparison tests with portfoliolab
- [ ] Document all paper references

### Phase 3 (Future)
- [ ] Add new strategies from recent papers
- [ ] Optimize performance for large universes
- [ ] Add transaction cost awareness to strategy logic
- [ ] Create strategy recommendation system

## Paper References (Bibliography)

### Surveys
- Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey. ACM Computing Surveys, https://arxiv.org/abs/1212.2129

### Foundational Papers
- Cover, T.M., 1991. Universal Portfolios. Mathematical Finance, 1(1), pp.1-29. http://www-isl.stanford.edu/~cover/papers/portfolios_side_info.pdf
- Helmbold, D.P., et al., 1998. On-line portfolio selection using multiplicative updates. Mathematical Finance, 8(4), pp.325-347.

### Mean Reversion
- Li, B., Hoi, S., 2012. On-Line Portfolio Selection with Moving Average Reversion. ICML 2012. https://arxiv.org/pdf/1206.4626.pdf
- Li, B., Zhao, P., Hoi, S.C., Gopalkrishnan, V., 2012. PAMR: Passive aggressive mean reversion strategy for portfolio selection. Machine Learning, 87, 221-258. https://link.springer.com/content/pdf/10.1007%2Fs10994-012-5281-z.pdf
- Li, B., et al., 2013. Confidence Weighted Mean Reversion Strategy for Online Portfolio Selection. https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3292&context=sis_research
- Huang, D., et al., 2013. Robust Median Reversion Strategy for Online Portfolio Selection. https://www.ijcai.org/Proceedings/13/Papers/296.pdf

### Correlation-Driven
- Li, B., Hoi, S.C., Sahoo, D., Liu, Z.Y., 2011. Correlation-Driven Nonparametric Learning for Portfolio Selection. https://dl.acm.org/doi/abs/10.1145/1961189.1961193
- Zhao, P., Hoi, S.C., 2019. Functional Correlation Driven Portfolio Selection. https://jfds.pm-research.com/content/1/2/78

## Notes and Observations

### Performance Considerations
- Price relatives calculation can be vectorized for speed
- Weight matrix storage (T x N) can be memory-intensive for large universes
- Consider sparse storage for strategies with many zero weights

### Hyperparameter Sensitivity
- EG: Very sensitive to `eta` - orders of magnitude changes in performance
- OLMAR: `window` and `alpha` highly dataset-dependent
- PAMR: `epsilon` acts as active/passive threshold, 0 or 1 often best
- UP: Number of experts affects both performance and computation time

### Common Pitfalls
1. **Simplex projection**: Critical for ensuring valid weights, must be numerically stable
2. **Division by zero**: Check for zero denominators in loss functions
3. **Initialization**: First few periods often need special handling (not enough data)
4. **Normalization**: Always normalize weights after updates to ensure sum = 1

### Extension Points
1. **Short-selling**: Current impl is long-only, could extend to allow shorts
2. **Transaction costs**: Could integrate cost model directly into weight updates
3. **Multi-period optimization**: Some strategies could look ahead k periods
4. **Ensemble methods**: Combine strategies using meta-learning

## Contact for Questions
- See `.github/copilot-instructions.md` for project overview
- See `work-documentation/2025-11-16_quick-start-guide.md` for setup
- All strategies must pass through registry validation before use in dashboard
