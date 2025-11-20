"""
Transaction cost models for portfolio backtesting.

Implements realistic broker fee structures, including Maxblue (Deutsche Bank) costs.
"""

from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd
import numpy as np


@dataclass
class TransactionCostModel:
    """
    Base class for transaction cost models.
    """
    name: str
    
    def calculate_cost(self, trade_value: float, **kwargs) -> float:
        """
        Calculate transaction cost for a single trade.
        
        Args:
            trade_value: Absolute value of trade in base currency
            **kwargs: Additional parameters (e.g., shares, price)
            
        Returns:
            Transaction cost in base currency
        """
        raise NotImplementedError


@dataclass
class MaxblueCostModel(TransactionCostModel):
    """
    Maxblue (Deutsche Bank) transaction cost model.
    
    Fee structure (as of 2025):
    - Base commission: 0.25% of trade value
    - Minimum commission: €8.90 per trade
    - Maximum commission: €58.90 per trade
    - Exchange fee: ~€2.00 per order (varies by exchange)
    
    Total cost per trade = min(max(0.0025 × trade_value, €8.90), €58.90) + €2.00
    """
    
    name: str = "Maxblue"
    commission_rate: float = 0.0025  # 0.25%
    commission_min: float = 8.90  # EUR
    commission_max: float = 58.90  # EUR
    exchange_fee: float = 2.00  # EUR per order
    currency: str = "EUR"
    
    def calculate_cost(self, trade_value: float, **kwargs) -> float:
        """
        Calculate Maxblue transaction cost.
        
        Args:
            trade_value: Absolute value of trade in EUR
            
        Returns:
            Total transaction cost in EUR
        """
        if trade_value <= 0:
            return 0.0
        
        # Base commission with min/max bounds
        commission_raw = self.commission_rate * trade_value
        commission = np.clip(commission_raw, self.commission_min, self.commission_max)
        
        # Total cost
        total_cost = commission + self.exchange_fee
        
        return total_cost


@dataclass
class ZeroCostModel(TransactionCostModel):
    """Zero transaction costs (frictionless market assumption)."""
    
    name: str = "Zero Cost"
    
    def calculate_cost(self, trade_value: float, **kwargs) -> float:
        """No transaction costs."""
        return 0.0


@dataclass
class PercentageCostModel(TransactionCostModel):
    """Simple percentage-based transaction cost."""
    
    name: str = "Percentage"
    rate: float = 0.001  # 0.1% default
    
    def calculate_cost(self, trade_value: float, **kwargs) -> float:
        """Calculate cost as percentage of trade value."""
        return self.rate * abs(trade_value)


def apply_transaction_costs(
    weights: pd.DataFrame,
    portfolio_values: pd.Series,
    price_relatives: pd.DataFrame,
    cost_model: TransactionCostModel,
    initial_capital: float = 10000.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Apply transaction costs to portfolio backtest.
    
    Args:
        weights: Portfolio weights (date × assets)
        portfolio_values: Gross portfolio values (before costs)
        price_relatives: Price relatives (P_t / P_{t-1})
        cost_model: Transaction cost model to use
        initial_capital: Starting capital
        
    Returns:
        Tuple of (net_portfolio_values, total_costs, costs_per_period)
    """
    n_periods = len(weights)
    n_assets = weights.shape[1]
    
    # Initialize
    net_values = np.zeros(n_periods)
    net_values[0] = initial_capital
    
    costs_per_period = np.zeros(n_periods)
    total_costs = 0.0
    
    # Current holdings (shares of each asset)
    current_holdings = np.zeros(n_assets)
    current_holdings[:] = initial_capital * weights.iloc[0].values
    
    for t in range(1, n_periods):
        # Portfolio value before rebalancing (holdings appreciate with prices)
        holdings_value = current_holdings * price_relatives.iloc[t].values
        portfolio_value_pre = holdings_value.sum()
        
        # Target holdings after rebalancing
        target_weights = weights.iloc[t].values
        target_holdings = portfolio_value_pre * target_weights
        
        # Calculate trades (difference between target and current)
        trades = target_holdings - holdings_value
        trade_values = np.abs(trades)
        
        # Calculate transaction costs
        period_cost = 0.0
        for asset_idx in range(n_assets):
            if trade_values[asset_idx] > 0:  # Only if there's a trade
                trade_cost = cost_model.calculate_cost(trade_values[asset_idx])
                period_cost += trade_cost
        
        # Update portfolio
        net_values[t] = portfolio_value_pre - period_cost
        costs_per_period[t] = period_cost
        total_costs += period_cost
        
        # Update holdings (after costs)
        current_holdings = target_holdings
        # Adjust for costs proportionally
        if net_values[t] > 0:
            current_holdings *= (net_values[t] / portfolio_value_pre)
    
    return (
        pd.Series(net_values, index=weights.index),
        total_costs,
        pd.Series(costs_per_period, index=weights.index)
    )


def compare_cost_models(
    weights: pd.DataFrame,
    portfolio_values: pd.Series,
    price_relatives: pd.DataFrame,
    initial_capital: float = 10000.0
) -> Dict[str, Dict[str, Any]]:
    """
    Compare multiple cost models on the same backtest.
    
    Returns:
        Dict mapping model name to results dict with:
            - net_portfolio_values: Series
            - total_costs: float
            - final_value: float
            - cost_drag: float (percentage points of return lost to costs)
    """
    models = {
        'Zero Cost': ZeroCostModel(),
        'Maxblue': MaxblueCostModel(),
        '0.1% Flat': PercentageCostModel(rate=0.001),
        '0.5% Flat': PercentageCostModel(rate=0.005),
    }
    
    results = {}
    gross_return = (portfolio_values.iloc[-1] / initial_capital - 1) * 100
    
    for model_name, model in models.items():
        net_values, total_costs, costs_per_period = apply_transaction_costs(
            weights, portfolio_values, price_relatives, model, initial_capital
        )
        
        net_return = (net_values.iloc[-1] / initial_capital - 1) * 100
        cost_drag = gross_return - net_return
        
        results[model_name] = {
            'net_portfolio_values': net_values,
            'total_costs': total_costs,
            'costs_per_period': costs_per_period,
            'final_value': net_values.iloc[-1],
            'net_return_%': net_return,
            'cost_drag_%': cost_drag,
            'cost_drag_bps': cost_drag * 100,  # basis points
        }
    
    return results


def estimate_turnover_from_weights(weights: pd.DataFrame) -> pd.Series:
    """
    Estimate portfolio turnover from weight changes.
    
    Turnover at time t = Σ |w_t - w_{t-1}| / 2
    
    This represents the fraction of portfolio traded.
    """
    turnover = weights.diff().abs().sum(axis=1) / 2
    turnover.iloc[0] = 1.0  # Initial allocation
    return turnover
