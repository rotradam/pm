# Boosting Exponential Gradient Strategy for Online Portfolio Selection (WAEG) - Implementation Guide

## 📋 Executive Summary

This document provides a comprehensive implementation guide for the **Weak Aggregating Exponential Gradient (WAEG)** strategy from the research paper "Boosting Exponential Gradient Strategy for Online Portfolio Selection." The strategy combines multiple Exponential Gradient (EG) experts with different learning rates using the Weak Aggregating Algorithm (WAA) to create a robust online portfolio selection system.

## 🎯 Core Problem Definition

### Online Portfolio Selection Framework
- **Input**: Sequence of price relative vectors `x_1, x_2, ..., x_n` where each `x_t = (x_{t,1}, ..., x_{t,m})` represents asset price ratios (closing/opening prices)
- **Output**: Final cumulative wealth `S_n` after `n` trading periods
- **Constraint**: Portfolio vectors must satisfy `b_t ∈ Δ_m` (simplex: non-negative, sum to 1)

### Key Mathematical Formulation
For a portfolio strategy `b_1, b_2, ..., b_n`:
```
S_n = S_0 × ∏_{t=1}^n (b_t · x_t) = S_0 × ∏_{t=1}^n (∑_{i=1}^m b_{t,i} × x_{t,i})
```

## 🧠 Algorithm Deep Dive

### Weak Aggregating Algorithm (WAA) Foundation

WAA combines multiple experts by:
1. Maintaining weights based on cumulative performance
2. Using exponential weighting with adaptive learning rate
3. Aggregating expert predictions weighted by performance

**Key Equation**:
```
p_t(θ) = β_t^{G_{t-1}(θ)} × q(θ) / ∫_Θ β_t^{G_{t-1}(θ)} q(dθ)
```
where `β_t = e^{1/√t}` is the learning rate.

### Exponential Gradient (EG) Experts

Each EG expert with parameter `η` updates its portfolio using:
```
b_{t+1,i}(η) = [b_{t,i}(η) × exp(η × x_{t,i} / (b_t(η) · x_t))] / [∑_{j=1}^m b_{t,j}(η) × exp(η × x_{t,j} / (b_t(η) · x_t))]
```

This formulation maximizes logarithmic return while minimizing distance from previous portfolio using relative entropy.

## 🚀 WAEG Strategy Implementation

### Algorithm 3: WAEG Strategy

```python
import numpy as np
from typing import List, Tuple

class WAEGStrategy:
    def __init__(self, m: int, k: int = 20, eta_min: float = 0.01, 
                 eta_max: float = 0.2, alpha: float = None):
        """
        Initialize WAEG strategy
        
        Args:
            m: Number of assets
            k: Number of EG experts
            eta_min: Minimum learning rate for EG experts
            eta_max: Maximum learning rate for EG experts  
            alpha: Smoothing parameter (if None, use basic WAEG)
        """
        self.m = m
        self.k = k
        self.eta_min = eta_min
        self.eta_max = eta_max
        self.alpha = alpha
        
        # Generate expert parameters
        self.eta_list = np.linspace(eta_min, eta_max, k)
        
        # Initialize state
        self.reset()
    
    def reset(self):
        """Reset strategy to initial state"""
        # Initial uniform portfolio
        self.b_current = np.ones(self.m) / self.m
        self.S = 1.0  # Cumulative wealth
        
        # Expert states
        self.experts_b = [np.ones(self.m) / self.m for _ in range(self.k)]
        self.experts_G = np.zeros(self.k)  # Cumulative returns
        self.experts_weights = np.ones(self.k) / self.k
    
    def _normalize_price_relatives(self, x: np.ndarray) -> np.ndarray:
        """Normalize price relatives as per paper assumption"""
        if self.alpha is not None:
            # Use smoothing for WAEG~
            return (1 - self.alpha/self.m) * x + (self.alpha/self.m) * np.ones(self.m)
        else:
            # Basic normalization: ensure max is 1
            return x / np.max(x) if np.max(x) > 0 else x
    
    def _update_eg_expert(self, expert_idx: int, x_t: np.ndarray) -> np.ndarray:
        """Update a single EG expert's portfolio"""
        eta = self.eta_list[expert_idx]
        b_current = self.experts_b[expert_idx]
        
        # Calculate denominator: b_t(η) · x_t
        denom = np.dot(b_current, x_t)
        if denom <= 0:  # Handle numerical issues
            return b_current
        
        # EG update
        numerator = b_current * np.exp(eta * x_t / denom)
        b_new = numerator / np.sum(numerator)
        
        # Apply smoothing if using WAEG~
        if self.alpha is not None:
            b_new = (1 - self.alpha) * b_new + (self.alpha / self.m) * np.ones(self.m)
        
        return b_new
    
    def update(self, x_t: np.ndarray) -> float:
        """
        Update strategy with new price relative vector
        
        Args:
            x_t: Price relative vector for current period
            
        Returns:
            Current cumulative wealth
        """
        # Normalize price relatives
        x_normalized = self._normalize_price_relatives(x_t)
        
        # Update cumulative wealth
        portfolio_return = np.dot(self.b_current, x_normalized)
        self.S *= portfolio_return
        
        # Update expert cumulative returns
        for j in range(self.k):
            expert_return = np.dot(self.experts_b[j], x_normalized)
            if expert_return > 0:
                self.experts_G[j] += np.log(expert_return)
        
        # Calculate new expert weights (for next period)
        t_adjusted = len(self.experts_G) + 2  # Time adjustment for stability
        beta = np.exp(1 / np.sqrt(t_adjusted))
        
        weights_numerator = beta ** self.experts_G
        total_weight = np.sum(weights_numerator)
        if total_weight > 0:
            self.experts_weights = weights_numerator / total_weight
        else:
            self.experts_weights = np.ones(self.k) / self.k
        
        # Update expert portfolios for next period
        new_expert_portfolios = []
        for j in range(self.k):
            new_portfolio = self._update_eg_expert(j, x_normalized)
            new_expert_portfolios.append(new_portfolio)
        
        # Aggregate expert advice for next portfolio
        next_portfolio = np.zeros(self.m)
        for j in range(self.k):
            next_portfolio += self.experts_weights[j] * new_expert_portfolios[j]
        
        # Ensure portfolio is valid (sums to 1, non-negative)
        next_portfolio = np.maximum(next_portfolio, 0)
        next_portfolio /= np.sum(next_portfolio)
        
        # Update state
        self.experts_b = new_expert_portfolios
        self.b_current = next_portfolio
        
        return self.S
    
    def run_online(self, price_relatives: List[np.ndarray]) -> Tuple[float, List[float]]:
        """
        Run WAEG strategy on sequence of price relatives
        
        Args:
            price_relatives: List of price relative vectors
            
        Returns:
            Final wealth and wealth history
        """
        self.reset()
        wealth_history = [self.S]
        
        for x_t in price_relatives:
            current_wealth = self.update(x_t)
            wealth_history.append(current_wealth)
        
        return self.S, wealth_history
```

