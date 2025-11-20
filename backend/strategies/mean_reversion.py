"""
Mean Reversion OLPS Strategies.

Implements strategies that bet on price reversals:
- OLMAR: Online Moving Average Reversion
- PAMR: Passive Aggressive Mean Reversion
- CWMR: Confidence Weighted Mean Reversion
- RMR: Robust Median Reversion
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from scipy.stats import norm

from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from .utils import (
    calculate_relative_returns,
    normalize_weights,
    uniform_weights,
    calculate_turnover,
    calculate_cumulative_returns,
    simplex_projection,
    simple_moving_average,
    exponentially_weighted_average,
)


class OLMAR(OlpsStrategy):
    """
    Online Moving Average Reversion (OLMAR) Strategy.
    
    Predicts mean reversion toward moving average (SMA or EWA) and adjusts weights accordingly.
    
    Algorithm:
    1. Calculate moving average (SMA or EWA)
    2. Predict next price relative: x̂_t = MA_t / price_{t-1}
    3. Loss = max(0, epsilon - portfolio_return)
    4. Lambda = loss / ||x̂_t - mean(x̂_t)||²
    5. w_{t+1} = w_t + lambda * (x̂_t - mean(x̂_t))
    6. Project to simplex
    
    Paper Reference:
        Li, B., Hoi, S., 2012. On-Line Portfolio Selection with Moving Average Reversion.
        ICML 2012.
        https://arxiv.org/pdf/1206.4626.pdf
    """
    
    def __init__(self):
        super().__init__(
            id="OLMAR",
            name="Online Moving Average Reversion",
            paper_ref="Li & Hoi 2012 - OLMAR",
            library_ref="portfoliolab.olmar (migrated)"
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute OLMAR strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, must include:
                - reversion_method: 1 (SMA) or 2 (EWA)
                - epsilon: Reversion threshold [1, inf), typical: 20
                - window: SMA window (for method 1), typical: 5-21
                - alpha: EWA smoothing (0, 1) (for method 2), typical: 0.95
                Optional:
                - initial_capital: Starting capital (default: 1.0)
        
        Returns:
            StrategyResult with OLMAR weights
        """
        # Extract configuration
        reversion_method = config.get('reversion_method')
        if reversion_method not in [1, 2]:
            raise ValueError("reversion_method must be 1 (SMA) or 2 (EWA)")
        
        epsilon = config.get('epsilon')
        if epsilon is None or epsilon < 1:
            raise ValueError("epsilon must be >= 1")
        
        if reversion_method == 1:
            window = config.get('window')
            if window is None or window < 1:
                raise ValueError("window must be >= 1 for SMA method")
        else:
            alpha = config.get('alpha')
            if alpha is None or alpha <= 0 or alpha >= 1:
                raise ValueError("alpha must be in (0, 1) for EWA method")
        
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Initialize weights
        current_weights = uniform_weights(n_assets)
        
        # Calculate moving averages
        if reversion_method == 1:
            ma = simple_moving_average(prices_df, window)
        else:
            ma = exponentially_weighted_average(prices_df, alpha)
        
        # Calculate predicted price relatives
        # x̂_t = MA_t / price_{t-1}
        predicted_relatives = (ma / prices_df.shift(1)).dropna()
        
        # Calculate actual price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Track weights over time
        weights_over_time = np.zeros((n_periods, n_assets))
        weights_over_time[0] = current_weights
        turnover_values = np.zeros(n_periods)
        
        # Determine start time (need enough data for MA)
        start_time = window if reversion_method == 1 else 1
        
        # Run OLMAR updates
        for t in range(1, n_periods):
            # For initial periods before MA is ready, use uniform weights
            if t < start_time:
                weights_over_time[t] = current_weights
                continue
            
            # Get predicted relatives (use index to match dates properly)
            try:
                x_hat = predicted_relatives.loc[prices_df.index[t]].values
            except KeyError:
                # If MA not available yet, keep current weights
                weights_over_time[t] = current_weights
                continue
            
            # Calculate loss function
            portfolio_return = np.dot(current_weights, price_relatives[t-1])
            loss = max(0, epsilon - portfolio_return)
            
            # Calculate deviation from mean
            x_bar = x_hat - np.mean(x_hat) * np.ones(n_assets)
            
            # Calculate lambda (lagrangian multiplier)
            norm_sq = np.linalg.norm(x_bar) ** 2
            if norm_sq == 0:
                lambd = 0
            else:
                lambd = loss / norm_sq
            
            # Update weights
            new_weights = current_weights + lambd * x_bar
            
            # Project to simplex
            new_weights = simplex_projection(new_weights)
            new_weights = normalize_weights(new_weights)
            
            # Calculate turnover
            turnover_values[t] = calculate_turnover(
                current_weights,
                new_weights,
                price_relatives[t-1]
            )
            
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
            'strategy_type': 'mean_reversion',
            'n_assets': n_assets,
            'reversion_method': 'SMA' if reversion_method == 1 else 'EWA',
            'epsilon': epsilon,
            'window': window if reversion_method == 1 else None,
            'alpha': alpha if reversion_method == 2 else None,
            'description': f'OLMAR with {"SMA" if reversion_method == 1 else "EWA"}, epsilon={epsilon}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class PAMR(OlpsStrategy):
    """
    Passive Aggressive Mean Reversion (PAMR) Strategy.
    
    Switches between passive and aggressive mean reversion based on portfolio performance.
    
    Three variants:
    - PAMR (0): tau = loss / ||x̄||²
    - PAMR-1 (1): tau = min(C, loss / ||x̄||²)
    - PAMR-2 (2): tau = loss / (||x̄||² + 1/(2C))
    
    Algorithm:
    1. Calculate loss = max(0, portfolio_return - epsilon)
    2. Calculate adjusted returns: x̄ = x - mean(x)
    3. Calculate tau (step size) based on optimization method
    4. Update: w_{t+1} = w_t - tau * x̄
    5. Project to simplex
    
    Paper Reference:
        Li, B., Zhao, P., Hoi, S.C., Gopalkrishnan, V., 2012.
        PAMR: Passive aggressive mean reversion strategy for portfolio selection.
        Machine Learning, 87, 221-258.
        https://link.springer.com/content/pdf/10.1007%2Fs10994-012-5281-z.pdf
    """
    
    def __init__(self):
        super().__init__(
            id="PAMR",
            name="Passive Aggressive Mean Reversion",
            paper_ref="Li et al. 2012 - PAMR",
            library_ref="portfoliolab.pamr (migrated)"
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute PAMR strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict, must include:
                - optimization_method: 0 (PAMR), 1 (PAMR-1), or 2 (PAMR-2)
                - epsilon: Sensitivity [0, inf), typical: 0 (active) or 1 (passive)
                - agg: Aggressiveness (C) [0, inf), typical: 100 (PAMR-1), 10000 (PAMR-2)
                Optional:
                - initial_capital: Starting capital (default: 1.0)
        
        Returns:
            StrategyResult with PAMR weights
        """
        # Extract configuration
        optimization_method = config.get('optimization_method')
        if optimization_method not in [0, 1, 2]:
            raise ValueError("optimization_method must be 0 (PAMR), 1 (PAMR-1), or 2 (PAMR-2)")
        
        epsilon = config.get('epsilon')
        if epsilon is None or epsilon < 0:
            raise ValueError("epsilon must be >= 0")
        
        agg = config.get('agg')  # C parameter
        if agg is None or agg < 0:
            raise ValueError("agg (aggressiveness) must be >= 0")
        
        initial_capital = config.get('initial_capital', 1.0)
        
        # Setup
        n_assets = len(prices_df.columns)
        n_periods = len(prices_df)
        
        # Initialize weights
        current_weights = uniform_weights(n_assets)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Track weights over time
        weights_over_time = np.zeros((n_periods, n_assets))
        weights_over_time[0] = current_weights
        turnover_values = np.zeros(n_periods)
        
        # Run PAMR updates
        for t in range(1, n_periods):
            # Get current price relatives
            x_t = price_relatives[t-1]
            
            # Calculate portfolio return
            portfolio_return = np.dot(current_weights, x_t)
            
            # Calculate loss
            loss = max(0, portfolio_return - epsilon)
            
            # Calculate adjusted market change
            x_bar = x_t - np.mean(x_t) * np.ones(n_assets)
            
            # Calculate norm
            norm_sq = np.linalg.norm(x_bar) ** 2
            
            # Calculate tau based on optimization method
            if norm_sq == 0:
                tau = 0
            elif optimization_method == 0:
                # PAMR
                tau = loss / norm_sq
            elif optimization_method == 1:
                # PAMR-1
                tau = min(agg, loss / norm_sq)
            else:
                # PAMR-2
                tau = loss / (norm_sq + 1 / (2 * agg))
            
            # Update weights
            new_weights = current_weights - tau * x_bar
            
            # Project to simplex
            new_weights = simplex_projection(new_weights)
            new_weights = normalize_weights(new_weights)
            
            # Calculate turnover
            turnover_values[t] = calculate_turnover(
                current_weights,
                new_weights,
                x_t
            )
            
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
        
        # Method names
        method_names = {0: 'PAMR', 1: 'PAMR-1', 2: 'PAMR-2'}
        method_name = method_names[optimization_method]
        
        # Metadata
        metadata = {
            'strategy_type': 'mean_reversion',
            'n_assets': n_assets,
            'optimization_method': method_name,
            'epsilon': epsilon,
            'agg': agg,
            'description': f'{method_name} with epsilon={epsilon}, C={agg}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )


class CWMR(OlpsStrategy):
    """
    Confidence Weighted Mean Reversion (CWMR) Strategy.
    
    Models portfolio weights as a Gaussian distribution with mean and variance.
    Uses confidence-weighted online learning for mean reversion.
    
    **Classification**: CAUSAL
    **Implementability**: Yes - But computationally expensive
    **Complexity**: VERY_HIGH
    
    Algorithm:
    1. Maintain distribution: weights ~ N(μ, Σ)
    2. Calculate portfolio return and variance
    3. Compute Lagrangian multiplier λ
    4. Update μ: μ ← μ - λ * Σ * (x_t - mean_x)
    5. Update Σ using variance update method (var or sd)
    6. Project μ to simplex
    
    Paper Reference:
        Li, B., Hoi, S.C., Zhao, P. & Gopalkrishnan, V., 2011.
        Confidence Weighted Mean Reversion Strategy for On-Line Portfolio Selection.
        AISTATS 2011.
        https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=3292&context=sis_research
    """
    
    def __init__(self):
        super().__init__(
            id="CWMR",
            name="Confidence Weighted Mean Reversion",
            paper_ref="Li et al. 2011 - CWMR",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL,
            complexity=StrategyComplexity.VERY_HIGH,
            description="Models weights as Gaussian distribution. Uses confidence-weighted learning for mean reversion. "
                        "Computationally expensive due to matrix operations. Extremely sensitive to parameters.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute CWMR strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - confidence: Confidence parameter [0, 1] (extreme values 0 or 1 work best)
                - epsilon: Mean reversion threshold [0, 1]
                - method: 'var' for variance or 'sd' for standard deviation update
        
        Returns:
            StrategyResult with Gaussian-distributed weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        confidence = config.get('confidence', 0.95)
        epsilon = config.get('epsilon', 0.5)
        method = config.get('method', 'var')
        
        # Validate parameters
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
        if not 0 <= epsilon <= 1:
            raise ValueError("epsilon must be in [0, 1]")
        if method not in ['var', 'sd']:
            raise ValueError("method must be 'var' or 'sd'")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        
        # Calculate theta from confidence
        theta = norm.ppf(confidence)
        
        # Initialize distribution parameters
        mu = uniform_weights(n_assets)  # Mean of distribution
        sigma = np.identity(n_assets) / (n_assets ** 2)  # Variance matrix
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # First weight
        weights_matrix.iloc[0] = mu
        current_weights = mu.copy()
        
        # Iterate through time
        for t in range(1, n_periods):
            # Previous price relative
            x_t = price_relatives[t-1]  # Shape: (n_assets,)
            
            # Calculate portfolio statistics
            m_t = np.dot(x_t, current_weights)  # Portfolio return
            v_t = np.dot(np.dot(x_t, sigma), x_t.T)  # Return variance
            w_t = np.dot(x_t, sigma)  # Weighted variance
            
            # Calculate weighted average (reversion target)
            mean_x = np.diag(sigma) / np.trace(sigma)
            
            # Calculate lambda (Lagrangian multiplier)
            lambd = self._calculate_lambda(m_t, v_t, w_t, mean_x, epsilon, theta)
            
            # Update mu
            mu = mu - lambd * np.dot(sigma, (x_t - mean_x))
            
            # Update sigma (variance matrix)
            if method == 'sd':
                # Standard deviation update
                sqrt_u = (-lambd * theta * v_t + np.sqrt(lambd**2 * theta**2 * v_t**2 + 4*v_t)) / 2
                sigma_inv = np.linalg.pinv(sigma)
                sigma_inv_update = sigma_inv + lambd * theta / sqrt_u * np.outer(x_t, x_t)
                sigma = np.linalg.pinv(sigma_inv_update)
            else:  # method == 'var'
                # Variance update
                sigma_inv = np.linalg.pinv(sigma)
                sigma_inv_update = sigma_inv + 2 * lambd * theta * np.outer(x_t, x_t)
                sigma = np.linalg.pinv(sigma_inv_update)
            
            # Ensure positive semi-definite
            sigma = np.maximum(sigma, 1e-5 * np.identity(n_assets))
            
            # Normalize sigma
            sigma = sigma / (m_t * np.trace(sigma))
            
            # Project mu to simplex
            mu = simplex_projection(mu)
            
            # Store weights
            weights_matrix.iloc[t] = mu
            
            # Calculate turnover
            turnover_values[t] = calculate_turnover(current_weights, mu)
            current_weights = mu.copy()
        
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
            'strategy_type': 'mean_reversion',
            'n_assets': n_assets,
            'confidence': confidence,
            'epsilon': epsilon,
            'method': method,
            'theta': theta,
            'description': f'CWMR with confidence={confidence}, epsilon={epsilon}, method={method}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    @staticmethod
    def _calculate_lambda(m, v, w, mean_x, epsilon, theta):
        """
        Calculate Lagrangian multiplier for CWMR update.
        
        Args:
            m: Portfolio return
            v: Return variance
            w: Weighted variance
            mean_x: Weighted average (reversion target)
            epsilon: Mean reversion parameter
            theta: Confidence parameter (from norm.ppf)
        
        Returns:
            Lambda (Lagrangian multiplier)
        """
        # Expression for quadratic equation
        expr = v - np.dot(mean_x, w) + theta**2 * v / 2
        
        # Quadratic coefficients: a*λ² + b*λ + c = 0
        a = expr**2 - theta**4 * v**2 / 4
        b = 2 * (epsilon - m) * expr
        c = (epsilon - m)**2 - theta**2 * v
        
        # Solve quadratic equation
        discriminant = b**2 - 4*a*c
        
        if discriminant < 0:
            # No real solution, use linear approximation
            lambd = max(-c / b, 0) if b != 0 else 0
        else:
            # Two solutions, take the maximum positive one
            sqrt_disc = np.sqrt(discriminant)
            sol1 = (-b + sqrt_disc) / (2*a) if a != 0 else 0
            sol2 = (-b - sqrt_disc) / (2*a) if a != 0 else 0
            sol3 = -c / b if b != 0 else 0
            lambd = max(sol1, sol2, sol3, 0)
        
        # Bound lambda for numerical stability
        lambd = min(lambd, 10000)
        
        return lambd


class RMR(OlpsStrategy):
    """
    Robust Median Reversion (RMR) Strategy.
    
    Uses L1-median of historical prices for robust mean reversion prediction.
    More robust to outliers than L2-norm methods like OLMAR or PAMR.
    
    **Classification**: CAUSAL_LAGGING
    **Implementability**: Yes - But requires windowed data
    **Complexity**: HIGH
    
    Algorithm:
    1. Calculate L1-median of price window using Modified Weiszfeld Algorithm
    2. Predict price relatives: x̂_t = L1_median / current_price
    3. Calculate deviation: δ = x̂_t - mean(x̂_t)
    4. Compute alpha: α = min(0, (x̂_t·w - ε) / ||δ||₁²)
    5. Update: w_{t+1} = w_t - α * δ
    6. Project to simplex
    
    Paper Reference:
        Huang, D., Zhou, J., Li, B., Hoi, S.C.H., Zhou, S., 2016.
        Robust Median Reversion Strategy for Online Portfolio Selection.
        IEEE TKDE, vol. 28, no. 9, pp. 2480-2493.
        https://www.ijcai.org/Proceedings/13/Papers/296.pdf
    """
    
    def __init__(self):
        super().__init__(
            id="RMR",
            name="Robust Median Reversion",
            paper_ref="Huang et al. 2016 - RMR",
            library_ref=None,
            strategy_type=StrategyType.CAUSAL_LAGGING,
            complexity=StrategyComplexity.HIGH,
            description="Uses L1-median for robust mean reversion. More resistant to outliers than OLMAR/PAMR. "
                        "Requires window of historical data. Iterative algorithm for median calculation.",
            implementable=True
        )
    
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute RMR strategy.
        
        Args:
            prices_df: DataFrame of asset prices (date x assets)
            config: Configuration dict with:
                - initial_capital: Starting capital
                - epsilon: Reversion threshold [1, inf), typically 15-25
                - window: Size of window [2, inf), typically 2, 7, or 21
                - n_iteration: Max iterations for L1-median [2, inf), typically 200
                - tau: Tolerance level [0, 1), default 0.001
        
        Returns:
            StrategyResult with robustly reversion-based weights
        """
        # Extract configuration
        initial_capital = config.get('initial_capital', 1.0)
        epsilon = config.get('epsilon', 20.0)
        window = config.get('window', 7)
        n_iteration = config.get('n_iteration', 200)
        tau = config.get('tau', 0.001)
        
        # Validate parameters
        if epsilon < 1:
            raise ValueError("epsilon must be >= 1")
        if not isinstance(window, int) or window < 2:
            raise ValueError("window must be integer >= 2")
        if not isinstance(n_iteration, int) or n_iteration < 2:
            raise ValueError("n_iteration must be integer >= 2")
        if not 0 <= tau < 1:
            raise ValueError("tau must be in [0, 1)")
        
        # Setup
        n_periods, n_assets = prices_df.shape
        prices_array = prices_df.values
        
        # Storage
        weights_matrix = pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)
        turnover_values = np.zeros(n_periods)
        
        # Calculate price relatives
        price_relatives = calculate_relative_returns(prices_df)
        
        # Initialize with uniform weights
        current_weights = uniform_weights(n_assets)
        weights_matrix.iloc[0] = current_weights
        
        # Iterate through time
        for t in range(1, n_periods):
            # Until we have enough history, use uniform weights
            if t < window:
                weights_matrix.iloc[t] = current_weights
                continue
            
            # Get price window
            price_window = prices_array[t - window + 1:t + 1]  # Shape: (window, n_assets)
            
            # Calculate L1-median prediction
            predicted_relatives = self._calculate_l1_median_prediction(
                price_window, n_iteration, tau
            )
            
            # Calculate deviation from mean
            mean_pred = np.mean(predicted_relatives)
            deviation = predicted_relatives - mean_pred
            
            # Calculate L1 norm squared
            norm_l1_sq = np.sum(np.abs(deviation)) ** 2
            
            # Skip if zero norm
            if norm_l1_sq == 0:
                weights_matrix.iloc[t] = current_weights
                continue
            
            # Calculate portfolio return with prediction
            pred_return = np.dot(predicted_relatives, current_weights)
            
            # Calculate alpha (Lagrangian multiplier)
            alpha = min(0, (pred_return - epsilon) / norm_l1_sq)
            
            # Update weights
            new_weights = current_weights - alpha * deviation
            
            # Project to simplex
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
            'strategy_type': 'mean_reversion',
            'n_assets': n_assets,
            'epsilon': epsilon,
            'window': window,
            'n_iteration': n_iteration,
            'tau': tau,
            'description': f'RMR with epsilon={epsilon}, window={window}, iterations={n_iteration}'
        }
        
        return StrategyResult(
            weights=weights_matrix,
            gross_portfolio_values=portfolio_values,
            net_portfolio_values=portfolio_values.copy(),
            turnover=turnover_series,
            metadata=metadata
        )
    
    @staticmethod
    def _calculate_l1_median_prediction(price_window, n_iteration, tau):
        """
        Calculate L1-median of price window using Modified Weiszfeld Algorithm.
        
        Args:
            price_window: Array of shape (window, n_assets) with historical prices
            n_iteration: Maximum number of iterations
            tau: Tolerance level for convergence
        
        Returns:
            Predicted price relatives (L1-median / current_price)
        """
        # Start with componentwise median as initial guess
        current_pred = np.median(price_window, axis=0)
        
        # Iteratively refine using Modified Weiszfeld Algorithm
        for _ in range(n_iteration - 1):
            prev_pred = current_pred.copy()
            
            # Calculate distances from current prediction to each price point
            diffs = price_window - current_pred  # Shape: (window, n_assets)
            distances = np.linalg.norm(diffs, axis=1, ord=2)  # Shape: (window,)
            
            # Avoid division by zero
            distances = np.maximum(distances, 1e-10)
            
            # Weighted average (Weiszfeld update)
            weights = 1.0 / distances
            weighted_sum = np.sum(price_window * weights[:, np.newaxis], axis=0)
            weight_sum = np.sum(weights)
            
            current_pred = weighted_sum / weight_sum if weight_sum > 0 else prev_pred
            
            # Check convergence
            change = np.linalg.norm(prev_pred - current_pred, ord=1)
            if change <= tau * np.linalg.norm(current_pred, ord=1):
                break
        
        # Convert to price relatives (prediction / current_price)
        current_price = price_window[-1]
        predicted_relatives = current_pred / current_price
        
        return predicted_relatives

