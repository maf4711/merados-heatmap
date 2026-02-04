#!/usr/bin/env python3
"""
meradOS Heatmap v3.0 - Stock Market Intelligence
=================================================
Features:
- Multi-Source Data (FMP, Finnhub, Alpha Vantage, yfinance)
- SQLite Cache für Performance
- Data Quality Scores
- Interactive Heatmap (Finviz-Style)
- News & Sentiment Analysis
- Stock Screener
- DCF Fair Value

Start: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

warnings.filterwarnings('ignore')

# Import Multi-Source Data Providers
try:
    from data_providers import (
        MultiSourceFetcher, get_stock_data, get_quote, get_news, get_sentiment,
        get_cache_stats, get_api_status, clear_cache, DataSource, DataQuality,
        FMP_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY
    )
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False
    import yfinance as yf

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="meradOS Heatmap",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/maf4711/merados-heatmap',
        'Report a bug': 'https://github.com/maf4711/merados-heatmap/issues',
        'About': '# meradOS Heatmap v3.0\nMulti-Source Stock Market Intelligence'
    }
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

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

    .quality-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .quality-high { background: #dcfce7; color: #166534; }
    .quality-medium { background: #fef3c7; color: #92400e; }
    .quality-low { background: #fee2e2; color: #991b1b; }

    .source-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        background: #e5e7eb;
        color: #374151;
        margin-left: 8px;
    }

    .news-card {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }

    .sentiment-bullish { color: #10b981; }
    .sentiment-bearish { color: #ef4444; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
    }

    div[data-testid="stSidebar"] * {
        color: white !important;
    }

    .api-status {
        padding: 8px 12px;
        border-radius: 8px;
        margin: 4px 0;
        font-size: 0.85rem;
    }

    .api-active { background: rgba(16, 185, 129, 0.2); }
    .api-inactive { background: rgba(239, 68, 68, 0.2); }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS
# ============================================================================

SECTOR_STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'INTC', 'AMD', 'IBM', 'QCOM', 'TXN'],
    'Financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA', 'PYPL'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD'],
    'Consumer': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'WMT', 'TGT', 'COST', 'PG', 'KO', 'PEP'],
    'Communication': ['GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA', 'VZ', 'T', 'TMUS'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'OXY', 'PSX', 'MPC', 'VLO'],
    'Industrials': ['UPS', 'HON', 'UNP', 'BA', 'CAT', 'GE', 'RTX', 'DE', 'LMT'],
}

KNOWN_PEERS = {
    'AAPL': ['MSFT', 'GOOGL', 'META', 'AMZN', 'NVDA'],
    'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'META', 'ORCL'],
    'GOOGL': ['META', 'MSFT', 'AMZN', 'AAPL', 'NFLX'],
    'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO', 'TSM'],
    'TSLA': ['F', 'GM', 'RIVN', 'NIO', 'TM'],
    'JPM': ['BAC', 'WFC', 'C', 'GS', 'MS'],
    'AMZN': ['WMT', 'TGT', 'COST', 'EBAY', 'SHOP'],
}

# ============================================================================
# DATA FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def fetch_stock_data_cached(ticker: str) -> tuple:
    """Cached wrapper für Stock Data"""
    if MULTI_SOURCE_AVAILABLE:
        data, quality = get_stock_data(ticker)
        return data, quality
    else:
        # Fallback zu yfinance
        return fetch_yfinance_data(ticker), {'overall_score': 70, 'quote': {'source': 'Yahoo Finance'}}


def fetch_yfinance_data(ticker: str) -> Dict:
    """Fallback: yfinance direkt"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        prev = info.get('previousClose', price)
        change_pct = ((price - prev) / prev * 100) if prev else 0

        return {
            'ticker': ticker.upper(),
            'name': info.get('longName') or info.get('shortName', ticker),
            'price': price,
            'change_percent': change_pct,
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'dividend_yield': info.get('dividendYield'),
            'profit_margin': info.get('profitMargins'),
            'roe': info.get('returnOnEquity'),
            'revenue_growth': info.get('revenueGrowth'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'free_cashflow': info.get('freeCashflow'),
            'recommendation': info.get('recommendationKey'),
            'target_mean': info.get('targetMeanPrice'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            '52w_high': info.get('fiftyTwoWeekHigh'),
            '52w_low': info.get('fiftyTwoWeekLow'),
            'beta': info.get('beta'),
        }
    except:
        return {'ticker': ticker, 'error': 'Failed to fetch'}


@st.cache_data(ttl=300)
def fetch_historical_data(ticker: str, period: str = '1y') -> pd.DataFrame:
    """Holt historische Daten"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        return stock.history(period=period)
    except:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def fetch_sector_data(sector_stocks: Dict, max_per_sector: int = 10) -> pd.DataFrame:
    """Holt Daten für Heatmap"""
    all_data = []

    for sector, tickers in sector_stocks.items():
        for ticker in tickers[:max_per_sector]:
            try:
                data, quality = fetch_stock_data_cached(ticker)
                if data and data.get('price'):
                    all_data.append({
                        'Ticker': ticker,
                        'Name': (data.get('name', ticker) or ticker)[:25],
                        'Sector': sector,
                        'Price': data.get('price', 0),
                        'Change %': data.get('change_percent', 0),
                        'Market Cap': data.get('market_cap', 0),
                        'P/E': data.get('pe_ratio'),
                        'Quality': quality.get('overall_score', 70) if isinstance(quality, dict) else 70,
                    })
            except:
                continue

    return pd.DataFrame(all_data)


def calculate_score(data: Dict) -> Dict:
    """Berechnet Investment Score"""
    scores = {}

    # Valuation (25)
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

    # Profitability (25)
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

    # Growth (20)
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

    # Health (15)
    health_score = 0
    de = data.get('debt_to_equity')
    if de is not None:
        if de < 0.5: health_score += 7
        elif de < 1.0: health_score += 5
        elif de < 2.0: health_score += 2

    if data.get('current_ratio') and data['current_ratio'] > 1.5:
        health_score += 5

    if data.get('free_cashflow') and data['free_cashflow'] > 0:
        health_score += 3

    scores['health'] = min(15, health_score)

    # Dividend (10)
    div_score = 0
    dy = data.get('dividend_yield')
    if dy:
        if dy > 0.04: div_score += 7
        elif dy > 0.02: div_score += 5
        elif dy > 0: div_score += 3
    scores['dividend'] = min(10, div_score)

    # Analyst (5)
    analyst_score = 0
    rec = data.get('recommendation')
    if rec:
        if 'buy' in rec.lower(): analyst_score = 5 if 'strong' in rec.lower() else 4
        elif 'hold' in rec.lower(): analyst_score = 2.5
    scores['analyst'] = analyst_score

    # Total
    total = sum(scores.values())
    scores['total'] = total
    scores['percentage'] = round((total / 100) * 100, 1)

    if scores['percentage'] >= 75:
        scores['rating'] = 'STRONG BUY'
        scores['color'] = '#10b981'
    elif scores['percentage'] >= 60:
        scores['rating'] = 'BUY'
        scores['color'] = '#34d399'
    elif scores['percentage'] >= 45:
        scores['rating'] = 'HOLD'
        scores['color'] = '#fbbf24'
    elif scores['percentage'] >= 30:
        scores['rating'] = 'SELL'
        scores['color'] = '#f97316'
    else:
        scores['rating'] = 'STRONG SELL'
        scores['color'] = '#ef4444'

    return scores


def calculate_dcf(data: Dict) -> Dict:
    """DCF Fair Value"""
    fcf = data.get('free_cashflow')
    market_cap = data.get('market_cap')
    price = data.get('price')

    if not fcf or not market_cap or not price or fcf <= 0 or price <= 0:
        return {'error': 'Insufficient data for DCF'}

    shares = market_cap / price
    growth = data.get('revenue_growth') or 0.05
    growth = max(-0.10, min(0.30, growth))
    discount = 0.10
    terminal = 0.025

    projected = []
    current = fcf
    for _ in range(5):
        current *= (1 + growth)
        growth *= 0.9
        projected.append(current)

    pv_fcf = sum(cf / ((1 + discount) ** (i + 1)) for i, cf in enumerate(projected))
    terminal_value = projected[-1] * (1 + terminal) / (discount - terminal)
    pv_terminal = terminal_value / ((1 + discount) ** 5)

    fair_value = (pv_fcf + pv_terminal) / shares
    upside = ((fair_value / price) - 1) * 100

    return {
        'fair_value': round(fair_value, 2),
        'current_price': price,
        'upside_percent': round(upside, 1),
        'verdict': 'UNDERVALUED' if upside > 15 else ('OVERVALUED' if upside < -15 else 'FAIR VALUE')
    }


# ============================================================================
# CHART FUNCTIONS
# ============================================================================

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


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.markdown('<div style="font-size:1.8rem;font-weight:700;text-align:center;padding:1rem;background:linear-gradient(90deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🔥 meradOS</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🗺️ Heatmap", "📊 Analysis", "📰 News", "🔍 Screener", "📋 Watchlist", "⚙️ Settings"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Search")
quick_ticker = st.sidebar.text_input("Ticker", placeholder="AAPL, MSFT...")

if quick_ticker:
    data, quality = fetch_stock_data_cached(quick_ticker.upper())
    if data and data.get('price'):
        change = data.get('change_percent', 0)
        color = '#10b981' if change >= 0 else '#ef4444'
        q_score = quality.get('overall_score', 70) if isinstance(quality, dict) else 70
        st.sidebar.markdown(f"""
        **{data.get('name', quick_ticker)[:20]}**

        Price: **${data.get('price', 0):.2f}**

        Change: <span style="color:{color}">{change:+.2f}%</span>

        Data Quality: **{q_score:.0f}/100**
        """, unsafe_allow_html=True)

# API Status in Sidebar
if MULTI_SOURCE_AVAILABLE:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Data Sources")

    api_status = get_api_status()
    for api, info in api_status.items():
        status = "✅" if info['available'] else "❌"
        css_class = "api-active" if info['available'] else "api-inactive"
        st.sidebar.markdown(f'<div class="api-status {css_class}">{status} {api.upper()}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<small style="color:#9ca3af;">
**meradOS Heatmap** v3.0

Multi-Source Data Engine
SQLite Cache • Quality Scores

[GitHub](https://github.com/maf4711/merados-heatmap)
</small>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN PAGES
# ============================================================================

if page == "🗺️ Heatmap":
    st.markdown('<p class="main-header">🔥 meradOS Heatmap</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Source Market Intelligence • Real-time Data Quality Tracking</p>', unsafe_allow_html=True)

    with st.spinner('Loading market data...'):
        df = fetch_sector_data(SECTOR_STOCKS, max_per_sector=10)

    if not df.empty:
        # Summary Cards
        col1, col2, col3, col4, col5 = st.columns(5)

        gainers = len(df[df['Change %'] > 0])
        losers = len(df[df['Change %'] < 0])
        avg_change = df['Change %'].mean()
        avg_quality = df['Quality'].mean()
        best = df.loc[df['Change %'].idxmax()] if not df.empty else None

        with col1:
            st.markdown(f'<div class="metric-card"><div style="font-size:2rem;font-weight:700;">{gainers}</div><div>📈 Gainers</div></div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f'<div class="metric-card" style="background:linear-gradient(135deg,#ef4444,#dc2626);"><div style="font-size:2rem;font-weight:700;">{losers}</div><div>📉 Losers</div></div>', unsafe_allow_html=True)

        with col3:
            color = '#10b981' if avg_change >= 0 else '#ef4444'
            st.markdown(f'<div class="metric-card-neutral"><div style="font-size:2rem;font-weight:700;color:{color};">{avg_change:+.2f}%</div><div>Ø Change</div></div>', unsafe_allow_html=True)

        with col4:
            q_class = 'quality-high' if avg_quality >= 80 else ('quality-medium' if avg_quality >= 60 else 'quality-low')
            st.markdown(f'<div class="metric-card-neutral"><div style="font-size:2rem;font-weight:700;">{avg_quality:.0f}</div><div>Data Quality</div></div>', unsafe_allow_html=True)

        with col5:
            if best is not None:
                st.markdown(f'<div class="metric-card-neutral"><div style="font-size:1.5rem;font-weight:700;color:#10b981;">{best["Ticker"]}</div><div>🏆 +{best["Change %"]:.2f}%</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Treemap
        fig = create_treemap(df)
        st.plotly_chart(fig, use_container_width=True)

        # Bottom Section
        col1, col2 = st.columns([1, 1])

        with col1:
            fig = create_sector_chart(df)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Top & Flop")
            tab1, tab2 = st.tabs(["🟢 Top 10", "🔴 Flop 10"])

            with tab1:
                top = df.nlargest(10, 'Change %')[['Ticker', 'Name', 'Change %', 'Price', 'Quality']]
                st.dataframe(top, hide_index=True, use_container_width=True)

            with tab2:
                bottom = df.nsmallest(10, 'Change %')[['Ticker', 'Name', 'Change %', 'Price', 'Quality']]
                st.dataframe(bottom, hide_index=True, use_container_width=True)


elif page == "📊 Analysis":
    st.markdown('<p class="main-header">📊 Stock Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Enter Ticker", value="AAPL").upper()
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)

    if ticker:
        with st.spinner(f'Loading {ticker}...'):
            data, quality = fetch_stock_data_cached(ticker)

        if data and data.get('price'):
            scores = calculate_score(data)
            dcf = calculate_dcf(data)

            # Header
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.markdown(f"### {data.get('name', ticker)}")
                st.caption(f"{data.get('sector', '')} • {data.get('industry', '')}")

            with col2:
                change = data.get('change_percent', 0)
                st.metric("Price", f"${data.get('price', 0):.2f}", f"{change:+.2f}%")

            with col3:
                q_score = quality.get('overall_score', 70) if isinstance(quality, dict) else 70
                q_source = quality.get('quote', {}).get('source', 'Unknown') if isinstance(quality, dict) else 'Yahoo'
                q_class = 'quality-high' if q_score >= 80 else ('quality-medium' if q_score >= 60 else 'quality-low')
                st.markdown(f"""
                **Data Quality**
                <span class="quality-badge {q_class}">{q_score:.0f}/100</span>
                <span class="source-badge">{q_source}</span>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div style="background:{scores['color']};padding:1rem;border-radius:10px;text-align:center;color:white;">
                    <div style="font-size:1.5rem;font-weight:700;">{scores['percentage']:.0f}%</div>
                    <div>{scores['rating']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Chart", "📊 Metrics", "💎 DCF", "👥 Peers", "📰 News"])

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
                    de = data.get('debt_to_equity')
                    st.metric("Debt/Equity", f"{de:.1f}" if de else "N/A")
                    cr = data.get('current_ratio')
                    st.metric("Current Ratio", f"{cr:.2f}" if cr else "N/A")
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
                        st.metric("Upside/Downside", f"{dcf['upside_percent']:+.1f}%")

                    verdict_colors = {'UNDERVALUED': '#10b981', 'OVERVALUED': '#ef4444', 'FAIR VALUE': '#fbbf24'}
                    st.markdown(f"""
                    <div style="background:{verdict_colors.get(dcf['verdict'], '#fbbf24')};padding:1rem;border-radius:12px;text-align:center;color:white;margin-top:1rem;">
                        <h3 style="margin:0;">{dcf['verdict']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

            with tab4:
                peers = KNOWN_PEERS.get(ticker, [])
                if peers:
                    compare_tickers = [ticker] + peers[:5]
                    fig = create_comparison_chart(compare_tickers, '6mo')
                    st.plotly_chart(fig, use_container_width=True)

                    # Peer Comparison Table
                    peer_data = []
                    for p in peers[:6]:
                        p_data, _ = fetch_stock_data_cached(p)
                        if p_data and p_data.get('price'):
                            peer_data.append({
                                'Ticker': p,
                                'Price': f"${p_data.get('price', 0):.2f}",
                                'P/E': p_data.get('pe_ratio'),
                                'ROE %': (p_data.get('roe') or 0) * 100,
                            })
                    if peer_data:
                        st.dataframe(pd.DataFrame(peer_data), hide_index=True, use_container_width=True)
                else:
                    st.info("No peer data available.")

            with tab5:
                if MULTI_SOURCE_AVAILABLE:
                    news = get_news(ticker)
                    sentiment = get_sentiment(ticker)

                    if sentiment:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            bullish = sentiment.get('bullish_percent', 50)
                            st.metric("🐂 Bullish", f"{bullish:.1f}%")
                        with col2:
                            bearish = sentiment.get('bearish_percent', 50)
                            st.metric("🐻 Bearish", f"{bearish:.1f}%")
                        with col3:
                            buzz = sentiment.get('buzz_score', 0)
                            st.metric("📢 Buzz Score", f"{buzz:.2f}")
                        st.markdown("---")

                    if news:
                        for n in news[:5]:
                            st.markdown(f"""
                            <div class="news-card">
                                <strong>{n.get('title', 'No title')}</strong><br>
                                <small style="color:#6b7280;">{n.get('source', '')} • {n.get('published', '')[:10]}</small><br>
                                <a href="{n.get('url', '#')}" target="_blank">Read more →</a>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No news available.")
                else:
                    st.warning("News requires API keys. See Settings.")


elif page == "📰 News":
    st.markdown('<p class="main-header">📰 Market News</p>', unsafe_allow_html=True)

    ticker = st.text_input("Ticker for News", value="AAPL").upper()

    if MULTI_SOURCE_AVAILABLE and ticker:
        with st.spinner('Loading news & sentiment...'):
            news = get_news(ticker)
            sentiment = get_sentiment(ticker)

        if sentiment:
            st.markdown("### 🎭 Sentiment Analysis")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                bullish = sentiment.get('bullish_percent', 0)
                st.markdown(f"""
                <div class="metric-card" style="background:#10b981;">
                    <div style="font-size:2rem;font-weight:700;">{bullish:.1f}%</div>
                    <div>🐂 Bullish</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                bearish = sentiment.get('bearish_percent', 0)
                st.markdown(f"""
                <div class="metric-card" style="background:#ef4444;">
                    <div style="font-size:2rem;font-weight:700;">{bearish:.1f}%</div>
                    <div>🐻 Bearish</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                articles = sentiment.get('articles_in_week', 0)
                st.markdown(f"""
                <div class="metric-card-neutral">
                    <div style="font-size:2rem;font-weight:700;">{articles}</div>
                    <div>📰 Articles/Week</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                buzz = sentiment.get('buzz_score', 0)
                st.markdown(f"""
                <div class="metric-card-neutral">
                    <div style="font-size:2rem;font-weight:700;">{buzz:.2f}</div>
                    <div>📢 Buzz Score</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

        st.markdown("### 📰 Latest News")
        if news:
            for n in news:
                st.markdown(f"""
                <div class="news-card">
                    <strong>{n.get('title', 'No title')}</strong><br>
                    <small style="color:#6b7280;">{n.get('source', '')} • {n.get('published', '')[:10]}</small><br>
                    {n.get('text', '')[:150]}...<br>
                    <a href="{n.get('url', '#')}" target="_blank">Read more →</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No news available.")
    else:
        st.warning("News feature requires API keys (Finnhub/FMP). See Settings page.")


elif page == "🔍 Screener":
    st.markdown('<p class="main-header">🔍 Stock Screener</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("#### Filters")
        max_pe = st.slider("Max P/E", 0, 100, 50)
        min_div = st.slider("Min Dividend %", 0.0, 10.0, 0.0, 0.5)
        min_roe = st.slider("Min ROE %", 0, 50, 0)
        sectors = st.multiselect("Sectors", list(SECTOR_STOCKS.keys()), default=list(SECTOR_STOCKS.keys()))

    with col2:
        with st.spinner('Screening...'):
            df = fetch_sector_data({k: v for k, v in SECTOR_STOCKS.items() if k in sectors}, max_per_sector=8)

        if not df.empty:
            # Fetch additional data for filtering
            screened = []
            for _, row in df.iterrows():
                data, _ = fetch_stock_data_cached(row['Ticker'])
                if data:
                    pe = data.get('pe_ratio') or 999
                    div = (data.get('dividend_yield') or 0) * 100
                    roe = (data.get('roe') or 0) * 100

                    if pe <= max_pe and div >= min_div and roe >= min_roe:
                        screened.append({
                            'Ticker': row['Ticker'],
                            'Name': row['Name'],
                            'Price': row['Price'],
                            'Change %': row['Change %'],
                            'P/E': pe if pe < 999 else None,
                            'Div %': div,
                            'ROE %': roe,
                        })

            if screened:
                result_df = pd.DataFrame(screened).sort_values('Change %', ascending=False)
                st.markdown(f"**Found {len(result_df)} stocks**")
                st.dataframe(result_df, hide_index=True, use_container_width=True)
            else:
                st.info("No stocks match your criteria.")


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
            data, quality = fetch_stock_data_cached(ticker)
            if data and data.get('price'):
                scores = calculate_score(data)
                q_score = quality.get('overall_score', 70) if isinstance(quality, dict) else 70
                watchlist_data.append({
                    'Ticker': ticker,
                    'Name': (data.get('name', ticker) or ticker)[:25],
                    'Price': f"${data.get('price', 0):.2f}",
                    'Change': f"{data.get('change_percent', 0):+.2f}%",
                    'Score': f"{scores['percentage']:.0f}%",
                    'Quality': f"{q_score:.0f}",
                    'Rating': scores['rating'],
                })

        if watchlist_data:
            df = pd.DataFrame(watchlist_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Remove buttons
            st.markdown("#### Remove from Watchlist")
            cols = st.columns(min(len(st.session_state.watchlist), 6))
            for i, ticker in enumerate(st.session_state.watchlist[:6]):
                with cols[i]:
                    if st.button(f"🗑️ {ticker}", key=f"del_{ticker}"):
                        st.session_state.watchlist.remove(ticker)
                        st.rerun()

            st.markdown("---")
            fig = create_comparison_chart(st.session_state.watchlist[:8], '3mo')
            st.plotly_chart(fig, use_container_width=True)


elif page == "⚙️ Settings":
    st.markdown('<p class="main-header">⚙️ Settings</p>', unsafe_allow_html=True)

    st.markdown("### 🔑 API Keys")
    st.markdown("""
    Configure API keys for better data quality. All APIs have free tiers.

    Set environment variables or create a `.env` file:
    """)

    st.code("""
# .env file
FMP_API_KEY=your_key_here          # financialmodelingprep.com (250/day free)
FINNHUB_API_KEY=your_key_here      # finnhub.io (60/min free)
ALPHA_VANTAGE_API_KEY=your_key_here # alphavantage.co (25/day free)
    """, language="bash")

    st.markdown("### 📡 API Status")

    if MULTI_SOURCE_AVAILABLE:
        status = get_api_status()

        for api, info in status.items():
            col1, col2, col3 = st.columns([1, 2, 2])

            with col1:
                st.markdown(f"**{api.upper()}**")

            with col2:
                if info['available']:
                    st.success("✅ Connected")
                else:
                    st.error("❌ Not configured")

            with col3:
                stats = info.get('stats', {})
                if stats:
                    st.caption(f"Requests today: {stats.get('requests_today', 0)}")
    else:
        st.warning("Multi-source providers not loaded. Using yfinance only.")

    st.markdown("---")

    st.markdown("### 🗑️ Cache Management")

    if MULTI_SOURCE_AVAILABLE:
        cache_stats = get_cache_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Cache Statistics:**")
            for table, count in cache_stats.items():
                st.caption(f"{table}: {count} entries")

        with col2:
            if st.button("🗑️ Clear All Cache", type="primary"):
                clear_cache()
                st.success("Cache cleared!")
                st.rerun()

    st.markdown("---")

    st.markdown("### ℹ️ About")
    st.markdown("""
    **meradOS Heatmap v3.0**

    Multi-source stock market intelligence platform with:
    - 🔄 Automatic data source fallback
    - 💾 SQLite caching for performance
    - ⭐ Data quality scoring
    - 📊 Real-time market heatmap
    - 📰 News & sentiment analysis

    **Data Priority:**
    1. Financial Modeling Prep (SEC data - highest quality)
    2. Finnhub (News & Sentiment)
    3. Alpha Vantage
    4. Yahoo Finance (fallback)

    [GitHub](https://github.com/maf4711/merados-heatmap) • MIT License
    """)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#9ca3af;padding:1rem;">
    <small>🔥 <strong>meradOS Heatmap</strong> v3.0 • Multi-Source Data Engine •
    <a href="https://github.com/maf4711/merados-heatmap" style="color:#667eea;">GitHub</a></small>
</div>
""", unsafe_allow_html=True)
