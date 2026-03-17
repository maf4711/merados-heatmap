"""
meradOS Heatmap - Finnhub Provider (News & Sentiment)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .config import FINNHUB_API_KEY, FINNHUB_BASE_URL
from .quality import DataSource
from .cache import cache


class FinnhubProvider:
    """Finnhub - Beste Quelle fuer News & Sentiment"""

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
