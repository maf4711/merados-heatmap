"""
meradOS Heatmap - Chart Functions
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List


def create_treemap(df: pd.DataFrame) -> go.Figure:
    """Erstellt Heatmap Treemap"""
    if df.empty:
        return go.Figure()

    df['Size'] = df['Market Cap'].fillna(1e9).clip(lower=1e9)

    fig = px.treemap(
        df,
        path=['Sector', 'Ticker'],
        values='Size',
        color='Change %',
        color_continuous_scale=[
            [0, '#ef4444'], [0.25, '#f97316'], [0.5, '#fbbf24'],
            [0.75, '#34d399'], [1, '#10b981']
        ],
        range_color=[-5, 5],
        hover_data={'Name': True, 'Price': ':.2f', 'Change %': ':.2f', 'P/E': ':.1f', 'Size': False},
    )

    fig.update_layout(
        height=650,
        margin=dict(t=30, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title='Change %', tickformat='.1f', ticksuffix='%'),
        paper_bgcolor='rgba(0,0,0,0)',
    )

    fig.update_traces(
        textinfo='label+text',
        texttemplate='<b>%{label}</b><br>%{color:.2f}%',
    )

    return fig


def create_sector_chart(df: pd.DataFrame) -> go.Figure:
    """Sektor Performance"""
    if df.empty:
        return go.Figure()

    sector_perf = df.groupby('Sector')['Change %'].mean().sort_values(ascending=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in sector_perf.values]

    fig = go.Figure(go.Bar(
        x=sector_perf.values, y=sector_perf.index, orientation='h',
        marker_color=colors,
        text=[f'{x:+.2f}%' for x in sector_perf.values],
        textposition='outside'
    ))

    fig.update_layout(
        title='Sector Performance',
        height=350,
        margin=dict(l=120, r=60, t=50, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_price_chart(ticker: str, period: str = '1y') -> go.Figure:
    """Price Chart mit Volume"""
    # Import here to avoid circular dependency
    from utils import fetch_historical_data

    hist = fetch_historical_data(ticker, period)
    if hist.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist['Open'], high=hist['High'],
        low=hist['Low'], close=hist['Close'], name='Price',
        increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    ), row=1, col=1)

    if len(hist) > 20:
        hist['SMA20'] = hist['Close'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], name='SMA 20',
                                 line=dict(color='#f97316', width=1.5)), row=1, col=1)
    if len(hist) > 50:
        hist['SMA50'] = hist['Close'].rolling(50).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name='SMA 50',
                                 line=dict(color='#3b82f6', width=1.5)), row=1, col=1)

    colors = ['#10b981' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else '#ef4444'
              for i in range(len(hist))]
    fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume',
                         marker_color=colors, opacity=0.7), row=2, col=1)

    fig.update_layout(
        height=500, xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_comparison_chart(tickers: List[str], period: str = '6mo') -> go.Figure:
    """Vergleichs-Chart"""
    # Import here to avoid circular dependency
    from utils import fetch_historical_data

    fig = go.Figure()
    colors = px.colors.qualitative.Set2

    for i, ticker in enumerate(tickers):
        hist = fetch_historical_data(ticker, period)
        if not hist.empty:
            normalized = (hist['Close'] / hist['Close'].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=hist.index, y=normalized, name=ticker, mode='lines',
                line=dict(color=colors[i % len(colors)], width=2)
            ))

    fig.update_layout(
        title='Performance Comparison (Normalized)',
        height=400, hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig
