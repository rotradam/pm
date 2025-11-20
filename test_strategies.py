#!/usr/bin/env python3
"""
Test script for newly implemented OLPS strategies - Batch 2
Tests: CORN, CORNK, CORNU, BCRP, BestStock, FTL, FTRL

Usage:
    python test_new_strategies_batch2.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.strategies import (
    CORN, CORNK, CORNU,
    BCRP, BestStock, FTL, FTRL
)


def load_test_data():
    """Load a small subset of price data for testing."""
    try:
        prices = pd.read_parquet('data/processed/prices_2015-01-01_2025-11-16.parquet')
        
        # Use 2020-2021 data with 5 assets for quick testing
        test_prices = prices.loc['2020-01-01':'2021-12-31'].iloc[:, :5].dropna(how='any')
        
        print(f"Test data shape: {test_prices.shape}")
        print(f"Date range: {test_prices.index[0]} to {test_prices.index[-1]}")
        print(f"Assets: {list(test_prices.columns)}\n")
        
        return test_prices
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def test_strategy(strategy_class, strategy_name, prices, config):
    """Test a single strategy."""
    print(f"\n{'='*60}")
    print(f"Testing: {strategy_name}")
    print(f"{'='*60}")
    
    try:
        strategy = strategy_class()
        print(f"✓ Strategy instantiated")
        print(f"  Type: {strategy.strategy_type.name}")
        print(f"  Implementable: {strategy.implementable}")
        print(f"  Paper: {strategy.paper_ref or 'N/A'}")
        
        result = strategy.run(prices, config)
        print(f"✓ Strategy executed successfully")
        
        # Basic validation
        assert result.weights.shape[0] == len(prices), "Weights shape mismatch"
        assert result.weights.shape[1] == len(prices.columns), "Weights columns mismatch"
        assert len(result.gross_portfolio_values) == len(prices), "Portfolio values length mismatch"
        assert len(result.turnover) == len(prices), "Turnover length mismatch"
        print(f"✓ Output validation passed")
        
        # Performance metrics
        final_value = result.gross_portfolio_values.iloc[-1]
        initial_value = config['initial_capital']
        total_return = (final_value / initial_value - 1) * 100
        
        print(f"\nPerformance:")
        print(f"  Initial Capital: ${initial_value:,.2f}")
        print(f"  Final Value: ${final_value:,.2f}")
        print(f"  Total Return: {total_return:.2f}%")
        print(f"  Avg Daily Turnover: {result.turnover.mean():.4f}")
        print(f"  Max Daily Turnover: {result.turnover.max():.4f}")
        
        # Check for NaN or inf
        if result.weights.isna().any().any():
            print("  ⚠️ WARNING: NaN values in weights")
        if result.gross_portfolio_values.isna().any():
            print("  ⚠️ WARNING: NaN values in portfolio values")
        if np.isinf(result.weights.values).any():
            print("  ⚠️ WARNING: Inf values in weights")
            
        # Weight constraints
        weight_sums = result.weights.sum(axis=1)
        if not np.allclose(weight_sums, 1.0, atol=1e-4):
            print(f"  ⚠️ WARNING: Weights don't sum to 1.0 (range: {weight_sums.min():.4f} - {weight_sums.max():.4f})")
        else:
            print(f"  ✓ Weights sum to 1.0")
            
        if (result.weights < -1e-6).any().any():
            print(f"  ⚠️ WARNING: Negative weights detected (min: {result.weights.min().min():.6f})")
        else:
            print(f"  ✓ No negative weights")
        
        return True
        
    except Exception as e:
        print(f"✗ Strategy failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("OLPS Strategy Test Suite - Batch 2")
    print("Testing: Correlation-Driven & Follow-The-Leader Strategies")
    print("="*60)
    
    # Load test data
    prices = load_test_data()
    if prices is None:
        print("Failed to load test data. Exiting.")
        return
    
    # Test configuration
    initial_capital = 10000
    
    # Correlation-Driven Strategies
    strategies = [
        (CORN, "CORN - Correlation-Driven", {
            'initial_capital': initial_capital,
            'window': 5,
            'rho': 0.1
        }),
        (CORNK, "CORNK - Top-K Ensemble", {
            'initial_capital': initial_capital,
            'window': 5,
            'rho': 3,
            'k': 2
        }),
        (CORNU, "CORNU - Uniform Ensemble", {
            'initial_capital': initial_capital,
            'window': 5,
            'rho': 0.1
        }),
    ]
    
    # Follow-The-Leader Strategies
    ftl_strategies = [
        (BCRP, "BCRP - Best Constant Rebalanced Portfolio", {
            'initial_capital': initial_capital
        }),
        (BestStock, "BestStock - Best Single Asset", {
            'initial_capital': initial_capital
        }),
        (FTL, "FTL - Follow The Leader", {
            'initial_capital': initial_capital
        }),
        (FTRL, "FTRL - Follow The Regularized Leader", {
            'initial_capital': initial_capital,
            'lam': 0.1
        }),
    ]
    
    strategies.extend(ftl_strategies)
    
    # Run tests
    results = []
    for strategy_class, name, config in strategies:
        success = test_strategy(strategy_class, name, prices, config)
        results.append((name, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
