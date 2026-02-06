"""
Health check endpoint.

Provides API health status for monitoring and load balancers.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns basic service status information for monitoring purposes.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )
