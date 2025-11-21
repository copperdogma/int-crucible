"""
Database models for Int Crucible.

These models extend the Kosmos Base to add Crucible-specific domain entities:
- Project, ChatSession, Message, ProblemSpec, WorldModel
- Run, Candidate, ScenarioSuite, Evaluation, Issue
"""

import enum
from datetime import datetime

# Import Kosmos Base to ensure compatibility
from kosmos.db.models import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from crucible.models.run_contracts import RunTriggerSource


# Enums
class ChatSessionMode(str, enum.Enum):
    """Chat session mode."""
    SETUP = "setup"
    ANALYSIS = "analysis"


class MessageRole(str, enum.Enum):
    """Message role in chat."""
    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"


class ResolutionLevel(str, enum.Enum):
    """Problem resolution level."""
    COARSE = "coarse"
    MEDIUM = "medium"
    FINE = "fine"


class RunMode(str, enum.Enum):
    """Run execution mode."""
    FULL_SEARCH = "full_search"
    EVAL_ONLY = "eval_only"
    SEEDED = "seeded"


class RunStatus(str, enum.Enum):
    """Run execution status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CandidateOrigin(str, enum.Enum):
    """Candidate origin."""
    USER = "user"
    SYSTEM = "system"


class CandidateStatus(str, enum.Enum):
    """Candidate status."""
    NEW = "new"
    UNDER_TEST = "under_test"
    PROMISING = "promising"
    WEAK = "weak"
    REJECTED = "rejected"


class IssueType(str, enum.Enum):
    """Issue type."""
    MODEL = "model"
    CONSTRAINT = "constraint"
    EVALUATOR = "evaluator"
    SCENARIO = "scenario"


class IssueSeverity(str, enum.Enum):
    """Issue severity."""
    MINOR = "minor"
    IMPORTANT = "important"
    CATASTROPHIC = "catastrophic"


class IssueResolutionStatus(str, enum.Enum):
    """Issue resolution status."""
    OPEN = "open"
    RESOLVED = "resolved"
    INVALIDATED = "invalidated"


# Models
class Project(Base):
    """
    Project model.

    Top-level container for a problem domain and all related work.
    """
    __tablename__ = "crucible_projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")
    problem_spec = relationship("ProblemSpec", back_populates="project", uselist=False, cascade="all, delete-orphan")
    world_model = relationship("WorldModel", back_populates="project", uselist=False, cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.id}: {self.title[:50]}>"


class ChatSession(Base):
    """
    Chat session model.

    A conversation thread within a project.
    """
    __tablename__ = "crucible_chat_sessions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False)
    title = Column(String, nullable=True)
    mode = Column(SQLEnum(ChatSessionMode), default=ChatSessionMode.SETUP)

    # Optional context links
    run_id = Column(String, nullable=True)  # For analysis chats focused on a run
    candidate_id = Column(String, nullable=True)  # For analysis chats focused on a candidate

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<ChatSession {self.id} project={self.project_id}>"


class Message(Base):
    """
    Message model.

    Individual message in a chat session.
    """
    __tablename__ = "crucible_messages"

    id = Column(String, primary_key=True)
    chat_session_id = Column(String, ForeignKey("crucible_chat_sessions.id"), nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Additional metadata (agent name, etc.)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id} role={self.role}>"


class ProblemSpec(Base):
    """
    Problem specification model.

    Structured problem specification with constraints, goals, and configuration.
    """
    __tablename__ = "crucible_problem_specs"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False, unique=True)

    # Constraints: JSON array of {name, description, weight (0-100)}
    constraints = Column(JSON, nullable=False, default=list)

    # Goals: JSON array of goal descriptions
    goals = Column(JSON, nullable=False, default=list)

    # Resolution level
    resolution = Column(SQLEnum(ResolutionLevel), default=ResolutionLevel.MEDIUM)

    # Execution mode
    mode = Column(SQLEnum(RunMode), default=RunMode.FULL_SEARCH)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="problem_spec")

    def __repr__(self):
        return f"<ProblemSpec {self.id} project={self.project_id}>"


class WorldModel(Base):
    """
    World model representation.

    Structured world model with actors, mechanisms, resources, etc.
    """
    __tablename__ = "crucible_world_models"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False, unique=True)

    # World model data: JSON structure with actors, mechanisms, resources, constraints, assumptions, simplifications
    model_data = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="world_model")

    def __repr__(self):
        return f"<WorldModel {self.id} project={self.project_id}>"


class Run(Base):
    """
    Run model.

    An execution of the full pipeline (ProblemSpec → WorldModeller → Designers → ScenarioGenerator → Evaluators → I-Ranker).
    """
    __tablename__ = "crucible_runs"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False)

    # Execution configuration
    mode = Column(SQLEnum(RunMode), nullable=False)
    config = Column(JSON, nullable=True)  # Budget, options, etc.
    recommended_message_id = Column(String, ForeignKey("crucible_messages.id"), nullable=True)
    recommended_config_snapshot = Column(JSON, nullable=True)
    ui_trigger_id = Column(String, nullable=True)
    ui_trigger_source = Column(SQLEnum(RunTriggerSource), nullable=True)
    ui_trigger_metadata = Column(JSON, nullable=True)
    ui_triggered_at = Column(DateTime, nullable=True)
    run_summary_message_id = Column(String, ForeignKey("crucible_messages.id"), nullable=True)

    # Status
    status = Column(SQLEnum(RunStatus), default=RunStatus.CREATED)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="runs")
    candidates = relationship("Candidate", back_populates="run", cascade="all, delete-orphan")
    scenario_suite = relationship("ScenarioSuite", back_populates="run", uselist=False, cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="run", cascade="all, delete-orphan")
    recommended_message = relationship(
        "Message",
        primaryjoin="Run.recommended_message_id==Message.id",
        viewonly=True,
    )
    run_summary_message = relationship(
        "Message",
        primaryjoin="Run.run_summary_message_id==Message.id",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Run {self.id} status={self.status}>"


class Candidate(Base):
    """
    Candidate model.

    A candidate solution generated or evaluated in a run.
    """
    __tablename__ = "crucible_candidates"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("crucible_runs.id"), nullable=False)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False)

    # Origin and description
    origin = Column(SQLEnum(CandidateOrigin), nullable=False)
    mechanism_description = Column(Text, nullable=False)
    predicted_effects = Column(JSON, nullable=True)

    # Scores: JSON with P, R, I, constraint_satisfaction
    scores = Column(JSON, nullable=True)

    # Provenance: JSON array of {type, timestamp, actor, reference_ids}
    provenance_log = Column(JSON, nullable=False, default=list)

    # Parent relationships: JSON array of candidate IDs
    parent_ids = Column(JSON, nullable=False, default=list)

    # Status
    status = Column(SQLEnum(CandidateStatus), default=CandidateStatus.NEW)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    run = relationship("Run", back_populates="candidates")
    project = relationship("Project")
    evaluations = relationship("Evaluation", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate {self.id} status={self.status}>"


class ScenarioSuite(Base):
    """
    Scenario suite model.

    Collection of scenarios for a run.
    """
    __tablename__ = "crucible_scenario_suites"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("crucible_runs.id"), nullable=False, unique=True)

    # Scenarios: JSON array of scenario objects
    scenarios = Column(JSON, nullable=False, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("Run", back_populates="scenario_suite")

    def __repr__(self):
        return f"<ScenarioSuite {self.id} run={self.run_id}>"


class Evaluation(Base):
    """
    Evaluation model.

    Evaluation of a candidate against a scenario.
    """
    __tablename__ = "crucible_evaluations"

    id = Column(String, primary_key=True)
    candidate_id = Column(String, ForeignKey("crucible_candidates.id"), nullable=False)
    run_id = Column(String, ForeignKey("crucible_runs.id"), nullable=False)

    # Scenario reference (string ID within the scenario suite)
    scenario_id = Column(String, nullable=False)

    # Scores
    P = Column(JSON, nullable=True)  # Prediction quality (can be structured)
    R = Column(JSON, nullable=True)  # Resource cost (can be structured)
    constraint_satisfaction = Column(JSON, nullable=True)  # Per-constraint scores

    # Explanation
    explanation = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="evaluations")
    run = relationship("Run", back_populates="evaluations")

    def __repr__(self):
        return f"<Evaluation {self.id} candidate={self.candidate_id} scenario={self.scenario_id}>"


class Issue(Base):
    """
    Issue model.

    User-flagged or system-detected issue.
    """
    __tablename__ = "crucible_issues"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("crucible_projects.id"), nullable=False)

    # Optional context links
    run_id = Column(String, nullable=True)
    candidate_id = Column(String, nullable=True)

    # Issue details
    type = Column(SQLEnum(IssueType), nullable=False)
    severity = Column(SQLEnum(IssueSeverity), nullable=False)
    description = Column(Text, nullable=False)
    resolution_status = Column(SQLEnum(IssueResolutionStatus), default=IssueResolutionStatus.OPEN)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="issues")

    def __repr__(self):
        return f"<Issue {self.id} type={self.type} severity={self.severity}>"

