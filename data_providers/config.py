"""
meradOS Heatmap - Data Provider Configuration
"""

import logging
import os

logger = logging.getLogger(__name__)

# API Keys (aus Environment oder .env)
FMP_API_KEY = os.getenv('FMP_API_KEY', '')  # financialmodelingprep.com
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')  # finnhub.io
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')  # alphavantage.co

# Cache-Einstellungen
CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache.db')
CACHE_TTL_QUOTES = 300  # 5 Minuten fuer Kursdaten
CACHE_TTL_FUNDAMENTALS = 86400  # 24 Stunden fuer Fundamentals
CACHE_TTL_NEWS = 1800  # 30 Minuten fuer News

# API Endpunkte
FMP_BASE_URL = 'https://financialmodelingprep.com/api/v3'
FINNHUB_BASE_URL = 'https://finnhub.io/api/v1'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'


def validate_config():
    """Prueft ob API-Keys konfiguriert sind und warnt bei fehlenden Keys."""
    missing = []
    if not FMP_API_KEY:
        missing.append('FMP_API_KEY')
    if not FINNHUB_API_KEY:
        missing.append('FINNHUB_API_KEY')
    if not ALPHA_VANTAGE_API_KEY:
        missing.append('ALPHA_VANTAGE_API_KEY')
    if missing:
        logger.warning(f"Missing API keys: {', '.join(missing)}. Some data providers will be unavailable.")


validate_config()
