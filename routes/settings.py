"""
meradOS Heatmap - Settings Page
"""

import streamlit as st

from utils import MULTI_SOURCE_AVAILABLE, get_api_status, get_cache_stats, clear_cache


def render_settings():
    """Renders the Settings page"""
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
