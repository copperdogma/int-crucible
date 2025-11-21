# Story 016: Run advisor contract and explicit execution control

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **MVP Criteria** – user can submit a problem and inspect ranked candidates + provenance.
  - **Resource Awareness** – explicit tracking of costs/resources.
- See `docs/design.md`:
  - **Feature: Run Configuration & Execution Pipeline** – user-triggered runs.
  - **Design Principles** – resource awareness and transparency.

## Alignment with Design
- Int Crucible’s pipeline (Designers, ScenarioGenerator, Evaluators, I-Ranker) can be **expensive** in both tokens and compute.
- This story codifies a clear UX and backend contract:
  - The Architect acts as an **advisor** for runs (what to run, with which parameters).
  - The **user explicitly starts runs** via the Run Config UI.
  - No runs are ever started “behind the scenes” from chat alone.

## Problem Statement
Without a clear run contract:

1. It is easy for an over-eager agent to start runs implicitly based on chat instructions (e.g., “Go ahead and run it”), potentially incurring unintended cost.
2. Users might not understand when and why a run was executed.
3. There is no explicit separation between:
   - **Deciding what to run** (Architect guidance).
   - **Authorizing execution** (user clicking a button).

We want:
- The Architect to **propose and explain** run configurations.
- The user to **always** authorize execution from the UI (Run button).
- Clear logging around run recommendations and run execution events.

## Acceptance Criteria
- **Architect behavior in chat**:
  - When the user expresses intent to run the pipeline (e.g., “I’d like to run this”):
    - The Architect recommends:
      - A run `mode` (e.g., `full_search`, `eval_only`, `seeded`).
      - Key configuration parameters (e.g., candidate/scenario counts, budget).
    - The Architect clearly states that:
      - It **cannot** start runs directly.
      - The user should click the **Run** button in the Run Config panel to actually execute.
  - Architect suggestions and explanations are:
    - Stored as `agent` messages in `crucible_messages`.
    - Include structured metadata for `recommended_run_config`.

- **RunConfig / pipeline execution behavior**:
  - Runs are only created and executed via:
    - Explicit UI actions in the Run Config panel (e.g., “Run full pipeline”).
    - Corresponding backend endpoints (`/runs`, `/runs/{id}/full-pipeline`, etc.).
  - There is **no code path** where a chat-only API call can create and execute a run without an explicit UI action.

- **Pre-run validation and guidance**:
  - If the user asks the Architect to “run now” without required prerequisites (e.g., missing ProblemSpec/WorldModel):
    - The Architect explains what is missing and how to fix it.
    - It does **not** attempt to start a run.
  - The Architect may suggest:
    - “Once you’ve generated a WorldModel, open the Run panel and click Run with X settings.”

- **Post-run summaries in chat**:
  - When a run completes:
    - The system (via a background process or polling) can post a **summary** Architect message to the chat for that project:
      - Run ID, mode, high-level results (e.g., top candidate(s) and their I-scores).
      - Links or prompts to explore results in the UI.
  - These summary messages are:
    - Clearly labeled as post-run summaries.
    - Logged with metadata referencing `run_id`.

- **Logging and transparency**:
  - It is possible to reconstruct from the database:
    - Which Architect message(s) recommended a given run configuration.
    - Which explicit UI action actually triggered the run (via run timestamps and, if desired, an `issue` or `audit` log later).
  - No run exists without a clear user action in the UI.

## Tasks
- **Backend**:
  - [ ] Ensure no existing agent or service endpoint can create/execute runs **without** going through the explicit run APIs.
  - [ ] Extend Architect/Guidance responses to include:
    - A `recommended_run_config` object in `message_metadata` when the user asks about running.
  - [ ] Persist the recommending `message_id` and structured config metadata so runs can be traced back to the originating chat guidance.
  - [ ] When `/runs` APIs create a run, capture the explicit UI trigger (`user_action_id`, timestamp) and optionally reference the `recommended_run_config` used.
  - [ ] Optionally, provide an endpoint to:
    - Pre-validate a proposed run configuration and return any blockers (e.g., missing ProblemSpec/WorldModel).
  - [ ] Emit a post-run summary Architect message (with `run_id`, mode, key scores) once a pipeline finishes.

- **Frontend**:
  - [ ] In the chat UI:
    - Render Architect recommendations about runs in a clear, concise way (e.g., summary plus an explanation).
    - Visually differentiate Architect post-run summaries and link to the run details/results view.
  - [ ] In the Run Config panel:
    - Allow pre-filling fields from the most recent `recommended_run_config` (where appropriate).
    - Make it visually obvious when the config is “Architect-suggested”.
  - [ ] Explicitly keep the Run button as the only way to start the pipeline from the UI.

