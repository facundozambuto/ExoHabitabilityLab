"""
Planetary Scoring Factors.

This module contains factors related to the planet's physical properties:
- PlanetRadiusFactor: Evaluates size for rocky composition
- PlanetMassFactor: Assesses mass for atmosphere retention
- PlanetDensityFactor: Infers composition from bulk density
- EquilibriumTemperatureFactor: Surface temperature proxy
- SurfaceGravityFactor: Gravity effects on atmosphere and life

Scientific Background:
---------------------
Planet physical properties are crucial for habitability:
1. Size determines likelihood of rocky vs gaseous composition
2. Mass affects atmosphere retention and geological activity
3. Density reveals composition (rocky, icy, gaseous)
4. Temperature determines surface conditions
5. Gravity affects atmosphere scale height and life evolution

References:
- Fulton et al. (2017) "The California-Kepler Survey" - Radius gap
- Chen & Kipping (2017) "Probabilistic Forecasting of the Masses and Radii"
- Kaltenegger (2017) "How to Characterize Habitable Worlds and Signs of Life"
"""

from typing import List
import math

from app.domain.entities.exoplanet import ExoplanetEntity, PlanetType
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import ConfidenceLevel
from app.domain.scoring.base import BaseScoringFactor, FactorResult, FactorCategory


class PlanetRadiusFactor(BaseScoringFactor):
    """
    Evaluates habitability based on planet radius.
    
    Scientific Rationale:
    --------------------
    Planet radius is a primary indicator of composition:
    
    - <1.0 R⊕: Terrestrial, definitely rocky (Mars, Mercury, Venus)
    - 1.0-1.75 R⊕: Super-Earths, likely rocky with thicker atmospheres
    - 1.75-3.5 R⊕: Sub-Neptunes, likely significant H/He envelope
    - >3.5 R⊕: Neptune-like or gas giants, no solid surface
    
    The "radius gap" at ~1.75 R⊕ (Fulton gap) represents the boundary
    between rocky planets and those with substantial volatile envelopes.
    """
    
    @property
    def factor_id(self) -> str:
        return "planet_radius"
    
    @property
    def factor_name(self) -> str:
        return "Planet Radius"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PLANETARY
    
    @property
    def description(self) -> str:
        return (
            "Assesses planet size to determine likelihood of rocky composition "
            "and atmosphere retention. Earth-sized to super-Earth sizes are optimal."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Fulton et al. (2017) AJ 154:109 - California-Kepler Survey",
            "Chen & Kipping (2017) ApJ 834:17",
            "Rogers (2015) ApJ 801:41 - Rocky/volatile boundary",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate planet radius for habitability."""
        
        radius = exoplanet.physical.radius_earth
        if radius is None:
            return self._create_missing_data_result("planet_radius_earth")
        
        planet_type = exoplanet.physical.classify_planet_type()
        
        # Scoring based on radius
        if radius < 0.5:
            score = 0.3
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) is significantly smaller than Earth. "
                f"Very small planets like Mars ({0.53:.2f} R⊕) struggle to retain "
                f"atmospheres due to low gravity and lack of magnetic field. "
                f"Habitability is possible but challenging."
            )
        elif radius < 0.8:
            score = 0.6
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) suggests a Mars-to-Earth sized world. "
                f"Atmospheric retention is possible but surface gravity and geological "
                f"activity may be reduced compared to Earth."
            )
        elif radius < 1.25:
            score = 1.0
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) is Earth-like. This is the optimal "
                f"size range for rocky composition with substantial atmosphere. "
                f"Earth (1.0 R⊕) is our only confirmed habitable example."
            )
        elif radius < 1.75:
            score = 0.85
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) indicates a super-Earth. "
                f"Planets below the Fulton gap (~1.75 R⊕) are likely rocky with "
                f"potentially thicker atmospheres. Higher surface gravity may "
                f"affect life evolution but not necessarily habitability."
            )
        elif radius < 2.5:
            score = 0.4
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) is in the sub-Neptune regime, "
                f"above the Fulton radius gap. These planets likely have significant "
                f"H/He envelopes. Traditional surface habitability is unlikely, "
                f"though exotic scenarios (subsurface oceans) are possible."
            )
        elif radius < 4.0:
            score = 0.15
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) indicates a Neptune-like world. "
                f"These are ice giants with deep gaseous envelopes. No solid surface "
                f"exists for traditional habitability, though moons could be habitable."
            )
        else:
            score = 0.05
            explanation = (
                f"Planet radius ({radius:.2f} R⊕) indicates a gas giant similar to "
                f"Jupiter ({11.2:.1f} R⊕) or Saturn ({9.4:.1f} R⊕). No solid surface "
                f"exists. Any habitability would be limited to moons, not the planet itself."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{radius:.2f}",
            input_unit="Earth radii (R⊕)",
            optimal_range="0.8 - 1.6 R⊕",
            explanation=explanation,
            confidence=ConfidenceLevel.HIGH,
        )


class PlanetMassFactor(BaseScoringFactor):
    """
    Evaluates habitability based on planet mass.
    
    Scientific Rationale:
    --------------------
    Planet mass is critical because:
    - Determines surface gravity
    - Affects atmospheric retention (escape velocity)
    - Influences geological activity (internal heat)
    - Impacts plate tectonics possibility
    
    Optimal range: 0.5 - 5 M⊕
    - Below 0.5 M⊕: Difficulty retaining atmosphere (Mars is 0.11 M⊕)
    - Above 5 M⊕: May have significant H/He envelope
    - Above 10 M⊕: Likely mini-Neptune composition
    """
    
    @property
    def factor_id(self) -> str:
        return "planet_mass"
    
    @property
    def factor_name(self) -> str:
        return "Planet Mass"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PLANETARY
    
    @property
    def description(self) -> str:
        return (
            "Evaluates planet mass for atmosphere retention capability, "
            "geological activity potential, and likelihood of rocky composition."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Lopez & Fortney (2014) ApJ 792:1 - Mass-radius relations",
            "Dorn et al. (2017) A&A 597:A37 - Interior structure",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate planet mass for habitability."""
        
        mass = exoplanet.physical.mass_earth
        if mass is None:
            return self._create_missing_data_result("planet_mass_earth")
        
        if mass < 0.1:
            score = 0.15
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) is very low, similar to Mars (0.11 M⊕). "
                f"Such low mass results in weak gravity, making long-term atmospheric "
                f"retention extremely difficult without a strong magnetic field."
            )
        elif mass < 0.5:
            score = 0.4
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) is sub-Earth. Atmospheric retention "
                f"is challenging but possible. Reduced geological activity may "
                f"limit carbon cycling and magnetic dynamo generation."
            )
        elif mass < 2.0:
            score = 1.0
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) is Earth-like. This is optimal for "
                f"rocky composition with sufficient gravity for atmospheric retention "
                f"and likely active geology supporting a carbon cycle."
            )
        elif mass < 5.0:
            score = 0.8
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) indicates a super-Earth. Rocky composition "
                f"is still likely. Higher surface gravity may affect life evolution "
                f"but enhances atmospheric retention."
            )
        elif mass < 10.0:
            score = 0.4
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) is at the upper limit for rocky planets. "
                f"May have accreted a significant volatile envelope during formation. "
                f"Composition uncertain without density measurement."
            )
        else:
            score = 0.1
            explanation = (
                f"Planet mass ({mass:.2f} M⊕) strongly suggests a mini-Neptune or "
                f"larger. Neptune is 17 M⊕. Such massive planets almost certainly "
                f"have thick gaseous envelopes with no accessible solid surface."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{mass:.2f}",
            input_unit="Earth masses (M⊕)",
            optimal_range="0.5 - 5.0 M⊕",
            explanation=explanation,
            confidence=ConfidenceLevel.HIGH,
        )


