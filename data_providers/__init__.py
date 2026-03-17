"""
meradOS Heatmap - Multi-Source Data Providers
==============================================
Implementiert:
- SQLite Cache fuer Performance
- Financial Modeling Prep (SEC-Daten)
- Finnhub (News & Sentiment)
- Alpha Vantage (Fallback)
- yfinance (Fallback)
- Data Quality Scores

Prioritaet: FMP -> Finnhub -> Alpha Vantage -> yfinance
"""

# Configuration
from .config import (
    FMP_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY,
    CACHE_DB_PATH, CACHE_TTL_QUOTES, CACHE_TTL_FUNDAMENTALS, CACHE_TTL_NEWS,
    FMP_BASE_URL, FINNHUB_BASE_URL, ALPHA_VANTAGE_BASE_URL,
)

# Quality
from .quality import DataSource, DataQuality

# Cache
from .cache import CacheManager, cache

# Providers
from .fmp import FMPProvider
from .finnhub import FinnhubProvider
from .alpha_vantage import AlphaVantageProvider
from .yfinance_provider import YFinanceProvider

# Fetcher & Convenience Functions
from .fetcher import (
    MultiSourceFetcher, fetcher,
    get_stock_data, get_quote, get_news, get_sentiment,
    clear_cache, get_cache_stats, get_api_status,
)

__all__ = [
    # Config
    'FMP_API_KEY', 'FINNHUB_API_KEY', 'ALPHA_VANTAGE_API_KEY',
    'CACHE_DB_PATH', 'CACHE_TTL_QUOTES', 'CACHE_TTL_FUNDAMENTALS', 'CACHE_TTL_NEWS',
    'FMP_BASE_URL', 'FINNHUB_BASE_URL', 'ALPHA_VANTAGE_BASE_URL',
    # Quality
    'DataSource', 'DataQuality',
    # Cache
    'CacheManager', 'cache',
    # Providers
    'FMPProvider', 'FinnhubProvider', 'AlphaVantageProvider', 'YFinanceProvider',
    # Fetcher
    'MultiSourceFetcher', 'fetcher',
    # Convenience
    'get_stock_data', 'get_quote', 'get_news', 'get_sentiment',
    'clear_cache', 'get_cache_stats', 'get_api_status',
]
