"""
Domain Mappers.

Functions to convert between database models and domain entities.
This maintains clean separation between persistence and domain layers.
"""

from app.models.exoplanet import Exoplanet
from app.domain.entities.exoplanet import (
    ExoplanetEntity,
    OrbitalParameters,
    PhysicalParameters,
)
from app.domain.entities.star import StarEntity


def exoplanet_model_to_entity(model: Exoplanet) -> ExoplanetEntity:
    """
    Convert a database Exoplanet model to a domain ExoplanetEntity.
    
    Args:
        model: SQLAlchemy Exoplanet model instance
        
    Returns:
        ExoplanetEntity domain object
    """
    return ExoplanetEntity(
        id=model.id,
        name=model.name,
        host_star_name=model.host_star,
        orbital=OrbitalParameters(
            period_days=model.orbital_period_days,
            semi_major_axis_au=model.semi_major_axis_au,
            eccentricity=model.eccentricity,
            inclination_deg=model.inclination_deg,
        ),
        physical=PhysicalParameters(
            radius_earth=model.planet_radius_earth,
            radius_jupiter=model.planet_radius_jupiter,
            mass_earth=model.planet_mass_earth,
            mass_jupiter=model.planet_mass_jupiter,
            density_g_cm3=model.planet_density_g_cm3,
            equilibrium_temp_k=model.equilibrium_temp_k,
        ),
        discovery_method=model.discovery_method,
        discovery_year=model.discovery_year,
        discovery_facility=model.discovery_facility,
        distance_pc=model.distance_pc,
        nasa_id=model.nasa_id,
        esa_id=model.esa_id,
    )


def exoplanet_model_to_star_entity(model: Exoplanet) -> StarEntity:
    """
    Extract host star information from Exoplanet model to StarEntity.
    
    The Exoplanet database model contains stellar parameters which
    we need to extract into a separate StarEntity for the scoring engine.
    
    Args:
        model: SQLAlchemy Exoplanet model instance
        
    Returns:
        StarEntity domain object with host star properties
    """
    return StarEntity(
        name=model.host_star,
        spectral_type=model.stellar_type,
        mass_solar=model.stellar_mass_solar,
        radius_solar=model.stellar_radius_solar,
        temperature_k=model.stellar_temp_k,
        luminosity_solar=model.stellar_luminosity_solar,
        metallicity=model.stellar_metallicity,
        age_gyr=model.stellar_age_gyr,
    )
