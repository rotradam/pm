import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent theme to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#e5e7eb"),
        title_font=dict(family="Inter, sans-serif", size=16, weight=600, color="#f3f4f6"),
        hoverlabel=dict(
            bgcolor="#1f2937",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#f3f4f6"
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

def plot_equity_curves(results: Dict[str, pd.Series], title: str = "Portfolio Performance") -> go.Figure:
    """Plot equity curves for multiple strategies."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Plotly
    
    for i, (name, series) in enumerate(results.items()):
        color = colors[i % len(colors)]
        
        # Determine line style
        dash = 'solid'
        width = 2
        if 'Benchmark' in name or 'EW' in name or 'BAH' in name:
            dash = 'dot'
            width = 2
            
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            name=name,
            mode='lines',
            line=dict(width=width, dash=dash, color=color),
            hovertemplate="%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified"
    )
    
    return apply_theme(fig)

def plot_drawdowns(results: Dict[str, pd.Series], title: str = "Drawdowns") -> go.Figure:
    """Plot drawdown curves."""
    fig = go.Figure()
    
    for name, series in results.items():
        cummax = series.cummax()
        drawdown = (series - cummax) / cummax * 100
        
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            name=name,
            mode='lines',
            fill='tozeroy',
            hovertemplate="%{y:.2f}%<extra></extra>"
        ))
        
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified"
    )
    
    return apply_theme(fig)

def plot_weights_heatmap(weights: pd.DataFrame, title: str = "Portfolio Weights") -> go.Figure:
    """Plot heatmap of portfolio weights."""
    # Use auto-scaling for better visibility of small weights
    z_max = weights.max().max() if not weights.empty else 1.0
    
    fig = go.Figure(data=go.Heatmap(
        z=weights.T.values,
        x=weights.index,
        y=weights.columns,
        colorscale='Viridis',
        zmin=0,
        zmax=z_max,
        colorbar=dict(title="Weight")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Asset",
        height=500
    )
    
    return apply_theme(fig)

def plot_allocation_pie(weights: pd.Series, title: str = None) -> go.Figure:
    """Plot pie chart of current portfolio allocation."""
    # Filter out zero weights for cleaner pie chart
    active_weights = weights[weights > 0.001]  # 0.1% threshold
    
    if active_weights.empty:
        # Fallback if everything is 0 (shouldn't happen usually)
        active_weights = weights
        
    fig = px.pie(
        values=active_weights.values,
        names=active_weights.index,
        title=title,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    # Move legend to bottom to prevent overlapping with chart or title
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=30 if title else 0, b=50) # Add margin for title if present, and bottom for legend
    )
    
    return apply_theme(fig)

def plot_metrics_table(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a styled table for metrics."""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Strategy</b>'] + [f'<b>{c}</b>' for c in metrics_df.columns],
            fill_color='#1f2937',
            align='left',
            font=dict(color='#f3f4f6', size=12),
            line_color='#374151'
        ),
        cells=dict(
            values=[metrics_df.index] + [metrics_df[c] for c in metrics_df.columns],
            fill_color='#111827',
            align='left',
            font=dict(color='#d1d5db', size=12),
            line_color='#374151',
            height=30
        )
    )])
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=len(metrics_df) * 35 + 40
    )
    
    return fig
