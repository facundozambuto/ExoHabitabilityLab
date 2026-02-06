"""
AI Image Generation Service.

This module provides image generation using multiple AI providers:

- Pollinations.ai (FREE, no API key required) - Default
- OpenAI DALL-E (paid, requires API key)

Also supports multiple storage backends:
- None (return base64 directly)
- Local filesystem
- ImgBB (free tier available)
- Cloudinary (free tier available)
"""

import logging
import hashlib
import base64
import os
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.domain.entities.exoplanet import ExoplanetEntity, PlanetType
from app.domain.entities.star import StarEntity, SpectralClass
from app.domain.entities.habitability import HabitabilityAssessment

logger = logging.getLogger(__name__)


class ImageStyle(str, Enum):
    """Available artistic styles for image generation."""
    REALISTIC = "realistic"
    ARTISTIC = "artistic"
    CINEMATIC = "cinematic"
    SCIENTIFIC = "scientific"
    RETRO_SCIFI = "retro_scifi"


class ImageFormat(str, Enum):
    """Supported image output formats."""
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"
    PORTRAIT = "1024x1792"


@dataclass
class GeneratedImage:
    """Result of image generation."""
    exoplanet_name: str
    prompt: str
    negative_prompt: str
    style: ImageStyle
    format: ImageFormat
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    image_base64: Optional[str] = None
    generation_id: Optional[str] = None
    prompt_hash: str = ""
    scientific_notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.prompt_hash:
            content = f"{self.prompt}:{self.style.value}:{self.format.value}"
            self.prompt_hash = hashlib.md5(content.encode()).hexdigest()


@dataclass
class PromptComponents:
    """Components used to build the image prompt."""
    view_angle: str = "orbital view"
    lighting: str = "starlight"
    atmosphere: str = ""
    surface: str = ""
    features: List[str] = field(default_factory=list)
    star_color: str = "yellow"
    star_size_description: str = ""
    mood: str = ""
    style_modifiers: List[str] = field(default_factory=list)
    
    def build_prompt(self, style: ImageStyle) -> str:
        parts = []
        if style == ImageStyle.REALISTIC:
            parts.append("Photorealistic render of an exoplanet,")
        elif style == ImageStyle.ARTISTIC:
            parts.append("Artistic digital painting of an alien world,")
        elif style == ImageStyle.CINEMATIC:
            parts.append("Cinematic sci-fi scene of an exoplanet,")
        elif style == ImageStyle.SCIENTIFIC:
            parts.append("Scientific visualization of an exoplanet,")
        elif style == ImageStyle.RETRO_SCIFI:
            parts.append("Retro 1970s sci-fi book cover style exoplanet,")
        
        if self.surface:
            parts.append(self.surface)
        if self.atmosphere:
            parts.append(f"with {self.atmosphere}")
        for feature in self.features[:4]:
            parts.append(feature)
        parts.append(f"illuminated by {self.star_color} {self.lighting}")
        if self.star_size_description:
            parts.append(f"with {self.star_size_description} in the sky")
        parts.append(f"viewed from {self.view_angle}")
        if self.mood:
            parts.append(self.mood)
        for modifier in self.style_modifiers[:3]:
            parts.append(modifier)
        
        if style in [ImageStyle.REALISTIC, ImageStyle.CINEMATIC]:
            parts.extend(["highly detailed", "8K resolution", "volumetric lighting"])
        elif style == ImageStyle.SCIENTIFIC:
            parts.extend(["accurate representation", "NASA art style", "detailed textures"])
        
        return ", ".join(parts)


