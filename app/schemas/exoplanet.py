"""
Pydantic schemas for exoplanet data validation.

These schemas define the structure of API requests and responses
for exoplanet-related endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExoplanetBase(BaseModel):
    """
    Base schema for exoplanet data.
    
    Contains common fields shared between different exoplanet schemas.
    """
    
    name: str = Field(..., description="Official designation of the exoplanet")
    host_star: str = Field(..., description="Name of the host star")
    discovery_method: Optional[str] = Field(
        None, description="Method used to discover the planet (e.g., Transit, Radial Velocity)"
    )
    discovery_year: Optional[int] = Field(
        None, description="Year the planet was discovered"
    )
    
    # Orbital parameters
    orbital_period_days: Optional[float] = Field(
        None, description="Orbital period in Earth days", ge=0
    )
    semi_major_axis_au: Optional[float] = Field(
        None, description="Semi-major axis in Astronomical Units (AU)", ge=0
    )
    eccentricity: Optional[float] = Field(
        None, description="Orbital eccentricity (0 = circular, 1 = parabolic)", ge=0, le=1
    )
    
    # Planetary parameters
    planet_radius_earth: Optional[float] = Field(
        None, description="Planet radius in Earth radii", ge=0
    )
    planet_mass_earth: Optional[float] = Field(
        None, description="Planet mass in Earth masses", ge=0
    )
    equilibrium_temp_k: Optional[float] = Field(
        None, description="Equilibrium temperature in Kelvin", ge=0
    )
    
    # Stellar parameters
    stellar_type: Optional[str] = Field(
        None, description="Spectral type of the host star (e.g., G2V, K5V, M3V)"
    )
    stellar_mass_solar: Optional[float] = Field(
        None, description="Host star mass in solar masses", ge=0
    )
    stellar_radius_solar: Optional[float] = Field(
        None, description="Host star radius in solar radii", ge=0
    )
    stellar_temp_k: Optional[float] = Field(
        None, description="Host star effective temperature in Kelvin", ge=0
    )
    
    # Distance
    distance_pc: Optional[float] = Field(
        None, description="Distance from Earth in parsecs", ge=0
    )


class ExoplanetCreate(ExoplanetBase):
    """Schema for creating a new exoplanet record."""
    pass


class ExoplanetUpdate(BaseModel):
    """Schema for updating an existing exoplanet record."""
    
    model_config = ConfigDict(extra="forbid")
    
    name: Optional[str] = None
    host_star: Optional[str] = None
    discovery_method: Optional[str] = None
    discovery_year: Optional[int] = None
    orbital_period_days: Optional[float] = Field(None, ge=0)
    semi_major_axis_au: Optional[float] = Field(None, ge=0)
    eccentricity: Optional[float] = Field(None, ge=0, le=1)
    planet_radius_earth: Optional[float] = Field(None, ge=0)
    planet_mass_earth: Optional[float] = Field(None, ge=0)
    equilibrium_temp_k: Optional[float] = Field(None, ge=0)
    stellar_type: Optional[str] = None
    stellar_mass_solar: Optional[float] = Field(None, ge=0)
    stellar_radius_solar: Optional[float] = Field(None, ge=0)
    stellar_temp_k: Optional[float] = Field(None, ge=0)
    distance_pc: Optional[float] = Field(None, ge=0)


class ExoplanetInDB(ExoplanetBase):
    """Schema for exoplanet data as stored in the database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique identifier in the database")
    nasa_id: Optional[str] = Field(None, description="NASA Exoplanet Archive identifier")
    created_at: datetime
    updated_at: datetime


class ExoplanetResponse(ExoplanetBase):
    """Schema for exoplanet data in API responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique identifier")
    nasa_id: Optional[str] = Field(None, description="NASA Exoplanet Archive identifier")


class ExoplanetListResponse(BaseModel):
    """Schema for paginated list of exoplanets."""
    
    items: list[ExoplanetResponse] = Field(..., description="List of exoplanets")
    total: int = Field(..., description="Total number of exoplanets matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
