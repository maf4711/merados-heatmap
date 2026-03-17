"""
Tests for data_providers: DataQuality, CacheManager
"""

import os
import sqlite3
import tempfile
from datetime import datetime

import pytest

from data_providers.quality import DataSource, DataQuality
from data_providers.cache import CacheManager


# ---------------------------------------------------------------------------
# DataSource enum
# ---------------------------------------------------------------------------
class TestDataSource:
    def test_enum_values(self):
        assert DataSource.FMP.value == "Financial Modeling Prep"
        assert DataSource.YFINANCE.value == "Yahoo Finance"
        assert DataSource.CACHE.value == "Cache"

    def test_all_members(self):
        names = [m.name for m in DataSource]
        assert "FMP" in names
        assert "FINNHUB" in names
        assert "ALPHA_VANTAGE" in names
        assert "YFINANCE" in names
        assert "CACHE" in names
        assert "UNKNOWN" in names


# ---------------------------------------------------------------------------
# DataQuality
# ---------------------------------------------------------------------------
class TestDataQuality:
    def _make_quality(self, source=DataSource.FMP, freshness="live",
                      completeness=100.0, reliability=90.0):
        return DataQuality(
            source=source,
            freshness=freshness,
            completeness=completeness,
            reliability=reliability,
            timestamp=datetime(2026, 3, 17, 12, 0, 0),
            fields_available=["price", "name", "pe_ratio"],
            fields_missing=["peg_ratio"],
        )

    def test_overall_score_fmp_live_full(self):
        q = self._make_quality()
        # FMP=95, live=1.0, completeness=100 => 95*1.0*(100/100) = 95.0
        assert q.overall_score == 95.0

    def test_overall_score_cached_reduces(self):
        q = self._make_quality(freshness="cached")
        # 95 * 0.9 * 1.0 = 85.5
        assert q.overall_score == 85.5

    def test_overall_score_stale_reduces_more(self):
        q = self._make_quality(freshness="stale")
        # 95 * 0.7 * 1.0 = 66.5
        assert q.overall_score == 66.5

    def test_overall_score_partial_completeness(self):
        q = self._make_quality(completeness=50.0)
        # 95 * 1.0 * 0.5 = 47.5
        assert q.overall_score == 47.5

    def test_overall_score_yfinance(self):
        q = self._make_quality(source=DataSource.YFINANCE)
        # 70 * 1.0 * 1.0 = 70.0
        assert q.overall_score == 70.0

    def test_overall_score_unknown_source(self):
        q = self._make_quality(source=DataSource.UNKNOWN, freshness="stale",
                               completeness=50.0)
        # 30 * 0.7 * 0.5 = 10.5
        assert q.overall_score == 10.5

    def test_to_dict_keys(self):
        q = self._make_quality()
        d = q.to_dict()
        assert d["source"] == "Financial Modeling Prep"
        assert d["freshness"] == "live"
        assert d["completeness"] == 100.0
        assert d["overall_score"] == 95.0
        assert d["fields_available"] == 3
        assert d["fields_missing"] == 1


# ---------------------------------------------------------------------------
# CacheManager (uses temp SQLite DB)
# ---------------------------------------------------------------------------
class TestCacheManager:
    @pytest.fixture()
    def cache(self, tmp_path):
        db_path = str(tmp_path / "test_cache.db")
        return CacheManager(db_path=db_path)

    def test_set_and_get(self, cache):
        cache.set("quotes_cache", "AAPL", {"price": 185.0}, "FMP", ttl=3600)
        result = cache.get("quotes_cache", "AAPL")
        assert result is not None
        data, source, ts = result
        assert data["price"] == 185.0
        assert source == "FMP"

    def test_get_nonexistent_returns_none(self, cache):
        assert cache.get("quotes_cache", "ZZZZ") is None

    def test_get_expired_returns_none(self, cache):
        cache.set("quotes_cache", "MSFT", {"price": 400.0}, "FMP", ttl=0)
        # TTL=0 means already expired
        import time
        time.sleep(0.01)
        assert cache.get("quotes_cache", "MSFT") is None

    def test_ticker_uppercased(self, cache):
        cache.set("quotes_cache", "aapl", {"price": 185.0}, "FMP", ttl=3600)
        result = cache.get("quotes_cache", "AAPL")
        assert result is not None

    def test_clear_specific_ticker(self, cache):
        cache.set("quotes_cache", "AAPL", {"price": 185.0}, "FMP", ttl=3600)
        cache.set("quotes_cache", "MSFT", {"price": 400.0}, "FMP", ttl=3600)
        cache.clear("quotes_cache", "AAPL")
        assert cache.get("quotes_cache", "AAPL") is None
        assert cache.get("quotes_cache", "MSFT") is not None

    def test_clear_all(self, cache):
        cache.set("quotes_cache", "AAPL", {"price": 185.0}, "FMP", ttl=3600)
        cache.set("fundamentals_cache", "AAPL", {"pe": 28}, "FMP", ttl=3600)
        cache.clear()
        assert cache.get("quotes_cache", "AAPL") is None
        assert cache.get("fundamentals_cache", "AAPL") is None

    def test_get_stats(self, cache):
        cache.set("quotes_cache", "AAPL", {"price": 185.0}, "FMP", ttl=3600)
        cache.set("quotes_cache", "MSFT", {"price": 400.0}, "FMP", ttl=3600)
        stats = cache.get_stats()
        assert stats["quotes_cache"] == 2
        assert stats["fundamentals_cache"] == 0

    def test_track_api_call(self, cache):
        cache.track_api_call("FMP", success=True)
        cache.track_api_call("FMP", success=False)
        stats = cache.get_api_stats("FMP")
        assert stats["requests_today"] == 2
        assert stats["errors_today"] == 1
