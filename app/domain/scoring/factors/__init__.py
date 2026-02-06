"""
Scoring Factors Package.

This package contains all individual scoring factor implementations.
Each factor is a plugin that evaluates one aspect of habitability.

Factor Categories:
- Stellar: Host star properties (type, luminosity, age)
- Planetary: Planet physical properties (radius, mass, temperature)
- Orbital: Orbital characteristics (eccentricity, HZ position)
- Derived: Calculated estimates (atmosphere retention, tidal locking)
"""

from typing import List

from app.domain.scoring.base import ScoringFactor

# Import all factor implementations
from app.domain.scoring.factors.stellar import (
    StellarTypeFactor,
    StellarLuminosityFactor,
    StellarAgeFactor,
    HabitableZonePositionFactor,
)
from app.domain.scoring.factors.planetary import (
    PlanetRadiusFactor,
    PlanetMassFactor,
    PlanetDensityFactor,
    EquilibriumTemperatureFactor,
    SurfaceGravityFactor,
)
from app.domain.scoring.factors.orbital import (
    OrbitalEccentricityFactor,
    TidalLockingFactor,
)
from app.domain.scoring.factors.derived import (
    AtmosphereRetentionFactor,
    MagneticFieldPotentialFactor,
)


def get_all_factors() -> List[ScoringFactor]:
    """
    Get instances of all available scoring factors.
    
    Returns:
        List of all scoring factor instances
    """
    return [
        # Stellar factors
        StellarTypeFactor(),
        StellarLuminosityFactor(),
        StellarAgeFactor(),
        HabitableZonePositionFactor(),
        
        # Planetary factors
        PlanetRadiusFactor(),
        PlanetMassFactor(),
        PlanetDensityFactor(),
        EquilibriumTemperatureFactor(),
        SurfaceGravityFactor(),
        
        # Orbital factors
        OrbitalEccentricityFactor(),
        TidalLockingFactor(),
        
        # Derived factors
        AtmosphereRetentionFactor(),
        MagneticFieldPotentialFactor(),
    ]


def get_factor_by_id(factor_id: str) -> ScoringFactor | None:
    """
    Get a specific factor by its ID.
    
    Args:
        factor_id: The factor's unique identifier
        
    Returns:
        Factor instance or None if not found
    """
    for factor in get_all_factors():
        if factor.factor_id == factor_id:
            return factor
    return None


__all__ = [
    "get_all_factors",
    "get_factor_by_id",
    "StellarTypeFactor",
    "StellarLuminosityFactor",
    "StellarAgeFactor",
    "HabitableZonePositionFactor",
    "PlanetRadiusFactor",
    "PlanetMassFactor",
    "PlanetDensityFactor",
    "EquilibriumTemperatureFactor",
    "SurfaceGravityFactor",
    "OrbitalEccentricityFactor",
    "TidalLockingFactor",
    "AtmosphereRetentionFactor",
    "MagneticFieldPotentialFactor",
]
