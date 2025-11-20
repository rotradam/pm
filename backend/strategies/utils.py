"""
Utility functions for OLPS strategies.

Common helper functions used across all strategy implementations.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd


def calculate_returns(prices: pd.DataFrame, method: str = 'simple') -> pd.DataFrame:
    """
    Calculate returns from price series.
    
    Args:
        prices: DataFrame with dates as index and assets as columns
        method: 'simple' for (p_t - p_{t-1})/p_{t-1}, 'log' for log(p_t/p_{t-1})
    
    Returns:
        DataFrame of returns with same structure as prices (first row will be NaN)
    """
    if method == 'simple':
        returns = prices.pct_change()
    elif method == 'log':
        returns = np.log(prices / prices.shift(1))
    else:
        raise ValueError(f"Unknown method: {method}. Use 'simple' or 'log'")
    
    return returns


def calculate_relative_returns(prices: pd.DataFrame) -> np.ndarray:
    """
    Calculate relative returns (price relatives) for OLPS strategies.
    
    Price relative: x_t = p_t / p_{t-1} (ratio of consecutive prices)
    
    Args:
        prices: DataFrame with dates as index and assets as columns
    
    Returns:
        numpy array of shape (T-1, N) where T is time periods and N is assets
        Each row represents the price relatives for all assets at time t
    """
    # Calculate price relatives (avoid first row which would be inf)
    price_relatives = (prices / prices.shift(1)).dropna()
    return price_relatives.values


def normalize_weights(weights: np.ndarray, threshold: float = 1e-6) -> np.ndarray:
    """
    Normalize weights to sum to 1 and remove negligible values.
    
    Args:
        weights: Array of portfolio weights
        threshold: Values below this threshold are set to zero
    
    Returns:
        Normalized weight vector that sums to 1
    """
    # Set very small weights to zero
    weights = np.where(np.abs(weights) < threshold, 0, weights)
    
    # Ensure no negative weights (for long-only portfolios)
    weights = np.maximum(weights, 0)
    
    # Normalize to sum to 1
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        weights = weights / weight_sum
    else:
        # If all weights are zero, return uniform weights
        weights = np.ones(len(weights)) / len(weights)
    
    return weights


def uniform_weights(n_assets: int) -> np.ndarray:
    """
    Generate uniform (equal) weights for all assets.
    
    Args:
        n_assets: Number of assets
    
    Returns:
        Array of equal weights summing to 1
    """
    return np.ones(n_assets) / n_assets


def calculate_turnover(
    weights_old: np.ndarray,
    weights_new: np.ndarray,
    price_relatives: Optional[np.ndarray] = None
) -> float:
    """
    Calculate portfolio turnover between two weight vectors.
    
    Turnover represents the total amount of trading required to rebalance.
    
    Args:
        weights_old: Previous period's weights
        weights_new: Current period's target weights
        price_relatives: Optional price relatives to adjust weights_old for price changes
                        If provided, weights_old will be adjusted before comparison
    
    Returns:
        Turnover value (typically between 0 and 2)
        0 = no rebalancing, 2 = complete portfolio flip
    """
    # If price relatives provided, adjust old weights for price changes
    if price_relatives is not None:
        weights_after_price_change = weights_old * price_relatives
        weights_after_price_change = normalize_weights(weights_after_price_change)
    else:
        weights_after_price_change = weights_old
    
    # Turnover is sum of absolute differences
    turnover = np.sum(np.abs(weights_new - weights_after_price_change))
    
    return turnover


def calculate_portfolio_value(
    initial_value: float,
    weights: np.ndarray,
    returns: np.ndarray,
    rebalance: bool = True
) -> Tuple[float, np.ndarray]:
    """
    Calculate portfolio value after one period given weights and returns.
    
    Args:
        initial_value: Portfolio value at start of period
        weights: Portfolio weights (should sum to 1)
        returns: Asset returns for the period (simple returns, not log returns)
        rebalance: If True, rebalance to target weights; if False, let weights drift
    
    Returns:
        Tuple of (new_portfolio_value, new_weights)
    """
    # Portfolio return is weighted sum of asset returns
    portfolio_return = np.dot(weights, returns)
    new_value = initial_value * (1 + portfolio_return)
    
    if rebalance:
        # Weights reset to target weights
        new_weights = weights.copy()
    else:
        # Weights drift with asset performance
        new_weights = weights * (1 + returns)
        new_weights = normalize_weights(new_weights)
    
    return new_value, new_weights


def calculate_cumulative_returns(
    weights_matrix: pd.DataFrame,
    price_relatives: np.ndarray,
    initial_capital: float = 1.0
) -> pd.Series:
    """
    Calculate cumulative portfolio returns over time.
    
    Args:
        weights_matrix: DataFrame of weights (T x N) indexed by date
        price_relatives: Array of price relatives (T-1 x N), one less row than weights
        initial_capital: Starting portfolio value
    
    Returns:
        Series of cumulative portfolio values indexed by date
    """
    n_periods = len(weights_matrix)
    portfolio_values = np.zeros(n_periods)
    portfolio_values[0] = initial_capital
    
    # Note: price_relatives has T-1 rows (no relative for first period)
    # So we calculate returns starting from period 1
    for t in range(1, n_periods):
        weights = weights_matrix.iloc[t-1].values  # Use previous period's weights
        price_rel = price_relatives[t-1]  # Price relative from t-1 to t
        
        # Portfolio growth factor is weighted sum of price relatives
        portfolio_growth = np.dot(weights, price_rel)
        portfolio_values[t] = portfolio_values[t-1] * portfolio_growth
    
    # Create series with same index as weights_matrix
    result = pd.Series(
        portfolio_values,
        index=weights_matrix.index,
        name='portfolio_value'
    )
    
    return result


def simple_moving_average(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Calculate simple moving average of prices.
    
    Args:
        prices: DataFrame of asset prices
        window: Window size for moving average
    
    Returns:
        DataFrame of moving averages (first window-1 rows will be NaN)
    """
    return prices.rolling(window=window).mean()