class ImagePromptGenerator:
    """Generates scientifically-informed image prompts from exoplanet data."""
    
    STAR_COLORS = {
        SpectralClass.O: ("intense blue-white", "blindingly bright"),
        SpectralClass.B: ("blue-white", "brilliant"),
        SpectralClass.A: ("white", "bright"),
        SpectralClass.F: ("yellow-white", "warm"),
        SpectralClass.G: ("yellow", "Sun-like"),
        SpectralClass.K: ("orange", "amber-tinted"),
        SpectralClass.M: ("deep red", "dim, looming"),
        SpectralClass.L: ("dark red", "barely visible"),
        SpectralClass.T: ("dim magenta", "faint"),
        SpectralClass.Y: ("infrared-dark", "nearly invisible"),
    }
    
    def generate_prompt(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
        assessment: Optional[HabitabilityAssessment] = None,
        style: ImageStyle = ImageStyle.REALISTIC,
        format: ImageFormat = ImageFormat.LANDSCAPE,
    ) -> GeneratedImage:
        components = PromptComponents()
        scientific_notes = []
        
        self._add_star_properties(star, components, scientific_notes)
        self._add_surface_properties(exoplanet, components, scientific_notes)
        self._add_atmosphere_properties(exoplanet, components, scientific_notes)
        self._add_climate_properties(exoplanet, components, scientific_notes)
        self._add_orbital_properties(exoplanet, star, components, scientific_notes)
        if assessment:
            self._add_habitability_context(assessment, components, scientific_notes)
        self._add_style_modifiers(style, components)
        
        prompt = components.build_prompt(style)
        negative_prompt = self._generate_negative_prompt(exoplanet, style)
        
        return GeneratedImage(
            exoplanet_name=exoplanet.name,
            prompt=prompt,
            negative_prompt=negative_prompt,
            style=style,
            format=format,
            scientific_notes=scientific_notes,
        )
    
    def _add_star_properties(self, star: StarEntity, comp: PromptComponents, notes: List[str]) -> None:
        if star.spectral_class and star.spectral_class in self.STAR_COLORS:
            color, desc = self.STAR_COLORS[star.spectral_class]
            comp.star_color = color
            comp.lighting = f"{desc} starlight"
        else:
            teff = star.temperature_k or 5778
            if teff > 10000: comp.star_color = "blue-white"
            elif teff > 7500: comp.star_color = "white"
            elif teff > 6000: comp.star_color = "yellow-white"
            elif teff > 5000: comp.star_color = "yellow"
            elif teff > 3700: comp.star_color = "orange"
            else: comp.star_color = "deep red"
        
        if star.spectral_class in [SpectralClass.M, SpectralClass.K]:
            comp.star_size_description = f"a {comp.star_color} sun dominating the horizon"
            notes.append("Cool stars appear larger from close habitable zone orbits")
        elif star.spectral_class in [SpectralClass.O, SpectralClass.B, SpectralClass.A]:
            comp.star_size_description = f"a {comp.star_color} sun appearing small but intense"
        else:
            comp.star_size_description = f"a {comp.star_color} sun"
    
    def _add_surface_properties(self, exo: ExoplanetEntity, comp: PromptComponents, notes: List[str]) -> None:
        ptype = exo.physical.classify_planet_type()
        if ptype == PlanetType.TERRESTRIAL:
            comp.surface = "rocky terrestrial world with rugged terrain"
            comp.features.append("mountain ranges and impact craters")
            notes.append("Terrestrial: Rocky composition like Earth or Mars")
        elif ptype == PlanetType.SUPER_EARTH:
            comp.surface = "massive rocky super-Earth with dramatic landscapes"
            comp.features.append("vast mountain ranges under thick atmosphere")
            notes.append("Super-Earth: Larger rocky world with stronger gravity")
        elif ptype == PlanetType.SUB_NEPTUNE:
            comp.surface = "sub-Neptune world with deep atmospheric layers"
            comp.features.append("swirling cloud bands in atmospheric haze")
            notes.append("Sub-Neptune: Likely significant H/He envelope")
        elif ptype == PlanetType.NEPTUNE_LIKE:
            comp.surface = "ice giant with deep blue-green atmosphere"
            comp.features.append("dramatic storm systems and wind bands")
            notes.append("Neptune-like: Ice giant composition")
        elif ptype == PlanetType.GAS_GIANT:
            comp.surface = "massive gas giant with banded atmosphere"
            comp.features.append("swirling storms and cyclonic features")
            notes.append("Gas giant: Jupiter-like composition")
        else:
            comp.surface = "mysterious alien world"
            comp.features.append("exotic terrain")
    
    def _add_atmosphere_properties(self, exo: ExoplanetEntity, comp: PromptComponents, notes: List[str]) -> None:
        mass = exo.physical.mass_earth
        radius = exo.physical.radius_earth
        temp = exo.physical.equilibrium_temp_k
        
        if mass is not None and mass < 0.3:
            comp.atmosphere = "thin, wispy atmosphere"
        elif radius is not None and radius > 2.5:
            comp.atmosphere = "thick, layered atmosphere with hazes"
        elif temp is not None:
            if temp < 200: comp.atmosphere = "frozen atmosphere with ice crystal hazes"
            elif temp < 280: comp.atmosphere = "cool atmosphere with water ice clouds"
            elif temp < 320:
                comp.atmosphere = "temperate atmosphere with water vapor clouds"
                comp.features.append("potential ocean glint on the surface")
            elif temp < 450: comp.atmosphere = "hot hazy atmosphere"
            else: comp.atmosphere = "scorching atmosphere with molten surface glow"
        else:
            comp.atmosphere = "mysterious atmospheric haze"
    
    def _add_climate_properties(self, exo: ExoplanetEntity, comp: PromptComponents, notes: List[str]) -> None:
        temp = exo.physical.equilibrium_temp_k
        if temp is None: return
        
        if temp < 150:
            comp.mood = "frozen desolate wasteland aesthetic"
            comp.features.append("ice-covered surface")
            notes.append(f"T_eq {temp}K: Extremely cold")
        elif temp < 230:
            comp.mood = "cold alien tundra aesthetic"
            comp.features.append("glacial landscapes")
            notes.append(f"T_eq {temp}K: Cold")
        elif temp < 280:
            comp.mood = "cool temperate Earth-like aesthetic"
            comp.features.append("possible liquid water oceans")
            notes.append(f"T_eq {temp}K: Potentially habitable")
        elif temp < 320:
            comp.mood = "warm tropical Earth-like aesthetic"
            comp.features.append("lush potential for life")
            notes.append(f"T_eq {temp}K: Optimal for liquid water")
        elif temp < 400:
            comp.mood = "hot Venus-like aesthetic"
            comp.features.append("thick clouds obscuring surface")
            notes.append(f"T_eq {temp}K: Hot")
        elif temp < 700:
            comp.mood = "scorching volcanic aesthetic"
            comp.features.append("glowing magma visible")
            notes.append(f"T_eq {temp}K: Very hot")
        else:
            comp.mood = "hellish lava world aesthetic"
            comp.features.append("entirely molten surface")
            notes.append(f"T_eq {temp}K: Lava world")
    
    def _add_orbital_properties(self, exo: ExoplanetEntity, star: StarEntity, comp: PromptComponents, notes: List[str]) -> None:
        ecc = exo.orbital.eccentricity
        period = exo.orbital.period_days
        if ecc is not None and ecc > 0.3:
            comp.features.append("extreme seasonal variation visible")
            notes.append(f"High eccentricity ({ecc:.2f})")
        if period is not None and period < 30:
            teff = star.temperature_k or 5778
            if teff < 4500:
                comp.view_angle = "terminator zone (day-night boundary)"
                comp.features.append("eternal twilight at the terminator")
                notes.append("Likely tidally locked")
    
    def _add_habitability_context(self, assessment: HabitabilityAssessment, comp: PromptComponents, notes: List[str]) -> None:
        score = assessment.total_score
        if score >= 0.8:
            comp.features.append("potentially habitable surface conditions")
            comp.mood = "hopeful, promising for life"
        elif score >= 0.6:
            comp.features.append("marginally habitable conditions")
        elif score >= 0.3:
            comp.features.append("challenging environment for life")
    
    def _add_style_modifiers(self, style: ImageStyle, comp: PromptComponents) -> None:
        if style == ImageStyle.REALISTIC:
            comp.style_modifiers = ["NASA visualization style", "scientifically accurate", "photorealistic"]
        elif style == ImageStyle.ARTISTIC:
            comp.style_modifiers = ["digital art", "vibrant colors", "dramatic composition"]
        elif style == ImageStyle.CINEMATIC:
            comp.style_modifiers = ["movie poster composition", "dramatic lighting", "epic scale"]
        elif style == ImageStyle.SCIENTIFIC:
            comp.style_modifiers = ["NASA/ESA art style", "educational illustration"]
        elif style == ImageStyle.RETRO_SCIFI:
            comp.style_modifiers = ["1970s sci-fi paperback cover", "retro space art", "bold colors"]
    
    def _generate_negative_prompt(self, exo: ExoplanetEntity, style: ImageStyle) -> str:
        negatives = ["text", "watermark", "signature", "blurry", "low quality", "distorted"]
        if style == ImageStyle.REALISTIC:
            negatives.extend(["cartoon", "anime", "fantasy elements"])
        ptype = exo.physical.classify_planet_type()
        if ptype in [PlanetType.GAS_GIANT, PlanetType.NEPTUNE_LIKE]:
            negatives.extend(["solid surface", "mountains", "continents"])
        return ", ".join(negatives)