class PlanetDensityFactor(BaseScoringFactor):
    """
    Evaluates habitability based on bulk density.
    
    Scientific Rationale:
    --------------------
    Bulk density reveals planetary composition:
    
    - >5 g/cm³: Iron-rich, rocky (Earth: 5.51, Mercury: 5.43)
    - 3-5 g/cm³: Rocky with less iron (Mars: 3.93)
    - 1-3 g/cm³: Ice-rock mixture or water world
    - <1 g/cm³: Significant H/He envelope (Saturn: 0.69)
    
    For habitability, rocky composition (>3 g/cm³) is preferred.
    """
    
    @property
    def factor_id(self) -> str:
        return "planet_density"
    
    @property
    def factor_name(self) -> str:
        return "Planet Bulk Density"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PLANETARY
    
    @property
    def description(self) -> str:
        return (
            "Infers planetary composition from bulk density. Rocky planets "
            "have densities >3 g/cm³, while gas-rich planets are less dense."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Zeng et al. (2016) ApJ 819:127 - Mass-radius-composition",
            "Fortney et al. (2007) ApJ 659:1661 - Planetary structure",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate planet density for composition."""
        
        # Try measured density or estimate from mass/radius
        density = exoplanet.physical.estimate_density()
        
        if density is None:
            return self._create_missing_data_result("planet_density")
        
        if density < 1.0:
            score = 0.05
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) is very low, indicating a "
                f"gas-dominated composition. For reference, Saturn's density is "
                f"0.69 g/cm³. No solid surface likely exists."
            )
        elif density < 2.0:
            score = 0.2
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) suggests significant volatile "
                f"content. May be a water world or have a thick H/He atmosphere. "
                f"Neptune's density is 1.64 g/cm³."
            )
        elif density < 3.5:
            score = 0.5
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) indicates an ice-rock mixture "
                f"or low-iron rocky composition. Could be a water world with "
                f"a deep ocean. Mars density is 3.93 g/cm³."
            )
        elif density < 5.0:
            score = 0.85
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) suggests rocky composition "
                f"similar to Mars (3.93 g/cm³). Iron core may be smaller than Earth's. "
                f"Suitable for surface habitability."
            )
        elif density < 6.5:
            score = 1.0
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) is Earth-like (5.51 g/cm³). "
                f"This indicates rocky composition with an iron-nickel core. "
                f"Optimal for habitability with a solid surface."
            )
        else:
            score = 0.7
            explanation = (
                f"Bulk density ({density:.2f} g/cm³) is higher than Earth, suggesting "
                f"an iron-rich composition (Mercury: 5.43 g/cm³). Rocky with possible "
                f"large metallic core. Surface habitability possible."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{density:.2f}",
            input_unit="g/cm³",
            optimal_range="4.0 - 6.0 g/cm³",
            explanation=explanation,
            confidence=ConfidenceLevel.MEDIUM,  # Density often estimated
        )


class EquilibriumTemperatureFactor(BaseScoringFactor):
    """
    Evaluates habitability based on equilibrium temperature.
    
    Scientific Rationale:
    --------------------
    Equilibrium temperature (T_eq) is calculated assuming no atmosphere:
    T_eq = T_star × sqrt(R_star / 2a) × (1 - A)^0.25
    
    where A is albedo and a is semi-major axis.
    
    For habitability with liquid water:
    - Optimal: 230-310 K (with moderate greenhouse effect)
    - Extended: 180-350 K (with extreme atmospheric adjustment)
    
    Earth's T_eq is ~255 K, actual surface is ~288 K (greenhouse effect).
    """
    
    @property
    def factor_id(self) -> str:
        return "equilibrium_temperature"
    
    @property
    def factor_name(self) -> str:
        return "Equilibrium Temperature"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PLANETARY
    
    @property
    def description(self) -> str:
        return (
            "Assesses the planet's temperature without atmospheric effects. "
            "Actual surface temperature depends on atmosphere composition. "
            "Optimal range allows liquid water with Earth-like atmosphere."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Kasting et al. (1993) Icarus 101:108-128",
            "Kopparapu et al. (2013) ApJ 765:131",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate equilibrium temperature."""
        
        temp = exoplanet.physical.equilibrium_temp_k
        if temp is None:
            return self._create_missing_data_result("equilibrium_temp_k")
        
        # Temperature scoring with gradual transitions
        if temp < 150:
            score = 0.05
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is extremely cold. "
                f"Surface water would be permanently frozen. Even with strong "
                f"greenhouse effects, liquid water at the surface is unlikely. "
                f"Subsurface oceans might exist (like Europa at ~100 K)."
            )
        elif temp < 200:
            score = 0.3
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is very cold. "
                f"A very thick CO₂ atmosphere would be needed for liquid water. "
                f"This is colder than early Mars scenarios."
            )
        elif temp < 230:
            score = 0.6
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is at the outer edge "
                f"of habitability. With a CO₂-rich atmosphere providing strong "
                f"greenhouse warming, liquid water could potentially exist."
            )
        elif temp < 260:
            score = 0.9
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is in the optimal range. "
                f"Earth's T_eq is ~255 K, with greenhouse warming raising actual "
                f"surface temperature to ~288 K. Similar conditions expected."
            )
        elif temp < 300:
            score = 1.0
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is excellent for habitability. "
                f"With an Earth-like atmosphere, surface temperatures would support "
                f"liquid water across much of the planet."
            )
        elif temp < 350:
            score = 0.6
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is warm. Liquid water "
                f"possible with a thin atmosphere or high albedo clouds, but "
                f"risk of runaway greenhouse effect exists."
            )
        elif temp < 450:
            score = 0.2
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is hot. Surface conditions "
                f"would be harsh. Venus (T_eq ~230 K) has surface temp of 737 K "
                f"due to runaway greenhouse. Habitability very unlikely."
            )
        else:
            score = 0.02
            explanation = (
                f"Equilibrium temperature ({temp:.0f} K) is extremely hot. "
                f"This planet likely has molten surface or is a 'lava world'. "
                f"No possibility of liquid water at the surface."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{temp:.0f}",
            input_unit="Kelvin",
            optimal_range="230 - 300 K",
            explanation=explanation,
            confidence=ConfidenceLevel.MEDIUM,
        )