- **UX & messaging**:
  - [ ] Tune Architect phrasing so it:
    - Encourages the user to run when appropriate.
    - Makes the explicit-click requirement clear.
  - [ ] Ensure that error messages for missing prerequisites or invalid configs are:
    - Shown both in the Run Config panel.
    - Communicated by the Architect when asked in chat.

- **Browser testing and UI verification**:
  - [ ] **CRITICAL**: Use browser tools to test the implementation in the live UI:
    - Start the frontend and backend servers.
    - Navigate to the chat interface and Run Config panel.
    - Test run recommendation flow:
      - Ask Architect to run the pipeline in chat.
      - Verify Architect recommends config but states it cannot start runs directly.
      - Verify recommended config appears in Run Config panel (if applicable).
      - Verify Run button is the only way to start execution.
    - Test error handling:
      - Ask to run without prerequisites and verify Architect explains what's missing.
      - Verify error messages appear in both chat and Run Config panel.
    - Test post-run summaries:
      - Execute a run and verify summary appears in chat when complete.
      - Verify summary is properly labeled and linked.
    - Verify the UI is elegant, functional, and matches the acceptance criteria.
    - Fix any issues found during browser testing before proceeding to sign-off.

- **Sign-off**:
  - [ ] Test flows where:
    - The user asks the Architect to run, then clicks the Run button.
    - The user asks to run but prerequisites are missing.
  - [ ] Confirm:
    - No runs are created without explicit UI action.
    - Architect recommendations and post-run summaries are properly logged and cross-referenced with `run_id`.
  - [ ] User must sign off on the run advisor contract before this story can be marked complete.

## Implementation Plan

### Backend — Data Model & Audit Trail
- Extend `crucible/db/models.Run` with optional fields for `recommended_message_id` (FK to `crucible_messages.id`), `recommended_config_snapshot` (JSON), `ui_trigger_id`, `ui_trigger_source` (enum like `run_config_panel`/`api`), `ui_trigger_payload` (JSON for client metadata), and `run_summary_message_id`. Ship an Alembic migration plus repository updates so `create_run()` and `RunResponse` surface the new fields.
- Update `crucible/db/repositories.create_run` and `crucible/services/run_service.RunService` to accept the new metadata, enforce that `recommended_message_id` belongs to the same project/chat, and stamp a server-side `ui_triggered_at = datetime.utcnow()`. Add lightweight helpers for attaching/extracting this audit record.
- Introduce a `log_run_summary_message()` helper inside `crucible/services/run_service.py` (or a new `run_summary_service.py`) that takes a completed run plus ranking output, creates a `crucible_messages` entry with `message_metadata.run_summary = {..., run_id}` and stores that message id back onto the run.

### Backend — Guidance & Messaging Contract
- Enhance `GuidanceService` / `guidance_agent` so when `guidance_type == "run_recommendation"` it assembles a structured `recommended_run_config` object (mode, candidate & scenario counts, budget estimate, prerequisite checklist, rationale, timestamp). Inject this into the Architect message metadata and ensure the natural-language body contains (1) the recommendation summary, (2) explicit “I cannot press Run—use the Run panel” copy.
- When prerequisites are missing, populate `recommended_run_config.status = "blocked"` plus `blockers: ["world_model_missing"]` so both chat and UI can surface the same message. Wire `GuidanceService` to reuse the new backend preflight validator to keep chat + Run Config error messaging aligned.
- After `RunService` finishes a pipeline, call the new summary helper to post a labeled Architect message whose metadata includes `run_summary` (run_id, mode, counts, top candidates with I-scores, links) so chat history shows provenance for every execution.

### Backend — API & Validation Flow
- Expand `RunCreateRequest` to accept `chat_session_id`, `recommended_message_id`, `ui_trigger_id`, and `ui_trigger_source`. Reject requests without a `ui_trigger_id` (so scripted API calls must still simulate an explicit action) and verify the referenced chat session belongs to the supplied project.
- Add a lightweight pre-validation endpoint (e.g., `POST /projects/{project_id}/runs/preflight`) that invokes `crucible/services/run_verification.py` plus new config heuristics to return `{ready: bool, blockers: [], warnings: [], normalized_config}`. The Run Config panel will poll this endpoint before enabling `Start Run`, and the Architect can reuse it for precise guidance messaging.
- Ensure `/runs/{run_id}/full-pipeline` (and partial phase endpoints) call `RunService` variants that (a) update `recommended_config_snapshot` on the run when overrides are supplied, (b) emit run summary messages, and (c) never auto-create runs—only operate on ids created via `/runs`.

