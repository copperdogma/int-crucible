# Changelog

All notable changes to Int Crucible will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Story 005: Designers and ScenarioGenerator**
  - DesignerAgent (`crucible/agents/designer_agent.py`) - Generates diverse candidate solutions from WorldModel
  - ScenarioGeneratorAgent (`crucible/agents/scenario_generator_agent.py`) - Produces scenario suites that stress critical constraints and assumptions
  - DesignerService (`crucible/services/designer_service.py`) - Orchestrates candidate generation with provenance tracking
  - ScenarioService (`crucible/services/scenario_service.py`) - Orchestrates scenario suite generation
  - RunService (`crucible/services/run_service.py`) - Orchestrates complete design + scenario generation phase
  - API endpoints for design and scenario generation:
    - `POST /runs/{run_id}/generate-candidates` - Generate candidates for a run
    - `POST /runs/{run_id}/generate-scenarios` - Generate scenario suite for a run
    - `POST /runs/{run_id}/design-and-scenarios` - Execute full design + scenario phase
  - Candidate and ScenarioSuite JSON schema documentation (`docs/candidate-scenario-schema.md`)
  - Comprehensive test suite:
    - 6 unit tests for DesignerAgent (`tests/unit/agents/test_designer_agent.py`)
    - 6 unit tests for ScenarioGeneratorAgent (`tests/unit/agents/test_scenario_generator_agent.py`)
    - 4 unit tests for DesignerService (`tests/unit/services/test_designer_service.py`)
    - 4 unit tests for ScenarioService (`tests/unit/services/test_scenario_service.py`)
    - 10 integration tests for design + scenario generation flow (`tests/integration/test_design_scenario_flow.py`)
- WorldModeller agent (`crucible/agents/worldmodeller_agent.py`) - Builds structured world models from ProblemSpec and chat context
- WorldModel service (`crucible/services/worldmodel_service.py`) - Orchestrates WorldModel operations with provenance tracking
- WorldModel API endpoints:
  - `GET /projects/{project_id}/world-model` - Retrieve WorldModel
  - `POST /projects/{project_id}/world-model/refine` - Refine WorldModel via agent
  - `PUT /projects/{project_id}/world-model` - Manual WorldModel updates
- WorldModel JSON schema documentation (`docs/world-model-schema.md`)
- Comprehensive test suite:
  - 12 unit tests for WorldModellerAgent (`tests/unit/agents/test_worldmodeller_agent.py`)
  - 13 unit tests for WorldModelService (`tests/unit/services/test_worldmodel_service.py`)
  - 8 integration tests for ProblemSpec → WorldModel flow (`tests/integration/test_problemspec_worldmodel_flow.py`)
- Integration test infrastructure (`tests/integration/conftest.py`) with file-based SQLite database fixture

### Changed
- Updated `crucible/db/repositories.py` - Added graceful error handling for `session.refresh()` in `create_world_model()`
- Updated `tests/conftest.py` - Added fixtures for WorldModeller testing and improved SQLite threading support
- Updated Story 004 work log with implementation details

### Fixed
- SQLite threading issues in integration tests by using file-based database instead of in-memory
- Repository `session.refresh()` edge cases in WorldModel creation

## [0.1.0] - 2025-01-17

### Added
- Initial project structure
- ProblemSpec agent and service (Story 003)
- Domain schema and database models (Story 002)
- Basic API endpoints for ProblemSpec operations
- CLI interface
- Kosmos integration