class SurfaceGravityFactor(BaseScoringFactor):
    """
    Evaluates habitability based on surface gravity.
    
    Scientific Rationale:
    --------------------
    Surface gravity affects:
    - Atmosphere retention (higher g = better retention)
    - Atmospheric scale height (higher g = denser atmosphere at surface)
    - Biological evolution (organisms must work against gravity)
    - Geological processes (volcanism, tectonics)
    
    Earth's surface gravity is 9.81 m/s² (1.0 g).
    Range 0.5-2.5 g is considered potentially habitable for Earth-like life.
    """
    
    @property
    def factor_id(self) -> str:
        return "surface_gravity"
    
    @property
    def factor_name(self) -> str:
        return "Surface Gravity"
    
    @property
    def category(self) -> FactorCategory:
        return FactorCategory.PLANETARY
    
    @property
    def description(self) -> str:
        return (
            "Assesses surface gravity for atmospheric retention and biological "
            "compatibility. Moderate gravity (0.5-2.5 g) is considered optimal."
        )
    
    @property
    def references(self) -> List[str]:
        return [
            "Heller & Armstrong (2014) Astrobiology 14:50-66 - Superhabitable worlds",
        ]
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate surface gravity."""
        
        gravity = exoplanet.physical.surface_gravity_earth
        if gravity is None:
            return self._create_missing_data_result("surface_gravity")
        
        if gravity < 0.3:
            score = 0.3
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is very low. Atmospheric "
                f"retention would be difficult. Mars (0.38 g) has lost most of "
                f"its atmosphere. Life could exist but face significant challenges."
            )
        elif gravity < 0.7:
            score = 0.6
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is below Earth's but potentially "
                f"habitable. Atmosphere may be thinner and more easily lost to space. "
                f"Life would need to adapt to lower gravity."
            )
        elif gravity < 1.5:
            score = 1.0
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is Earth-like. This is optimal "
                f"for atmospheric retention and compatible with Earth-like biology. "
                f"Geological processes would be similar to Earth."
            )
        elif gravity < 2.5:
            score = 0.7
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is elevated but potentially "
                f"habitable. Stronger atmospheric retention but biological organisms "
                f"would need adaptations. Flight would be more difficult."
            )
        elif gravity < 4.0:
            score = 0.3
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is very high. While atmospheric "
                f"retention is excellent, extreme gravity poses challenges for "
                f"biological structures. Complex life may struggle."
            )
        else:
            score = 0.1
            explanation = (
                f"Surface gravity ({gravity:.2f} g) is extreme. Even with solid "
                f"surface (if any), such high gravity would severely limit biological "
                f"evolution and may indicate a very dense composition."
            )
        
        return FactorResult(
            factor_id=self.factor_id,
            score=score,
            input_value=f"{gravity:.2f}",
            input_unit="g (Earth = 1.0)",
            optimal_range="0.7 - 1.5 g",
            explanation=explanation,
            confidence=ConfidenceLevel.MEDIUM,  # Depends on mass/radius accuracy
        )
