import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, Any, Optional

from backend.strategies.base import (
    OlpsStrategy,
    StrategyResult,
    StrategyType,
    StrategyComplexity
)
from backend.strategies.utils import (
    calculate_relative_returns,
    normalize_weights
)

class DTC(OlpsStrategy):
    """
    Decentralized Online Portfolio Selection with Transaction Costs (DTC).
    
    This strategy optimizes portfolio weights by maximizing expected returns while
    penalizing transaction costs and enforcing a minimum entropy constraint for
    diversification.
    
    Variants:
    - DTC1: Uses simple exponential smoothing for price prediction.
    - DTC2: Uses adaptive exponential smoothing.
    
    Reference:
    "Decentralized Online Portfolio Selection with Transaction Costs"
    """
    
    def __init__(self):
        super().__init__(
            id="DTC",
            name="Decentralized Online Portfolio Selection",
            paper_ref="Decentralized Online Portfolio Selection with Transaction Costs",
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.HIGH,
            description="Optimizes portfolio with transaction cost regularization and entropy constraints.",
            implementable=True
        )
        
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Run the DTC strategy.
        
        Config parameters:
        - variant: 'DTC1' or 'DTC2' (default: 'DTC1')
        - lambda_param: Trade-off parameter for transaction costs (default: 0.05)
        - xi_param: Minimum entropy threshold (default: 1.0)
        - alpha: Decay factor for DTC1 (default: 0.5)
        - gamma: Step size for DTC2 (default: 1e-5)
        - cost_rate: Transaction cost rate (default: 0.0025)
        - initial_capital: Initial portfolio value (default: 1.0)
        """
        # Extract configuration
        variant = config.get('variant', 'DTC1')
        lambda_param = config.get('lambda_param', 0.05)
        xi_param = config.get('xi_param', 1.0)
        alpha = config.get('alpha', 0.5)
        gamma = config.get('gamma', 1e-5)
        cost_rate = config.get('cost_rate', 0.0025)
        initial_capital = config.get('initial_capital', 10000.0)
        
        # Data preparation
        prices = prices_df.values
        dates = prices_df.index
        assets = prices_df.columns
        n_periods, n_assets = prices.shape
        
        # Calculate price relatives (x_t = p_t / p_{t-1})
        # We prepend a row of 1s for the first period to align indices
        x = np.vstack([np.ones(n_assets), prices[1:] / prices[:-1]])
        
        # Initialize variables
        weights = np.zeros((n_periods, n_assets))
        b_prev = np.ones(n_assets) / n_assets  # Initial uniform weights
        weights[0] = b_prev
        
        # State variables for predictions
        p_pred_prev = prices[0].copy()  # For DTC1
        x_pred_prev = np.ones(n_assets) # For DTC2
        alpha_adaptive = np.full(n_assets, alpha) # For DTC2
        
        # Portfolio values
        gross_values = np.zeros(n_periods)
        net_values = np.zeros(n_periods)
        turnover = np.zeros(n_periods)
        
        gross_values[0] = initial_capital
        net_values[0] = initial_capital
        
        # Helper: Entropy calculation
        def calculate_entropy(w):
            w_safe = np.clip(w, 1e-10, 1.0)
            return -np.sum(w_safe * np.log(w_safe))
        
        # Helper: Objective function
        def objective(b, x_hat, b_tilde):
            return_term = np.dot(b, x_hat)
            trans_term = lambda_param * np.sum(np.abs(b - b_tilde))
            return -(return_term - trans_term) # Minimize negative objective
            
        # Helper: Entropy constraint
        def entropy_constraint(b):
            return calculate_entropy(b) - xi_param
            
        # Optimization constraints
        constraints = [
            {'type': 'eq', 'fun': lambda b: np.sum(b) - 1},
            {'type': 'ineq', 'fun': entropy_constraint}
        ]
        bounds = [(0, 1) for _ in range(n_assets)]
        
        # Main loop
        for t in range(1, n_periods):
            # 1. Calculate adjusted previous portfolio (after price changes)
            x_actual_prev = x[t-1] # x_{t-1}
            
            # b_tilde_{t-1} = (b_{t-1} * x_{t-1}) / (b_{t-1} . x_{t-1})
            denom = np.dot(b_prev, x_actual_prev)
            if denom == 0:
                b_tilde_prev = b_prev
            else:
                b_tilde_prev = (b_prev * x_actual_prev) / denom
            
            # 2. Predict next price relative x_hat_t
            if variant == 'DTC1':
                # Exponential smoothing on PRICES
                # p_hat_t = alpha * p_{t-1} + (1-alpha) * p_hat_{t-1}
                p_prev = prices[t-1]
                p_pred = alpha * p_prev + (1 - alpha) * p_pred_prev
                
                # x_hat_t = p_hat_t / p_{t-1}
                # Handle division by zero if price is 0 (unlikely)
                with np.errstate(divide='ignore', invalid='ignore'):
                    x_pred = p_pred / p_prev
                    x_pred = np.nan_to_num(x_pred, nan=1.0)
                
                p_pred_prev = p_pred
                
            else: # DTC2
                # Adaptive exponential smoothing on RELATIVES (based on notes logic)
                # Note: The notes say "predict_price_relative_DTC2" uses alpha_adaptive
                
                # Update alpha based on previous prediction error
                # error = x_{t-1} - x_hat_{t-1}
                # But wait, at t=1, we don't have x_hat_0. 
                # The notes initialize x_pred_prev = ones.
                
                prediction_error = x_actual_prev - x_pred_prev
                alpha_adaptive += gamma * np.sign(prediction_error)
                alpha_adaptive = np.clip(alpha_adaptive, 0, 1)
                
                # Prediction: x_hat_t = alpha_t + (1-alpha_t) * (x_hat_{t-1} / x_{t-1})
                # Wait, the formula in notes: x_pred = alpha + (1-alpha) * (x_pred_prev / actual_x_prev)
                # This looks like a mean reversion of relatives?
                with np.errstate(divide='ignore', invalid='ignore'):
                    term2 = x_pred_prev / x_actual_prev
                    term2 = np.nan_to_num(term2, nan=1.0)
                    
                x_pred = alpha_adaptive + (1 - alpha_adaptive) * term2
                x_pred_prev = x_pred
            
            # 3. Optimize portfolio b_t
            # Initial guess: uniform or previous
            x0 = np.ones(n_assets) / n_assets
            
            try:
                res = minimize(
                    objective, 
                    x0, 
                    args=(x_pred, b_tilde_prev),
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints,
                    options={'disp': False, 'ftol': 1e-6}
                )
                
                if res.success:
                    b_t = normalize_weights(res.x)
                else:
                    # Fallback to previous weights if optimization fails
                    b_t = b_tilde_prev
            except Exception:
                b_t = b_tilde_prev
                
            weights[t] = b_t
            b_prev = b_t
            
            # 4. Calculate returns and turnover
            # Actual return for period t: b_t . x_t
            # But we incur transaction costs moving from b_tilde_prev to b_t
            
            # Transaction cost
            # cost = rate * sum(|b_t - b_tilde_prev|)
            tc = cost_rate * np.sum(np.abs(b_t - b_tilde_prev))
            turnover[t] = np.sum(np.abs(b_t - b_tilde_prev))
            
            # Gross return (before cost)
            gross_ret = np.dot(b_t, x[t]) - 1
            gross_values[t] = gross_values[t-1] * (1 + gross_ret)
            
            # Net return (after cost)
            # Wealth update: W_t = W_{t-1} * (b_t . x_t - cost)
            # Note: The cost is deducted from the invested amount effectively reducing return
            period_factor = np.dot(b_t, x[t]) - tc
            net_values[t] = net_values[t-1] * period_factor
            
        # Create result objects
        weights_df = pd.DataFrame(weights, index=dates, columns=assets)
        
        return StrategyResult(
            weights=weights_df,
            gross_portfolio_values=pd.Series(gross_values, index=dates),
            net_portfolio_values=pd.Series(net_values, index=dates),
            turnover=pd.Series(turnover, index=dates),
            metadata={
                "variant": variant,
                "lambda": lambda_param,
                "xi": xi_param,
                "cost_rate": cost_rate
            }
        )
