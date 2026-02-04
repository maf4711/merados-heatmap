#!/usr/bin/env python3
"""
meradOS Heatmap - Stock Market Intelligence
============================================
Umfassende Aktienanalyse mit:
- Interaktive Market Heatmap (Finviz-Style)
- Sektor-relatives Scoring
- DCF Fair Value Berechnung
- News & Sentiment Analyse
- Stock Screener
- Watchlist & Alerts

Start: streamlit run app.py
Vercel: streamlit run app.py --server.port $PORT
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import numpy as np

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="meradOS Heatmap",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/merados/heatmap',
        'Report a bug': 'https://github.com/merados/heatmap/issues',
        'About': '# meradOS Heatmap\nStock Market Intelligence Platform'
    }
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .metric-card-neutral {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1.5rem;
        border-radius: 16px;
        color: #1f2937;
        text-align: center;
    }

    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .score-strong-buy { background: #10b981; color: white; }
    .score-buy { background: #34d399; color: white; }
    .score-hold { background: #fbbf24; color: black; }
    .score-sell { background: #f97316; color: white; }
    .score-strong-sell { background: #ef4444; color: white; }

    .news-card {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f3f4f6;
        padding: 8px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background: transparent;
        border-radius: 8px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
    }

    div[data-testid="stSidebar"] * {
        color: white !important;
    }

    .sidebar-logo {
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .gainers-badge { background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; }
    .losers-badge { background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS & DATA
# ============================================================================

SECTOR_STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'INTC', 'AMD', 'IBM', 'QCOM', 'TXN', 'NOW', 'INTU', 'AMAT', 'MU', 'LRCX'],
    'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA', 'PYPL', 'COF', 'USB', 'PNC'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD', 'CVS', 'MDT', 'ISRG'],
    'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'TGT', 'LOW', 'TJX', 'BKNG', 'MAR', 'GM', 'F', 'ORLY', 'ROST'],
    'Consumer Defensive': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'MDLZ', 'CL', 'KHC', 'GIS', 'KMB', 'SYY', 'HSY', 'K', 'CAG', 'CPB'],
    'Communication': ['GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR', 'EA', 'TTWO', 'WBD', 'PARA', 'FOX', 'OMC'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'OXY', 'PSX', 'MPC', 'VLO', 'PXD', 'DVN', 'HES', 'HAL', 'BKR', 'FANG'],
    'Industrials': ['UPS', 'HON', 'UNP', 'BA', 'CAT', 'GE', 'RTX', 'DE', 'LMT', 'MMM', 'FDX', 'NSC', 'CSX', 'EMR', 'ITW'],
}

KNOWN_PEERS = {
    'AAPL': ['MSFT', 'GOOGL', 'META', 'AMZN', 'NVDA', 'TSM', 'AVGO', 'ORCL', 'CRM', 'ADBE'],
    'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'META', 'ORCL', 'CRM', 'SAP', 'ADBE', 'IBM', 'CSCO'],
    'GOOGL': ['META', 'MSFT', 'AMZN', 'AAPL', 'NFLX', 'SNAP', 'PINS', 'TTD', 'ROKU'],
    'META': ['GOOGL', 'SNAP', 'PINS', 'TTD', 'MSFT', 'NFLX', 'ROKU', 'AMZN'],
    'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO', 'TXN', 'MU', 'MRVL', 'TSM', 'ASML'],
    'TSLA': ['F', 'GM', 'RIVN', 'LCID', 'NIO', 'TM', 'HMC'],
    'JPM': ['BAC', 'WFC', 'C', 'GS', 'MS', 'USB', 'PNC'],
    'AMZN': ['WMT', 'TGT', 'COST', 'EBAY', 'SHOP', 'MELI'],
}

SCREENER_PRESETS = {
    'Value Stocks': {'max_pe': 15, 'min_dividend': 0.02, 'max_debt_equity': 1.0},
    'Growth Stocks': {'min_revenue_growth': 0.15, 'min_earnings_growth': 0.20},
    'Dividend Champions': {'min_dividend': 0.03, 'max_payout': 0.70},
    'Low Volatility': {'max_beta': 1.0, 'min_market_cap': 10e9},
    'Momentum': {'min_perf_6m': 0.10},
}

# ============================================================================
# DATA FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """Holt Aktiendaten von Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Berechne Änderung
        price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        prev = info.get('previousClose', price)
        change_pct = ((price - prev) / prev * 100) if prev and prev > 0 else 0

        return {
            'ticker': ticker.upper(),
            'name': info.get('longName') or info.get('shortName', ticker),
            'price': price,
            'previous_close': prev,
            'change': price - prev if prev else 0,
            'change_percent': change_pct,
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'profit_margin': info.get('profitMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'free_cashflow': info.get('freeCashflow'),
            'recommendation': info.get('recommendationKey'),
            'target_mean': info.get('targetMeanPrice'),
            'target_high': info.get('targetHighPrice'),
            'target_low': info.get('targetLowPrice'),
            'analyst_count': info.get('numberOfAnalystOpinions'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            '52w_high': info.get('fiftyTwoWeekHigh'),
            '52w_low': info.get('fiftyTwoWeekLow'),
            'beta': info.get('beta'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume'),
            'short_ratio': info.get('shortRatio'),
            'payout_ratio': info.get('payoutRatio'),
        }
    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}


@st.cache_data(ttl=300)
def fetch_historical_data(ticker: str, period: str = '1y') -> pd.DataFrame:
    """Holt historische Kursdaten"""
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period=period)
    except:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def fetch_news(ticker: str) -> List[Dict]:
    """Holt News für eine Aktie"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        return news[:10] if news else []
    except:
        return []


@st.cache_data(ttl=600)
def fetch_sector_data(sector_stocks: Dict[str, List[str]], max_per_sector: int = 12) -> pd.DataFrame:
    """Holt Daten für alle Sektor-Aktien"""
    all_data = []

    for sector, tickers in sector_stocks.items():
        for ticker in tickers[:max_per_sector]:
            try:
                data = fetch_stock_data(ticker)
                if 'error' not in data and data.get('price'):
                    all_data.append({
                        'Ticker': ticker,
                        'Name': (data.get('name', ticker) or ticker)[:25],
                        'Sector': sector,
                        'Price': data.get('price', 0),
                        'Change %': data.get('change_percent', 0),
                        'Market Cap': data.get('market_cap', 0),
                        'P/E': data.get('pe_ratio'),
                        'Volume': data.get('volume', 0),
                        'Dividend %': (data.get('dividend_yield') or 0) * 100,
                    })
            except:
                continue

    return pd.DataFrame(all_data)


def calculate_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """Berechnet den Score für eine Aktie"""
    scores = {}

    # Valuation (25 Punkte)
    val_score = 0
    pe = data.get('pe_ratio')
    if pe and pe > 0:
        if pe < 15: val_score += 10
        elif pe < 20: val_score += 7
        elif pe < 25: val_score += 5
        elif pe < 35: val_score += 2

    peg = data.get('peg_ratio')
    if peg and 0 < peg < 2:
        val_score += 8 if peg < 1 else 5

    pb = data.get('price_to_book')
    if pb and 0 < pb < 3:
        val_score += 4 if pb < 2 else 2

    scores['valuation'] = min(25, val_score)

    # Profitability (25 Punkte)
    prof_score = 0
    pm = data.get('profit_margin')
    if pm:
        if pm > 0.20: prof_score += 10
        elif pm > 0.10: prof_score += 6
        elif pm > 0: prof_score += 3

    roe = data.get('roe')
    if roe:
        if roe > 0.20: prof_score += 10
        elif roe > 0.15: prof_score += 7
        elif roe > 0.10: prof_score += 4

    scores['profitability'] = min(25, prof_score)

    # Growth (20 Punkte)
    growth_score = 0
    rg = data.get('revenue_growth')
    if rg:
        if rg > 0.20: growth_score += 10
        elif rg > 0.10: growth_score += 6
        elif rg > 0: growth_score += 3

    eg = data.get('earnings_growth')
    if eg:
        if eg > 0.20: growth_score += 10
        elif eg > 0.10: growth_score += 6
        elif eg > 0: growth_score += 3

    scores['growth'] = min(20, growth_score)

    # Financial Health (15 Punkte)
    health_score = 0
    de = data.get('debt_to_equity')
    if de is not None:
        if de < 0.5: health_score += 7
        elif de < 1.0: health_score += 5
        elif de < 2.0: health_score += 2

    cr = data.get('current_ratio')
    if cr and cr > 1.5:
        health_score += 5

    if data.get('free_cashflow') and data['free_cashflow'] > 0:
        health_score += 3

    scores['financial_health'] = min(15, health_score)

    # Dividend (10 Punkte)
    div_score = 0
    dy = data.get('dividend_yield')
    if dy:
        if dy > 0.04: div_score += 7
        elif dy > 0.02: div_score += 5
        elif dy > 0: div_score += 3

    scores['dividend'] = min(10, div_score)

    # Analyst (5 Punkte)
    analyst_score = 0
    rec = data.get('recommendation')
    if rec:
        rec_lower = rec.lower()
        if 'buy' in rec_lower: analyst_score = 5 if 'strong' in rec_lower else 4
        elif 'hold' in rec_lower: analyst_score = 2.5

    scores['analyst'] = analyst_score

    # Total
    total = sum(scores.values())
    scores['total'] = total
    scores['percentage'] = round((total / 100) * 100, 1)

    # Rating
    pct = scores['percentage']
    if pct >= 75:
        scores['rating'] = 'STRONG BUY'
        scores['color'] = '#10b981'
        scores['class'] = 'score-strong-buy'
    elif pct >= 60:
        scores['rating'] = 'BUY'
        scores['color'] = '#34d399'
        scores['class'] = 'score-buy'
    elif pct >= 45:
        scores['rating'] = 'HOLD'
        scores['color'] = '#fbbf24'
        scores['class'] = 'score-hold'
    elif pct >= 30:
        scores['rating'] = 'SELL'
        scores['color'] = '#f97316'
        scores['class'] = 'score-sell'
    else:
        scores['rating'] = 'STRONG SELL'
        scores['color'] = '#ef4444'
        scores['class'] = 'score-strong-sell'

    return scores


def calculate_dcf(data: Dict[str, Any]) -> Dict[str, Any]:
    """DCF Fair Value Berechnung"""
    fcf = data.get('free_cashflow')
    market_cap = data.get('market_cap')
    price = data.get('price')

    if not fcf or not market_cap or not price or fcf <= 0 or price <= 0:
        return {'error': 'Nicht genug Daten für DCF'}

    shares = market_cap / price
    growth_rate = data.get('revenue_growth') or 0.05
    growth_rate = max(-0.10, min(0.30, growth_rate))
    discount_rate = 0.10
    terminal_growth = 0.025
    years = 5

    projected_fcf = []
    current_fcf = fcf
    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth_rate)
        growth_rate = growth_rate * 0.9
        projected_fcf.append(current_fcf)

    pv_fcf = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(projected_fcf))

    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount_rate) ** years)

    enterprise_value = pv_fcf + pv_terminal
    fair_value = enterprise_value / shares if shares > 0 else 0
    upside = ((fair_value / price) - 1) * 100

    return {
        'fair_value': round(fair_value, 2),
        'current_price': price,
        'upside_percent': round(upside, 1),
        'verdict': 'UNTERBEWERTET' if upside > 15 else ('ÜBERBEWERTET' if upside < -15 else 'FAIR')
    }


# ============================================================================
# CHART FUNCTIONS
# ============================================================================

def create_treemap(df: pd.DataFrame) -> go.Figure:
    """Erstellt eine Treemap-Heatmap"""
    if df.empty:
        return go.Figure()

    df['Size'] = df['Market Cap'].fillna(1e9).clip(lower=1e9)

    fig = px.treemap(
        df,
        path=['Sector', 'Ticker'],
        values='Size',
        color='Change %',
        color_continuous_scale=[
            [0, '#ef4444'],
            [0.25, '#f97316'],
            [0.5, '#fbbf24'],
            [0.75, '#34d399'],
            [1, '#10b981']
        ],
        range_color=[-5, 5],
        hover_data={
            'Name': True,
            'Price': ':.2f',
            'Change %': ':.2f',
            'P/E': ':.1f',
            'Size': False,
        },
    )

    fig.update_layout(
        height=650,
        margin=dict(t=30, l=10, r=10, b=10),
        coloraxis_colorbar=dict(
            title='Change %',
            tickformat='.1f',
            ticksuffix='%',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    fig.update_traces(
        textinfo='label+text',
        texttemplate='<b>%{label}</b><br>%{color:.2f}%',
        hovertemplate='<b>%{label}</b><br>' +
                      '%{customdata[0]}<br>' +
                      'Price: $%{customdata[1]:.2f}<br>' +
                      'Change: %{color:.2f}%<br>' +
                      'P/E: %{customdata[3]:.1f}<extra></extra>'
    )

    return fig


def create_sector_performance(df: pd.DataFrame) -> go.Figure:
    """Sektor-Performance Balkendiagramm"""
    if df.empty:
        return go.Figure()

    sector_perf = df.groupby('Sector')['Change %'].mean().sort_values(ascending=True)
    colors = ['#10b981' if x > 0 else '#ef4444' for x in sector_perf.values]

    fig = go.Figure(go.Bar(
        x=sector_perf.values,
        y=sector_perf.index,
        orientation='h',
        marker_color=colors,
        text=[f'{x:+.2f}%' for x in sector_perf.values],
        textposition='outside',
        textfont=dict(size=12, color='#374151')
    ))

    fig.update_layout(
        title=dict(text='Sector Performance', font=dict(size=16)),
        xaxis_title='Average Change %',
        yaxis_title='',
        height=350,
        margin=dict(l=120, r=60, t=50, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='#e5e7eb', zerolinecolor='#9ca3af'),
    )

    return fig


def create_price_chart(ticker: str, period: str = '1y') -> go.Figure:
    """Erstellt Preischart"""
    hist = fetch_historical_data(ticker, period)
    if hist.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist['Open'], high=hist['High'],
        low=hist['Low'], close=hist['Close'], name='Price',
        increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    ), row=1, col=1)

    # SMAs
    if len(hist) > 20:
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], name='SMA 20',
                                 line=dict(color='#f97316', width=1.5)), row=1, col=1)
    if len(hist) > 50:
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name='SMA 50',
                                 line=dict(color='#3b82f6', width=1.5)), row=1, col=1)

    # Volume
    colors = ['#10b981' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else '#ef4444'
              for i in range(len(hist))]
    fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume',
                         marker_color=colors, opacity=0.7), row=2, col=1)

    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_comparison_chart(tickers: List[str], period: str = '6mo') -> go.Figure:
    """Erstellt Vergleichschart (normalisiert)"""
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
        title='Performance Comparison (Normalized to 100)',
        xaxis_title='Date',
        yaxis_title='Normalized Price',
        height=400,
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.markdown('<div class="sidebar-logo">🔥 meradOS</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🗺️ Heatmap", "📊 Analyse", "🔍 Screener", "📰 News", "📋 Watchlist"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Search")
quick_ticker = st.sidebar.text_input("Ticker", placeholder="AAPL, MSFT...")

if quick_ticker:
    st.sidebar.markdown("---")
    data = fetch_stock_data(quick_ticker.upper())
    if 'error' not in data:
        change = data.get('change_percent', 0)
        color = '#10b981' if change >= 0 else '#ef4444'
        st.sidebar.markdown(f"""
        **{data.get('name', quick_ticker)[:20]}**

        Price: **${data.get('price', 0):.2f}**

        Change: <span style="color:{color}">{change:+.2f}%</span>
        """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<small style="color: #9ca3af;">
**meradOS Heatmap** v2.0

Data: Yahoo Finance
100% Free & Open Source

[GitHub](https://github.com/merados/heatmap)
</small>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN PAGES
# ============================================================================

if page == "🗺️ Heatmap":
    st.markdown('<p class="main-header">🔥 meradOS Heatmap</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time Market Intelligence • Sector Performance • Stock Screening</p>', unsafe_allow_html=True)

    with st.spinner('Loading market data...'):
        df = fetch_sector_data(SECTOR_STOCKS, max_per_sector=10)

    if not df.empty:
        # Summary Cards
        col1, col2, col3, col4, col5 = st.columns(5)

        gainers = len(df[df['Change %'] > 0])
        losers = len(df[df['Change %'] < 0])
        avg_change = df['Change %'].mean()
        best = df.loc[df['Change %'].idxmax()] if not df.empty else None
        worst = df.loc[df['Change %'].idxmin()] if not df.empty else None

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: 700;">{gainers}</div>
                <div>📈 Gainers</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);">
                <div style="font-size: 2rem; font-weight: 700;">{losers}</div>
                <div>📉 Losers</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            color = '#10b981' if avg_change >= 0 else '#ef4444'
            st.markdown(f"""
            <div class="metric-card-neutral">
                <div style="font-size: 2rem; font-weight: 700; color: {color};">{avg_change:+.2f}%</div>
                <div>Ø Change</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            if best is not None:
                st.markdown(f"""
                <div class="metric-card-neutral">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #10b981;">{best['Ticker']}</div>
                    <div>🏆 +{best['Change %']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        with col5:
            if worst is not None:
                st.markdown(f"""
                <div class="metric-card-neutral">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #ef4444;">{worst['Ticker']}</div>
                    <div>📉 {worst['Change %']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Treemap
        fig = create_treemap(df)
        st.plotly_chart(fig, use_container_width=True)

        # Bottom Section
        col1, col2 = st.columns([1, 1])

        with col1:
            fig = create_sector_performance(df)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Top & Flop")

            tab1, tab2 = st.tabs(["🟢 Top 10", "🔴 Flop 10"])

            with tab1:
                top = df.nlargest(10, 'Change %')[['Ticker', 'Name', 'Change %', 'Price', 'P/E']]
                st.dataframe(top, hide_index=True, use_container_width=True)

            with tab2:
                bottom = df.nsmallest(10, 'Change %')[['Ticker', 'Name', 'Change %', 'Price', 'P/E']]
                st.dataframe(bottom, hide_index=True, use_container_width=True)


elif page == "📊 Analyse":
    st.markdown('<p class="main-header">📊 Stock Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Enter Ticker", value="AAPL", help="e.g., AAPL, MSFT, GOOGL").upper()
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

    if ticker:
        with st.spinner(f'Loading {ticker}...'):
            data = fetch_stock_data(ticker)

        if 'error' in data:
            st.error(f"Error: {data.get('error')}")
        else:
            scores = calculate_score(data)
            dcf = calculate_dcf(data)

            # Header
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {data.get('name', ticker)}")
                st.caption(f"{data.get('sector', '')} • {data.get('industry', '')}")

            with col2:
                price = data.get('price', 0)
                change = data.get('change_percent', 0)
                st.metric("Price", f"${price:.2f}", f"{change:+.2f}%")

            with col3:
                st.markdown(f"""
                <div class="score-badge {scores['class']}">{scores['percentage']:.0f}% • {scores['rating']}</div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Chart", "📊 Metrics", "💎 Valuation", "👥 Peers"])

            with tab1:
                fig = create_price_chart(ticker, period)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("#### 💰 Valuation")
                    st.metric("P/E Ratio", f"{data.get('pe_ratio', 'N/A'):.1f}" if data.get('pe_ratio') else "N/A")
                    st.metric("Forward P/E", f"{data.get('forward_pe', 'N/A'):.1f}" if data.get('forward_pe') else "N/A")
                    st.metric("PEG Ratio", f"{data.get('peg_ratio', 'N/A'):.2f}" if data.get('peg_ratio') else "N/A")
                    st.metric("P/B Ratio", f"{data.get('price_to_book', 'N/A'):.2f}" if data.get('price_to_book') else "N/A")

                with col2:
                    st.markdown("#### 📊 Profitability")
                    pm = data.get('profit_margin')
                    st.metric("Profit Margin", f"{pm*100:.1f}%" if pm else "N/A")
                    roe = data.get('roe')
                    st.metric("ROE", f"{roe*100:.1f}%" if roe else "N/A")
                    rg = data.get('revenue_growth')
                    st.metric("Revenue Growth", f"{rg*100:.1f}%" if rg else "N/A")

                with col3:
                    st.markdown("#### 🏦 Health")
                    st.metric("Debt/Equity", f"{data.get('debt_to_equity', 'N/A'):.1f}" if data.get('debt_to_equity') else "N/A")
                    st.metric("Current Ratio", f"{data.get('current_ratio', 'N/A'):.2f}" if data.get('current_ratio') else "N/A")
                    fcf = data.get('free_cashflow')
                    st.metric("Free Cash Flow", f"${fcf/1e9:.1f}B" if fcf else "N/A")

            with tab3:
                if 'error' in dcf:
                    st.warning(dcf['error'])
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("DCF Fair Value", f"${dcf['fair_value']:.2f}")
                    with col2:
                        st.metric("Current Price", f"${dcf['current_price']:.2f}")
                    with col3:
                        st.metric("Upside", f"{dcf['upside_percent']:+.1f}%")

                    verdict_colors = {'UNTERBEWERTET': '#10b981', 'ÜBERBEWERTET': '#ef4444', 'FAIR': '#fbbf24'}
                    st.markdown(f"""
                    <div style="background: {verdict_colors.get(dcf['verdict'], '#fbbf24')};
                                padding: 1rem; border-radius: 12px; text-align: center; color: white; margin-top: 1rem;">
                        <h3 style="margin: 0;">{dcf['verdict']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

            with tab4:
                peers = KNOWN_PEERS.get(ticker, [])
                if peers:
                    compare_tickers = [ticker] + peers[:5]
                    fig = create_comparison_chart(compare_tickers, '6mo')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No peer data available for this ticker.")


elif page == "🔍 Screener":
    st.markdown('<p class="main-header">🔍 Stock Screener</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("#### Presets")
        preset = st.selectbox("Quick Filter", ["Custom"] + list(SCREENER_PRESETS.keys()))

        st.markdown("#### Filters")
        max_pe = st.slider("Max P/E", 0, 100, 50)
        min_div = st.slider("Min Dividend %", 0.0, 10.0, 0.0, 0.5)
        min_growth = st.slider("Min Revenue Growth %", -50, 100, 0)

    with col2:
        with st.spinner('Screening stocks...'):
            df = fetch_sector_data(SECTOR_STOCKS, max_per_sector=8)

        if not df.empty:
            # Apply filters
            filtered = df.copy()

            if max_pe < 50:
                filtered = filtered[filtered['P/E'].fillna(999) <= max_pe]

            if min_div > 0:
                filtered = filtered[filtered['Dividend %'] >= min_div]

            st.markdown(f"**Found {len(filtered)} stocks matching criteria**")

            st.dataframe(
                filtered.sort_values('Change %', ascending=False),
                use_container_width=True,
                hide_index=True
            )


elif page == "📰 News":
    st.markdown('<p class="main-header">📰 Market News</p>', unsafe_allow_html=True)

    ticker = st.text_input("Ticker for News", value="AAPL").upper()

    if ticker:
        with st.spinner('Loading news...'):
            news = fetch_news(ticker)

        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-card">
                    <strong>{item.get('title', 'No title')}</strong><br>
                    <small style="color: #6b7280;">{item.get('publisher', '')} • {datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')}</small>
                    <br><a href="{item.get('link', '#')}" target="_blank">Read more →</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No news available for this ticker.")


elif page == "📋 Watchlist":
    st.markdown('<p class="main-header">📋 Watchlist</p>', unsafe_allow_html=True)

    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']

    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add Ticker", placeholder="AMZN")
    with col2:
        if st.button("➕ Add", use_container_width=True):
            if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker.upper())
                st.rerun()

    st.markdown("---")

    if st.session_state.watchlist:
        watchlist_data = []
        for ticker in st.session_state.watchlist:
            data = fetch_stock_data(ticker)
            if 'error' not in data:
                scores = calculate_score(data)
                watchlist_data.append({
                    'Ticker': ticker,
                    'Name': (data.get('name', ticker) or ticker)[:25],
                    'Price': f"${data.get('price', 0):.2f}",
                    'Change': f"{data.get('change_percent', 0):+.2f}%",
                    'Score': f"{scores['percentage']:.0f}%",
                    'Rating': scores['rating'],
                })

        if watchlist_data:
            df = pd.DataFrame(watchlist_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            fig = create_comparison_chart(st.session_state.watchlist[:8], '3mo')
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #9ca3af; padding: 1rem;">
    <small>🔥 <strong>meradOS Heatmap</strong> • Built with Streamlit & Plotly • Data: Yahoo Finance •
    <a href="https://github.com/merados/heatmap" style="color: #667eea;">GitHub</a></small>
</div>
""", unsafe_allow_html=True)
