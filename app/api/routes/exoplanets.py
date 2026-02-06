"""
Exoplanet API endpoints.

Provides CRUD operations and habitability scoring for exoplanet data.
"""

import math
from typing import Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession, HabitabilityScorer, PaginationParams
from app.core.logging import get_logger
from app.models.exoplanet import Exoplanet
from app.schemas.exoplanet import (
    ExoplanetCreate,
    ExoplanetListResponse,
    ExoplanetResponse,
)
from app.schemas.scoring import HabitabilityScoreResponse, ScoringMethodology
from app.services.nasa import nasa_service
from app.services.esa import esa_service
from app.services.image_generation import (
    ImagePromptGenerator,
    ImageStyle,
    ImageFormat,
    get_image_service,
)
from app.domain.entities.exoplanet import ExoplanetEntity, OrbitalParameters, PhysicalParameters
from app.domain.entities.star import StarEntity

logger = get_logger(__name__)

router = APIRouter(prefix="/exoplanets", tags=["Exoplanets"])


@router.get(
    "",
    response_model=ExoplanetListResponse,
    summary="List Exoplanets",
    description="Get a paginated list of exoplanets from the database.",
)
async def list_exoplanets(
    db: DbSession,
    pagination: PaginationParams,
    stellar_type: Optional[str] = Query(
        None,
        description="Filter by stellar type (e.g., 'G', 'K', 'M')"
    ),
    min_radius: Optional[float] = Query(
        None, ge=0, description="Minimum planet radius in Earth radii"
    ),
    max_radius: Optional[float] = Query(
        None, ge=0, description="Maximum planet radius in Earth radii"
    ),
    discovery_year: Optional[int] = Query(
        None, description="Filter by discovery year"
    ),
) -> ExoplanetListResponse:
    """
    Get a paginated list of exoplanets with optional filters.
    
    Supports filtering by:
    - stellar_type: Host star spectral class (prefix match)
    - min_radius / max_radius: Planet size range
    - discovery_year: Year of discovery
    """
    # Build query
    query = select(Exoplanet)
    count_query = select(func.count(Exoplanet.id))
    
    # Apply filters
    if stellar_type:
        query = query.where(Exoplanet.stellar_type.ilike(f"{stellar_type}%"))
        count_query = count_query.where(Exoplanet.stellar_type.ilike(f"{stellar_type}%"))
    
    if min_radius is not None:
        query = query.where(Exoplanet.planet_radius_earth >= min_radius)
        count_query = count_query.where(Exoplanet.planet_radius_earth >= min_radius)
    
    if max_radius is not None:
        query = query.where(Exoplanet.planet_radius_earth <= max_radius)
        count_query = count_query.where(Exoplanet.planet_radius_earth <= max_radius)
    
    if discovery_year is not None:
        query = query.where(Exoplanet.discovery_year == discovery_year)
        count_query = count_query.where(Exoplanet.discovery_year == discovery_year)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(Exoplanet.name)
    query = query.offset(pagination["offset"]).limit(pagination["page_size"])
    
    # Execute query
    result = await db.execute(query)
    exoplanets = result.scalars().all()
    
    # Calculate total pages
    total_pages = math.ceil(total / pagination["page_size"]) if total > 0 else 1
    
    return ExoplanetListResponse(
        items=[ExoplanetResponse.model_validate(ep) for ep in exoplanets],
        total=total,
        page=pagination["page"],
        page_size=pagination["page_size"],
        total_pages=total_pages,
    )


@router.get(
    "/{exoplanet_id}",
    response_model=ExoplanetResponse,
    summary="Get Exoplanet Details",
    description="Get detailed information about a specific exoplanet.",
)
async def get_exoplanet(
    exoplanet_id: int,
    db: DbSession,
) -> ExoplanetResponse:
    """
    Get detailed data for a specific exoplanet by ID.
    
    Returns 404 if the exoplanet is not found.
    """
    result = await db.execute(
        select(Exoplanet).where(Exoplanet.id == exoplanet_id)
    )
    exoplanet = result.scalar_one_or_none()
    
    if not exoplanet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exoplanet with ID {exoplanet_id} not found",
        )
    
    return ExoplanetResponse.model_validate(exoplanet)


