"""
SQLAlchemy base configuration.

Provides the declarative base and common model utilities.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common columns and utilities for all database models.
    """
    
    metadata = metadata
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Model data as dictionary
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