def exponentially_weighted_average(
    prices: pd.DataFrame,
    alpha: float
) -> pd.DataFrame:
    """
    Calculate exponentially weighted moving average.
    
    Args:
        prices: DataFrame of asset prices
        alpha: Smoothing parameter (0 < alpha <= 1)
               Higher alpha = more weight on recent prices
    
    Returns:
        DataFrame of exponentially weighted averages
    """
    # Use pandas ewm with span parameter
    # span = 2/alpha - 1, so alpha = 2/(span + 1)
    span = (2 / alpha) - 1
    return prices.ewm(span=span, adjust=False).mean()


def check_valid_weights(weights: np.ndarray, tolerance: float = 1e-5) -> bool:
    """
    Validate that weights form a valid portfolio.
    
    Args:
        weights: Array of portfolio weights
        tolerance: Tolerance for sum check
    
    Returns:
        True if weights are valid (non-negative, sum to ~1)
    
    Raises:
        ValueError if weights are invalid
    """
    # Check for negative weights (long-only constraint)
    if np.any(weights < -tolerance):
        raise ValueError(f"Negative weights detected: {weights[weights < -tolerance]}")
    
    # Check that weights sum to approximately 1
    weight_sum = np.sum(weights)
    if abs(weight_sum - 1.0) > tolerance:
        raise ValueError(f"Weights sum to {weight_sum:.6f}, expected 1.0")
    
    return True


def simplex_projection(weights: np.ndarray) -> np.ndarray:
    """
    Project weights onto the probability simplex (non-negative, sum to 1).
    
    Uses efficient algorithm for simplex projection.
    
    Args:
        weights: Array of weights (may be negative or not sum to 1)
    
    Returns:
        Projected weights on the simplex
    """
    n = len(weights)
    
    # Sort weights in descending order
    sorted_weights = np.sort(weights)[::-1]
    
    # Find the projection
    cumsum = np.cumsum(sorted_weights)
    rho = np.where((sorted_weights * np.arange(1, n + 1) > (cumsum - 1)))[0]
    
    if len(rho) == 0:
        theta = (cumsum[-1] - 1) / n
    else:
        rho_max = rho[-1]
        theta = (cumsum[rho_max] - 1) / (rho_max + 1)
    
    # Project
    projected = np.maximum(weights - theta, 0)
    
    return projected
