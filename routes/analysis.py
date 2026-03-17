"""
meradOS Heatmap - Analysis Page
"""

import streamlit as st
import pandas as pd

from utils import (
    MULTI_SOURCE_AVAILABLE, KNOWN_PEERS,
    fetch_stock_data_cached, calculate_score, calculate_dcf,
    create_price_chart, create_comparison_chart,
    get_news, get_sentiment,
)


def render_analysis():
    """Renders the Stock Analysis page"""
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
                _render_metrics(data)

            with tab3:
                _render_dcf(dcf)

            with tab4:
                _render_peers(ticker)

            with tab5:
                _render_analysis_news(ticker)


def _render_metrics(data):
    """Renders the Metrics tab"""
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


def _render_dcf(dcf):
    """Renders the DCF tab"""
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


def _render_peers(ticker):
    """Renders the Peers tab"""
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


def _render_analysis_news(ticker):
    """Renders the News sub-tab within Analysis"""
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
