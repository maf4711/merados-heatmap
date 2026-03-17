"""
meradOS Heatmap - Alpha Vantage Provider (Fallback)
"""

import requests
from typing import Dict, Optional

from .config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL
from .quality import DataSource
from .cache import cache


class AlphaVantageProvider:
    """Alpha Vantage - Solider Fallback mit technischen Indikatoren"""

    @staticmethod
    def is_available() -> bool:
        return bool(ALPHA_VANTAGE_API_KEY)

    @staticmethod
    def get_quote(ticker: str) -> Optional[Dict]:
        """Holt Global Quote"""
        if not ALPHA_VANTAGE_API_KEY:
            return None

        try:
            url = f"{ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('alpha_vantage', response.ok)

            if response.ok:
                data = response.json()
                q = data.get('Global Quote', {})
                if q:
                    return {
                        'ticker': ticker.upper(),
                        'price': float(q.get('05. price', 0)),
                        'change': float(q.get('09. change', 0)),
                        'change_percent': float(q.get('10. change percent', '0%').replace('%', '')),
                        'day_high': float(q.get('03. high', 0)),
                        'day_low': float(q.get('04. low', 0)),
                        'open': float(q.get('02. open', 0)),
                        'previous_close': float(q.get('08. previous close', 0)),
                        'volume': int(q.get('06. volume', 0)),
                        '_source': DataSource.ALPHA_VANTAGE.value
                    }
        except:
            cache.track_api_call('alpha_vantage', False)
        return None

    @staticmethod
    def get_overview(ticker: str) -> Optional[Dict]:
        """Holt Company Overview (Fundamentals)"""
        if not ALPHA_VANTAGE_API_KEY:
            return None

        try:
            url = f"{ALPHA_VANTAGE_BASE_URL}?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('alpha_vantage', response.ok)

            if response.ok:
                o = response.json()
                if o.get('Symbol'):
                    return {
                        'ticker': ticker.upper(),
                        'name': o.get('Name'),
                        'description': o.get('Description', '')[:500],
                        'sector': o.get('Sector'),
                        'industry': o.get('Industry'),
                        'country': o.get('Country'),
                        'market_cap': int(o.get('MarketCapitalization', 0)),
                        'pe_ratio': float(o.get('PERatio', 0) or 0),
                        'forward_pe': float(o.get('ForwardPE', 0) or 0),
                        'peg_ratio': float(o.get('PEGRatio', 0) or 0),
                        'price_to_book': float(o.get('PriceToBookRatio', 0) or 0),
                        'dividend_yield': float(o.get('DividendYield', 0) or 0),
                        'eps': float(o.get('EPS', 0) or 0),
                        'roe': float(o.get('ReturnOnEquityTTM', 0) or 0),
                        'roa': float(o.get('ReturnOnAssetsTTM', 0) or 0),
                        'profit_margin': float(o.get('ProfitMargin', 0) or 0),
                        'operating_margin': float(o.get('OperatingMarginTTM', 0) or 0),
                        'revenue_growth': float(o.get('QuarterlyRevenueGrowthYOY', 0) or 0),
                        'earnings_growth': float(o.get('QuarterlyEarningsGrowthYOY', 0) or 0),
                        'beta': float(o.get('Beta', 0) or 0),
                        '52w_high': float(o.get('52WeekHigh', 0) or 0),
                        '52w_low': float(o.get('52WeekLow', 0) or 0),
                        'target_price': float(o.get('AnalystTargetPrice', 0) or 0),
                        '_source': DataSource.ALPHA_VANTAGE.value
                    }
        except:
            cache.track_api_call('alpha_vantage', False)
        return None
