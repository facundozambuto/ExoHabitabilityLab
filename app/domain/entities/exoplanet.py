"""
Exoplanet Domain Entity.

This module defines the core ExoplanetEntity class representing
an exoplanet with all its astrophysical properties. This is a
domain object independent of database or API concerns.

Scientific Notes:
-----------------
Exoplanets are planets orbiting stars other than our Sun. Key parameters
for habitability assessment include:

- Orbital parameters: Period, semi-major axis, eccentricity
- Physical parameters: Mass, radius, density, temperature
- Host star properties: Spectral type, luminosity, age

References:
- Seager, S. (2010) "Exoplanets" - University of Arizona Press
- Perryman, M. (2018) "The Exoplanet Handbook" - Cambridge University Press
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import math


class PlanetType(str, Enum):
    """
    Classification of exoplanets by size and composition.
    
    Based on mass-radius relationships from Fulton et al. (2017)
    and Chen & Kipping (2017).
    """
    TERRESTRIAL = "terrestrial"          # < 1.0 R⊕, likely rocky
    SUPER_EARTH = "super_earth"          # 1.0 - 1.75 R⊕, rocky/volatile mix
    SUB_NEPTUNE = "sub_neptune"          # 1.75 - 3.5 R⊕, significant H/He envelope
    NEPTUNE_LIKE = "neptune_like"        # 3.5 - 6.0 R⊕, ice giant
    GAS_GIANT = "gas_giant"              # > 6.0 R⊕, Jupiter-like
    UNKNOWN = "unknown"


@dataclass
class OrbitalParameters:
    """
    Orbital characteristics of an exoplanet.
    
    Attributes:
        period_days: Orbital period in Earth days
        semi_major_axis_au: Distance from star in Astronomical Units
        eccentricity: Orbital eccentricity (0 = circular, 1 = parabolic)
        inclination_deg: Orbital inclination in degrees (90° = edge-on)
    """
    period_days: Optional[float] = None
    semi_major_axis_au: Optional[float] = None
    eccentricity: Optional[float] = None
    inclination_deg: Optional[float] = None
    
    @property
    def is_circular(self) -> bool:
        """Check if orbit is approximately circular (e < 0.1)."""
        return self.eccentricity is not None and self.eccentricity < 0.1
    
    @property
    def is_highly_eccentric(self) -> bool:
        """Check if orbit is highly eccentric (e > 0.3)."""
        return self.eccentricity is not None and self.eccentricity > 0.3
    
    def periastron_distance_au(self) -> Optional[float]:
        """Calculate closest approach to star."""
        if self.semi_major_axis_au is None or self.eccentricity is None:
            return None
        return self.semi_major_axis_au * (1 - self.eccentricity)
    
    def apastron_distance_au(self) -> Optional[float]:
        """Calculate farthest distance from star."""
        if self.semi_major_axis_au is None or self.eccentricity is None:
            return None
        return self.semi_major_axis_au * (1 + self.eccentricity)


@dataclass
class PhysicalParameters:
    """
    Physical characteristics of an exoplanet.
    
    Attributes:
        radius_earth: Planet radius in Earth radii (R⊕)
        radius_jupiter: Planet radius in Jupiter radii (R_J)
        mass_earth: Planet mass in Earth masses (M⊕)
        mass_jupiter: Planet mass in Jupiter masses (M_J)
        density_g_cm3: Bulk density in g/cm³
        equilibrium_temp_k: Equilibrium temperature in Kelvin
    """
    radius_earth: Optional[float] = None
    radius_jupiter: Optional[float] = None
    mass_earth: Optional[float] = None
    mass_jupiter: Optional[float] = None
    density_g_cm3: Optional[float] = None
    equilibrium_temp_k: Optional[float] = None
    
    # Physical constants
    EARTH_RADIUS_KM = 6371.0
    EARTH_MASS_KG = 5.972e24
    JUPITER_RADIUS_KM = 69911.0
    JUPITER_MASS_KG = 1.898e27
    G_CONST = 6.674e-11  # m³/(kg·s²)
    
    @property
    def surface_gravity_earth(self) -> Optional[float]:
        """
        Estimate surface gravity relative to Earth.
        
        Uses g = GM/R² scaling: g/g_Earth = (M/M_Earth) / (R/R_Earth)²
        
        Returns:
            Surface gravity in Earth gravities (g_Earth = 1.0)
        """
        if self.mass_earth is None or self.radius_earth is None:
            return None
        if self.radius_earth <= 0:
            return None
        return self.mass_earth / (self.radius_earth ** 2)
    
    @property
    def escape_velocity_km_s(self) -> Optional[float]:
        """
        Calculate escape velocity in km/s.
        
        v_esc = sqrt(2GM/R)
        Earth's escape velocity is ~11.2 km/s
        """
        if self.mass_earth is None or self.radius_earth is None:
            return None
        if self.radius_earth <= 0:
            return None
        # Scale from Earth values: v_esc = 11.2 * sqrt(M/R) where M, R in Earth units
        return 11.186 * math.sqrt(self.mass_earth / self.radius_earth)
    
    def classify_planet_type(self) -> PlanetType:
        """
        Classify planet based on radius.
        
        Classification based on:
        - Fulton et al. (2017): The California-Kepler Survey
        - Chen & Kipping (2017): Mass-radius relation
        """
        if self.radius_earth is None:
            return PlanetType.UNKNOWN
        
        r = self.radius_earth
        if r < 1.0:
            return PlanetType.TERRESTRIAL
        elif r < 1.75:
            return PlanetType.SUPER_EARTH
        elif r < 3.5:
            return PlanetType.SUB_NEPTUNE
        elif r < 6.0:
            return PlanetType.NEPTUNE_LIKE
        else:
            return PlanetType.GAS_GIANT
    
    def estimate_density(self) -> Optional[float]:
        """
        Estimate density if not provided but mass and radius are known.
        
        ρ = M / (4/3 π R³)
        Earth's density is ~5.51 g/cm³
        """
        if self.density_g_cm3 is not None:
            return self.density_g_cm3
        
        if self.mass_earth is None or self.radius_earth is None:
            return None
        
        # Scale from Earth: ρ/ρ_Earth = M/R³
        earth_density = 5.514  # g/cm³
        return earth_density * self.mass_earth / (self.radius_earth ** 3)


@dataclass
class ExoplanetEntity:
    """
    Domain entity representing an exoplanet.
    
    This is the core business object containing all astrophysical
    data about an exoplanet. It is independent of persistence
    concerns (database) and presentation concerns (API).
    
    Scientific Context:
    -------------------
    An exoplanet's habitability potential depends on a complex interplay
    of factors including its size, mass, temperature, orbital characteristics,
    and the properties of its host star. This entity encapsulates all
    relevant parameters for habitability assessment.
    
    Attributes:
        id: Unique identifier
        name: Official IAU designation (e.g., "Kepler-442 b")
        host_star_name: Name of the host star
        orbital: Orbital parameters
        physical: Physical parameters
        discovery_method: Detection method (Transit, Radial Velocity, etc.)
        discovery_year: Year of discovery
        distance_pc: Distance from Earth in parsecs
    """
    
    id: Optional[int] = None
    name: str = ""
    host_star_name: str = ""
    
    # Structured parameters
    orbital: OrbitalParameters = field(default_factory=OrbitalParameters)
    physical: PhysicalParameters = field(default_factory=PhysicalParameters)
    
    # Discovery information
    discovery_method: Optional[str] = None
    discovery_year: Optional[int] = None
    discovery_facility: Optional[str] = None
    
    # Position
    distance_pc: Optional[float] = None
    ra_deg: Optional[float] = None
    dec_deg: Optional[float] = None
    
    # External identifiers
    nasa_id: Optional[str] = None
    esa_id: Optional[str] = None
    
    # Additional notes
    notes: Optional[str] = None
    
    @property
    def planet_type(self) -> PlanetType:
        """Get the planet classification based on radius."""
        return self.physical.classify_planet_type()
    
    @property
    def is_potentially_rocky(self) -> bool:
        """
        Check if planet is likely to have a rocky composition.
        
        Based on the radius gap at ~1.75 R⊕ (Fulton gap).
        """
        return self.planet_type in (PlanetType.TERRESTRIAL, PlanetType.SUPER_EARTH)
    
    @property
    def distance_light_years(self) -> Optional[float]:
        """Convert distance from parsecs to light-years."""
        if self.distance_pc is None:
            return None
        return self.distance_pc * 3.26156  # 1 pc = 3.26156 ly
    
    def get_data_completeness(self, required_fields: list[str]) -> float:
        """
        Calculate what fraction of required data fields are available.
        
        Args:
            required_fields: List of field names to check
            
        Returns:
            Fraction of fields with data (0.0 to 1.0)
        """
        if not required_fields:
            return 1.0
        
        available = 0
        for field_name in required_fields:
            value = self._get_nested_value(field_name)
            if value is not None:
                available += 1
        
        return available / len(required_fields)
    
    def _get_nested_value(self, field_path: str):
        """Get a potentially nested field value using dot notation."""
        parts = field_path.split(".")
        obj = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return None
        return obj
    
    def __str__(self) -> str:
        return f"{self.name} ({self.planet_type.value})"
    
    def __repr__(self) -> str:
        return (
            f"ExoplanetEntity(id={self.id}, name='{self.name}', "
            f"host='{self.host_star_name}', type={self.planet_type.value})"
        )
