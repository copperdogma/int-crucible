# Changelog

All notable changes to Int Crucible will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-11-21] - Stories 010 & 020: Multi-chat support and SQLAlchemy metadata cache fix

### Added
- **Story 010: Multiple chat sessions per project** (Complete)
  - `ChatSessionSwitcher` component for creating, switching, and managing chat sessions
  - Inline chat title editing with proper blur handling
  - Context badges showing run_id or candidate_id associations
  - "Discuss in Chat" flow from Run History to create analysis chats
  - Backend API endpoints for chat session updates (`PUT /chat-sessions/{id}`)
  - Run filtering by `chat_session_id` in all run listing endpoints
  - Integration tests for multi-chat workflows (`tests/integration/test_multi_chat_workflow.py`)
- **Story 020: SQLAlchemy metadata cache fix** (Complete)
  - Automatic metadata refresh in `crucible/db/session.py` to sync table definitions with database schema
  - Raw SQL workaround in `get_project_run_summary` endpoint using SQLAlchemy 2.0 named parameters
  - `RunProxy` class with datetime and JSON parsing for raw SQL results
  - CORS exception handlers for all error types

### Changed
- **Backend**: Added `chat_session_id` column to `Run` model with foreign key relationship
  - Migration: `e900a34872ac_add_chat_session_id_to_runs.py`
  - Updated `create_run` and `list_runs` repository functions to support `chat_session_id`
  - Modified `RunResponse` and `RunCreateRequest` models to include `chat_session_id`
- **Frontend**: Enhanced chat interface for multi-chat support
  - `ChatInterface` now requires explicit chat selection (removed aggressive auto-creation)
  - `RunHistoryPanel` includes "Discuss in Chat" button for creating analysis chats
  - `page.tsx` integrates `ChatSessionSwitcher` and handles analysis chat creation
- **API**: Improved error handling with CORS headers on all responses
  - Exception handlers for `StarletteHTTPException`, `RequestValidationError`, `SQLAlchemyError`, and general `Exception`
  - All error responses now include proper CORS headers

### Fixed
- **Critical**: SQLAlchemy metadata cache issue preventing Run History from loading
  - Metadata refresh automatically syncs table definitions after migrations
  - Raw SQL workaround ensures endpoint works even if metadata refresh fails
  - Fixed SQLAlchemy 2.0 parameter binding (named parameters instead of positional)
  - Fixed datetime and JSON parsing for raw SQL results
- **Frontend**: Chat title edit blur issue preventing save button clicks
  - Added `stopPropagation()` to prevent blur from canceling edit on save click

### Documentation
- Updated `docs/stories/story-010-multi-chat-and-run-history.md` with completion status and work log
- Created `docs/stories/story-020-sqlalchemy-metadata-cache-fix.md` documenting the issue and solution
- Updated `docs/stories.md` to mark both stories as complete

## [2025-01-21] - Story 018: AI-first test pipeline and snapshot-based scenarios

### Added
- **Story 018: AI-first snapshot testing system** (Complete)
  - Database schema and models:
    - Alembic migration `cf03659c04c2_add_snapshots_table.py` creates `crucible_snapshots` table with:
      - Core fields: `id`, `name` (unique), `description`, `tags` (JSON array)
      - References: `project_id` (FK), `run_id` (optional)
      - Snapshot data: `snapshot_data` (JSON - full ProblemSpec, WorldModel, run config), `reference_metrics` (JSON), `invariants` (JSON array)
      - Versioning: `version` field (default "1.0") for schema evolution
      - Timestamps: `created_at`, `updated_at`
      - Indexes on `project_id`, `name`, and `tags` (GIN for PostgreSQL)
    - `Snapshot` model in `crucible/db/models.py` with helper methods (`to_dict()`, `get_snapshot_data()`, `get_invariants()`)
    - Repository functions in `crucible/db/repositories.py`: `create_snapshot()`, `get_snapshot()`, `get_snapshot_by_name()`, `list_snapshots()` (with filters), `update_snapshot()`, `delete_snapshot()`
  - Service layer (`crucible/services/snapshot_service.py`):
    - `capture_snapshot_data()`: Extracts full ProblemSpec, WorldModel, run config, optional chat context
    - `capture_reference_metrics()`: Captures baseline run observability data (counts, duration, LLM usage, I-scores)
    - `restore_snapshot_data()`: Restores ProblemSpec and WorldModel to a project (version-aware, uses raw SQL for schema compatibility)
    - `replay_snapshot()`: Creates temporary project, restores data, executes pipeline, validates invariants
    - `validate_invariants()`: Validates 10+ invariant types (min_candidates, run_status, min_top_i_score, no_hard_constraint_violations, max_duration_seconds, min_evaluation_coverage, etc.)
    - `run_snapshot_tests()`: Test harness for running multiple snapshots with cost tracking and failure handling
  - API endpoints (`crucible/api/main.py`):
    - `POST /snapshots` - Create snapshot from project/run
    - `GET /snapshots` - List snapshots with filters (project_id, tags, name)
    - `GET /snapshots/{id}` - Get full snapshot details
    - `DELETE /snapshots/{id}` - Delete snapshot
    - `POST /snapshots/{id}/replay` - Replay snapshot with options
    - `POST /snapshots/run-tests` - Run snapshot test suite
    - All endpoints use Pydantic models for type safety and structured responses
  - CLI commands (`crucible/cli/main.py`):
    - `crucible snapshot create` - Create snapshot with options (project-id, run-id, name, description, tags, invariants-file)
    - `crucible snapshot list` - List snapshots with filtering (table/JSON output)
    - `crucible snapshot show` - Show snapshot details
    - `crucible snapshot delete` - Delete snapshot
    - `crucible snapshot replay` - Replay snapshot with options (phases, num-candidates, num-scenarios, reuse-project)
    - `crucible snapshot test` - Run snapshot tests (supports --all, --snapshot-ids, --max-snapshots, --stop-on-failure, --cost-limit-usd, --format json)
    - All commands support `--format json` for AI consumption
  - Testing:
    - Unit tests: `tests/unit/db/test_snapshot_repositories.py` (10 tests) - All passing
    - Integration tests: `tests/integration/test_snapshot_flow.py` (6 tests) - All passing
    - Manual test script: `scripts/test_snapshot_018.py` for end-to-end verification
    - Total: 16/16 tests passing
  - Documentation:
    - `docs/snapshot-testing.md` - Comprehensive guide with philosophy, usage, invariant types, best practices, AI agent patterns
    - `AGENTS.md` - Updated with "AI-First Tools and Testing Pipeline" section emphasizing snapshot testing as primary mission
    - Story work log updated with detailed progress tracking

### Changed
- `AGENTS.md`: Added section on AI-first snapshot testing system with usage patterns and commands
- `docs/stories/story-018-ai-first-test-pipeline.md`: Updated with complete work log and implementation status

### Technical Notes
- Snapshot data capture uses raw SQL with table reflection to handle SQLAlchemy metadata caching issues
- Invariant validation integrates with existing `verify_run_completeness()` and `get_run_statistics()` from `run_verification.py`
- Cost tracking uses existing `llm_usage` aggregation from `crucible/utils/llm_usage.py`
- All snapshot operations are idempotent and create new runs (no side effects on existing data)
- System ready for immediate use by AI agents and humans for regression testing, debugging, and continuous validation

## [2025-11-21] - Story 019: Operational observability and cost dashboards

