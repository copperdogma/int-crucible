"""
Integration tests for multi-chat and run history workflows.

Tests the complete multi-chat workflow:
1. Create project with multiple chat sessions
2. Create runs from different chats
3. Verify runs are linked to chat sessions
4. Test filtering runs by chat session
5. Test creating analysis chats from runs
6. Test switching between chats
"""

import pytest
from datetime import datetime

from crucible.db.repositories import (
    create_project,
    create_chat_session,
    create_message,
    create_run,
    list_chat_sessions,
    list_runs,
    get_chat_session,
    get_run,
    update_chat_session,
)
from crucible.db.models import ChatSessionMode, RunMode, RunStatus, MessageRole
from crucible.models.run_contracts import RunTriggerSource
from crucible.api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(integration_db_session):
    """Create a test client for the FastAPI app."""
    from crucible.api.main import get_db
    
    def override_get_db():
        yield integration_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(integration_db_session):
    """Create a sample project for testing."""
    project = create_project(
        integration_db_session,
        title="Test Project: Multi-Chat Workflow",
        description="Testing multiple chats and runs"
    )
    return project


def test_create_multiple_chat_sessions(integration_db_session, sample_project):
    """Test creating multiple chat sessions for a project."""
    # Create setup chat
    setup_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Setup Chat",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Create analysis chat
    analysis_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Analysis Chat",
        mode=ChatSessionMode.ANALYSIS.value
    )
    
    # Create what-if chat
    whatif_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="What-if: Alternative Constraint",
        mode=ChatSessionMode.SETUP.value
    )
    
    # List all chats for project
    chats = list_chat_sessions(integration_db_session, project_id=sample_project.id)
    
    assert len(chats) == 3
    assert setup_chat.id in [c.id for c in chats]
    assert analysis_chat.id in [c.id for c in chats]
    assert whatif_chat.id in [c.id for c in chats]
    
    # Verify chat properties
    assert setup_chat.mode == ChatSessionMode.SETUP
    assert analysis_chat.mode == ChatSessionMode.ANALYSIS
    assert setup_chat.title == "Setup Chat"
    assert analysis_chat.title == "Analysis Chat"


def test_create_runs_from_different_chats(integration_db_session, sample_project):
    """Test creating runs from different chat sessions."""
    # Create two chat sessions
    chat1 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 1",
        mode=ChatSessionMode.SETUP.value
    )
    
    chat2 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 2",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Create runs from different chats
    run1 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        config={"num_candidates": 5},
        chat_session_id=chat1.id,
        ui_trigger_id="test-trigger-1",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    run2 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.EVAL_ONLY.value,
        config={"num_candidates": 3},
        chat_session_id=chat2.id,
        ui_trigger_id="test-trigger-2",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # Verify runs are linked to correct chats
    assert run1.chat_session_id == chat1.id
    assert run2.chat_session_id == chat2.id
    assert run1.project_id == sample_project.id
    assert run2.project_id == sample_project.id


def test_filter_runs_by_chat_session(integration_db_session, sample_project):
    """Test filtering runs by chat session."""
    # Create chats
    chat1 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 1",
        mode=ChatSessionMode.SETUP.value
    )
    
    chat2 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 2",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Create runs
    run1 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=chat1.id,
        ui_trigger_id="test-1",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    run2 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=chat1.id,
        ui_trigger_id="test-2",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    run3 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=chat2.id,
        ui_trigger_id="test-3",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # Filter runs by chat1
    chat1_runs = list_runs(
        integration_db_session,
        project_id=sample_project.id,
        chat_session_id=chat1.id
    )
    
    assert len(chat1_runs) == 2
    assert run1.id in [r.id for r in chat1_runs]
    assert run2.id in [r.id for r in chat1_runs]
    assert run3.id not in [r.id for r in chat1_runs]
    
    # Filter runs by chat2
    chat2_runs = list_runs(
        integration_db_session,
        project_id=sample_project.id,
        chat_session_id=chat2.id
    )
    
    assert len(chat2_runs) == 1
    assert run3.id in [r.id for r in chat2_runs]


def test_create_analysis_chat_from_run(integration_db_session, sample_project):
    """Test creating an analysis chat session from a run."""
    # Create setup chat and run
    setup_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Setup Chat",
        mode=ChatSessionMode.SETUP.value
    )
    
    run = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=setup_chat.id,
        ui_trigger_id="test-trigger",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # Create analysis chat with run context
    analysis_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title=f"Analysis: Run {run.id[:8]}",
        mode=ChatSessionMode.ANALYSIS.value,
        run_id=run.id
    )
    
    # Verify analysis chat properties
    assert analysis_chat.run_id == run.id
    assert analysis_chat.mode == ChatSessionMode.ANALYSIS
    assert analysis_chat.project_id == sample_project.id
    assert "Analysis" in analysis_chat.title


