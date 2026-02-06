"""
Star Domain Entity.

This module defines the StarEntity class representing host stars
with all their astrophysical properties relevant to habitability.

Scientific Notes:
-----------------
The host star is crucial for habitability assessment because:
1. It determines the habitable zone location and width
2. Stellar type affects UV radiation and flare activity
3. Stellar age impacts planetary evolution time
4. Stellar mass determines main-sequence lifetime

Spectral Classification (Morgan-Keenan system):
- O, B, A: Hot, massive, short-lived (generally unfavorable)
- F: Warm, reasonable lifetime
- G: Sun-like (optimal)
- K: Cooler, very stable, long-lived (favorable)
- M: Red dwarfs, most common, long-lived but issues with tidal locking

Luminosity Classes:
- I: Supergiants
- II: Bright giants
- III: Giants
- IV: Subgiants
- V: Main-sequence (dwarfs) - most relevant for habitability
- VI: Subdwarfs
- VII: White dwarfs

References:
- Kasting et al. (1993) "Habitable Zones around Main Sequence Stars"
- Kopparapu et al. (2013, 2014) "Habitable Zone Calculations"
- Lingam & Loeb (2019) "Life in the Cosmos"
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum
import math


class SpectralClass(str, Enum):
    """Main spectral classes in order of decreasing temperature."""
    O = "O"  # > 30,000 K, blue
    B = "B"  # 10,000 - 30,000 K, blue-white
    A = "A"  # 7,500 - 10,000 K, white
    F = "F"  # 6,000 - 7,500 K, yellow-white
    G = "G"  # 5,200 - 6,000 K, yellow (Sun)
    K = "K"  # 3,700 - 5,200 K, orange
    M = "M"  # 2,400 - 3,700 K, red
    L = "L"  # 1,300 - 2,400 K, brown dwarf
    T = "T"  # 550 - 1,300 K, brown dwarf
    Y = "Y"  # < 550 K, coldest brown dwarfs
    UNKNOWN = "UNKNOWN"


class LuminosityClass(str, Enum):
    """Morgan-Keenan luminosity classes."""
    Ia = "Ia"    # Luminous supergiants
    Ib = "Ib"    # Less luminous supergiants
    II = "II"    # Bright giants
    III = "III"  # Giants
    IV = "IV"    # Subgiants
    V = "V"      # Main-sequence (dwarfs)
    VI = "VI"    # Subdwarfs
    VII = "VII"  # White dwarfs
    UNKNOWN = "UNKNOWN"


@dataclass
class StarEntity:
    """
    Domain entity representing a host star.
    
    Contains all astrophysical properties of a star relevant
    for exoplanet habitability assessment.
    
    Attributes:
        name: Star designation
        spectral_type: Full spectral classification (e.g., "G2V")
        mass_solar: Mass in solar masses (M☉)
        radius_solar: Radius in solar radii (R☉)
        temperature_k: Effective temperature in Kelvin
        luminosity_solar: Luminosity in solar luminosities (L☉)
        metallicity: [Fe/H] metallicity index
        age_gyr: Age in billions of years
    """
    
    name: str = ""
    spectral_type: Optional[str] = None
    mass_solar: Optional[float] = None
    radius_solar: Optional[float] = None
    temperature_k: Optional[float] = None
    luminosity_solar: Optional[float] = None  # Can be in log or linear scale
    luminosity_log: Optional[float] = None    # Log(L/L☉)
    metallicity: Optional[float] = None       # [Fe/H]
    age_gyr: Optional[float] = None
    
    # Solar constants for reference
    SOLAR_TEMP_K = 5778
    SOLAR_MASS_KG = 1.989e30
    SOLAR_RADIUS_KM = 696340
    SOLAR_LUMINOSITY_W = 3.828e26
    
    @property
    def spectral_class(self) -> SpectralClass:
        """
        Extract the primary spectral class from the full type.
        
        Examples:
            "G2V" -> SpectralClass.G
            "K5" -> SpectralClass.K
            "M3.5V" -> SpectralClass.M
        """
        if not self.spectral_type:
            return SpectralClass.UNKNOWN
        
        first_char = self.spectral_type[0].upper()
        try:
            return SpectralClass(first_char)
        except ValueError:
            return SpectralClass.UNKNOWN
    
    @property
    def luminosity_class(self) -> LuminosityClass:
        """
        Extract the luminosity class from the full spectral type.
        
        Examples:
            "G2V" -> LuminosityClass.V
            "K3III" -> LuminosityClass.III
            "F5IV" -> LuminosityClass.IV
        """
        if not self.spectral_type:
            return LuminosityClass.UNKNOWN
        
        # Look for Roman numerals at the end
        spec = self.spectral_type.upper()
        
        if "VII" in spec:
            return LuminosityClass.VII
        elif "VI" in spec:
            return LuminosityClass.VI
        elif "IV" in spec:
            return LuminosityClass.IV
        elif "III" in spec:
            return LuminosityClass.III
        elif "II" in spec:
            return LuminosityClass.II
        elif "IB" in spec:
            return LuminosityClass.Ib
        elif "IA" in spec:
            return LuminosityClass.Ia
        elif "V" in spec:
            return LuminosityClass.V
        
        return LuminosityClass.UNKNOWN
    
    @property
    def is_main_sequence(self) -> bool:
        """Check if star is a main-sequence dwarf (luminosity class V)."""
        return self.luminosity_class == LuminosityClass.V
    
    @property
    def luminosity_linear(self) -> Optional[float]:
        """
        Get luminosity in linear solar units.
        
        NASA data often provides log(L/L☉), so convert if needed.
        """
        if self.luminosity_solar is not None:
            return self.luminosity_solar
        if self.luminosity_log is not None:
            return 10 ** self.luminosity_log
        return None
    
    def estimate_luminosity(self) -> Optional[float]:
        """
        Estimate luminosity from temperature and radius if not directly available.
        
        Uses Stefan-Boltzmann law: L = 4πR²σT⁴
        In solar units: L/L☉ = (R/R☉)² × (T/T☉)⁴
        """
        if self.luminosity_linear is not None:
            return self.luminosity_linear
        
        if self.radius_solar is not None and self.temperature_k is not None:
            return (self.radius_solar ** 2) * ((self.temperature_k / self.SOLAR_TEMP_K) ** 4)
        
        return None
    
    def estimate_main_sequence_lifetime_gyr(self) -> Optional[float]:
        """
        Estimate main-sequence lifetime based on stellar mass.
        
        Approximation: t_ms ≈ 10 × (M/M☉)^(-2.5) billion years
        
        This assumes hydrogen burning efficiency scales with mass.
        The Sun's main-sequence lifetime is ~10 Gyr.
        """
        if self.mass_solar is None or self.mass_solar <= 0:
            return None
        
        return 10.0 * (self.mass_solar ** -2.5)
    
    def calculate_habitable_zone(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculate the habitable zone boundaries around this star.
        
        Returns inner/outer boundaries for both conservative and optimistic
        habitable zones based on Kopparapu et al. (2013, 2014).
        
        Returns:
            Tuple of (conservative_inner_au, conservative_outer_au,
                      optimistic_inner_au, optimistic_outer_au)
            or None if luminosity cannot be determined
            
        Scientific Background:
        - Conservative HZ: "Runaway Greenhouse" to "Maximum Greenhouse"
        - Optimistic HZ: "Recent Venus" to "Early Mars" limits
        """
        luminosity = self.estimate_luminosity()
        if luminosity is None:
            return None
        
        # Kopparapu et al. (2013) stellar flux boundaries (S_eff)
        # These are for a 1 M_Earth planet
        # Inner edge: Recent Venus / Runaway Greenhouse
        # Outer edge: Early Mars / Maximum Greenhouse
        
        teff = self.temperature_k if self.temperature_k else self.SOLAR_TEMP_K
        t_star = teff - 5780  # Offset from solar temperature
        
        # Polynomial coefficients for stellar flux (Kopparapu 2014)
        # S_eff = S_eff_sun + a*T_star + b*T_star^2 + c*T_star^3 + d*T_star^4
        
        # Recent Venus (optimistic inner)
        s_recent_venus = 1.7763 + 1.4335e-4*t_star + 3.3954e-9*t_star**2 - 7.6364e-12*t_star**3 - 1.1950e-15*t_star**4
        
        # Runaway Greenhouse (conservative inner)
        s_runaway = 1.0385 + 1.2456e-4*t_star + 1.4612e-8*t_star**2 - 7.6345e-12*t_star**3 - 1.7511e-15*t_star**4
        
        # Maximum Greenhouse (conservative outer)
        s_max_greenhouse = 0.3507 + 5.9578e-5*t_star + 1.6707e-9*t_star**2 - 3.0058e-12*t_star**3 - 5.1925e-16*t_star**4
        
        # Early Mars (optimistic outer)
        s_early_mars = 0.3207 + 5.4471e-5*t_star + 1.5275e-9*t_star**2 - 2.1709e-12*t_star**3 - 3.8282e-16*t_star**4
        
        # Convert stellar flux to distance: d = sqrt(L / S_eff)
        sqrt_l = math.sqrt(luminosity)
        
        conservative_inner = sqrt_l / math.sqrt(s_runaway) if s_runaway > 0 else None
        conservative_outer = sqrt_l / math.sqrt(s_max_greenhouse) if s_max_greenhouse > 0 else None
        optimistic_inner = sqrt_l / math.sqrt(s_recent_venus) if s_recent_venus > 0 else None
        optimistic_outer = sqrt_l / math.sqrt(s_early_mars) if s_early_mars > 0 else None
        
        if all(v is not None for v in [conservative_inner, conservative_outer, optimistic_inner, optimistic_outer]):
            return (conservative_inner, conservative_outer, optimistic_inner, optimistic_outer)
        
        return None
    
    def is_in_habitable_zone(self, distance_au: float, conservative: bool = True) -> Optional[bool]:
        """
        Check if a given orbital distance is within the habitable zone.
        
        Args:
            distance_au: Orbital semi-major axis in AU
            conservative: Use conservative (True) or optimistic (False) boundaries
            
        Returns:
            True if in HZ, False if not, None if HZ cannot be calculated
        """
        hz = self.calculate_habitable_zone()
        if hz is None:
            return None
        
        cons_inner, cons_outer, opt_inner, opt_outer = hz
        
        if conservative:
            return cons_inner <= distance_au <= cons_outer
        else:
            return opt_inner <= distance_au <= opt_outer
    
    def get_hz_position(self, distance_au: float) -> Optional[str]:
        """
        Describe the position relative to the habitable zone.
        
        Returns:
            String description of position (e.g., "conservative_hz", "inner_edge", etc.)
        """
        hz = self.calculate_habitable_zone()
        if hz is None:
            return None
        
        cons_inner, cons_outer, opt_inner, opt_outer = hz
        
        if distance_au < opt_inner:
            return "too_hot"
        elif distance_au < cons_inner:
            return "optimistic_inner_edge"
        elif distance_au <= cons_outer:
            return "conservative_hz"
        elif distance_au <= opt_outer:
            return "optimistic_outer_edge"
        else:
            return "too_cold"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.spectral_type or 'Unknown type'})"
    
    def __repr__(self) -> str:
        return (
            f"StarEntity(name='{self.name}', type='{self.spectral_type}', "
            f"mass={self.mass_solar}M☉, temp={self.temperature_k}K)"
        )