### Added
- **Story 019: Operational observability and cost dashboards** (Complete)
  - Backend metrics and logging data model:
    - Alembic migration `a3d1c7e53b34_run_observability_fields.py` adds observability columns to `crucible_runs`:
      - `duration_seconds` (Float, nullable): Total run duration
      - `candidate_count`, `scenario_count`, `evaluation_count` (Integer, not null, default 0): Entity counts
      - `metrics` (JSON, nullable): Structured phase timings and resource breakdowns
      - `llm_usage` (JSON, nullable): Aggregated LLM token usage and cost per phase
      - `error_summary` (Text, nullable): Human-readable error summary for failed runs
    - Migration backfills existing rows with default values for counts
  - RunService instrumentation:
    - `_persist_run_observability()` method records all observability metrics
    - `_record_phase()` helper consistently tracks phase timings (design, scenarios, evaluation, ranking)
    - Phase-level LLM usage aggregation via `crucible/utils/llm_usage.py` utility module
    - Automatic error summary capture on pipeline failures (truncated to 512 chars)
    - Resource breakdown tracking (candidate/scenario/evaluation counts, LLM call counts)
  - API observability surface:
    - New `GET /projects/{project_id}/runs/summary` endpoint with pagination and status filtering
    - Returns `RunSummaryListResponse` with observability fields (duration, counts, metrics, llm_usage, error_summary)
    - `RunResponse` model extended with all observability fields
    - `_serialize_run()` helper includes new fields in API responses
  - CLI observability surface:
    - New `crucible runs` command with comprehensive filtering:
      - `--project-id` (required): Filter by project
      - `--status` (repeatable): Filter by run status
      - `--limit`, `--offset`: Pagination support
      - `--since-hours`: Time window filtering
      - `--format json`: Machine-readable JSON output for AI/automation
    - Rich-formatted table output with status badges, duration, counts, LLM calls, and cost
    - Error summary displayed for failed runs
  - Frontend run history view:
    - New `RunHistoryPanel.tsx` component with:
      - Table view showing Run ID, status, created_at, duration, counts (C/S/E), LLM calls, cost
      - Status badges (color-coded: green for completed, red for failed)
      - Detail view with phase timings, error summary, and links to Results view
      - Filtering by status and pagination controls
      - Loading/empty/error states with clear messaging
    - Integrated into main app page as modal overlay
    - "Run History" button in project toolbar
  - LLM usage tracking utility:
    - `crucible/utils/llm_usage.py` module for extracting and aggregating LLM usage from Kosmos `LLMResponse` objects
    - `usage_stats_to_dict()` extracts usage stats from responses
    - `aggregate_usage()` aggregates multiple usage dictionaries into phase and total summaries
    - Agents (Designer, ScenarioGenerator, Evaluator) return `usage_summary` in execution results
    - Services propagate usage data up the call stack to RunService
  - Documentation:
    - `docs/design.md` updated with observability data contract including sample JSON payloads for `metrics` and `llm_usage`
    - Story work log updated with implementation details
  - Comprehensive test coverage:
    - Unit tests verify RunService observability persistence
    - Integration tests verify run summary endpoint with filtering and pagination
    - All 12 tests passing

### Changed
- `Run` database model extended with 7 new observability fields
- `RunService.execute_full_pipeline()` now tracks and persists detailed phase timings, resource breakdowns, and LLM usage
- All agent `execute()` methods now return `usage_summary` from LLM responses
- All service methods propagate `usage_summary` up the call stack
- API `RunResponse` model includes all observability fields
- CLI `crucible runs` command provides both human-readable and machine-readable output

### Fixed
- Error handling in `RunService` now captures and persists error summaries for failed runs
- Migration handles SQLite vs PostgreSQL differences (server defaults, column alterations)

## [2025-11-21] - Story 008: Provenance and candidate lineage

