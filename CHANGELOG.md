# Changelog

All notable changes to Int Crucible will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Story 008b: Test Tooling and Run Execution Fixes** (Story definition)
  - Created story document for interactive test tooling and debugging infrastructure
  - Addresses issues discovered during end-to-end testing:
    - Run execution failures with "ProblemSpec or WorldModel not found" errors
    - Lack of test tooling for interactive debugging
    - Poor error visibility and incomplete status reporting
  - Story includes comprehensive acceptance criteria, detailed debugging tasks, and test tooling requirements
  - Prioritized as High (008b) to address critical reliability issues
- **Story 007b: Interactive Guidance and Onboarding Agent** (Implementation)
  - GuidanceAgent (`crucible/agents/guidance_agent.py`) - AI-native guidance agent that explains Int Crucible workflow, provides contextual help, and suggests next steps
    - Uses tool-based approach for dynamic system queries
    - Provides natural language guidance rather than rigid templates
    - Adapts to project state (ProblemSpec, WorldModel, runs) for contextual suggestions
  - GuidanceService (`crucible/services/guidance_service.py`) - Orchestrates guidance operations with tool creation
    - Creates callable tools for querying project state, ProblemSpec, WorldModel, runs, and messages
    - Determines workflow stage and provides state-aware guidance
  - API endpoints for guidance:
    - `POST /chat-sessions/{chat_session_id}/guidance` - Request guidance for a chat session
    - `GET /projects/{project_id}/workflow-state` - Get current workflow state for contextual guidance
  - Frontend integration:
    - "Get Help" button in ChatInterface for requesting guidance
    - WorkflowProgress component showing project progress through ProblemSpec → WorldModel → Run stages
    - Guidance messages displayed in chat interface
  - Comprehensive test suite:
    - 3 unit tests for GuidanceAgent (`tests/unit/agents/test_guidance_agent.py`)
  - Story document updated with implementation details and design philosophy
- **Story 011: Native LLM Function Calling for Guidance Agent** (Story definition)
  - Created story document for future enhancement to use native LLM function calling (Claude tool use, OpenAI functions)
  - Currently guidance agent uses prompt-based tool descriptions; future enhancement will enable true tool invocation
  - Prioritized as Medium
- **Story 007: Chat-First Web UI** (UI improvements)
  - Auto-focus on project title input when create form opens
  - Prerequisites checking in Run Config panel (shows warning if ProblemSpec/WorldModel missing)
  - Improved error messages for missing prerequisites
  - Timezone display fixes (properly converts UTC to local time)
  - Devtools indicator hiding (prevents blocking chat input)
  - Hydration warning suppression (handles browser extension modifications)
- **Story 006: Evaluators and I-Ranker**
  - EvaluatorAgent (`crucible/agents/evaluator_agent.py`) - Evaluates candidates against scenarios, producing structured P (prediction quality), R (resource cost), and constraint satisfaction scores
  - EvaluatorService (`crucible/services/evaluator_service.py`) - Orchestrates evaluation operations with database integration
  - RankerService (`crucible/services/ranker_service.py`) - Aggregates evaluations, computes I = P/R metric, and flags hard constraint violations (weight >= 100)
  - Enhanced RunService with evaluation and ranking phases:
    - `execute_evaluation_phase()` - Evaluate all candidates against all scenarios
    - `execute_ranking_phase()` - Rank candidates based on evaluations
    - `execute_evaluate_and_rank_phase()` - Combined evaluation + ranking phase
    - `execute_full_pipeline()` - Complete pipeline: Design → Scenarios → Evaluation → Ranking
  - API endpoints for evaluation and ranking:
    - `POST /runs/{run_id}/evaluate` - Evaluate all candidates in a run
    - `POST /runs/{run_id}/rank` - Rank candidates based on evaluations
    - `POST /runs/{run_id}/evaluate-and-rank` - Execute evaluate + rank phase
    - `POST /runs/{run_id}/full-pipeline` - Execute complete pipeline
  - Comprehensive test suite:
    - 6 unit tests for EvaluatorAgent (`tests/unit/agents/test_evaluator_agent.py`)
    - 4 unit tests for EvaluatorService (`tests/unit/services/test_evaluator_service.py`)
    - 5 unit tests for RankerService (`tests/unit/services/test_ranker_service.py`)
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
- Updated `frontend/components/RunConfigPanel.tsx` - Added prerequisites checking with visual warnings
- Updated `frontend/components/ChatInterface.tsx` - Fixed timezone parsing and display
- Updated `frontend/components/ProjectSelector.tsx` - Added auto-focus functionality
- Updated `frontend/app/layout.tsx` - Added suppressHydrationWarning for browser extensions
- Updated `frontend/app/globals.css` - Added CSS rules to hide devtools indicators
- Updated `frontend/next.config.ts` - Disabled build activity indicator
- Updated `docs/stories.md` - Added Story 007b, Story 008b, and Story 011 to story index
- Updated `frontend/components/ChatInterface.tsx` - Added "Get Help" button and guidance message handling
- Updated `frontend/app/page.tsx` - Integrated WorkflowProgress component
- Updated `frontend/lib/api.ts` - Added guidance API client functions
- Updated `.gitignore` - Added `.playwright-mcp/` directory

### Fixed
- SQLite threading issues in integration tests by using file-based database instead of in-memory
- Repository `session.refresh()` edge cases in WorldModel creation
- Timezone display issue in chat messages (now correctly converts UTC to local time)
- Devtools indicator blocking chat input area
- React hydration warnings from browser extensions
- Run Config error handling (now shows helpful prerequisites warning instead of generic error)

## [0.1.0] - 2025-01-17

### Added
- Initial project structure
- ProblemSpec agent and service (Story 003)
- Domain schema and database models (Story 002)
- Basic API endpoints for ProblemSpec operations
- CLI interface
- Kosmos integration

