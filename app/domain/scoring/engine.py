"""
Scoring Engine - Core orchestrator for habitability assessment.

This module contains the main ScoringEngine class that:
1. Manages registered scoring factors (plugins)
2. Orchestrates factor evaluation
3. Combines scores using configured weights
4. Produces the final HabitabilityAssessment

Design Principles:
- Open for extension, closed for modification
- Dependency injection for factors and configuration
- Clear separation between orchestration and calculation
"""

from typing import List, Dict, Optional, Type
from datetime import datetime

from app.domain.entities.exoplanet import ExoplanetEntity
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import (
    HabitabilityAssessment,
    FactorScore,
    ConfidenceLevel,
)
from app.domain.scoring.base import ScoringFactor, FactorResult, FactorCategory
from app.domain.scoring.config import ScoringConfig, load_default_config
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScoringEngine:
    """
    Main scoring engine for habitability assessment.
    
    The engine manages a collection of scoring factors (plugins) and
    orchestrates the evaluation process. Factors can be registered
    dynamically, allowing the system to be extended without modifying
    this core class.
    
    Example usage:
        engine = ScoringEngine()
        engine.register_factor(StellarTypeFactor())
        engine.register_factor(PlanetRadiusFactor())
        
        assessment = engine.evaluate(exoplanet, star)
    """
    
    VERSION = "2.0.0"
    
    def __init__(
        self,
        config: Optional[ScoringConfig] = None,
        factors: Optional[List[ScoringFactor]] = None,
    ):
        """
        Initialize the scoring engine.
        
        Args:
            config: Scoring configuration (weights, thresholds)
            factors: Initial list of scoring factors to register
        """
        self.config = config or load_default_config()
        self._factors: Dict[str, ScoringFactor] = {}
        
        if factors:
            for factor in factors:
                self.register_factor(factor)
        
        logger.info(f"ScoringEngine v{self.VERSION} initialized")
    
    def register_factor(self, factor: ScoringFactor) -> None:
        """
        Register a scoring factor with the engine.
        
        Args:
            factor: Scoring factor instance implementing ScoringFactor protocol
            
        Raises:
            ValueError: If factor with same ID already registered
        """
        if factor.factor_id in self._factors:
            logger.warning(f"Replacing existing factor: {factor.factor_id}")
        
        self._factors[factor.factor_id] = factor
        logger.debug(f"Registered scoring factor: {factor.factor_id}")
    
    def unregister_factor(self, factor_id: str) -> bool:
        """
        Remove a scoring factor from the engine.
        
        Args:
            factor_id: ID of the factor to remove
            
        Returns:
            True if factor was removed, False if not found
        """
        if factor_id in self._factors:
            del self._factors[factor_id]
            logger.debug(f"Unregistered scoring factor: {factor_id}")
            return True
        return False
    
    def get_registered_factors(self) -> List[str]:
        """Get list of registered factor IDs."""
        return list(self._factors.keys())
    
    def get_factor(self, factor_id: str) -> Optional[ScoringFactor]:
        """Get a specific factor by ID."""
        return self._factors.get(factor_id)
    
    def evaluate(
        self,
        exoplanet: ExoplanetEntity,
        star: StarEntity,
    ) -> HabitabilityAssessment:
        """
        Perform complete habitability assessment.
        
        Evaluates all registered and enabled factors, combines scores
        using configured weights, and produces a comprehensive assessment.
        
        Args:
            exoplanet: The exoplanet entity to assess
            star: The host star entity
            
        Returns:
            HabitabilityAssessment with scores and explanations
        """
        logger.info(f"Starting habitability assessment for {exoplanet.name}")
        
        factor_scores: List[FactorScore] = []
        missing_parameters: List[str] = []
        applicable_factors = 0
        total_applicable_factors = 0
        
        # Get normalized weights
        normalized_weights = self.config.normalize_weights()
        
        # Evaluate each factor
        for factor_id, factor in self._factors.items():
            # Check if factor is enabled
            if not self.config.is_factor_enabled(factor_id):
                logger.debug(f"Skipping disabled factor: {factor_id}")
                continue
            
            total_applicable_factors += 1
            
            try:
                # Evaluate the factor
                result = factor.evaluate(exoplanet, star)
                
                # Get weight (use normalized weight or factor's default)
                weight = normalized_weights.get(factor_id, 0.1)
                
                # Track applicability
                if result.is_applicable:
                    applicable_factors += 1
                else:
                    if result.missing_data:
                        missing_parameters.append(result.missing_data)
                
                # Create factor score
                factor_score = FactorScore(
                    factor_id=factor_id,
                    factor_name=factor.factor_name,
                    category=factor.category.value,
                    raw_score=result.score,
                    weight=weight,
                    weighted_score=result.score * weight,
                    input_value=result.input_value,
                    input_unit=result.input_unit,
                    optimal_range=result.optimal_range,
                    explanation=result.explanation,
                    confidence=result.confidence,
                    references=result.references or factor.references,
                )
                factor_scores.append(factor_score)
                
            except Exception as e:
                logger.error(f"Error evaluating factor {factor_id}: {e}")
                # Add error factor score
                factor_scores.append(FactorScore(
                    factor_id=factor_id,
                    factor_name=factor.factor_name,
                    category=factor.category.value,
                    raw_score=0.5,
                    weight=normalized_weights.get(factor_id, 0.1),
                    weighted_score=0.05,
                    explanation=f"Error during evaluation: {str(e)}",
                    confidence=ConfidenceLevel.VERY_LOW,
                ))
        
        # Calculate total score
        total_score = self._calculate_total_score(factor_scores)
        
        # Calculate data completeness
        data_completeness = (
            applicable_factors / total_applicable_factors
            if total_applicable_factors > 0 else 0.0
        )
        
        # Create assessment
        assessment = HabitabilityAssessment(
            exoplanet_id=exoplanet.id or 0,
            exoplanet_name=exoplanet.name,
            host_star_name=star.name,
            total_score=total_score,
            factor_scores=factor_scores,
            data_completeness=data_completeness,
            missing_parameters=missing_parameters,
            assessment_timestamp=datetime.utcnow(),
            scoring_version=self.VERSION,
        )
        
        logger.info(
            f"Assessment complete for {exoplanet.name}: "
            f"score={total_score:.3f}, completeness={data_completeness:.0%}"
        )
        
        return assessment
    
    def _calculate_total_score(self, factor_scores: List[FactorScore]) -> float:
        """
        Calculate the total habitability score from factor scores.
        
        Uses weighted average by default, can be configured for other methods.
        
        Args:
            factor_scores: List of individual factor scores
            
        Returns:
            Total score between 0.0 and 1.0
        """
        if not factor_scores:
            return 0.0
        
        if self.config.normalization_method == "weighted_average":
            total_weight = sum(f.weight for f in factor_scores)
            if total_weight == 0:
                return 0.0
            return sum(f.weighted_score for f in factor_scores) / total_weight
        
        elif self.config.normalization_method == "geometric_mean":
            # Geometric mean - penalizes low scores more heavily
            import math
            product = 1.0
            for f in factor_scores:
                # Avoid zero scores breaking the calculation
                product *= max(f.raw_score, 0.01)
            return product ** (1.0 / len(factor_scores))
        
        elif self.config.normalization_method == "minimum":
            # Weakest link approach - score limited by worst factor
            return min(f.raw_score for f in factor_scores)
        
        else:
            # Default to weighted average
            total_weight = sum(f.weight for f in factor_scores)
            if total_weight == 0:
                return 0.0
            return sum(f.weighted_score for f in factor_scores) / total_weight
    
    def get_methodology(self) -> dict:
        """
        Get detailed methodology information.
        
        Returns:
            Dictionary describing all factors, weights, and references
        """
        factors_info = []
        for factor_id, factor in self._factors.items():
            weight = self.config.get_weight(factor_id)
            factors_info.append({
                "id": factor_id,
                "name": factor.factor_name,
                "category": factor.category.value,
                "description": factor.description,
                "weight": weight,
                "enabled": self.config.is_factor_enabled(factor_id),
                "references": factor.references,
            })
        
        return {
            "version": self.VERSION,
            "normalization_method": self.config.normalization_method,
            "minimum_factors_required": self.config.minimum_factors,
            "factors": factors_info,
            "total_factors": len(self._factors),
            "enabled_factors": len(self.config.get_enabled_factors()),
        }
    
    def get_factors_by_category(self) -> Dict[str, List[str]]:
        """Get factors grouped by category."""
        result: Dict[str, List[str]] = {}
        for factor_id, factor in self._factors.items():
            category = factor.category.value
            if category not in result:
                result[category] = []
            result[category].append(factor_id)
        return result


def create_default_engine() -> ScoringEngine:
    """
    Create a scoring engine with all default factors registered.
    
    Returns:
        ScoringEngine with standard habitability factors
    """
    from app.domain.scoring.factors import get_all_factors
    
    engine = ScoringEngine()
    for factor in get_all_factors():
        engine.register_factor(factor)
    
    return engine
