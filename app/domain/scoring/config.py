"""
Scoring Configuration Management.

This module handles loading and managing scoring configuration,
including factor weights, thresholds, and scientific parameters.

Configuration can be loaded from:
1. Built-in defaults (this file)
2. YAML configuration files
3. Environment variables

The configuration system allows researchers to:
- Adjust factor weights without code changes
- Test different scoring hypotheses
- Customize the scoring for specific research goals
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import os


@dataclass
class FactorWeightConfig:
    """Configuration for a single factor's weight and parameters."""
    factor_id: str
    weight: float
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate weight is in valid range."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


@dataclass
class ScoringConfig:
    """
    Complete scoring configuration.
    
    Attributes:
        version: Configuration version string
        factor_weights: Dictionary mapping factor_id to weight config
        normalization_method: How to normalize final score
        minimum_factors: Minimum number of factors required
        confidence_thresholds: Thresholds for confidence levels
    """
    
    version: str = "2.0.0"
    factor_weights: Dict[str, FactorWeightConfig] = field(default_factory=dict)
    normalization_method: str = "weighted_average"
    minimum_factors: int = 3
    confidence_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Default factor weights based on scientific importance
    DEFAULT_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        # Stellar factors (30% total)
        "stellar_type": 0.12,
        "stellar_luminosity": 0.08,
        "stellar_age": 0.05,
        "habitable_zone_position": 0.05,
        
        # Planetary factors (40% total)
        "planet_radius": 0.12,
        "planet_mass": 0.08,
        "planet_density": 0.05,
        "equilibrium_temperature": 0.10,
        "surface_gravity": 0.05,
        
        # Orbital factors (15% total)
        "orbital_eccentricity": 0.08,
        "tidal_locking": 0.07,
        
        # Derived/Estimated factors (15% total)
        "atmosphere_retention": 0.08,
        "magnetic_field_potential": 0.07,
    })
    
    DEFAULT_CONFIDENCE_THRESHOLDS: Dict[str, float] = field(default_factory=lambda: {
        "very_low": 0.2,
        "low": 0.4,
        "medium": 0.6,
        "high": 0.8,
        "very_high": 1.0,
    })
    
    def __post_init__(self):
        """Initialize with defaults if empty."""
        if not self.factor_weights:
            self.factor_weights = {
                fid: FactorWeightConfig(factor_id=fid, weight=w)
                for fid, w in self.DEFAULT_WEIGHTS.items()
            }
        if not self.confidence_thresholds:
            self.confidence_thresholds = dict(self.DEFAULT_CONFIDENCE_THRESHOLDS)
    
    def get_weight(self, factor_id: str) -> float:
        """
        Get the weight for a factor.
        
        Args:
            factor_id: The factor's unique identifier
            
        Returns:
            Weight value (0.0 if factor not configured)
        """
        if factor_id in self.factor_weights:
            config = self.factor_weights[factor_id]
            return config.weight if config.enabled else 0.0
        return 0.0
    
    def is_factor_enabled(self, factor_id: str) -> bool:
        """Check if a factor is enabled."""
        if factor_id in self.factor_weights:
            return self.factor_weights[factor_id].enabled
        return True  # Enable by default
    
    def get_factor_parameters(self, factor_id: str) -> Dict[str, Any]:
        """Get custom parameters for a factor."""
        if factor_id in self.factor_weights:
            return self.factor_weights[factor_id].parameters
        return {}
    
    def get_enabled_factors(self) -> List[str]:
        """Get list of enabled factor IDs."""
        return [
            fid for fid, config in self.factor_weights.items()
            if config.enabled
        ]
    
    def get_total_weight(self) -> float:
        """Calculate total weight of all enabled factors."""
        return sum(
            config.weight
            for config in self.factor_weights.values()
            if config.enabled
        )
    
    def normalize_weights(self) -> Dict[str, float]:
        """
        Return weights normalized to sum to 1.0.
        
        Returns:
            Dictionary of factor_id -> normalized_weight
        """
        total = self.get_total_weight()
        if total == 0:
            return {}
        
        return {
            fid: config.weight / total
            for fid, config in self.factor_weights.items()
            if config.enabled
        }
    
    @classmethod
    def from_yaml(cls, filepath: str | Path) -> "ScoringConfig":
        """
        Load configuration from a YAML file.
        
        Args:
            filepath: Path to YAML configuration file
            
        Returns:
            ScoringConfig instance
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoringConfig":
        """
        Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            ScoringConfig instance
        """
        factor_weights = {}
        for fid, config in data.get("factor_weights", {}).items():
            if isinstance(config, dict):
                factor_weights[fid] = FactorWeightConfig(
                    factor_id=fid,
                    weight=config.get("weight", 0.1),
                    enabled=config.get("enabled", True),
                    parameters=config.get("parameters", {}),
                )
            else:
                # Simple weight value
                factor_weights[fid] = FactorWeightConfig(
                    factor_id=fid,
                    weight=float(config),
                )
        
        return cls(
            version=data.get("version", "2.0.0"),
            factor_weights=factor_weights,
            normalization_method=data.get("normalization_method", "weighted_average"),
            minimum_factors=data.get("minimum_factors", 3),
            confidence_thresholds=data.get("confidence_thresholds", {}),
        )
    
    def to_yaml(self, filepath: str | Path) -> None:
        """
        Save configuration to a YAML file.
        
        Args:
            filepath: Output path for YAML file
        """
        data = self.to_dict()
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "factor_weights": {
                fid: {
                    "weight": config.weight,
                    "enabled": config.enabled,
                    "parameters": config.parameters,
                }
                for fid, config in self.factor_weights.items()
            },
            "normalization_method": self.normalization_method,
            "minimum_factors": self.minimum_factors,
            "confidence_thresholds": self.confidence_thresholds,
        }


def load_default_config() -> ScoringConfig:
    """
    Load the default scoring configuration.
    
    Checks for config file in standard locations, falls back to defaults.
    
    Returns:
        ScoringConfig instance
    """
    # Check for environment variable
    config_path = os.environ.get("EXOHABITABILITY_SCORING_CONFIG")
    
    # Check standard locations
    search_paths = [
        config_path,
        "config/scoring.yaml",
        "config/scoring.yml",
        Path(__file__).parent.parent.parent / "config" / "scoring.yaml",
    ]
    
    for path in search_paths:
        if path and Path(path).exists():
            return ScoringConfig.from_yaml(path)
    
    # Return defaults
    return ScoringConfig()
