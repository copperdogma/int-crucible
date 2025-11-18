# Story: Implement provenance and candidate lineage

**Status**: To Do

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
- [ ] Define the provenance log structure for candidates and world-model entries (type, actor, timestamp, description, references).
- [ ] Extend the Candidate and WorldModel schemas to store parent relationships and provenance logs.
- [ ] Update Designer, WorldModeller, Evaluator, I-Ranker, and Feedback agents to emit provenance events at key steps.
- [ ] Implement backend functions to query provenance for a given candidate or project.
- [ ] Implement a basic lineage view in the UI (textual list of events with parent relationships; graphical view can be deferred).
- [ ] Add tests or sample runs demonstrating that provenance and lineage are recorded and retrievable for a run.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The provenance design should keep compatibility with future graph-based visualization and potential reuse of Kosmos’s knowledge/provenance machinery.


