# Story 018: AI-first test pipeline and snapshot-based scenarios

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **MVP Criteria** – system can run a complete end-to-end loop and be applied to improving Int Crucible itself.
  - **Transparency and provenance** – ability to inspect how outputs were produced.
  - **Resource awareness** – explicit tracking of costs/resources.
- See `docs/design.md`:
  - **Architecture Overview** – modular monolith with well-defined pipeline phases.
  - **Feature: Run Configuration & Execution Pipeline** – ProblemSpec → WorldModel → Designers → ScenarioGenerator → Evaluators → I-Ranker.
  - **Feature: Run-Time Views & Feedback** – post-run exploration and issue handling.

## Alignment with Design
- This story treats **Int Crucible itself as a system under test that is exercised and maintained by AI agents**:
  - The entire pipeline (backend + frontend APIs) should be runnable and verifiable by AI without manual intervention.
  - Instead of deterministic, brittle tests, we rely on:
    - Structured invariants and health checks.
    - Snapshot-based scenarios that can be replayed to reproduce issues.
    - AI-driven analysis and debugging using those snapshots.
- It builds on:
  - Story 008b (test tooling and run verification).
  - Story 008 (provenance and lineage).
  - Story 019 (observability and metrics).

## Problem Statement
Traditional TDD and unit-testing are ill-suited here because:

1. **All core reasoning is done by LLMs**, which are:
   - Non-deterministic.
   - Sensitive to prompt/model changes.
   - Expensive to call at high volume.
2. We still need **high-confidence guardrails** as the system evolves, especially if:
   - AI agents are making code changes.
   - AI agents are responsible for verification and regression detection.
3. Current tests (unit + integration + `test_run`) focus on:
   - Plumbing correctness.
   - Basic invariants around runs, candidates, and evaluations.
   - They do **not** provide:
   - A reusable library of “interesting” real-world problem snapshots.
   - A consistent way for AI agents to **create, store, and replay** those snapshots when debugging.

We want:
- An **AI-first test pipeline** that:
  - Lets AI (and humans) run curated end-to-end scenarios.
  - Captures **snapshots** of system state around failures or surprising behaviors.
  - Provides tools for AI agents to:
    - Re-run from snapshots.
    - Compare before/after behavior.
    - Decide whether a change is a regression or improvement based on high-level invariants.

## Acceptance Criteria
- **Snapshot representation and storage**:
  - There is a first-class notion of a **test snapshot** that includes:
    - Project ID and metadata (title, description).
    - Key artifacts: ProblemSpec, WorldModel, and at least one Run (or run config).
    - Minimal chat history necessary to recreate the context (optional but preferred).
    - Recorded metrics for the reference run (candidate count, scenario count, evaluations, status, basic P/R/I stats).
  - Snapshots are stored in a form that:
    - Can be **listed, inspected, and re-used** (e.g., `crucible_snapshots` table or tagged runs/projects).
    - Is stable under normal schema evolution (JSON payloads with version tags are acceptable).

- **Snapshot creation tools (AI-accessible)**:
  - API/CLI tools exist to:
    - Create a snapshot from an existing project/run (e.g., “capture this as snapshot X”).
    - Attach a short natural language description of what the snapshot tests (e.g., “Chat-first UI spec modelling with heavy constraints”).
  - These tools are available to AI agents via:
    - Well-documented HTTP endpoints.
    - Clearly shaped responses (IDs, descriptions, linked resources).

- **Snapshot replay / re-run**:
  - For each snapshot, there is a **replay mechanism** that:
    - Re-runs the pipeline (or selected phases) from the stored ProblemSpec/WorldModel and run config.
    - Does **not** rely on the original chat interaction to be replayed exactly.
  - Replay does **not** guarantee identical candidate content or scores, but it must:
    - Successfully complete the pipeline without errors.
    - Satisfy agreed high-level invariants (see below).

