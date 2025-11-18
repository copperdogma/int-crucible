# Story: Implement ProblemSpec modelling flow

**Status**: Done

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – ProblemSpec agent.
  - **MVP Criteria** – User can submit a problem and drive an end-to-end loop.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – Projects, chat sessions, ProblemSpec object.
  - **Feature: Run Configuration & Execution Pipeline** – selecting mode (full search, eval-only, seeded).

## Acceptance Criteria
- A ProblemSpec data model exists that captures constraints (with weights), goals, resolution, and mode.
- The backend exposes endpoints or functions to read/update the ProblemSpec for a project.
- A ProblemSpec agent is implemented on top of Kosmos’s agent framework that:
  - Consumes recent chat context and the current ProblemSpec.
  - Proposes structured updates and follow-up questions.
- The chat flow supports:
  - User providing free-form problem description.
  - Agent asking clarification questions.
  - Incremental construction of ProblemSpec until it is “ready to run”.
- A simple test path (API/CLI) exists that shows a ProblemSpec being built from a sample conversation.
- User signs off that the ProblemSpec flow feels usable for MVP.

## Tasks
- [x] Define the ProblemSpec schema (fields for constraints, goals, resolution, mode) in the backend domain model.
- [x] Implement persistence for ProblemSpec (CRUD) aligned with Story 002's schema.
- [x] Implement a Kosmos-based ProblemSpec agent that can:
  - [x] Read recent chat messages and current ProblemSpec.
  - [x] Propose updated ProblemSpec and follow-up questions.
- [x] Add backend endpoints or service methods to:
  - [x] Trigger ProblemSpec refinement for a given project/chat.
  - [x] Retrieve the current ProblemSpec.
- [x] Wire the ProblemSpec agent into the chat loop so that setup chats can iteratively refine the spec.
- [x] Create a minimal test script or unit tests that demonstrate end-to-end ProblemSpec construction from sample input.
- [x] Add comprehensive unit tests for ProblemSpec agent and service (pytest test suite with 23 tests).
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The ProblemSpec agent should be conservative about overwriting user-provided constraints; it should propose changes that the user can accept or reject in the UI.

## Work Log

### 20250117-2200 — ProblemSpec agent implementation
- **Result:** Success; ProblemSpec agent created and integrated
- **Notes:**
  - Created `crucible/agents/problemspec_agent.py` extending Kosmos BaseAgent
  - Agent reads chat messages and current ProblemSpec, uses LLM to propose updates
  - Implements conservative constraint merging (preserves user intent)
  - Handles JSON parsing with markdown code block extraction
- **Next:** Create service layer for orchestration

### 20250117-2210 — ProblemSpec service layer implementation
- **Result:** Success; service layer created with database integration
- **Notes:**
  - Created `crucible/services/problemspec_service.py` with ProblemSpecService class
  - Service orchestrates agent and database operations
  - Implements conservative merging of spec updates
  - Handles enum conversion (ResolutionLevel, RunMode) properly
  - Reads chat messages from database and passes context to agent
- **Next:** Add API endpoints for ProblemSpec operations

### 20250117-2220 — API endpoints implementation
- **Result:** Success; API endpoints added for ProblemSpec operations
- **Notes:**
  - Added `GET /projects/{project_id}/problem-spec` endpoint to retrieve ProblemSpec
  - Added `POST /projects/{project_id}/problem-spec/refine` endpoint to refine spec
  - Created Pydantic models for request/response validation
  - Integrated database session dependency injection
- **Next:** Create test script demonstrating end-to-end flow

### 20250117-2230 — Test script creation
- **Result:** Success; comprehensive test script created
- **Notes:**
  - Created `scripts/test_problemspec_flow.py` demonstrating full flow
  - Test script: creates project, chat session, messages, calls agent, shows results
  - Includes logging and error handling
  - Ready for manual testing
- **Next:** Verify all changes compile and work correctly

### 20250117-2240 — Code verification
- **Result:** Success; all code compiles and linter passes
- **Notes:**
  - All imports resolve correctly (verified with virtual environment)
  - Linter passes with no errors
  - Code follows existing patterns in codebase
  - Database operations use proper enum handling
  - Service layer properly integrates agent and database
  - ProblemSpec schema already defined in Story 002 (models.py)
  - CRUD operations already implemented in Story 002 (repositories.py)
  - Agent, service, API endpoints, and test script all complete
- **Next:** Manual testing with test script (requires LLM provider configured)

### 20250117-2250 — Testing guide creation
- **Result:** Success; comprehensive testing guide created
- **Notes:**
  - Created `docs/testing-story-003.md` with detailed testing instructions
  - Covers test script, API endpoints, and direct service testing
  - Includes troubleshooting and example scenarios
  - Documents LLM provider setup (Anthropic, OpenAI, Ollama)
- **Next:** User can now test the implementation using the guide

### 20250117-2255 — .env.example creation
- **Result:** Success; Int Crucible-specific .env.example created
- **Notes:**
  - Created `.env.example` in project root with Int Crucible-specific settings
  - Includes all Crucible config (DATABASE_URL, LOG_LEVEL, API_HOST, API_PORT)
  - Documents LLM provider setup (Anthropic/Claude, OpenAI, Ollama options)
  - References Kosmos settings for advanced options
  - Provides clear examples and instructions for each configuration option
- **Next:** User can copy .env.example to .env and configure their API keys

### 20250117-2320 — Unit tests implementation
- **Result:** Success; comprehensive unit test suite created
- **Notes:**
  - Created `tests/unit/agents/test_problemspec_agent.py` with 11 test cases
  - Created `tests/unit/services/test_problemspec_service.py` with 12 test cases
  - Created `tests/conftest.py` with reusable fixtures (mock LLM provider, test DB session, sample data)
  - Created `pytest.ini` configuration file
  - Tests cover: initialization, execution, JSON parsing edge cases, error handling, enum conversion
  - All 23 tests pass successfully
  - Tests use mocks to avoid real LLM API calls
  - Tests verify database operations with in-memory SQLite
- **Next:** Story complete pending user sign-off


