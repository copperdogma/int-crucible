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
        
        # Force metadata sync: ensure SQLAlchemy table definitions match actual database schema
        # This is critical after migrations add new columns - SQLAlchemy metadata is cached
        # at import time and doesn't automatically reflect migration changes
        try:
            from sqlalchemy import inspect, Table
            from crucible.db.models import Run
            
            inspector = inspect(_engine)
            
            # Check if chat_session_id exists in database but not in model metadata
            db_columns = {col['name'] for col in inspector.get_columns('crucible_runs')}
            model_columns = set(Run.__table__.columns.keys())
            
            missing_columns = db_columns - model_columns
            
            if missing_columns:
                logger.info(f"Found columns in database but not in model metadata: {missing_columns}")
                logger.info("Refreshing table metadata to sync with database schema...")
                
                # The issue: SQLAlchemy's Run.__table__ was built at import time before migrations
                # Solution: Use Table reflection with extend_existing=True to update the table
                table_name = Run.__table__.name
                
                # Remove the old table from metadata
                old_table = CrucibleBase.metadata.tables.pop(table_name, None)
                
                # Reflect the table from the database (this gets the actual schema including new columns)
                reflected_table = Table(
                    table_name,
                    CrucibleBase.metadata,
                    autoload_with=_engine,
                    extend_existing=False  # Create new table object
                )
                
                # Update the Run model's table to use the reflected version
                # This ensures all columns from the database are included
                Run.__table__ = reflected_table
                
                # Verify the column is now present
                if 'chat_session_id' in Run.__table__.columns:
                    logger.info(f"Successfully refreshed {table_name} metadata. Added columns: {missing_columns}")
                else:
                    logger.warning(f"Reflected table but chat_session_id still missing. This may cause issues.")
            else:
                logger.debug("Table metadata is in sync with database")
                
        except Exception as e:
            logger.warning(f"Could not sync metadata with database schema: {e}")
            logger.warning("This may cause issues with recently added columns. The column exists in the database but SQLAlchemy may not see it.")
            import traceback
            logger.debug(traceback.format_exc())
            # Don't fail initialization - the column exists, we just need to work around it
        
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

