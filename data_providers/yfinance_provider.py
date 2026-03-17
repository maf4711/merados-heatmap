"""
meradOS Heatmap - Yahoo Finance Provider (Final Fallback)
"""

import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional

from .quality import DataSource


class YFinanceProvider:
    """Yahoo Finance - Kostenloser Fallback ohne API-Key"""

    @staticmethod
    def is_available() -> bool:
        return True  # Immer verfuegbar

    @staticmethod
    def get_quote(ticker: str) -> Optional[Dict]:
        """Holt Quote via yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            prev = info.get('previousClose', price)
            change = price - prev if prev else 0
            change_pct = (change / prev * 100) if prev else 0

            return {
                'ticker': ticker.upper(),
                'name': info.get('longName') or info.get('shortName'),
                'price': price,
                'change': change,
                'change_percent': change_pct,
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'open': info.get('open'),
                'previous_close': prev,
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                '_source': DataSource.YFINANCE.value
            }
        except:
            return None

    @staticmethod
    def get_fundamentals(ticker: str) -> Optional[Dict]:
        """Holt Fundamentals via yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'ticker': ticker.upper(),
                'name': info.get('longName') or info.get('shortName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country'),
                'description': info.get('longBusinessSummary', '')[:500],
                'website': info.get('website'),
                'employees': info.get('fullTimeEmployees'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'free_cashflow': info.get('freeCashflow'),
                'beta': info.get('beta'),
                '52w_high': info.get('fiftyTwoWeekHigh'),
                '52w_low': info.get('fiftyTwoWeekLow'),
                'target_mean': info.get('targetMeanPrice'),
                'target_high': info.get('targetHighPrice'),
                'target_low': info.get('targetLowPrice'),
                'recommendation': info.get('recommendationKey'),
                'analyst_count': info.get('numberOfAnalystOpinions'),
                '_source': DataSource.YFINANCE.value
            }
        except:
            return None

    @staticmethod
    def get_news(ticker: str) -> Optional[List[Dict]]:
        """Holt News via yfinance"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news

            if news:
                return [{
                    'title': n.get('title'),
                    'text': '',
                    'url': n.get('link'),
                    'source': n.get('publisher'),
                    'published': datetime.fromtimestamp(n.get('providerPublishTime', 0)).isoformat(),
                    'image': n.get('thumbnail', {}).get('resolutions', [{}])[0].get('url') if n.get('thumbnail') else None,
                    '_source': DataSource.YFINANCE.value
                } for n in news[:10]]
        except:
            pass
        return None