- **AI-first invariants and regression checks**:
  - For each snapshot, we can define **invariants** such as:
    - “At least N candidates are generated.”
    - “No hard constraints are silently ignored (violations are correctly flagged).”
    - “Run status ends in COMPLETED, not FAILED.”
    - “Top candidate I-score remains within a reasonable band (e.g., > 0.3).”
  - A small verification harness (CLI or API) can:
    - Run snapshot scenarios and check invariants.
    - Return a structured pass/fail report that an AI agent can interpret.

- **Automation entrypoint for AI agents**:
  - A single “AI test pipeline” entrypoint exists (CLI and/or API) that:
    - Accepts a list of snapshot IDs (or all snapshots) to run.
    - Executes each snapshot with invariants.
    - Produces a **machine-readable report**:
      - For each snapshot: pass/fail, violated invariants, metrics deltas, and basic summaries.
  - This entrypoint is:
    - Idempotent.
    - Safe to run frequently.
    - Bounded in cost (configurable selection of snapshots, max runs, etc.).

## Tasks
- **Snapshot model & storage**:
  - [ ] Design a `Snapshot` concept:
    - Either a dedicated table (e.g., `crucible_snapshots`) or a convention over existing entities.
    - Fields: `id`, `project_id`, optional `run_id`, `description`, `created_at`, `snapshot_data` (JSON), `version`.
  - [ ] Implement repository/helpers to:
    - Create, list, and fetch snapshots.
    - Serialize/deserialize the snapshot_data payload.

- **Snapshot creation tooling**:
  - [ ] Add API/CLI commands, e.g.:
    - `POST /snapshots` – create from `{ project_id, run_id?, description }`.
    - `GET /snapshots` and `GET /snapshots/{id}` – list and inspect.
  - [ ] Include enough context in `snapshot_data` to re-run the pipeline without the original chat:
    - ProblemSpec, WorldModel, run config, and relevant IDs.

- **Replay and invariants**:
  - [ ] Implement a replay helper that:
    - Creates a new run based on snapshot data.
    - Executes the pipeline (full or partial) against that run.
  - [ ] Define a small set of **generic invariants** applicable to most snapshots:
    - Pipeline completes without exceptions.
    - Candidate/scenario/evaluation counts exceed minimum thresholds.
    - No obvious structural regressions (e.g., empty constraints, missing scores).
  - [ ] Represent invariants as data (JSON) attached to snapshots so AI agents can:
    - Read them.
    - Potentially propose new invariants in the future.

- **AI-facing test harness**:
  - [ ] Expose a `POST /snapshots/run-tests` (or similar) endpoint that:
    - Accepts a list of snapshot IDs and test options (max snapshots, phases to run, etc.).
    - Returns structured pass/fail results and basic metrics.
  - [ ] Optionally add a CLI command (e.g., `crucible snapshot-tests`) that a human or AI-in-CLI can call.

- **Documentation & patterns**:
  - [ ] Document:
    - How to create snapshots.
    - How invariants are defined and interpreted.
    - How AI agents should use this pipeline for regression testing.
  - [ ] Provide at least 2–3 concrete example snapshots in docs (e.g., focused on chat-first UI, heavy constraints, and a failure-mode scenario).

- **Sign-off**:
  - [ ] Demonstrate:
    - Creating a snapshot from a “good” run.
    - Running snapshot tests before and after a non-trivial change.
    - Showing how an AI (or human) could see a regression in the snapshot test report.
  - [ ] User must sign off that the AI-first testing loop is usable and provides real value, even with non-deterministic LLM outputs.

## Priority and Timing Notes
- **Essentiality**:
  - For a **human-driven MVP**, this is **nice-to-have but not strictly required**.
  - For a future where **AI agents are doing “ALL the work AND verification”**, this becomes **foundational**:
    - It’s how AI gets reliable feedback about regressions without deterministic outputs.
    - It underpins safe, iterative AI-led refactoring of the system.
- **Recommended timing**:
  - Implement **after**:
    - Core pipeline stories (003–006) and run verification (002b, 008b) are solid.
    - Provenance (008) and observability (019) provide basic structure and metrics.
  - In practice: schedule 018 shortly after 019, once the system is stable enough that captured snapshots will remain meaningful as you iterate.