### Frontend — Chat + Run Config UX
- Teach `ChatInterface.tsx` to detect `message_metadata.recommended_run_config` and render a highlighted “Architect Run Recommendation” card summarizing mode + parameters, blocker status, and a CTA button (“Use these settings”) that calls a new callback prop to share the payload with the Run Config panel. Do the same for `message_metadata.run_summary`, showing a labeled post-run card with a “View results” button that opens the results modal for that `run_id`.
- Lift a `runConfigDraft` state into `app/page.tsx` (or context) so both `ChatInterface` and `RunConfigPanel` can read/write the latest architect suggestion. Pass `initialConfig`, `isArchitectSuggested`, and `recommendedMessageId` into `RunConfigPanel`.
- Update `RunConfigPanel.tsx` to (1) prefill inputs from the shared draft, (2) show a badge when the active form matches an Architect suggestion, (3) call the new `/preflight` endpoint before enabling `Start Run`, and (4) send `chat_session_id`, `recommended_message_id`, and a generated `ui_trigger_id` to `runsApi.create`. If preflight reports blockers, surface them inline and keep the Run button disabled while also nudging the chat to explain.
- Extend `frontend/lib/api.ts` with helpers for the preflight endpoint plus the new request fields, and wire `ResultsView` / overlays so clicking “View results” from chat focuses the appropriate run.

### Testing & Verification
- Add backend unit tests covering: (a) `RunService` rejecting missing prerequisites at create time, (b) metadata persistence on runs, and (c) post-run summary messages (see `tests/unit/services/test_run_service.py` and `tests/unit/agents/test_guidance_agent.py`). Add an integration test ensuring `/runs` cannot be invoked without a `ui_trigger_id`.
- Extend frontend tests (React Testing Library) to simulate receiving a `recommended_run_config` message, confirm the card renders, and verify clicking “Use these settings” prefills the Run Config panel without auto-starting a run.
- Update the manual/browser checklist (story tasks) to cover the new cards, prefill behavior, error handling, and logging traceability. Tie these tests into the existing verification guide so QA can confirm no run is possible without explicit UI action.

### Proposed Metadata Schema

**Architect recommendation payload (`message_metadata.recommended_run_config`):**
- `version` (int, default `1`) for forward compatibility.
- `recommendation_id` (UUID) so UI and backend can reference the same suggestion.
- `project_id`, `chat_session_id`, `source_message_id`.
- `generated_at` (ISO timestamp) and optional `expires_at`.
- `status`: enum `ready`, `blocked`, `info`. `blocked` requires a `blockers` array such as `["missing_problem_spec", "missing_world_model"]`.
- `mode`: mirrors `RunMode` enum.
- `parameters`: `{ "num_candidates": int, "num_scenarios": int, "seed_candidate_ids": string[], "budget_tokens": int | null, "budget_usd": float | null, "max_runtime_s": int | null }`.
- `prerequisites`: `{ "problem_spec": bool, "world_model": bool, "seed_candidates": bool }`.
- `estimated_cost`: `{ "tokens": int | null, "usd": float | null }`.
- `rationale`: short paragraph displayed in chat UI.
- `notes`: optional bullet list for UI to render tooltips.
- `blockers`: array of codes (see `RunBlockerCode` enum below) plus optional `details` map for rich messages.

**Run audit columns (`crucible_runs` additions):**
- `recommended_message_id` (FK → `crucible_messages.id`, nullable).
- `recommended_config_snapshot` (JSON, stored copy of the `recommended_run_config` at the time of run creation).
- `ui_trigger_id` (string, required, UUID supplied by frontend).
- `ui_trigger_source` (enum `RunTriggerSource` with values `run_config_panel`, `api_client`, `integration_test`, `cli_tool`).
- `ui_trigger_metadata` (JSON blob with browser info, user id, etc.).
- `ui_triggered_at` (UTC timestamp, default `now()`).
- `run_summary_message_id` (FK → `crucible_messages.id` for the post-run summary).

**Post-run summary payload (`message_metadata.run_summary`):**
- `run_id`, `project_id`, `mode`, `status`.
- `started_at`, `completed_at`, `duration_seconds`.
- `counts`: `{ "candidates": int, "scenarios": int, "evaluations": int }`.
- `top_candidates`: array of up to 3 entries `{ "candidate_id": str, "label": str, "I": float, "P": float | null, "R": float | null, "notes": str | null }`.
- `links`: `{ "results_view": "/runs/{run_id}", "download": optional }` so the frontend can deeplink without inference.
- `summary_label`: e.g., “Run CR-123 summary” to ensure the chat clearly marks these messages.

