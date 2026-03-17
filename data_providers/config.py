"""
meradOS Heatmap - Data Provider Configuration
"""

import os

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
