"""
meradOS Heatmap - News Page
"""

import streamlit as st

from utils import MULTI_SOURCE_AVAILABLE, get_news, get_sentiment


def render_news():
    """Renders the Market News page"""
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
