"""
Pydantic schemas for habitability scoring.

These schemas define the structure of habitability score responses,
including detailed breakdowns and scientific explanations.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ScoringFactorResult(BaseModel):
    """
    Result for an individual scoring factor.
    
    Each factor contributes to the overall habitability score
    and includes a scientific explanation.
    """
    
    factor_name: str = Field(
        ..., description="Name of the scoring factor (e.g., 'stellar_type', 'planet_radius')"
    )
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Partial score for this factor (0-1)"
    )
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Weight of this factor in the total score"
    )
    weighted_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted contribution to total score"
    )
    input_value: Optional[str] = Field(
        None, description="The input value used for scoring"
    )
    explanation: str = Field(
        ..., description="Scientific explanation for this factor's score"
    )
    confidence: str = Field(
        ..., description="Confidence level in this factor (low, medium, high)"
    )


class HabitabilityScoreResponse(BaseModel):
    """
    Complete habitability score response.
    
    Contains the overall score, detailed breakdown by factor,
    and scientific disclaimers.
    """
    
    exoplanet_id: int = Field(..., description="ID of the scored exoplanet")
    exoplanet_name: str = Field(..., description="Name of the scored exoplanet")
    
    # Overall score
    total_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall habitability score (0-1). Higher values indicate "
                    "more Earth-like conditions based on available parameters."
    )
    
    # Score interpretation
    score_category: str = Field(
        ..., description="Human-readable category (e.g., 'Very Low', 'Low', 'Moderate', 'High', 'Very High')"
    )
    
    # Detailed breakdown
    factors: list[ScoringFactorResult] = Field(
        ..., description="Detailed breakdown of individual scoring factors"
    )
    
    # Data quality
    data_completeness: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of parameters available for scoring (0-1)"
    )
    missing_parameters: list[str] = Field(
        default_factory=list,
        description="List of parameters that were unavailable for scoring"
    )
    
    # Scientific disclaimer
    scientific_disclaimer: str = Field(
        default=(
            "IMPORTANT: This habitability score is a probabilistic indicator based on "
            "limited astrophysical parameters. It does NOT indicate the presence of life "
            "or guarantee conditions suitable for life as we know it. Many factors essential "
            "for habitability (atmospheric composition, magnetic field, geological activity, etc.) "
            "cannot be determined from current observational data. This score should be "
            "interpreted as a rough estimate of Earth-like conditions only."
        ),
        description="Scientific disclaimer about score interpretation"
    )
    
    methodology_summary: str = Field(
        default=(
            "The habitability score is computed using a weighted combination of factors: "
            "stellar type (spectral class favorability for stable habitable zones), "
            "planet radius (likelihood of rocky composition), and equilibrium temperature "
            "(proximity to liquid water temperature range). Each factor is normalized to 0-1 "
            "and combined using scientifically-informed weights."
        ),
        description="Brief explanation of the scoring methodology"
    )


class ScoringMethodology(BaseModel):
    """
    Detailed explanation of the scoring methodology.
    
    Provides transparency about how scores are calculated.
    """
    
    version: str = Field(..., description="Version of the scoring algorithm")
    factors: list[dict] = Field(
        ..., description="List of factors with their weights and descriptions"
    )
    references: list[str] = Field(
        default_factory=list,
        description="Scientific references for the methodology"
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations of the scoring approach"
    )
