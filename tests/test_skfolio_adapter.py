import sys
from pathlib import Path
import pandas as pd
import numpy as np
from skfolio.optimization import MeanRisk

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.strategies.skfolio_adapter import SkfolioAdapter

def test_skfolio_adapter():
    print("Testing SkfolioAdapter...")
    
    # Create dummy data
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    assets = ['A', 'B', 'C']
    prices = pd.DataFrame(
        np.random.randn(100, 3).cumsum(axis=0) + 100,
        index=dates,
        columns=assets
    )
    
    # Instantiate adapter
    adapter = SkfolioAdapter(
        estimator_cls=MeanRisk,
        estimator_kwargs={},
        id="MV_TEST",
        name="Mean-Variance Test",
        window_size=20,
        rebalance_frequency='Monthly'
    )
    
    # Run strategy
    config = {'initial_capital': 10000}
    result = adapter.run(prices, config)
    
    # Verify results
    assert result.weights.shape == prices.shape
    assert result.gross_portfolio_values.shape[0] == len(prices)
    assert not result.weights.isna().all().all()
    
    print("✅ SkfolioAdapter test passed!")
    print(f"Final Portfolio Value: {result.gross_portfolio_values.iloc[-1]:.2f}")

if __name__ == "__main__":
    test_skfolio_adapter()
