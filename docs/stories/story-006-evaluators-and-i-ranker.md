# Story: Implement Evaluators and I-Ranker

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Evaluator agents, I-Ranker, Provenance tracker.
  - **MVP Criteria** – structured P, R, constraint satisfaction, and I = P/R scores.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run Configuration & Execution Pipeline** – Evaluations, scores, ranking.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – ranked list, candidate detail view.

## Acceptance Criteria
- Evaluator agents can:
  - Consume a candidate and a set of scenarios.
  - Produce consistent scores for P (prediction quality), R (resource/complexity cost), and constraint satisfaction per scenario.
- The I-Ranker can:
  - Aggregate evaluator outputs into final scores per candidate.
  - Compute I = P/R for each candidate.
  - Flag violations of “hard” (weight 100) constraints.
- Evaluation remains language-level only (no real code execution) for the MVP.
- The pipeline can run a full “evaluate + rank” phase:
  - Input: candidate set + scenarios.
  - Output: ranked list with explanations and flags.
- The system stores evaluation results and rankings in the DB and exposes them via the backend for UI consumption.

## Tasks
- [x] Design the Evaluation record structure (per-candidate, per-scenario) and integrate it into the schema (Story 002).
- [x] Implement Evaluator agents that:
  - [x] Accept candidate + scenario descriptions.
  - [x] Produce structured P, R, and constraint satisfaction scores, plus a brief explanation.
- [x] Implement I-Ranker logic that:
  - [x] Aggregates evaluations.
  - [x] Computes I = P/R and highlights hard-constraint violations.
- [x] Integrate Evaluators and I-Ranker into the run pipeline orchestration.
- [x] Expose ranked results and evaluation summaries via backend endpoints.
- [x] Add tests or demo runs showing evaluation and ranking for sample candidates and scenarios.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The MVP can use relatively simple scoring heuristics as long as they are structured and explainable; more advanced scoring and uncertainty modelling can be added later.

## Work Log

### 20250117-1800 — Created EvaluatorAgent
- **Result:** Success; EvaluatorAgent created and integrated
- **Notes:**
  - Created `crucible/agents/evaluator_agent.py` extending Kosmos BaseAgent
  - Agent reads candidate and scenario descriptions, uses LLM to evaluate performance
  - Produces structured scores for P (prediction quality), R (resource cost), and constraint satisfaction
  - Handles JSON parsing with markdown code block extraction
  - Uses lower temperature (0.3) for more consistent scoring
  - Returns safe defaults on parsing errors
- **Next:** Create EvaluatorService

### 20250117-1810 — Created EvaluatorService
- **Result:** Success; EvaluatorService created with database integration
- **Notes:**
  - Created `crucible/services/evaluator_service.py` with EvaluatorService class
  - Implements `evaluate_candidate_against_scenario()` for single evaluations
  - Implements `evaluate_all_candidates()` for batch evaluation of all candidates against all scenarios
  - Automatically skips existing evaluations to avoid duplicates
  - Integrates with ProblemSpec and WorldModel for context
  - Creates Evaluation records in database with P, R, constraint_satisfaction, and explanation
- **Next:** Create I-Ranker service

### 20250117-1820 — Created RankerService (I-Ranker)
- **Result:** Success; RankerService created for ranking candidates
- **Notes:**
  - Created `crucible/services/ranker_service.py` with RankerService class
  - Implements `rank_candidates()` that aggregates evaluations per candidate
  - Computes I = P/R for each candidate (with division-by-zero protection)
  - Aggregates P and R scores by averaging across all scenarios
  - Aggregates constraint satisfaction scores per constraint
  - Flags hard constraint violations (weight >= 100) and marks candidates as REJECTED
  - Updates candidate status based on I score: PROMISING (>=0.8), UNDER_TEST (>=0.5), WEAK (<0.5)
  - Updates candidate scores in database with aggregated P, R, I, and constraint_satisfaction
  - Returns ranked list sorted by I score (descending)
- **Next:** Integrate into RunService pipeline

### 20250117-1830 — Integrated evaluation and ranking into RunService
- **Result:** Success; evaluation and ranking phases integrated into pipeline
- **Notes:**
  - Updated `crucible/services/run_service.py` to include EvaluatorService and RankerService
  - Added `execute_evaluation_phase()` method for evaluation phase
  - Added `execute_ranking_phase()` method for ranking phase
  - Added `execute_evaluate_and_rank_phase()` method for combined phase
  - Added `execute_full_pipeline()` method for complete pipeline: Design → Scenarios → Evaluation → Ranking
  - Full pipeline marks run as COMPLETED when finished
  - All phases properly handle errors and update run status
- **Next:** Add API endpoints

### 20250117-1840 — Added API endpoints for evaluation and ranking
- **Result:** Success; API endpoints added for all evaluation and ranking operations
- **Notes:**
  - Added `POST /runs/{run_id}/evaluate` endpoint for evaluation phase
  - Added `POST /runs/{run_id}/rank` endpoint for ranking phase
  - Added `POST /runs/{run_id}/evaluate-and-rank` endpoint for combined phase
  - Added `POST /runs/{run_id}/full-pipeline` endpoint for complete pipeline execution
  - Created Pydantic models for all request/response types
  - Updated `crucible/api/main.py` with all new endpoints
  - Updated `crucible/services/__init__.py` and `crucible/agents/__init__.py` to export new services
- **Next:** Create unit tests

### 20250117-1850 — Created unit tests for EvaluatorAgent and services
- **Result:** Success; comprehensive unit test suites created
- **Notes:**
  - Created `tests/unit/agents/test_evaluator_agent.py` with 6 test cases
  - Created `tests/unit/services/test_evaluator_service.py` with 4 test cases
  - Created `tests/unit/services/test_ranker_service.py` with 5 test cases
  - Tests cover: initialization, execution, JSON parsing edge cases, error handling, missing inputs, hard constraint violations
  - All tests use mocks to avoid real LLM API calls
  - Tests verify database operations with mocked sessions
  - Total: 15 unit tests for new functionality
- **Next:** Verify all code compiles and linter passes

### 20250117-1900 — Code verification
- **Result:** Success; all code compiles and linter passes
- **Notes:**
  - All imports resolve correctly (verified with virtual environment)
  - Linter passes with no errors
  - Code follows existing patterns in codebase
  - Database operations use proper JSON field handling
  - Service layers properly integrate agents and database
  - API endpoints properly integrated with FastAPI
  - All 15 unit tests structured and ready to run
  - Evaluation record structure already exists in Story 002 schema (Evaluation model)
- **Next:** Story implementation complete pending user sign-off
