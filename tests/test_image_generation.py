"""
Unit tests for the Image Generation Service.

Tests cover:
- Prompt generation from exoplanet data
- Scientific accuracy of prompts
- Style variations
- Edge cases
"""

import pytest

from app.services.image_generation import (
    ImagePromptGenerator,
    ImageStyle,
    ImageFormat,
    GeneratedImage,
    PromptComponents,
    MockImageGenerationService,
)
from app.domain.entities.exoplanet import ExoplanetEntity, OrbitalParameters, PhysicalParameters
from app.domain.entities.star import StarEntity


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def earth_like_planet() -> ExoplanetEntity:
    """Create an Earth-like test exoplanet."""
    return ExoplanetEntity(
        name="Kepler-442b",
        orbital=OrbitalParameters(
            period_days=112.3,
            semi_major_axis_au=0.409,
            eccentricity=0.04,
        ),
        physical=PhysicalParameters(
            radius_earth=1.34,
            mass_earth=2.34,
            equilibrium_temp_k=273,
        ),
    )


@pytest.fixture
def hot_jupiter() -> ExoplanetEntity:
    """Create a hot Jupiter test exoplanet."""
    return ExoplanetEntity(
        name="HD-189733b",
        orbital=OrbitalParameters(
            period_days=2.2,
            semi_major_axis_au=0.03,
            eccentricity=0.0,
        ),
        physical=PhysicalParameters(
            radius_earth=12.7,
            mass_earth=363.0,
            equilibrium_temp_k=1200,
        ),
    )


@pytest.fixture
def frozen_world() -> ExoplanetEntity:
    """Create a frozen exoplanet."""
    return ExoplanetEntity(
        name="Frozen-1",
        orbital=OrbitalParameters(
            period_days=500.0,
            semi_major_axis_au=2.5,
        ),
        physical=PhysicalParameters(
            radius_earth=1.1,
            mass_earth=1.2,
            equilibrium_temp_k=150,
        ),
    )


@pytest.fixture
def lava_world() -> ExoplanetEntity:
    """Create a lava world exoplanet."""
    return ExoplanetEntity(
        name="Lava-1",
        orbital=OrbitalParameters(
            period_days=0.5,
            semi_major_axis_au=0.01,
        ),
        physical=PhysicalParameters(
            radius_earth=1.2,
            mass_earth=1.5,
            equilibrium_temp_k=2000,
        ),
    )


@pytest.fixture
def sun_like_star() -> StarEntity:
    """Create a Sun-like test star."""
    return StarEntity(
        name="Sun-Twin",
        spectral_type="G2V",
        temperature_k=5778,
        mass_solar=1.0,
        radius_solar=1.0,
        luminosity_solar=1.0,
    )


@pytest.fixture
def m_dwarf_star() -> StarEntity:
    """Create an M dwarf test star."""
    return StarEntity(
        name="Proxima-Like",
        spectral_type="M5V",
        temperature_k=3050,
        mass_solar=0.12,
        radius_solar=0.15,
        luminosity_solar=0.0017,
    )


@pytest.fixture
def hot_star() -> StarEntity:
    """Create a hot A-type star."""
    return StarEntity(
        name="Vega-Like",
        spectral_type="A0V",
        temperature_k=9600,
        mass_solar=2.1,
        radius_solar=2.4,
        luminosity_solar=40.0,
    )


@pytest.fixture
def prompt_generator() -> ImagePromptGenerator:
    """Create a prompt generator instance."""
    return ImagePromptGenerator()


# ============================================================
# Prompt Generator Tests
# ============================================================

