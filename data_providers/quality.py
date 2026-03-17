"""
meradOS Heatmap - Data Quality Scoring
"""

from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class DataSource(Enum):
    FMP = "Financial Modeling Prep"
    FINNHUB = "Finnhub"
    ALPHA_VANTAGE = "Alpha Vantage"
    YFINANCE = "Yahoo Finance"
    CACHE = "Cache"
    UNKNOWN = "Unknown"


@dataclass
class DataQuality:
    """Datenqualitaets-Score fuer Transparenz"""
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
