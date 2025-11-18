"""
Unit tests for database models and operations.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from kosmos.db.models import Base, Hypothesis, Experiment, HypothesisStatus, ExperimentStatus
from kosmos.db import operations
from datetime import datetime


@pytest.fixture
def test_db():
    """Create test database in memory."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


class TestHypothesisCRUD:
    """Test hypothesis CRUD operations."""

    def test_create_hypothesis(self, test_db):
        """Test creating a hypothesis."""
        hypothesis = operations.create_hypothesis(
            session=test_db,
            id="hyp-1",
            research_question="Does X affect Y?",
            statement="X increases Y",
            rationale="Because of Z",
            domain="biology",
            novelty_score=0.8,
            testability_score=0.9,
            confidence_score=0.7
        )

        assert hypothesis.id == "hyp-1"
        assert hypothesis.statement == "X increases Y"
        assert hypothesis.status == HypothesisStatus.GENERATED
        assert hypothesis.novelty_score == 0.8

    def test_get_hypothesis(self, test_db):
        """Test retrieving a hypothesis."""
        # Create
        operations.create_hypothesis(
            session=test_db,
            id="hyp-2",
            research_question="Test question",
            statement="Test statement",
            rationale="Test rationale",
            domain="physics"
        )

        # Retrieve
        hypothesis = operations.get_hypothesis(test_db, "hyp-2")

        assert hypothesis is not None
        assert hypothesis.id == "hyp-2"
        assert hypothesis.domain == "physics"

    def test_list_hypotheses(self, test_db):
        """Test listing hypotheses."""
        # Create multiple
        for i in range(5):
            operations.create_hypothesis(
                session=test_db,
                id=f"hyp-{i}",
                research_question=f"Question {i}",
                statement=f"Statement {i}",
                rationale=f"Rationale {i}",
                domain="biology" if i % 2 == 0 else "physics"
            )

        # List all
        all_hyps = operations.list_hypotheses(test_db)
        assert len(all_hyps) == 5

        # Filter by domain
        bio_hyps = operations.list_hypotheses(test_db, domain="biology")
        assert len(bio_hyps) == 3

    def test_update_hypothesis_status(self, test_db):
        """Test updating hypothesis status."""
        # Create
        operations.create_hypothesis(
            session=test_db,
            id="hyp-3",
            research_question="Test",
            statement="Test",
            rationale="Test",
            domain="biology"
        )

        # Update status
        updated = operations.update_hypothesis_status(
            session=test_db,
            hypothesis_id="hyp-3",
            status=HypothesisStatus.TESTING
        )

        assert updated.status == HypothesisStatus.TESTING


class TestExperimentCRUD:
    """Test experiment CRUD operations."""

    def test_create_experiment(self, test_db):
        """Test creating an experiment."""
        # Create hypothesis first
        operations.create_hypothesis(
            session=test_db,
            id="hyp-10",
            research_question="Test",
            statement="Test",
            rationale="Test",
            domain="biology"
        )

        # Create experiment
        experiment = operations.create_experiment(
            session=test_db,
            id="exp-1",
            hypothesis_id="hyp-10",
            experiment_type="computational",
            description="Test experiment",
            protocol={"method": "t-test", "data": "dataset.csv"},
            domain="biology"
        )

        assert experiment.id == "exp-1"
        assert experiment.hypothesis_id == "hyp-10"
        assert experiment.status == ExperimentStatus.CREATED

    def test_update_experiment_status(self, test_db):
        """Test updating experiment status."""
        # Create hypothesis
        operations.create_hypothesis(
            session=test_db,
            id="hyp-11",
            research_question="Test",
            statement="Test",
            rationale="Test",
            domain="biology"
        )

        # Create experiment
        operations.create_experiment(
            session=test_db,
            id="exp-2",
            hypothesis_id="hyp-11",
            experiment_type="computational",
            description="Test",
            protocol={},
            domain="biology"
        )

        # Update to running
        updated = operations.update_experiment_status(
            session=test_db,
            experiment_id="exp-2",
            status=ExperimentStatus.RUNNING
        )

        assert updated.status == ExperimentStatus.RUNNING
        assert updated.started_at is not None

        # Update to completed
        updated = operations.update_experiment_status(
            session=test_db,
            experiment_id="exp-2",
            status=ExperimentStatus.COMPLETED,
            execution_time_seconds=30.5
        )

        assert updated.status == ExperimentStatus.COMPLETED
        assert updated.completed_at is not None
        assert updated.execution_time_seconds == 30.5


class TestResultCRUD:
    """Test result CRUD operations."""

    def test_create_result(self, test_db):
        """Test creating a result."""
        # Create hypothesis and experiment
        operations.create_hypothesis(
            session=test_db,
            id="hyp-20",
            research_question="Test",
            statement="Test",
            rationale="Test",
            domain="biology"
        )

        operations.create_experiment(
            session=test_db,
            id="exp-10",
            hypothesis_id="hyp-20",
            experiment_type="computational",
            description="Test",
            protocol={},
            domain="biology"
        )

        # Create result
        result = operations.create_result(
            session=test_db,
            id="res-1",
            experiment_id="exp-10",
            data={"mean": 5.2, "std": 1.1},
            statistical_tests={"t_test": {"p_value": 0.03}},
            interpretation="Significant result",
            supports_hypothesis=True,
            p_value=0.03
        )

        assert result.id == "res-1"
        assert result.experiment_id == "exp-10"
        assert result.supports_hypothesis is True
        assert result.p_value == 0.03

    def test_get_results_for_experiment(self, test_db):
        """Test retrieving results for an experiment."""
        # Setup
        operations.create_hypothesis(
            session=test_db,
            id="hyp-21",
            research_question="Test",
            statement="Test",
            rationale="Test",
            domain="biology"
        )

        operations.create_experiment(
            session=test_db,
            id="exp-11",
            hypothesis_id="hyp-21",
            experiment_type="computational",
            description="Test",
            protocol={},
            domain="biology"
        )

        # Create multiple results
        for i in range(3):
            operations.create_result(
                session=test_db,
                id=f"res-{i}",
                experiment_id="exp-11",
                data={"result": i}
            )

        # Retrieve
        results = operations.get_results_for_experiment(test_db, "exp-11")

        assert len(results) == 3