class TestImagePromptGenerator:
    """Tests for the ImagePromptGenerator class."""
    
    def test_basic_prompt_generation(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test basic prompt generation works."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.REALISTIC,
        )
        
        assert isinstance(result, GeneratedImage)
        assert result.exoplanet_name == "Kepler-442b"
        assert len(result.prompt) > 50
        assert result.style == ImageStyle.REALISTIC
    
    def test_prompt_contains_planet_features(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test prompt contains relevant planet features."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        prompt_lower = result.prompt.lower()
        
        # Should mention rocky/terrestrial nature
        assert any(word in prompt_lower for word in ["rocky", "terrestrial", "super-earth"])
    
    def test_star_color_in_prompt(
        self,
        prompt_generator,
        earth_like_planet,
    ):
        """Test star color is reflected in prompt."""
        # Test with different star types
        g_star = StarEntity(name="G", spectral_type="G2V", temperature_k=5500)
        m_star = StarEntity(name="M", spectral_type="M5V", temperature_k=3000)
        
        g_result = prompt_generator.generate_prompt(earth_like_planet, g_star)
        m_result = prompt_generator.generate_prompt(earth_like_planet, m_star)
        
        assert "yellow" in g_result.prompt.lower()
        assert "red" in m_result.prompt.lower()
    
    def test_hot_planet_prompt(
        self,
        prompt_generator,
        lava_world,
        sun_like_star,
    ):
        """Test hot planet gets appropriate prompt."""
        result = prompt_generator.generate_prompt(lava_world, sun_like_star)
        
        prompt_lower = result.prompt.lower()
        
        # Should mention extreme heat
        assert any(word in prompt_lower for word in ["lava", "molten", "scorching", "hellish"])
    
    def test_frozen_planet_prompt(
        self,
        prompt_generator,
        frozen_world,
        sun_like_star,
    ):
        """Test frozen planet gets appropriate prompt."""
        result = prompt_generator.generate_prompt(frozen_world, sun_like_star)
        
        prompt_lower = result.prompt.lower()
        
        # Should mention cold/ice
        assert any(word in prompt_lower for word in ["frozen", "ice", "cold", "glacial"])
    
    def test_gas_giant_prompt(
        self,
        prompt_generator,
        hot_jupiter,
        sun_like_star,
    ):
        """Test gas giant gets appropriate prompt."""
        result = prompt_generator.generate_prompt(hot_jupiter, sun_like_star)
        
        prompt_lower = result.prompt.lower()
        
        # Should mention gas/atmosphere features
        assert any(word in prompt_lower for word in ["gas", "atmosphere", "clouds", "storm", "band"])


class TestImageStyles:
    """Tests for different artistic styles."""
    
    def test_realistic_style(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test realistic style prompt."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.REALISTIC,
        )
        
        prompt_lower = result.prompt.lower()
        
        assert any(word in prompt_lower for word in ["photorealistic", "realistic", "render"])
    
    def test_artistic_style(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test artistic style prompt."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.ARTISTIC,
        )
        
        prompt_lower = result.prompt.lower()
        
        assert any(word in prompt_lower for word in ["artistic", "painting", "digital art"])
    
    def test_cinematic_style(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test cinematic style prompt."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.CINEMATIC,
        )
        
        prompt_lower = result.prompt.lower()
        
        assert any(word in prompt_lower for word in ["cinematic", "movie", "dramatic"])
    
    def test_scientific_style(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test scientific style prompt."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.SCIENTIFIC,
        )
        
        prompt_lower = result.prompt.lower()
        
        assert any(word in prompt_lower for word in ["scientific", "nasa", "accurate"])
    
    def test_retro_style(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test retro sci-fi style prompt."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.RETRO_SCIFI,
        )
        
        prompt_lower = result.prompt.lower()
        
        assert any(word in prompt_lower for word in ["retro", "1970s", "vintage", "sci-fi"])


class TestNegativePrompts:
    """Tests for negative prompt generation."""
    
    def test_negative_prompt_exists(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test negative prompt is generated."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        assert result.negative_prompt is not None
        assert len(result.negative_prompt) > 0
    
    def test_negative_prompt_contains_quality_terms(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test negative prompt filters low quality."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        neg_lower = result.negative_prompt.lower()
        
        assert any(word in neg_lower for word in ["blurry", "low quality", "watermark"])
    
    def test_gas_giant_negative_prompt(
        self,
        prompt_generator,
        hot_jupiter,
        sun_like_star,
    ):
        """Test gas giant negative prompt excludes surface features."""
        result = prompt_generator.generate_prompt(
            hot_jupiter,
            sun_like_star,
        )
        
        neg_lower = result.negative_prompt.lower()
        
        # Should exclude solid surface features
        assert any(word in neg_lower for word in ["solid surface", "mountains", "continents"])


class TestScientificNotes:
    """Tests for scientific notes generation."""
    
    def test_scientific_notes_included(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test scientific notes are included."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        assert result.scientific_notes is not None
        assert len(result.scientific_notes) > 0
    
    def test_temperature_note(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test temperature is noted."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        notes_text = " ".join(result.scientific_notes).lower()
        
        # Should mention temperature
        assert any(term in notes_text for term in ["t_eq", "temperature", "habitable", "k:"])


class TestPromptCaching:
    """Tests for prompt hash/caching."""
    
    def test_prompt_hash_generated(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test prompt hash is generated."""
        result = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
        )
        
        assert result.prompt_hash is not None
        assert len(result.prompt_hash) == 32  # MD5 hash length
    
    def test_same_inputs_same_hash(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test same inputs produce same hash."""
        result1 = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.REALISTIC,
        )
        result2 = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.REALISTIC,
        )
        
        assert result1.prompt_hash == result2.prompt_hash
    
    def test_different_style_different_hash(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test different styles produce different hashes."""
        result1 = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.REALISTIC,
        )
        result2 = prompt_generator.generate_prompt(
            earth_like_planet,
            sun_like_star,
            style=ImageStyle.ARTISTIC,
        )
        
        assert result1.prompt_hash != result2.prompt_hash


# ============================================================
# Mock Service Tests
# ============================================================

class TestMockImageService:
    """Tests for the mock image generation service."""
    
    @pytest.mark.asyncio
    async def test_mock_service_returns_result(self):
        """Test mock service returns a result."""
        service = MockImageGenerationService()
        
        result = await service.generate(
            prompt="test prompt",
            negative_prompt="test negative",
            style=ImageStyle.REALISTIC,
            format=ImageFormat.LANDSCAPE,
        )
        
        assert result is not None
        assert "generation_id" in result
        assert "url" in result
        assert result["status"] == "mock"  # Mock service returns "mock" status
        assert result["provider"] == "mock"
    
    @pytest.mark.asyncio
    async def test_mock_service_check_status(self):
        """Test mock service status check."""
        service = MockImageGenerationService()
        
        result = await service.check_status("test-id")
        
        assert result["status"] == "completed"


# ============================================================
# Edge Cases
# ============================================================

class TestEdgeCases:
    """Tests for edge cases in prompt generation."""
    
    def test_minimal_data_planet(
        self,
        prompt_generator,
        sun_like_star,
    ):
        """Test planet with minimal data."""
        minimal_planet = ExoplanetEntity(
            name="Minimal",
            orbital=OrbitalParameters(),
            physical=PhysicalParameters(radius_earth=1.5),
        )
        
        result = prompt_generator.generate_prompt(minimal_planet, sun_like_star)
        
        assert result is not None
        assert len(result.prompt) > 0
    
    def test_minimal_data_star(
        self,
        prompt_generator,
        earth_like_planet,
    ):
        """Test star with minimal data."""
        minimal_star = StarEntity(name="Minimal")
        
        result = prompt_generator.generate_prompt(earth_like_planet, minimal_star)
        
        assert result is not None
        assert len(result.prompt) > 0
    
    def test_all_formats(
        self,
        prompt_generator,
        earth_like_planet,
        sun_like_star,
    ):
        """Test all image formats."""
        for fmt in ImageFormat:
            result = prompt_generator.generate_prompt(
                earth_like_planet,
                sun_like_star,
                format=fmt,
            )
            
            assert result.format == fmt
