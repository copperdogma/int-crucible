# Story: Implement WorldModeller and live spec/world-model view

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – WorldModeller (MVP), Provenance tracker.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Live Spec / World-Model View** – live spec panel and structured world model.
  - **Feature: Chat-First Project & ProblemSpec Modelling** – world model derived from ProblemSpec and chat.

## Acceptance Criteria
- A WorldModel structure exists in the backend (actors, mechanisms, resources, constraints, assumptions, simplifications).
- The backend can generate/update the WorldModel from the ProblemSpec using a WorldModeller agent.
- The UI shows:
  - A human-readable spec panel (Objectives, Constraints, Actors, Assumptions & Simplifications).
  - The ability to view/edit the spec and see corresponding updates in the underlying WorldModel.
- WorldModel changes are tracked with basic provenance information (who/what changed what and when).
- The system can reach a consistent “ready to run” state where ProblemSpec and WorldModel are aligned.
- User signs off that the spec/world-model view is usable enough for MVP.

## Tasks
- [ ] Define the WorldModel JSON structure and how it is stored in the database.
- [ ] Implement a Kosmos-based WorldModeller agent that:
  - [ ] Takes ProblemSpec + relevant chat history as input.
  - [ ] Proposes additions/updates/removals in the WorldModel.
- [ ] Implement backend endpoints/services to:
  - [ ] Retrieve and update the WorldModel for a project.
  - [ ] Apply WorldModeller suggestions, including provenance entries.
- [ ] Implement the UI components for the live spec panel (front-end):
  - [ ] Render Objectives, Constraints, Actors, Assumptions/Simplifications from WorldModel/ProblemSpec.
  - [ ] Allow user edits and show updates reflected in structured data.
- [ ] Implement a simple mapping layer between the textual spec and the WorldModel JSON.
- [ ] Add tests or a demo flow showing ProblemSpec → WorldModel refinement loop.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The WorldModeller should aim for “usable but not exhaustive” models; it is acceptable to leave less-critical details out for the MVP as long as scenario generation and evaluation can proceed.