## 🔧 Implementation Details & Best Practices

### 1. **Numerical Stability**
```python
# Critical: Handle numerical edge cases
def _safe_division(self, numerator: np.ndarray, denominator: float) -> np.ndarray:
    """Safe division with overflow protection"""
    if denominator < 1e-10:
        return numerator / (denominator + 1e-10)
    return numerator / denominator
```

### 2. **Parameter Selection Strategy**
```python
def suggest_parameters(self, market_volatility: float) -> dict:
    """
    Suggest parameters based on market characteristics
    
    Args:
        market_volatility: Estimated market volatility
        
    Returns:
        Dictionary of suggested parameters
    """
    if market_volatility > 0.15:  # High volatility
        return {'k': 30, 'eta_min': 0.005, 'eta_max': 0.1}
    else:  # Low volatility
        return {'k': 20, 'eta_min': 0.01, 'eta_max': 0.2}
```

### 3. **Data Preprocessing**
```python
def preprocess_data(price_data: np.ndarray) -> List[np.ndarray]:
    """
    Convert raw price data to price relatives
    
    Args:
        price_data: Array of shape (n_periods, n_assets) with raw prices
        
    Returns:
        List of price relative vectors
    """
    price_relatives = []
    for t in range(1, len(price_data)):
        x_t = price_data[t] / price_data[t-1]  # Simple price relatives
        price_relatives.append(x_t)
    return price_relatives
```

## 📊 Performance Monitoring

### Key Metrics to Track
```python
class PerformanceMetrics:
    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        excess_returns = np.array(returns) - risk_free_rate
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0
    
    @staticmethod
    def max_drawdown(wealth_history: List[float]) -> float:
        peak = wealth_history[0]
        max_dd = 0.0
        for wealth in wealth_history:
            if wealth > peak:
                peak = wealth
            dd = (peak - wealth) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
    
    @staticmethod
    def volatility(returns: List[float]) -> float:
        return np.std(returns)
```

## 🧪 Testing Framework

### Unit Tests
```python
import unittest

class TestWAEGStrategy(unittest.TestCase):
    def setUp(self):
        self.m = 3
        self.strategy = WAEGStrategy(m=self.m, k=5)
    
    def test_initialization(self):
        self.assertEqual(len(self.strategy.b_current), self.m)
        self.assertTrue(np.allclose(np.sum(self.strategy.b_current), 1.0))
    
    def test_portfolio_update(self):
        x_t = np.array([1.02, 0.98, 1.05])  # Sample price relatives
        wealth = self.strategy.update(x_t)
        self.assertGreater(wealth, 0)
        self.assertTrue(np.allclose(np.sum(self.strategy.b_current), 1.0))
```

## 🚨 Critical Implementation Notes

### 1. **Numerical Precision**
- Use `np.float64` for all calculations
- Implement safeguards against division by zero
- Handle extreme market movements gracefully

### 2. **Memory Management**
- For long time series, consider incremental updates
- Store only necessary historical information
- Use generators for large datasets

### 3. **Reproducibility**
- Set random seeds for expert parameter generation
- Log all parameter choices
- Version control for strategy variants

## 🔮 Extensions & Future Work

### 1. **Transaction Cost Integration**
```python
def update_with_costs(self, x_t: np.ndarray, cost_rate: float = 0.001) -> float:
    """Update strategy considering transaction costs"""
    old_portfolio = self.b_current.copy()
    wealth_before = self.S
    
    # Regular update
    wealth_after = self.update(x_t)
    
    # Calculate turnover and apply costs
    turnover = np.sum(np.abs(self.b_current - old_portfolio))
    cost = turnover * cost_rate
    self.S *= (1 - cost)
    
    return self.S
```

### 2. **Dynamic Expert Pool**
- Adapt number of experts based on market regime
- Prune poorly performing experts
- Add new experts with different parameter ranges

## 📈 Expected Performance Characteristics

Based on the paper's results:
- **Competitive Performance**: Should approach BCRP performance asymptotically
- **Market Adaptability**: Works well in both US and Chinese markets
- **Robustness**: Less sensitive to exact parameter choices compared to single EG strategy
- **Computational Efficiency**: Linear in number of experts and assets

This implementation provides a solid foundation for the WAEG strategy that can be further optimized and extended based on specific requirements and market conditions.