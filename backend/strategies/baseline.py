"""
Baseline OLPS strategies.

Implements simple benchmark strategies:
- Equal Weight (EW): Uniform allocation rebalanced regularly
- Buy and Hold (BAH): Initial allocation with no rebalancing
- Constant Rebalanced Portfolio (CRP): Fixed target weights with regular rebalancing
"""

from typing import Any, Dict
import numpy as np
import pandas as pd

from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from .utils import (
    calculate_relative_returns,
    normalize_weights,
    uniform_weights,
    calculate_turnover,
    calculate_cumulative_returns,
)


class EqualWeight(OlpsStrategy):
    """
    Equal Weight (EW) / Uniform Portfolio Strategy.
    
    Allocates equal weight (1/N) to each asset and rebalances regularly.
    This is the simplest possible strategy and serves as a baseline benchmark.
    
    **Classification**: BENCHMARK
    **Implementability**: Yes - Simple and practical for live trading
    **Complexity**: LOW
    
    Paper Reference:
        Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey.
        ACM Computing Surveys, V, N, Article A (December 2012), 33 pages.
        https://arxiv.org/abs/1212.2129
    """
    
    def __init__(self):
        super().__init__(
            id="EW",
            name="Equal Weight",
            paper_ref="Li & Hoi 2012 - OLPS Survey",
            library_ref=None,
            strategy_type=StrategyType.BENCHMARK,
            complexity=StrategyComplexity.LOW,
            description="Allocates equal weight (1/N) to each asset. Rebalances to maintain equal weights. "
                        "Simple baseline that surprisingly often beats more complex strategies. No optimization required.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute Equal Weight strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, can include:
                - initial_capital: Starting capital (default: 1.0)
                - rebalance_frequency: Not used (always rebalances)
        
        Returns:
            StrategyResult with uniform weights throughout
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Equal weights for all periods
        equal_weights = uniform_weights(n_assets)
        
        # Build weights matrix (same weights every period)
        weights_matrix = pd.DataFrame(
            np.tile(equal_weights, (n_periods, 1)),
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
        turnover_series = pd.Series(0.0, index=prices_df.index)
        for t in range(1, len(price_relatives)):
            # Weights after price change
            weights_after_change = equal_weights * price_relatives[t-1]
            weights_after_change = normalize_weights(weights_after_change)
            
            # Turnover to rebalance back to equal weights
            turnover_series.iloc[t] = calculate_turnover(
                weights_after_change,
                equal_weights
            )
        
        # Metadata
        metadata = {
            'strategy_type': 'baseline',
            'n_assets': n_assets,
            'uniform_weight': 1.0 / n_assets,
            'description': 'Equal allocation (1/N) with full rebalancing each period'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),  # No costs yet
            turnover=turnover_series,
            metadata=metadata
        )


class BuyAndHold(OlpsStrategy):
    """
    Buy and Hold (BAH) Strategy.
    
    Invests with initial weights and never rebalances. Weights drift with asset returns.
    Ultimate passive strategy - no trading after initial allocation.
    
    **Classification**: BENCHMARK
    **Implementability**: Yes - Simplest possible passive strategy
    **Complexity**: LOW
    
    Paper Reference:
        Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey.
        ACM Computing Surveys, V, N, Article A (December 2012), 33 pages.
        https://arxiv.org/abs/1212.2129
    """
    
    def __init__(self):
        super().__init__(
            id="BAH",
            name="Buy and Hold",
            paper_ref="Li & Hoi 2012 - OLPS Survey",
            library_ref=None,
            strategy_type=StrategyType.BENCHMARK,
            complexity=StrategyComplexity.LOW,
            description="Buy assets with initial weights and never rebalance. Weights drift naturally with "
                        "asset returns. Zero trading costs after initial purchase. True passive investing.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute Buy and Hold strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, can include:
                - initial_capital: Starting capital (default: 1.0)
                - initial_weights: Starting weights (default: equal weight)
        
        Returns:
            StrategyResult with drifting weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        initial_weights = config.get('initial_weights', None)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Initialize weights
        if initial_weights is None:
            initial_weights = uniform_weights(n_assets)
        else:
            initial_weights = np.array(initial_weights)
            initial_weights = normalize_weights(initial_weights)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Track weights over time (they drift with returns)
        weights_over_time = np.zeros((n_periods, n_assets))
        weights_over_time[0] = initial_weights
        
        # Let weights drift with price changes
        current_weights = initial_weights.copy()
        for t in range(1, n_periods):
            # Weights change proportionally to price relatives
            current_weights = current_weights * price_relatives[t-1]
            current_weights = normalize_weights(current_weights)
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
        
        # No turnover (no rebalancing)
        turnover_series = pd.Series(0.0, index=prices_df.index)
        
        # Metadata
        metadata = {
            'strategy_type': 'baseline',
            'n_assets': n_assets,
            'initial_weights': initial_weights.tolist(),
            'final_weights': current_weights.tolist(),
            'description': 'Buy once and hold with no rebalancing (weights drift)'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),  # No costs
            turnover=turnover_series,
            metadata=metadata
        )


class ConstantRebalancedPortfolio(OlpsStrategy):
    """
    Constant Rebalanced Portfolio (CRP) Strategy.
    
    Maintains fixed target weights by rebalancing at each period.
    Can be seen as generalization of Equal Weight with custom target weights.
    
    **Classification**: BENCHMARK
    **Implementability**: Yes - Standard rebalancing strategy
    **Complexity**: LOW
    
    Paper Reference:
        Li, B., Hoi, S. C.H., 2012. OnLine Portfolio Selection: A Survey.
        ACM Computing Surveys, V, N, Article A (December 2012), 33 pages.
        https://arxiv.org/abs/1212.2129
        
        Also see: Cover, T.M., 1991. Universal Portfolios.
        Mathematical Finance, 1(1), pp.1-29.
    """
    
    def __init__(self):
        super().__init__(
            id="CRP",
            name="Constant Rebalanced Portfolio",
            paper_ref="Cover 1991; Li & Hoi 2012",
            library_ref=None,
            strategy_type=StrategyType.BENCHMARK,
            complexity=StrategyComplexity.LOW,
            description="Maintains fixed target weights through regular rebalancing. Generalizes Equal Weight "
                        "by allowing custom target allocations. Classic portfolio rebalancing strategy.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute Constant Rebalanced Portfolio strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, must include:
                - target_weights: List/array of target weights (must sum to 1)
                Optional:
                - initial_capital: Starting capital (default: 1.0)
        
        Returns:
            StrategyResult with constant target weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        target_weights = config.get('target_weights', None)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Target weights
        if target_weights is None:
            # Default to equal weights
            target_weights = uniform_weights(n_assets)
        elif isinstance(target_weights, str) and target_weights == 'equal':
            target_weights = uniform_weights(n_assets)
        else:
            target_weights = np.array(target_weights)
            target_weights = normalize_weights(target_weights)
        
        # Validate weights
        if len(target_weights) != n_assets:
            raise ValueError(
                f"Target weights length ({len(target_weights)}) "
                f"doesn't match number of assets ({n_assets})"
            )
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Build weights matrix (constant target weights every period)
        weights_matrix = pd.DataFrame(
            np.tile(target_weights, (n_periods, 1)),
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
        turnover_series = pd.Series(0.0, index=prices_df.index)
        for t in range(1, len(price_relatives)):
            # Weights after price change
            weights_after_change = target_weights * price_relatives[t-1]
            weights_after_change = normalize_weights(weights_after_change)
            
            # Turnover to rebalance back to target weights
            turnover_series.iloc[t] = calculate_turnover(
                weights_after_change,
                target_weights
            )
        
        # Metadata
        metadata = {
            'strategy_type': 'baseline',
            'n_assets': n_assets,
            'target_weights': target_weights.tolist(),
            'description': f'Constant rebalancing to fixed weights'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),  # No costs yet
            turnover=turnover_series,
            metadata=metadata
        )
