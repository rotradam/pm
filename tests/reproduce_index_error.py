import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.strategies.utils import calculate_relative_returns, calculate_cumulative_returns

def test_index_error():
    print("Reproducing IndexError...")
    
    # Create a price series with a scenario that might cause dropna() to drop more than 1 row
    # Scenario: Price goes to 0, then stays 0 (0/0 = NaN)
    dates = pd.date_range(start="2023-01-01", periods=10)
    prices_data = {
        "A": [100, 101, 102, 0, 0, 105, 106, 107, 108, 109], # Asset A dies then comes back? Or just bad data.
        "B": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
    }
    prices_df = pd.DataFrame(prices_data, index=dates)
    
    print("Prices:")
    print(prices_df)
    
    # Calculate relatives using the fixed function
    relatives_array = calculate_relative_returns(prices_df)
    relatives = pd.DataFrame(relatives_array, index=prices_df.index[1:], columns=prices_df.columns)
    print(f"\nRelatives shape: {relatives.shape}")
    print(relatives)
    
    # Expected shape: (9, 2)
    # If shape is (8, 2), then we have a problem.
    
    # Simulate the loop in calculate_cumulative_returns
    n_periods = len(prices_df) # 10
    weights_matrix = pd.DataFrame(
        np.ones((n_periods, 2)) * 0.5,
        index=dates,
        columns=["A", "B"]
    )
    
    print(f"\nLooping from 1 to {n_periods} (exclusive)...")
    try:
        calculate_cumulative_returns(weights_matrix, relatives_array)
        print("Success! No error.")
    except IndexError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

if __name__ == "__main__":
    test_index_error()
