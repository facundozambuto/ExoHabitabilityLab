"""
Domain Entities - Core business objects.

Entities are objects with a distinct identity that persists over time.
They encapsulate both data and behavior related to exoplanets,
stars, and habitability assessments.
"""

from app.domain.entities.exoplanet import ExoplanetEntity
from app.domain.entities.star import StarEntity
from app.domain.entities.habitability import HabitabilityAssessment

__all__ = [
    "ExoplanetEntity",
    "StarEntity",
    "HabitabilityAssessment",
]