### Added
- **Story 008: Implement provenance and candidate lineage** (Complete)
  - Canonical provenance tracking system:
    - New `crucible/core/provenance.py` module with shared helpers for building normalized provenance entries
    - `build_provenance_entry()` function ensures consistent event structure across all agents
    - `summarize_provenance_log()` function generates lightweight summaries for UI/API listings
    - Standardized entry format: type, timestamp, actor, source, description, reference_ids, metadata
  - Database schema extensions:
    - Added `provenance_log` JSON column to `crucible_problem_specs` table (Alembic migration `6a9abf0029cd`)
    - Candidate model already had `provenance_log` and `parent_ids` (now fully utilized)
    - WorldModel provenance already existed in `model_data.provenance` (now consistently used)
    - Repository helpers updated to append provenance entries atomically
  - Service layer provenance instrumentation:
    - **DesignerService**: Logs "design" events when generating candidates with run context
    - **EvaluatorService**: Logs "eval_result" events after each candidate-scenario evaluation
    - **RankerService**: Logs "ranking" events when computing I-scores and updating candidate status
    - **ProblemSpecService**: Logs "spec_update" events when refining ProblemSpec with chat context
    - All services use centralized helpers to ensure schema consistency
  - API endpoints for provenance access:
    - Enhanced `GET /runs/{run_id}/candidates` to include `parent_ids` and `provenance_summary` (last event + count)
    - New `GET /runs/{run_id}/candidates/{candidate_id}` endpoint returns full candidate detail:
      - Complete provenance log with all events
      - Parent candidate summaries (id, description, status)
      - All evaluations with scenario context
      - Full scores and constraint breakdown
    - New `GET /projects/{project_id}/provenance` endpoint aggregates provenance across:
      - ProblemSpec provenance log entries
      - WorldModel provenance entries
      - All candidate provenance logs with lineage relationships
  - Frontend lineage visualization:
    - **ResultsView.tsx** enhanced with candidate detail modal:
      - Shows parent candidate chips with status indicators
      - Displays chronological provenance timeline (newest first)
      - Renders last event summary in candidate list cards
      - Fetches full detail on-demand when candidate is selected
      - Displays evaluation summaries with scenario context
    - New API client methods in `frontend/lib/api.ts`:
      - `runsApi.getCandidateDetail(runId, candidateId)` for full lineage data
      - `projectsApi.getProvenance(projectId)` for project-wide provenance (future use)
  - Documentation and schema updates:
    - `docs/candidate-scenario-schema.md` updated with canonical provenance entry structure
    - `docs/world-model-schema.md` documents provenance array format
    - `docs/stories/story-008-provenance-and-lineage.md` updated with implementation details and work log
  - Comprehensive test coverage:
    - Integration tests verify candidate detail endpoint returns provenance and parent summaries
    - Integration tests verify project provenance endpoint aggregates all logs correctly
    - Unit tests verify ProblemSpecService appends provenance entries correctly
    - All existing tests updated to account for provenance fields

### Changed
- `CandidateResponse` model now includes `parent_ids` and optional `provenance_summary` for list views
- All candidate-generating services now emit provenance events automatically (no manual bookkeeping)
- ProblemSpec updates now capture provenance with chat session context and delta information
- Candidate list API responses include lightweight provenance summaries for quick inspection
- Frontend ResultsView now fetches detailed lineage data on-demand for selected candidates

### Fixed
- SQLite migration compatibility: `ALTER COLUMN ... SET NOT NULL` skipped for SQLite (column added with default)
- Provenance log entries now consistently use UTC timestamps via centralized helper
- Parent relationship tracking now properly initialized (empty array instead of None)

## [2025-11-21] - Story 016: Run advisor contract and explicit execution control

