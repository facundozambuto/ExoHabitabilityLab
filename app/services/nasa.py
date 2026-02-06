"""
NASA Exoplanet Archive data fetching service.

This service interfaces with the NASA Exoplanet Archive TAP API
to retrieve confirmed exoplanet data.

API Documentation:
https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html
"""

from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.exoplanet import Exoplanet

logger = get_logger(__name__)

# NASA Exoplanet Archive TAP query columns
# These correspond to the Planetary Systems Composite Parameters table (pscomppars)
NASA_QUERY_COLUMNS = [
    "pl_name",           # Planet name
    "hostname",          # Host star name
    "discoverymethod",   # Discovery method
    "disc_year",         # Discovery year
    "disc_facility",     # Discovery facility
    "pl_orbper",         # Orbital period (days)
    "pl_orbsmax",        # Semi-major axis (AU)
    "pl_orbeccen",       # Eccentricity
    "pl_orbincl",        # Inclination (degrees)
    "pl_rade",           # Planet radius (Earth radii)
    "pl_radj",           # Planet radius (Jupiter radii)
    "pl_masse",          # Planet mass (Earth masses)
    "pl_massj",          # Planet mass (Jupiter masses)
    "pl_dens",           # Planet density (g/cm³)
    "pl_eqt",            # Equilibrium temperature (K)
    "st_spectype",       # Stellar spectral type
    "st_mass",           # Stellar mass (solar masses)
    "st_rad",            # Stellar radius (solar radii)
    "st_teff",           # Stellar effective temperature (K)
    "st_lum",            # Stellar luminosity (log solar)
    "st_met",            # Stellar metallicity
    "st_age",            # Stellar age (Gyr)
    "sy_dist",           # Distance (parsecs)
    "ra",                # Right ascension (degrees)
    "dec",               # Declination (degrees)
]


