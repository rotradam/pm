"""
Correlation-Driven OLPS Strategies.

This module implements the CORN (Correlation-driven Nonparametric Learning) family of strategies.
All strategies use rolling correlation coefficients to identify similar market conditions from
the past and optimize weights to maximize returns in those similar periods.

Paper Reference:
    Li, B., Hoi, S.C., & Gopalkrishnan, V. (2011).
    CORN: Correlation-driven nonparametric learning approach for portfolio selection.
    ACM TIST, 2, 21:1-21:29.
    https://dl.acm.org/doi/abs/10.1145/1961189.1961193
"""

from typing import Any, Dict, List
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


class CORN(OlpsStrategy):
    """
    Correlation Driven Nonparametric Learning (CORN).
    
    Finds similar market windows from the past using correlation and optimizes
    weights to maximize returns in those similar periods.
    
    **Classification**: CAUSAL_LAGGING
    **Implementability**: Yes - Requires window of historical data
    **Complexity**: HIGH
    
    Algorithm:
    1. Calculate rolling correlation coefficient between current and past windows
    2. Identify similar periods where correlation > rho threshold
    3. Optimize weights to maximize log returns in similar periods
    4. Use SLSQP optimization with simplex constraints
    
    Paper Reference:
        Li, B., Hoi, S.C., & Gopalkrishnan, V. (2011).
        CORN: Correlation-driven nonparametric learning approach for portfolio selection.
        ACM TIST, 2, 21:1-21:29.
    """
    
    def __init__(self):
        super().__init__(
            id="CORN",
            name="Correlation Driven Nonparametric Learning",
            paper_ref="Li et al. 2011 - CORN",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL_LAGGING,
            complexity=StrategyComplexity.HIGH,
            description="Uses correlation to find similar market periods and optimizes for those conditions. "
                        "Requires historical window. Works well with window=[1,7] and rho=[0,0.2].",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute CORN strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - window: Lookback window [1, inf), typically [1, 7]
                - rho: Correlation threshold [-1, 1], typically [0, 0.2]
        
        Returns:
            StrategyResult with correlation-driven weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        window = config.get('window', 5)
        rho = config.get('rho', 0.1)
        
        # Validate parameters
        if not isinstance(window, int) or window < 1:
            raise ValueError("window must be integer >= 1")
        if not -1 <= rho <= 1:
            raise ValueError("rho must be in [-1, 1]")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        prices_array = prices_df.values
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Calculate rolling correlation coefficients
        corr_coef = self._calc_rolling_corr_coef(price_relatives, window, n_assets)
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Initialize with uniform weights
        current_weights = uniform_weights(n_assets)
        weights_matrix.iloc[0] = current_weights
        
        # Iterate through time
        for t in range(1, n_periods):
            # Default to uniform if not enough history
            if t < window:
                weights_matrix.iloc[t] = current_weights
                continue
            
            # Correlation matrix index (offset by window)
            corr_idx = t - window
            
            # Find similar periods
            similar_set = []
            for past_idx in range(corr_idx):
                if corr_coef[corr_idx, past_idx] > rho:
                    # Map back to original time index
                    similar_set.append(past_idx + window)
            
            # Optimize if we have similar periods
            if similar_set:
                optimize_array = price_relatives[similar_set]
                new_weights = self._optimize_weights(optimize_array, n_assets)
            else:
                new_weights = current_weights.copy()
            
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
            'strategy_type': 'correlation_driven',
            'n_assets': n_assets,
            'window': window,
            'rho': rho,
            'description': f'CORN with window={window}, rho={rho}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    @staticmethod
    def _calc_rolling_corr_coef(price_relatives, window, n_assets):
        """
        Calculate rolling correlation coefficient matrix.
        
        Args:
            price_relatives: Array of price relatives (n_periods x n_assets)
            window: Window size
            n_assets: Number of assets
        
        Returns:
            Correlation coefficient matrix
        """
        n_periods = len(price_relatives)
        
        # Flatten the array
        flattened = price_relatives.flatten()
        
        # Create rolling window indices
        idx = np.arange(n_assets * window)[None, :] + n_assets * \
              np.arange(n_periods - window + 1)[:, None]
        
        # Get rolled windows
        rolled_returns = flattened[idx]
        
        # Calculate correlation coefficient
        with np.errstate(divide='ignore', invalid='ignore'):
            rolling_corr_coef = np.nan_to_num(np.corrcoef(rolled_returns), nan=0)
        
        return rolling_corr_coef
    
    @staticmethod
    def _optimize_weights(optimize_array, n_assets):
        """
        Optimize weights to maximize log returns.
        
        Args:
            optimize_array: Array of price relatives for similar periods
            n_assets: Number of assets
        
        Returns:
            Optimized weights
        """
        # Initial guess
        x0 = uniform_weights(n_assets)
        
        # Objective: minimize negative log returns (= maximize log returns)
        def objective(w):
            portfolio_returns = np.dot(optimize_array, w)
            # Avoid log(0)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            return -np.sum(np.log(portfolio_returns))
        
        # Jacobian (gradient)
        def jacobian(w):
            portfolio_returns = np.dot(optimize_array, w)
            portfolio_returns = np.maximum(portfolio_returns, 1e-10)
            return -np.dot(1.0 / portfolio_returns, optimize_array)
        
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
            # Fallback to uniform if optimization fails
            return x0


class CORNK(OlpsStrategy):
    """
    Correlation Driven Nonparametric Learning - K (CORN-K).
    
    Ensemble approach that creates multiple CORN experts with different parameters
    and selects the top-K performing experts at each time step.
    
    **Classification**: CAUSAL_LAGGING
    **Implementability**: Yes - But computationally expensive
    **Complexity**: VERY_HIGH
    
    Algorithm:
    1. Generate window × rho experts with different (window, rho) parameters
    2. Track each expert's cumulative performance
    3. Select top-K experts based on historical performance
    4. Aggregate weights uniformly across top-K experts
    
    Paper Reference:
        Li, B., Hoi, S.C., & Gopalkrishnan, V. (2011).
        CORN: Correlation-driven nonparametric learning approach for portfolio selection.
        ACM TIST, 2, 21:1-21:29.
    """
    
    def __init__(self):
        super().__init__(
            id="CORNK",
            name="CORN with Top-K Experts",
            paper_ref="Li et al. 2011 - CORN-K",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL_LAGGING,
            complexity=StrategyComplexity.VERY_HIGH,
            description="Ensemble of CORN experts. Tracks top-K performing parameter combinations. "
                        "Very computationally expensive. Best with k=1 or k=2.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute CORN-K strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - window: Max window size [1, inf), typically [1, 7]
                - rho: Number of rho levels [1, inf), typically [2, 7]
                - k: Number of top experts [1, window*rho], typically 1 or 2
        
        Returns:
            StrategyResult with ensemble weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        max_window = config.get('window', 5)
        n_rho = config.get('rho', 3)
        k = config.get('k', 2)
        
        # Validate parameters
        if not isinstance(max_window, int) or max_window < 1:
            raise ValueError("window must be integer >= 1")
        if not isinstance(n_rho, int) or n_rho < 1:
            raise ValueError("rho must be integer >= 1")
        if not isinstance(k, int) or k < 1:
            raise ValueError("k must be integer >= 1")
        
        n_experts = max_window * n_rho
        if k > n_experts:
            raise ValueError(f"k must be <= window * rho = {n_experts}")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        
        # Generate expert parameters: (window, rho) pairs
        expert_params = []
        for w in range(1, max_window + 1):
            for r in range(n_rho):
                rho_value = r / n_rho  # [0, (n_rho-1)/n_rho]
                expert_params.append((w, rho_value))
        
        # Initialize expert performance tracking
        expert_wealth = np.ones(n_experts)
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Initialize with uniform weights
        current_weights = uniform_weights(n_assets)
        weights_matrix.iloc[0] = current_weights
        
        # Calculate correlation coefficients for each expert
        expert_corr_coefs = []
        for w, _ in expert_params:
            corr_coef = CORN._calc_rolling_corr_coef(price_relatives, w, n_assets)
            expert_corr_coefs.append(corr_coef)
        
        # Iterate through time
        for t in range(1, n_periods):
            # Get expert weights
            expert_weights_list = []
            
            for expert_idx, (w, rho_value) in enumerate(expert_params):
                # Default to uniform if not enough history
                if t < w:
                    expert_weights_list.append(uniform_weights(n_assets))
                    continue
                
                # Correlation matrix index (offset by window)
                corr_idx = t - w
                
                # Find similar periods for this expert
                similar_set = []
                corr_coef = expert_corr_coefs[expert_idx]
                for past_idx in range(corr_idx):
                    if corr_coef[corr_idx, past_idx] > rho_value:
                        similar_set.append(past_idx + w)
                
                # Optimize if we have similar periods
                if similar_set:
                    optimize_array = price_relatives[similar_set]
                    weights = CORN._optimize_weights(optimize_array, n_assets)
                else:
                    weights = uniform_weights(n_assets)
                
                expert_weights_list.append(weights)
            
            # Select top-K experts by wealth
            top_k_indices = np.argsort(expert_wealth)[-k:]
            
            # Aggregate weights uniformly across top-K
            new_weights = np.zeros(n_assets)
            for idx in top_k_indices:
                new_weights += expert_weights_list[idx]
            new_weights /= k
            
            # Ensure valid weights
            new_weights = simplex_projection(new_weights)
            
            # Update expert wealth
            for expert_idx in range(n_experts):
                expert_return = np.dot(price_relatives[t-1], expert_weights_list[expert_idx])
                expert_wealth[expert_idx] *= expert_return
            
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
            'strategy_type': 'correlation_driven',
            'n_assets': n_assets,
            'window': max_window,
            'rho': n_rho,
            'k': k,
            'n_experts': n_experts,
            'description': f'CORN-K with window={max_window}, rho_levels={n_rho}, k={k}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class CORNU(OlpsStrategy):
    """
    Correlation Driven Nonparametric Learning - Uniform (CORN-U).
    
    Creates W experts (one for each window size) with the same rho value and
    aggregates uniformly across all experts.
    
    **Classification**: CAUSAL_LAGGING
    **Implementability**: Yes - Simpler than CORN-K
    **Complexity**: HIGH
    
    Algorithm:
    1. Generate W experts with windows [1, 2, ..., W] and same rho
    2. Each expert follows CORN strategy
    3. Aggregate weights uniformly across all experts
    
    Paper Reference:
        Li, B., Hoi, S.C., & Gopalkrishnan, V. (2011).
        CORN: Correlation-driven nonparametric learning approach for portfolio selection.
        ACM TIST, 2, 21:1-21:29.
    """
    
    def __init__(self):
        super().__init__(
            id="CORNU",
            name="CORN with Uniform Experts",
            paper_ref="Li et al. 2011 - CORN-U",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL_LAGGING,
            complexity=StrategyComplexity.HIGH,
            description="Uniform aggregation of CORN experts with different window sizes. "
                        "Less complex than CORN-K. Works well with window=[1,7] and rho=[0,0.2].",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute CORN-U strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - window: Max window size [1, inf), typically [1, 7]
                - rho: Correlation threshold [-1, 1], typically [0, 0.2]
        
        Returns:
            StrategyResult with uniformly aggregated weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        max_window = config.get('window', 5)
        rho = config.get('rho', 0.1)
        
        # Validate parameters
        if not isinstance(max_window, int) or max_window < 1:
            raise ValueError("window must be integer >= 1")
        if not -1 <= rho <= 1:
            raise ValueError("rho must be in [-1, 1]")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        price_relatives = calculate_relative_returns(prices_df)
        
        # Generate experts with windows [1, 2, ..., max_window]
        n_experts = max_window
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Initialize with uniform weights
        current_weights = uniform_weights(n_assets)
        weights_matrix.iloc[0] = current_weights
        
        # Calculate correlation coefficients for each expert
        expert_corr_coefs = []
        for w in range(1, max_window + 1):
            corr_coef = CORN._calc_rolling_corr_coef(price_relatives, w, n_assets)
            expert_corr_coefs.append(corr_coef)
        
        # Iterate through time
        for t in range(1, n_periods):
            # Aggregate expert weights
            new_weights = np.zeros(n_assets)
            
            for expert_idx, w in enumerate(range(1, max_window + 1)):
                # Default to uniform if not enough history
                if t < w:
                    expert_weights = uniform_weights(n_assets)
                else:
                    # Correlation matrix index (offset by window)
                    corr_idx = t - w
                    
                    # Find similar periods
                    similar_set = []
                    corr_coef = expert_corr_coefs[expert_idx]
                    for past_idx in range(corr_idx):
                        if corr_coef[corr_idx, past_idx] > rho:
                            similar_set.append(past_idx + w)
                    
                    # Optimize if we have similar periods
                    if similar_set:
                        optimize_array = price_relatives[similar_set]
                        expert_weights = CORN._optimize_weights(optimize_array, n_assets)
                    else:
                        expert_weights = uniform_weights(n_assets)
                
                new_weights += expert_weights
            
            # Uniform aggregation
            new_weights /= n_experts
            
            # Ensure valid weights
            new_weights = simplex_projection(new_weights)
            
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
            'strategy_type': 'correlation_driven',
            'n_assets': n_assets,
            'window': max_window,
            'rho': rho,
            'n_experts': n_experts,
            'description': f'CORN-U with window={max_window}, rho={rho}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )



# TODO: SCORN, SCORNK, FCORN, FCORNK to be implemented
# These strategies are complex variations requiring significant testing
# Current priority: Get CORN, CORNK, CORNU + follow-the-leader strategies working first
