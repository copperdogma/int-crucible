# Story 019: Operational observability and cost dashboards

**Status**: To Do  

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
    - `duration_seconds` (or equivalent), derived from timestamps.
    - Optional `metrics` JSON with phase-level timings (design, scenarios, evaluation, ranking).
    - Optional `llm_usage` JSON for approximate token counts / cost per run (if provider data is available via Kosmos).
  - A small set of **well-defined log/metric fields** is documented so both humans and AI agents can interpret them.

- **API / CLI: observability surfaces**:
  - CLI:
    - `crucible test-run` (or a new `crucible runs` command) can:
      - List recent runs with status, duration, and basic counts (candidates, scenarios, evaluations).
      - Show a short error summary for failed runs.
  - API:
    - A `GET /projects/{project_id}/runs/summary` (or similar) endpoint returns:
      - Recent runs with status, created/started/completed timestamps, duration, candidate/scenario/evaluation counts, and any recorded `metrics`/`llm_usage`.

- **Frontend: basic run history view**:
  - Within the project UI (can be part of or adjacent to Run Config / Results):
    - A “Run History” table shows:
      - Run ID (or short label), status, created_at, duration.
      - Candidate count, scenario count, evaluation count (if available).
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

## Tasks
- **Backend: metrics & schema**:
  - [ ] Decide where to store run metrics:
    - Either extend `crucible_runs.config` or add a dedicated `metrics` JSON column.
  - [ ] Update `RunService.execute_full_pipeline` to:
    - Record total duration and per-phase durations consistently.
    - Optionally record LLM usage data if available via Kosmos provider (tokens used per phase, etc.).
  - [ ] Ensure metrics are persisted and retrievable for completed and failed runs.

- **API & CLI**:
  - [ ] Add an API endpoint (e.g., `GET /projects/{project_id}/runs/summary`) that:
    - Returns a concise summary of recent runs and metrics.
  - [ ] Add/extend CLI commands (`crucible runs` or extend `test_run`) to:
    - List recent runs for a project with key metrics in a table.
    - Show basic error and health information.

- **Frontend**:
  - [ ] Add a simple “Run History” component for a project:
    - Table view of runs with key metrics.
    - Link into existing Results view for each run.
  - [ ] Add a minimal detail view (modal or panel) that:
    - Shows phase timings and error summary (if any).
    - Is easy to scan and does not overwhelm the main UI.

- **Documentation & usage**:
  - [ ] Document:
    - What metrics are captured.
    - How to read them in CLI and UI.
    - Any limitations (e.g., approximate cost, missing metrics when provider data is unavailable).
  - [ ] Provide at least one documented “operations checklist” example:
    - E.g., steps to inspect a failed run and see metrics from CLI + UI.

- **Sign-off**:
  - [ ] Run several end-to-end pipelines and confirm:
    - Run History shows meaningful metrics.
    - Errors are surfaced clearly.
    - An AI (or human) could use the metrics to reason about operational health.
  - [ ] User must sign off that observability is sufficient for day-to-day solo use and for AI agents to introspect runs.

## Notes
- This is intentionally **MVP-level observability**:
  - No heavy dashboards, external metrics stores, or alerting systems.
  - Focus is on giving a single technical user and AI agents enough visibility to debug and manage runs.
- Future extensions might include:
  - Exporting metrics to external monitoring (Prometheus, Grafana, etc.).
  - More detailed token/cost tracking and budgeting features.
  - Automated health checks and anomaly detection agents.