class NASAExoplanetService:
    """
    Service for fetching exoplanet data from NASA Exoplanet Archive.
    
    Uses the Table Access Protocol (TAP) API to query the archive.
    
    Example usage:
        service = NASAExoplanetService()
        planets = await service.fetch_exoplanets(limit=100)
    """
    
    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Initialize the NASA Exoplanet service.
        
        Args:
            base_url: Override the default NASA API URL
        """
        self.base_url = base_url or settings.nasa_api_base_url
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    def _build_query(
        self,
        columns: list[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        where_clause: Optional[str] = None,
    ) -> str:
        """
        Build an ADQL query for the NASA TAP service.
        
        Args:
            columns: List of column names to select
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            where_clause: Optional WHERE clause conditions
            
        Returns:
            str: ADQL query string
        """
        columns_str = ", ".join(columns)
        query = f"SELECT {columns_str} FROM pscomppars"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        # Order by discovery year and name for consistent pagination
        query += " ORDER BY disc_year DESC, pl_name ASC"
        
        if limit:
            query += f" TOP {limit}"
        
        return query
    
    async def fetch_exoplanets(
        self,
        limit: int = 100,
        offset: int = 0,
        stellar_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch exoplanet data from NASA Exoplanet Archive.
        
        Args:
            limit: Maximum number of planets to fetch
            offset: Number of planets to skip (for pagination)
            stellar_type: Filter by stellar spectral type (e.g., 'G', 'K', 'M')
            
        Returns:
            list: List of exoplanet data dictionaries
            
        Note:
            The TAP API doesn't support OFFSET directly, so we fetch more
            and slice. For production, consider using async pagination tokens.
        """
        logger.info(f"Fetching exoplanets from NASA (limit={limit}, offset={offset})")
        
        # Build WHERE clause
        where_parts = []
        if stellar_type:
            where_parts.append(f"st_spectype LIKE '{stellar_type}%'")
        
        where_clause = " AND ".join(where_parts) if where_parts else None
        
        # Build query - fetch extra for offset simulation
        fetch_limit = limit + offset
        query = self._build_query(
            columns=NASA_QUERY_COLUMNS,
            limit=fetch_limit,
            where_clause=where_clause,
        )
        
        params = {
            "query": query,
            "format": "json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Apply offset by slicing
                planets = data[offset:offset + limit] if offset > 0 else data[:limit]
                
                logger.info(f"Successfully fetched {len(planets)} exoplanets from NASA")
                return planets
                
        except httpx.HTTPStatusError as e:
            logger.error(f"NASA API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"NASA API request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching NASA data: {e}")
            raise
    
    async def fetch_exoplanet_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """
        Fetch a specific exoplanet by its name.
        
        Args:
            name: Official planet designation (e.g., 'Kepler-442 b')
            
        Returns:
            dict or None: Exoplanet data or None if not found
        """
        logger.info(f"Fetching exoplanet '{name}' from NASA")
        
        where_clause = f"pl_name = '{name}'"
        query = self._build_query(
            columns=NASA_QUERY_COLUMNS,
            limit=1,
            where_clause=where_clause,
        )
        
        params = {
            "query": query,
            "format": "json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data:
                    logger.info(f"Found exoplanet '{name}'")
                    return data[0]
                else:
                    logger.warning(f"Exoplanet '{name}' not found")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching exoplanet '{name}': {e}")
            raise
    
    async def get_total_count(self, stellar_type: Optional[str] = None) -> int:
        """
        Get the total count of exoplanets in the archive.
        
        Args:
            stellar_type: Optional filter by stellar type
            
        Returns:
            int: Total number of confirmed exoplanets
        """
        where_parts = []
        if stellar_type:
            where_parts.append(f"st_spectype LIKE '{stellar_type}%'")
        
        where_clause = " AND ".join(where_parts) if where_parts else None
        
        query = "SELECT COUNT(*) as cnt FROM pscomppars"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        params = {
            "query": query,
            "format": "json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return data[0]["cnt"] if data else 0
                
        except Exception as e:
            logger.error(f"Error getting exoplanet count: {e}")
            return 0
    
    def map_to_model(self, nasa_data: dict[str, Any]) -> dict[str, Any]:
        """
        Map NASA API response to our database model fields.
        
        Args:
            nasa_data: Raw data from NASA API
            
        Returns:
            dict: Data mapped to Exoplanet model fields
        """
        return {
            "nasa_id": nasa_data.get("pl_name"),
            "name": nasa_data.get("pl_name", "Unknown"),
            "host_star": nasa_data.get("hostname", "Unknown"),
            "discovery_method": nasa_data.get("discoverymethod"),
            "discovery_year": nasa_data.get("disc_year"),
            "discovery_facility": nasa_data.get("disc_facility"),
            "orbital_period_days": nasa_data.get("pl_orbper"),
            "semi_major_axis_au": nasa_data.get("pl_orbsmax"),
            "eccentricity": nasa_data.get("pl_orbeccen"),
            "inclination_deg": nasa_data.get("pl_orbincl"),
            "planet_radius_earth": nasa_data.get("pl_rade"),
            "planet_radius_jupiter": nasa_data.get("pl_radj"),
            "planet_mass_earth": nasa_data.get("pl_masse"),
            "planet_mass_jupiter": nasa_data.get("pl_massj"),
            "planet_density_g_cm3": nasa_data.get("pl_dens"),
            "equilibrium_temp_k": nasa_data.get("pl_eqt"),
            "stellar_type": nasa_data.get("st_spectype"),
            "stellar_mass_solar": nasa_data.get("st_mass"),
            "stellar_radius_solar": nasa_data.get("st_rad"),
            "stellar_temp_k": nasa_data.get("st_teff"),
            "stellar_luminosity_solar": nasa_data.get("st_lum"),
            "stellar_metallicity": nasa_data.get("st_met"),
            "stellar_age_gyr": nasa_data.get("st_age"),
            "distance_pc": nasa_data.get("sy_dist"),
            "ra_deg": nasa_data.get("ra"),
            "dec_deg": nasa_data.get("dec"),
        }


# Singleton instance for dependency injection
nasa_service = NASAExoplanetService()
