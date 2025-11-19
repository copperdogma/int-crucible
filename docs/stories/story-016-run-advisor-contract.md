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
  - [ ] Optionally, provide an endpoint to:
    - Pre-validate a proposed run configuration and return any blockers (e.g., missing ProblemSpec/WorldModel).

- **Frontend**:
  - [ ] In the chat UI:
    - Render Architect recommendations about runs in a clear, concise way (e.g., summary plus an explanation).
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

- **Sign-off**:
  - [ ] Test flows where:
    - The user asks the Architect to run, then clicks the Run button.
    - The user asks to run but prerequisites are missing.
  - [ ] Confirm:
    - No runs are created without explicit UI action.
    - Architect recommendations and post-run summaries are properly logged and cross-referenced with `run_id`.
  - [ ] User must sign off on the run advisor contract before this story can be marked complete.


