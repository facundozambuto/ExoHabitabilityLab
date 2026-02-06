"""
Application configuration using Pydantic Settings.

Manages environment variables and application settings for ExoHabitabilityLab.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        app_name: Name of the application
        app_version: Current version of the API
        debug: Enable debug mode
        environment: Current environment (development, staging, production)
        database_url: SQLite database connection string
        nasa_api_base_url: NASA Exoplanet Archive API base URL
        esa_api_base_url: ESA API base URL (placeholder for future use)
        log_level: Logging level
        api_v1_prefix: API version 1 prefix
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "ExoHabitabilityLab"
    app_version: str = "0.1.0"
    app_description: str = "Exploring worlds where life could emerge - A scientific API for exoplanet habitability analysis"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./exohabitability.db"
    
    # External APIs
    nasa_api_base_url: str = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    esa_api_base_url: str = "https://exoplanet.eu/api"  # Placeholder
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    
    # Logging
    log_level: str = "INFO"
    
    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Image Generation Configuration
    # Provider options: "pollinations" (free), "dalle" (OpenAI), "stability" (Stability AI)
    image_provider: str = "pollinations"
    pollinations_api_key: str = "pk_NGG18T1EUVVmvVBz"  # Optional - for gen.pollinations.ai (get free key at enter.pollinations.ai)
    openai_api_key: str = ""  # Required for DALL-E
    stability_api_key: str = ""  # Required for Stability AI
    
    # Image Storage Configuration
    # Storage options: "local", "cloudinary", "imgbb", "none" (return base64)
    image_storage: str = "none"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    imgbb_api_key: str = ""  # Free tier available at imgbb.com
    
    # Local storage path (if image_storage is "local")
    image_storage_path: str = "./generated_images"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings singleton
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()
