"""
meradOS Heatmap - Multi-Source Data Fetcher
"""

from datetime import datetime
from typing import Dict, List, Tuple

from .config import (
    FMP_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY,
    CACHE_TTL_QUOTES, CACHE_TTL_FUNDAMENTALS, CACHE_TTL_NEWS
)
from .quality import DataSource, DataQuality
from .cache import cache
from .fmp import FMPProvider
from .finnhub import FinnhubProvider
from .alpha_vantage import AlphaVantageProvider
from .yfinance_provider import YFinanceProvider


class MultiSourceFetcher:
    """
    Intelligenter Daten-Fetcher mit Multi-Source Fallback

    Prioritaet:
    1. Cache (wenn fresh)
    2. Financial Modeling Prep (beste Qualitaet)
    3. Finnhub (News & Sentiment)
    4. Alpha Vantage
    5. yfinance (Fallback)
    """

    def __init__(self):
        self.cache = cache
        self.providers = {
            'fmp': FMPProvider,
            'finnhub': FinnhubProvider,
            'alpha_vantage': AlphaVantageProvider,
            'yfinance': YFinanceProvider
        }

    def get_quote(self, ticker: str, use_cache: bool = True) -> Tuple[Dict, DataQuality]:
        """Holt Quote mit Fallback-Kette"""
        ticker = ticker.upper()

        # 1. Cache pruefen
        if use_cache:
            cached = self.cache.get('quotes_cache', ticker)
            if cached:
                data, source, timestamp = cached
                quality = DataQuality(
                    source=DataSource.CACHE,
                    freshness="cached",
                    completeness=self._calc_completeness(data, ['price', 'change_percent', 'volume']),
                    reliability=70,
                    timestamp=datetime.fromtimestamp(timestamp),
                    fields_available=list(data.keys()),
                    fields_missing=[]
                )
                return data, quality

        # 2. Fallback-Kette
        providers_order = [
            ('fmp', FMPProvider.get_quote),
            ('finnhub', FinnhubProvider.get_quote),
            ('alpha_vantage', AlphaVantageProvider.get_quote),
            ('yfinance', YFinanceProvider.get_quote),
        ]

        for provider_name, fetch_func in providers_order:
            if not self.providers[provider_name].is_available() and provider_name != 'yfinance':
                continue

            data = fetch_func(ticker)
            if data and data.get('price'):
                # Cache speichern
                self.cache.set('quotes_cache', ticker, data, provider_name, CACHE_TTL_QUOTES)

                source_map = {
                    'fmp': DataSource.FMP,
                    'finnhub': DataSource.FINNHUB,
                    'alpha_vantage': DataSource.ALPHA_VANTAGE,
                    'yfinance': DataSource.YFINANCE
                }

                quality = DataQuality(
                    source=source_map.get(provider_name, DataSource.UNKNOWN),
                    freshness="live",
                    completeness=self._calc_completeness(data, ['price', 'change_percent', 'volume', 'market_cap']),
                    reliability=self._get_reliability(provider_name),
                    timestamp=datetime.now(),
                    fields_available=[k for k, v in data.items() if v is not None and k != '_source'],
                    fields_missing=[k for k, v in data.items() if v is None]
                )

                return data, quality

        # Nichts gefunden
        return {}, DataQuality(
            source=DataSource.UNKNOWN,
            freshness="stale",
            completeness=0,
            reliability=0,
            timestamp=datetime.now(),
            fields_available=[],
            fields_missing=['price', 'change_percent', 'volume']
        )

    def get_fundamentals(self, ticker: str, use_cache: bool = True) -> Tuple[Dict, DataQuality]:
        """Holt Fundamentals mit Fallback-Kette"""
        ticker = ticker.upper()

        # 1. Cache pruefen
        if use_cache:
            cached = self.cache.get('fundamentals_cache', ticker)
            if cached:
                data, source, timestamp = cached
                quality = DataQuality(
                    source=DataSource.CACHE,
                    freshness="cached",
                    completeness=self._calc_completeness(data, FMPProvider.REQUIRED_FIELDS),
                    reliability=70,
                    timestamp=datetime.fromtimestamp(timestamp),
                    fields_available=list(data.keys()),
                    fields_missing=[]
                )
                return data, quality

        # 2. Fallback-Kette
        providers_order = [
            ('fmp', FMPProvider.get_fundamentals),
            ('alpha_vantage', AlphaVantageProvider.get_overview),
            ('yfinance', YFinanceProvider.get_fundamentals),
        ]

        for provider_name, fetch_func in providers_order:
            if not self.providers[provider_name].is_available() and provider_name != 'yfinance':
                continue

            data = fetch_func(ticker)
            if data:
                self.cache.set('fundamentals_cache', ticker, data, provider_name, CACHE_TTL_FUNDAMENTALS)

                source_map = {
                    'fmp': DataSource.FMP,
                    'alpha_vantage': DataSource.ALPHA_VANTAGE,
                    'yfinance': DataSource.YFINANCE
                }

                quality = DataQuality(
                    source=source_map.get(provider_name, DataSource.UNKNOWN),
                    freshness="live",
                    completeness=self._calc_completeness(data, FMPProvider.REQUIRED_FIELDS),
                    reliability=self._get_reliability(provider_name),
                    timestamp=datetime.now(),
                    fields_available=[k for k, v in data.items() if v is not None and k != '_source'],
                    fields_missing=[k for k, v in data.items() if v is None]
                )

                return data, quality

        return {}, DataQuality(
            source=DataSource.UNKNOWN,
            freshness="stale",
            completeness=0,
            reliability=0,
            timestamp=datetime.now(),
            fields_available=[],
            fields_missing=FMPProvider.REQUIRED_FIELDS
        )

    def get_news(self, ticker: str, use_cache: bool = True) -> Tuple[List[Dict], DataQuality]:
        """Holt News mit Fallback-Kette"""
        ticker = ticker.upper()

        # 1. Cache pruefen
        if use_cache:
            cached = self.cache.get('news_cache', ticker)
            if cached:
                data, source, timestamp = cached
                quality = DataQuality(
                    source=DataSource.CACHE,
                    freshness="cached",
                    completeness=100 if data else 0,
                    reliability=70,
                    timestamp=datetime.fromtimestamp(timestamp),
                    fields_available=['news'],
                    fields_missing=[]
                )
                return data, quality

        # 2. Fallback-Kette - Finnhub zuerst fuer beste News
        providers_order = [
            ('finnhub', FinnhubProvider.get_news),
            ('fmp', FMPProvider.get_news),
            ('yfinance', YFinanceProvider.get_news),
        ]

        for provider_name, fetch_func in providers_order:
            if not self.providers[provider_name].is_available() and provider_name != 'yfinance':
                continue

            data = fetch_func(ticker)
            if data:
                self.cache.set('news_cache', ticker, data, provider_name, CACHE_TTL_NEWS)

                source_map = {
                    'finnhub': DataSource.FINNHUB,
                    'fmp': DataSource.FMP,
                    'yfinance': DataSource.YFINANCE
                }

                quality = DataQuality(
                    source=source_map.get(provider_name, DataSource.UNKNOWN),
                    freshness="live",
                    completeness=100,
                    reliability=self._get_reliability(provider_name),
                    timestamp=datetime.now(),
                    fields_available=['news'],
                    fields_missing=[]
                )

                return data, quality

        return [], DataQuality(
            source=DataSource.UNKNOWN,
            freshness="stale",
            completeness=0,
            reliability=0,
            timestamp=datetime.now(),
            fields_available=[],
            fields_missing=['news']
        )

    def get_sentiment(self, ticker: str, use_cache: bool = True) -> Tuple[Dict, DataQuality]:
        """Holt Sentiment (nur Finnhub)"""
        ticker = ticker.upper()

        # Cache pruefen
        if use_cache:
            cached = self.cache.get('sentiment_cache', ticker)
            if cached:
                data, source, timestamp = cached
                quality = DataQuality(
                    source=DataSource.CACHE,
                    freshness="cached",
                    completeness=100 if data else 0,
                    reliability=70,
                    timestamp=datetime.fromtimestamp(timestamp),
                    fields_available=list(data.keys()) if data else [],
                    fields_missing=[]
                )
                return data, quality

        # Finnhub ist die einzige Quelle fuer Sentiment
        if FinnhubProvider.is_available():
            data = FinnhubProvider.get_sentiment(ticker)
            if data:
                self.cache.set('sentiment_cache', ticker, data, 'finnhub', CACHE_TTL_NEWS)

                quality = DataQuality(
                    source=DataSource.FINNHUB,
                    freshness="live",
                    completeness=100,
                    reliability=85,
                    timestamp=datetime.now(),
                    fields_available=list(data.keys()),
                    fields_missing=[]
                )

                return data, quality

        return {}, DataQuality(
            source=DataSource.UNKNOWN,
            freshness="stale",
            completeness=0,
            reliability=0,
            timestamp=datetime.now(),
            fields_available=[],
            fields_missing=['sentiment']
        )

    def get_complete_data(self, ticker: str) -> Dict:
        """Holt alle verfuegbaren Daten fuer einen Ticker"""
        ticker = ticker.upper()

        quote, quote_quality = self.get_quote(ticker)
        fundamentals, fund_quality = self.get_fundamentals(ticker)
        news, news_quality = self.get_news(ticker)
        sentiment, sent_quality = self.get_sentiment(ticker)

        # Merge alle Daten
        combined = {**fundamentals, **quote}  # Quote ueberschreibt fuer aktuellste Preise

        # Data Quality Summary
        qualities = [quote_quality, fund_quality, news_quality, sent_quality]
        avg_score = sum(q.overall_score for q in qualities) / len(qualities)

        return {
            'data': combined,
            'news': news,
            'sentiment': sentiment,
            'quality': {
                'overall_score': round(avg_score, 1),
                'quote': quote_quality.to_dict(),
                'fundamentals': fund_quality.to_dict(),
                'news': news_quality.to_dict(),
                'sentiment': sent_quality.to_dict(),
            }
        }

    def _calc_completeness(self, data: Dict, required_fields: List[str]) -> float:
        """Berechnet Vollstaendigkeit der Daten"""
        if not data or not required_fields:
            return 0

        available = sum(1 for f in required_fields if data.get(f) is not None)
        return round((available / len(required_fields)) * 100, 1)

    def _get_reliability(self, provider: str) -> float:
        """Gibt Zuverlaessigkeits-Score fuer Provider zurueck"""
        reliability_scores = {
            'fmp': 95,
            'finnhub': 85,
            'alpha_vantage': 80,
            'yfinance': 70
        }
        return reliability_scores.get(provider, 50)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Globale Fetcher-Instanz
