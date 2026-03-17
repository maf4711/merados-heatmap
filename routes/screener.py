"""
meradOS Heatmap - Screener Page
"""

import streamlit as st
import pandas as pd

from utils import SECTOR_STOCKS, fetch_stock_data_cached, fetch_sector_data


def render_screener():
    """Renders the Stock Screener page"""
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
