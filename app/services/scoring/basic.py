"""
Basic habitability scoring service.

This module implements a heuristic-based habitability scoring system
that evaluates exoplanet characteristics against parameters favorable
for life as we know it.

SCIENTIFIC DISCLAIMER:
This scoring system provides PROBABILISTIC INDICATORS only. It does NOT
detect life or guarantee habitability. Many critical factors cannot be
measured with current technology (atmospheric composition, magnetic field,
geological activity, presence of water, etc.).

The score represents similarity to Earth-like conditions based on
limited available astrophysical parameters.

References:
- Kasting et al. (1993) "Habitable Zones around Main Sequence Stars"
- Kopparapu et al. (2013) "Habitable Zone Calculations"
- Tasker et al. (2017) "Habitability Definition"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.logging import get_logger
from app.models.exoplanet import Exoplanet
from app.schemas.scoring import (
    HabitabilityScoreResponse,
    ScoringFactorResult,
)

logger = get_logger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence levels for scoring factors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ScoringWeight:
    """Configuration for a scoring factor's weight."""
    name: str
    weight: float
    description: str


# Scoring weights configuration
# These weights reflect the relative importance of each factor
# for potential habitability based on scientific literature
SCORING_WEIGHTS = {
    "stellar_type": ScoringWeight(
        name="Stellar Type",
        weight=0.30,
        description="Host star spectral class affects habitable zone stability and UV radiation"
    ),
    "planet_radius": ScoringWeight(
        name="Planet Radius",
        weight=0.35,
        description="Planet size indicates likelihood of rocky composition and atmosphere retention"
    ),
    "equilibrium_temperature": ScoringWeight(
        name="Equilibrium Temperature",
        weight=0.35,
        description="Surface temperature proxy affects potential for liquid water"
    ),
}


