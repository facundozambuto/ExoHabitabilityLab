"""
Stellar Scoring Factors.

This module contains factors related to the host star's properties:
- StellarTypeFactor: Evaluates spectral type for habitable zone stability
- StellarLuminosityFactor: Assesses luminosity class and stability
- StellarAgeFactor: Considers time for planetary evolution
- HabitableZonePositionFactor: Checks if planet is in the habitable zone

Scientific Background:
---------------------
The host star is fundamental to habitability because:
1. It determines the energy flux received by the planet
2. Spectral type affects UV radiation and flare activity
3. Stellar lifetime limits time available for life evolution
4. Habitable zone location and width depend on stellar luminosity

References:
- Kasting et al. (1993) "Habitable Zones around Main Sequence Stars"
- Kopparapu et al. (2013) "Habitable Zones around Main-Sequence Stars"
- Lingam & Loeb (2019) "Life in the Cosmos"
"""

from typing import List

from app.domain.entities.exoplanet import ExoplanetEntity
from app.domain.entities.star import StarEntity, SpectralClass, LuminosityClass
from app.domain.entities.habitability import ConfidenceLevel
from app.domain.scoring.base import BaseScoringFactor, FactorResult, FactorCategory


class StellarTypeFactor(BaseScoringFactor):
    """
    Evaluates habitability based on host star spectral type.
    
    Scientific Rationale:
    --------------------
    - G-type stars (like the Sun) provide stable radiation over ~10 Gyr
    - K-type stars are even more stable with 15-30+ Gyr lifetimes
    - M-type stars are most common but have issues:
      * Tidal locking due to close-in habitable zones
      * Frequent stellar flares stripping atmospheres
      * UV variability during flare events
    - O, B, A stars are too short-lived for complex life evolution
    
    Scoring:
    - G, K types: High scores (0.85-0.95)
    - F type: Moderate score (0.6)
    - M type: Lower score (0.4) due to tidal locking concerns
    - O, B, A: Low scores (0.05-0.2) due to short lifetimes
    """
    
    SPECTRAL_SCORES = {
        SpectralClass.O: 0.05,   # Very hot, ~1-10 Myr lifetime
        SpectralClass.B: 0.10,   # Hot, ~10-100 Myr lifetime
        SpectralClass.A: 0.20,   # ~100 Myr - 2 Gyr lifetime
        SpectralClass.F: 0.60,   # ~2-4 Gyr lifetime
        SpectralClass.G: 0.95,   # Sun-like, ~10 Gyr lifetime
        SpectralClass.K: 0.90,   # Orange dwarf, 15-30+ Gyr
        SpectralClass.M: 0.45,   # Red dwarf, but tidal locking issues
        SpectralClass.L: 0.10,   # Brown dwarf
        SpectralClass.T: 0.05,   # Cool brown dwarf
        SpectralClass.Y: 0.02,   # Coldest brown dwarfs
        SpectralClass.UNKNOWN: 0.50,
    }
    
    SPECTRAL_EXPLANATIONS = {
        SpectralClass.O: (
            "O-type stars are extremely luminous and hot (>30,000 K) with very short "
            "main-sequence lifetimes of only 1-10 million years. This is far too brief "
            "for even simple life to evolve (Earth took ~1 billion years for single-celled life). "
            "Additionally, intense UV radiation would be challenging for surface habitability."
        ),
        SpectralClass.B: (
            "B-type stars (10,000-30,000 K) have lifetimes of 10-100 million years. "
            "While some simple life might emerge, complex life evolution is unlikely "
            "given the limited time available. High UV flux poses additional challenges."
        ),
        SpectralClass.A: (
            "A-type stars (7,500-10,000 K) live 100 million to 2 billion years. "
            "Marginally sufficient for simple life, but complex multicellular organisms "
            "may not have time to evolve. The habitable zone is relatively wide."
        ),
        SpectralClass.F: (
            "F-type stars (6,000-7,500 K) have 2-4 billion year lifetimes. "
            "Sufficient time for life evolution, though less than Sun-like stars. "
            "The habitable zone is wider than for G-types, which is favorable."
        ),
        SpectralClass.G: (
            "G-type stars like our Sun (5,200-6,000 K) are considered optimal for "
            "habitability. They provide stable radiation for ~10 billion years, "
            "ample time for complex life to evolve. Earth orbits a G2V star, "
            "making this our only confirmed example of a life-bearing environment."
        ),
        SpectralClass.K: (
            "K-type orange dwarfs (3,700-5,200 K) are excellent for habitability. "
            "They have extremely stable luminosity, lifetimes of 15-30+ billion years "
            "(longer than the current age of the universe), lower UV emission, "
            "and wider habitable zones than M-dwarfs. Many astrobiologists consider "
            "K-dwarfs potentially superior to Sun-like stars for life."
        ),
        SpectralClass.M: (
            "M-type red dwarfs (2,400-3,700 K) are the most common stars but present "
            "habitability challenges. The habitable zone is very close to the star, "
            "likely causing tidal locking (one side always facing the star). "
            "Frequent stellar flares can strip planetary atmospheres. However, "
            "their extremely long lifetimes (trillions of years) provide ample "
            "evolution time if these challenges can be overcome."
        ),
        SpectralClass.L: (
            "L-type objects are very cool (1,300-2,400 K) brown dwarfs or the coolest "
            "red dwarfs. The habitable zone would be extremely close, virtually "
            "guaranteeing tidal locking and atmospheric stripping from stellar activity."
        ),
        SpectralClass.T: (
            "T-type brown dwarfs (550-1,300 K) lack sufficient luminosity to maintain "
            "a conventional habitable zone at any reasonable distance."
        ),
        SpectralClass.Y: (
            "Y-type objects are the coldest brown dwarfs (<550 K), with surface "
            "temperatures similar to planets. Not suitable for habitability assessment."
        ),
        SpectralClass.UNKNOWN: (
            "Stellar spectral type is unknown. Cannot assess host star suitability "
            "for supporting a habitable environment. Neutral score assigned."
        ),
    }
    
    @property
    def factor_id(self) -> str:
        return "stellar_type"
    
    @property
    def factor_name(self) -> str:
        return "Stellar Spectral Type"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STELLAR
    
    @property
    def description(self) -> str:
        return (
            "Evaluates the host star's spectral class for habitable zone stability, "
            "stellar lifetime, and radiation environment. G and K type main-sequence "
            "stars are considered most favorable for habitability."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Kasting et al. (1993) Icarus 101:108-128",
            "Lingam & Loeb (2019) 'Life in the Cosmos' Cambridge University Press",
            "Cuntz & Guinan (2016) ApJ 827:79",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate stellar type for habitability."""
        
        if not star.spectral_type:
            return self._create_missing_data_result("stellar_type")
        
        spectral_class = star.spectral_class
        score = self.SPECTRAL_SCORES.get(spectral_class, 0.5)
        explanation = self.SPECTRAL_EXPLANATIONS.get(spectral_class, "Unknown spectral class.")
        
        # Higher confidence for well-characterized spectral types
        if spectral_class in (SpectralClass.F, SpectralClass.G, SpectralClass.K, SpectralClass.M):
            confidence = ConfidenceLevel.HIGH
        elif spectral_class == SpectralClass.UNKNOWN:
            confidence = ConfidenceLevel.VERY_LOW
        else:
            confidence = ConfidenceLevel.MEDIUM
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=star.spectral_type,
            input_unit="Spectral Class",
            optimal_range="G0V - K5V",
            explanation=explanation,
            confidence=confidence,
        )


class StellarLuminosityFactor(BaseScoringFactor):
    """
    Evaluates habitability based on stellar luminosity class.
    
    Scientific Rationale:
    --------------------
    Main-sequence (dwarf) stars (luminosity class V) are most favorable because:
    - Stable hydrogen burning provides consistent energy output
    - Predictable habitable zone location
    - Long lifetimes for most spectral types
    
    Giants, supergiants, and evolved stars are problematic:
    - Variable luminosity disrupts habitable zones
    - Stellar wind and mass loss affect planetary atmospheres
    - Represents a transient phase in stellar evolution
    """
    
    LUMINOSITY_SCORES = {
        LuminosityClass.V: 1.0,     # Main-sequence - optimal
        LuminosityClass.IV: 0.5,    # Subgiant - transitioning
        LuminosityClass.VI: 0.7,    # Subdwarf - less luminous but stable
        LuminosityClass.III: 0.2,   # Giant - evolved, variable
        LuminosityClass.II: 0.1,    # Bright giant - highly evolved
        LuminosityClass.Ib: 0.05,   # Supergiant - short-lived phase
        LuminosityClass.Ia: 0.02,   # Luminous supergiant - very short-lived
        LuminosityClass.VII: 0.1,   # White dwarf - stellar remnant
        LuminosityClass.UNKNOWN: 0.5,
    }
    
    @property
    def factor_id(self) -> str:
        return "stellar_luminosity"
    
    @property
    def factor_name(self) -> str:
        return "Stellar Luminosity Class"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STELLAR
    
    @property
    def description(self) -> str:
        return (
            "Assesses whether the host star is in a stable evolutionary phase. "
            "Main-sequence (class V) stars provide stable energy output for billions "
            "of years, while evolved stars have variable luminosity and shorter remaining lifetimes."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Morgan & Keenan (1973) ARA&A 11:29-50",
            "Gray & Corbally (2009) 'Stellar Spectral Classification' Princeton",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate stellar luminosity class."""
        
        luminosity_class = star.luminosity_class
        score = self.LUMINOSITY_SCORES.get(luminosity_class, 0.5)
        
        if luminosity_class == LuminosityClass.V:
            explanation = (
                f"The host star is a main-sequence dwarf (class V), indicating stable "
                f"hydrogen core burning. This provides consistent luminosity output over "
                f"billions of years, allowing habitable zone stability."
            )
            confidence = ConfidenceLevel.HIGH
        elif luminosity_class == LuminosityClass.IV:
            explanation = (
                f"The host star is a subgiant (class IV), indicating it is beginning to "
                f"evolve off the main sequence. The habitable zone will shift outward "
                f"as luminosity increases over the next ~1 billion years."
            )
            confidence = ConfidenceLevel.MEDIUM
        elif luminosity_class in (LuminosityClass.III, LuminosityClass.II):
            explanation = (
                f"The host star is an evolved giant (class {luminosity_class.value}). "
                f"Giants have variable luminosity and short remaining lifetimes. "
                f"Any previously habitable planets would have been engulfed or sterilized."
            )
            confidence = ConfidenceLevel.HIGH
        elif luminosity_class in (LuminosityClass.Ia, LuminosityClass.Ib):
            explanation = (
                f"The host star is a supergiant (class {luminosity_class.value}), representing "
                f"a very short-lived phase before supernova. Not suitable for habitability."
            )
            confidence = ConfidenceLevel.HIGH
        elif luminosity_class == LuminosityClass.UNKNOWN:
            explanation = (
                f"Luminosity class unknown. Cannot determine stellar evolutionary state. "
                f"If spectral type includes 'V', the star is likely main-sequence."
            )
            confidence = ConfidenceLevel.LOW
        else:
            explanation = f"Stellar luminosity class: {luminosity_class.value}"
            confidence = ConfidenceLevel.MEDIUM
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=luminosity_class.value,
            input_unit="Luminosity Class",
            optimal_range="V (Main Sequence)",
            explanation=explanation,
            confidence=confidence,
        )


