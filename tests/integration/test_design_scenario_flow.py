"""
Integration tests for Design + Scenario Generation flow.

Tests the complete end-to-end workflow:
1. Create project with ProblemSpec and WorldModel
2. Create a Run
3. Generate candidates using DesignerAgent
4. Generate scenario suite using ScenarioGeneratorAgent
5. Verify database persistence and provenance tracking
6. Test API endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from crucible.db.repositories import (
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    get_run,
    get_problem_spec,
    get_world_model,
    list_candidates,
    get_scenario_suite,
    get_candidate,
)
from crucible.services.designer_service import DesignerService
from crucible.services.scenario_service import ScenarioService
from crucible.services.run_service import RunService
from crucible.api.main import app
from fastapi.testclient import TestClient
from crucible.db.models import RunStatus, CandidateStatus, CandidateOrigin
from kosmos.core.providers.base import LLMResponse, UsageStats


@pytest.fixture
def test_client(integration_db_session):
    """Create a test client for the FastAPI app."""
    from crucible.api.main import get_db
    
    # Override the get_db dependency to use our integration test session
    def override_get_db():
        yield integration_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_with_spec_and_model(integration_db_session):
    """Create a sample project with ProblemSpec and WorldModel."""
    project = create_project(
        integration_db_session,
        title="Test Project: API Performance",
        description="Improve API response times"
    )
    
    # Create ProblemSpec
    problem_spec = create_problem_spec(
        integration_db_session,
        project.id,
        constraints=[
            {"name": "Performance", "description": "Response time must be under 500ms", "weight": 80},
            {"name": "Budget", "description": "Limited budget", "weight": 60}
        ],
        goals=["Reduce response time to under 500ms", "Maintain system reliability"],
        resolution="medium",
        mode="full_search"
    )
    
    # Create WorldModel
    world_model = create_world_model(
        integration_db_session,
        project.id,
        model_data={
            "actors": [
                {
                    "id": "actor_1",
                    "name": "API Server",
                    "description": "Handles API requests",
                    "type": "system",
                    "capabilities": ["process_requests", "return_responses"],
                    "constraints": []
                }
            ],
            "mechanisms": [
                {
                    "id": "mechanism_1",
                    "name": "Request Processing",
                    "description": "Processes incoming API requests",
                    "type": "process",
                    "inputs": ["request"],
                    "outputs": ["response"],
                    "actors_involved": ["actor_1"],
                    "resources_required": []
                }
            ],
            "resources": [
                {
                    "id": "resource_1",
                    "name": "CPU",
                    "description": "Processing power",
                    "type": "energy",
                    "units": "cores",
                    "availability": "limited",
                    "constraints": []
                }
            ],
            "constraints": [
                {
                    "id": "constraint_1",
                    "name": "Response Time",
                    "description": "Must respond within 500ms",
                    "type": "hard",
                    "weight": 80,
                    "applies_to": ["actor_1", "mechanism_1"]
                }
            ],
            "assumptions": [
                {
                    "id": "assumption_1",
                    "description": "Current infrastructure can be optimized",
                    "rationale": "Based on ProblemSpec constraints",
                    "confidence": "medium",
                    "source": "agent"
                }
            ],
            "simplifications": [],
            "provenance": []
        }
    )
    
    return project, problem_spec, world_model


@pytest.fixture
def sample_run(integration_db_session, sample_project_with_spec_and_model):
    """Create a sample run for testing."""
    project, _, _ = sample_project_with_spec_and_model
    
    run = create_run(
        integration_db_session,
        project_id=project.id,
        mode="full_search",
        config={"budget": "medium", "depth": "medium"}
    )
    
    return run


@pytest.fixture
def mock_designer_llm_response():
    """Mock LLM response for DesignerAgent."""
    return {
        "candidates": [
            {
                "mechanism_description": "Implement caching layer to reduce database queries",
                "predicted_effects": {
                    "actors_affected": [
                        {
                            "actor_id": "actor_1",
                            "impact": "positive",
                            "description": "Reduces load on API server"
                        }
                    ],
                    "resources_impacted": [
                        {
                            "resource_id": "resource_1",
                            "change": "decrease",
                            "magnitude": "medium",
                            "description": "Reduces CPU usage"
                        }
                    ],
                    "mechanisms_modified": [
                        {
                            "mechanism_id": "mechanism_1",
                            "change_type": "enhanced",
                            "description": "Adds caching to request processing"
                        }
                    ]
                },
                "constraint_compliance": {
                    "constraint_1": 0.9
                },
                "reasoning": "Caching reduces response time by avoiding repeated database queries"
            },
            {
                "mechanism_description": "Optimize database queries with indexes and query optimization",
                "predicted_effects": {
                    "actors_affected": [
                        {
                            "actor_id": "actor_1",
                            "impact": "positive",
                            "description": "Faster query processing"
                        }
                    ],
                    "resources_impacted": [
                        {
                            "resource_id": "resource_1",
                            "change": "decrease",
                            "magnitude": "small",
                            "description": "Slightly reduces CPU usage"
                        }
                    ],
                    "mechanisms_modified": [
                        {
                            "mechanism_id": "mechanism_1",
                            "change_type": "enhanced",
                            "description": "Optimizes query execution"
                        }
                    ]
                },
                "constraint_compliance": {
                    "constraint_1": 0.7
                },
                "reasoning": "Database optimization directly improves response times"
            },
            {
                "mechanism_description": "Implement horizontal scaling with load balancer",
                "predicted_effects": {
                    "actors_affected": [
                        {
                            "actor_id": "actor_1",
                            "impact": "positive",
                            "description": "Distributes load across multiple servers"
                        }
                    ],
                    "resources_impacted": [
                        {
                            "resource_id": "resource_1",
                            "change": "increase",
                            "magnitude": "large",
                            "description": "Requires more CPU resources"
                        }
                    ],
                    "mechanisms_modified": [
                        {
                            "mechanism_id": "mechanism_1",
                            "change_type": "enhanced",
                            "description": "Adds load balancing to request processing"
                        }
                    ]
                },
                "constraint_compliance": {
                    "constraint_1": 0.8
                },
                "reasoning": "Scaling improves performance but increases resource costs"
            }
        ],
        "reasoning": "Generated three diverse approaches: caching (low cost), optimization (medium cost), and scaling (high cost)"
    }


@pytest.fixture
def mock_scenario_generator_llm_response():
    """Mock LLM response for ScenarioGeneratorAgent."""
    return {
        "scenarios": [
            {
                "id": "scenario_1",
                "name": "High Load Stress Test",
                "description": "Test system under high concurrent load",
                "type": "stress_test",
                "focus": {
                    "constraints": ["constraint_1"],
                    "assumptions": ["assumption_1"],
                    "actors": ["actor_1"],
                    "resources": ["resource_1"]
                },
                "initial_state": {
                    "actors": {
                        "actor_1": {
                            "state": "normal operation"
                        }
                    },
                    "resources": {
                        "resource_1": {
                            "quantity": 4,
                            "units": "cores"
                        }
                    },
                    "mechanisms": {
                        "mechanism_1": {
                            "state": "processing normally"
                        }
                    }
                },
                "events": [
                    {
                        "step": 1,
                        "description": "Simulate 1000 concurrent requests",
                        "actor": "actor_1",
                        "action": "process_requests"
                    },
                    {
                        "step": 2,
                        "description": "Measure response times",
                        "actor": "actor_1",
                        "action": "return_responses"
                    }
                ],
                "expected_outcomes": {
                    "success_criteria": [
                        "All requests complete within 500ms",
                        "No errors or timeouts"
                    ],
                    "failure_modes": [
                        "Response time exceeds 500ms",
                        "System becomes unresponsive"
                    ]
                },
                "weight": 0.9
            },
            {
                "id": "scenario_2",
                "name": "Resource Constraint Edge Case",
                "description": "Test with limited CPU resources",
                "type": "edge_case",
                "focus": {
                    "constraints": ["constraint_1"],
                    "assumptions": [],
                    "actors": ["actor_1"],
                    "resources": ["resource_1"]
                },
                "initial_state": {
                    "actors": {
                        "actor_1": {
                            "state": "normal operation"
                        }
                    },
                    "resources": {
                        "resource_1": {
                            "quantity": 1,
                            "units": "cores"
                        }
                    },
                    "mechanisms": {
                        "mechanism_1": {
                            "state": "processing normally"
                        }
                    }
                },
                "events": [
                    {
                        "step": 1,
                        "description": "Process requests with limited CPU",
                        "actor": "actor_1",
                        "action": "process_requests"
                    }
                ],
                "expected_outcomes": {
                    "success_criteria": [
                        "System maintains response time under 500ms"
                    ],
                    "failure_modes": [
                        "Response time degrades significantly"
                    ]
                },
                "weight": 0.7
            }
        ],
        "reasoning": "Generated scenarios that stress the high-weight performance constraint and test resource limitations"
    }


class TestDesignPhase:
    """Test the design phase (candidate generation)."""
    
    @patch('crucible.agents.designer_agent.get_provider')
    def test_generate_candidates_success(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_designer_llm_response
    ):
        """Test successful candidate generation."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_designer_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=300, total_tokens=500),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Generate candidates
        service = DesignerService(integration_db_session)
        result = service.generate_candidates(
            run_id=sample_run.id,
            project_id=project.id,
            num_candidates=3
        )
        
        # Verify result
        assert result["count"] == 3
        assert len(result["candidates"]) == 3
        assert result["reasoning"] is not None
        
        # Verify candidates were saved to database
        candidates = list_candidates(integration_db_session, run_id=sample_run.id)
        assert len(candidates) == 3
        
        # Verify first candidate
        candidate = candidates[0]
        assert candidate.run_id == sample_run.id
        assert candidate.project_id == project.id
        assert candidate.origin == CandidateOrigin.SYSTEM
        assert candidate.status == CandidateStatus.NEW
        assert candidate.mechanism_description is not None
        assert len(candidate.mechanism_description) > 0
        assert candidate.predicted_effects is not None
        assert candidate.scores is not None
        assert "constraint_satisfaction" in candidate.scores
        
        # Verify provenance log
        assert len(candidate.provenance_log) > 0
        provenance_entry = candidate.provenance_log[0]
        assert provenance_entry["type"] == "design"
        assert provenance_entry["actor"] == "agent"
        assert sample_run.id in provenance_entry["source"]
    
    @patch('crucible.agents.designer_agent.get_provider')
    def test_generate_candidates_with_existing(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_designer_llm_response
    ):
        """Test candidate generation with existing candidates."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Create an existing candidate
        from crucible.db.repositories import create_candidate
        existing_candidate = create_candidate(
            integration_db_session,
            run_id=sample_run.id,
            project_id=project.id,
            origin=CandidateOrigin.USER.value,
            mechanism_description="User-provided candidate"
        )
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_designer_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=300, total_tokens=500),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Generate candidates
        service = DesignerService(integration_db_session)
        result = service.generate_candidates(
            run_id=sample_run.id,
            project_id=project.id,
            num_candidates=3
        )
        
        # Verify new candidates were created
        candidates = list_candidates(integration_db_session, run_id=sample_run.id)
        assert len(candidates) >= 4  # 1 existing + 3 new
        
        # Verify agent was called with existing candidate IDs
        call_args = mock_provider.generate.call_args
        assert existing_candidate.id in str(call_args) or "existing" in str(call_args).lower()


class TestScenarioPhase:
    """Test the scenario generation phase."""
    
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_generate_scenario_suite_success(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_scenario_generator_llm_response
    ):
        """Test successful scenario suite generation."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_scenario_generator_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=400, total_tokens=600),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Generate scenario suite
        service = ScenarioService(integration_db_session)
        result = service.generate_scenario_suite(
            run_id=sample_run.id,
            project_id=project.id,
            num_scenarios=2
        )
        
        # Verify result
        assert result["count"] == 2
        assert len(result["scenarios"]) == 2
        assert result["reasoning"] is not None
        
        # Verify scenario suite was saved to database
        scenario_suite = get_scenario_suite(integration_db_session, sample_run.id)
        assert scenario_suite is not None
        assert scenario_suite.run_id == sample_run.id
        assert len(scenario_suite.scenarios) == 2
        
        # Verify first scenario structure
        scenario = scenario_suite.scenarios[0]
        assert scenario["id"] == "scenario_1"
        assert scenario["name"] == "High Load Stress Test"
        assert scenario["type"] == "stress_test"
        assert "focus" in scenario
        assert "initial_state" in scenario
        assert "events" in scenario
        assert "expected_outcomes" in scenario
        assert "weight" in scenario
    
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_generate_scenario_suite_with_candidates(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_scenario_generator_llm_response
    ):
        """Test scenario generation with existing candidates for targeting."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Create a candidate first
        from crucible.db.repositories import create_candidate
        candidate = create_candidate(
            integration_db_session,
            run_id=sample_run.id,
            project_id=project.id,
            origin=CandidateOrigin.SYSTEM.value,
            mechanism_description="Test candidate mechanism"
        )
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_scenario_generator_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=400, total_tokens=600),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Generate scenario suite
        service = ScenarioService(integration_db_session)
        result = service.generate_scenario_suite(
            run_id=sample_run.id,
            project_id=project.id
        )
        
        # Verify agent was called with candidate information
        call_args = mock_provider.generate.call_args
        assert candidate.id in str(call_args) or "candidate" in str(call_args).lower()


class TestDesignAndScenarioPhase:
    """Test the complete design + scenario generation phase."""
    
    @patch('crucible.agents.designer_agent.get_provider')
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_execute_design_and_scenario_phase(
        self,
        mock_scenario_provider,
        mock_designer_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_designer_llm_response,
        mock_scenario_generator_llm_response
    ):
        """Test the complete design + scenario generation phase."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock Designer LLM provider
        mock_designer = Mock()
        mock_designer.generate.return_value = LLMResponse(
            content=json.dumps(mock_designer_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=300, total_tokens=500),
            model="test-model",
            finish_reason="stop"
        )
        mock_designer_provider.return_value = mock_designer
        
        # Mock ScenarioGenerator LLM provider
        mock_scenario = Mock()
        mock_scenario.generate.return_value = LLMResponse(
            content=json.dumps(mock_scenario_generator_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=400, total_tokens=600),
            model="test-model",
            finish_reason="stop"
        )
        mock_scenario_provider.return_value = mock_scenario
        
        # Execute design + scenario phase
        service = RunService(integration_db_session)
        result = service.execute_design_and_scenario_phase(
            run_id=sample_run.id,
            num_candidates=3,
            num_scenarios=2
        )
        
        # Verify result structure
        assert result["status"] == "completed"
        assert "candidates" in result
        assert "scenarios" in result
        assert result["candidates"]["count"] == 3
        assert result["scenarios"]["count"] == 2
        
        # Verify run status
        run = get_run(integration_db_session, sample_run.id)
        assert run.status == RunStatus.RUNNING  # Still running, not completed
        
        # Verify candidates in database
        candidates = list_candidates(integration_db_session, run_id=sample_run.id)
        assert len(candidates) == 3
        
        # Verify scenario suite in database
        scenario_suite = get_scenario_suite(integration_db_session, sample_run.id)
        assert scenario_suite is not None
        assert len(scenario_suite.scenarios) == 2
    
    @patch('crucible.agents.designer_agent.get_provider')
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_execute_design_and_scenario_phase_missing_spec(
        self,
        mock_scenario_provider,
        mock_designer_provider,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run
    ):
        """Test that phase fails gracefully when ProblemSpec is missing."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Delete ProblemSpec
        from crucible.db.repositories import get_problem_spec
        problem_spec = get_problem_spec(integration_db_session, project.id)
        if problem_spec:
            integration_db_session.delete(problem_spec)
            integration_db_session.commit()
        
        # Execute phase - should raise ValueError
        service = RunService(integration_db_session)
        with pytest.raises(ValueError, match="ProblemSpec not found"):
            service.execute_design_and_scenario_phase(
                run_id=sample_run.id
            )


class TestDesignScenarioAPIEndpoints:
    """Test API endpoints for design and scenario generation."""
    
    @patch('crucible.agents.designer_agent.get_provider')
    def test_generate_candidates_endpoint(
        self,
        mock_get_provider,
        test_client,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_designer_llm_response
    ):
        """Test POST /runs/{run_id}/generate-candidates endpoint."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_designer_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=300, total_tokens=500),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.post(
            f"/runs/{sample_run.id}/generate-candidates",
            json={"num_candidates": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "reasoning" in data
        assert "count" in data
        assert data["count"] == 3
        assert len(data["candidates"]) == 3
        
        app.dependency_overrides.clear()
    
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_generate_scenarios_endpoint(
        self,
        mock_get_provider,
        test_client,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_scenario_generator_llm_response
    ):
        """Test POST /runs/{run_id}/generate-scenarios endpoint."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock LLM provider
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_scenario_generator_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=400, total_tokens=600),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.post(
            f"/runs/{sample_run.id}/generate-scenarios",
            json={"num_scenarios": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scenario_suite" in data
        assert "scenarios" in data
        assert "reasoning" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["scenarios"]) == 2
        
        app.dependency_overrides.clear()
    
    @patch('crucible.agents.designer_agent.get_provider')
    @patch('crucible.agents.scenario_generator_agent.get_provider')
    def test_design_and_scenarios_endpoint(
        self,
        mock_scenario_provider,
        mock_designer_provider,
        test_client,
        integration_db_session,
        sample_project_with_spec_and_model,
        sample_run,
        mock_designer_llm_response,
        mock_scenario_generator_llm_response
    ):
        """Test POST /runs/{run_id}/design-and-scenarios endpoint."""
        project, _, _ = sample_project_with_spec_and_model
        
        # Mock Designer LLM provider
        mock_designer = Mock()
        mock_designer.generate.return_value = LLMResponse(
            content=json.dumps(mock_designer_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=300, total_tokens=500),
            model="test-model",
            finish_reason="stop"
        )
        mock_designer_provider.return_value = mock_designer
        
        # Mock ScenarioGenerator LLM provider
        mock_scenario = Mock()
        mock_scenario.generate.return_value = LLMResponse(
            content=json.dumps(mock_scenario_generator_llm_response),
            usage=UsageStats(input_tokens=200, output_tokens=400, total_tokens=600),
            model="test-model",
            finish_reason="stop"
        )
        mock_scenario_provider.return_value = mock_scenario
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.post(
            f"/runs/{sample_run.id}/design-and-scenarios",
            json={"num_candidates": 3, "num_scenarios": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "scenarios" in data
        assert "status" in data
        assert data["status"] == "completed"
        assert data["candidates"]["count"] == 3
        assert data["scenarios"]["count"] == 2
        
        app.dependency_overrides.clear()
    
    def test_generate_candidates_endpoint_run_not_found(
        self,
        test_client,
        integration_db_session
    ):
        """Test POST /runs/{run_id}/generate-candidates when run doesn't exist."""
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API with non-existent run ID
        response = test_client.post(
            "/runs/non-existent-run-id/generate-candidates",
            json={"num_candidates": 3}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        app.dependency_overrides.clear()

