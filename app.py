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
import warnings

warnings.filterwarnings('ignore')

from utils import (
    MULTI_SOURCE_AVAILABLE, fetch_stock_data_cached,
    get_api_status,
)
from routes import (
    render_heatmap, render_analysis, render_news,
    render_screener, render_watchlist, render_settings,
)

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
# PAGE ROUTING
# ============================================================================

if page == "🗺️ Heatmap":
    render_heatmap()
elif page == "📊 Analysis":
    render_analysis()
elif page == "📰 News":
    render_news()
elif page == "🔍 Screener":
    render_screener()
elif page == "📋 Watchlist":
    render_watchlist()
elif page == "⚙️ Settings":
    render_settings()

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