class StellarAgeFactor(BaseScoringFactor):
    """
    Evaluates habitability based on stellar age.
    
    Scientific Rationale:
    --------------------
    Stellar age is important because:
    - Young stars (<1 Gyr) have intense UV and flare activity
    - Very young planetary systems may still be undergoing bombardment
    - Complex life requires billions of years to evolve
    - Earth took ~4 Gyr to develop complex multicellular life
    
    Optimal range: 2-8 Gyr for Sun-like stars
    - Enough time for life to evolve
    - Before red giant phase begins
    """
    
    @property
    def factor_id(self) -> str:
        return "stellar_age"
    
    @property
    def factor_name(self) -> str:
        return "Stellar System Age"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STELLAR
    
    @property
    def description(self) -> str:
        return (
            "Considers the age of the stellar system for planetary evolution and "
            "life development timescales. Very young systems may still be too active, "
            "while optimal ages allow sufficient time for biological evolution."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Lineweaver (2001) Icarus 151:307-313",
            "Spiegel & Turner (2012) PNAS 109:395-400",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate stellar age for habitability."""
        
        if star.age_gyr is None:
            return self._create_missing_data_result("stellar_age_gyr")
        
        age = star.age_gyr
        
        # Scoring based on age
        if age < 0.5:
            score = 0.2
            explanation = (
                f"The system is very young ({age:.1f} Gyr). Young stars have intense "
                f"UV and X-ray emission, frequent flares, and the planetary system may "
                f"still be experiencing heavy bombardment. Complex life unlikely."
            )
        elif age < 1.0:
            score = 0.4
            explanation = (
                f"The system is relatively young ({age:.1f} Gyr). Stellar activity is "
                f"still elevated compared to mature stars. Simple life might emerge, "
                f"but complex life would require more time."
            )
        elif age < 2.0:
            score = 0.7
            explanation = (
                f"The system age ({age:.1f} Gyr) is approaching optimal for habitability. "
                f"Stellar activity has decreased and sufficient time exists for at least "
                f"simple life evolution (Earth had microbial life by ~3.5 Gya)."
            )
        elif age < 8.0:
            score = 1.0
            explanation = (
                f"The system age ({age:.1f} Gyr) is in the optimal range for habitability. "
                f"Sufficient time has passed for complex life evolution (Earth: ~4 Gyr), "
                f"and for Sun-like stars, the main-sequence phase continues."
            )
        elif age < 10.0:
            score = 0.7
            explanation = (
                f"The system is mature ({age:.1f} Gyr). For G-type stars, this is near "
                f"the end of stable main-sequence evolution. Still habitable, but "
                f"stellar luminosity may be increasing."
            )
        else:
            score = 0.4
            explanation = (
                f"The system is very old ({age:.1f} Gyr). Sun-like stars would be "
                f"evolving off the main sequence. K and M dwarfs remain stable, "
                f"but may have lost volatiles over time."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{age:.1f}",
            input_unit="Billion years (Gyr)",
            optimal_range="2-8 Gyr",
            explanation=explanation,
            confidence=ConfidenceLevel.MEDIUM,  # Stellar ages have uncertainties
        )


class HabitableZonePositionFactor(BaseScoringFactor):
    """
    Evaluates whether the planet is within the habitable zone.
    
    Scientific Rationale:
    --------------------
    The habitable zone (HZ) is the region where liquid water could exist
    on a planet's surface given sufficient atmospheric pressure.
    
    Two definitions are commonly used:
    - Conservative HZ: Runaway greenhouse to maximum greenhouse limits
    - Optimistic HZ: Recent Venus to early Mars limits
    
    Based on Kopparapu et al. (2013, 2014) calculations.
    """
    
    @property
    def factor_id(self) -> str:
        return "habitable_zone_position"
    
    @property
    def factor_name(self) -> str:
        return "Habitable Zone Position"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STELLAR
    
    @property
    def description(self) -> str:
        return (
            "Determines if the planet's orbital distance places it within the "
            "habitable zone where liquid water could exist on the surface. "
            "Based on climate models for Earth-like atmospheres."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Kopparapu et al. (2013) ApJ 765:131",
            "Kopparapu et al. (2014) ApJ 787:L29",
            "Kane & Gelino (2012) PASP 124:323-328",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate habitable zone position."""
        
        # Need orbital distance
        if exoplanet.orbital.semi_major_axis_au is None:
            return self._create_missing_data_result("semi_major_axis_au")
        
        distance_au = exoplanet.orbital.semi_major_axis_au
        
        # Calculate habitable zone
        hz = star.calculate_habitable_zone()
        if hz is None:
            return FactorResult(
                factor_id=self.factor_id,
                score=0.5,
                input_value=f"{distance_au:.3f}",
                input_unit="AU",
                explanation="Cannot calculate habitable zone without stellar luminosity data.",
                confidence=ConfidenceLevel.VERY_LOW,
                is_applicable=False,
                missing_data="stellar_luminosity",
            )
        
        cons_inner, cons_outer, opt_inner, opt_outer = hz
        position = star.get_hz_position(distance_au)
        
        if position == "conservative_hz":
            score = 1.0
            explanation = (
                f"The planet orbits at {distance_au:.3f} AU, firmly within the "
                f"conservative habitable zone ({cons_inner:.3f} - {cons_outer:.3f} AU). "
                f"Climate models suggest liquid water could exist on the surface "
                f"with an Earth-like atmosphere."
            )
        elif position == "optimistic_inner_edge":
            score = 0.7
            explanation = (
                f"The planet orbits at {distance_au:.3f} AU, in the optimistic inner "
                f"habitable zone (between {opt_inner:.3f} and {cons_inner:.3f} AU). "
                f"Conditions are warm but could support liquid water with a "
                f"thinner atmosphere or cloud feedback."
            )
        elif position == "optimistic_outer_edge":
            score = 0.7
            explanation = (
                f"The planet orbits at {distance_au:.3f} AU, in the optimistic outer "
                f"habitable zone (between {cons_outer:.3f} and {opt_outer:.3f} AU). "
                f"Liquid water possible with a thick CO₂ atmosphere providing "
                f"additional greenhouse warming."
            )
        elif position == "too_hot":
            # Calculate how far inside
            excess = (opt_inner - distance_au) / opt_inner
            score = max(0.0, 0.3 - excess)
            explanation = (
                f"The planet orbits at {distance_au:.3f} AU, inside the habitable zone "
                f"(inner edge: {opt_inner:.3f} AU). The planet likely experiences "
                f"runaway greenhouse conditions, with surface temperatures too high "
                f"for liquid water."
            )
        elif position == "too_cold":
            # Calculate how far outside
            excess = (distance_au - opt_outer) / opt_outer
            score = max(0.0, 0.3 - excess * 0.5)
            explanation = (
                f"The planet orbits at {distance_au:.3f} AU, outside the habitable zone "
                f"(outer edge: {opt_outer:.3f} AU). Surface water would be frozen "
                f"without extreme greenhouse warming."
            )
        else:
            score = 0.5
            explanation = f"Orbital distance: {distance_au:.3f} AU. HZ position uncertain."
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{distance_au:.3f}",
            input_unit="AU",
            optimal_range=f"{cons_inner:.3f} - {cons_outer:.3f} AU (conservative)",
            explanation=explanation,
            confidence=ConfidenceLevel.HIGH if hz else ConfidenceLevel.LOW,
        )
