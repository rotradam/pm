import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.strategies import list_strategies, get_strategy
from backend.data.prices import PriceFetcher
from dashboard.utils.ui import load_css
from dashboard.utils.viz import plot_equity_curves, plot_drawdowns, plot_weights_heatmap, plot_metrics_table, plot_allocation_pie

st.set_page_config(page_title="Strategy Analysis", page_icon="📈", layout="wide")
load_css()

st.title("📈 Strategy Analysis")

# Sidebar controls
st.sidebar.header("Configuration")

# Load Data
@st.cache_data
def load_data():
    try:
        return pd.read_parquet('data/processed/prices_2015-01-01_2025-11-16.parquet')
    except:
        return None

prices = load_data()

if prices is None:
    st.error("Data not found. Please go to Data Management to download data.")
    st.stop()

def get_default_strategy_config(strategy_id, initial_capital=10000):
    """Get default configuration for a strategy."""
    base_config = {'initial_capital': initial_capital}
    
    # Strategy-specific defaults
    defaults = {
        # Baseline
        'EW': {},
        'BAH': {},
        'CRP': {'target_weights': 'equal'},
        
        # Momentum
        'EG': {'eta': 0.05, 'update_rule': 'MU'},
        'UP': {'n_experts': 20, 'aggregation': 'hist_performance'},
        
        # Mean Reversion
        'OLMAR': {'reversion_method': 1, 'epsilon': 10.0, 'window': 5},
        'PAMR': {'optimization_method': 0, 'epsilon': 0.5, 'agg': 10.0},
        'CWMR': {'confidence': 0.95, 'epsilon': 0.5, 'method': 'var'},
        'RMR': {'epsilon': 20.0, 'window': 7, 'n_iteration': 200, 'tau': 0.001},
        
        # Correlation-Driven
        'CORN': {'window': 5, 'rho': 0.1},
        'CORNK': {'window': 5, 'rho': 3, 'k': 2},
        'CORNU': {'window': 5, 'rho': 0.1},
        
        # Follow-The-Leader
        'BCRP': {},
        'BestStock': {},
        'FTL': {},
        'FTRL': {'lam': 0.1},
        
        # Skfolio
        'MV': {}
    }
    
    if strategy_id in defaults:
        base_config.update(defaults[strategy_id])
    
    return base_config

# Strategy Selection
strategies = list_strategies()
strategy_names = [s['name'] for s in strategies]
selected_strategy_name = st.sidebar.selectbox("Select Strategy", strategy_names)
selected_strategy_info = next(s for s in strategies if s['name'] == selected_strategy_name)
strategy_id = selected_strategy_info['id']

# Parameters
st.sidebar.subheader("Parameters")
initial_capital = st.sidebar.number_input("Initial Capital", value=10000, step=1000)
rebalance_freq = st.sidebar.selectbox("Rebalance Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"], index=2)
include_cash = st.sidebar.checkbox("Include Cash Asset", value=False, help="Adds a synthetic 'CASH' asset with constant value.")

# Run Button
if st.sidebar.button("Run Analysis", type="primary"):
    with st.spinner(f"Running {selected_strategy_name}..."):
        try:
            # Instantiate strategy
            strategy = get_strategy(strategy_id)
            
            # Prepare data
            run_prices = prices.copy()
            
            # 1. Add Cash if requested
            if include_cash:
                run_prices["CASH"] = 100.0
                
            # 2. Resample based on frequency
            if rebalance_freq != "Daily":
                rule_map = {
                    "Weekly": "W-FRI",
                    "Monthly": "M",
                    "Quarterly": "Q"
                }
                run_prices = run_prices.resample(rule_map[rebalance_freq]).last().dropna()
            
            if run_prices.empty:
                st.error("Resampling resulted in empty data.")
                st.stop()

            # Get default config and update with UI params
            config = get_default_strategy_config(strategy_id, initial_capital)
            config['rebalance_frequency'] = rebalance_freq
            
            result = strategy.run(run_prices, config)
            
            # Display Results
            st.markdown(f"### Performance: {selected_strategy_name}")
            
            # Metrics
            final_value = result.gross_portfolio_values.iloc[-1]
            total_return = (final_value / initial_capital - 1) * 100
            
            # Calculate Sharpe
            returns = result.gross_portfolio_values.pct_change().dropna()
            vol = returns.std() * np.sqrt(252)
            sharpe = (returns.mean() * 252) / vol if vol > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Final Value", f"${final_value:,.2f}")
            col2.metric("Total Return", f"{total_return:.2f}%")
            col3.metric("Sharpe Ratio", f"{sharpe:.2f}")
            col3.metric("Turnover", f"{result.turnover.mean():.4f}")
            
            # Plots
            tab1, tab2, tab3, tab4 = st.tabs(["Equity Curve", "Drawdown", "Weights Heatmap", "Current Allocation"])
            
            with tab1:
                st.plotly_chart(plot_equity_curves({selected_strategy_name: result.gross_portfolio_values}), use_container_width=True)
                
            with tab2:
                st.plotly_chart(plot_drawdowns({selected_strategy_name: result.gross_portfolio_values}), use_container_width=True)
                
            with tab3:
                st.plotly_chart(plot_weights_heatmap(result.weights), use_container_width=True)
                
            with tab4:
                # Show last 3 periods of allocations
                weights_history = result.weights.tail(3)
                # Reverse order to show Latest first
                weights_history = weights_history.iloc[::-1]
                
                if weights_history.empty:
                    st.info("No allocation data available.")
                else:
                    for i, (date, row) in enumerate(weights_history.iterrows()):
                        date_str = date.strftime('%Y-%m-%d')
                        label = "Latest Prediction" if i == 0 else f"Allocation on {date_str}"
                        
                        st.markdown(f"### {label}")
                        st.plotly_chart(
                            plot_allocation_pie(row, title=None), 
                            use_container_width=True,
                            key=f"allocation_pie_{i}"
                        )
                        
                        if i < len(weights_history) - 1:
                            st.markdown("---")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            import traceback
            st.code(traceback.format_exc())

# Strategy Info
with st.expander("Strategy Details"):
    st.json(selected_strategy_info)