### Added
- **Story 016: Run advisor contract and explicit execution control** (Complete)
  - Run audit metadata and provenance tracking:
    - Database migration adds audit columns to `crucible_runs`: `recommended_message_id`, `recommended_config_snapshot`, `ui_trigger_id`, `ui_trigger_source`, `ui_trigger_metadata`, `ui_triggered_at`, `run_summary_message_id`
    - Shared contract definitions in `crucible/models/run_contracts.py` (RunTriggerSource enum, RecommendedRunConfig, RunSummary, RunPreflightResponse dataclasses)
    - Full audit trail enables reconstructing which Architect message recommended a run, which UI action triggered it, and which summary message was posted
  - Architect run recommendations:
    - GuidanceService detects run-intent queries and generates structured `recommended_run_config` metadata
    - Recommendations include: mode, candidate/scenario counts, budget estimates, prerequisite checklist, rationale, blocker status
    - Architect explicitly states it cannot start runs directly and directs users to the Run Config panel
    - Recommendations stored in message metadata and linked to runs via `recommended_message_id`
  - Preflight validation:
    - New `RunPreflightService` validates run configurations before execution
    - Checks prerequisites (ProblemSpec, WorldModel, sufficient candidates)
    - Returns structured blockers and warnings for UI display
    - New API endpoint `POST /projects/{project_id}/runs/preflight` for UI validation
    - GuidanceService reuses preflight logic to provide accurate chat guidance
  - Explicit run execution control:
    - `/runs` API now requires `ui_trigger_id` and `ui_trigger_source` (no runs without explicit UI action)
    - Run Config panel generates trigger IDs and sends audit metadata on run creation
    - Preflight validation gates the "Start Run" button (disabled until prerequisites met)
    - No code path allows chat-only API calls to create/execute runs
  - Post-run summaries:
    - RunService automatically posts Architect summary messages after pipeline completion
    - Summary messages include: run ID, mode, counts, top candidates with I-scores, duration
    - Summary messages linked to runs via `run_summary_message_id`
    - Chat UI displays summary cards with "View results" buttons for easy navigation
  - Frontend UI components:
    - `RunRecommendationCard.tsx`: Displays Architect run recommendations with mode, parameters, blockers, and "Use these settings" CTA
    - `RunSummaryCard.tsx`: Displays post-run summaries with top candidates and results link
    - `RunConfigPanel.tsx`: Enhanced to accept architect recommendations, prefill fields, show blockers/warnings, and gate Run button on preflight validation
    - Shared state management between ChatInterface and RunConfigPanel for recommendation flow
  - Comprehensive testing:
    - Unit tests for `RunPreflightService` (blockers, warnings, prerequisite handling)
    - Unit tests for `RunService` improvements (post-run summaries, prerequisite failures)
    - Manual browser QA verified end-to-end flow: recommendation → preflight → execution → summary
    - All acceptance criteria validated in live UI

### Changed
- `/runs` API endpoints now require `ui_trigger_id` and `ui_trigger_source` for audit trail
- GuidanceService enhanced to emit structured run recommendations with blocker detection
- RunService automatically generates post-run summary messages with metadata linking
- ChatInterface renders new recommendation and summary cards for better UX
- RunConfigPanel integrates with preflight validation and architect recommendations

### Fixed
- SQLite migration compatibility (conditional foreign key creation for non-SQLite databases)
- Column existence checks prevent duplicate column errors during migration
- Run creation now properly captures and persists audit metadata

### Added
- **Story 017: Candidate ranking explanations in UI** (Medium Priority)
  - Story definition for adding human-readable explanations to candidate rankings
  - Backend ranking rationale generation with brief explanations and key factors
  - Frontend display of ranking explanations in Results view and candidate detail modals
  - Designed to satisfy MVP requirement for "brief, understandable explanation of why top candidates are ranked higher"
- **Story 018: AI-first test pipeline and snapshot-based scenarios** (Medium Priority)
  - Story definition for AI-native testing infrastructure
  - Snapshot-based scenario system for reproducible testing with LLM outputs
  - AI-accessible test harness with structured invariants and health checks
  - Snapshot creation and management tools accessible to AI agents
  - Designed to enable AI agents to reliably test and iterate on Int Crucible itself
- **Story 019: Operational observability and cost dashboards** (Medium Priority)
  - Story definition for run-level metrics and operational visibility
  - Basic dashboards for run health, performance, and cost tracking
  - Structured logging and metrics suitable for both human and AI consumption
  - Designed to support resource awareness and transparency requirements
- **Story implementation order guidance** in `docs/stories.md`
  - Recommended order: 016 → 008 → 019 → 018 → 010 → 009 → 017
  - Rationale provided for each story's placement based on dependencies and importance

## [2025-11-20] - Story 015: Chat-first project creation and streaming pipeline improvements

