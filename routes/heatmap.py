"""
meradOS Heatmap - Heatmap Page
"""

import streamlit as st

from utils import (
    SECTOR_STOCKS, fetch_sector_data,
    create_treemap, create_sector_chart,
)


def render_heatmap():
    """Renders the Heatmap page"""
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
