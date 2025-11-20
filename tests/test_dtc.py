#!/usr/bin/env python3
"""
Test script for DTC strategy implementation.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.strategies import DTC

def load_test_data():
    """Load a small subset of price data for testing."""
    try:
        # Try to load processed data first
        prices_path = Path('data/processed/prices_2015-01-01_2025-11-16.parquet')
        if prices_path.exists():
            prices = pd.read_parquet(prices_path)
            # Use 2020-2021 data with 5 assets for quick testing
            test_prices = prices.loc['2020-01-01':'2021-12-31'].iloc[:, :5].dropna(how='any')
            return test_prices
        else:
            # Create synthetic data if file doesn't exist
            dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
            data = np.random.randn(100, 5).cumsum(axis=0) + 100
            return pd.DataFrame(data, index=dates, columns=['A', 'B', 'C', 'D', 'E'])
            
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def test_dtc():
    print(f"\n{'='*60}")
    print(f"Testing: Decentralized Online Portfolio Selection (DTC)")
    print(f"{'='*60}")
    
    prices = load_test_data()
    if prices is None:
        print("Failed to load test data.")
        return
        
    print(f"Test data shape: {prices.shape}")
    
    # Test DTC1
    print("\nTesting DTC1 Variant...")
    dtc1 = DTC()
    config1 = {
        'variant': 'DTC1',
        'lambda_param': 0.05,
        'xi_param': 1.0,
        'alpha': 0.5,
        'cost_rate': 0.0025,
        'initial_capital': 10000
    }
    
    try:
        result1 = dtc1.run(prices, config1)
        print("✓ DTC1 executed successfully")
        print(f"  Final Value: ${result1.gross_portfolio_values.iloc[-1]:,.2f}")
        print(f"  Total Return: {(result1.gross_portfolio_values.iloc[-1]/10000 - 1)*100:.2f}%")
        print(f"  Avg Turnover: {result1.turnover.mean():.4f}")
        
        # Check constraints
        weights = result1.weights
        if not np.allclose(weights.sum(axis=1), 1.0, atol=1e-4):
            print("  ⚠️ WARNING: Weights don't sum to 1.0")
        else:
            print("  ✓ Weights sum to 1.0")
            
    except Exception as e:
        print(f"✗ DTC1 failed: {e}")
        import traceback
        traceback.print_exc()

    # Test DTC2
    print("\nTesting DTC2 Variant...")
    dtc2 = DTC()
    config2 = {
        'variant': 'DTC2',
        'lambda_param': 0.05,
        'xi_param': 1.0,
        'alpha': 0.5,
        'gamma': 1e-5,
        'cost_rate': 0.0025,
        'initial_capital': 10000
    }
    
    try:
        result2 = dtc2.run(prices, config2)
        print("✓ DTC2 executed successfully")
        print(f"  Final Value: ${result2.gross_portfolio_values.iloc[-1]:,.2f}")
        print(f"  Total Return: {(result2.gross_portfolio_values.iloc[-1]/10000 - 1)*100:.2f}%")
        print(f"  Avg Turnover: {result2.turnover.mean():.4f}")
        
    except Exception as e:
        print(f"✗ DTC2 failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dtc()
