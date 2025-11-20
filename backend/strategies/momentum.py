"""
Momentum and Trend-Following OLPS Strategies.

Implements strategies that follow winning assets:
- Exponential Gradient (EG): Exponentially weights assets based on recent performance
- Universal Portfolio (UP): Fund of funds approach with multiple CRP experts
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from .utils import (
    calculate_relative_returns,
    normalize_weights,
    uniform_weights,
    calculate_turnover,
    calculate_cumulative_returns,
    simplex_projection,
)


class ExponentialGradient(OlpsStrategy):
    """
    Exponential Gradient (EG) Strategy.
    
    Tracks the best performing assets using exponential weighting based on returns.
    The strategy adjusts weights multiplicatively based on asset performance.
    
    Three update rules are available:
    - MU (Multiplicative Update): exp(eta * returns)
    - EM (Expectation Maximization): 1 + eta * (returns - 1)
    - GP (Gradient Projection): gradient-based projection onto simplex
    
    Paper Reference:
        Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey.
        ACM Computing Surveys, V, N, Article A (December 2012), 33 pages.
        https://arxiv.org/abs/1212.2129
        
        Original: Helmbold, D.P., et al., 1998. On-line portfolio selection using
        multiplicative updates. Mathematical Finance, 8(4), pp.325-347.
    """
    
    def __init__(self):
        super().__init__(
            id="EG",
            name="Exponential Gradient",
            paper_ref="Li & Hoi 2012; Helmbold et al. 1998",
            library_ref="portfoliolab.eg (migrated)"
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute Exponential Gradient strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, must include:
                - eta: Learning rate [0, inf). Typical values: 0.05 (conservative) or 20 (aggressive)
                - update_rule: 'MU', 'EM', or 'GP'
                Optional:
                - initial_capital: Starting capital (default: 1.0)
                - initial_weights: Starting weights (default: uniform)
        
        Returns:
            StrategyResult with EG weights
        """
        # Extract configuration
        eta = config.get('eta')
        if eta is None:
            raise ValueError("EG strategy requires 'eta' parameter")
        
        update_rule = config.get('update_rule', 'MU')
        if update_rule not in ['MU', 'EM', 'GP']:
            raise ValueError(f"Unknown update_rule: {update_rule}. Use 'MU', 'EM', or 'GP'")
        
        initial_capital = config.get('initial_capital', 1.0)
        initial_weights = config.get('initial_weights', None)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Initialize weights
        if initial_weights is None:
            current_weights = uniform_weights(n_assets)
        else:
            current_weights = np.array(initial_weights)
            current_weights = normalize_weights(current_weights)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Track weights over time
        weights_over_time = np.zeros((n_periods, n_assets))
        weights_over_time[0] = current_weights
        turnover_values = np.zeros(n_periods)
        
        # Run EG update for each period
        for t in range(1, n_periods):
            # Get previous period's price relatives
            x_t = price_relatives[t-1]
            
            # Portfolio return for previous period
            portfolio_return = np.dot(current_weights, x_t)
            
            # Update weights based on selected rule
            if update_rule == 'MU':
                # Multiplicative Update: w_i^{t+1} = w_i^t * exp(eta * x_i^t / b^t)
                new_weights = current_weights * np.exp(eta * x_t / portfolio_return)
            
            elif update_rule == 'EM':
                # Expectation Maximization: w_i^{t+1} = w_i^t * (1 + eta * (x_i^t / b^t - 1))
                new_weights = current_weights * (1 + eta * (x_t / portfolio_return - 1))
            
            elif update_rule == 'GP':
                # Gradient Projection: w^{t+1} = w^t + eta * (x^t - mean(x^t) * 1) / b^t
                gradient = (x_t - np.mean(x_t) * np.ones(n_assets)) / portfolio_return
                new_weights = current_weights + eta * gradient
                # Project onto probability simplex
                new_weights = simplex_projection(new_weights)
            
            # Normalize to ensure sum = 1 and non-negative
            new_weights = normalize_weights(new_weights)
            
            # Calculate turnover
            turnover_values[t] = calculate_turnover(current_weights, new_weights, x_t)
            
            # Update
            current_weights = new_weights
            weights_over_time[t] = current_weights
        
        # Build weights DataFrame
        weights_matrix = pd.DataFrame(
            weights_over_time,
            index=prices_df.index,
            columns=prices_df.columns
        )
        
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
            'strategy_type': 'momentum',
            'n_assets': n_assets,
            'eta': eta,
            'update_rule': update_rule,
            'initial_weights': weights_over_time[0].tolist(),
            'final_weights': weights_over_time[-1].tolist(),
            'description': f'Exponential Gradient with {update_rule} update rule and eta={eta}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class UniversalPortfolio(OlpsStrategy):
    """
    Universal Portfolio (UP) Strategy.
    
    Fund-of-funds approach that combines multiple CRP (Constant Rebalanced Portfolio) experts
    with different fixed weights. The strategy aggregates expert returns using various methods.
    
    Three aggregation methods:
    - hist_performance: Weight experts by historical performance
    - uniform: Equal weight to all experts
    - top-k: Only allocate to top-k performing experts
    
    Paper Reference:
        Cover, T.M., 1991. Universal Portfolios. Mathematical Finance, 1(1), pp.1-29.
        http://www-isl.stanford.edu/~cover/papers/portfolios_side_info.pdf
        
        Also: Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey.
        https://arxiv.org/abs/1212.2129
    """
    
    def __init__(self):
        super().__init__(
            id="UP",
            name="Universal Portfolio",
            paper_ref="Cover 1991; Li & Hoi 2012",
            library_ref="portfoliolab.up (migrated)"
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute Universal Portfolio strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, must include:
                - n_experts: Number of CRP experts to generate
                - aggregation: 'hist_performance', 'uniform', or 'top-k'
                - k: Number of top experts (required if aggregation='top-k')
                Optional:
                - initial_capital: Starting capital (default: 1.0)
                - expert_weights: List of weight vectors for experts (default: random simplex)
        
        Returns:
            StrategyResult with aggregated expert weights
        """
        # Extract configuration
        n_experts = config.get('n_experts')
        if n_experts is None:
            raise ValueError("UP strategy requires 'n_experts' parameter")
        
        aggregation = config.get('aggregation', 'hist_performance')
        if aggregation not in ['hist_performance', 'uniform', 'top-k']:
            raise ValueError(
                f"Unknown aggregation: {aggregation}. "
                f"Use 'hist_performance', 'uniform', or 'top-k'"
            )
        
        k = config.get('k', 1)
        if aggregation == 'top-k' and k > n_experts:
            raise ValueError(f"k ({k}) cannot exceed n_experts ({n_experts})")
        
        initial_capital = config.get('initial_capital', 1.0)
        expert_weights_config = config.get('expert_weights', None)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Generate expert weight vectors (each expert is a CRP with fixed weights)
        if expert_weights_config is not None:
            expert_weights_list = expert_weights_config
        else:
            # Generate random weights on the simplex
            expert_weights_list = self._generate_random_simplex_points(n_experts, n_assets)
        
        # Run each expert (CRP)
        expert_returns = np.zeros((n_periods, n_experts))
        expert_weights_matrix = np.zeros((n_experts, n_periods, n_assets))
        
        for i, expert_weights in enumerate(expert_weights_list):
            # Each expert maintains constant weights (CRP)
            for t in range(n_periods):
                expert_weights_matrix[i, t] = expert_weights
                
                if t > 0:
                    # Expert return is weighted return
                    expert_returns[t, i] = np.dot(expert_weights, price_relatives[t-1])
        
        # Calculate cumulative returns for each expert
        expert_cumulative = np.cumprod(1 + expert_returns, axis=0)
        
        # Calculate weights on experts based on aggregation method
        weights_on_experts = self._calculate_expert_allocation(
            expert_cumulative,
            aggregation,
            k,
            n_experts,
            n_periods
        )
        
        # Aggregate expert weights
        final_weights_over_time = np.zeros((n_periods, n_assets))
        for t in range(n_periods):
            # Weighted average of all expert weights
            for i in range(n_experts):
                final_weights_over_time[t] += (
                    weights_on_experts[t, i] * expert_weights_matrix[i, t]
                )
            # Normalize
            final_weights_over_time[t] = normalize_weights(final_weights_over_time[t])
        
        # Build weights DataFrame
        weights_matrix = pd.DataFrame(
            final_weights_over_time,
            index=prices_df.index,
            columns=prices_df.columns
        )
        
        # Calculate portfolio values
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Calculate turnover
        turnover_values = np.zeros(n_periods)
        for t in range(1, n_periods):
            turnover_values[t] = calculate_turnover(
                final_weights_over_time[t-1],
                final_weights_over_time[t],
                price_relatives[t-1]
            )
        turnover_series = pd.Series(turnover_values, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'momentum',
            'n_assets': n_assets,
            'n_experts': n_experts,
            'aggregation': aggregation,
            'k': k if aggregation == 'top-k' else None,
            'description': f'Universal Portfolio with {n_experts} CRP experts, {aggregation} aggregation'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    def _generate_random_simplex_points(
        self,
        n_points: int,
        n_dim: int,
        seed: int = 42
    ) -> List[np.ndarray]:
        """
        Generate random points on the probability simplex.
        
        Uses Dirichlet distribution for uniform sampling on simplex.
        """
        np.random.seed(seed)
        # Dirichlet with uniform alpha generates uniform simplex samples
        alpha = np.ones(n_dim)
        points = np.random.dirichlet(alpha, size=n_points)
        return [points[i] for i in range(n_points)]
    
    def _calculate_expert_allocation(
        self,
        expert_cumulative: np.ndarray,
        aggregation: str,
        k: int,
        n_experts: int,
        n_periods: int
    ) -> np.ndarray:
        """
        Calculate allocation weights to experts based on aggregation method.
        
        Returns array of shape (n_periods, n_experts) with weights summing to 1 per period.
        """
        weights_on_experts = np.zeros((n_periods, n_experts))
        
        if aggregation == 'hist_performance':
            # Weight experts proportionally to their cumulative returns
            for t in range(n_periods):
                if t == 0:
                    # Equal weights initially
                    weights_on_experts[t] = np.ones(n_experts) / n_experts
                else:
                    # Normalize cumulative returns to get weights
                    total = np.sum(expert_cumulative[t])
                    if total > 0:
                        weights_on_experts[t] = expert_cumulative[t] / total
                    else:
                        weights_on_experts[t] = np.ones(n_experts) / n_experts
        
        elif aggregation == 'uniform':
            # Equal weight to all experts
            weights_on_experts[:] = 1.0 / n_experts
        
        elif aggregation == 'top-k':
            # Only allocate to top-k performing experts
            for t in range(n_periods):
                if t == 0:
                    # Equal weights initially
                    weights_on_experts[t] = np.ones(n_experts) / n_experts
                else:
                    # Find top-k experts by cumulative return
                    top_k_indices = np.argpartition(expert_cumulative[t], -k)[-k:]
                    weights_on_experts[t, top_k_indices] = 1.0 / k
        
        return weights_on_experts
