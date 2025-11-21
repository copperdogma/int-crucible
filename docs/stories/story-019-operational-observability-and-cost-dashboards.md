# Story 019: Operational observability and cost dashboards

**Status**: Done  

---

## Related Requirement
- See `docs/requirements.md`:
  - **Fundamental Principles – Resource awareness** – track and reason about resources/costs (the \(R\) in \(I = P/R\)).
  - **Transparency and provenance** – expose how outputs were produced, including assumptions and resource usage.
- See `docs/design.md`:
  - **Architecture Overview – Backend API + Orchestration Engine** – logging and persistence.
  - **Migrations & setup** – shared DB and Kosmos logging infrastructure.

## Alignment with Design
- The system already:
  - Tracks P, R, and I scores per candidate.
  - Logs run status and basic statistics (via CLI `test_run` and backend logging).
- This story focuses on **operational visibility** for a single technical user (and AI agents) by:
  - Making **run-level metrics**, errors, and resource usage easy to inspect.
  - Providing basic dashboards or views so humans and AI can:
    - See which runs succeeded/failed and why.
    - Understand rough token / cost usage per run or per phase (if available).
    - Spot performance regressions or anomalies.

## Problem Statement
Currently:

1. Run execution details are primarily visible via:
   - Logs.
   - Ad-hoc CLI output from `crucible test-run`.
2. There is no consolidated, structured view of:
   - Run history and statuses across projects.
   - Approximate LLM usage/cost per run or phase.
   - Error patterns over time.
3. As Int Crucible becomes more complex (and as AI agents operate it), it becomes harder to:
   - Quickly diagnose pipeline issues.
   - Estimate or control cost impact of runs.
   - Provide AI agents with the context they need to reason about operational health.

We want:
- A **lightweight observability layer** and simple “dashboards” (CLI and/or UI) that show:
  - Recent runs, their durations, statuses, and candidate counts.
  - Basic error summaries.
  - Optional approximate token/cost metrics where available.

## Acceptance Criteria
- **Backend: metrics & logging data model**:
  - Run records (`crucible_runs`) and/or related tables expose:
    - `duration_seconds` (or equivalent), derived from timestamps, plus persisted `candidate_count`, `scenario_count`, and `evaluation_count` so summaries do not need to re-scan child tables.
    - A `metrics` JSON payload with a documented contract: `phase_timings` (per-phase start/duration), `resource_breakdown` (e.g., calls made, retries), and optional `notes`.
    - An `llm_usage` JSON payload (when data from Kosmos providers exists) that records prompt/output tokens, estimated cost (USD), and the provider/model names per phase.
    - A short text `error_summary` column for failed/partial runs.
  - A small set of **well-defined log/metric fields** is documented so both humans and AI agents can interpret them and compute the `R` portion of \(I = P/R\).

- **API / CLI: observability surfaces**:
  - CLI:
    - `crucible test-run` (or a new `crucible runs` command) can:
      - List recent runs with status, duration, and basic counts (candidates, scenarios, evaluations).
      - Show a short error summary for failed runs.
      - Filter by project, status, and time window, and support both table output and a `--format json` option for AI/automation.
  - API:
    - A `GET /projects/{project_id}/runs/summary` (or similar) endpoint returns:
      - Recent runs with status, created/started/completed timestamps, duration, candidate/scenario/evaluation counts, and any recorded `metrics`/`llm_usage`.
      - Supports pagination (`limit`/`cursor` or `page`), optional status filters, and returns deterministic field names documented for AI use.

- **Frontend: basic run history view**:
  - Within the project UI (can be part of or adjacent to Run Config / Results):
    - A “Run History” table shows:
      - Run ID (or short label), status, created_at, duration.
      - Candidate count, scenario count, evaluation count (if available).
      - Status badges and pills for failure/success, and inline indicators when metrics data is missing.
    - Clicking a run row opens a simple detail view with:
      - Phase timings (if available).
      - Any recorded error summary.
      - Links to open the run’s Results view.
  - The view is **read-only** and focused on clarity, not heavy analytics.

- **Error and health visibility**:
  - For failed runs:
    - A short, human-readable `error_summary` is recorded and exposed via CLI/API/UI.
    - The Run History view clearly indicates failure and links to the error summary.
  - The system makes it easy to answer:
    - “Which run failed most recently and why?”
    - “Roughly how long do runs take and how many candidates/evaluations are being produced?”

- **AI-consumable observability**:
  - At least one endpoint (or CLI command) is simple enough that an AI agent can:
    - Read recent runs and their statuses.
    - Detect anomalous patterns (e.g., many FAILED runs).
    - Use this information in higher-level automation stories later (e.g., auto-triage).
  - The same structured response can be retrieved without ANSI/Rich formatting (pure JSON) and is documented with an explicit schema snippet.

