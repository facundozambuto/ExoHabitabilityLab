"""
ESA Exoplanet data fetching service.

This is a mock service for MVP that provides sample ESA-style data.
In production, this would interface with the ESA Exoplanet EU catalog
or other ESA open datasets.

Future integration points:
- http://exoplanet.eu/catalog/
- ESA Gaia archive for stellar parameters
"""

from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# Mock ESA data for MVP demonstration
# These are real exoplanets with data that might come from European sources
MOCK_ESA_DATA: list[dict[str, Any]] = [
    {
        "esa_id": "ESA-001",
        "name": "Proxima Centauri b",
        "host_star": "Proxima Centauri",
        "discovery_method": "Radial Velocity",
        "discovery_year": 2016,
        "orbital_period_days": 11.186,
        "semi_major_axis_au": 0.0485,
        "eccentricity": 0.11,
        "planet_radius_earth": 1.08,
        "planet_mass_earth": 1.27,
        "equilibrium_temp_k": 234,
        "stellar_type": "M5.5V",
        "stellar_mass_solar": 0.122,
        "stellar_radius_solar": 0.154,
        "stellar_temp_k": 3042,
        "distance_pc": 1.30,
        "notes": "Closest known exoplanet to Earth. Located in habitable zone of Proxima Centauri.",
    },
    {
        "esa_id": "ESA-002",
        "name": "TRAPPIST-1 e",
        "host_star": "TRAPPIST-1",
        "discovery_method": "Transit",
        "discovery_year": 2017,
        "orbital_period_days": 6.099,
        "semi_major_axis_au": 0.029,
        "eccentricity": 0.005,
        "planet_radius_earth": 0.92,
        "planet_mass_earth": 0.69,
        "equilibrium_temp_k": 251,
        "stellar_type": "M8V",
        "stellar_mass_solar": 0.089,
        "stellar_radius_solar": 0.121,
        "stellar_temp_k": 2566,
        "distance_pc": 12.43,
        "notes": "One of seven Earth-sized planets. Potentially in the habitable zone.",
    },
    {
        "esa_id": "ESA-003",
        "name": "K2-18 b",
        "host_star": "K2-18",
        "discovery_method": "Transit",
        "discovery_year": 2015,
        "orbital_period_days": 32.94,
        "semi_major_axis_au": 0.1429,
        "eccentricity": 0.09,
        "planet_radius_earth": 2.61,
        "planet_mass_earth": 8.63,
        "equilibrium_temp_k": 284,
        "stellar_type": "M2.5V",
        "stellar_mass_solar": 0.495,
        "stellar_radius_solar": 0.469,
        "stellar_temp_k": 3503,
        "distance_pc": 38.0,
        "notes": "Sub-Neptune in habitable zone. Water vapor detected in atmosphere (2019).",
    },
    {
        "esa_id": "ESA-004",
        "name": "LHS 1140 b",
        "host_star": "LHS 1140",
        "discovery_method": "Transit",
        "discovery_year": 2017,
        "orbital_period_days": 24.737,
        "semi_major_axis_au": 0.0946,
        "eccentricity": 0.0,
        "planet_radius_earth": 1.73,
        "planet_mass_earth": 6.98,
        "equilibrium_temp_k": 235,
        "stellar_type": "M4.5V",
        "stellar_mass_solar": 0.179,
        "stellar_radius_solar": 0.206,
        "stellar_temp_k": 3216,
        "distance_pc": 14.99,
        "notes": "Super-Earth in habitable zone. Dense, rocky composition likely.",
    },
    {
        "esa_id": "ESA-005",
        "name": "TOI-700 d",
        "host_star": "TOI-700",
        "discovery_method": "Transit",
        "discovery_year": 2020,
        "orbital_period_days": 37.42,
        "semi_major_axis_au": 0.163,
        "eccentricity": 0.0,
        "planet_radius_earth": 1.19,
        "planet_mass_earth": 1.72,
        "equilibrium_temp_k": 268,
        "stellar_type": "M2V",
        "stellar_mass_solar": 0.415,
        "stellar_radius_solar": 0.421,
        "stellar_temp_k": 3480,
        "distance_pc": 31.13,
        "notes": "First Earth-sized planet in habitable zone discovered by TESS.",
    },
]