class BasicHabitabilityScorer:
    """
    Basic habitability scoring engine using heuristic methods.
    
    This scorer evaluates three primary factors:
    1. Stellar Type: Preference for stable main-sequence stars (G, K types)
    2. Planet Radius: Preference for Earth-like rocky planets (0.5-2.0 R⊕)
    3. Equilibrium Temperature: Preference for liquid water range (~180-310 K)
    
    Each factor produces a score from 0 to 1, weighted and combined
    into a final habitability score.
    
    Example usage:
        scorer = BasicHabitabilityScorer()
        result = scorer.calculate_score(exoplanet)
    """
    
    # Stellar type scoring based on spectral class
    # G and K stars are considered most favorable for habitability
    # due to stable luminosity and longer main-sequence lifetimes
    STELLAR_TYPE_SCORES = {
        "O": 0.05,   # Very hot, short-lived, intense UV
        "B": 0.10,   # Hot, short-lived
        "A": 0.20,   # Moderately hot, shorter lifetime
        "F": 0.50,   # Warmer than Sun, reasonable lifetime
        "G": 0.95,   # Sun-like, optimal for life as we know it
        "K": 0.85,   # Slightly cooler, very stable, long-lived
        "M": 0.40,   # Most common, but issues with tidal locking and flares
        "L": 0.10,   # Brown dwarf, very cool
        "T": 0.05,   # Brown dwarf, very cool
        "Y": 0.02,   # Coolest brown dwarfs
    }
    
    # Earth-equivalent temperature boundaries for habitability
    # Based on water phase diagram considerations
    TEMP_OPTIMAL_MIN = 230  # K - Conservative lower bound for liquid water
    TEMP_OPTIMAL_MAX = 310  # K - Upper bound before runaway greenhouse
    TEMP_OUTER_MIN = 180    # K - Absolute minimum (with greenhouse effects)
    TEMP_OUTER_MAX = 350    # K - Absolute maximum (theoretical)
    
    # Planet radius boundaries (Earth radii)
    # Based on mass-radius relationships and atmosphere retention
    RADIUS_OPTIMAL_MIN = 0.5   # Minimum for atmosphere retention
    RADIUS_OPTIMAL_MAX = 1.6   # Transition to mini-Neptune territory
    RADIUS_ROCKY_MAX = 2.0     # Upper limit for likely rocky composition
    RADIUS_SUPER_EARTH_MAX = 3.0  # Extended range for super-Earths
    
    def __init__(self) -> None:
        """Initialize the habitability scorer."""
        self.weights = SCORING_WEIGHTS
        logger.info("BasicHabitabilityScorer initialized")
    
    def _score_stellar_type(
        self,
        stellar_type: Optional[str]
    ) -> tuple[float, str, ConfidenceLevel]:
        """
        Score based on host star spectral type.
        
        G and K type stars are considered most favorable because:
        - G stars (like our Sun) provide stable radiation over billions of years
        - K stars are even more stable with longer main-sequence lifetimes
        - M stars, while common, have issues with tidal locking and stellar flares
        
        Args:
            stellar_type: Spectral classification (e.g., "G2V", "K5", "M3.5V")
            
        Returns:
            tuple: (score, explanation, confidence)
        """
        if not stellar_type or not stellar_type.strip():
            return (
                0.5,  # Neutral score when unknown
                "Stellar type unknown. Cannot assess host star suitability for "
                "habitable zone stability. Assigned neutral score.",
                ConfidenceLevel.LOW
            )
        
        # Extract primary spectral class (first letter)
        spectral_class = stellar_type.strip()[0].upper()
        
        score = self.STELLAR_TYPE_SCORES.get(spectral_class, 0.3)
        
        # Generate explanation based on spectral type
        explanations = {
            "O": (
                f"O-type star ({stellar_type}): Extremely luminous and hot. "
                "Very short lifetime (~1-10 million years) insufficient for "
                "complex life evolution. Intense UV radiation problematic for habitability."
            ),
            "B": (
                f"B-type star ({stellar_type}): Very luminous and hot. "
                "Short main-sequence lifetime (~10-100 million years). "
                "High UV flux makes surface habitability challenging."
            ),
            "A": (
                f"A-type star ({stellar_type}): Hot star with moderate lifetime. "
                "Habitable zone exists but star may not be stable long enough "
                "for complex life development."
            ),
            "F": (
                f"F-type star ({stellar_type}): Warmer than the Sun. "
                "Adequate lifetime for life evolution (~2-4 billion years). "
                "Habitable zone is wider but UV levels are elevated."
            ),
            "G": (
                f"G-type star ({stellar_type}): Sun-like star. Optimal conditions "
                "for habitability based on our only known example of life. "
                "Stable luminosity and ~10 billion year main-sequence lifetime."
            ),
            "K": (
                f"K-type star ({stellar_type}): Slightly cooler than Sun. "
                "Excellent habitability potential with very stable luminosity "
                "and extended lifetime (15-30+ billion years). Reduced UV flux."
            ),
            "M": (
                f"M-type star ({stellar_type}): Red dwarf, most common stellar type. "
                "Concerns include: tidal locking of habitable zone planets, "
                "frequent stellar flares, and narrow habitable zones. However, "
                "very long lifetimes allow extended evolution time."
            ),
            "L": (
                f"L-type object ({stellar_type}): Brown dwarf or very cool red dwarf. "
                "Extremely low luminosity results in very close, narrow habitable zone "
                "with high probability of tidal locking."
            ),
            "T": (
                f"T-type object ({stellar_type}): Cool brown dwarf. "
                "Insufficient luminosity for conventional habitable zone."
            ),
            "Y": (
                f"Y-type object ({stellar_type}): Coldest brown dwarf class. "
                "Surface temperature similar to planets. Not suitable for "
                "traditional habitability assessments."
            ),
        }
        
        explanation = explanations.get(
            spectral_class,
            f"Unknown spectral type ({stellar_type}). Cannot properly assess "
            "stellar characteristics for habitability."
        )
        
        confidence = ConfidenceLevel.HIGH if spectral_class in "FGKM" else ConfidenceLevel.MEDIUM
        
        return (score, explanation, confidence)
    
    def _score_planet_radius(
        self,
        radius_earth: Optional[float]
    ) -> tuple[float, str, ConfidenceLevel]:
        """
        Score based on planet radius in Earth radii.
        
        Scoring rationale based on planetary composition research:
        - Planets < 0.5 R⊕: May not retain atmosphere (like Mars)
        - Planets 0.5-1.6 R⊕: Most likely rocky with potential atmospheres
        - Planets 1.6-2.0 R⊕: Transition zone, could be rocky or mini-Neptune
        - Planets 2.0-3.0 R⊕: Likely significant volatile envelope
        - Planets > 3.0 R⊕: Almost certainly gas-dominated
        
        Args:
            radius_earth: Planet radius in Earth radii
            
        Returns:
            tuple: (score, explanation, confidence)
        """
        if radius_earth is None:
            return (
                0.5,
                "Planet radius unknown. Cannot assess size-based habitability factors "
                "such as rocky composition likelihood or atmosphere retention capability.",
                ConfidenceLevel.LOW
            )
        
        r = radius_earth
        
        if r < 0.3:
            score = 0.1
            explanation = (
                f"Planet radius ({r:.2f} R⊕) is very small. Likely insufficient "
                "mass to retain a substantial atmosphere against stellar wind "
                "and thermal escape. Similar to Mercury or smaller."
            )
        elif r < 0.5:
            score = 0.3
            explanation = (
                f"Planet radius ({r:.2f} R⊕) is sub-Earth sized. May struggle "
                "to retain atmosphere long-term, similar to Mars. Possible thin "
                "atmosphere scenarios exist."
            )
        elif r < 0.8:
            score = 0.75
            explanation = (
                f"Planet radius ({r:.2f} R⊕) suggests a smaller rocky world. "
                "Should be capable of retaining an atmosphere. Potentially "
                "habitable if other conditions are favorable."
            )
        elif r < 1.3:
            score = 1.0
            explanation = (
                f"Planet radius ({r:.2f} R⊕) is Earth-like. Optimal size range "
                "for rocky composition with substantial atmosphere. Size alone "
                "suggests high potential for Earth-like surface conditions."
            )
        elif r < 1.6:
            score = 0.85
            explanation = (
                f"Planet radius ({r:.2f} R⊕) indicates a super-Earth. Likely "
                "rocky composition with potentially thicker atmosphere. May have "
                "higher surface gravity but still potentially habitable."
            )
        elif r < 2.0:
            score = 0.55
            explanation = (
                f"Planet radius ({r:.2f} R⊕) is in the transition zone. May be "
                "a rocky super-Earth with thick atmosphere or a mini-Neptune with "
                "significant volatile envelope. Composition uncertain."
            )
        elif r < 3.0:
            score = 0.25
            explanation = (
                f"Planet radius ({r:.2f} R⊕) suggests a mini-Neptune. Likely "
                "has a substantial hydrogen/helium envelope or water-world "
                "composition. Traditional surface habitability unlikely."
            )
        else:
            score = 0.05
            explanation = (
                f"Planet radius ({r:.2f} R⊕) indicates a Neptune or Jupiter-sized "
                "world. Gas giant composition expected. No solid surface for "
                "traditional habitability, though moons could be habitable."
            )
        
        confidence = ConfidenceLevel.HIGH if radius_earth else ConfidenceLevel.LOW
        
        return (score, explanation, confidence)
    
    def _score_equilibrium_temperature(
        self,
        temp_k: Optional[float]
    ) -> tuple[float, str, ConfidenceLevel]:
        """
        Score based on equilibrium temperature.
        
        The equilibrium temperature is calculated assuming no atmosphere.
        Actual surface temperature depends heavily on atmospheric composition
        (greenhouse effect). Earth's equilibrium temp is ~255K but surface is ~288K.
        
        Scoring rationale:
        - 230-310 K: Optimal range for liquid water with moderate greenhouse
        - 180-230 K: Could support liquid water with strong greenhouse (like early Mars)
        - 310-350 K: Could support water with thin atmosphere (like early Venus window)
        - Outside these ranges: Challenging for liquid water
        
        Args:
            temp_k: Equilibrium temperature in Kelvin
            
        Returns:
            tuple: (score, explanation, confidence)
        """
        if temp_k is None:
            return (
                0.5,
                "Equilibrium temperature unknown. Cannot assess thermal conditions "
                "for potential liquid water. This is a critical parameter for "
                "habitability assessment.",
                ConfidenceLevel.LOW
            )
        
        t = temp_k
        
        # Score using a peaked function centered on optimal range
        if self.TEMP_OPTIMAL_MIN <= t <= self.TEMP_OPTIMAL_MAX:
            # Optimal range - peak score
            # Slight preference for Earth-like ~255-288K
            center = 270
            score = 1.0 - 0.1 * abs(t - center) / 40
            score = max(0.85, min(1.0, score))
            explanation = (
                f"Equilibrium temperature ({t:.0f} K) is within the optimal range "
                f"for liquid water ({self.TEMP_OPTIMAL_MIN}-{self.TEMP_OPTIMAL_MAX} K). "
                "With an appropriate atmospheric greenhouse effect, surface conditions "
                "could support liquid water. Earth's equilibrium temperature is ~255 K."
            )
        elif self.TEMP_OUTER_MIN <= t < self.TEMP_OPTIMAL_MIN:
            # Cold but potentially habitable with greenhouse
            score = 0.4 + 0.45 * (t - self.TEMP_OUTER_MIN) / (self.TEMP_OPTIMAL_MIN - self.TEMP_OUTER_MIN)
            explanation = (
                f"Equilibrium temperature ({t:.0f} K) is below optimal but within "
                "the extended habitable range. A significant greenhouse effect "
                "(stronger than Earth's) would be required for surface liquid water. "
                "Early Mars may have had such conditions."
            )
        elif self.TEMP_OPTIMAL_MAX < t <= self.TEMP_OUTER_MAX:
            # Warm but potentially habitable
            score = 0.4 + 0.45 * (self.TEMP_OUTER_MAX - t) / (self.TEMP_OUTER_MAX - self.TEMP_OPTIMAL_MAX)
            explanation = (
                f"Equilibrium temperature ({t:.0f} K) is above optimal. "
                "Liquid water possible with a thin atmosphere or at the surface "
                "with atmospheric water vapor, but risk of runaway greenhouse. "
                "Conditions similar to inner edge of habitable zone."
            )
        elif t < self.TEMP_OUTER_MIN:
            # Too cold
            score = max(0.05, 0.4 * (t / self.TEMP_OUTER_MIN))
            explanation = (
                f"Equilibrium temperature ({t:.0f} K) is very low. Surface water "
                "would be frozen under most atmospheric scenarios. Subsurface "
                "liquid water possible (like Europa), but surface habitability unlikely."
            )
        else:
            # Too hot
            score = max(0.05, 0.4 * (1 - (t - self.TEMP_OUTER_MAX) / 200))
            score = max(0.02, score)
            explanation = (
                f"Equilibrium temperature ({t:.0f} K) is very high. Surface water "
                "would vaporize, potentially leading to runaway greenhouse effect. "
                "Venus-like conditions or worse expected."
            )
        
        confidence = ConfidenceLevel.MEDIUM  # Temperature alone is incomplete picture
        
        return (score, explanation, confidence)
    
    def calculate_score(self, exoplanet: Exoplanet) -> HabitabilityScoreResponse:
        """
        Calculate the complete habitability score for an exoplanet.
        
        Combines individual factor scores using configured weights
        to produce an overall habitability assessment.
        
        Args:
            exoplanet: Exoplanet model instance with astrophysical data
            
        Returns:
            HabitabilityScoreResponse: Complete scoring results with explanations
        """
        logger.info(f"Calculating habitability score for {exoplanet.name}")
        
        factors: list[ScoringFactorResult] = []
        missing_params: list[str] = []
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Score stellar type
        stellar_score, stellar_explanation, stellar_confidence = self._score_stellar_type(
            exoplanet.stellar_type
        )
        stellar_weight = self.weights["stellar_type"].weight
        factors.append(ScoringFactorResult(
            factor_name="stellar_type",
            score=stellar_score,
            weight=stellar_weight,
            weighted_contribution=stellar_score * stellar_weight,
            input_value=exoplanet.stellar_type or "Unknown",
            explanation=stellar_explanation,
            confidence=stellar_confidence.value,
        ))
        total_weighted_score += stellar_score * stellar_weight
        total_weight += stellar_weight
        if not exoplanet.stellar_type:
            missing_params.append("stellar_type")
        
        # Score planet radius
        radius_score, radius_explanation, radius_confidence = self._score_planet_radius(
            exoplanet.planet_radius_earth
        )
        radius_weight = self.weights["planet_radius"].weight
        factors.append(ScoringFactorResult(
            factor_name="planet_radius",
            score=radius_score,
            weight=radius_weight,
            weighted_contribution=radius_score * radius_weight,
            input_value=f"{exoplanet.planet_radius_earth:.2f} R⊕" if exoplanet.planet_radius_earth else "Unknown",
            explanation=radius_explanation,
            confidence=radius_confidence.value,
        ))
        total_weighted_score += radius_score * radius_weight
        total_weight += radius_weight
        if exoplanet.planet_radius_earth is None:
            missing_params.append("planet_radius_earth")
        
        # Score equilibrium temperature
        temp_score, temp_explanation, temp_confidence = self._score_equilibrium_temperature(
            exoplanet.equilibrium_temp_k
        )
        temp_weight = self.weights["equilibrium_temperature"].weight
        factors.append(ScoringFactorResult(
            factor_name="equilibrium_temperature",
            score=temp_score,
            weight=temp_weight,
            weighted_contribution=temp_score * temp_weight,
            input_value=f"{exoplanet.equilibrium_temp_k:.0f} K" if exoplanet.equilibrium_temp_k else "Unknown",
            explanation=temp_explanation,
            confidence=temp_confidence.value,
        ))
        total_weighted_score += temp_score * temp_weight
        total_weight += temp_weight
        if exoplanet.equilibrium_temp_k is None:
            missing_params.append("equilibrium_temp_k")
        
        # Calculate final score
        final_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Determine score category
        score_category = self._get_score_category(final_score)
        
        # Calculate data completeness
        total_params = 3
        available_params = total_params - len(missing_params)
        data_completeness = available_params / total_params
        
        logger.info(
            f"Habitability score for {exoplanet.name}: {final_score:.3f} "
            f"({score_category}, {data_completeness:.0%} data completeness)"
        )
        
        return HabitabilityScoreResponse(
            exoplanet_id=exoplanet.id,
            exoplanet_name=exoplanet.name,
            total_score=round(final_score, 4),
            score_category=score_category,
            factors=factors,
            data_completeness=round(data_completeness, 2),
            missing_parameters=missing_params,
        )
    
    def _get_score_category(self, score: float) -> str:
        """
        Convert numeric score to human-readable category.
        
        Args:
            score: Habitability score (0-1)
            
        Returns:
            str: Category label
        """
        if score >= 0.8:
            return "Very High"
        elif score >= 0.6:
            return "High"
        elif score >= 0.4:
            return "Moderate"
        elif score >= 0.2:
            return "Low"
        else:
            return "Very Low"
    
    def get_methodology(self) -> dict:
        """
        Return detailed methodology information.
        
        Returns:
            dict: Methodology details including factors, weights, and references
        """
        return {
            "version": "1.0.0",
            "factors": [
                {
                    "name": "stellar_type",
                    "weight": self.weights["stellar_type"].weight,
                    "description": self.weights["stellar_type"].description,
                    "optimal_values": ["G-type (Sun-like)", "K-type (orange dwarf)"],
                },
                {
                    "name": "planet_radius",
                    "weight": self.weights["planet_radius"].weight,
                    "description": self.weights["planet_radius"].description,
                    "optimal_range": "0.8-1.3 Earth radii",
                },
                {
                    "name": "equilibrium_temperature",
                    "weight": self.weights["equilibrium_temperature"].weight,
                    "description": self.weights["equilibrium_temperature"].description,
                    "optimal_range": "230-310 K",
                },
            ],
            "references": [
                "Kasting, J.F. et al. (1993) 'Habitable Zones around Main Sequence Stars' - Icarus",
                "Kopparapu, R.K. et al. (2013) 'Habitable Zone Calculations' - ApJ",
                "Tasker, E. et al. (2017) 'Habitability Definition Workshop Report' - Astrobiology",
                "Fulton, B.J. et al. (2017) 'The California-Kepler Survey' - AJ (radius gap)",
            ],
            "limitations": [
                "Does not account for atmospheric composition (crucial for actual temperature)",
                "Cannot assess magnetic field strength (protection from stellar radiation)",
                "Does not consider tidal locking effects for close-in planets",
                "Ignores orbital stability in multi-planet systems",
                "Cannot determine presence of water or other volatiles",
                "Does not factor in stellar age and activity levels",
                "Mass-radius relationship assumptions may not apply to all planets",
            ],
        }


# Singleton instance for dependency injection
habitability_scorer = BasicHabitabilityScorer()
