"""SQLAlchemy base class and shared configuration.

This module provides the declarative base class and common SQLAlchemy
tooling for both unit tests and production use.
"""

from sqlalchemy.orm import declarative_base

# The base class for all SQLAlchemy models.  This is imported by
# ``db.models`` and, when combined with Alembic's ``env.py``, provides the
# target metadata that Alembic needs for migrations in Phase 2.
Base = declarative_base()