class ESAExoplanetService:
    """
    Service for ESA exoplanet data (mock implementation for MVP).
    
    This service provides mock data simulating what might come from
    European Space Agency sources. In production, this would integrate
    with actual ESA APIs.
    
    Example usage:
        service = ESAExoplanetService()
        planets = await service.fetch_exoplanets(limit=10)
    """
    
    def __init__(self) -> None:
        """Initialize the ESA Exoplanet service."""
        self._mock_data = MOCK_ESA_DATA
        logger.info("ESA service initialized (mock mode for MVP)")
    
    async def fetch_exoplanets(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Fetch exoplanet data (mock implementation).
        
        Args:
            limit: Maximum number of planets to fetch
            offset: Number of planets to skip
            
        Returns:
            list: List of exoplanet data dictionaries
        """
        logger.info(f"Fetching exoplanets from ESA (mock) - limit={limit}, offset={offset}")
        
        # Simulate pagination on mock data
        end_idx = min(offset + limit, len(self._mock_data))
        planets = self._mock_data[offset:end_idx]
        
        logger.info(f"Returning {len(planets)} exoplanets from ESA (mock)")
        return planets
    
    async def fetch_exoplanet_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """
        Fetch a specific exoplanet by name (mock implementation).
        
        Args:
            name: Planet name to search for
            
        Returns:
            dict or None: Exoplanet data or None if not found
        """
        logger.info(f"Searching for exoplanet '{name}' in ESA data (mock)")
        
        for planet in self._mock_data:
            if planet["name"].lower() == name.lower():
                return planet
        
        logger.warning(f"Exoplanet '{name}' not found in ESA mock data")
        return None
    
    async def fetch_exoplanet_by_esa_id(self, esa_id: str) -> Optional[dict[str, Any]]:
        """
        Fetch a specific exoplanet by ESA ID (mock implementation).
        
        Args:
            esa_id: ESA identifier
            
        Returns:
            dict or None: Exoplanet data or None if not found
        """
        for planet in self._mock_data:
            if planet["esa_id"] == esa_id:
                return planet
        return None
    
    async def get_total_count(self) -> int:
        """
        Get total count of exoplanets (mock implementation).
        
        Returns:
            int: Number of available exoplanets
        """
        return len(self._mock_data)
    
    def map_to_model(self, esa_data: dict[str, Any]) -> dict[str, Any]:
        """
        Map ESA data format to our database model fields.
        
        Args:
            esa_data: Raw data from ESA source
            
        Returns:
            dict: Data mapped to Exoplanet model fields
        """
        return {
            "esa_id": esa_data.get("esa_id"),
            "name": esa_data.get("name", "Unknown"),
            "host_star": esa_data.get("host_star", "Unknown"),
            "discovery_method": esa_data.get("discovery_method"),
            "discovery_year": esa_data.get("discovery_year"),
            "orbital_period_days": esa_data.get("orbital_period_days"),
            "semi_major_axis_au": esa_data.get("semi_major_axis_au"),
            "eccentricity": esa_data.get("eccentricity"),
            "planet_radius_earth": esa_data.get("planet_radius_earth"),
            "planet_mass_earth": esa_data.get("planet_mass_earth"),
            "equilibrium_temp_k": esa_data.get("equilibrium_temp_k"),
            "stellar_type": esa_data.get("stellar_type"),
            "stellar_mass_solar": esa_data.get("stellar_mass_solar"),
            "stellar_radius_solar": esa_data.get("stellar_radius_solar"),
            "stellar_temp_k": esa_data.get("stellar_temp_k"),
            "distance_pc": esa_data.get("distance_pc"),
            "notes": esa_data.get("notes"),
        }


# Singleton instance for dependency injection
esa_service = ESAExoplanetService()
