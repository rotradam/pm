"""
Adapter for skfolio strategies to be used in the OLPS framework.
"""

from typing import Any, Dict, Type, Optional
import numpy as np
import pandas as pd
from skfolio.optimization import MeanRisk, ObjectiveFunction, BaseOptimization

from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from .utils import (
    calculate_relative_returns,
    calculate_cumulative_returns,
    calculate_turnover,
    normalize_weights,
    uniform_weights
)

class SkfolioAdapter(OlpsStrategy):
    """
    Adapter to run skfolio strategies within the OLPS framework.
    
    Performs a rolling window optimization to generate time-varying weights.
    """
    
    def __init__(
        self,
        estimator_cls: Type[BaseOptimization],
        estimator_kwargs: Dict[str, Any],
        id: str,
        name: str,
        window_size: int = 252,
        rebalance_frequency: str = 'Monthly',
        description: str = ""
    ):
        super().__init__(
            id=id,
            name=name,
            paper_ref="skfolio documentation",
            library_ref="skfolio",
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.HIGH,
            description=description,
            implementable=True
        )
        self.estimator_cls = estimator_cls
        self.estimator_kwargs = estimator_kwargs
        self.window_size = window_size
        self.rebalance_frequency = rebalance_frequency

    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute skfolio strategy using rolling window optimization.
        """
        initial_capital = config.get('initial_capital', 10000.0)
        window = config.get('window_size', self.window_size)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        dates = prices_df.index
        
        # Initialize weights (start with equal weight or 0)
        weights_matrix = pd.DataFrame(
            0.0,
            index=dates,
            columns=prices_df.columns
        )
        
        # Determine rebalance dates
        if self.rebalance_frequency == 'Daily':
            rebalance_dates = dates
        elif self.rebalance_frequency == 'Weekly':
            rebalance_dates = prices_df.resample('W').last().index
        elif self.rebalance_frequency == 'Monthly':
            rebalance_dates = prices_df.resample('ME').last().index
        elif self.rebalance_frequency == 'Quarterly':
            rebalance_dates = prices_df.resample('QE').last().index
        else:
            rebalance_dates = dates # Default to daily
            
        rebalance_dates = [d for d in rebalance_dates if d in dates]
        
        # Initial weights (before first rebalance)
        current_weights = uniform_weights(n_assets)
        
        # Loop through time
        last_rebalance_idx = 0
        
        for t in range(n_periods):
            date = dates[t]
            
            # Check if we should rebalance
            if date in rebalance_dates and t >= window:
                # Get historical data for training
                train_data = prices_df.iloc[t-window:t]
                
                try:
                    # Fit skfolio model
                    # skfolio expects returns or prices depending on model, usually prices or returns
                    # Most skfolio estimators take X as returns
                    train_returns = train_data.pct_change().dropna()
                    
                    if not train_returns.empty:
                        model = self.estimator_cls(**self.estimator_kwargs)
                        model.fit(train_returns)
                        
                        # Get weights
                        if hasattr(model, 'weights_'):
                            new_weights = model.weights_
                        elif hasattr(model, 'predict'):
                            new_weights = model.predict(train_returns)
                        else:
                            new_weights = current_weights # Fallback
                            
                        current_weights = normalize_weights(new_weights)
                except Exception as e:
                    # Fallback to previous weights on error
                    # print(f"Optimization failed at {date}: {e}")
                    pass
            
            weights_matrix.iloc[t] = current_weights
            
        # Calculate portfolio values
        price_relatives = calculate_relative_returns(prices_df)
        portfolio_values = calculate_cumulative_returns(
            weights_matrix,
            price_relatives,
            initial_capital
        )
        
        # Calculate turnover
        turnover_series = pd.Series(0.0, index=dates)
        for t in range(1, n_periods):
            weights_after_change = weights_matrix.iloc[t-1] * price_relatives[t-1]
            weights_after_change = normalize_weights(weights_after_change)
            turnover_series.iloc[t] = calculate_turnover(
                weights_after_change,
                weights_matrix.iloc[t].values
            )

        metadata = {
            'strategy_type': 'skfolio_adapter',
            'estimator': self.estimator_cls.__name__,
            'window_size': window,
            'rebalance_frequency': self.rebalance_frequency
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