@router.get(
    "/{exoplanet_id}/score",
    response_model=HabitabilityScoreResponse,
    summary="Get Habitability Score",
    description="Calculate and return the comprehensive habitability score for an exoplanet using 13 scientific factors.",
)
async def get_habitability_score(
    exoplanet_id: int,
    db: DbSession,
    scorer: HabitabilityScorer,
) -> HabitabilityScoreResponse:
    """
    Calculate the habitability score for a specific exoplanet.
    
    The score is based on 13 scientific factors:
    
    **Stellar Factors:**
    - Stellar type (host star spectral classification)
    - Stellar luminosity (energy output stability)
    - Stellar age (time for life evolution)
    - Habitable zone position (orbital distance relative to HZ)
    
    **Planetary Factors:**
    - Planet radius (likelihood of rocky composition)
    - Planet mass (atmosphere retention capability)
    - Planet density (composition indicator)
    - Equilibrium temperature (surface conditions)
    - Surface gravity (habitability for complex life)
    
    **Orbital Factors:**
    - Orbital eccentricity (climate stability)
    - Tidal locking risk (day/night cycle implications)
    
    **Derived Factors:**
    - Atmosphere retention potential
    - Magnetic field likelihood
    
    Returns a detailed breakdown with scientific explanations.
    
    **Important**: This score is a PROBABILISTIC INDICATOR only.
    It does not indicate the presence of life or guarantee habitability.
    """
    result = await db.execute(
        select(Exoplanet).where(Exoplanet.id == exoplanet_id)
    )
    exoplanet = result.scalar_one_or_none()
    
    if not exoplanet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exoplanet with ID {exoplanet_id} not found",
        )
    
    # Calculate habitability score
    score_result = scorer.calculate_score(exoplanet)
    
    return score_result


@router.get(
    "/scoring/methodology",
    response_model=ScoringMethodology,
    summary="Get Scoring Methodology",
    description="Get detailed information about how habitability scores are calculated.",
)
async def get_scoring_methodology(
    scorer: HabitabilityScorer,
) -> ScoringMethodology:
    """
    Return detailed methodology information for the habitability scoring system.
    
    Includes:
    - Factor descriptions and weights
    - Scientific references
    - Known limitations
    """
    methodology = scorer.get_methodology()
    return ScoringMethodology(**methodology)