## Tasks
- **Backend: metrics & schema**:
  - [ ] Add an Alembic migration that introduces `duration_seconds`, `candidate_count`, `scenario_count`, `evaluation_count`, `metrics`, `llm_usage`, and `error_summary` columns (or equivalent) to `crucible_runs`.
  - [ ] Decide where to store run metrics:
    - Either extend `crucible_runs.config` or add a dedicated `metrics` JSON column (migration above reflects the choice).
  - [ ] Update `RunService.execute_full_pipeline` to:
    - Record total duration and per-phase durations consistently.
    - Optionally record LLM usage data if available via Kosmos provider (tokens used per phase, etc.).
    - Persist resource counters (LLM calls, retries) needed for `resource_breakdown`.
  - [ ] Capture `error_summary` automatically from exceptions and ensure it is saved on partial failures.
  - [ ] Ensure metrics are persisted and retrievable for completed and failed runs.
  - [ ] Backfill existing run rows with default values (e.g., zero counts, null metrics) so history pages behave consistently.
  - [ ] Document the `metrics`/`llm_usage` contract in `docs/design.md` (include sample payload).

- **API & CLI**:
  - [ ] Add an API endpoint (e.g., `GET /projects/{project_id}/runs/summary`) that:
    - Returns a concise summary of recent runs and metrics.
    - Accepts pagination + filtering query params and enforces sensible defaults (e.g., last 20 runs).
    - Includes automated tests covering happy path, empty state, and filter handling.
  - [ ] Add/extend CLI commands (`crucible runs` or extend `test_run`) to:
    - List recent runs for a project with key metrics in a table.
    - Show basic error and health information.
    - Offer `--limit`, `--status`, `--project-id`, and `--format json` switches.
    - Include unit/integration tests (Typer command) plus an example snippet in docs.

- **Frontend**:
  - [ ] Add a simple “Run History” component for a project:
    - Table view of runs with key metrics.
    - Link into existing Results view for each run.
    - Loading/empty/error states so operational users know when data is stale or unavailable.
  - [ ] Add a minimal detail view (modal or panel) that:
    - Shows phase timings and error summary (if any).
    - Is easy to scan and does not overwhelm the main UI.
    - Surfaces cost/token usage when present and clearly labels when unavailable.

- **Documentation & usage**:
  - [ ] Document:
    - What metrics are captured.
    - How to read them in CLI and UI.
    - Any limitations (e.g., approximate cost, missing metrics when provider data is unavailable).
    - The JSON schema/field names for API + CLI outputs aimed at AI agents.
  - [ ] Provide at least one documented “operations checklist” example:
    - E.g., steps to inspect a failed run and see metrics from CLI + UI.
    - Include troubleshooting tips (e.g., what to do when `llm_usage` is null because provider omitted telemetry).

- **Sign-off**:
  - [ ] Run several end-to-end pipelines and confirm:
    - Run History shows meaningful metrics.
    - Errors are surfaced clearly.
    - An AI (or human) could use the metrics to reason about operational health.
    - CLI JSON output can be consumed by a simple script/agent to flag anomalies.
  - [ ] User must sign off that observability is sufficient for day-to-day solo use and for AI agents to introspect runs.

## Notes
- This is intentionally **MVP-level observability**:
  - No heavy dashboards, external metrics stores, or alerting systems.
  - Focus is on giving a single technical user and AI agents enough visibility to debug and manage runs.
- Future extensions might include:
  - Exporting metrics to external monitoring (Prometheus, Grafana, etc.).
  - More detailed token/cost tracking and budgeting features.
  - Automated health checks and anomaly detection agents.


## Work Log

### 20251121-1530 — Expanded observability plan
- **Result:** Success; acceptance criteria/tasks now cover schema updates, RunService instrumentation, API/CLI filters, UI states, and AI-consumable outputs.
- **Notes:** Added requirements for metrics payload structure, CLI `--format json`, pagination/filtering, and documentation deliverables so Resource Awareness + Transparency principles stay traceable.
- **Next:** Await approval to start backend migration + RunService logging changes, then proceed to API/CLI surfaces and UI work.

### 20251121-1705 — Implemented schema + surfaces
- **Result:** Success; added Alembic migration, Run model fields, RunService observability plumbing, `/projects/{id}/runs/summary` endpoint, `crucible runs` CLI, and a frontend Run History panel with React Query wiring.
- **Notes:** LLM usage is aggregated per phase + total (if telemetry exists). CLI + API share deterministic filters/pagination. UI modal deep-links into results and exposes phase timings & error summaries.
- **Next:** Monitor QA feedback, tune UI polish, and extend tests if new regressions surface.

