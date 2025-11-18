"""
Integration test configuration.

Uses file-based SQLite database to avoid in-memory database threading issues.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crucible.db.models import Base as CrucibleBase


@pytest.fixture
def integration_db_session():
    """
    Create a file-based SQLite database session for integration testing.
    
    Uses a temporary file to avoid SQLite in-memory database threading issues
    with FastAPI TestClient.
    """
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        CrucibleBase.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            yield session
        finally:
            session.close()
            engine.dispose()
    finally:
        # Clean up temporary database file
        if os.path.exists(db_path):
            os.unlink(db_path)

