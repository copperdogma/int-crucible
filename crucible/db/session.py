"""
Database session management for Int Crucible.

Extends Kosmos database initialization to include Crucible models.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from kosmos.db import get_session as kosmos_get_session
from kosmos.db import init_database as kosmos_init_database
from sqlalchemy.orm import Session

from crucible.config import get_config
from crucible.db.models import Base as CrucibleBase

logger = logging.getLogger(__name__)


def init_database(database_url: str = None, echo: bool = False):
    """
    Initialize database with both Kosmos and Crucible models.

    Args:
        database_url: Database URL (defaults to config value)
        echo: Whether to echo SQL statements
    """
    if database_url is None:
        config = get_config()
        database_url = config.database_url

    # Initialize Kosmos database (creates Kosmos tables)
    kosmos_init_database(database_url=database_url, echo=echo)

    # Create Crucible tables (they share the same engine)
    # Get the engine from Kosmos
    from kosmos.db import _engine
    if _engine is not None:
        CrucibleBase.metadata.create_all(bind=_engine)
        logger.info("Crucible database models initialized")
    else:
        logger.warning("Kosmos engine not initialized, Crucible tables may not be created")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session (reuses Kosmos session management).

    Yields:
        SQLAlchemy session
    """
    with kosmos_get_session() as session:
        yield session


def init_from_config():
    """
    Initialize database from Crucible configuration.

    This will initialize both Kosmos and Crucible models.
    """
    config = get_config()
    init_database(database_url=config.database_url)

