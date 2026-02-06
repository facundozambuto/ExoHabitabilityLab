"""
Orbital Scoring Factors.

This module contains factors related to orbital dynamics:
- OrbitalEccentricityFactor: Climate stability from orbital shape
- TidalLockingFactor: Rotation state assessment

Scientific Background:
---------------------
Orbital dynamics significantly impact habitability:
1. Eccentricity causes temperature variations throughout the year
2. Tidal locking creates permanent day/night hemispheres
3. Orbital stability ensures long-term climate consistency

References:
- Williams & Pollard (2002) "Earth-like worlds on eccentric orbits"
- Barnes et al. (2008) "Habitability of eccentric orbits"
- Leconte et al. (2015) "Asynchronous rotation of Earth-mass planets"
"""

from typing import List
import math

from app.domain.entities.exoplanet import ExoplanetEntity
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import ConfidenceLevel
from app.domain.scoring.base import BaseScoringFactor, FactorResult, FactorCategory


class OrbitalEccentricityFactor(BaseScoringFactor):
    """
    Evaluates habitability based on orbital eccentricity.
    
    Scientific Rationale:
    --------------------
    Orbital eccentricity (e) affects climate stability:
    
    - e = 0: Perfect circle, stable temperatures
    - e = 0.01-0.1: Nearly circular, mild seasonal variation
    - e = 0.1-0.3: Moderate, significant seasonal effects
    - e = 0.3-0.5: High, extreme temperature swings
    - e > 0.5: Extreme, may leave habitable zone periodically
    
    Earth's eccentricity is ~0.017, very nearly circular.
    Mars has e = 0.093, causing significant seasonal variation.
    Mercury has e = 0.206.
    
    However, some models suggest moderate eccentricity could expand
    the habitable zone outward if the planet receives enough average flux.
    """
    
    @property
    def factor_id(self) -> str:
        return "orbital_eccentricity"
    
    @property
    def factor_name(self) -> str:
        return "Orbital Eccentricity"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.ORBITAL
    
    @property
    def description(self) -> str:
        return (
            "Assesses orbital shape for climate stability. Circular orbits "
            "provide stable temperatures; eccentric orbits cause extreme seasons."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Williams & Pollard (2002) IJAstrobiology 1:61-69",
            "Barnes et al. (2008) Astrobiology 8:557-568",
            "Dressing et al. (2010) ApJ 721:1295-1307",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate orbital eccentricity for climate stability."""
        
        ecc = exoplanet.orbital.eccentricity
        if ecc is None:
            return self._create_missing_data_result("orbital_eccentricity")
        
        # Calculate flux variation: max/min = ((1+e)/(1-e))²
        if ecc < 1.0:
            flux_ratio = ((1 + ecc) / (1 - ecc)) ** 2
        else:
            flux_ratio = float('inf')
        
        if ecc < 0.02:
            score = 1.0
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is nearly circular. "
                f"Earth's eccentricity is 0.017. Climate would be very stable "
                f"with minimal temperature variation from orbital position. "
                f"Stellar flux varies by only ~{(flux_ratio-1)*100:.1f}%."
            )
        elif ecc < 0.1:
            score = 0.9
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is low. Mars (e=0.093) shows "
                f"how this can cause notable but manageable seasonal variation. "
                f"Climate would remain stable enough for habitability. "
                f"Stellar flux varies by ~{(flux_ratio-1)*100:.1f}%."
            )
        elif ecc < 0.2:
            score = 0.7
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is moderate, similar to Mercury "
                f"(e=0.206). Significant seasonal temperature swings would occur. "
                f"Climate regulation mechanisms would be stressed. "
                f"Stellar flux varies by ~{(flux_ratio-1)*100:.0f}%."
            )
        elif ecc < 0.3:
            score = 0.5
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is high. Temperature difference "
                f"between closest approach (perihelion) and farthest point (aphelion) "
                f"would be extreme. Climate may be habitable on average but challenging. "
                f"Stellar flux varies by ~{(flux_ratio-1)*100:.0f}%."
            )
        elif ecc < 0.5:
            score = 0.25
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is very high. The planet may "
                f"leave the habitable zone for portions of its orbit, experiencing "
                f"freeze-thaw cycles. Long-term surface habitability is doubtful. "
                f"Stellar flux varies by ~{(flux_ratio-1)*100:.0f}%."
            )
        elif ecc < 0.8:
            score = 0.1
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is extreme. Such highly elliptical "
                f"orbits cause massive temperature swings. The planet alternates "
                f"between scorching perihelion and frozen aphelion passages. "
                f"Stellar flux varies by ~{(flux_ratio-1)*100:.0f}%."
            )
        else:
            score = 0.02
            explanation = (
                f"Orbital eccentricity ({ecc:.3f}) is near-parabolic. This orbit "
                f"is more like a comet than a planet. No stable climate is possible. "
                f"Surface conditions would be catastrophically variable."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{ecc:.3f}",
            input_unit="dimensionless (0=circle, 1=parabola)",
            optimal_range="0.0 - 0.1",
            explanation=explanation,
            confidence=ConfidenceLevel.HIGH,
        )


class TidalLockingFactor(BaseScoringFactor):
    """
    Evaluates habitability based on tidal locking potential.
    
    Scientific Rationale:
    --------------------
    Tidal locking occurs when a planet's rotation period equals its orbital
    period, resulting in one hemisphere always facing the star.
    
    Tidal locking timescale depends on:
    - Distance from star (closer = faster locking)
    - Planet mass (smaller = faster locking)  
    - Star mass (larger = faster locking)
    
    For M-dwarf habitable zones, tidal locking is expected.
    
    Habitability implications:
    - Permanent day side: extreme heat, potentially uninhabitable
    - Permanent night side: extreme cold, frozen
    - Terminator zone: potentially habitable twilight band
    - Atmosphere can redistribute heat (models show this works)
    
    Recent research (Leconte et al. 2015) suggests atmospheric circulation
    may prevent complete synchronization in some cases.
    """
    
    @property
    def factor_id(self) -> str:
        return "tidal_locking"
    
    @property
    def factor_name(self) -> str:
        return "Tidal Locking Potential"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.ORBITAL
    
    @property
    def description(self) -> str:
        return (
            "Estimates likelihood of tidal locking based on orbital distance "
            "and stellar type. Tidally locked planets may still be habitable "
            "if atmospheric heat redistribution is efficient."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Barnes (2017) Celestial Mechanics 129:509-536",
            "Leconte et al. (2015) Science 347:632-635",
            "Pierrehumbert & Hammond (2019) Annual Reviews",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate tidal locking potential."""
        
        # Get necessary parameters
        orbital_period = exoplanet.orbital.period_days
        semi_major_axis = exoplanet.orbital.semi_major_axis_au
        
        if orbital_period is None and semi_major_axis is None:
            return self._create_missing_data_result("orbital_period or semi_major_axis")
        
        # Estimate tidal locking based on stellar type and orbital distance
        spectral = star.spectral_class
        
        # Get star effective temperature as proxy for type
        teff = star.temperature_k
        
        # Estimate tidal locking probability
        # Planets within ~0.5 AU of M dwarfs are likely locked
        # Planets within ~0.3 AU of K dwarfs may be locked
        # Planets around G, F, A stars rarely lock in habitable zone
        
        lock_probability = 0.0
        lock_explanation = ""
        
        if semi_major_axis is not None:
            a = semi_major_axis
            
            if teff is not None:
                if teff < 3700:  # M dwarf
                    if a < 0.05:
                        lock_probability = 0.99
                    elif a < 0.1:
                        lock_probability = 0.95
                    elif a < 0.2:
                        lock_probability = 0.7
                    elif a < 0.5:
                        lock_probability = 0.3
                    else:
                        lock_probability = 0.05
                    lock_explanation = (
                        f"M dwarf host star (T_eff ~{teff:.0f} K) with planet at {a:.3f} AU. "
                        f"M dwarf habitable zones are close-in, promoting tidal locking."
                    )
                elif teff < 5200:  # K dwarf
                    if a < 0.1:
                        lock_probability = 0.8
                    elif a < 0.3:
                        lock_probability = 0.4
                    elif a < 0.5:
                        lock_probability = 0.1
                    else:
                        lock_probability = 0.02
                    lock_explanation = (
                        f"K dwarf host star (T_eff ~{teff:.0f} K) with planet at {a:.3f} AU. "
                        f"Moderate tidal locking risk for close-in orbits."
                    )
                elif teff < 6000:  # G dwarf (Sun-like)
                    if a < 0.1:
                        lock_probability = 0.5
                    elif a < 0.3:
                        lock_probability = 0.1
                    else:
                        lock_probability = 0.01
                    lock_explanation = (
                        f"G dwarf host star (T_eff ~{teff:.0f} K) like our Sun, with planet "
                        f"at {a:.3f} AU. Tidal locking unlikely in habitable zone."
                    )
                else:  # F, A stars
                    lock_probability = 0.01
                    lock_explanation = (
                        f"Hot star (T_eff ~{teff:.0f} K) with distant habitable zone. "
                        f"Tidal locking extremely unlikely at {a:.3f} AU."
                    )
            else:
                # No stellar temp, estimate from distance alone
                lock_probability = max(0, 1 - (a / 0.3))
                lock_explanation = f"Planet at {a:.3f} AU (stellar properties unknown)."
        else:
            # Use orbital period as proxy
            if orbital_period is not None:
                if orbital_period < 10:
                    lock_probability = 0.9
                elif orbital_period < 30:
                    lock_probability = 0.5
                elif orbital_period < 100:
                    lock_probability = 0.2
                else:
                    lock_probability = 0.05
                lock_explanation = (
                    f"Orbital period of {orbital_period:.1f} days. "
                    f"Shorter periods correlate with higher locking probability."
                )
        
        # Score based on tidal locking probability
        # Note: Tidal locking doesn't necessarily preclude habitability,
        # but it does reduce it. Score reflects this nuance.
        
        if lock_probability < 0.1:
            score = 1.0
            status = "Tidal locking very unlikely."
            habitability_note = (
                "Planet likely rotates freely, distributing heat like Earth. "
                "Day-night cycles support diverse ecosystems."
            )
        elif lock_probability < 0.3:
            score = 0.9
            status = "Tidal locking unlikely."
            habitability_note = (
                "Some tidal evolution may slow rotation, but full synchronization "
                "is improbable over typical planetary lifetimes."
            )
        elif lock_probability < 0.5:
            score = 0.7
            status = "Tidal locking possible."
            habitability_note = (
                "Planet may be in a spin-orbit resonance (like Mercury's 3:2) "
                "or slowly rotating. Climate effects would be intermediate."
            )
        elif lock_probability < 0.7:
            score = 0.6
            status = "Tidal locking likely."
            habitability_note = (
                "Synchronous rotation expected. Habitability depends on atmospheric "
                "heat transport. Terminator region may support life."
            )
        elif lock_probability < 0.9:
            score = 0.5
            status = "Tidal locking very likely."
            habitability_note = (
                "Planet almost certainly tidally locked. Models show thick atmospheres "
                "can redistribute heat, maintaining surface habitability."
            )
        else:
            score = 0.4
            status = "Tidal locking essentially certain."
            habitability_note = (
                "Permanent day and night hemispheres. The terminator zone provides "
                "a ring of potentially habitable temperatures. Atmospheric dynamics "
                "are critical for overall habitability."
            )
        
        full_explanation = f"{lock_explanation} {status} {habitability_note}"
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{lock_probability:.0%}",
            input_unit="estimated probability",
            optimal_range="<30% probability (free rotation preferred)",
            explanation=full_explanation,
            confidence=ConfidenceLevel.LOW,  # Tidal locking is hard to measure directly
        )
