"""
API dependencies for dependency injection.

Provides common dependencies used across API routes.
"""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.scoring.advanced import AdvancedHabitabilityScorer, advanced_habitability_scorer


# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


# Pagination dependencies
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of items per page"
    ),
) -> dict[str, int]:
    """
    Get pagination parameters from query string.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        dict: Pagination parameters with offset calculated
    """
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }


PaginationParams = Annotated[dict[str, int], Depends(get_pagination_params)]


def get_habitability_scorer() -> AdvancedHabitabilityScorer:
    """
    Get the habitability scoring service.
    
    Returns the advanced 13-factor scoring engine that evaluates:
    - Stellar factors: type, luminosity, age, habitable zone position
    - Planetary factors: radius, mass, density, temperature, surface gravity
    - Orbital factors: eccentricity, tidal locking risk
    - Derived factors: atmosphere retention, magnetic field potential
    
    Returns:
        AdvancedHabitabilityScorer: Full scoring service instance
    """
    return advanced_habitability_scorer


HabitabilityScorer = Annotated[AdvancedHabitabilityScorer, Depends(get_habitability_scorer)]
