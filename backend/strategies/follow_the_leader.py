"""
Follow-The-Leader OLPS Strategies.

This module implements follow-the-leader strategies and look-ahead benchmarks.

References:
    - Cover, T. M. (1991). Universal Portfolios. Mathematical Finance, 1(1), 1-29.
    - Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey. ACM Comput. Surv.
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from backend.strategies.base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from backend.strategies.utils import (
    calculate_relative_returns,
    calculate_cumulative_returns,
    calculate_turnover,
    uniform_weights,
    simplex_projection
)


class BCRP(OlpsStrategy):
    """
    Best Constant Rebalanced Portfolio (BCRP).
    
    **NOT IMPLEMENTABLE** - Uses future information!
    
    Finds the single constant portfolio that would have performed best over the entire period.
    This is a benchmark strategy that requires knowing all future returns.
    
    **Classification**: BENCHMARK_LOOKAHEAD
    **Implementability**: No - Uses complete future information
    **Complexity**: LOW
    
    Algorithm:
    1. Use ALL price data (past and future)
    2. Find constant weights that maximize cumulative log return
    3. Apply those weights for entire period
    
    This is the theoretical best performance for any constant-rebalanced strategy.
    """
    
    def __init__(self):
        super().__init__(
            id="BCRP",
            name="Best Constant Rebalanced Portfolio",
            paper_ref="Cover 1991 - Universal Portfolios",
            library_ref=None,
            strategy_type=StrategyType.BENCHMARK_LOOKAHEAD,
            complexity=StrategyComplexity.LOW,
            description="Theoretical best constant portfolio using hindsight. NOT implementable in practice. "
                        "Useful as performance upper bound for CRP strategies.",
            implementable=False
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute BCRP (using hindsight).
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
        
        Returns:
            StrategyResult with hindsight-optimal constant weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        
        # Optimize using ALL data (hindsight)
        best_weights = self._optimize_bcrp(price_relatives, n_assets)
        
        # Apply constant weights for entire period
        weights_matrix = pd.DataFrame(
            np.tile(best_weights, (n_periods, 1)),
            index=prices_df.index,
            columns=prices_df.columns
        )
        
        # Calculate turnover (only on first rebalance)
        turnover_values = np.zeros(n_periods)
        turnover_values[0] = np.sum(np.abs(best_weights - uniform_weights(n_assets)))
        
        # Calculate portfolio values
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Turnover series
        turnover_series = pd.Series(turnover_values, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'benchmark_lookahead',
            'n_assets': n_assets,
            'description': 'BCRP (hindsight optimal)'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    @staticmethod
    def _optimize_bcrp(price_relatives, n_assets):
        """
        Find constant weights that maximize cumulative log return.
        
        Args:
            price_relatives: Array of all price relatives
            n_assets: Number of assets
        
        Returns:
            Optimal constant weights
        """
        # Initial guess
        x0 = uniform_weights(n_assets)
        
        # Objective: maximize log returns
        def objective(w):
            portfolio_returns = np.dot(price_relatives, w)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            return -np.sum(np.log(portfolio_returns))
        
        # Jacobian
        def jacobian(w):
            portfolio_returns = np.dot(price_relatives, w)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            return -np.dot(1.0 / portfolio_returns, price_relatives)
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Bounds: each weight in [0, 1]
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            jac=jacobian,
            options={'ftol': 1e-9, 'maxiter': 1000}
        )
        
        if result.success:
            return result.x
        else:
            return x0


class BestStock(OlpsStrategy):
    """
    Best Single Stock (BestStock).
    
    **NOT IMPLEMENTABLE** - Uses future information!
    
    Invests 100% in the single asset that performed best over the entire period.
    This is a benchmark showing the theoretical best single-asset performance.
    
    **Classification**: BENCHMARK_LOOKAHEAD
    **Implementability**: No - Uses complete future information
    **Complexity**: LOW
    
    Algorithm:
    1. Calculate each asset's total return over entire period
    2. Select the best-performing asset
    3. Invest 100% in that asset for entire period
    """
    
    def __init__(self):
        super().__init__(
            id="BestStock",
            name="Best Single Stock",
            paper_ref="Cover 1991 - Universal Portfolios",
            library_ref=None,
            strategy_type=StrategyType.BENCHMARK_LOOKAHEAD,
            complexity=StrategyComplexity.LOW,
            description="100% investment in the best-performing asset (hindsight). NOT implementable. "
                        "Useful as performance upper bound.",
            implementable=False
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute BestStock (using hindsight).
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
        
        Returns:
            StrategyResult with 100% weight on best asset
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        
        # Find best asset (maximum cumulative return)
        cumulative_returns = np.prod(price_relatives, axis=0)
        best_asset_idx = np.argmax(cumulative_returns)
        
        # Create weights: 100% in best asset
        best_weights = np.zeros(n_assets)
        best_weights[best_asset_idx] = 1.0
        
        # Apply constant weights for entire period
        weights_matrix = pd.DataFrame(
            np.tile(best_weights, (n_periods, 1)),
            index=prices_df.index,
            columns=prices_df.columns
        )
        
        # Calculate turnover (only on first rebalance)
        turnover_values = np.zeros(n_periods)
        turnover_values[0] = np.sum(np.abs(best_weights - uniform_weights(n_assets)))
        
        # Calculate portfolio values
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Turnover series
        turnover_series = pd.Series(turnover_values, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'benchmark_lookahead',
            'n_assets': n_assets,
            'best_asset': prices_df.columns[best_asset_idx],
            'best_asset_return': cumulative_returns[best_asset_idx],
            'description': f'Best Stock: {prices_df.columns[best_asset_idx]} (hindsight)'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class FTL(OlpsStrategy):
    """
    Follow The Leader (FTL).
    
    At each time step, invests in the portfolio that would have been best
    from the beginning up to the current time.
    
    **Classification**: CAUSAL
    **Implementability**: Yes
    **Complexity**: MEDIUM
    
    Algorithm:
    1. At time t, use returns from [0, t-1]
    2. Find constant portfolio that maximizes returns over that history
    3. Use those weights for time t
    4. Repeat for each time step
    
    This is the causal (no future information) version of BCRP.
    """
    
    def __init__(self):
        super().__init__(
            id="FTL",
            name="Follow The Leader",
            paper_ref="Li & Hoi 2012 - OLPS Survey",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.MEDIUM,
            description="Follows best constant portfolio from history. Causal strategy. "
                        "Requires optimization at each step.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute FTL strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
        
        Returns:
            StrategyResult with follow-the-leader weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Initialize with uniform weights
        current_weights = uniform_weights(n_assets)
        weights_matrix.iloc[0] = current_weights
        
        # Iterate through time
        for t in range(1, n_periods):
            # Use all history up to t-1
            if t == 1:
                # Not enough history, use uniform
                new_weights = current_weights.copy()
            else:
                # Optimize on history [0, t-1]
                historical_returns = price_relatives[:t]
                new_weights = BCRP._optimize_bcrp(historical_returns, n_assets)
            
            # Store
            weights_matrix.iloc[t] = new_weights
            turnover_values[t] = calculate_turnover(current_weights, new_weights)
            current_weights = new_weights.copy()
        
        # Calculate portfolio values
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Turnover series
        turnover_series = pd.Series(turnover_values, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'follow_the_leader',
            'n_assets': n_assets,
            'description': 'FTL - Follow The Leader'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class FTRL(OlpsStrategy):
    """
    Follow The Regularized Leader (FTRL).
    
    Extension of FTL with L2 regularization to prevent overfitting and reduce turnover.
    
    **Classification**: CAUSAL
    **Implementability**: Yes
    **Complexity**: MEDIUM
    
    Algorithm:
    1. At time t, use returns from [0, t-1]
    2. Find portfolio that maximizes returns MINUS regularization penalty
    3. Regularization term: lambda * ||w - w_uniform||^2
    4. Use those weights for time t
    
    The regularization pulls weights toward uniform, reducing extreme positions.
    """
    
    def __init__(self):
        super().__init__(
            id="FTRL",
            name="Follow The Regularized Leader",
            paper_ref="Li & Hoi 2012 - OLPS Survey",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.MEDIUM,
            description="FTL with L2 regularization. Reduces overfitting and turnover. "
                        "Lambda controls regularization strength.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute FTRL strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - lam: Regularization parameter [0, inf), typically [0.01, 1.0]
        
        Returns:
            StrategyResult with regularized weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        lam = config.get('lam', 0.1)
        
        # Validate parameters
        if lam < 0:
            raise ValueError("lam must be >= 0")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        uniform_w = uniform_weights(n_assets)
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Initialize with uniform weights
        current_weights = uniform_w.copy()
        weights_matrix.iloc[0] = current_weights
        
        # Iterate through time
        for t in range(1, n_periods):
            # Use all history up to t-1
            if t == 1:
                # Not enough history, use uniform
                new_weights = current_weights.copy()
            else:
                # Optimize with regularization
                historical_returns = price_relatives[:t]
                new_weights = self._optimize_ftrl(historical_returns, n_assets, lam, uniform_w)
            
            # Store
            weights_matrix.iloc[t] = new_weights
            turnover_values[t] = calculate_turnover(current_weights, new_weights)
            current_weights = new_weights.copy()
        
        # Calculate portfolio values
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Turnover series
        turnover_series = pd.Series(turnover_values, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'follow_the_leader',
            'n_assets': n_assets,
            'lam': lam,
            'description': f'FTRL with lambda={lam}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    @staticmethod
    def _optimize_ftrl(price_relatives, n_assets, lam, uniform_w):
        """
        Optimize with L2 regularization.
        
        Args:
            price_relatives: Historical price relatives
            n_assets: Number of assets
            lam: Regularization parameter
            uniform_w: Uniform weights vector
        
        Returns:
            Regularized optimal weights
        """
        # Initial guess
        x0 = uniform_w.copy()
        
        # Objective: maximize log returns - lambda * L2 penalty
        def objective(w):
            # Log returns term
            portfolio_returns = np.dot(price_relatives, w)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            log_returns = -np.sum(np.log(portfolio_returns))
            
            # L2 regularization term
            diff = w - uniform_w
            regularization = lam * np.dot(diff, diff)
            
            return log_returns + regularization
        
        # Jacobian
        def jacobian(w):
            # Log returns gradient
            portfolio_returns = np.dot(price_relatives, w)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            log_grad = -np.dot(1.0 / portfolio_returns, price_relatives)
            
            # Regularization gradient
            reg_grad = 2 * lam * (w - uniform_w)
            
            return log_grad + reg_grad
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Bounds: each weight in [0, 1]
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            jac=jacobian,
            options={'ftol': 1e-9, 'maxiter': 1000}
        )
        
        if result.success:
            return result.x
        else:
            return x0