### Added
- **Story 015: Chat-first project creation and selection** (Complete)
  - Chat-first project creation:
    - Architect automatically greets users when no project is selected
    - Project creation triggered by natural language description from user
    - LLM-based project title and description inference from user input
    - Automatic chat session creation linked to new project
    - Initial greeting streamed through real-time pipeline
  - Streaming pipeline improvements:
    - Chat history remains visible during streaming (no "pop-in" effect)
    - Messages query disabled during streaming to prevent interference
    - Synchronous ref tracking (`isStartingStreamRef`) prevents race conditions
    - React Query cache cleared before streaming starts for clean state
    - Proper scroll-to-top behavior when switching projects
  - Heuristic-based spec refinement prevention:
    - Clarification queries ("what is...", "how does...") no longer trigger spec updates
    - `_should_refine_problem_spec()` method checks query intent before refinement
    - Prevents unwanted spec mutations when user is just asking questions
    - Still allows refinement when user explicitly asks for spec changes
  - New UI components:
    - `MessageContent.tsx`: Proper line break rendering for AI-generated messages
    - `ProjectEditModal.tsx`: Inline project title/description editing
  - Architect follow-up improvements:
    - Summary of updates appended to Architect messages ("All set — added X constraints...")
    - Next steps suggested based on workflow stage
    - Future-tense language ("I'm going to...") instead of past-tense ("I've done...")

### Fixed
- Chat history disappearing during streaming (messages now always rendered)
- "Send" button stuck in "Sending..." mode (proper state management)
- Spec panel Resolution padding (text no longer "mushed" against highlight border)
- Unexpected world model generation on clarification queries
- Initial user message hidden by Workflow Progress box (auto-scroll to top)
- Line breaks not respected in AI-generated messages (new MessageContent component)

### Changed
- Project creation flow moved from modal form to conversational chat interface
- Streaming pipeline consolidated to single real-time update system
- Guidance service now uses heuristics to determine if spec refinement is appropriate
- ProblemSpec service ensures minimal spec created even if agent returns empty updates
- Workflow stage determination improved (remains "setup" until both ProblemSpec and WorldModel exist)

### Added
- **Story 011: Native LLM Function Calling for Guidance/Architect** (2025-01-17)
  - Native LLM function calling infrastructure:
    - `crucible/core/tools.py`: Tool schema generation from Python functions (235 lines)
      - Automatic schema generation from function signatures with type hints
      - Extracts parameter descriptions from docstrings
      - Supports OpenAI and Anthropic tool formats
      - Handles Optional parameters and defaults
    - `crucible/core/tool_calling.py`: Multi-turn tool calling executor (762 lines)
      - `ToolCallingExecutor` class manages tool execution and LLM interaction
      - Supports OpenAI function calling (primary) and Anthropic tool use (fallback)
      - Multi-turn tool calling loop (agent can chain multiple tools in sequence)
      - Tool call validation with allow/deny lists
      - Max iterations limit to prevent tool call loops
  - Guidance Agent integration:
    - Updated `GuidanceAgent` to use `ToolCallingExecutor` for native function calling
    - Automatically initializes tool executor when tools are provided
    - Falls back to prompt-based tool descriptions if function calling unavailable
    - Supports tools: `get_workflow_state`, `get_problem_spec`, `get_world_model`, `list_runs`, `get_chat_history`
  - Tool call audit logging:
    - `ToolCallAudit` dataclass captures: `tool_name`, `arguments` (redacted), `result_summary`, `duration_ms`, `success`, `error`
    - Sensitive argument redaction (password, api_key, secret, token, key fields)
    - Audit logs stored in `message_metadata["tool_call_audits"]` for provenance tracking
    - API endpoint `/architect-reply` includes audit logs in response metadata
  - Comprehensive test suite:
    - `tests/unit/core/test_tools.py`: Tool schema generation tests (142 lines)
    - `tests/unit/core/test_tool_calling.py`: Tool execution tests (293 lines)
    - Tests cover schema generation, tool validation, execution, error handling, audit logging
  - Documentation:
    - `docs/tool-calling-architecture.md`: Complete architecture documentation (343 lines)
    - Includes usage examples, security considerations, how to add new tools
    - Performance considerations and future enhancements documented

