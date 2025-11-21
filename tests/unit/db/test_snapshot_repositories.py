"""
Unit tests for snapshot repository functions.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

from crucible.db.repositories import (
    create_snapshot,
    get_snapshot,
    get_snapshot_by_name,
    list_snapshots,
    update_snapshot,
    delete_snapshot,
)
from crucible.db.models import Snapshot


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def sample_snapshot():
    """Sample Snapshot object."""
    snapshot = Snapshot(
        id="snapshot-123",
        name="Test Snapshot",
        description="Test description",
        tags=["test", "automated"],
        project_id="project-123",
        run_id="run-123",
        snapshot_data={"version": "1.0", "problem_spec": {}},
        reference_metrics={"candidate_count": 5},
        invariants=[{"type": "min_candidates", "value": 3}],
        version="1.0"
    )
    return snapshot


class TestCreateSnapshot:
    """Tests for create_snapshot function."""

    def test_create_snapshot_basic(self, mock_session):
        """Test basic snapshot creation."""
        snapshot = create_snapshot(
            session=mock_session,
            project_id="project-123",
            name="Test Snapshot",
            description="Test description",
            tags=["test"],
            snapshot_id="snapshot-123"
        )
        
        assert snapshot.id == "snapshot-123"
        assert snapshot.name == "Test Snapshot"
        assert snapshot.project_id == "project-123"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_snapshot_auto_id(self, mock_session):
        """Test snapshot creation with auto-generated ID."""
        with patch('crucible.db.repositories.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="auto-id-123")
            
            snapshot = create_snapshot(
                session=mock_session,
                project_id="project-123",
                name="Test Snapshot"
            )
            
            assert snapshot.id == "auto-id-123"
            mock_session.add.assert_called_once()


class TestGetSnapshot:
    """Tests for get_snapshot function."""

    def test_get_snapshot_exists(self, mock_session, sample_snapshot):
        """Test getting existing snapshot."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_snapshot
        mock_session.query.return_value = mock_query
        
        result = get_snapshot(mock_session, "snapshot-123")
        
        assert result == sample_snapshot
        assert result.id == "snapshot-123"

    def test_get_snapshot_not_found(self, mock_session):
        """Test getting non-existent snapshot."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query
        
        result = get_snapshot(mock_session, "non-existent")
        
        assert result is None


class TestListSnapshots:
    """Tests for list_snapshots function."""

    def test_list_snapshots_all(self, mock_session, sample_snapshot):
        """Test listing all snapshots."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_snapshot]
        mock_session.query.return_value = mock_query
        
        result = list_snapshots(mock_session)
        
        assert len(result) == 1
        assert result[0] == sample_snapshot

    def test_list_snapshots_filter_by_project(self, mock_session, sample_snapshot):
        """Test listing snapshots filtered by project."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.order_by.return_value = mock_filter
        mock_filter.all.return_value = [sample_snapshot]
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        
        result = list_snapshots(mock_session, project_id="project-123")
        
        assert len(result) == 1
        assert result[0].project_id == "project-123"

    def test_list_snapshots_filter_by_tags(self, mock_session, sample_snapshot):
        """Test listing snapshots filtered by tags."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.order_by.return_value = mock_filter
        mock_filter.all.return_value = [sample_snapshot]
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        
        result = list_snapshots(mock_session, tags=["test"])
        
        assert len(result) == 1


class TestUpdateSnapshot:
    """Tests for update_snapshot function."""

    def test_update_snapshot(self, mock_session, sample_snapshot):
        """Test updating snapshot."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_snapshot
        mock_session.query.return_value = mock_query
        
        result = update_snapshot(
            mock_session,
            "snapshot-123",
            description="Updated description",
            tags=["updated", "tags"],
            invariants=[{"type": "min_candidates", "value": 5}]
        )
        
        assert result is not None
        assert result.description == "Updated description"
        assert result.tags == ["updated", "tags"]
        mock_session.commit.assert_called_once()


class TestDeleteSnapshot:
    """Tests for delete_snapshot function."""

    def test_delete_snapshot_exists(self, mock_session, sample_snapshot):
        """Test deleting existing snapshot."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_snapshot
        mock_session.query.return_value = mock_query
        
        result = delete_snapshot(mock_session, "snapshot-123")
        
        assert result is True
        mock_session.delete.assert_called_once_with(sample_snapshot)
        mock_session.commit.assert_called_once()

    def test_delete_snapshot_not_found(self, mock_session):
        """Test deleting non-existent snapshot."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query
        
        result = delete_snapshot(mock_session, "non-existent")
        
        assert result is False
        mock_session.delete.assert_not_called()

