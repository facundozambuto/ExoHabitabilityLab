"""
Advanced Habitability Scoring Service.

This service wraps the full 13-factor ScoringEngine and provides
an interface compatible with the API's HabitabilityScoreResponse.

The service integrates all scoring factors:
1. Stellar Type
2. Stellar Luminosity
3. Stellar Age
4. Habitable Zone Position
5. Planet Radius
6. Planet Mass
7. Planet Density
8. Equilibrium Temperature
9. Surface Gravity
10. Orbital Eccentricity
11. Tidal Locking
12. Atmosphere Retention
13. Magnetic Field Potential
"""

from typing import Optional

from app.models.exoplanet import Exoplanet
from app.domain.mappers import exoplanet_model_to_entity, exoplanet_model_to_star_entity
from app.domain.scoring.engine import ScoringEngine
from app.domain.scoring.factors import get_all_factors
from app.schemas.scoring import HabitabilityScoreResponse, ScoringFactorResult


# Category thresholds for score interpretation
SCORE_CATEGORIES = [
    (0.0, 0.2, "Very Low"),
    (0.2, 0.4, "Low"),
    (0.4, 0.6, "Moderate"),
    (0.6, 0.8, "High"),
    (0.8, 1.0, "Very High"),
]


def get_score_category(score: float) -> str:
    """Convert numeric score to human-readable category."""
    for lower, upper, category in SCORE_CATEGORIES:
        if lower <= score < upper:
            return category
    return "Very High" if score >= 0.8 else "Very Low"


class AdvancedHabitabilityScorer:
    """
    Advanced habitability scoring service using the full 13-factor engine.
    
    This service converts database models to domain entities,
    runs them through the comprehensive scoring engine, and
    produces API-compatible responses.
    
    Factors evaluated:
    - Stellar: Type, luminosity, age, habitable zone position
    - Planetary: Radius, mass, density, temperature, surface gravity
    - Orbital: Eccentricity, tidal locking risk
    - Derived: Atmosphere retention, magnetic field potential
    """
    
    VERSION = "2.0.0"
    
    def __init__(self):
        """Initialize the scorer with the full factor set."""
        self._engine = ScoringEngine(factors=get_all_factors())
    
    def calculate_score(self, exoplanet: Exoplanet) -> HabitabilityScoreResponse:
        """
        Calculate comprehensive habitability score for an exoplanet.
        
        Converts the database model to domain entities, evaluates all
        13 factors, and produces a detailed response.
        
        Args:
            exoplanet: Database model with exoplanet data
            
        Returns:
            HabitabilityScoreResponse with full factor breakdown
        """
        # Convert database model to domain entities
        exoplanet_entity = exoplanet_model_to_entity(exoplanet)
        star_entity = exoplanet_model_to_star_entity(exoplanet)
        
        # Run full assessment
        assessment = self._engine.evaluate(exoplanet_entity, star_entity)
        
        # Convert factor scores to API schema
        factors = [
            ScoringFactorResult(
                factor_name=fs.factor_id,
                score=fs.raw_score,
                weight=fs.weight,
                weighted_contribution=fs.weighted_score,
                input_value=str(fs.input_value) if fs.input_value is not None else None,
                explanation=fs.explanation,
                confidence=fs.confidence.value if hasattr(fs.confidence, 'value') else str(fs.confidence),
            )
            for fs in assessment.factor_scores
        ]
        
        # Get score category
        category = get_score_category(assessment.total_score)
        
        # Build response
        return HabitabilityScoreResponse(
            exoplanet_id=exoplanet.id,
            exoplanet_name=exoplanet.name,
            total_score=assessment.total_score,
            score_category=category,
            factors=factors,
            data_completeness=assessment.data_completeness,
            missing_parameters=assessment.missing_parameters,
            scientific_disclaimer=(
                "IMPORTANT: This habitability score is a probabilistic indicator based on "
                "limited astrophysical parameters. It evaluates 13 factors including stellar "
                "properties, planetary characteristics, orbital dynamics, and derived estimates. "
                "It does NOT indicate the presence of life or guarantee conditions suitable for "
                "life as we know it. Many factors essential for habitability (atmospheric "
                "composition, magnetic field strength, geological activity, etc.) cannot be "
                "directly measured from current observational data."
            ),
            methodology_summary=(
                f"The habitability score is computed using a weighted combination of 13 factors "
                f"(Scoring Engine v{self.VERSION}):\n"
                "• STELLAR: Spectral type favorability, luminosity stability, stellar age, "
                "habitable zone position\n"
                "• PLANETARY: Radius (rocky composition), mass, bulk density, equilibrium "
                "temperature, surface gravity\n"
                "• ORBITAL: Eccentricity (climate stability), tidal locking risk\n"
                "• DERIVED: Atmosphere retention potential, magnetic field likelihood\n\n"
                "Each factor is normalized to 0-1 and combined using scientifically-informed "
                "weights based on astrobiological research."
            ),
        )
    
    def get_methodology(self) -> dict:
        """
        Return detailed methodology information.
        
        Returns:
            Dictionary with version, factors, references, and limitations
        """
        factors_info = []
        
        for factor_id in self._engine.get_registered_factors():
            factor = self._engine.get_factor(factor_id)
            if factor:
                factors_info.append({
                    "id": factor.factor_id,
                    "name": factor.factor_name,
                    "category": factor.category.value,
                    "description": factor.description,
                    "weight": self._engine.config.get_weight(factor_id),
                    "references": factor.references,
                })
        
        return {
            "version": self.VERSION,
            "factors": factors_info,
            "references": [
                "Kasting, J.F. et al. (1993) - Habitable Zones around Main Sequence Stars",
                "Kopparapu, R.K. et al. (2013) - Habitable Zone Calculations",
                "Fulton, B.J. et al. (2017) - The California-Kepler Survey",
                "Chen, J. & Kipping, D. (2017) - Probabilistic Forecasting of Planet Masses",
                "Lingam, M. & Loeb, A. (2019) - Life in the Cosmos",
                "Barnes, R. (2017) - Tidal Locking of Habitable Exoplanets",
                "Cockell, C.S. et al. (2016) - Habitability: A Review",
            ],
            "limitations": [
                "Atmospheric composition cannot be determined for most exoplanets",
                "Magnetic field presence is estimated from planetary properties only",
                "Surface conditions are derived from equilibrium temperature assumptions",
                "Binary star systems may have complex habitability dynamics not fully captured",
                "Age-related factors depend on stellar age estimates which can be uncertain",
                "Tidal effects are approximated and may not capture resonant orbital scenarios",
                "Life as we know it is the baseline - alternative biochemistries are not considered",
                "Data completeness significantly affects score reliability",
            ],
        }


# Global instance for dependency injection
advanced_habitability_scorer = AdvancedHabitabilityScorer()
