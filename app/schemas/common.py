"""
Common schemas used across the application.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    detail: str = Field(..., description="Error message")
    error_code: str = Field(None, description="Machine-readable error code")
