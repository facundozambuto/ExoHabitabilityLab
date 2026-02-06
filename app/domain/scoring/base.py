"""
Scoring Factor Base Classes and Protocols.

This module defines the abstract base class and interfaces for
habitability scoring factors. Each factor implements the ScoringFactor
protocol and can be dynamically registered with the scoring engine.

Design Pattern: Strategy Pattern
- Each factor is a strategy for evaluating one aspect of habitability
- Factors are interchangeable and can be added/removed at runtime
- The engine doesn't need to know the details of each factor
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Protocol, runtime_checkable
from enum import Enum

from app.domain.entities.exoplanet import ExoplanetEntity
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import ConfidenceLevel


class FactorCategory(str, Enum):
    """Categories for grouping scoring factors."""
    STELLAR = "stellar"           # Host star properties
    PLANETARY = "planetary"       # Planet physical properties  
    ORBITAL = "orbital"           # Orbital characteristics
    ATMOSPHERIC = "atmospheric"   # Atmosphere-related estimates
    DERIVED = "derived"           # Calculated/derived properties


@dataclass
class FactorResult:
    """
    Result from evaluating a single scoring factor.
    
    Attributes:
        factor_id: Unique identifier for this factor
        score: Normalized score (0.0 to 1.0)
        input_value: The raw input value used
        input_unit: Unit of measurement for input
        optimal_range: Description of optimal values for this factor
        explanation: Scientific explanation of the score
        confidence: Confidence level based on data quality
        references: Scientific references for this factor's logic
        is_applicable: Whether this factor could be evaluated
        missing_data: What data was missing if not applicable
    """
    
    factor_id: str
    score: float = 0.5  # Default neutral score
    input_value: Optional[str] = None
    input_unit: Optional[str] = None
    optimal_range: Optional[str] = None
    explanation: str = "No evaluation performed"
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    references: List[str] = field(default_factory=list)
    is_applicable: bool = True
    missing_data: Optional[str] = None
    
    def __post_init__(self):
        """Validate score is in valid range."""
        self.score = max(0.0, min(1.0, self.score))


@runtime_checkable
class ScoringFactor(Protocol):
    """
    Protocol defining the interface for all scoring factors.
    
    Each scoring factor must implement:
    - factor_id: Unique string identifier
    - factor_name: Human-readable name
    - category: Factor category for grouping
    - description: Scientific description
    - evaluate(): Method to calculate the score
    """
    
    @property
    def factor_id(self) -> str:
        """Unique identifier for this factor."""
        ...
    
    @property
    def factor_name(self) -> str:
        """Human-readable name for display."""
        ...
    
    @property
    def category(self) -> FactorCategory:
        """Category for grouping factors."""
        ...
    
    @property
    def description(self) -> str:
        """Scientific description of what this factor measures."""
        ...
    
    @property
    def references(self) -> List[str]:
        """Scientific references for the scoring logic."""
        ...
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """
        Evaluate this factor for the given exoplanet/star system.
        
        Args:
            exoplanet: The exoplanet entity to evaluate
            star: The host star entity
            
        Returns:
            FactorResult with score, explanation, and metadata
        """
        ...


class BaseScoringFactor(ABC):
    """
    Abstract base class for scoring factors.
    
    Provides common functionality and enforces the interface.
    Concrete factors should extend this class and implement
    the abstract methods.
    """
    
    def __init__(self):
        """Initialize the scoring factor."""
        pass
    
    @property
    @abstractmethod
    def factor_id(self) -> str:
        """Unique identifier for this factor."""
        pass
    
    @property
    @abstractmethod
    def factor_name(self) -> str:
        """Human-readable name."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> FactorCategory:
        """Factor category."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Scientific description."""
        pass
    
    @property
    def references(self) -> List[str]:
        """Scientific references (override in subclass if needed)."""
        return []
    
    @abstractmethod
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> FactorResult:
        """Evaluate this factor."""
        pass
    
    def _create_missing_data_result(self, missing_field: str) -> FactorResult:
        """
        Create a result for when required data is missing.
        
        Args:
            missing_field: Name of the missing field
            
        Returns:
            FactorResult with neutral score and explanation
        """
        return FactorResult(
            factor_id=self.factor_id,
            score=0.5,  # Neutral score when data missing
            explanation=f"Required data '{missing_field}' is not available. "
                       f"Assigned neutral score.",
            confidence=ConfidenceLevel.VERY_LOW,
            is_applicable=False,
            missing_data=missing_field,
        )
    
    def _interpolate_score(
        self,
        value: float,
        optimal_min: float,
        optimal_max: float,
        absolute_min: float,
        absolute_max: float,
    ) -> float:
        """
        Interpolate a score based on value's position relative to optimal range.
        
        Returns 1.0 if in optimal range, decreasing to 0.0 at absolute limits.
        
        Args:
            value: The value to score
            optimal_min: Lower bound of optimal range (score = 1.0)
            optimal_max: Upper bound of optimal range (score = 1.0)
            absolute_min: Lower absolute limit (score = 0.0)
            absolute_max: Upper absolute limit (score = 0.0)
            
        Returns:
            Score between 0.0 and 1.0
        """
        # In optimal range
        if optimal_min <= value <= optimal_max:
            return 1.0
        
        # Below optimal
        if value < optimal_min:
            if value <= absolute_min:
                return 0.0
            # Linear interpolation from absolute_min to optimal_min
            return (value - absolute_min) / (optimal_min - absolute_min)
        
        # Above optimal
        if value > optimal_max:
            if value >= absolute_max:
                return 0.0
            # Linear interpolation from optimal_max to absolute_max
            return (absolute_max - value) / (absolute_max - optimal_max)
        
        return 0.5  # Fallback
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.factor_id}')"
