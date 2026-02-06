"""
Derived/Composite Scoring Factors.

This module contains factors that are inferred from multiple properties:
- AtmosphereRetentionFactor: Likelihood of holding an atmosphere
- MagneticFieldPotentialFactor: Probability of protective magnetic field

Scientific Background:
---------------------
These factors combine multiple physical parameters to estimate
properties that cannot be directly observed for exoplanets:

1. Atmosphere retention depends on:
   - Escape velocity (mass + radius)
   - Stellar activity (UV, X-ray, stellar wind)
   - Planet age (time for atmospheric loss)

2. Magnetic field depends on:
   - Planet size and mass (convecting core)
   - Rotation rate (dynamo action)
   - Composition (metallic core needed)

References:
- Tian et al. (2015) "Water Loss from Earth-like Planets"
- Driscoll & Bercovici (2014) "On the Thermal and Magnetic Histories"
- Zuluaga et al. (2013) "The Habitable Zone Gallery: Magnetic Fields"
"""

from typing import List
import math

from app.domain.entities.exoplanet import ExoplanetEntity, PlanetType
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import ConfidenceLevel
from app.domain.scoring.base import BaseScoringFactor, FactorResult, FactorCategory


class AtmosphereRetentionFactor(BaseScoringFactor):
    """
    Estimates the ability to retain a substantial atmosphere.
    
    Scientific Rationale:
    --------------------
    Atmosphere retention is governed by:
    
    1. Escape velocity: v_esc = sqrt(2GM/R)
       - Higher = better retention
       - Earth: 11.2 km/s, Mars: 5.0 km/s
    
    2. Stellar radiation/wind:
       - Young, active stars strip atmospheres
       - M dwarfs have intense flares
       - UV and X-ray photoevaporation
    
    3. Jeans escape criterion:
       - Gas escapes if thermal velocity > ~0.2 × escape velocity
       - Temperature at exobase matters
    
    4. Non-thermal losses:
       - Sputtering from stellar wind
       - Charge exchange
       - Photochemical escape
    
    Mars lost most of its atmosphere due to low gravity + no magnetic field.
    Venus retained a thick atmosphere despite no magnetic field (higher mass).
    """
    
    @property
    def factor_id(self) -> str:
        return "atmosphere_retention"
    
    @property
    def factor_name(self) -> str:
        return "Atmosphere Retention Potential"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.DERIVED
    
    @property
    def description(self) -> str:
        return (
            "Estimates the planet's ability to retain a substantial atmosphere "
            "based on escape velocity, stellar environment, and composition."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Tian et al. (2015) Space Science Reviews 194:97-140",
            "Johnstone et al. (2019) A&A 624:L10",
            "Owen & Wu (2017) ApJ 847:29 - Photoevaporation",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate atmosphere retention potential."""
        
        # Get physical parameters
        mass = exoplanet.physical.mass_earth
        radius = exoplanet.physical.radius_earth
        
        if mass is None and radius is None:
            return self._create_missing_data_result("planet_mass or planet_radius")
        
        # Calculate escape velocity (relative to Earth)
        # v_esc ∝ sqrt(M/R)
        if mass is not None and radius is not None:
            escape_vel_ratio = math.sqrt(mass / radius)
            escape_vel_kms = 11.2 * escape_vel_ratio  # Earth's is 11.2 km/s
        elif mass is not None:
            # Estimate radius from mass using Earth-like density
            est_radius = mass ** 0.27  # Rough M-R relation for rocky planets
            escape_vel_ratio = math.sqrt(mass / est_radius)
            escape_vel_kms = 11.2 * escape_vel_ratio
        else:
            # Radius only - assume Earth-like density
            est_mass = radius ** 3.7  # Rough R-M relation
            escape_vel_ratio = math.sqrt(est_mass / radius)
            escape_vel_kms = 11.2 * escape_vel_ratio
        
        # Get stellar activity indicator
        stellar_teff = star.temperature_k or 5778
        stellar_age = star.age_gyr
        
        # M dwarfs (< 3700 K) are more active
        stellar_activity_penalty = 0.0
        if stellar_teff < 3700:
            stellar_activity_penalty = 0.2
            activity_note = (
                "M dwarf host has intense UV/X-ray activity and stellar wind, "
                "significantly increasing atmospheric loss rates."
            )
        elif stellar_teff < 4500:
            stellar_activity_penalty = 0.1
            activity_note = (
                "Late K dwarf host has moderately elevated activity compared to Sun."
            )
        else:
            activity_note = "Sun-like or hotter star has moderate stellar activity."
        
        # Young stars are more active
        if stellar_age is not None and stellar_age < 1.0:
            stellar_activity_penalty += 0.15
            activity_note += f" Young star age ({stellar_age:.2f} Gyr) indicates higher activity."
        
        # Base score from escape velocity
        if escape_vel_kms < 3.0:
            base_score = 0.1
            escape_note = (
                f"Very low escape velocity ({escape_vel_kms:.1f} km/s, vs Earth's 11.2 km/s). "
                f"Even heavy molecules like CO₂ will escape on geologic timescales."
            )
        elif escape_vel_kms < 5.0:
            base_score = 0.3
            escape_note = (
                f"Low escape velocity ({escape_vel_kms:.1f} km/s), similar to Mars (5.0 km/s). "
                f"Light gases (H₂, He) escape rapidly; heavier gases slowly leak."
            )
        elif escape_vel_kms < 8.0:
            base_score = 0.6
            escape_note = (
                f"Moderate escape velocity ({escape_vel_kms:.1f} km/s). "
                f"Can retain N₂, O₂, CO₂ atmospheres but susceptible to loss over billions of years."
            )
        elif escape_vel_kms < 12.0:
            base_score = 0.85
            escape_note = (
                f"Earth-like escape velocity ({escape_vel_kms:.1f} km/s). "
                f"Excellent retention of all but lightest gases (H₂, He)."
            )
        elif escape_vel_kms < 20.0:
            base_score = 0.95
            escape_note = (
                f"High escape velocity ({escape_vel_kms:.1f} km/s). "
                f"Excellent atmospheric retention, even for hydrogen-rich atmospheres."
            )
        else:
            base_score = 0.8  # Very high may indicate mini-Neptune
            escape_note = (
                f"Very high escape velocity ({escape_vel_kms:.1f} km/s). "
                f"May retain primordial H/He envelope, suggesting gas-rich composition."
            )
        
        # Apply stellar activity penalty
        score = max(0.05, base_score - stellar_activity_penalty)
        
        full_explanation = f"{escape_note} {activity_note}"
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{escape_vel_kms:.1f}",
            input_unit="km/s (escape velocity)",
            optimal_range="8 - 15 km/s (Earth: 11.2 km/s)",
            explanation=full_explanation,
            confidence=ConfidenceLevel.MEDIUM,
        )


class MagneticFieldPotentialFactor(BaseScoringFactor):
    """
    Estimates the likelihood of a protective magnetic field.
    
    Scientific Rationale:
    --------------------
    Planetary magnetic fields protect against:
    - Stellar wind erosion of atmosphere
    - Surface radiation from cosmic rays
    - UV-induced atmospheric chemistry destruction
    
    Magnetic dynamo requirements:
    1. Electrically conductive fluid (liquid iron core)
    2. Convection (thermal or compositional)
    3. Rotation (Coriolis effect organizes flow)
    
    Indicators used:
    - Planet mass: Larger = more likely molten core
    - Density: Higher = more likely iron core
    - Age: Very old planets may have solidified cores
    - Rotation: Faster = stronger dynamo
    
    Limitations:
    - We cannot directly detect exoplanet magnetic fields (yet)
    - All estimates are probabilistic
    """
    
    @property
    def factor_id(self) -> str:
        return "magnetic_field"
    
    @property
    def factor_name(self) -> str:
        return "Magnetic Field Potential"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.DERIVED
    
    @property
    def description(self) -> str:
        return (
            "Estimates the probability of a protective magnetic field based on "
            "mass, density, and stellar age indicators."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Driscoll & Bercovici (2014) Physics Earth Planet Int 236:36-51",
            "Zuluaga et al. (2013) ApJ 770:23",
            "Tarduno et al. (2020) PNAS - Importance of magnetic fields",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate magnetic field potential."""
        
        mass = exoplanet.physical.mass_earth
        density = exoplanet.physical.estimate_density()
        radius = exoplanet.physical.radius_earth
        stellar_age = star.age_gyr
        
        # We need at least some mass/size indicator
        if mass is None and radius is None:
            return self._create_missing_data_result("planet_mass or planet_radius")
        
        # Start with base probability based on mass
        factors_contributing = []
        penalties = []
        
        if mass is not None:
            if mass < 0.2:
                mass_score = 0.2
                factors_contributing.append(
                    f"Very low mass ({mass:.2f} M⊕) suggests small iron core, unlikely to remain molten"
                )
            elif mass < 0.5:
                mass_score = 0.4
                factors_contributing.append(
                    f"Sub-Earth mass ({mass:.2f} M⊕) may have cooled core like Mars"
                )
            elif mass < 1.5:
                mass_score = 0.8
                factors_contributing.append(
                    f"Earth-like mass ({mass:.2f} M⊕) supports convecting liquid core"
                )
            elif mass < 5.0:
                mass_score = 0.9
                factors_contributing.append(
                    f"Super-Earth mass ({mass:.2f} M⊕) likely has vigorous core convection"
                )
            else:
                mass_score = 0.7  # May be gas-rich with no solid core
                factors_contributing.append(
                    f"High mass ({mass:.2f} M⊕) - if rocky, strong dynamo likely; if gas-rich, different dynamics"
                )
        else:
            # Estimate from radius
            if radius is not None:
                if radius < 0.7:
                    mass_score = 0.3
                    factors_contributing.append(f"Small radius ({radius:.2f} R⊕) suggests low mass")
                elif radius < 1.3:
                    mass_score = 0.75
                    factors_contributing.append(f"Earth-like radius ({radius:.2f} R⊕)")
                else:
                    mass_score = 0.6
                    factors_contributing.append(f"Larger radius ({radius:.2f} R⊕) - composition uncertain")
            else:
                mass_score = 0.5
        
        # Density indicator - higher density suggests metallic core
        if density is not None:
            if density > 5.0:
                density_bonus = 0.1
                factors_contributing.append(
                    f"High density ({density:.1f} g/cm³) indicates substantial iron core"
                )
            elif density > 4.0:
                density_bonus = 0.05
                factors_contributing.append(
                    f"Rocky density ({density:.1f} g/cm³) consistent with iron core"
                )
            elif density < 2.5:
                density_bonus = -0.2
                penalties.append(
                    f"Low density ({density:.1f} g/cm³) suggests ice-rich or gas-rich composition"
                )
            else:
                density_bonus = 0.0
        else:
            density_bonus = 0.0
        
        # Age consideration - very old planets may have cooled cores
        age_penalty = 0.0
        if stellar_age is not None:
            if stellar_age > 10.0:
                age_penalty = 0.15
                penalties.append(
                    f"Old system ({stellar_age:.1f} Gyr) - core may have solidified"
                )
            elif stellar_age > 8.0:
                age_penalty = 0.05
                penalties.append(
                    f"Mature system ({stellar_age:.1f} Gyr) - core cooling may be advanced"
                )
            elif stellar_age < 0.5:
                # Very young - dynamo may not be established yet
                age_penalty = 0.1
                penalties.append(
                    f"Very young system ({stellar_age:.1f} Gyr) - dynamo may still be establishing"
                )
        
        # Tidal locking consideration
        # Tidally locked planets rotate slowly, potentially weakening dynamo
        # However, tidal heating can maintain liquid core
        orbital_period = exoplanet.orbital.period_days
        tidal_note = ""
        tidal_adjustment = 0.0
        
        if orbital_period is not None and orbital_period < 30:
            stellar_teff = star.temperature_k or 5778
            if stellar_teff < 4000:  # M dwarf - likely tidally locked
                tidal_adjustment = -0.1
                tidal_note = (
                    "Short orbital period around cool star suggests tidal locking. "
                    "Slow rotation may weaken dynamo, but tidal heating maintains core heat."
                )
        
        # Calculate final score
        score = max(0.05, min(1.0, 
            mass_score + density_bonus - age_penalty + tidal_adjustment
        ))
        
        # Build explanation
        explanation_parts = []
        if factors_contributing:
            explanation_parts.append("Positive factors: " + "; ".join(factors_contributing))
        if penalties:
            explanation_parts.append("Negative factors: " + "; ".join(penalties))
        if tidal_note:
            explanation_parts.append(tidal_note)
        
        if score >= 0.7:
            summary = "Magnetic field likely present, providing atmospheric protection."
        elif score >= 0.4:
            summary = "Magnetic field possible but uncertain. Some atmospheric protection expected."
        else:
            summary = "Magnetic field unlikely. Atmosphere more vulnerable to stellar wind erosion."
        
        explanation_parts.append(summary)
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{score:.0%}",
            input_unit="estimated probability",
            optimal_range="High mass + high density + moderate age",
            explanation=" ".join(explanation_parts),
            confidence=ConfidenceLevel.LOW,  # Magnetic fields cannot be directly observed
        )
