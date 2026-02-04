#!/usr/bin/env python3
"""
meradOS Heatmap - Multi-Source Data Providers
==============================================
Implementiert:
- SQLite Cache für Performance
- Financial Modeling Prep (SEC-Daten)
- Finnhub (News & Sentiment)
- Alpha Vantage (Fallback)
- yfinance (Fallback)
- Data Quality Scores

Priorität: FMP → Finnhub → Alpha Vantage → yfinance
"""

import sqlite3
import json
import hashlib
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# KONFIGURATION
# ============================================================================

# API Keys (aus Environment oder .env)
FMP_API_KEY = os.getenv('FMP_API_KEY', '')  # financialmodelingprep.com
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')  # finnhub.io
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')  # alphavantage.co

# Cache-Einstellungen
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), 'cache.db')
CACHE_TTL_QUOTES = 300  # 5 Minuten für Kursdaten
CACHE_TTL_FUNDAMENTALS = 86400  # 24 Stunden für Fundamentals
CACHE_TTL_NEWS = 1800  # 30 Minuten für News

# API Endpunkte
FMP_BASE_URL = 'https://financialmodelingprep.com/api/v3'
FINNHUB_BASE_URL = 'https://finnhub.io/api/v1'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'


# ============================================================================
# DATA QUALITY
# ============================================================================

class DataSource(Enum):
    FMP = "Financial Modeling Prep"
    FINNHUB = "Finnhub"
    ALPHA_VANTAGE = "Alpha Vantage"
    YFINANCE = "Yahoo Finance"
    CACHE = "Cache"
    UNKNOWN = "Unknown"


@dataclass
class DataQuality:
    """Datenqualitäts-Score für Transparenz"""
    source: DataSource
    freshness: str  # "live", "cached", "stale"
    completeness: float  # 0-100%
    reliability: float  # 0-100%
    timestamp: datetime
    fields_available: List[str]
    fields_missing: List[str]

    @property
    def overall_score(self) -> float:
        """Gesamtscore 0-100"""
        source_scores = {
            DataSource.FMP: 95,
            DataSource.FINNHUB: 85,
            DataSource.ALPHA_VANTAGE: 80,
            DataSource.YFINANCE: 70,
            DataSource.CACHE: 60,
            DataSource.UNKNOWN: 30
        }
        freshness_multiplier = {
            "live": 1.0,
            "cached": 0.9,
            "stale": 0.7
        }
        base = source_scores.get(self.source, 50)
        fresh = freshness_multiplier.get(self.freshness, 0.8)
        return round(base * fresh * (self.completeness / 100), 1)

    def to_dict(self) -> Dict:
        return {
            'source': self.source.value,
            'freshness': self.freshness,
            'completeness': self.completeness,
            'reliability': self.reliability,
            'overall_score': self.overall_score,
            'timestamp': self.timestamp.isoformat(),
            'fields_available': len(self.fields_available),
            'fields_missing': len(self.fields_missing)
        }


# ============================================================================
# SQLITE CACHE
# ============================================================================

class CacheManager:
    """SQLite-basierter Cache für API-Responses"""

    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialisiert die Datenbank"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Quotes Cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                source TEXT,
                timestamp REAL,
                ttl INTEGER
            )
        ''')

        # Fundamentals Cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamentals_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                source TEXT,
                timestamp REAL,
                ttl INTEGER
            )
        ''')

        # News Cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                source TEXT,
                timestamp REAL,
                ttl INTEGER
            )
        ''')

        # Sentiment Cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                source TEXT,
                timestamp REAL,
                ttl INTEGER
            )
        ''')

        # API Stats (für Rate Limiting)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_stats (
                api_name TEXT PRIMARY KEY,
                requests_today INTEGER DEFAULT 0,
                last_request REAL,
                errors_today INTEGER DEFAULT 0,
                last_reset TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get(self, table: str, ticker: str) -> Optional[Tuple[Dict, str, float]]:
        """Holt Daten aus Cache wenn nicht abgelaufen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT data, source, timestamp, ttl FROM {table}
            WHERE ticker = ?
        ''', (ticker.upper(),))

        row = cursor.fetchone()
        conn.close()

        if row:
            data, source, timestamp, ttl = row
            age = datetime.now().timestamp() - timestamp

            if age < ttl:
                return json.loads(data), source, timestamp

        return None

    def set(self, table: str, ticker: str, data: Dict, source: str, ttl: int):
        """Speichert Daten im Cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            INSERT OR REPLACE INTO {table} (ticker, data, source, timestamp, ttl)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticker.upper(), json.dumps(data), source, datetime.now().timestamp(), ttl))

        conn.commit()
        conn.close()

    def clear(self, table: str = None, ticker: str = None):
        """Löscht Cache (optional gefiltert)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if table and ticker:
            cursor.execute(f'DELETE FROM {table} WHERE ticker = ?', (ticker.upper(),))
        elif table:
            cursor.execute(f'DELETE FROM {table}')
        else:
            for t in ['quotes_cache', 'fundamentals_cache', 'news_cache', 'sentiment_cache']:
                cursor.execute(f'DELETE FROM {t}')

        conn.commit()
        conn.close()

    def get_stats(self) -> Dict:
        """Gibt Cache-Statistiken zurück"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}
        for table in ['quotes_cache', 'fundamentals_cache', 'news_cache', 'sentiment_cache']:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = cursor.fetchone()[0]

        conn.close()
        return stats

    def track_api_call(self, api_name: str, success: bool = True):
        """Trackt API-Aufrufe für Rate Limiting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT requests_today, errors_today, last_reset FROM api_stats WHERE api_name = ?
        ''', (api_name,))
        row = cursor.fetchone()

        if row:
            requests, errors, last_reset = row
            if last_reset != today:
                requests, errors = 0, 0

            requests += 1
            if not success:
                errors += 1

            cursor.execute('''
                UPDATE api_stats SET requests_today = ?, errors_today = ?,
                last_request = ?, last_reset = ? WHERE api_name = ?
            ''', (requests, errors, datetime.now().timestamp(), today, api_name))
        else:
            cursor.execute('''
                INSERT INTO api_stats (api_name, requests_today, errors_today, last_request, last_reset)
                VALUES (?, 1, ?, ?, ?)
            ''', (api_name, 0 if success else 1, datetime.now().timestamp(), today))

        conn.commit()
        conn.close()

    def get_api_stats(self, api_name: str) -> Dict:
        """Gibt API-Statistiken zurück"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM api_stats WHERE api_name = ?', (api_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'api_name': row[0],
                'requests_today': row[1],
                'last_request': row[2],
                'errors_today': row[3],
                'last_reset': row[4]
            }
        return {}


