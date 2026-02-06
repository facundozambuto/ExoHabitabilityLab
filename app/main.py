"""
ExoHabitabilityLab - FastAPI Application Entry Point

A scientific API for exploring exoplanet habitability potential.
"Exploring worlds where life could emerge"

This module initializes the FastAPI application with:
- CORS middleware configuration
- API routing
- Database lifecycle management
- OpenAPI documentation customization
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.db.session import close_db, init_db

# Import routers
from app.api.routes.health import router as health_router
from app.api.routes.exoplanets import router as exoplanets_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, create tables
    - Shutdown: Close database connections
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    await init_db()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring",
        },
        {
            "name": "Exoplanets",
            "description": "Exoplanet data retrieval and habitability scoring",
        },
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(exoplanets_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.app_name,
        "description": settings.app_description,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_v1_prefix}/health",
    }


# Entry point for uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
