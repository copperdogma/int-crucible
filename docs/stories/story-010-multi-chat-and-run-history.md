# Story: Support multiple chats and runs per project

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Target Audience** – a single technical user iterating on complex designs.
  - **MVP Criteria** – enabling iterative use on Int Crucible itself.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – multiple chats per project.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – run history and exploration.

## Acceptance Criteria
- Each project can have multiple chat sessions, with:
  - Clear labelling (e.g., setup vs analysis vs what-if).
  - Persistent history per chat.
- Runs are associated with:
  - A project.
  - Optionally a specific chat or candidate context.
- The UI lets the user:
  - Switch between chats within a project.
  - View a run history for the project.
  - Open results from previous runs and continue analysis in new chats.
- Backend supports querying:
  - All chats for a project.
  - All runs for a project and their statuses.
- This functionality is integrated enough that you can use Int Crucible to iteratively improve Int Crucible itself across multiple runs and chat branches.

## Tasks
- [ ] Finalize the schema for `ChatSession`, `Message`, and `Run` with relationships to `Project` and (optionally) `Candidate`.
- [ ] Implement backend endpoints to:
  - [ ] Create/list/select chat sessions for a project.
  - [ ] Create/list runs for a project, filtered by chat or candidate.
- [ ] Implement UI elements to:
  - [ ] Show a list of chats for the current project and switch between them.
  - [ ] Show a list of runs with basic metadata (mode, created_at, status).
  - [ ] Open an existing run’s results in a new or existing chat context.
- [ ] Ensure that pipeline invocations correctly link created runs and candidates back to the originating project/chat/candidate.
- [ ] Add tests or sample flows demonstrating a multi-run, multi-chat workflow on a single project.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This story makes the system feel like a persistent reasoning environment rather than a single-shot tool, which is particularly important for using Int Crucible to improve itself over time.


