import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.strategies.dtc import DTC
from backend.strategies.waeg import WAEGStrategy

def test_nan_strategies():
    print("Reproducing NaN in DTC and WAEG...")
    
    # Create problematic price data
    # 1. Asset A: Normal
    # 2. Asset B: Constant (returns = 0 -> relative = 1)
    # 3. Asset C: Drops to 0 (relative = 0)
    # 4. Asset D: 0 then jumps (relative = inf)
    
    dates = pd.date_range(start="2023-01-01", periods=10)
    prices_data = {
        "A": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        "B": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        "C": [10, 5, 1, 0, 0, 0, 0, 0, 0, 0],
        "D": [10, 10, 0, 0, 10, 10, 10, 10, 10, 10] # 0 -> 10 jump causes Inf
    }
    prices_df = pd.DataFrame(prices_data, index=dates)
    
    print("Prices:")
    print(prices_df)
    
    config = {'initial_capital': 10000}
    
    # Test DTC
    print("\n--- Testing DTC ---")
    try:
        dtc = DTC()
        res = dtc.run(prices_df, config)
        print(f"Final Value: {res.gross_portfolio_values.iloc[-1]}")
        if np.isnan(res.gross_portfolio_values.iloc[-1]):
            print("FAILURE: DTC returned NaN")
        else:
            print("SUCCESS: DTC returned valid value")
    except Exception as e:
        print(f"ERROR in DTC: {e}")

    # Test WAEG
    print("\n--- Testing WAEG ---")
    try:
        waeg = WAEGStrategy()
        res = waeg.run(prices_df, config)
        print(f"Final Value: {res.gross_portfolio_values.iloc[-1]}")
        if np.isnan(res.gross_portfolio_values.iloc[-1]):
            print("FAILURE: WAEG returned NaN")
        else:
            print("SUCCESS: WAEG returned valid value")
    except Exception as e:
        print(f"ERROR in WAEG: {e}")

if __name__ == "__main__":
    test_nan_strategies()