fetcher = MultiSourceFetcher()


def get_stock_data(ticker: str) -> Tuple[Dict, Dict]:
    """
    Convenience Function: Holt alle Daten fuer einen Ticker

    Returns:
        Tuple[data_dict, quality_dict]
    """
    result = fetcher.get_complete_data(ticker)
    return result['data'], result['quality']


def get_quote(ticker: str) -> Dict:
    """Convenience: Holt nur Quote"""
    data, _ = fetcher.get_quote(ticker)
    return data


def get_news(ticker: str) -> List[Dict]:
    """Convenience: Holt nur News"""
    data, _ = fetcher.get_news(ticker)
    return data


def get_sentiment(ticker: str) -> Dict:
    """Convenience: Holt nur Sentiment"""
    data, _ = fetcher.get_sentiment(ticker)
    return data


def clear_cache(ticker: str = None):
    """Loescht Cache"""
    cache.clear(ticker=ticker)


def get_cache_stats() -> Dict:
    """Gibt Cache-Statistiken zurueck"""
    return cache.get_stats()


def get_api_status() -> Dict:
    """Gibt Status aller APIs zurueck"""
    return {
        'fmp': {
            'available': FMPProvider.is_available(),
            'stats': cache.get_api_stats('fmp')
        },
        'finnhub': {
            'available': FinnhubProvider.is_available(),
            'stats': cache.get_api_stats('finnhub')
        },
        'alpha_vantage': {
            'available': AlphaVantageProvider.is_available(),
            'stats': cache.get_api_stats('alpha_vantage')
        },
        'yfinance': {
            'available': True,
            'stats': {}
        }
    }
