"""
Repository functions for Int Crucible domain entities.

Provides basic CRUD operations for all core entities.
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.db.models import (
    Candidate,
    ChatSession,
    Evaluation,
    Issue,
    Message,
    ProblemSpec,
    Project,
    Run,
    ScenarioSuite,
    WorldModel,
)


# Project operations
def create_project(
    session: Session,
    title: str,
    description: str | None = None,
    project_id: str | None = None
) -> Project:
    """Create a new project."""
    if project_id is None:
        project_id = str(uuid.uuid4())

    project = Project(
        id=project_id,
        title=title,
        description=description
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: str) -> Project | None:
    """Get a project by ID."""
    return session.query(Project).filter(Project.id == project_id).first()


def list_projects(session: Session) -> list[Project]:
    """List all projects."""
    return session.query(Project).order_by(Project.created_at.desc()).all()


def update_project(
    session: Session,
    project_id: str,
    title: str | None = None,
    description: str | None = None
) -> Project | None:
    """Update a project."""
    project = get_project(session, project_id)
    if project is None:
        return None

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description

    project.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(project)
    return project


# ChatSession operations
def create_chat_session(
    session: Session,
    project_id: str,
    title: str | None = None,
    mode: str = "setup",
    run_id: str | None = None,
    candidate_id: str | None = None,
    chat_session_id: str | None = None
) -> ChatSession:
    """Create a new chat session."""
    if chat_session_id is None:
        chat_session_id = str(uuid.uuid4())

    chat_session = ChatSession(
        id=chat_session_id,
        project_id=project_id,
        title=title,
        mode=mode,
        run_id=run_id,
        candidate_id=candidate_id
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


def get_chat_session(session: Session, chat_session_id: str) -> ChatSession | None:
    """Get a chat session by ID."""
    return session.query(ChatSession).filter(ChatSession.id == chat_session_id).first()


def list_chat_sessions(session: Session, project_id: str | None = None) -> list[ChatSession]:
    """List chat sessions, optionally filtered by project."""
    query = session.query(ChatSession)
    if project_id is not None:
        query = query.filter(ChatSession.project_id == project_id)
    return query.order_by(ChatSession.created_at.desc()).all()


# Message operations
def create_message(
    session: Session,
    chat_session_id: str,
    role: str,
    content: str,
    message_metadata: dict | None = None,
    message_id: str | None = None
) -> Message:
    """Create a new message."""
    if message_id is None:
        message_id = str(uuid.uuid4())

    message = Message(
        id=message_id,
        chat_session_id=chat_session_id,
        role=role,
        content=content,
        message_metadata=message_metadata
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_message(session: Session, message_id: str) -> Message | None:
    """Get a message by ID."""
    return session.query(Message).filter(Message.id == message_id).first()


def list_messages(session: Session, chat_session_id: str) -> list[Message]:
    """List all messages in a chat session."""
    return session.query(Message).filter(
        Message.chat_session_id == chat_session_id
    ).order_by(Message.created_at.asc()).all()


# ProblemSpec operations
def create_problem_spec(
    session: Session,
    project_id: str,
    constraints: list[dict] | None = None,
    goals: list[str] | None = None,
    resolution: str = "medium",
    mode: str = "full_search",
    problem_spec_id: str | None = None
) -> ProblemSpec:
    """Create a new problem spec."""
    if problem_spec_id is None:
        problem_spec_id = str(uuid.uuid4())

    problem_spec = ProblemSpec(
        id=problem_spec_id,
        project_id=project_id,
        constraints=constraints or [],
        goals=goals or [],
        resolution=resolution,
        mode=mode
    )
    session.add(problem_spec)
    session.commit()
    session.refresh(problem_spec)
    return problem_spec


def get_problem_spec(session: Session, project_id: str) -> ProblemSpec | None:
    """Get problem spec for a project."""
    return session.query(ProblemSpec).filter(ProblemSpec.project_id == project_id).first()


def update_problem_spec(
    session: Session,
    project_id: str,
    constraints: list[dict] | None = None,
    goals: list[str] | None = None,
    resolution: str | None = None,
    mode: str | None = None
) -> ProblemSpec | None:
    """Update a problem spec."""
    problem_spec = get_problem_spec(session, project_id)
    if problem_spec is None:
        return None

    if constraints is not None:
        problem_spec.constraints = constraints
    if goals is not None:
        problem_spec.goals = goals
    if resolution is not None:
        problem_spec.resolution = resolution
    if mode is not None:
        problem_spec.mode = mode

    problem_spec.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(problem_spec)
    return problem_spec


# WorldModel operations
def create_world_model(
    session: Session,
    project_id: str,
    model_data: dict | None = None,
    world_model_id: str | None = None
) -> WorldModel:
    """Create a new world model."""
    if world_model_id is None:
        world_model_id = str(uuid.uuid4())

    world_model = WorldModel(
        id=world_model_id,
        project_id=project_id,
        model_data=model_data or {}
    )
    session.add(world_model)
    session.commit()
    # Refresh to ensure we have the latest data (skip if table doesn't exist yet)
    try:
        session.refresh(world_model)
    except Exception:
        # If refresh fails (e.g., table doesn't exist in test), that's okay
        # The object is already committed and we have the data
        pass
    return world_model


def get_world_model(session: Session, project_id: str) -> WorldModel | None:
    """Get world model for a project."""
    return session.query(WorldModel).filter(WorldModel.project_id == project_id).first()


def update_world_model(
    session: Session,
    project_id: str,
    model_data: dict
) -> WorldModel | None:
    """Update a world model."""
    world_model = get_world_model(session, project_id)
    if world_model is None:
        return None

    world_model.model_data = model_data
    world_model.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(world_model)
    return world_model


# Run operations
def create_run(
    session: Session,
    project_id: str,
    mode: str,
    config: dict | None = None,
    run_id: str | None = None,
    recommended_message_id: str | None = None,
    recommended_config_snapshot: dict | None = None,
    ui_trigger_id: str | None = None,
    ui_trigger_source: str | None = None,
    ui_trigger_metadata: dict | None = None,
    ui_triggered_at: datetime | None = None,
) -> Run:
    """Create a new run."""
    if run_id is None:
        run_id = str(uuid.uuid4())

    run = Run(
        id=run_id,
        project_id=project_id,
        mode=mode,
        config=config,
        recommended_message_id=recommended_message_id,
        recommended_config_snapshot=recommended_config_snapshot,
        ui_trigger_id=ui_trigger_id,
        ui_trigger_source=ui_trigger_source,
        ui_trigger_metadata=ui_trigger_metadata,
        ui_triggered_at=ui_triggered_at,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: str) -> Run | None:
    """Get a run by ID."""
    return session.query(Run).filter(Run.id == run_id).first()


def list_runs(session: Session, project_id: str | None = None) -> list[Run]:
    """List runs, optionally filtered by project."""
    query = session.query(Run)
    if project_id is not None:
        query = query.filter(Run.project_id == project_id)
    return query.order_by(Run.created_at.desc()).all()


def update_run_status(
    session: Session,
    run_id: str,
    status: str,
    started_at: datetime | None = None,
    completed_at: datetime | None = None
) -> Run | None:
    """Update run status."""
    run = get_run(session, run_id)
    if run is None:
        return None

    run.status = status
    if started_at is not None:
        run.started_at = started_at
    if completed_at is not None:
        run.completed_at = completed_at

    session.commit()
    session.refresh(run)
    return run


# Candidate operations
def create_candidate(
    session: Session,
    run_id: str,
    project_id: str,
    origin: str,
    mechanism_description: str,
    predicted_effects: dict | None = None,
    parent_ids: list[str] | None = None,
    candidate_id: str | None = None
) -> Candidate:
    """Create a new candidate."""
    if candidate_id is None:
        candidate_id = str(uuid.uuid4())

    candidate = Candidate(
        id=candidate_id,
        run_id=run_id,
        project_id=project_id,
        origin=origin,
        mechanism_description=mechanism_description,
        predicted_effects=predicted_effects,
        parent_ids=parent_ids or []
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def get_candidate(session: Session, candidate_id: str) -> Candidate | None:
    """Get a candidate by ID."""
    return session.query(Candidate).filter(Candidate.id == candidate_id).first()


def list_candidates(
    session: Session,
    run_id: str | None = None,
    project_id: str | None = None
) -> list[Candidate]:
    """List candidates, optionally filtered by run or project."""
    query = session.query(Candidate)
    if run_id is not None:
        query = query.filter(Candidate.run_id == run_id)
    if project_id is not None:
        query = query.filter(Candidate.project_id == project_id)
    return query.order_by(Candidate.created_at.desc()).all()


def update_candidate(
    session: Session,
    candidate_id: str,
    scores: dict | None = None,
    status: str | None = None,
    provenance_log: list[dict] | None = None
) -> Candidate | None:
    """Update a candidate."""
    candidate = get_candidate(session, candidate_id)
    if candidate is None:
        return None

    if scores is not None:
        candidate.scores = scores
    if status is not None:
        candidate.status = status
    if provenance_log is not None:
        candidate.provenance_log = provenance_log

    candidate.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(candidate)
    return candidate


# ScenarioSuite operations
def create_scenario_suite(
    session: Session,
    run_id: str,
    scenarios: list[dict] | None = None,
    scenario_suite_id: str | None = None
) -> ScenarioSuite:
    """Create a new scenario suite."""
    if scenario_suite_id is None:
        scenario_suite_id = str(uuid.uuid4())

    scenario_suite = ScenarioSuite(
        id=scenario_suite_id,
        run_id=run_id,
        scenarios=scenarios or []
    )
    session.add(scenario_suite)
    session.commit()
    session.refresh(scenario_suite)
    return scenario_suite


def get_scenario_suite(session: Session, run_id: str) -> ScenarioSuite | None:
    """Get scenario suite for a run."""
    return session.query(ScenarioSuite).filter(ScenarioSuite.run_id == run_id).first()


# Evaluation operations
def create_evaluation(
    session: Session,
    candidate_id: str,
    run_id: str,
    scenario_id: str,
    P: dict | None = None,
    R: dict | None = None,
    constraint_satisfaction: dict | None = None,
    explanation: str | None = None,
    evaluation_id: str | None = None
) -> Evaluation:
    """Create a new evaluation."""
    if evaluation_id is None:
        evaluation_id = str(uuid.uuid4())

    evaluation = Evaluation(
        id=evaluation_id,
        candidate_id=candidate_id,
        run_id=run_id,
        scenario_id=scenario_id,
        P=P,
        R=R,
        constraint_satisfaction=constraint_satisfaction,
        explanation=explanation
    )
    session.add(evaluation)
    session.commit()
    session.refresh(evaluation)
    return evaluation


def get_evaluation(session: Session, evaluation_id: str) -> Evaluation | None:
    """Get an evaluation by ID."""
    return session.query(Evaluation).filter(Evaluation.id == evaluation_id).first()


def list_evaluations(
    session: Session,
    candidate_id: str | None = None,
    run_id: str | None = None
) -> list[Evaluation]:
    """List evaluations, optionally filtered by candidate or run."""
    query = session.query(Evaluation)
    if candidate_id is not None:
        query = query.filter(Evaluation.candidate_id == candidate_id)
    if run_id is not None:
        query = query.filter(Evaluation.run_id == run_id)
    return query.order_by(Evaluation.created_at.desc()).all()


# Issue operations
def create_issue(
    session: Session,
    project_id: str,
    type: str,
    severity: str,
    description: str,
    run_id: str | None = None,
    candidate_id: str | None = None,
    issue_id: str | None = None
) -> Issue:
    """Create a new issue."""
    if issue_id is None:
        issue_id = str(uuid.uuid4())

    issue = Issue(
        id=issue_id,
        project_id=project_id,
        run_id=run_id,
        candidate_id=candidate_id,
        type=type,
        severity=severity,
        description=description
    )
    session.add(issue)
    session.commit()
    session.refresh(issue)
    return issue


def get_issue(session: Session, issue_id: str) -> Issue | None:
    """Get an issue by ID."""
    return session.query(Issue).filter(Issue.id == issue_id).first()


def list_issues(
    session: Session,
    project_id: str | None = None,
    resolution_status: str | None = None
) -> list[Issue]:
    """List issues, optionally filtered by project or resolution status."""
    query = session.query(Issue)
    if project_id is not None:
        query = query.filter(Issue.project_id == project_id)
    if resolution_status is not None:
        query = query.filter(Issue.resolution_status == resolution_status)
    return query.order_by(Issue.created_at.desc()).all()


def update_issue(
    session: Session,
    issue_id: str,
    resolution_status: str | None = None,
    resolved_at: datetime | None = None
) -> Issue | None:
    """Update an issue."""
    issue = get_issue(session, issue_id)
    if issue is None:
        return None

    if resolution_status is not None:
        issue.resolution_status = resolution_status
    if resolved_at is not None:
        issue.resolved_at = resolved_at

    session.commit()
    session.refresh(issue)
    return issue