# Globale Cache-Instanz
cache = CacheManager()


# ============================================================================
# FINANCIAL MODELING PREP (SEC-DATEN)
# ============================================================================

class FMPProvider:
    """Financial Modeling Prep - Beste Qualität für US-Aktien (SEC-Daten)"""

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

                    # Company Profile für zusätzliche Infos
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


# ============================================================================
# FINNHUB (NEWS & SENTIMENT)
# ============================================================================

class FinnhubProvider:
    """Finnhub - Beste Quelle für News & Sentiment"""

    @staticmethod
    def is_available() -> bool:
        return bool(FINNHUB_API_KEY)

    @staticmethod
    def get_quote(ticker: str) -> Optional[Dict]:
        """Holt Echtzeit-Quote"""
        if not FINNHUB_API_KEY:
            return None

        try:
            url = f"{FINNHUB_BASE_URL}/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('finnhub', response.ok)

            if response.ok:
                q = response.json()
                if q.get('c'):  # Current price exists
                    return {
                        'ticker': ticker.upper(),
                        'price': q.get('c'),
                        'change': q.get('d'),
                        'change_percent': q.get('dp'),
                        'day_high': q.get('h'),
                        'day_low': q.get('l'),
                        'open': q.get('o'),
                        'previous_close': q.get('pc'),
                        '_source': DataSource.FINNHUB.value
                    }
        except:
            cache.track_api_call('finnhub', False)
        return None

    @staticmethod
    def get_news(ticker: str, days: int = 7) -> Optional[List[Dict]]:
        """Holt News der letzten X Tage"""
        if not FINNHUB_API_KEY:
            return None

        try:
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')

            url = f"{FINNHUB_BASE_URL}/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('finnhub', response.ok)

            if response.ok:
                news = response.json()
                return [{
                    'title': n.get('headline'),
                    'text': n.get('summary', '')[:200],
                    'url': n.get('url'),
                    'source': n.get('source'),
                    'published': datetime.fromtimestamp(n.get('datetime', 0)).isoformat(),
                    'image': n.get('image'),
                    '_source': DataSource.FINNHUB.value
                } for n in news[:15]]
        except:
            cache.track_api_call('finnhub', False)
        return None

    @staticmethod
    def get_sentiment(ticker: str) -> Optional[Dict]:
        """Holt Social Sentiment"""
        if not FINNHUB_API_KEY:
            return None

        try:
            # News Sentiment
            url = f"{FINNHUB_BASE_URL}/news-sentiment?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('finnhub', response.ok)

            if response.ok:
                data = response.json()
                sentiment = data.get('sentiment', {})
                buzz = data.get('buzz', {})

                return {
                    'ticker': ticker.upper(),
                    'bullish_percent': sentiment.get('bullishPercent', 0) * 100,
                    'bearish_percent': sentiment.get('bearishPercent', 0) * 100,
                    'articles_in_week': buzz.get('articlesInLastWeek', 0),
                    'buzz_score': buzz.get('buzz', 0),
                    'weekly_average': buzz.get('weeklyAverage', 0),
                    'company_news_score': data.get('companyNewsScore', 0),
                    'sector_avg_bullish': data.get('sectorAverageBullishPercent', 0) * 100,
                    'sector_avg_news_score': data.get('sectorAverageNewsScore', 0),
                    '_source': DataSource.FINNHUB.value
                }
        except:
            cache.track_api_call('finnhub', False)
        return None

    @staticmethod
    def get_recommendation(ticker: str) -> Optional[Dict]:
        """Holt Analysten-Empfehlungen"""
        if not FINNHUB_API_KEY:
            return None

        try:
            url = f"{FINNHUB_BASE_URL}/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=10)
            cache.track_api_call('finnhub', response.ok)

            if response.ok:
                recs = response.json()
                if recs:
                    latest = recs[0]
                    total = latest.get('buy', 0) + latest.get('hold', 0) + latest.get('sell', 0) + \
                            latest.get('strongBuy', 0) + latest.get('strongSell', 0)

                    return {
                        'ticker': ticker.upper(),
                        'period': latest.get('period'),
                        'strong_buy': latest.get('strongBuy', 0),
                        'buy': latest.get('buy', 0),
                        'hold': latest.get('hold', 0),
                        'sell': latest.get('sell', 0),
                        'strong_sell': latest.get('strongSell', 0),
                        'total_analysts': total,
                        '_source': DataSource.FINNHUB.value
                    }
        except:
            cache.track_api_call('finnhub', False)
        return None


