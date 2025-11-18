# Changelog

All notable changes to Int Crucible will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