# ============================================================
# Storage Service Interface
# ============================================================

class ImageStorageService(ABC):
    """Abstract base class for image storage backends."""
    
    @abstractmethod
    async def upload(self, image_data: bytes, filename: str) -> str:
        """Upload image and return public URL."""
        pass


class NoStorageService(ImageStorageService):
    """Returns base64 encoded image instead of uploading."""
    async def upload(self, image_data: bytes, filename: str) -> str:
        return f"data:image/png;base64,{base64.b64encode(image_data).decode()}"


class LocalStorageService(ImageStorageService):
    """Stores images locally."""
    def __init__(self, base_path: str = "./generated_images"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def upload(self, image_data: bytes, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)
        return f"/static/images/{filename}"


class ImgBBStorageService(ImageStorageService):
    """Upload images to ImgBB (free tier available)."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.upload_url = "https://api.imgbb.com/1/upload"
    
    async def upload(self, image_data: bytes, filename: str) -> str:
        b64_image = base64.b64encode(image_data).decode()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.upload_url,
                data={"key": self.api_key, "image": b64_image, "name": filename},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return data["data"]["url"]
            raise Exception(f"ImgBB upload failed: {data}")


# ============================================================
# Image Generation Service Interface
# ============================================================

class ImageGenerationService(ABC):
    """Abstract base class for image generation backends."""
    
    @abstractmethod
    async def generate(self, prompt: str, negative_prompt: str, style: ImageStyle, format: ImageFormat) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def check_status(self, generation_id: str) -> Dict[str, Any]:
        pass


# ============================================================
# Pollinations.ai Service (FREE with optional API key)
# ============================================================

class PollinationsImageService(ImageGenerationService):
    """
    Pollinations.ai - Image generation API.
    
    Documentation: https://pollinations.ai/
    API Key (optional): Get free credits at https://enter.pollinations.ai/
    
    Uses gen.pollinations.ai/image/{prompt} with Flux model.
    Authentication via Bearer token in Authorization header.
    """
    
    BASE_URL = "https://gen.pollinations.ai/image/"
    
    def __init__(
        self, 
        storage: Optional[ImageStorageService] = None, 
        api_key: Optional[str] = None,
        model: str = "flux"
    ):
        self.storage = storage or NoStorageService()
        self.api_key = api_key
        self.model = model
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers including auth if API key is provided."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://pollinations.ai/",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _get_dimensions(self, format: ImageFormat) -> tuple[int, int]:
        if format == ImageFormat.SQUARE: return 1024, 1024
        elif format == ImageFormat.LANDSCAPE: return 1792, 1024
        else: return 1024, 1792
    
    def _build_url(self, prompt: str, width: int, height: int, seed: int) -> str:
        """Build the image URL."""
        encoded_prompt = quote(prompt)
        return (
            f"{self.BASE_URL}{encoded_prompt}"
            f"?model={self.model}&width={width}&height={height}&seed={seed}&enhance=false"
        )
    
    async def generate(self, prompt: str, negative_prompt: str, style: ImageStyle, format: ImageFormat) -> Dict[str, Any]:
        generation_id = str(uuid.uuid4())
        width, height = self._get_dimensions(format)
        seed = abs(hash(generation_id)) % 100000
        
        image_url = self._build_url(prompt, width, height, seed)
        headers = self._get_headers()
        
        try:
            async with httpx.AsyncClient(
                timeout=120.0, 
                follow_redirects=True,
            ) as client:
                logger.info(f"Generating image from gen.pollinations.ai (model={self.model}, seed={seed})...")
                response = await client.get(image_url, headers=headers)
                response.raise_for_status()
                
                image_data = response.content
                content_type = response.headers.get("content-type", "image/jpeg")
                
                # Verify we got an image
                if "image" not in content_type:
                    raise ValueError(f"Expected image, got {content_type}. Response: {response.text[:200]}")
                
                ext = "png" if "png" in content_type else "jpg"
                filename = f"exoplanet_{generation_id}.{ext}"
                
                stored_url = await self.storage.upload(image_data, filename)
                
                return {
                    "generation_id": generation_id,
                    "status": "completed",
                    "url": stored_url,
                    "direct_url": image_url,
                    "provider": "pollinations.ai",
                    "model": self.model,
                    "width": width,
                    "height": height,
                    "image_data": image_data,
                }
        except httpx.TimeoutException:
            logger.error("Pollinations.ai request timed out")
            return {
                "generation_id": generation_id, 
                "status": "timeout", 
                "direct_url": image_url,
                "error": "Request timed out (120s).", 
                "provider": "pollinations.ai"
            }
        except Exception as e:
            logger.error(f"Pollinations.ai error: {e}")
            return {
                "generation_id": generation_id, 
                "status": "error", 
                "direct_url": image_url,
                "error": str(e), 
                "provider": "pollinations.ai",
                "hint": "Get a free API key at https://enter.pollinations.ai/"
            }
    
    async def check_status(self, generation_id: str) -> Dict[str, Any]:
        return {"generation_id": generation_id, "status": "completed"}


# ============================================================
# OpenAI DALL-E Service
# ============================================================

class DallEImageService(ImageGenerationService):
    """OpenAI DALL-E implementation (requires API key)."""
    
    def __init__(self, api_key: str, storage: Optional[ImageStorageService] = None):
        self.api_key = api_key
        self.storage = storage or NoStorageService()
    
    async def generate(self, prompt: str, negative_prompt: str, style: ImageStyle, format: ImageFormat) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        generation_id = str(uuid.uuid4())
        size_map = {ImageFormat.SQUARE: "1024x1024", ImageFormat.LANDSCAPE: "1792x1024", ImageFormat.PORTRAIT: "1024x1792"}
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": size_map[format], "quality": "hd", "response_format": "b64_json"},
            )
            response.raise_for_status()
            data = response.json()
            
            b64_image = data["data"][0]["b64_json"]
            image_data = base64.b64decode(b64_image)
            filename = f"exoplanet_{generation_id}.png"
            stored_url = await self.storage.upload(image_data, filename)
            
            return {"generation_id": generation_id, "status": "completed", "url": stored_url, "provider": "openai-dalle-3", "image_data": image_data}
    
    async def check_status(self, generation_id: str) -> Dict[str, Any]:
        return {"generation_id": generation_id, "status": "completed"}


# ============================================================
# Mock Service
# ============================================================

class MockImageGenerationService(ImageGenerationService):
    """Mock implementation for testing."""
    async def generate(self, prompt: str, negative_prompt: str, style: ImageStyle, format: ImageFormat) -> Dict[str, Any]:
        return {"generation_id": str(uuid.uuid4()), "status": "mock", "url": None, "provider": "mock", "message": "Mock - no image generated"}
    
    async def check_status(self, generation_id: str) -> Dict[str, Any]:
        return {"generation_id": generation_id, "status": "completed"}


# ============================================================
# Factory Functions
# ============================================================

def get_storage_service(storage_type: Optional[str] = None) -> ImageStorageService:
    """Get storage service based on configuration."""
    storage = storage_type or settings.image_storage
    
    if storage == "local":
        return LocalStorageService(settings.image_storage_path)
    elif storage == "imgbb" and settings.imgbb_api_key:
        return ImgBBStorageService(settings.imgbb_api_key)
    return NoStorageService()


def get_image_service(provider: Optional[str] = None) -> ImageGenerationService:
    """
    Get image generation service.
    
    Options: 
    - "pollinations" (free with optional API key for better reliability)
    - "dalle" (OpenAI, requires API key)
    - "mock" (for testing)
    
    For Pollinations.ai:
    - Without API key: Uses image.pollinations.ai (may have rate limits/downtime)
    - With API key: Uses gen.pollinations.ai with Flux model (more reliable)
    - Get free API key at: https://enter.pollinations.ai/
    """
    provider = provider or settings.image_provider
    storage = get_storage_service()
    
    if provider == "pollinations":
        return PollinationsImageService(
            storage=storage,
            api_key=settings.pollinations_api_key or None,
            model="flux"
        )
    elif provider == "dalle" and settings.openai_api_key:
        return DallEImageService(api_key=settings.openai_api_key, storage=storage)
    elif provider == "mock":
        return MockImageGenerationService()
    else:
        # Default to Pollinations
        return PollinationsImageService(
            storage=storage,
            api_key=settings.pollinations_api_key or None,
            model="flux"
        )