**Run preflight response (`POST /projects/{project_id}/runs/preflight`):**
- Request: `{ "mode": RunMode, "parameters": { ... }, "chat_session_id": str | null, "recommended_message_id": str | null }`.
- Response: `{ "ready": bool, "blockers": RunBlockerCode[], "warnings": RunWarningCode[], "normalized_config": { ... }, "prerequisites": { ... }, "notes": [] }`.

**Enumerations:**
- `RunTriggerSource = Enum("run_config_panel", "api_client", "integration_test", "cli_tool")`.
- `RunBlockerCode = Enum("missing_problem_spec", "missing_world_model", "insufficient_candidates", "validation_error")`.
- `RunWarningCode = Enum("high_budget", "large_candidate_count", "deprecated_mode")`.

These schemas should be defined centrally (e.g., `crucible/services/run_service.py` or a new `crucible/models/run_contract.py`) and reused by both backend responses and frontend TypeScript types to prevent drift.

## Implementation Breakdown

### Backend Subtasks
1. **Database migration (alembic)**: Extend `crucible_runs` with the audit columns above, add enums (`RunTriggerSource`, blocker/warning enums if stored), and ensure new fields default safely for existing rows. Update SQLAlchemy models plus repository dataclasses.
2. **Repositories & models**: Update `crucible/db/models.py` and `crucible/db/repositories.py` to accept/persist the new metadata. Add helper dataclasses/utilities (e.g., `RunRecommendationSnapshot`) so services and API handlers can serialize/deserialize consistently.
3. **Run creation API**: Modify `RunCreateRequest` and `/runs` handler in `crucible/api/main.py` to require `ui_trigger_id`, validate optional `chat_session_id`/`recommended_message_id`, and hydrate `recommended_config_snapshot`.
4. **Preflight endpoint**: Add `POST /projects/{project_id}/runs/preflight` that calls a new `RunPreflightService` (wrapping `run_verification` + heuristics) and returns the standardized response envelope. Reuse same logic inside `GuidanceService` when generating recommendations.
5. **Guidance agent integration**: In `crucible/services/guidance_service.py` and `guidance_agent.py`, detect run-intent queries, call the preflight helper, and populate `recommended_run_config` metadata + natural-language copy (including explicit “use Run button” reminder).
6. **Run execution logging**: Enhance `RunService.execute_*` to stamp `recommended_config_snapshot`, emit a post-run summary message via a new helper, and persist `run_summary_message_id`. Ensure summary generation is idempotent and handles failures gracefully.
7. **Audit utilities/tests**: Add unit/integration tests around the migration, preflight response, `/runs` validator, and post-run summary creation (`tests/unit/services/test_run_service.py`, `tests/integration/test_run_contract.py`).

### Frontend Subtasks
1. **Shared state plumbing**: In `app/page.tsx`, introduce `runConfigDraft` (with metadata + status) and pass setters into `ChatInterface` and `RunConfigPanel`.
2. **Chat UI cards**: Update `ChatInterface.tsx` (and maybe `MessageContent.tsx`) to render two new components:
   - `RunRecommendationCard` that shows the structured config, blockers, rationale, and a “Use these settings” CTA (calling the shared state setter).
   - `RunSummaryCard` that shows post-run highlights with a button to open `ResultsView` for `run_id`.
3. **Run Config panel**: Teach `RunConfigPanel.tsx` to accept `initialConfig`, `recommendedMessageId`, and `isArchitectSuggested`. Prefill fields, highlight when using a suggestion, and display blockers/warnings from the preflight response inline above the Run button.
4. **API client updates**: Extend `frontend/lib/api.ts` with types for the metadata schema, support `runsApi.preflight`, and allow `runsApi.create` to send the new fields (`chat_session_id`, `recommended_message_id`, `ui_trigger_id`, `ui_trigger_source`).
5. **UX safeguards**: Disable the Run button unless preflight `ready === true`, show error banners that mirror the backend `blockers`, and ensure the UI never calls `/runs/{run_id}/full-pipeline` unless the run was created via the button click.
6. **Tests**: Add component tests (React Testing Library) for the new cards and Run Config panel states (blocked vs ready), plus Cypress/manual scripts covering the acceptance scenarios.

## Work Log

