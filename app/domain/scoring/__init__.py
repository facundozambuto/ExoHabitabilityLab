"""
Scoring Engine - Extensible habitability scoring system.

This package implements a strategy/plugin-based scoring engine
that allows new scientific factors to be added without modifying
core code.

Architecture:
- ScoringFactor: Protocol/interface for scoring factors
- ScoringEngine: Core engine that orchestrates factor evaluation
- Factor Plugins: Individual scoring factor implementations
- Configuration: YAML-based weight and parameter configuration
"""

from app.domain.scoring.engine import ScoringEngine
from app.domain.scoring.base import ScoringFactor, FactorResult
from app.domain.scoring.config import ScoringConfig

__all__ = [
    "ScoringEngine",
    "ScoringFactor",
    "FactorResult",
    "ScoringConfig",
]
