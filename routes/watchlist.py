"""
meradOS Heatmap - Watchlist Page
"""

import streamlit as st
import pandas as pd

from utils import fetch_stock_data_cached, calculate_score, create_comparison_chart


def render_watchlist():
    """Renders the Watchlist page"""
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
