"""
meradOS Heatmap - Financial Modeling Prep Provider (SEC-Daten)
"""

import requests
from typing import Dict, List, Optional

from .config import FMP_API_KEY, FMP_BASE_URL
from .quality import DataSource
from .cache import cache


class FMPProvider:
    """Financial Modeling Prep - Beste Qualitaet fuer US-Aktien (SEC-Daten)"""

    REQUIRED_FIELDS = [
        'price', 'pe_ratio', 'market_cap', 'dividend_yield',
        'profit_margin', 'roe', 'revenue_growth', 'debt_to_equity'
    ]

    @staticmethod
    def is_available() -> bool:
        return bool(FMP_API_KEY)

    @staticmethod
    def get_quote(ticker: str) -> Optional[Dict]:
        """Holt Echtzeit-Quote"""
        if not FMP_API_KEY:
            return None

        try:
            url = f"{FMP_BASE_URL}/quote/{ticker}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('fmp', response.ok)

            if response.ok:
                data = response.json()
                if data and len(data) > 0:
                    q = data[0]
                    return {
                        'ticker': ticker.upper(),
                        'name': q.get('name'),
                        'price': q.get('price'),
                        'change': q.get('change'),
                        'change_percent': q.get('changesPercentage'),
                        'day_high': q.get('dayHigh'),
                        'day_low': q.get('dayLow'),
                        'year_high': q.get('yearHigh'),
                        'year_low': q.get('yearLow'),
                        'market_cap': q.get('marketCap'),
                        'volume': q.get('volume'),
                        'avg_volume': q.get('avgVolume'),
                        'pe_ratio': q.get('pe'),
                        'eps': q.get('eps'),
                        'exchange': q.get('exchange'),
                        '_source': DataSource.FMP.value
                    }
        except Exception as e:
            cache.track_api_call('fmp', False)
        return None

    @staticmethod
    def get_fundamentals(ticker: str) -> Optional[Dict]:
        """Holt Fundamental-Daten (Ratios, Financials)"""
        if not FMP_API_KEY:
            return None

        try:
            # Key Metrics
            url = f"{FMP_BASE_URL}/key-metrics-ttm/{ticker}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)

            if response.ok:
                metrics = response.json()
                if metrics and len(metrics) > 0:
                    m = metrics[0]

                    # Company Profile fuer zusaetzliche Infos
                    profile_url = f"{FMP_BASE_URL}/profile/{ticker}?apikey={FMP_API_KEY}"
                    profile_resp = requests.get(profile_url, timeout=10)
                    profile = profile_resp.json()[0] if profile_resp.ok and profile_resp.json() else {}

                    # Ratios
                    ratios_url = f"{FMP_BASE_URL}/ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
                    ratios_resp = requests.get(ratios_url, timeout=10)
                    ratios = ratios_resp.json()[0] if ratios_resp.ok and ratios_resp.json() else {}

                    cache.track_api_call('fmp', True)

                    return {
                        'ticker': ticker.upper(),
                        'name': profile.get('companyName'),
                        'sector': profile.get('sector'),
                        'industry': profile.get('industry'),
                        'country': profile.get('country'),
                        'description': profile.get('description', '')[:500],
                        'website': profile.get('website'),
                        'employees': profile.get('fullTimeEmployees'),

                        # Valuation
                        'pe_ratio': m.get('peRatioTTM'),
                        'forward_pe': ratios.get('priceEarningsToGrowthRatioTTM'),
                        'peg_ratio': m.get('pegRatioTTM'),
                        'price_to_book': m.get('pbRatioTTM'),
                        'price_to_sales': m.get('priceToSalesRatioTTM'),
                        'ev_to_ebitda': m.get('enterpriseValueOverEBITDATTM'),

                        # Profitability
                        'profit_margin': m.get('netIncomePerShareTTM'),
                        'operating_margin': ratios.get('operatingProfitMarginTTM'),
                        'gross_margin': ratios.get('grossProfitMarginTTM'),
                        'roe': m.get('roeTTM'),
                        'roa': m.get('roaTTM'),
                        'roic': m.get('roicTTM'),

                        # Growth
                        'revenue_growth': ratios.get('revenueGrowthTTM'),
                        'earnings_growth': ratios.get('netIncomeGrowthTTM'),

                        # Financial Health
                        'debt_to_equity': m.get('debtToEquityTTM'),
                        'current_ratio': m.get('currentRatioTTM'),
                        'quick_ratio': ratios.get('quickRatioTTM'),

                        # Dividends
                        'dividend_yield': m.get('dividendYieldTTM'),
                        'payout_ratio': m.get('payoutRatioTTM'),

                        # Cash Flow
                        'free_cashflow_per_share': m.get('freeCashFlowPerShareTTM'),
                        'operating_cashflow_per_share': m.get('operatingCashFlowPerShareTTM'),

                        # Analyst
                        'target_high': profile.get('dcfDiff'),
                        'dcf': profile.get('dcf'),

                        '_source': DataSource.FMP.value
                    }
        except Exception as e:
            cache.track_api_call('fmp', False)
        return None

    @staticmethod
    def get_news(ticker: str, limit: int = 10) -> Optional[List[Dict]]:
        """Holt News"""
        if not FMP_API_KEY:
            return None

        try:
            url = f"{FMP_BASE_URL}/stock_news?tickers={ticker}&limit={limit}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('fmp', response.ok)

            if response.ok:
                news = response.json()
                return [{
                    'title': n.get('title'),
                    'text': n.get('text', '')[:200],
                    'url': n.get('url'),
                    'source': n.get('site'),
                    'published': n.get('publishedDate'),
                    'image': n.get('image'),
                    '_source': DataSource.FMP.value
                } for n in news[:limit]]
        except:
            cache.track_api_call('fmp', False)
        return None
