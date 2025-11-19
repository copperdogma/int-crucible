# Story 015: Chat-first project creation and selection

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **Target Audience** – technically sophisticated solo user who should feel natural using the system.
  - **Key Features – Interaction shell (MVP UI)** – chat-first interaction.
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – project + chat entry point.

## Alignment with Design
- Projects are the top-level container for all state (ProblemSpec, WorldModel, runs, candidates, issues).
- This story makes **project creation itself** conversational:
  - The Architect greets the user and asks what they are trying to solve or design.
  - The system infers a project title/description from the answer.
  - The UI updates live as the project is created and named.
- Existing project selection remains as a separate, explicit affordance for multi-project workflows.

## Problem Statement
Currently:

1. Project creation is driven by a **popup/form** where the user types a title and optional description.
2. The chat-first design stops at the project boundary:
   - You must create/select a project before the Architect can engage.
3. The first few interactions with Int Crucible feel more like configuring an app than talking to an Architect about a problem.

We want:
- The very first experience to be a natural conversation:
  - “What are you trying to solve or make?”
  - “I’ll create a project called X; you can rename it later.”
- While still preserving:
  - Explicit project selection.
  - Clear visibility into which project is active.

## Acceptance Criteria
- **Chat-first creation for new sessions**:
  - When the user has no active project selected and opens the main UI:
    - The Architect posts an initial greeting explaining the system at a high level.
    - The Architect then asks a simple, open-ended question about what the user wants to work on.
  - When the user replies with a free-text problem description:
    - The backend creates a new `Project` with:
      - A reasonable inferred `title` (e.g., based on a short extract of the description).
      - A `description` reflecting the user’s initial message.
    - A new `ChatSession` is created and linked to this project.
    - The Architect acknowledges the new project, mentioning its inferred title and that it can be changed later.

- **Live UI updates**:
  - The project selector UI reflects the newly created project immediately.
  - The main layout clearly indicates the active project (title, etc.) without requiring another page reload.

- **Multi-project support**:
  - Users can still:
    - See a list of existing projects.
    - Create an additional project explicitly (e.g., via “New Project” in the selector).
  - When “New Project” is chosen:
    - The creation flow uses the same **Architect-first chat pattern** as above (rather than just a form).

- **Logging**:
  - All steps in project creation are represented in the conversation log for that new chat session:
    - Architect greeting.
    - User description.
    - Architect message confirming project creation (title/description).
  - The new project’s `title` and `description` are persisted in `crucible_projects` and can be retrieved later via the API.

## Tasks
- **Backend**:
  - [ ] Add an API path or extend existing logic to:
    - Create a new project from a free-text description plus optional suggested title.
  - [ ] Define a simple heuristic for inferring project titles from the initial user message (e.g., first sentence or a short LLM-generated phrase).
  - [ ] Ensure the Architect/Guidance logic can:
    - Detect when a chat session has no associated project and trigger project creation.
    - Or, alternatively, that the frontend orchestrates this flow explicitly while keeping logging consistent.

- **Frontend**:
  - [ ] When no project is selected:
    - Display the Architect greeting and prompt as the first chat messages (without requiring a modal form).
  - [ ] On the user’s first substantive reply:
    - Call the backend to create a project and initial chat session.
    - Update the project selector and current project state.
  - [ ] For “New Project” from the selector:
    - Open a fresh chat area that replays the Architect greeting + problem prompt, instead of a static form.

- **UX & safeguards**:
  - [ ] Make it clear in the UI:
    - Which project you are currently in.
    - How to rename or edit the project title/description.
  - [ ] Avoid accidental project creation spam by:
    - Ensuring only one project is created per new conversational flow.
    - Providing a clear path to discard or rename a just-created project if it was a misfire.

- **Browser testing and UI verification**:
  - [ ] **CRITICAL**: Use browser tools to test the implementation in the live UI:
    - Start the frontend and backend servers.
    - Test first-time user flow (no existing projects):
      - Verify Architect greeting appears automatically.
      - Send a problem description and verify project is created.
      - Verify project appears in selector immediately.
      - Verify active project is clearly indicated in UI.
    - Test returning user flow (existing projects):
      - Verify project list is accessible.
      - Create additional project via "New Project" and verify chat-first flow.
      - Verify project switching works correctly.
    - Verify the UI is elegant, functional, and matches the acceptance criteria.
    - Fix any issues found during browser testing before proceeding to sign-off.

- **Sign-off**:
  - [ ] Walk through:
    - First-time user flow (no existing projects).
    - Returning user flow (multiple projects, creating an additional one).
  - [ ] Confirm that all project creation steps are:
    - Conversational.
    - Logged in the chat.
    - Reflected in the project list UI.
  - [ ] User must sign off on the chat-first project creation experience before this story can be marked complete.