### Fixed
- **Story 014: Streaming UI improvements** (2025-01-17)
  - Fixed highlighting fade behavior: only border color fades, text remains fully readable
    - Changed `.highlight-recent` and `.highlight-fading` to use `rgba()` opacity on border color only
    - Removed element-level `opacity` that was fading text unnecessarily
  - Fixed input field behavior: input remains enabled while agent is replying
    - Input field only disabled when no chat session exists (removed `isSending` check)
    - Send button correctly disabled during agent replies (`isGeneratingReply` check)
    - Users can now type and edit their next message while waiting for agent response
    - Enter key still prevented from sending while agent is replying

### Added
- **Story 013: Spec/World-Model Deltas and Live Highlighting** (Implementation)
  - Backend delta computation:
    - `_compute_spec_delta` method in `ProblemSpecService` computes structured deltas comparing current vs updated ProblemSpec
    - `_compute_world_model_delta` method in `WorldModelService` computes structured deltas from agent changes
    - Delta structures include: `touched_sections`, `constraints` (added/updated/removed), `goals` (added/updated/removed), `resolution_changed`, `mode_changed`
    - Deltas stored in Architect message `message_metadata` for timeline reconstruction
    - Fallback logic infers deltas from user queries when frontend refinement happens first
  - Frontend delta display:
    - `DeltaSummary` component shows compact one-line summaries in Architect messages (e.g., "Spec update: +1 constraint, 2 constraints updated")
    - Expandable `[Details]` toggle reveals per-item change information
    - Human-readable format with proper pluralization
  - Live highlighting in spec panel:
    - Individual constraint/goal tracking with delta-based ordering (newest = most vibrant)
    - Three highlight levels: `highlight-newest` (3px green border, full opacity), `highlight-recent` (2px, 0.7 opacity), `highlight-fading` (2px, 0.4 opacity)
    - Border-only highlighting (no background) for clean visual design
    - Highlights driven by structured deltas from message metadata, not UI heuristics
    - Proper padding alignment between Goals and Constraints sections
  - Timeline reconstruction:
    - Deltas persist in message metadata, enabling reconstruction of spec/world-model evolution
    - Stable delta structure suitable for future provenance work (Story 008)
  - Comprehensive browser testing:
    - All acceptance criteria verified in live UI
    - Tested delta summaries, highlighting, fading, and newest item detection
    - Fixed delta-based fading (not time-based) and individual item tracking
- **Story 012: Architect-led Conversational Loop and Full Interaction Logging** (Implementation)
  - Architect auto-reply functionality:
    - Automatic Architect responses after every user message (removed "Get Help" button requirement)
    - New API endpoint `/chat-sessions/{id}/architect-reply` for generating Architect replies
    - Architect persona clearly labeled in UI with `agent_name: "Architect"` metadata
    - Workflow-aware guidance based on project state (setup/ready_to_run/completed)
  - Full conversational logging:
    - All user messages, Architect responses, and system events stored in `crucible_messages`
    - Structured metadata includes: `workflow_stage`, `guidance_type`, `agent_name`, `suggested_actions`
    - Error handling creates system messages instead of breaking conversation flow
    - Complete interaction log enables future analysis and UX improvements
  - GuidanceService enhancements:
    - `_determine_guidance_type()` method categorizes guidance (spec_refinement, clarification, run_recommendation, etc.)
    - Metadata enrichment for all Architect responses
    - Tool-based approach for dynamic system queries
  - Frontend improvements:
    - Auto-focus on chat input when entering chat mode and after Architect replies
    - Loading indicators: "Sending..." and "Architect is replying..." states
    - Inline system/error messages in chat (no alerts)
    - Fixed SpecPanel scrolling with proper flex layout and nested scroll containers
    - Fixed WorkflowProgress text color (changed from blue to gray to avoid confusion with clickable elements)
    - Fixed chat input visibility (ensured input area remains visible with proper flex constraints)
  - Architecture documentation:
    - Added "Conversational Logging" section to `docs/architecture.md`
    - Documents decision to treat conversations as canonical interaction log
  - Comprehensive browser testing:
    - All acceptance criteria verified in live UI
    - Tested auto-reply functionality, UI labeling, error handling, and conversation flow
    - All UI issues identified and resolved