### 20251120-1756 — Story build prep
- **Result:** Success; reviewed acceptance criteria and expanded backend/frontend tasks covering audit metadata and post-run summaries.
- **Notes:** Story doc now calls out data linkage between chat recommendations, UI triggers, and run completions; no implementation work has begun.
- **Next:** Flesh out backend data model adjustments (message metadata + run triggers) and coordinate UI/Agent design for surfaced summaries.

### 20251120-1801 — Implementation plan detailing
- **Result:** Success; documented backend schema/runtime changes, API validation flow, architect messaging contract, and frontend UX sharing plan between chat + Run Config.
- **Notes:** Plan now references concrete files (`crucible/db/models.py`, `crucible/api/main.py`, `frontend/components/ChatInterface.tsx`, etc.) and defines metadata shapes so future implementers know what to persist/render.
- **Next:** Align with stakeholders on the recommended metadata schema (fields + enums) before starting migrations, then split the work into backend/fronted subtasks.

### 20251120-1804 — Metadata schema alignment
- **Result:** Success; captured the exact structures (fields, enums, response shapes) for architect recommendations, run audit records, post-run summaries, and preflight validation so both backend and frontend can implement against the same contract.
- **Notes:** Section highlights where to host shared definitions plus blocker/warning enumerations for UI copy.
- **Next:** Circulate schema with stakeholders for approval, then proceed to define backend/TS types and migrations.

### 20251120-1809 — Implementation breakdown
- **Result:** Success; decomposed Story 016 into concrete backend and frontend subtasks referencing the key files/services (migrations, repositories, guidance service, Chat UI, Run Config panel).
- **Notes:** Breakdown separates schema work, API hooks, UX changes, and testing so multiple contributors can parallelize.
- **Next:** Sequence these subtasks (migrations → backend APIs → frontend wiring) and assign owners/timelines.

## Execution Roadmap

1. **Phase 1 – Schema & Contracts (Backend lead)**
   - Implement Alembic migration + SQLAlchemy/repository updates.
   - Land shared Python dataclasses/enums for recommendation, trigger, summary, and blocker metadata.
   - Deliverables: migration merged, updated `Run` model + repository helpers, contract module published.
2. **Phase 2 – API & Agent Enforcement (Backend lead, Guidance owner)**
   - Update `/runs` create + new `/preflight` endpoint, integrate with `RunService`, `RunVerification`, and `GuidanceService`.
   - Ensure post-run summary messages and audit logging fire reliably (unit/integration tests passing).
   - Deliverables: endpoints behind feature flag (if needed), tests green, guidance responses emitting metadata.
3. **Phase 3 – Frontend Wiring (Frontend lead)**
   - Share run-config state between chat and Run Config panel, render recommendation/summary cards, gate Run button on preflight/trigger data.
   - Deliverables: UI cards, prefilled Run Config state, API client updates, component tests.
4. **Phase 4 – End-to-End Verification (QA/owner)**
   - Manual/browser checklist from story tasks, plus optional Cypress smoke covering the advisor contract.
   - Verify audit trail in DB (run record links to recommendation + UI trigger; summary messages present).

Dependencies: Phase 2 depends on Phase 1 contracts; Phase 3 can start once Phase 2 exposes stable APIs; Phase 4 requires all features merged.

### 20251120-1813 — Roadmap planning
- **Result:** Success; sequenced Story 016 subtasks into four phases with clear dependencies and owners.
- **Notes:** Provides a playbook for coordinating contributors plus QA expectations.
- **Next:** Kick off Phase 1 (schema/migration PR) and align owners per phase.

### 20251120-1935 — Phase 3 UI & client wiring
- **Result:** Implemented the shared run-config draft flow (chat → Run Config panel), rendered Architect recommendation/summary cards, and extended the frontend API client plus Run Config panel gating to honor preflight + UI trigger requirements.
- **Notes:** Chat emits callbacks when metadata arrives; Run Config panel now preloads architect suggestions, surfaces blockers/warnings from `/preflight`, and sends the new metadata when creating runs.
- **Next:** Proceed to Phase 4 verification to validate the full-story acceptance criteria.

### 20251121-0010 — Phase 4 verification
- **Result:** Added targeted unit tests for `RunPreflightService` (blockers/warnings) and `RunService` (post-run summary messages + prerequisite failures) and executed `pytest tests/unit/services/test_run_preflight_service.py tests/unit/services/test_run_service_improvements.py`.
- **Notes:** Automated coverage validates the backend contract; UI/browser verification still pending once servers can be exercised interactively.
- **Next:** Schedule manual/browser QA to exercise the Run button flow and confirm recommendation/summary cards in a live environment.