def test_update_chat_session_title(integration_db_session, sample_project):
    """Test updating a chat session's title."""
    chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Original Title",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Update title
    updated_chat = update_chat_session(
        integration_db_session,
        chat_session_id=chat.id,
        title="Updated Title"
    )
    
    assert updated_chat is not None
    assert updated_chat.title == "Updated Title"
    assert updated_chat.id == chat.id
    
    # Verify in database
    retrieved_chat = get_chat_session(integration_db_session, chat.id)
    assert retrieved_chat.title == "Updated Title"


def test_api_list_chat_sessions(test_client, integration_db_session, sample_project):
    """Test API endpoint for listing chat sessions."""
    # Create multiple chats
    chat1 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 1",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Use API to list chats
    response = test_client.get(f"/projects/{sample_project.id}/chat-sessions")
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) >= 1
    assert any(c["id"] == chat1.id for c in chats)


def test_api_create_run_with_chat_session(test_client, integration_db_session, sample_project):
    """Test API endpoint for creating run with chat session."""
    # Create chat
    chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Test Chat",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Create run via API
    response = test_client.post(
        "/runs",
        json={
            "project_id": sample_project.id,
            "mode": "full_search",
            "config": {"num_candidates": 5},
            "chat_session_id": chat.id,
            "ui_trigger_id": "test-api-trigger",
            "ui_trigger_source": RunTriggerSource.INTEGRATION_TEST.value
        }
    )
    
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["project_id"] == sample_project.id
    assert run_data["chat_session_id"] == chat.id
    assert run_data["mode"] == "full_search"


def test_api_filter_runs_by_chat(test_client, integration_db_session, sample_project):
    """Test API endpoint for filtering runs by chat session."""
    # Create chats and runs
    chat1 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 1",
        mode=ChatSessionMode.SETUP.value
    )
    
    chat2 = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Chat 2",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Create runs
    run1 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=chat1.id,
        ui_trigger_id="test-1",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    run2 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=chat2.id,
        ui_trigger_id="test-2",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # Filter by chat1
    response = test_client.get(
        f"/projects/{sample_project.id}/runs",
        params={"chat_session_id": chat1.id}
    )
    
    assert response.status_code == 200
    runs = response.json()
    run_ids = [r["id"] for r in runs]
    assert run1.id in run_ids
    assert run2.id not in run_ids


def test_api_update_chat_session(test_client, integration_db_session, sample_project):
    """Test API endpoint for updating chat session."""
    # Create chat
    chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Original Title",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Update via API
    response = test_client.put(
        f"/chat-sessions/{chat.id}",
        json={
            "title": "Updated Title",
            "mode": "analysis"
        }
    )
    
    assert response.status_code == 200
    updated_chat = response.json()
    assert updated_chat["title"] == "Updated Title"
    assert updated_chat["mode"] == "analysis"


def test_multi_chat_workflow_integration(integration_db_session, sample_project):
    """Test complete multi-chat workflow: setup → run → analysis → what-if."""
    # 1. Create setup chat
    setup_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="Setup Chat",
        mode=ChatSessionMode.SETUP.value
    )
    
    # Add some messages to setup chat
    create_message(
        integration_db_session,
        chat_session_id=setup_chat.id,
        role=MessageRole.USER.value,
        content="I need to improve API performance"
    )
    
    # 2. Create run from setup chat
    run1 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=setup_chat.id,
        ui_trigger_id="workflow-trigger-1",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # 3. Create analysis chat for run1
    analysis_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title=f"Analysis: Run {run1.id[:8]}",
        mode=ChatSessionMode.ANALYSIS.value,
        run_id=run1.id
    )
    
    # 4. Create what-if chat
    whatif_chat = create_chat_session(
        integration_db_session,
        project_id=sample_project.id,
        title="What-if: Alternative Constraint",
        mode=ChatSessionMode.SETUP.value
    )
    
    # 5. Create another run from what-if chat
    run2 = create_run(
        integration_db_session,
        project_id=sample_project.id,
        mode=RunMode.FULL_SEARCH.value,
        chat_session_id=whatif_chat.id,
        ui_trigger_id="workflow-trigger-2",
        ui_trigger_source=RunTriggerSource.INTEGRATION_TEST.value
    )
    
    # Verify all relationships
    all_chats = list_chat_sessions(integration_db_session, project_id=sample_project.id)
    assert len(all_chats) == 3
    
    all_runs = list_runs(integration_db_session, project_id=sample_project.id)
    assert len(all_runs) == 2
    
    # Verify run1 is linked to setup_chat
    assert run1.chat_session_id == setup_chat.id
    
    # Verify run2 is linked to whatif_chat
    assert run2.chat_session_id == whatif_chat.id
    
    # Verify analysis_chat has run context
    assert analysis_chat.run_id == run1.id
    
    # Filter runs by setup_chat
    setup_runs = list_runs(
        integration_db_session,
        project_id=sample_project.id,
        chat_session_id=setup_chat.id
    )
    assert len(setup_runs) == 1
    assert setup_runs[0].id == run1.id
    
    # Filter runs by whatif_chat
    whatif_runs = list_runs(
        integration_db_session,
        project_id=sample_project.id,
        chat_session_id=whatif_chat.id
    )
    assert len(whatif_runs) == 1
    assert whatif_runs[0].id == run2.id

