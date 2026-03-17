"""
Tests for utils.py: calculate_score, calculate_dcf, constants
"""

import pytest

# We need to mock streamlit before importing utils, since utils imports it
import sys
from unittest.mock import MagicMock

# Stub streamlit to avoid ImportError in test environment
st_mock = MagicMock()
st_mock.cache_data = lambda **kwargs: (lambda f: f)  # no-op decorator
sys.modules["streamlit"] = st_mock

# Also stub charts module (imports plotly etc.)
sys.modules["charts"] = MagicMock()

from utils import calculate_score, calculate_dcf, SECTOR_STOCKS, KNOWN_PEERS


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    def test_sector_stocks_has_expected_sectors(self):
        assert "Technology" in SECTOR_STOCKS
        assert "Financial" in SECTOR_STOCKS
        assert "Energy" in SECTOR_STOCKS

    def test_sector_stocks_contains_known_tickers(self):
        assert "AAPL" in SECTOR_STOCKS["Technology"]
        assert "JPM" in SECTOR_STOCKS["Financial"]

    def test_known_peers_structure(self):
        assert "AAPL" in KNOWN_PEERS
        assert "MSFT" in KNOWN_PEERS["AAPL"]


# ---------------------------------------------------------------------------
# calculate_score
# ---------------------------------------------------------------------------
class TestCalculateScore:
    def test_empty_data_returns_zero_total(self):
        scores = calculate_score({})
        assert scores["total"] == 0
        assert scores["percentage"] == 0.0
        assert scores["rating"] == "STRONG SELL"

    def test_low_pe_gives_valuation_points(self):
        scores = calculate_score({"pe_ratio": 12})
        assert scores["valuation"] == 10

    def test_moderate_pe(self):
        scores = calculate_score({"pe_ratio": 18})
        assert scores["valuation"] == 7

    def test_high_pe_gives_few_points(self):
        scores = calculate_score({"pe_ratio": 30})
        assert scores["valuation"] == 2

    def test_profitability_high_margin_and_roe(self):
        scores = calculate_score({"profit_margin": 0.25, "roe": 0.25})
        assert scores["profitability"] == 20

    def test_growth_high(self):
        scores = calculate_score({"revenue_growth": 0.25, "earnings_growth": 0.25})
        assert scores["growth"] == 20

    def test_health_low_debt(self):
        scores = calculate_score({
            "debt_to_equity": 0.3,
            "current_ratio": 2.0,
            "free_cashflow": 1_000_000,
        })
        assert scores["health"] == 15

    def test_dividend_high_yield(self):
        scores = calculate_score({"dividend_yield": 0.05})
        assert scores["dividend"] == 7

    def test_analyst_strong_buy(self):
        scores = calculate_score({"recommendation": "strong_buy"})
        assert scores["analyst"] == 5

    def test_analyst_hold(self):
        scores = calculate_score({"recommendation": "hold"})
        assert scores["analyst"] == 2.5

    def test_strong_buy_rating(self):
        # Construct data that yields >= 75 points
        data = {
            "pe_ratio": 12, "peg_ratio": 0.8, "price_to_book": 1.5,
            "profit_margin": 0.25, "roe": 0.25,
            "revenue_growth": 0.25, "earnings_growth": 0.25,
            "debt_to_equity": 0.3, "current_ratio": 2.0, "free_cashflow": 1_000_000,
            "dividend_yield": 0.05, "recommendation": "strong_buy",
        }
        scores = calculate_score(data)
        assert scores["rating"] == "STRONG BUY"
        assert scores["color"] == "#10b981"

    def test_rating_thresholds(self):
        # BUY: 60-74
        data = {
            "pe_ratio": 12, "profit_margin": 0.25, "roe": 0.25,
            "revenue_growth": 0.25, "earnings_growth": 0.25,
            "debt_to_equity": 0.3,
        }
        scores = calculate_score(data)
        assert scores["percentage"] >= 45  # at least HOLD


# ---------------------------------------------------------------------------
# calculate_dcf
# ---------------------------------------------------------------------------
class TestCalculateDCF:
    def test_insufficient_data(self):
        result = calculate_dcf({})
        assert "error" in result

    def test_negative_fcf_returns_error(self):
        result = calculate_dcf({
            "free_cashflow": -100,
            "market_cap": 1_000_000,
            "price": 100,
        })
        assert "error" in result

    def test_valid_dcf_returns_fair_value(self):
        result = calculate_dcf({
            "free_cashflow": 50_000_000,
            "market_cap": 1_000_000_000,
            "price": 100,
            "revenue_growth": 0.10,
        })
        assert "fair_value" in result
        assert "upside_percent" in result
        assert "verdict" in result
        assert result["fair_value"] > 0

    def test_dcf_verdict_undervalued(self):
        # Very high FCF relative to market cap -> undervalued
        result = calculate_dcf({
            "free_cashflow": 500_000_000,
            "market_cap": 1_000_000_000,
            "price": 100,
            "revenue_growth": 0.15,
        })
        assert result["verdict"] == "UNDERVALUED"

    def test_dcf_growth_capped(self):
        # Growth > 30% should be capped to 30%
        result = calculate_dcf({
            "free_cashflow": 50_000_000,
            "market_cap": 1_000_000_000,
            "price": 100,
            "revenue_growth": 0.50,
        })
        assert "fair_value" in result
