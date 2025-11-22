# Story: Implement provenance and candidate lineage

**Status**: Implementation Complete ✅ (Pending User Sign-Off)

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Provenance tracker.
  - **MVP Criteria** – user can inspect candidate provenance/lineage at a basic level.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – candidate detail view and lineage.
  - **Feature: Feedback Loop on Model, Constraints, and Evaluations** – issues and patches that should be tracked.

## Acceptance Criteria
- Candidates carry:
  - `parents` / `parent_ids`.
  - `origin` (user/system).
  - A `provenance_log` capturing key events (creation, refinement, evaluation, feedback patches).
- WorldModel and ProblemSpec changes record provenance entries where relevant.
- The backend exposes provenance information so that:
  - The UI can show a basic lineage view (even if just textual) for each candidate.
  - Logs can be inspected to understand how a candidate evolved.
- Provenance is captured as part of normal pipeline execution (no manual bookkeeping required).

## Tasks
- [x] Define the provenance log structure for candidates, ProblemSpec, and WorldModel entries (type, actor, timestamp, description, references).
  - [x] Consolidate the canonical event schema (fields + allowed `type` values like `design`, `eval_result`, `ranking`, `feedback_patch`) across `docs/candidate-scenario-schema.md`, `docs/world-model-schema.md`, and a new ProblemSpec note so every component uses the same contract.
  - [x] Document how `parent_ids`, `origin`, `source`, and `reference_ids` should be populated by each agent/service so downstream consumers can build lineage trees deterministically.
- [x] Extend the Candidate, ProblemSpec, and WorldModel schemas to store parent relationships and provenance logs in a durable, queryable way.
  - [x] Verify the existing Candidate columns (`origin`, `parent_ids`, `provenance_log`) cover all fields; add repository helpers to append entries atomically and guard against race conditions during ranking/evaluation updates.
  - [x] Add a JSON `provenance_log` column (with Alembic migration + SQLAlchemy model updates) to `crucible_problem_specs`, and ensure `world_model.model_data` always exposes a `provenance` array so UI/API callers can fetch deltas without parsing entire objects.
  - [x] Define how downstream features (candidate refinement, issue-driven patches) will populate `parent_ids`, even if the MVP just stubs the hooks until refinement flows land.
- [x] Update Designer, WorldModeller, Evaluator, I-Ranker, and Feedback agents/services to emit provenance events at key steps.
  - [x] `ProblemSpecService` and `WorldModelService`: append provenance entries whenever `_apply_*_updates` runs (include chat session/message references, delta summaries, and manual-edit metadata).
  - [x] `DesignerService`: normalize the initial `design` provenance entry, honor optional `parents` from the agent response, and stash agent reasoning so refinements can chain off of earlier candidates.
  - [x] `EvaluatorService`: after each scenario evaluation (or aggregate pass), append `eval_result` entries with scenario IDs, score snapshots, and evaluation record IDs.
  - [x] `RankerService` (I-Ranker): when scores/statuses change, append a `ranking` provenance entry describing P/R/I, constraint flag summaries, and resulting status transitions.
  - [x] Stub hooks for future Feedback/Issue handling so when Story 009 lands we can append `feedback_patch` provenance without reworking this story.
- [x] Implement backend functions/endpoints to query provenance for a given candidate, run, or project.
  - [x] Add repository helpers plus `/candidates/{candidate_id}` (or `/runs/{run_id}/candidates/{candidate_id}`) endpoints that return the full provenance log, `parent_ids`, evaluations, and derived metadata for that candidate.
  - [x] Extend `/runs/{run_id}/candidates` (and any run summary endpoints) to include condensed provenance summaries (`last_event`, `parent_count`, `origin`) so the UI can avoid extra calls when rendering the table.
  - [x] Provide a project/run-level provenance feed endpoint (e.g., `/projects/{project_id}/provenance`) so chat/CLI surfaces can show how specs/world models/candidates evolved over time.
- [x] Implement a basic lineage view in the UI (textual list of events with parent relationships; graphical view can be deferred).
  - [x] Update `frontend/lib/api.ts` and the React Query hooks so candidate objects include `status`, `origin`, `parent_ids`, and provenance metadata.
  - [x] Enhance `ResultsView` (candidate modal) to render parent chips + a chronological provenance timeline grouped by event type, with affordances for inspecting evaluation references.
  - [x] Add a lightweight lineage panel (tree/table) that highlights ancestor chains and key run milestones; ensure it degrades gracefully when provenance data is sparse.
- [x] Add tests or sample runs demonstrating that provenance and lineage are recorded and retrievable for a run.
  - [x] Expand `tests/integration/test_design_scenario_flow.py` (and/or add a dedicated lineage test) to assert design/evaluation/ranking events are persisted and retrievable via the new endpoints.
  - [x] Add unit tests for the repository append helpers and ProblemSpec/WorldModel provenance writes.
  - [x] Provide a CLI script or documented manual run that exercises the new lineage API and captures sample JSON for future debugging.
- [ ] User must sign off on functionality before story can be marked complete.
  - [ ] Demo the provenance endpoints plus the new UI lineage view and capture acceptance notes in this Work Log.

## Notes
- The provenance design should keep compatibility with future graph-based visualization and potential reuse of Kosmos’s knowledge/provenance machinery.

## Work Log
### 20251121-0915 — Reviewed current provenance implementation and updated plan
- **Result:** Success; audited requirements/design docs plus existing backend/frontend code paths.
- **Notes:** Candidate DB schema already includes `origin`, `parent_ids`, and `provenance_log`, but ProblemSpec lacks provenance storage and API responses omit lineage data. UI currently has no candidate lineage surface.
- **Next:** Await go-ahead to implement data-model updates, API endpoints, and lineage UI per the revised task list.

### 20251121-0933 — Implemented provenance storage, APIs, and lineage UI
- **Result:** Success; added ProblemSpec `provenance_log` column/migration, repository append helpers, and provenance emission across Designer/Evaluator/Ranker services. Exposed new `/runs/{run_id}/candidates/{candidate_id}` and `/projects/{project_id}/provenance` endpoints plus richer candidate responses, updated React Results view to show lineage timeline, and refreshed docs/tests.
- **Notes:** Canonical provenance schema now shared by ProblemSpec, WorldModel, and Candidate logs. Frontend fetches detail on demand to avoid heavy candidate payloads. Added integration/unit coverage to guard new behavior.
- **Next:** Monitor downstream consumers (CLI, future feedback flows) to ensure they leverage the helper functions, and extend UI lineage rendering once graphical tree view is prioritized.


