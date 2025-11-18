"""
Database initialization and session management for Int Crucible.

Extends Kosmos database infrastructure with Crucible-specific models.
"""

from crucible.db.models import Base
from crucible.db.session import get_session, init_database, init_from_config

__all__ = [
    "Base",
    "init_database",
    "get_session",
    "init_from_config",
]

