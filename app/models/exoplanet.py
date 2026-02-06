"""
SQLAlchemy model for Exoplanet data.

This model stores exoplanet information retrieved from NASA and ESA APIs,
along with computed habitability scores.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, TimestampMixin


class Exoplanet(Base, TimestampMixin):
    """
    Database model for exoplanet data.
    
    Stores astrophysical parameters used for habitability scoring.
    
    Attributes:
        id: Primary key
        nasa_id: Unique identifier from NASA Exoplanet Archive
        name: Official planet designation
        host_star: Name of the host star
        
        # Discovery info
        discovery_method: Method used to detect the planet
        discovery_year: Year of discovery
        
        # Orbital parameters
        orbital_period_days: Orbital period in Earth days
        semi_major_axis_au: Distance from star in AU
        eccentricity: Orbital eccentricity (0-1)
        
        # Planetary parameters
        planet_radius_earth: Radius in Earth radii
        planet_mass_earth: Mass in Earth masses
        equilibrium_temp_k: Equilibrium temperature in Kelvin
        
        # Stellar parameters
        stellar_type: Spectral classification (e.g., G2V)
        stellar_mass_solar: Star mass in solar masses
        stellar_radius_solar: Star radius in solar radii
        stellar_temp_k: Star effective temperature in Kelvin
        
        # Distance
        distance_pc: Distance from Earth in parsecs
    """
    
    __tablename__ = "exoplanets"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # External identifiers
    nasa_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    esa_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    host_star: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Discovery info
    discovery_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    discovery_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discovery_facility: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Orbital parameters
    orbital_period_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    semi_major_axis_au: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eccentricity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inclination_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Planetary parameters
    planet_radius_earth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    planet_radius_jupiter: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    planet_mass_earth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    planet_mass_jupiter: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    planet_density_g_cm3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equilibrium_temp_k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Stellar parameters
    stellar_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    stellar_mass_solar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stellar_radius_solar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stellar_temp_k: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stellar_luminosity_solar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stellar_metallicity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stellar_age_gyr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Distance and position
    distance_pc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ra_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Right ascension
    dec_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Declination
    
    # Additional notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps (from TimestampMixin)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Exoplanet(id={self.id}, name='{self.name}', host_star='{self.host_star}')>"
    
    @property
    def has_radius(self) -> bool:
        """Check if planet radius data is available."""
        return self.planet_radius_earth is not None
    
    @property
    def has_mass(self) -> bool:
        """Check if planet mass data is available."""
        return self.planet_mass_earth is not None
    
    @property
    def has_temperature(self) -> bool:
        """Check if equilibrium temperature data is available."""
        return self.equilibrium_temp_k is not None
    
    @property
    def has_stellar_type(self) -> bool:
        """Check if stellar type data is available."""
        return self.stellar_type is not None and len(self.stellar_type.strip()) > 0
