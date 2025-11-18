# Story: Implement ProblemSpec modelling flow

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – ProblemSpec agent.
  - **MVP Criteria** – User can submit a problem and drive an end-to-end loop.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – Projects, chat sessions, ProblemSpec object.
  - **Feature: Run Configuration & Execution Pipeline** – selecting mode (full search, eval-only, seeded).

## Acceptance Criteria
- A ProblemSpec data model exists that captures constraints (with weights), goals, resolution, and mode.
- The backend exposes endpoints or functions to read/update the ProblemSpec for a project.
- A ProblemSpec agent is implemented on top of Kosmos’s agent framework that:
  - Consumes recent chat context and the current ProblemSpec.
  - Proposes structured updates and follow-up questions.
- The chat flow supports:
  - User providing free-form problem description.
  - Agent asking clarification questions.
  - Incremental construction of ProblemSpec until it is “ready to run”.
- A simple test path (API/CLI) exists that shows a ProblemSpec being built from a sample conversation.
- User signs off that the ProblemSpec flow feels usable for MVP.

## Tasks
- [ ] Define the ProblemSpec schema (fields for constraints, goals, resolution, mode) in the backend domain model.
- [ ] Implement persistence for ProblemSpec (CRUD) aligned with Story 002’s schema.
- [ ] Implement a Kosmos-based ProblemSpec agent that can:
  - [ ] Read recent chat messages and current ProblemSpec.
  - [ ] Propose updated ProblemSpec and follow-up questions.
- [ ] Add backend endpoints or service methods to:
  - [ ] Trigger ProblemSpec refinement for a given project/chat.
  - [ ] Retrieve the current ProblemSpec.
- [ ] Wire the ProblemSpec agent into the chat loop so that setup chats can iteratively refine the spec.
- [ ] Create a minimal test script or unit tests that demonstrate end-to-end ProblemSpec construction from sample input.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The ProblemSpec agent should be conservative about overwriting user-provided constraints; it should propose changes that the user can accept or reject in the UI.


