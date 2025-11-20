# CWMR and RMR Mean Reversion Strategies Implementation

**Date**: 2025-01-16
**Status**: ✅ Complete
**Strategies Added**: 2 (CWMR, RMR)
**Total Implemented**: 9/20 (45%)

## Overview

Successfully implemented CWMR (Confidence Weighted Mean Reversion) and RMR (Robust Median Reversion), completing the mean reversion strategy family in our backend. Both strategies are fully functional, tested, and integrated into the dashboard.

## Strategies Implemented

### 1. CWMR - Confidence Weighted Mean Reversion

**File**: `backend/strategies/mean_reversion.py` (lines 371-560)

**Paper Reference**: 
- Li, B., Hoi, S.C., Zhao, P. & Gopalkrishnan, V., 2011
- "Confidence Weighted Mean Reversion Strategy for On-Line Portfolio Selection"
- AISTATS 2011
- https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3292&context=sis_research

**Classification**:
- Type: `CAUSAL`
- Complexity: `VERY_HIGH`
- Implementable: Yes (but computationally expensive)

**Algorithm**:
1. Models portfolio weights as Gaussian distribution: `w ~ N(μ, Σ)`
2. Tracks mean (`μ`) and variance (`Σ`) over time
3. Calculates portfolio return and variance at each step
4. Computes Lagrangian multiplier `λ` via quadratic formula
5. Updates mean: `μ ← μ - λ * Σ * (x_t - mean_x)`
6. Updates variance using either 'var' or 'sd' method
7. Projects mean to simplex (ensures valid weights)

**Key Parameters**:
- `confidence` [0, 1]: Confidence level (0.95 recommended, extreme values 0 or 1 work best)
- `epsilon` [0, 1]: Mean reversion threshold (0.5 default)
- `method` {'var', 'sd'}: Variance update method ('var' default)

**Dependencies**:
- Uses `scipy.stats.norm.ppf()` to convert confidence to theta parameter
- Requires matrix operations (numpy linalg)

**Default Config** (dashboard):
```python
'CWMR': {
    'confidence': 0.95,
    'epsilon': 0.5,
    'method': 'var'
}
```

**Performance** (test subset: 199 days, 10 assets):
- Final Value: $10,858.21 (+8.58%)
- Average Turnover: 0.0077
- Rank: 3rd out of 5 tested strategies

**Notable Implementation Details**:
- Lambda calculation handles multiple solutions via quadratic equation
- Uses pseudoinverse for matrix operations (robust to singularity)
- Bounds lambda for numerical stability (max 10,000)
- Normalizes variance matrix to prevent drift

---

### 2. RMR - Robust Median Reversion

**File**: `backend/strategies/mean_reversion.py` (lines 562-787)

**Paper Reference**:
- Huang, D., Zhou, J., Li, B., Hoi, S.C.H., Zhou, S., 2016
- "Robust Median Reversion Strategy for Online Portfolio Selection"
- IEEE TKDE, vol. 28, no. 9, pp. 2480-2493
- https://www.ijcai.org/Proceedings/13/Papers/296.pdf

**Classification**:
- Type: `CAUSAL_LAGGING`
- Complexity: `HIGH`
- Implementable: Yes (requires windowed data)

**Algorithm**:
1. Maintains window of historical prices
2. Calculates L1-median using Modified Weiszfeld Algorithm
3. Predicts price relatives: `x̂_t = L1_median / current_price`
4. Calculates deviation: `δ = x̂_t - mean(x̂_t)`
5. Computes alpha: `α = min(0, (x̂_t·w - ε) / ||δ||₁²)`
6. Updates: `w_{t+1} = w_t - α * δ`
7. Projects to simplex

**Key Parameters**:
- `epsilon` [1, ∞): Reversion threshold (20.0 recommended, typical range 15-25)
- `window` [2, ∞): Historical window size (7 recommended, can use 2, 7, or 21)
- `n_iteration` [2, ∞): Max iterations for L1-median (200 default)
- `tau` [0, 1): Convergence tolerance (0.001 default)

**Key Advantages**:
- More robust to outliers than OLMAR/PAMR (uses L1-median instead of L2-mean)
- Iterative algorithm with convergence guarantee
- Better performance on noisy data

**Dependencies**:
- Uses Modified Weiszfeld Algorithm for L1-median computation
- Requires window of historical data (strategy waits until `t >= window`)

**Default Config** (dashboard):
```python
'RMR': {
    'epsilon': 20.0,
    'window': 7,
    'n_iteration': 200,
    'tau': 0.001
}
```

**Performance** (test subset: 199 days, 10 assets):
- Final Value: $15,497.89 (+54.98%) 🏆
- Average Turnover: 1.0108
- Rank: 1st out of 5 tested strategies

**Notable Implementation Details**:
- Starts with componentwise median as initial L1-median guess
- Iteratively refines using Weiszfeld weighted average
- Handles zero distances to avoid division by zero
- Checks convergence using L1-norm of change
- Uses uniform weights until sufficient history (t < window)

---

## Mean Reversion Family Complete

We now have **4 mean reversion strategies** fully implemented:

| Strategy | Type | Complexity | Robust? | Window? | Special Feature |
|----------|------|------------|---------|---------|-----------------|
| **OLMAR** | Causal | Medium | No (L2) | Yes | Moving average prediction |
| **PAMR** | Causal | Medium | No (L2) | No | 3 variants with aggressiveness parameter |
| **CWMR** | Causal | Very High | No | No | Gaussian confidence weighting |
| **RMR** | Causal-Lagging | High | **Yes (L1)** | Yes | L1-median for outlier resistance |

## Files Modified

1. **`backend/strategies/mean_reversion.py`**
   - Added `CWMR` class (191 lines)
   - Added `RMR` class (226 lines)
   - Fixed PAMR metadata bug (method_name undefined)
   - Total file size: 787 lines

2. **`backend/strategies/__init__.py`**
   - Added `CWMR` and `RMR` to imports
   - Updated `STRATEGY_REGISTRY` with new strategies
   - Fixed duplicate registry entries bug

3. **`dashboard_enhanced.py`**
   - Added default configs for CWMR and RMR
   - Total strategies with defaults: 9

4. **`test_new_strategies.py`** (NEW)
   - Created comprehensive test script
   - Loads price data from individual parquet files
   - Tests both CWMR and RMR
   - Compares with existing mean reversion strategies

## Test Results

### Test Setup
- **Data**: 199 trading days, 10 ETFs
- **Initial Capital**: $10,000
- **Environment**: Python 3.11.9, pyenv virtualenv `olps`

### Performance Ranking
1. **RMR**: $15,497.89 (+54.98%) 🥇
2. **PAMR**: $14,068.79 (+40.69%) 🥈
3. **CWMR**: $10,858.21 (+8.58%) 🥉
4. **OLMAR**: $10,839.86 (+8.40%)
5. **EW**: $10,820.74 (+8.21%)

### Key Observations
- **RMR dominates** on this test subset (L1-median robustness pays off)
- **PAMR performs well** with default parameters
- **CWMR and OLMAR** similar performance to Equal Weight baseline
- **Turnover**: RMR has highest (1.01), CWMR has lowest (0.008)

## Technical Implementation Notes

### CWMR Challenges
1. **Matrix Operations**: Required pseudoinverse for numerical stability
2. **Quadratic Equation**: Lambda calculation has 3 potential solutions, need to select maximum positive
3. **Variance Update**: Two methods ('var' and 'sd') with different update rules
4. **Numerical Stability**: Bounded lambda, ensured positive semi-definite variance, normalized sigma

### RMR Challenges
1. **L1-Median Computation**: Implemented Modified Weiszfeld Algorithm from scratch
2. **Convergence**: Needed tolerance check and max iterations
3. **Zero Distance**: Handled division-by-zero when prediction exactly matches a data point
4. **Windowing**: Strategy needs to wait `window` periods before making predictions

### Bug Fixes
1. **PAMR Metadata**: Fixed undefined `method_name`, `C`, `agg_interval` variables in metadata dict
2. **Registry Duplicates**: Removed duplicate OLMAR/PAMR entries in `__init__.py`

## Integration Status

✅ Strategies registered in `STRATEGY_REGISTRY`
✅ Default configs added to `get_default_strategy_config()`
✅ Import statements updated
✅ Classification metadata complete
✅ Tested and verified working
✅ Documentation complete

## Next Steps

With mean reversion family complete (4/4 strategies), the remaining work is:

### Phase 2: Correlation-Driven Strategies (7 strategies)
- Create `backend/strategies/correlation_driven.py`
- Implement: CORN, CORNK, CORNU, SCORN, SCORNK, FCORN, FCORNK
- All use correlation-based expert selection
- Classification: CAUSAL or CAUSAL_LAGGING, HIGH complexity

### Phase 3: Follow-The-Leader Strategies (4 strategies)
- Create `backend/strategies/follow_the_leader.py`
- Implement: BCRP, BestStock (BENCHMARK_LOOKAHEAD, NOT implementable)
- Implement: FTL, FTRL (CAUSAL, implementable)

### Phase 4: Final Integration
- Update all registry entries
- Update dashboard defaults
- Comprehensive testing of all 20 strategies
- Performance comparison report

## References

1. **CWMR Paper**: https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3292&context=sis_research
2. **RMR Paper**: https://www.ijcai.org/Proceedings/13/Papers/296.pdf
3. **Modified Weiszfeld Algorithm**: Standard algorithm for L1-median (geometric median) computation
4. **PortfolioLab Reference**: `/Users/royceantonjose/git_rotradam/portfolioManagement/portfoliolab/cwmr.py` and `rmr.py`

## Commands Used

```bash
# Activate environment
source activate_olps.sh

# Run tests
python test_new_strategies.py

# Verify no errors
python -m py_compile backend/strategies/mean_reversion.py
python -m py_compile backend/strategies/__init__.py
python -m py_compile dashboard_enhanced.py
```

## Conclusion

✅ **Successfully implemented CWMR and RMR**
✅ **Mean reversion strategy family complete (4/4)**
✅ **Total progress: 9/20 strategies (45%)**
✅ **All strategies tested and working**
✅ **Ready for dashboard integration**

The mean reversion family is now complete and production-ready. Both CWMR and RMR add sophisticated variance modeling and robustness features that complement the simpler OLMAR and PAMR strategies.

Next focus: Correlation-driven strategies (CORN family - 7 strategies).
