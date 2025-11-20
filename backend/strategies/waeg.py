import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity

class WAEGStrategy(OlpsStrategy):
    """
    Weak Aggregating Exponential Gradient (WAEG) Strategy.
    
    This strategy combines multiple Exponential Gradient (EG) experts with different 
    learning rates using the Weak Aggregating Algorithm (WAA).
    
    Reference:
    "Boosting Exponential Gradient Strategy for Online Portfolio Selection"
    """
    
    def __init__(self):
        super().__init__(
            id="WAEG",
            name="WAEG",
            paper_ref="Boosting Exponential Gradient Strategy for Online Portfolio Selection",
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.MEDIUM,
            description="Combines multiple Exponential Gradient experts using Weak Aggregating Algorithm.",
            implementable=True
        )
        
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Run WAEG strategy.
        
        Args:
            prices_df: DataFrame of asset prices
            config: Strategy configuration
                - k: Number of experts (default: 20)
                - eta_min: Minimum learning rate (default: 0.01)
                - eta_max: Maximum learning rate (default: 0.2)
                - alpha: Smoothing parameter (default: 0.0)
                
        Returns:
            StrategyResult object
        """
        # Extract configuration
        k = config.get('k', 20)
        eta_min = config.get('eta_min', 0.01)
        eta_max = config.get('eta_max', 0.2)
        alpha = config.get('alpha', 0.0)
        
        # Initialize experts
        eta_list = np.linspace(eta_min, eta_max, k)
        
        # Data preparation
        prices = prices_df.values
        n_periods, n_assets = prices.shape
        dates = prices_df.index
        assets = prices_df.columns
        
        # Calculate price relatives (x_t = p_t / p_{t-1})
        # First period has no relative, so we start from t=1
        x = np.zeros_like(prices)
        x[1:] = prices[1:] / prices[:-1]
        x[0] = 1.0 # Placeholder for first period
        
        # Initialize state
        # Portfolio weights for each expert
        expert_b = np.ones((k, n_assets)) / n_assets
        
        # Cumulative log returns (loss) for each expert
        expert_log_returns = np.zeros(k)
        
        # Expert weights (WAA weights)
        expert_weights = np.ones(k) / k
        
        # Result storage
        weights = np.zeros((n_periods, n_assets))
        weights[0] = np.ones(n_assets) / n_assets # Initial uniform portfolio
        
        portfolio_values = np.zeros(n_periods)
        portfolio_values[0] = config.get('initial_capital', 10000.0)
        
        # Run loop
        for t in range(n_periods - 1):
            # 1. Current portfolio is weighted average of experts
            # b_{t+1} = sum(w_{t,k} * b_{t+1,k})
            # Note: In online learning, we usually decide b_{t+1} based on info up to t.
            # Here we calculate weights for t+1 based on update at t.
            
            # Get price relative for period t+1 (to be revealed)
            # But first we need to update experts based on x_{t+1} AFTER we decided b_{t+1}
            # Wait, standard loop is:
            # At t: decide b_{t+1}
            # Observe x_{t+1}
            # Update wealth, update experts
            
            # Let's align with the standard loop structure
            # We are at index t (representing end of period t). We want to decide weights for t+1.
            # We have observed x_t (return from t-1 to t).
            
            # Current price relative x_{t+1} is NOT known yet.
            # We use the EXPERT portfolios that were updated at step t (using x_t)
            
            # Aggregate expert portfolios to get strategy portfolio
            b_waeg = np.zeros(n_assets)
            for i in range(k):
                b_waeg += expert_weights[i] * expert_b[i]
            
            # Store the weight for the NEXT period (t+1)
            weights[t+1] = b_waeg
            
            # Now we "move" to t+1 and observe x_{t+1}
            x_next = x[t+1]
            
            # Calculate portfolio return
            port_ret = np.dot(b_waeg, x_next)
            portfolio_values[t+1] = portfolio_values[t] * port_ret
            
            # Update experts and their weights
            
            # 1. Update expert cumulative performance (Gain/Loss)
            # G_{t, k} = G_{t-1, k} + log(b_{t,k} * x_t)
            current_expert_returns = np.zeros(k)
            for i in range(k):
                ret = np.dot(expert_b[i], x_next)
                current_expert_returns[i] = ret
                if ret > 0:
                    expert_log_returns[i] += np.log(ret)
                else:
                    expert_log_returns[i] += -100 # Penalize heavily if 0 or negative
            
            # 2. Update expert weights (WAA)
            # w_{t+1, k} propto exp(G_{t,k} / sqrt(t+1)) ?? 
            # Paper says beta_t = exp(1/sqrt(t)). Weight ~ beta_t ^ G_{t-1}
            # So Weight ~ exp(G / sqrt(t))
            
            # Time index for learning rate: t+1 (since we have observed t+1 periods)
            # Avoid division by zero
            time_idx = t + 1
            
            # Calculate unnormalized weights
            # Use stable softmax-like trick: exp(x - max(x))
            # exponent = G / sqrt(time)
            exponents = expert_log_returns / np.sqrt(time_idx)
            max_exp = np.max(exponents)
            numerator = np.exp(exponents - max_exp)
            expert_weights = numerator / np.sum(numerator)
            
            # 3. Update expert portfolios (EG update)
            # b_{t+1} = b_t * exp(eta * x_t / (b_t * x_t)) / Z
            for i in range(k):
                eta = eta_list[i]
                b = expert_b[i]
                
                # EG Update
                denom = np.dot(b, x_next)
                if denom > 1e-10:
                    numerator_eg = b * np.exp(eta * x_next / denom)
                    b_new = numerator_eg / np.sum(numerator_eg)
                else:
                    b_new = b # No update if return is 0
                
                # Apply smoothing if alpha > 0 (WAEG~)
                if alpha > 0:
                    b_new = (1 - alpha) * b_new + (alpha / n_assets)
                    
                expert_b[i] = b_new
                
        # Create result objects
        weights_df = pd.DataFrame(weights, index=dates, columns=assets)
        portfolio_series = pd.Series(portfolio_values, index=dates)
        
        # Calculate turnover
        turnover = np.zeros(n_periods)
        for t in range(1, n_periods):
            turnover[t] = np.sum(np.abs(weights[t] - weights[t-1]))
        turnover_series = pd.Series(turnover, index=dates)
        
        return StrategyResult(
            weights=weights_df,
            gross_portfolio_values=portfolio_series,
            net_portfolio_values=portfolio_series, # Costs not implemented yet
            turnover=turnover_series,
            metadata={"k": k, "eta_range": (eta_min, eta_max)}
        )
