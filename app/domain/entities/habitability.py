"""
Habitability Assessment Domain Entity.

This module defines the HabitabilityAssessment class which represents
the complete result of a habitability analysis for an exoplanet.

Scientific Context:
-------------------
Habitability assessment is an inherently uncertain process. We use
multiple factors to estimate the likelihood that an exoplanet could
support life as we know it. Each factor contributes a score and
an explanation, and the overall assessment includes confidence levels
based on data availability.

Key Principles:
1. No claim of life detection - these are probabilistic indicators
2. Transparency in methodology - all factors are explained
3. Confidence quantification - data quality affects certainty
4. Extensibility - new factors can be added via the plugin system
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime


class ConfidenceLevel(str, Enum):
    """
    Confidence levels for scoring assessments.
    
    Based on data availability and measurement uncertainty.
    """
    VERY_LOW = "very_low"    # < 20% data available or high uncertainty
    LOW = "low"              # 20-40% data available
    MEDIUM = "medium"        # 40-60% data available
    HIGH = "high"            # 60-80% data available
    VERY_HIGH = "very_high"  # > 80% data available with good precision


class ScoreCategory(str, Enum):
    """Human-readable habitability score categories."""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"
    
    @classmethod
    def from_score(cls, score: float) -> "ScoreCategory":
        """Convert numeric score to category."""
        if score >= 0.8:
            return cls.VERY_HIGH
        elif score >= 0.6:
            return cls.HIGH
        elif score >= 0.4:
            return cls.MODERATE
        elif score >= 0.2:
            return cls.LOW
        else:
            return cls.VERY_LOW


@dataclass
class FactorScore:
    """
    Individual factor contribution to habitability score.
    
    Attributes:
        factor_id: Unique identifier for the scoring factor
        factor_name: Human-readable name
        category: Factor category (stellar, planetary, orbital, derived)
        raw_score: Unweighted score (0-1)
        weight: Weight in the overall calculation
        weighted_score: raw_score × weight
        input_value: The value used for calculation (for display)
        input_unit: Unit of the input value
        optimal_range: Description of optimal values
        explanation: Scientific explanation of the score
        confidence: Confidence level for this factor
        references: Scientific references for the scoring logic
    """
    
    factor_id: str
    factor_name: str
    category: str
    raw_score: float
    weight: float
    weighted_score: float
    input_value: Optional[str] = None
    input_unit: Optional[str] = None
    optimal_range: Optional[str] = None
    explanation: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    references: List[str] = field(default_factory=list)
    
    @property
    def score_percentage(self) -> float:
        """Return score as percentage."""
        return self.raw_score * 100
    
    @property
    def is_favorable(self) -> bool:
        """Check if this factor is favorable for habitability."""
        return self.raw_score >= 0.5
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "factor_id": self.factor_id,
            "factor_name": self.factor_name,
            "category": self.category,
            "score": round(self.raw_score, 4),
            "weight": round(self.weight, 4),
            "weighted_contribution": round(self.weighted_score, 4),
            "input_value": self.input_value,
            "input_unit": self.input_unit,
            "optimal_range": self.optimal_range,
            "explanation": self.explanation,
            "confidence": self.confidence.value,
            "references": self.references,
        }


@dataclass
class HabitabilityAssessment:
    """
    Complete habitability assessment for an exoplanet.
    
    This is the main output of the scoring engine, containing:
    - Overall habitability score
    - Individual factor breakdowns
    - Confidence metrics
    - Scientific disclaimers
    - Methodology information
    
    Attributes:
        exoplanet_id: ID of the assessed exoplanet
        exoplanet_name: Name of the assessed exoplanet
        host_star_name: Name of the host star
        total_score: Overall habitability score (0-1)
        factor_scores: List of individual factor scores
        data_completeness: Fraction of required data available
        missing_parameters: List of unavailable parameters
        assessment_timestamp: When the assessment was performed
        scoring_version: Version of the scoring algorithm
    """
    
    exoplanet_id: int
    exoplanet_name: str
    host_star_name: str
    total_score: float
    factor_scores: List[FactorScore] = field(default_factory=list)
    
    # Data quality metrics
    data_completeness: float = 0.0
    missing_parameters: List[str] = field(default_factory=list)
    
    # Metadata
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)
    scoring_version: str = "2.0.0"
    
    # Scientific context
    DISCLAIMER: str = (
        "IMPORTANT SCIENTIFIC DISCLAIMER: This habitability score is a "
        "probabilistic indicator based on limited astrophysical parameters. "
        "It does NOT indicate the detection of life or guarantee conditions "
        "suitable for life as we know it. Many critical factors essential for "
        "habitability—including atmospheric composition, surface conditions, "
        "magnetic field strength, geological activity, and the presence of "
        "water—cannot be determined from current observational data. This "
        "score represents a statistical estimate of Earth-like conditions "
        "based on measurable parameters only."
    )
    
    @property
    def score_category(self) -> ScoreCategory:
        """Get human-readable score category."""
        return ScoreCategory.from_score(self.total_score)
    
    @property
    def overall_confidence(self) -> ConfidenceLevel:
        """
        Calculate overall confidence based on data completeness and factor confidences.
        """
        if self.data_completeness >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif self.data_completeness >= 0.6:
            return ConfidenceLevel.HIGH
        elif self.data_completeness >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif self.data_completeness >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    @property
    def favorable_factors(self) -> List[FactorScore]:
        """Get factors that contribute positively (score >= 0.5)."""
        return [f for f in self.factor_scores if f.is_favorable]
    
    @property
    def unfavorable_factors(self) -> List[FactorScore]:
        """Get factors that contribute negatively (score < 0.5)."""
        return [f for f in self.factor_scores if not f.is_favorable]
    
    @property
    def factors_by_category(self) -> Dict[str, List[FactorScore]]:
        """Group factor scores by category."""
        result: Dict[str, List[FactorScore]] = {}
        for factor in self.factor_scores:
            if factor.category not in result:
                result[factor.category] = []
            result[factor.category].append(factor)
        return result
    
    def get_summary(self) -> str:
        """
        Generate a human-readable summary of the assessment.
        
        Suitable for display to researchers, educators, and general users.
        """
        summary_parts = [
            f"Habitability Assessment for {self.exoplanet_name}",
            f"═" * 50,
            f"Overall Score: {self.total_score:.2%} ({self.score_category.value})",
            f"Data Completeness: {self.data_completeness:.0%}",
            f"Confidence Level: {self.overall_confidence.value.replace('_', ' ').title()}",
            "",
            "Factor Breakdown:",
        ]
        
        for factor in sorted(self.factor_scores, key=lambda f: f.weighted_score, reverse=True):
            status = "✓" if factor.is_favorable else "✗"
            summary_parts.append(
                f"  {status} {factor.factor_name}: {factor.raw_score:.2%} "
                f"(weight: {factor.weight:.0%})"
            )
        
        if self.missing_parameters:
            summary_parts.append("")
            summary_parts.append("Missing Data:")
            for param in self.missing_parameters:
                summary_parts.append(f"  • {param}")
        
        return "\n".join(summary_parts)
    
    def get_methodology_summary(self) -> str:
        """
        Return a summary of the scoring methodology.
        """
        factor_descriptions = []
        for factor in self.factor_scores:
            factor_descriptions.append(f"- {factor.factor_name} (weight: {factor.weight:.0%})")
        
        return (
            f"The habitability score (v{self.scoring_version}) is computed using "
            f"a weighted combination of {len(self.factor_scores)} factors:\n"
            + "\n".join(factor_descriptions) +
            "\n\nEach factor is normalized to 0-1 and combined using "
            "scientifically-informed weights based on peer-reviewed research."
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API serialization."""
        return {
            "exoplanet_id": self.exoplanet_id,
            "exoplanet_name": self.exoplanet_name,
            "host_star_name": self.host_star_name,
            "total_score": round(self.total_score, 4),
            "score_category": self.score_category.value,
            "overall_confidence": self.overall_confidence.value,
            "factors": [f.to_dict() for f in self.factor_scores],
            "factors_by_category": {
                cat: [f.to_dict() for f in factors]
                for cat, factors in self.factors_by_category.items()
            },
            "data_completeness": round(self.data_completeness, 4),
            "missing_parameters": self.missing_parameters,
            "assessment_timestamp": self.assessment_timestamp.isoformat(),
            "scoring_version": self.scoring_version,
            "scientific_disclaimer": self.DISCLAIMER,
            "methodology_summary": self.get_methodology_summary(),
        }
