# Story: Build minimal chat-first web UI

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Interaction shell (MVP UI), Programmatic interface (API/CLI).
  - **MVP Criteria** – user can submit a problem and inspect ranked candidates + provenance.

## Alignment with Design
- See `docs/design.md`:
  - **Architecture Overview** – frontend UI responsibilities.
  - **Feature: Chat-First Project & ProblemSpec Modelling** – project + chat entry point.
  - **Feature: Live Spec / World-Model View** – side-by-side spec.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – post-run exploration.

## Acceptance Criteria
- A minimal but usable web UI exists where:
  - The user can create/select a project.
  - The main surface is a chat with the system (ProblemSpec/Architect agent).
  - The user can view the live spec/world-model panel.
  - The user can configure and start a run from a simple run configuration panel.
  - The user can see a ranked list of candidates and open basic detail views (summary, scores, constraint flags).
- The UI talks exclusively to the backend APIs defined in earlier stories (no hidden logic that bypasses them).
- Styling is clean and readable, optimized for a single-user workflow (you).
- Basic error states and loading indicators are handled gracefully.

## Tasks
- [ ] Scaffold a Next.js + TypeScript frontend project (if not already done).
- [ ] Implement project list/selector and basic routing/state for “current project”.
- [ ] Implement chat UI:
  - [ ] Message list (user vs agent).
  - [ ] Input box with send behaviour.
  - [ ] Wiring to backend chat endpoints.
- [ ] Implement a right/secondary panel for the live spec/world-model view.
- [ ] Implement a simple run configuration panel and “Run” trigger wired to the backend.
- [ ] Implement a basic results view:
  - [ ] Ranked candidates with key scores (P, R, I, constraint warnings).
  - [ ] Candidate detail modal/page with explanation text.
- [ ] Add basic layout and styling so the UI is pleasant to use for long sessions.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This is intentionally a thin UI layer; most of the complexity should live in the backend and Kosmos-based agents.


