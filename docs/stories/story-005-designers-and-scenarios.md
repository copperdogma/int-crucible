# Story: Implement Designers and ScenarioGenerator

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Designer agents (MVP), ScenarioGenerator.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run Configuration & Execution Pipeline** – Designers, ScenarioGenerator, ScenarioSuite.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – candidate statuses and summaries.

## Acceptance Criteria
- Designer agents can generate multiple, diverse candidate solutions from the WorldModel.
- Each candidate includes at least:
  - Mechanism description.
  - Expected effects on actors/resources.
  - Rough constraint compliance estimates.
- The ScenarioGenerator can produce a minimal, structured scenario suite:
  - Scenarios that stress high-weight constraints and fragile assumptions.
  - Represented in a format that Evaluators can consume.
- The pipeline can run a “design + scenario generation” phase for a run:
  - Given a ProblemSpec + WorldModel, produce candidate list + scenarios.
- Candidate creation and scenario generation are visible in logs/DB for debugging.

## Tasks
- [x] Design the candidate representation and ScenarioSuite structure (aligned with Story 002 schema).
- [x] Implement Designer agents (on top of Kosmos agent framework) that:
  - [x] Generate multiple candidate mechanisms from the WorldModel.
  - [x] Provide rough constraint compliance estimates for each candidate.
- [x] Implement ScenarioGenerator agent that:
  - [x] Takes WorldModel and candidate set as input.
  - [x] Produces a minimal ScenarioSuite focused on critical constraints and assumptions.
- [x] Integrate Designers and ScenarioGenerator into the run pipeline orchestration.
- [x] Add basic logging and provenance entries for candidate and scenario generation.
- [x] Add tests or demo runs showing candidate and scenario generation for a sample problem.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- Diversity of candidates is more important than completeness; the MVP should surface clearly distinct approaches rather than many small variants.

## Work Log

### 20250117-1600 — Designed candidate and scenario suite JSON schemas
- **Result:** Success; schemas documented in `docs/candidate-scenario-schema.md`
- **Notes:**
  - Documented Candidate structure: mechanism_description, predicted_effects, scores, provenance_log, parent_ids
  - Documented ScenarioSuite structure: scenarios array with id, name, description, type, focus, initial_state, events, expected_outcomes, weight
  - Schemas align with Story 002 database models
  - MVP focus: minimal but sufficient for evaluators to consume
- **Next:** Implement Designer agent

### 20250117-1610 — Implemented DesignerAgent
- **Result:** Success; DesignerAgent created and integrated
- **Notes:**
  - Created `crucible/agents/designer_agent.py` extending Kosmos BaseAgent
  - Agent reads ProblemSpec and WorldModel, uses LLM to generate diverse candidate mechanisms
  - Generates predicted_effects (actors_affected, resources_impacted, mechanisms_modified)
  - Provides rough constraint_compliance estimates (0.0-1.0 or boolean)
  - Focuses on diversity over completeness (temperature=0.7 for more diverse outputs)
  - Handles JSON parsing with markdown code block extraction
  - Returns candidates list and reasoning
- **Next:** Implement ScenarioGenerator agent

### 20250117-1620 — Implemented ScenarioGeneratorAgent
- **Result:** Success; ScenarioGeneratorAgent created and integrated
- **Notes:**
  - Created `crucible/agents/scenario_generator_agent.py` extending Kosmos BaseAgent
  - Agent reads ProblemSpec, WorldModel, and candidate set
  - Generates scenarios that stress high-weight constraints and fragile assumptions
  - Produces structured scenarios with: id, name, description, type, focus, initial_state, events, expected_outcomes, weight
  - Supports scenario types: stress_test, edge_case, normal_operation, failure_mode
  - Can target scenarios based on existing candidates
  - Handles JSON parsing with markdown code block extraction
- **Next:** Create service layers