@router.post(
    "/sync/nasa",
    response_model=dict,
    summary="Sync NASA Data",
    description="Fetch and store exoplanet data from NASA Exoplanet Archive.",
)
async def sync_nasa_data(
    db: DbSession,
    limit: int = Query(100, ge=1, le=1000, description="Number of exoplanets to fetch"),
) -> dict:
    """
    Synchronize exoplanet data from NASA Exoplanet Archive.
    
    Fetches the latest data and stores/updates records in the database.
    This is an administrative endpoint for data population.
    """
    logger.info(f"Starting NASA data sync (limit={limit})")
    
    try:
        # Fetch data from NASA
        nasa_data = await nasa_service.fetch_exoplanets(limit=limit)
        
        created = 0
        updated = 0
        errors = 0
        
        for planet_data in nasa_data:
            try:
                mapped_data = nasa_service.map_to_model(planet_data)
                
                # Check if planet already exists
                result = await db.execute(
                    select(Exoplanet).where(Exoplanet.nasa_id == mapped_data["nasa_id"])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    for key, value in mapped_data.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated += 1
                else:
                    # Create new record
                    exoplanet = Exoplanet(**mapped_data)
                    db.add(exoplanet)
                    created += 1
                    
            except Exception as e:
                logger.error(f"Error processing planet: {e}")
                errors += 1
        
        await db.commit()
        
        logger.info(f"NASA sync complete: {created} created, {updated} updated, {errors} errors")
        
        return {
            "status": "success",
            "source": "NASA Exoplanet Archive",
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_processed": len(nasa_data),
        }
        
    except Exception as e:
        logger.error(f"NASA sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync NASA data: {str(e)}",
        )


@router.post(
    "/sync/esa",
    response_model=dict,
    summary="Sync ESA Data",
    description="Fetch and store exoplanet data from ESA (mock for MVP).",
)
async def sync_esa_data(
    db: DbSession,
) -> dict:
    """
    Synchronize exoplanet data from ESA sources.
    
    Note: This is a mock implementation for MVP that uses sample data.
    In production, this would connect to actual ESA APIs.
    """
    logger.info("Starting ESA data sync (mock)")
    
    try:
        # Fetch data from ESA (mock)
        esa_data = await esa_service.fetch_exoplanets()
        
        created = 0
        updated = 0
        
        for planet_data in esa_data:
            mapped_data = esa_service.map_to_model(planet_data)
            
            # Check if planet already exists by name (since we might have NASA data too)
            result = await db.execute(
                select(Exoplanet).where(Exoplanet.name == mapped_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update with ESA data
                existing.esa_id = mapped_data.get("esa_id")
                if mapped_data.get("notes"):
                    existing.notes = mapped_data["notes"]
                updated += 1
            else:
                # Create new record
                exoplanet = Exoplanet(**mapped_data)
                db.add(exoplanet)
                created += 1
        
        await db.commit()
        
        logger.info(f"ESA sync complete: {created} created, {updated} updated")
        
        return {
            "status": "success",
            "source": "ESA (mock)",
            "created": created,
            "updated": updated,
            "total_processed": len(esa_data),
            "note": "This is mock data for MVP demonstration",
        }
        
    except Exception as e:
        logger.error(f"ESA sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync ESA data: {str(e)}",
        )


# ============================================================
# Image Generation Endpoint
# ============================================================

class ImageStyleParam(str, Enum):
    """Query parameter enum for image styles."""
    realistic = "realistic"
    artistic = "artistic"
    cinematic = "cinematic"
    scientific = "scientific"
    retro_scifi = "retro_scifi"


class ImageFormatParam(str, Enum):
    """Query parameter enum for image formats."""
    square = "square"
    landscape = "landscape"
    portrait = "portrait"


@router.post(
    "/{exoplanet_id}/generate-art",
    summary="Generate Artistic Visualization",
    description="""
Generate an AI-powered artistic visualization of an exoplanet based on its 
scientific properties.

The generated image reflects:
- **Star properties**: Color and apparent size based on spectral type
- **Planet type**: Rocky, super-Earth, gas giant, etc.
- **Temperature**: From frozen worlds to lava planets
- **Atmosphere**: Based on mass, radius, and temperature
- **Orbital characteristics**: Tidal locking, eccentricity effects

**Available Styles:**
- `realistic`: NASA-style photorealistic visualization
- `artistic`: Vibrant digital art interpretation
- `cinematic`: Movie poster dramatic style
- `scientific`: Educational illustration
- `retro_scifi`: 1970s sci-fi book cover aesthetic

**Note**: Currently returns prompt and metadata. Connect to DALL-E or 
Stable Diffusion API for actual image generation.
    """,
    responses={
        200: {
            "description": "Image generation result with prompt and metadata",
            "content": {
                "application/json": {
                    "example": {
                        "exoplanet_id": 1,
                        "exoplanet_name": "Kepler-442 b",
                        "style": "realistic",
                        "format": "landscape",
                        "prompt": "Photorealistic render of an exoplanet, massive rocky super-Earth...",
                        "negative_prompt": "text, watermark, blurry...",
                        "scientific_notes": [
                            "Super-Earth: Larger rocky world with stronger gravity",
                            "T_eq 233K: Cool but potentially habitable"
                        ],
                        "generation_status": "prompt_ready",
                        "image_url": None,
                        "message": "Prompt generated. Connect image API for actual generation."
                    }
                }
            }
        },
        404: {"description": "Exoplanet not found"},
    },
    tags=["Image Generation"],
)
async def generate_exoplanet_art(
    exoplanet_id: int,
    db: DbSession,
    style: ImageStyleParam = Query(
        ImageStyleParam.realistic,
        description="Artistic style for the visualization"
    ),
    format: ImageFormatParam = Query(
        ImageFormatParam.landscape,
        description="Image format/aspect ratio"
    ),
    include_habitability: bool = Query(
        True,
        description="Include habitability context in the visualization"
    ),
):
    """
    Generate an artistic visualization of an exoplanet.
    
    Creates a scientifically-informed image prompt based on the exoplanet's
    physical and orbital properties, host star characteristics, and 
    habitability assessment.
    """
    # Fetch exoplanet from database
    result = await db.execute(
        select(Exoplanet).where(Exoplanet.id == exoplanet_id)
    )
    exoplanet = result.scalar_one_or_none()
    
    if not exoplanet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exoplanet with id {exoplanet_id} not found",
        )
    
    # Convert to domain entities
    exoplanet_entity = ExoplanetEntity(
        name=exoplanet.name,
        orbital=OrbitalParameters(
            period_days=exoplanet.orbital_period_days,
            semi_major_axis_au=exoplanet.semi_major_axis_au,
            eccentricity=exoplanet.eccentricity,
        ),
        physical=PhysicalParameters(
            radius_earth=exoplanet.planet_radius_earth,
            mass_earth=exoplanet.planet_mass_earth,
            equilibrium_temp_k=exoplanet.equilibrium_temp_k,
        ),
    )
    
    # Create star entity with spectral type (spectral_class is a computed property)
    star_entity = StarEntity(
        name=exoplanet.host_star or f"{exoplanet.name} host",
        spectral_type=exoplanet.stellar_type,
        temperature_k=exoplanet.stellar_temp_k,
        mass_solar=exoplanet.stellar_mass_solar,
        radius_solar=exoplanet.stellar_radius_solar,
    )
    
    # Map style parameter to ImageStyle enum
    style_mapping = {
        ImageStyleParam.realistic: ImageStyle.REALISTIC,
        ImageStyleParam.artistic: ImageStyle.ARTISTIC,
        ImageStyleParam.cinematic: ImageStyle.CINEMATIC,
        ImageStyleParam.scientific: ImageStyle.SCIENTIFIC,
        ImageStyleParam.retro_scifi: ImageStyle.RETRO_SCIFI,
    }
    
    format_mapping = {
        ImageFormatParam.square: ImageFormat.SQUARE,
        ImageFormatParam.landscape: ImageFormat.LANDSCAPE,
        ImageFormatParam.portrait: ImageFormat.PORTRAIT,
    }
    
    # Generate the prompt
    generator = ImagePromptGenerator()
    generated = generator.generate_prompt(
        exoplanet=exoplanet_entity,
        star=star_entity,
        assessment=None,  # TODO: Include habitability assessment if requested
        style=style_mapping[style],
        format=format_mapping[format],
    )
    
    # Generate actual image using configured provider (pollinations.ai by default - FREE)
    image_service = get_image_service()  # Uses settings.image_provider, defaults to pollinations.ai
    
    try:
        generation_result = await image_service.generate(
            prompt=generated.prompt,
            negative_prompt=generated.negative_prompt,
            style=style_mapping[style],
            format=format_mapping[format],
        )
        image_url = generation_result.get("url")
        generation_status = generation_result.get("status", "completed")
    except Exception as e:
        logger.warning(f"Image generation failed: {e}")
        image_url = None
        generation_status = "prompt_ready"
    
    return JSONResponse(
        content={
            "exoplanet_id": exoplanet_id,
            "exoplanet_name": exoplanet.name,
            "style": style.value,
            "format": format.value,
            "prompt": generated.prompt,
            "negative_prompt": generated.negative_prompt,
            "scientific_notes": generated.scientific_notes,
            "prompt_hash": generated.prompt_hash,
            "generation_status": generation_status,
            "image_url": image_url,
            "message": "Prompt generated successfully. " + (
                "Image URL provided by mock service." if image_url 
                else "Connect to DALL-E or Stable Diffusion API for actual image generation."
            ),
        }
    )
