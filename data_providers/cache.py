"""
meradOS Heatmap - SQLite Cache Manager
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

from .config import CACHE_DB_PATH


class CacheManager:
    """SQLite-basierter Cache fuer API-Responses"""

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

        # API Stats (fuer Rate Limiting)
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
        """Loescht Cache (optional gefiltert)"""
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
        """Gibt Cache-Statistiken zurueck"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}
        for table in ['quotes_cache', 'fundamentals_cache', 'news_cache', 'sentiment_cache']:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = cursor.fetchone()[0]

        conn.close()
        return stats

    def track_api_call(self, api_name: str, success: bool = True):
        """Trackt API-Aufrufe fuer Rate Limiting"""
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
        """Gibt API-Statistiken zurueck"""
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