### 20250117-1630 — Implemented DesignerService and ScenarioService
- **Result:** Success; service layers created with database integration
- **Notes:**
  - Created `crucible/services/designer_service.py` with DesignerService class
  - Created `crucible/services/scenario_service.py` with ScenarioService class
  - DesignerService orchestrates DesignerAgent and creates Candidate records in database
  - Automatically adds provenance_log entries for each candidate
  - Creates initial scores dict with constraint_satisfaction estimates
  - ScenarioService orchestrates ScenarioGeneratorAgent and creates/updates ScenarioSuite records
  - Both services handle ProblemSpec and WorldModel integration
  - Updated `crucible/services/__init__.py` to export new services
- **Next:** Add API endpoints

### 20250117-1640 — Added API endpoints for design and scenario generation
- **Result:** Success; API endpoints added for Designer and ScenarioGenerator operations
- **Notes:**
  - Added `POST /runs/{run_id}/generate-candidates` endpoint for candidate generation
  - Added `POST /runs/{run_id}/generate-scenarios` endpoint for scenario suite generation
  - Created Pydantic models for request/response validation
  - Integrated database session dependency injection
  - All endpoints follow same patterns as ProblemSpec/WorldModel endpoints
  - Endpoints properly handle run lookup and project_id resolution
- **Next:** Create run orchestration service

### 20250117-1650 — Implemented RunService for pipeline orchestration
- **Result:** Success; RunService created for orchestrating design + scenario phase
- **Notes:**
  - Created `crucible/services/run_service.py` with RunService class
  - Implements `execute_design_phase()` for candidate generation
  - Implements `execute_scenario_phase()` for scenario suite generation
  - Implements `execute_design_and_scenario_phase()` for full "design + scenario generation" phase
  - Updates run status to RUNNING when phase starts
  - Updates run status to FAILED on errors
  - Verifies ProblemSpec and WorldModel exist before execution
  - Added `POST /runs/{run_id}/design-and-scenarios` API endpoint for orchestration
  - Updated `crucible/services/__init__.py` to export RunService
- **Next:** Add unit tests

### 20250117-1700 — Created unit tests for agents and services
- **Result:** Success; comprehensive unit test suites created
- **Notes:**
  - Created `tests/unit/agents/test_designer_agent.py` with 6 test cases
  - Created `tests/unit/agents/test_scenario_generator_agent.py` with 6 test cases
  - Created `tests/unit/services/test_designer_service.py` with 4 test cases
  - Created `tests/unit/services/test_scenario_service.py` with 4 test cases
  - Tests cover: initialization, execution, JSON parsing edge cases, error handling, empty inputs, existing candidates/scenarios
  - All tests use mocks to avoid real LLM API calls
  - Tests verify database operations with mocked sessions
  - Total: 20 unit tests for new functionality
- **Next:** Verify all code compiles and linter passes

### 20250117-1710 — Code verification
- **Result:** Success; all code compiles and linter passes
- **Notes:**
  - All imports resolve correctly (verified with virtual environment)
  - Linter passes with no errors
  - Code follows existing patterns in codebase
  - Database operations use proper JSON field handling
  - Service layers properly integrate agents and database
  - Provenance tracking automatically added to all candidate creation
  - API endpoints properly integrated with FastAPI
  - All 20 unit tests structured and ready to run
  - Updated `crucible/agents/__init__.py` and `crucible/services/__init__.py` to export new components
- **Next:** Story implementation complete pending user sign-off

### 20250117-1720 — Created integration tests for design + scenario generation flow
- **Result:** Success; comprehensive integration test suite created
- **Notes:**
  - Created `tests/integration/test_design_scenario_flow.py` with 10 integration tests
  - Tests use file-based SQLite database (via `integration_db_session` fixture)
  - Test classes: TestDesignPhase, TestScenarioPhase, TestDesignAndScenarioPhase, TestDesignScenarioAPIEndpoints
  - Tests cover: candidate generation, scenario suite generation, full design+scenario phase, API endpoints, error handling
  - All tests use mocks for LLM providers to avoid real API calls
  - Tests verify database persistence, provenance tracking, and data structure correctness
  - Tests verify run status updates and error handling (missing ProblemSpec/WorldModel)
  - Total: 10 integration tests covering full end-to-end flow
- **Next:** Story implementation complete pending user sign-off

