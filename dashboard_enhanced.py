"""
Enhanced dashboard with strategy classifications, pie charts, and better data handling.

Key improvements:
1. Strategy badges showing type (Benchmark/Implementable/Look-Ahead/Paper-Only)
2. Pie chart for optimal portfolio weights
3. Data quality filtering (minimum data completeness)
4. Strategy ranking by multiple metrics
5. Default: run all strategies and rank by Sharpe ratio
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.strategies import list_strategies, get_strategy
from backend.costs import MaxblueCostModel, apply_transaction_costs


# Page config
st.set_page_config(
    page_title="OLPS Strategy Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .strategy-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .badge-benchmark {background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb;}
    .badge-implementable {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .badge-look-ahead {background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7;}
    .badge-paper-only {background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
    .badge-causal-lagging {background-color: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;}
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def get_strategy_badge(strategy_type: str, implementable: bool) -> str:
    """Generate HTML badge for strategy type."""
    if strategy_type == 'benchmark':
        return '<span class="strategy-badge badge-benchmark">📊 BENCHMARK</span>'
    elif strategy_type == 'benchmark_lookahead':
        return '<span class="strategy-badge badge-look-ahead">⚠️ LOOK-AHEAD</span>'
    elif strategy_type == 'causal':
        if implementable:
            return '<span class="strategy-badge badge-implementable">✅ IMPLEMENTABLE</span>'
        else:
            return '<span class="strategy-badge badge-paper-only">📄 PAPER ONLY</span>'
    elif strategy_type == 'causal_lagging':
        return '<span class="strategy-badge badge-causal-lagging">⏱️ LAGGING</span>'
    else:
        return '<span class="strategy-badge badge-paper-only">❓ UNKNOWN</span>'


@st.cache_data
def load_price_data():
    """Load the ETF price data from processed parquet file."""
    try:
        prices = pd.read_parquet('data/processed/prices_2015-01-01_2025-11-16.parquet')
        return prices
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


@st.cache_data
def load_universe():
    """Load the ETF universe."""
    try:
        universe = pd.read_csv('documents/etf_universe_full_clean.csv')
        return universe
    except Exception as e:
        st.error(f"Error loading universe: {e}")
        return None


def get_data_quality_stats(prices_df):
    """Calculate data quality statistics for each asset."""
    stats = pd.DataFrame({
        'ticker': prices_df.columns,
        'completeness_%': (prices_df.notna().sum() / len(prices_df) * 100).values,
        'total_days': len(prices_df),
        'missing_days': prices_df.isna().sum().values,
        'first_date': prices_df.apply(lambda x: x.first_valid_index()).values,
        'last_date': prices_df.apply(lambda x: x.last_valid_index()).values,
    })
    stats['data_years'] = (pd.to_datetime(stats['last_date']) - pd.to_datetime(stats['first_date'])).dt.days / 365.25
    return stats.sort_values('completeness_%', ascending=False)


def resample_prices(prices_df, frequency):
    """Resample prices based on frequency."""
    freq_map = {
        'Daily': 'D',
        'Weekly': 'W',
        'Monthly': 'ME',  # Month-end
        'Quarterly': 'QE'  # Quarter-end
    }
    
    if frequency == 'Daily':
        return prices_df
    
    freq = freq_map[frequency]
    return prices_df.resample(freq).last().dropna()


def calculate_metrics(portfolio_values, turnover_series, initial_capital=10000):
    """Calculate comprehensive performance metrics."""
    returns = portfolio_values.pct_change().dropna()
    
    # Total return
    total_return = (portfolio_values.iloc[-1] / initial_capital - 1) * 100
    
    # Annualized return
    days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
    years = days / 365.25
    annualized_return = ((portfolio_values.iloc[-1] / initial_capital) ** (1/years) - 1) * 100
    
    # Volatility (annualized)
    volatility = returns.std() * np.sqrt(252) * 100
    
    # Sharpe ratio (assuming 0% risk-free rate)
    sharpe = (annualized_return / volatility) if volatility > 0 else 0
    
    # Sortino ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) * 100 if len(downside_returns) > 0 else volatility
    sortino = (annualized_return / downside_std) if downside_std > 0 else 0
    
    # Max drawdown
    cummax = portfolio_values.cummax()
    drawdown = (portfolio_values - cummax) / cummax * 100
    max_drawdown = drawdown.min()
    
    # Calmar ratio
    calmar = (annualized_return / abs(max_drawdown)) if max_drawdown != 0 else 0
    
    # Average turnover
    avg_turnover = turnover_series.mean()
    total_turnover = turnover_series.sum()
    
    # Win rate
    win_rate = (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0
    
    return {
        'Total Return (%)': total_return,
        'Annualized Return (%)': annualized_return,
        'Volatility (%)': volatility,
        'Sharpe Ratio': sharpe,
        'Sortino Ratio': sortino,
        'Calmar Ratio': calmar,
        'Max Drawdown (%)': max_drawdown,
        'Avg Turnover': avg_turnover,
        'Total Turnover': total_turnover,
        'Win Rate (%)': win_rate,
        'Final Value': portfolio_values.iloc[-1]
    }


def find_common_date_range(prices_df):
    """
    Find the common date range where ALL assets have data.
    
    Returns:
        tuple: (common_start_date, common_end_date, n_days, per_asset_info)
    """
    # Find first and last valid date for each asset
    asset_ranges = {}
    for col in prices_df.columns:
        valid_data = prices_df[col].dropna()
        if len(valid_data) > 0:
            asset_ranges[col] = {
                'first_date': valid_data.index[0],
                'last_date': valid_data.index[-1],
                'n_days': len(valid_data)
            }
    
    if not asset_ranges:
        return None, None, 0, {}
    
    # Common start = latest first date (newest asset)
    common_start = max(info['first_date'] for info in asset_ranges.values())
    # Common end = earliest last date
    common_end = min(info['last_date'] for info in asset_ranges.values())
    
    # Calculate days in common range
    n_days = len(prices_df.loc[common_start:common_end])
    
    return common_start, common_end, n_days, asset_ranges


def apply_cost_model(result, prices_df, cost_model, initial_capital):
    """
    Apply transaction cost model to a backtest result.
    
    Args:
        result: dict with weights, portfolio_values, etc.
        prices_df: price DataFrame used in backtest
        cost_model: MaxblueCostModel instance
        initial_capital: starting capital
        
    Returns:
        dict with added net_portfolio_values, total_costs, cost_metrics
    """
    weights = result['weights']
    gross_values = result['portfolio_values']
    
    # Calculate price relatives (returns + 1)
    price_relatives = prices_df.pct_change().fillna(0) + 1
    # Align with weights
    price_relatives = price_relatives.loc[weights.index]
    
    # Apply transaction costs
    net_values, total_costs, costs_per_period = apply_transaction_costs(
        weights=weights,
        portfolio_values=gross_values,
        price_relatives=price_relatives,
        cost_model=cost_model,
        initial_capital=initial_capital
    )
    
    # Calculate cost metrics
    gross_return = (gross_values.iloc[-1] / initial_capital - 1) * 100
    net_return = (net_values.iloc[-1] / initial_capital - 1) * 100
    cost_drag_pct = gross_return - net_return
    cost_drag_bps = cost_drag_pct * 100  # basis points
    
    # Add to result
    result['net_portfolio_values'] = net_values
    result['total_costs'] = total_costs
    result['costs_per_period'] = costs_per_period
    result['cost_metrics'] = {
        'total_costs_eur': total_costs,
        'cost_drag_pct': cost_drag_pct,
        'cost_drag_bps': cost_drag_bps,
        'gross_return_pct': gross_return,
        'net_return_pct': net_return
    }
    
    return result


def plot_equity_curves(results_dict):
    """Plot equity curves for all strategies with different styles for benchmark/lagging."""
    from backend.strategies import get_strategy, StrategyType
    
    fig = go.Figure()
    
    for name, result in results_dict.items():
        strategy_id = result['strategy_id']
        
        try:
            strategy = get_strategy(strategy_id)
            strategy_type = strategy.strategy_type
        except:
            strategy_type = StrategyType.CAUSAL  # Default
        
        # Determine line style based on strategy type
        if strategy_type in [StrategyType.BENCHMARK, StrategyType.BENCHMARK_LOOKAHEAD]:
            # Benchmark strategies: dotted line, duller color (50% opacity)
            line_style = dict(width=2, dash='dot')
            opacity = 0.5
        elif strategy_type == StrategyType.CAUSAL_LAGGING:
            # Lagging strategies: dashed line, slightly dull (70% opacity)
            line_style = dict(width=2, dash='dash')
            opacity = 0.7
        else:
            # Causal strategies: solid line, full opacity
            line_style = dict(width=2)
            opacity = 1.0
        
        fig.add_trace(go.Scatter(
            x=result['portfolio_values'].index,
            y=result['portfolio_values'].values,
            name=name,
            mode='lines',
            line=line_style,
            opacity=opacity
        ))
    
    fig.update_layout(
        title='Portfolio Value Over Time',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        hovermode='x unified',
        height=500,
        template='plotly_white',
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig


def plot_weights_pie(weights_series, title="Current Portfolio Allocation", threshold=0.01):
    """Plot pie chart of portfolio weights, showing only positions > threshold."""
    # Filter to significant positions
    significant = weights_series[weights_series > threshold].sort_values(ascending=False)
    
    # Group small positions into "Others"
    small_positions = weights_series[weights_series <= threshold]
    if len(small_positions) > 0:
        others_weight = small_positions.sum()
        if others_weight > 0:
            significant = pd.concat([significant, pd.Series({'Others (each <1%)': others_weight})])
    
    fig = go.Figure(data=[go.Pie(
        labels=significant.index,
        values=significant.values,
        hole=0.3,
        textinfo='label+percent',
        textposition='auto',
        marker=dict(line=dict(color='white', width=2))
    )])
    
    fig.update_layout(
        title=title,
        height=500,
        template='plotly_white',
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    
    return fig


def plot_drawdown(results_dict):
    """Plot drawdown curves with different styles for benchmark/lagging strategies."""
    from backend.strategies import get_strategy, StrategyType
    
    fig = go.Figure()
    
    for name, result in results_dict.items():
        strategy_id = result['strategy_id']
        
        try:
            strategy = get_strategy(strategy_id)
            strategy_type = strategy.strategy_type
        except:
            strategy_type = StrategyType.CAUSAL  # Default
        
        # Determine line style based on strategy type
        if strategy_type in [StrategyType.BENCHMARK, StrategyType.BENCHMARK_LOOKAHEAD]:
            # Benchmark strategies: dotted line, duller color (50% opacity)
            line_style = dict(width=2, dash='dot')
            opacity = 0.5
        elif strategy_type == StrategyType.CAUSAL_LAGGING:
            # Lagging strategies: dashed line, slightly dull (70% opacity)
            line_style = dict(width=2, dash='dash')
            opacity = 0.7
        else:
            # Causal strategies: solid line, full opacity
            line_style = dict(width=2)
            opacity = 1.0
        
        pv = result['portfolio_values']
        cummax = pv.cummax()
        drawdown = (pv - cummax) / cummax * 100
        
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            name=name,
            mode='lines',
            fill='tozeroy',
            line=line_style,
            opacity=opacity
        ))
    
    fig.update_layout(
        title='Drawdown Over Time',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def plot_weights_heatmap(weights_df, title="Portfolio Weights Over Time"):
    """Plot heatmap of portfolio weights."""
    fig = go.Figure(data=go.Heatmap(
        z=weights_df.T.values,
        x=weights_df.index,
        y=weights_df.columns,
        colorscale='RdYlGn',
        zmid=1/len(weights_df.columns),
        colorbar=dict(title="Weight")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Assets',
        height=400,
        template='plotly_white'
    )
    
    return fig


def plot_final_weights(results_dict):
    """Plot final portfolio weights as bar chart."""
    fig = go.Figure()
    
    for name, result in results_dict.items():
        final_weights = result['weights'].iloc[-1]
        # Only show non-zero weights
        non_zero = final_weights[final_weights > 0.01]
        
        fig.add_trace(go.Bar(
            name=name,
            x=non_zero.index,
            y=non_zero.values,
            text=[f'{v:.1%}' for v in non_zero.values],
            textposition='auto'
        ))
    
    fig.update_layout(
        title='Final Portfolio Weights (>1%)',
        xaxis_title='Assets',
        yaxis_title='Weight',
        barmode='group',
        height=400,
        template='plotly_white',
        yaxis=dict(tickformat='.0%')
    )
    
    return fig


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
        'EG': {
            'eta': 0.05,
            'update_rule': 'MU'
        },
        'UP': {
            'n_experts': 20,
            'aggregation': 'hist_performance'
        },
        
        # Mean Reversion
        'OLMAR': {
            'reversion_method': 1,  # SMA
            'epsilon': 10.0,
            'window': 5
        },
        'PAMR': {
            'optimization_method': 0,  # PAMR
            'epsilon': 0.5,
            'agg': 10.0
        },
        'CWMR': {
            'confidence': 0.95,
            'epsilon': 0.5,
            'method': 'var'
        },
        'RMR': {
            'epsilon': 20.0,
            'window': 7,
            'n_iteration': 200,
            'tau': 0.001
        },
        
        # Correlation-Driven
        'CORN': {
            'window': 5,
            'rho': 0.1
        },
        'CORNK': {
            'window': 5,
            'rho': 3,
            'k': 2
        },
        'CORNU': {
            'window': 5,
            'rho': 0.1
        },
        
        # Follow-The-Leader
        'BCRP': {},
        'BestStock': {},
        'FTL': {},
        'FTRL': {
            'lam': 0.1
        }
    }
    
    if strategy_id in defaults:
        base_config.update(defaults[strategy_id])
    
    return base_config


def run_backtest(strategy_id, prices_df, config):
    """Run a single backtest."""
    try:
        strategy = get_strategy(strategy_id)
        result = strategy.run(prices_df, config)
        
        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy.name,
            'weights': result.weights,
            'portfolio_values': result.gross_portfolio_values,
            'turnover': result.turnover,
            'metadata': result.metadata
        }
    except Exception as e:
        st.error(f"Error running {strategy_id}: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


def main():
    # Header
    st.markdown('<div class="main-header">📈 OLPS Strategy Research Dashboard</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Research Platform for Online Portfolio Selection Strategies**  
    Compare benchmark and implementable strategies on real ETF data with customizable rebalancing frequencies.
    """)
    
    # Load data
    with st.spinner('Loading data...'):
        prices_full = load_price_data()
        universe = load_universe()
    
    if prices_full is None:
        st.error("Failed to load price data. Please ensure data/processed/prices_*.parquet exists.")
        st.info("💡 Run `python scripts/download_data.py` to fetch price data.")
        return
    
    # Sidebar - Configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Quick preset selector
    st.sidebar.subheader("Quick Presets")
    preset = st.sidebar.selectbox(
        "Load preset configuration",
        ['Custom', 'Quick Test (1 year, 10 assets)', 'Full Backtest (10 years, 50 assets)', 'Conservative (5 years, 20 assets)']
    )
    
    if preset == 'Quick Test (1 year, 10 assets)':
        default_start = max(prices_full.index.min().date(), prices_full.index.max().date() - timedelta(days=365))
        default_assets = 10
        default_min_completeness = 95.0
    elif preset == 'Full Backtest (10 years, 50 assets)':
        default_start = prices_full.index.min().date()
        default_assets = 50
        default_min_completeness = 90.0
    elif preset == 'Conservative (5 years, 20 assets)':
        default_start = max(prices_full.index.min().date(), prices_full.index.max().date() - timedelta(days=1825))
        default_assets = 20
        default_min_completeness = 98.0
    else:
        default_start = max(prices_full.index.min().date(), prices_full.index.max().date() - timedelta(days=730))
        default_assets = 20
        default_min_completeness = 95.0
    
    # Date range
    st.sidebar.subheader("📅 Date Range")
    min_date = prices_full.index.min().date()
    max_date = prices_full.index.max().date()
    
    date_range = st.sidebar.date_input(
        "Select date range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) != 2:
        st.sidebar.warning("Please select both start and end dates")
        return
    
    start_date, end_date = date_range
    
    # Filter prices by date
    prices_filtered = prices_full.loc[start_date:end_date]
    
    # Data quality filtering
    st.sidebar.subheader("🔍 Data Quality")
    min_completeness = st.sidebar.slider(
        "Minimum data completeness (%)",
        50.0, 100.0, default_min_completeness, 5.0,
        help="Only use assets with at least this percentage of data available"
    )
    
    # Calculate completeness
    completeness = prices_filtered.notna().sum() / len(prices_filtered) * 100
    qualified_assets = completeness[completeness >= min_completeness].index.tolist()
    
    st.sidebar.info(f"✅ {len(qualified_assets)} assets meet {min_completeness}% completeness")
    
    # Asset selection
    st.sidebar.subheader("🎯 Asset Universe")
    n_assets = st.sidebar.slider(
        "Number of assets",
        5,
        min(len(qualified_assets), 60),
        min(default_assets, len(qualified_assets))
    )
    
    # Select top N from qualified assets by completeness
    top_assets = completeness[qualified_assets].nlargest(n_assets).index.tolist()
    prices = prices_filtered[top_assets].dropna()
    
    # Calculate and display common date range
    common_start, common_end, n_common_days, asset_info = find_common_date_range(prices_filtered[top_assets])
    
    if common_start and common_end:
        st.sidebar.success(f"📊 Using {len(top_assets)} assets, {len(prices)} trading days")
        
        # Show explicit common date range
        st.sidebar.info(
            f"📅 **Common Data Period:**\n\n"
            f"From: `{common_start.strftime('%Y-%m-%d')}`\n\n"
            f"To: `{common_end.strftime('%Y-%m-%d')}`\n\n"
            f"Days: `{n_common_days}` ({n_common_days/252:.1f} years)"
        )
        
        # Show limiting assets (those that start latest)
        limiting_assets = sorted(
            [(ticker, info['first_date']) for ticker, info in asset_info.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if limiting_assets:
            st.sidebar.caption(f"⚠️ Backtest limited by:")
            for ticker, first_date in limiting_assets:
                st.sidebar.caption(f"  • `{ticker}` starts {first_date.strftime('%Y-%m-%d')}")
    else:
        st.sidebar.success(f"📊 Using {len(top_assets)} assets, {len(prices)} trading days")
    
    # Show data quality stats
    with st.sidebar.expander("📈 Data Quality Details"):
        quality_stats = get_data_quality_stats(prices_filtered[top_assets])
        st.dataframe(
            quality_stats[['ticker', 'completeness_%', 'data_years']].head(10),
            height=200
        )
    
    # Transaction costs toggle
    st.sidebar.subheader("💰 Transaction Costs")
    apply_costs = st.sidebar.checkbox(
        "Apply Maxblue transaction costs",
        value=True,
        help="Apply realistic Maxblue Depot transaction costs (0.25% commission, €8.90-€58.90 range, €2 exchange fee)"
    )
    
    if apply_costs:
        with st.sidebar.expander("⚙️ Cost Model Parameters"):
            st.write("**Maxblue Depot Model:**")
            st.write("- Commission: 0.25%")
            st.write("- Minimum: €8.90")
            st.write("- Maximum: €58.90")
            st.write("- Exchange fee: €2.00")
            st.caption("These are the standard Deutsche Bank Maxblue fees")
    
    # Rebalancing frequency
    st.sidebar.subheader("⏰ Rebalancing")
    frequency = st.sidebar.selectbox(
        "Frequency",
        ['Daily', 'Weekly', 'Monthly', 'Quarterly'],
        index=2  # Default to Monthly
    )
    
    # Resample prices
    prices_resampled = resample_prices(prices, frequency)
    st.sidebar.info(f"After resampling: {len(prices_resampled)} periods")
    
    # Initial capital
    initial_capital = st.sidebar.number_input(
        "Initial Capital ($)",
        min_value=1000,
        max_value=10000000,
        value=10000,
        step=1000
    )
    
    # Strategy selection
    st.sidebar.header("📊 Strategy Selection")
    
    # Get all available strategies
    all_strategies = list_strategies()
    
    # Create selection interface with badges
    run_all = st.sidebar.checkbox("🚀 Run All Strategies", value=True)
    
    if not run_all:
        st.sidebar.markdown("**Select strategies to compare:**")
        selected_strategies = []
        
        # Group by type for organized selection
        strategy_groups = {
            'Benchmark': [s for s in all_strategies if s['strategy_type'] in ['benchmark', 'benchmark_lookahead']],
            'Implementable': [s for s in all_strategies if s['strategy_type'] in ['causal', 'causal_lagging'] and s['implementable']],
            'Paper Only': [s for s in all_strategies if not s['implementable']]
        }
        
        for group_name, strategies in strategy_groups.items():
            if strategies:
                st.sidebar.markdown(f"**{group_name}**")
                for s in strategies:
                    badge = get_strategy_badge(s['strategy_type'], s['implementable'])
                    label = f"{s['name']} ({s['id']})"
                    if st.sidebar.checkbox(label, key=f"select_{s['id']}", value=False):
                        selected_strategies.append(s['id'])
    else:
        selected_strategies = [s['id'] for s in all_strategies]
    
    # Strategy-specific parameters (simplified for now)
    st.sidebar.header("🎛️ Parameters")
    with st.sidebar.expander("⚙️ Advanced Parameters"):
        st.info("Using default parameters for all strategies. Custom parameter tuning coming soon!")
    
    # Run backtests button
    if st.sidebar.button("🚀 Run Backtests", type="primary", use_container_width=True):
        if not selected_strategies:
            st.warning("⚠️ Please select at least one strategy")
            return
        
        # Create cost model if enabled
        cost_model = MaxblueCostModel() if apply_costs else None
        
        # Run all backtests
        results = {}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, sid in enumerate(selected_strategies):
            status_text.text(f"Running {sid}... ({idx+1}/{len(selected_strategies)})")
            
            # Get default configuration for this strategy
            config = get_default_strategy_config(sid, initial_capital)
            
            result = run_backtest(sid, prices_resampled, config)
            
            if result:
                # Apply transaction costs if enabled
                if apply_costs and cost_model:
                    result = apply_cost_model(result, prices_resampled, cost_model, initial_capital)
                else:
                    # No costs: net = gross
                    result['net_portfolio_values'] = result['portfolio_values']
                    result['total_costs'] = 0
                    result['costs_per_period'] = pd.Series(0, index=result['portfolio_values'].index)
                    result['cost_metrics'] = {
                        'total_costs_eur': 0,
                        'cost_drag_pct': 0,
                        'cost_drag_bps': 0,
                        'gross_return_pct': (result['portfolio_values'].iloc[-1] / initial_capital - 1) * 100,
                        'net_return_pct': (result['portfolio_values'].iloc[-1] / initial_capital - 1) * 100
                    }
                
                results[result['strategy_name']] = result
            
            progress_bar.progress((idx + 1) / len(selected_strategies))
        
        status_text.empty()
        progress_bar.empty()
        
        if not results:
            st.error("❌ No successful backtests")
            return
        
        # Store results in session state
        st.session_state['results'] = results
        st.session_state['prices'] = prices_resampled
        st.session_state['initial_capital'] = initial_capital
        st.session_state['all_strategies_info'] = all_strategies
        st.session_state['apply_costs'] = apply_costs
        
        st.success(f"✅ Completed {len(results)} backtests!")

    
    # Display results
    if 'results' in st.session_state:
        results = st.session_state['results']
        initial_capital = st.session_state['initial_capital']
        all_strategies_info = st.session_state.get('all_strategies_info', list_strategies())
        apply_costs = st.session_state.get('apply_costs', False)
        
        st.header("📊 Results & Analysis")
        
        # Show cost mode indicator
        if apply_costs:
            st.info("💰 **Transaction costs applied** - Returns shown are NET of Maxblue fees (0.25% commission)")
        else:
            st.info("📊 **Frictionless mode** - Returns shown are GROSS (no transaction costs)")
        
        # Create strategy lookup for metadata
        strategy_lookup = {s['id']: s for s in all_strategies_info}
        
        # Calculate all metrics (using net values if costs applied)
        metrics_data = {}
        for name, result in results.items():
            # Use net values if costs were applied
            portfolio_values = result.get('net_portfolio_values', result['portfolio_values'])
            
            metrics = calculate_metrics(
                portfolio_values,
                result['turnover'],
                initial_capital
            )
            
            # Add cost metrics if available
            if 'cost_metrics' in result and result['cost_metrics']['total_costs_eur'] > 0:
                metrics['Gross Return (%)'] = result['cost_metrics']['gross_return_pct']
                metrics['Net Return (%)'] = result['cost_metrics']['net_return_pct']
                metrics['Cost Drag (%)'] = result['cost_metrics']['cost_drag_pct']
                metrics['Cost Drag (bps)'] = result['cost_metrics']['cost_drag_bps']
                metrics['Total Costs (€)'] = result['cost_metrics']['total_costs_eur']
            
            # Add strategy classification
            sid = result['strategy_id']
            if sid in strategy_lookup:
                metrics['Type'] = strategy_lookup[sid]['strategy_type']
                metrics['Implementable'] = '✅' if strategy_lookup[sid]['implementable'] else '❌'
                metrics['Complexity'] = strategy_lookup[sid]['complexity']
            metrics_data[name] = metrics
        
        metrics_df = pd.DataFrame(metrics_data).T
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏆 Rankings",
            "📈 Performance",
            "💰 Cost Analysis",
            "🥧 Portfolio Weights",
            "📉 Risk Analysis",
            "ℹ️ Strategy Info"
        ])
        
        with tab1:
            st.subheader("Strategy Rankings")
            
            # Ranking selector
            rank_by = st.selectbox(
                "Rank by metric",
                ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Total Return (%)', 'Annualized Return (%)'],
                index=0
            )
            
            # Filter by implementability
            show_filter = st.radio(
                "Show strategies",
                ['All', 'Implementable Only', 'Benchmarks Only'],
                horizontal=True
            )
            
            filtered_df = metrics_df.copy()
            if show_filter == 'Implementable Only':
                filtered_df = filtered_df[filtered_df['Implementable'] == '✅']
            elif show_filter == 'Benchmarks Only':
                filtered_df = filtered_df[filtered_df['Type'].isin(['benchmark', 'benchmark_lookahead'])]
            
            # Sort and display
            ranked_df = filtered_df.sort_values(rank_by, ascending=False)
            
            # Add rank column
            ranked_df.insert(0, 'Rank', range(1, len(ranked_df) + 1))
            
            # Display table with formatting
            st.dataframe(
                ranked_df.style.format({
                    'Total Return (%)': '{:.2f}',
                    'Annualized Return (%)': '{:.2f}',
                    'Volatility (%)': '{:.2f}',
                    'Sharpe Ratio': '{:.2f}',
                    'Sortino Ratio': '{:.2f}',
                    'Calmar Ratio': '{:.2f}',
                    'Max Drawdown (%)': '{:.2f}',
                    'Avg Turnover': '{:.4f}',
                    'Total Turnover': '{:.2f}',
                    'Win Rate (%)': '{:.1f}',
                    'Final Value': '${:,.2f}'
                }),
                width="stretch",
                height=400
            )
            
            # Best strategy highlight
            best_strategy = ranked_df.index[0]
            best_value = ranked_df[rank_by].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏆 Top Strategy", best_strategy)
            with col2:
                st.metric(f"Best {rank_by}", f"{best_value:.2f}")
            with col3:
                implementable_status = ranked_df['Implementable'].iloc[0]
                st.metric("Implementable", implementable_status)
        
        with tab2:
            # Equity curves
            st.subheader("Equity Curves")
            fig_equity = plot_equity_curves(results)
            st.plotly_chart(fig_equity, width="stretch")
            
            # Summary metrics table
            st.subheader("Performance Summary")
            summary_cols = ['Total Return (%)', 'Annualized Return (%)', 'Volatility (%)', 
                          'Sharpe Ratio', 'Max Drawdown (%)', 'Win Rate (%)']
            st.dataframe(
                metrics_df[summary_cols].style.format({
                    'Total Return (%)': '{:.2f}',
                    'Annualized Return (%)': '{:.2f}',
                    'Volatility (%)': '{:.2f}',
                    'Sharpe Ratio': '{:.2f}',
                    'Max Drawdown (%)': '{:.2f}',
                    'Win Rate (%)': '{:.1f}'
                }).background_gradient(subset=['Sharpe Ratio'], cmap='RdYlGn'),
                width="stretch"
            )
        
        with tab3:
            st.subheader("💰 Transaction Cost Analysis")
            
            if apply_costs:
                # Cost impact table
                st.markdown("### Cost Impact by Strategy")
                
                cost_cols = ['Avg Turnover', 'Total Costs (€)', 'Gross Return (%)', 
                            'Net Return (%)', 'Cost Drag (%)', 'Cost Drag (bps)']
                
                available_cost_cols = [col for col in cost_cols if col in metrics_df.columns]
                
                if available_cost_cols:
                    cost_df = metrics_df[available_cost_cols].copy()
                    # Sort by cost drag (highest impact first)
                    if 'Cost Drag (%)' in cost_df.columns:
                        cost_df = cost_df.sort_values('Cost Drag (%)', ascending=False)
                    
                    st.dataframe(
                        cost_df.style.format({
                            'Avg Turnover': '{:.4f}',
                            'Total Costs (€)': '€{:,.2f}',
                            'Gross Return (%)': '{:.2f}',
                            'Net Return (%)': '{:.2f}',
                            'Cost Drag (%)': '{:.2f}',
                            'Cost Drag (bps)': '{:.0f}'
                        }).background_gradient(subset=['Cost Drag (%)'], cmap='RdYlGn_r'),
                        width="stretch"
                    )
                    
                    # Key insights
                    st.markdown("### 📊 Key Insights")
                    
                    if 'Cost Drag (%)' in metrics_df.columns:
                        highest_drag = metrics_df['Cost Drag (%)'].idxmax()
                        highest_drag_value = metrics_df.loc[highest_drag, 'Cost Drag (%)']
                        lowest_drag = metrics_df['Cost Drag (%)'].idxmin()
                        lowest_drag_value = metrics_df.loc[lowest_drag, 'Cost Drag (%)']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            total_fees = metrics_df['Total Costs (€)'].sum() if 'Total Costs (€)' in metrics_df.columns else 0
                            st.metric("💸 Total Fees Paid", f"€{total_fees:,.2f}")
                        with col2:
                            st.metric("🔴 Highest Cost Drag", f"{highest_drag_value:.2f}%", 
                                     delta=f"{highest_drag}", delta_color="inverse")
                        with col3:
                            st.metric("🟢 Lowest Cost Drag", f"{lowest_drag_value:.2f}%",
                                     delta=f"{lowest_drag}", delta_color="normal")
                    
                    # Gross vs Net comparison chart
                    st.markdown("### 📈 Gross vs Net Returns")
                    
                    if 'Gross Return (%)' in metrics_df.columns and 'Net Return (%)' in metrics_df.columns:
                        comparison_df = metrics_df[['Gross Return (%)', 'Net Return (%)']].copy()
                        comparison_df = comparison_df.sort_values('Gross Return (%)', ascending=False)
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            name='Gross Return',
                            x=comparison_df.index,
                            y=comparison_df['Gross Return (%)'],
                            marker_color='lightblue'
                        ))
                        fig.add_trace(go.Bar(
                            name='Net Return (After Costs)',
                            x=comparison_df.index,
                            y=comparison_df['Net Return (%)'],
                            marker_color='darkblue'
                        ))
                        fig.update_layout(
                            barmode='group',
                            title='Gross vs Net Returns Comparison',
                            xaxis_title='Strategy',
                            yaxis_title='Return (%)',
                            height=500
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Cumulative costs over time
                    st.markdown("### 📉 Cumulative Costs Over Time")
                    
                    selected_for_costs = st.multiselect(
                        "Select strategies to compare costs",
                        list(results.keys()),
                        default=list(results.keys())[:3]
                    )
                    
                    if selected_for_costs:
                        fig_costs = go.Figure()
                        
                        for name in selected_for_costs:
                            if 'costs_per_period' in results[name]:
                                cumulative_costs = results[name]['costs_per_period'].cumsum()
                                fig_costs.add_trace(go.Scatter(
                                    x=cumulative_costs.index,
                                    y=cumulative_costs.values,
                                    name=name,
                                    mode='lines'
                                ))
                        
                        fig_costs.update_layout(
                            title='Cumulative Transaction Costs',
                            xaxis_title='Date',
                            yaxis_title='Cumulative Costs (€)',
                            height=400
                        )
                        st.plotly_chart(fig_costs, use_container_width=True)
                else:
                    st.info("No cost data available. Ensure backtest was run with transaction costs enabled.")
            else:
                st.info("💡 **Transaction costs are disabled**. Enable them in the sidebar to see cost analysis.")
                st.markdown("""
                Cost analysis will show:
                - Total fees paid per strategy
                - Gross vs Net returns comparison
                - Cost drag impact (in % and basis points)
                - Cumulative costs over time
                
                **Maxblue Depot Cost Model:**
                - Commission: 0.25% per trade
                - Minimum: €8.90
                - Maximum: €58.90
                - Exchange fee: €2.00 per order
                """)
        
        with tab4:
            st.subheader("Optimal Portfolio Allocations")
            
            # Select strategy for detailed view
            selected_for_weights = st.selectbox(
                "Select strategy for detailed analysis",
                list(results.keys()),
                key='weights_strategy'
            )
            
            if selected_for_weights:
                weights_df = results[selected_for_weights]['weights']
                final_weights = weights_df.iloc[-1]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Current Allocation (Pie Chart)**")
                    fig_pie = plot_weights_pie(final_weights, f"{selected_for_weights} - Current Allocation")
                    st.plotly_chart(fig_pie, width="stretch")
                
                with col2:
                    st.markdown("**Top 10 Holdings**")
                    top_holdings = final_weights.sort_values(ascending=False).head(10)
                    holdings_df = pd.DataFrame({
                        'Asset': top_holdings.index,
                        'Weight (%)': top_holdings.values * 100
                    })
                    st.dataframe(
                        holdings_df.style.format({'Weight (%)': '{:.2f}'}),
                        width="stretch",
                        height=400
                    )
                
                # Weight evolution heatmap
                st.markdown("**Weight Evolution Over Time**")
                fig_heatmap = plot_weights_heatmap(weights_df, f"{selected_for_weights} - Weight Changes")
                st.plotly_chart(fig_heatmap, width="stretch")
                
                # Comparison of final weights
                st.markdown("**Compare Final Weights Across Strategies**")
                fig_final_weights = plot_final_weights(results)
                st.plotly_chart(fig_final_weights, width="stretch")
        
        with tab5:
            # Drawdown chart
            st.subheader("Drawdown Analysis")
            fig_drawdown = plot_drawdown(results)
            st.plotly_chart(fig_drawdown, width="stretch")
            
            # Risk metrics
            st.subheader("Risk Metrics")
            risk_cols = ['Volatility (%)', 'Max Drawdown (%)', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']
            st.dataframe(
                metrics_df[risk_cols].style.format({
                    'Volatility (%)': '{:.2f}',
                    'Max Drawdown (%)': '{:.2f}',
                    'Sharpe Ratio': '{:.2f}',
                    'Sortino Ratio': '{:.2f}',
                    'Calmar Ratio': '{:.2f}'
                }).background_gradient(subset=['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio'], cmap='RdYlGn'),
                width="stretch"
            )
            
            # Turnover analysis
            st.subheader("Trading Activity")
            
            fig_turnover = go.Figure()
            for name, result in results.items():
                fig_turnover.add_trace(go.Scatter(
                    x=result['turnover'].index,
                    y=result['turnover'].values,
                    name=name,
                    mode='lines'
                ))
            
            fig_turnover.update_layout(
                title='Portfolio Turnover Over Time',
                xaxis_title='Date',
                yaxis_title='Turnover',
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            
            st.plotly_chart(fig_turnover, width="stretch")
            
            # Turnover summary
            turnover_summary = metrics_df[['Avg Turnover', 'Total Turnover']].copy()
            st.dataframe(
                turnover_summary.style.format({
                    'Avg Turnover': '{:.4f}',
                    'Total Turnover': '{:.2f}'
                }),
                width="stretch"
            )
        
        with tab6:
            st.subheader("Strategy Information & Classification")
            
            st.markdown("""
            ### Strategy Types Explained
            
            - **📊 BENCHMARK**: Simple baseline strategies for comparison (Equal Weight, Buy & Hold)
            - **⚠️ LOOK-AHEAD**: Uses future information, not implementable in live trading (BCRP, Best Stock)
            - **✅ IMPLEMENTABLE**: Can be used in live trading, uses only past data
            - **⏱️ LAGGING**: Uses past data with lag (e.g., moving averages), still implementable
            - **📄 PAPER ONLY**: Theoretically interesting but impractical for live trading
            """)
            
            for name, result in results.items():
                sid = result['strategy_id']
                if sid in strategy_lookup:
                    s = strategy_lookup[sid]
                    
                    with st.expander(f"📋 {name} ({sid})"):
                        # Classification badges
                        badge_html = get_strategy_badge(s['strategy_type'], s['implementable'])
                        st.markdown(badge_html, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Metadata**")
                            st.write(f"**Paper**: {s['paper_ref']}")
                            st.write(f"**Complexity**: {s['complexity']}")
                            st.write(f"**Implementable**: {'✅ Yes' if s['implementable'] else '❌ No'}")
                        
                        with col2:
                            st.markdown("**Performance**")
                            metrics = metrics_data[name]
                            st.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
                            st.metric("Total Return", f"{metrics['Total Return (%)']:.2f}%")
                        
                        if s['description']:
                            st.markdown("**Description**")
                            st.info(s['description'])
    
    else:
        # Instructions when no results
        st.info("👈 Configure your backtest in the sidebar and click '🚀 Run Backtests' to begin")
        
        # Show available strategies
        st.header("📚 Available Strategies")
        
        strategies = list_strategies()
        
        # Group strategies by type
        st.subheader("Strategy Catalog")
        
        for s in strategies:
            badge_html = get_strategy_badge(s['strategy_type'], s['implementable'])
            
            with st.expander(f"{s['name']} ({s['id']})"):
                st.markdown(badge_html, unsafe_allow_html=True)
                st.write(f"**Paper**: {s['paper_ref']}")
                st.write(f"**Complexity**: {s['complexity']}")
                if s['description']:
                    st.info(s['description'])


if __name__ == "__main__":
    main()
