# Story: Implement feedback loop and issue handling

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Provenance tracker.
  - **Roadmap** – feedback and self-correction are key post-MVP directions; MVP should have a minimal feedback loop.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Feedback Loop on Model, Constraints, and Evaluations** – Feedback agent, Issue objects, rerun strategies.

## Acceptance Criteria
- The user can flag issues from:
  - The live spec/world-model view.
  - A candidate detail view.
- Issues are stored as structured objects with:
  - Type (model / constraint / evaluator / scenario).
  - Severity (minor / important / catastrophic).
  - Status (open / resolved / invalid).
- A Feedback agent can:
  - Ask clarifying questions in chat.
  - Propose remediation actions (patch-and-rescore, partial rerun, full rerun).
- The orchestrator can, at least for MVP:
  - Apply “minor” patches and rescore.
  - Mark candidates as invalidated when catastrophic issues are accepted.
- Issue events and resolutions are recorded in provenance/logs.

## Tasks
- [ ] Define the `Issue` entity (fields for type, severity, links to project/run/candidate, description, status).
- [ ] Implement backend endpoints or functions to create, update, and query issues.
- [ ] Implement a Feedback agent (on Kosmos framework) that:
  - [ ] Takes an issue + relevant context as input.
  - [ ] Asks clarifying questions via chat.
  - [ ] Proposes remediation options.
- [ ] Integrate issue handling into the pipeline orchestration (e.g., partial reruns, invalidation).
- [ ] Implement UI affordances to:
  - [ ] Flag issues from relevant views.
  - [ ] View open/resolved issues for a project/run/candidate.
- [ ] Add tests or sample flows showing issue creation, agent dialogue, and effect on runs/candidates.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This story focuses on a minimal but real feedback loop; advanced self-improvement and meta-evaluation can be handled in later stories/epics.