- **Story 008b: Test Tooling and Run Execution Fixes** (Implementation)
  - Run execution fixes:
    - Added session refresh (`session.expire_all()`) to fix "ProblemSpec or WorldModel not found" errors
    - Enhanced error messages with available projects list for better debugging
    - Fixed run status reporting to prevent overwriting "completed" status
    - Added comprehensive logging with phase tags and timing information
  - Test tooling CLI command (`crucible test-run`):
    - Execute full pipeline with detailed progress reporting
    - Verify existing runs with `--verify-only` flag
    - Custom candidate/scenario counts
    - Automatic verification of run completeness and data integrity
    - Rich formatted output with tables and progress indicators
  - Verification utilities (`crucible/services/run_verification.py`):
    - `verify_run_completeness()` - Checks all expected entities exist
    - `verify_data_integrity()` - Validates relationships and foreign keys
    - `get_run_statistics()` - Provides detailed run statistics
  - Comprehensive instrumentation:
    - Phase-level logging with timing for all pipeline phases
    - Entity count logging (candidates, scenarios, evaluations)
    - Clear phase identification with tags like `[Design Phase]`, `[Phase 1/2]`
  - Unit tests:
    - 11 test cases for verification utilities
    - 7 test cases for run service improvements
    - Total: 18 unit tests covering error handling, status reporting, and verification
  - E2E test script (`scripts/test_e2e_008b.py`):
    - Tests with real database data
    - Validates error handling, verification utilities, and session refresh fix
    - All 4 E2E test scenarios passing
  - Story document updated with implementation details and E2E test results
- **Stories 012-016: Comprehensive Architect-Centric Chat Experience** (Story definitions)
  - **Story 012: Architect-led conversational loop and full interaction logging**
    - Replaces Story 008c with comprehensive architect persona approach
    - Automatic Architect responses after every user message (removes "Get Help" button requirement)
    - Full conversational logging with structured metadata (workflow_stage, guidance_type, related IDs)
    - All interactions stored in `crucible_messages` for future analysis and improvement
    - Error handling via system messages in chat instead of alerts
  - **Story 013: Spec/world-model deltas and live highlighting**
    - ProblemSpec/WorldModel refinements return structured delta summaries
    - Compact "Spec update" lines in Architect replies with expandable details
    - Spec panel visual highlighting with recency-based fade (most recent = vibrant, older = subtle)
    - Delta information stored in message metadata for analyzable interaction log
  - **Story 014: Streaming architect responses and typing indicators**
    - Backend streaming support (SSE or StreamingResponse) for Architect replies
    - Frontend streaming consumption with live message updates and auto-scroll
    - Typing/busy indicator bubble in chat ("Architect is thinking...")
    - Input area busy state feedback without freezing UI
    - Graceful error handling with fallback to full response if streaming fails
    - Final messages stored as coherent single entries in database
  - **Story 015: Chat-first project creation and selection**
    - Project creation moved into conversational flow (Architect greets, asks what you're working on)
    - Architect infers project title/description from user's natural language response
    - Project selector remains for multi-project management but creation is chat-driven
    - All project creation steps logged as part of conversation transcript
  - **Story 016: Run advisor contract and explicit execution control**
    - Architect only advises on run configuration, never executes runs
    - Run execution always requires explicit user button click (budget protection)
    - Architect recommendations (mode, config) logged with metadata
    - Post-run summaries from Architect logged as conversational events
  - All stories prioritized as High
  - Story 008c superseded and removed (ideas migrated into 012-016)
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