# ============================================================================
# ALPHA VANTAGE (FALLBACK)
# ============================================================================

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


# ============================================================================
# YFINANCE (FINAL FALLBACK)
# ============================================================================

class YFinanceProvider:
    """Yahoo Finance - Kostenloser Fallback ohne API-Key"""

    @staticmethod
    def is_available() -> bool:
        return True  # Immer verfügbar

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


# ============================================================================
# MULTI-SOURCE DATA FETCHER
# ============================================================================

class MultiSourceFetcher:
    """
    Intelligenter Daten-Fetcher mit Multi-Source Fallback

    Priorität:
    1. Cache (wenn fresh)
    2. Financial Modeling Prep (beste Qualität)
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

        # 1. Cache prüfen
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

        # 1. Cache prüfen
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

        # 1. Cache prüfen
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

        # 2. Fallback-Kette - Finnhub zuerst für beste News
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

        # Cache prüfen
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

        # Finnhub ist die einzige Quelle für Sentiment
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
        """Holt alle verfügbaren Daten für einen Ticker"""
        ticker = ticker.upper()

        quote, quote_quality = self.get_quote(ticker)
        fundamentals, fund_quality = self.get_fundamentals(ticker)
        news, news_quality = self.get_news(ticker)
        sentiment, sent_quality = self.get_sentiment(ticker)

        # Merge alle Daten
        combined = {**fundamentals, **quote}  # Quote überschreibt für aktuellste Preise

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
        """Berechnet Vollständigkeit der Daten"""
        if not data or not required_fields:
            return 0

        available = sum(1 for f in required_fields if data.get(f) is not None)
        return round((available / len(required_fields)) * 100, 1)

    def _get_reliability(self, provider: str) -> float:
        """Gibt Zuverlässigkeits-Score für Provider zurück"""
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
    Convenience Function: Holt alle Daten für einen Ticker

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
    """Löscht Cache"""
    cache.clear(ticker=ticker)


def get_cache_stats() -> Dict:
    """Gibt Cache-Statistiken zurück"""
    return cache.get_stats()


def get_api_status() -> Dict:
    """Gibt Status aller APIs zurück"""
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


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == '__main__':
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'

    print(f"\n{'='*60}")
    print(f"  meradOS Multi-Source Data Test: {ticker}")
    print(f"{'='*60}")

    # API Status
    print("\n📡 API Status:")
    status = get_api_status()
    for api, info in status.items():
        avail = "✅" if info['available'] else "❌"
        print(f"   {api}: {avail}")

    # Daten holen
    print(f"\n📊 Lade Daten für {ticker}...")
    data, quality = get_stock_data(ticker)

    print(f"\n💰 Quote:")
    print(f"   Price: ${data.get('price', 'N/A')}")
    print(f"   Change: {data.get('change_percent', 'N/A')}%")

    print(f"\n📈 Fundamentals:")
    print(f"   P/E: {data.get('pe_ratio', 'N/A')}")
    print(f"   ROE: {data.get('roe', 'N/A')}")
    print(f"   Profit Margin: {data.get('profit_margin', 'N/A')}")

    print(f"\n⭐ Data Quality:")
    print(f"   Overall Score: {quality.get('overall_score', 'N/A')}/100")
    print(f"   Quote Source: {quality.get('quote', {}).get('source', 'N/A')}")
    print(f"   Fundamentals Source: {quality.get('fundamentals', {}).get('source', 'N/A')}")

    # News
    news = get_news(ticker)
    if news:
        print(f"\n📰 News ({len(news)} Artikel):")
        for n in news[:3]:
            print(f"   - {n.get('title', 'N/A')[:60]}...")

    # Sentiment
    sentiment = get_sentiment(ticker)
    if sentiment:
        print(f"\n🎭 Sentiment:")
        print(f"   Bullish: {sentiment.get('bullish_percent', 'N/A')}%")
        print(f"   Bearish: {sentiment.get('bearish_percent', 'N/A')}%")

    print(f"\n{'='*60}\n")
