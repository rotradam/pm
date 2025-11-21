import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.strategies import list_strategies, get_strategy
from backend.data.prices import PriceFetcher
from dashboard.utils.ui import load_css
from dashboard.utils.viz import plot_equity_curves, plot_drawdowns, plot_metrics_table

st.set_page_config(page_title="Comparison", page_icon="⚖️", layout="wide")
load_css()

st.title("⚖️ Strategy Comparison")

# Load Data
@st.cache_data
def load_data(tickers=None):
    if tickers:
        try:
            fetcher = PriceFetcher()
            # Default to 10 years
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")
            return fetcher.get_adjusted_close_matrix(tickers, start_date, end_date)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None

    try:
        processed_dir = Path("data/processed")
        price_files = list(processed_dir.glob("prices_*.parquet"))
        if not price_files:
            return None
        # Sort by modification time, newest first
        latest_file = sorted(price_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        return pd.read_parquet(latest_file)
    except:
        return None

selected_tickers = st.session_state.get("selected_tickers", [])
if selected_tickers:
    st.info(f"Comparing strategies on {len(selected_tickers)} selected assets: {', '.join(selected_tickers)}")
    prices = load_data(selected_tickers)
else:
    st.info("Using default universe data.")
    prices = load_data()

if prices is None:
    st.error("Data not found.")
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

def calculate_metrics(series, initial_capital=10000):
    """Calculate comprehensive metrics."""
    returns = series.pct_change().dropna()
    total_ret = (series.iloc[-1] / initial_capital - 1) * 100
    
    days = (series.index[-1] - series.index[0]).days
    years = days / 365.25
    ann_ret = ((series.iloc[-1] / initial_capital) ** (1/years) - 1) * 100
    
    vol = returns.std() * np.sqrt(252) * 100
    sharpe = (ann_ret / vol) if vol > 0 else 0
    
    downside = returns[returns < 0]
    downside_std = downside.std() * np.sqrt(252) * 100 if len(downside) > 0 else vol
    sortino = (ann_ret / downside_std) if downside_std > 0 else 0
    
    cummax = series.cummax()
    drawdown = (series - cummax) / cummax * 100
    max_dd = drawdown.min()
    calmar = (ann_ret / abs(max_dd)) if max_dd != 0 else 0
    
    return {
        "Total Return (%)": total_ret,
        "Ann. Return (%)": ann_ret,
        "Volatility (%)": vol,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Max Drawdown (%)": max_dd,
        "Calmar Ratio": calmar
    }

# Selection
strategies = list_strategies()
strategy_map = {s['id']: s for s in strategies}

# Group strategies
benchmarks = [s for s in strategies if s['strategy_type'] == 'benchmark']
tradable = [s for s in strategies if s['strategy_type'] != 'benchmark']

# Initialize session state for selections if not present
if 'selected_benchmarks' not in st.session_state:
    st.session_state.selected_benchmarks = ['EW', 'BAH']
if 'selected_tradable' not in st.session_state:
    st.session_state.selected_tradable = []

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Select Strategies")
    
    with st.expander("Benchmarks (Reference Only)", expanded=True):
        # Control buttons
        col_sel, col_clr = st.columns([1, 1])
        if col_sel.button("Select All", key="btn_all_bench", use_container_width=True):
            st.session_state.selected_benchmarks = [s['id'] for s in benchmarks]
        if col_clr.button("Clear", key="btn_clear_bench", use_container_width=True):
            st.session_state.selected_benchmarks = []
            
        selected_benchmarks = st.multiselect(
            "Select Benchmarks",
            [s['id'] for s in benchmarks],
            format_func=lambda x: f"{strategy_map[x]['name']} ({x})",
            key="selected_benchmarks"
        )
        
    with st.expander("Tradable Strategies (Active)", expanded=True):
        # Control buttons
        col_sel_t, col_clr_t = st.columns([1, 1])
        if col_sel_t.button("Select All", key="btn_all_trad", use_container_width=True):
            st.session_state.selected_tradable = [s['id'] for s in tradable]
        if col_clr_t.button("Clear", key="btn_clear_trad", use_container_width=True):
            st.session_state.selected_tradable = []
            
        selected_tradable = st.multiselect(
            "Select Active Strategies",
            [s['id'] for s in tradable],
            format_func=lambda x: f"{strategy_map[x]['name']} ({x})",
            key="selected_tradable"
        )
    
    selected_ids = selected_benchmarks + selected_tradable

with col2:
    st.subheader("Settings")
    initial_capital = st.number_input("Initial Capital", value=10000, step=1000)
    
    rebalance_freq = st.selectbox(
        "Rebalance Frequency",
        ["Daily", "Weekly", "Monthly", "Quarterly"],
        index=0,
        help="Resamples data to this frequency before running strategies."
    )
    
    include_cash = st.checkbox(
        "Include Cash Asset",
        value=False,
        help="Adds a synthetic 'CASH' asset with constant value (risk-free)."
    )

if st.button("Run Comparison", type="primary"):
    if not selected_ids:
        st.warning("Select at least one strategy.")
    else:
        # Prepare data
        run_prices = prices.copy()
        
        # 1. Add Cash if requested
        if include_cash:
            # Create a constant price series for CASH (e.g., starting at 100)
            # Using 1.0 or 100.0 doesn't matter for returns, but let's match scale roughly or just use 100
            run_prices["CASH"] = 100.0
            
        # 2. Resample based on frequency
        if rebalance_freq != "Daily":
            rule_map = {
                "Weekly": "W-FRI",
                "Monthly": "M",
                "Quarterly": "Q"
            }
            # Resample and take the last observation (Close)
            run_prices = run_prices.resample(rule_map[rebalance_freq]).last().dropna()
            
        if run_prices.empty:
            st.error("Resampling resulted in empty data. Try a smaller frequency or larger date range.")
            st.stop()

        results = {}
        metrics_list = []
        progress = st.progress(0)
        
        for i, sid in enumerate(selected_ids):
            try:
                strategy = get_strategy(sid)
                config = get_default_strategy_config(sid, initial_capital)
                
                # Pass frequency to config (some strategies like Skfolio might use it, 
                # though we already resampled the data so 'Daily' logic applies to the resampled bars)
                config['rebalance_frequency'] = rebalance_freq
                
                res = strategy.run(run_prices, config)
                results[sid] = res.gross_portfolio_values
                
                # Calculate metrics
                m = calculate_metrics(res.gross_portfolio_values, initial_capital)
                
                # Add strategy info
                info = strategy_map[sid]
                m['Strategy'] = sid
                m['Type'] = info['strategy_type']
                # Add boolean for sorting
                m['Is Tradable'] = info['strategy_type'] != 'benchmark'
                metrics_list.append(m)
                
            except Exception as e:
                st.error(f"Failed to run {sid}: {e}")
            progress.progress((i + 1) / len(selected_ids))
            
        if results:
            st.plotly_chart(plot_equity_curves(results, "Comparative Performance"), use_container_width=True)
            st.plotly_chart(plot_drawdowns(results, "Comparative Drawdowns"), use_container_width=True)
            
            # Metrics table
            if metrics_list:
                df_metrics = pd.DataFrame(metrics_list)
                # Reorder columns
                cols = ['Strategy', 'Type', 'Is Tradable', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 
                        'Total Return (%)', 'Ann. Return (%)', 'Volatility (%)', 'Max Drawdown (%)']
                df_metrics = df_metrics[cols].set_index('Strategy')
                
                st.markdown("### Performance Metrics")
                # Use interactive dataframe for sorting
                st.dataframe(
                    df_metrics.style.format("{:.2f}", subset=df_metrics.columns.drop(['Type', 'Is Tradable'])),
                    use_container_width=True,
                    column_config={
                        "Is Tradable": st.column_config.CheckboxColumn(
                            "Tradable?",
                            help="Checked if strategy is tradable (not a benchmark)",
                            default=False,
                        )
                    }
                )
