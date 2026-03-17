"""
meradOS Heatmap - Shared Utilities, Constants, Data Functions
"""

import streamlit as st
import pandas as pd
from typing import Dict, List

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

# Re-export chart functions so existing imports from utils still work
from charts import create_treemap, create_sector_chart, create_price_chart, create_comparison_chart

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
    """Cached wrapper fuer Stock Data"""
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
    """Holt Daten fuer Heatmap"""
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
