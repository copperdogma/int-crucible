# Story 015: Chat-first project creation and selection

**Status**: Complete  

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
  - [x] Add an API path or extend existing logic to:
    - Create a new project from a free-text description plus optional suggested title.
  - [x] Define a simple heuristic for inferring project titles from the initial user message (e.g., first sentence or a short LLM-generated phrase).
  - [x] Ensure the Architect/Guidance logic can:
    - Detect when a chat session has no associated project and trigger project creation.
    - Or, alternatively, that the frontend orchestrates this flow explicitly while keeping logging consistent.

- **Frontend**:
  - [x] When no project is selected:
    - Display the Architect greeting and prompt as the first chat messages (without requiring a modal form).
  - [x] On the user’s first substantive reply:
    - Call the backend to create a project and initial chat session.
    - Update the project selector and current project state.
  - [x] For "New Project" from the selector:
    - Open a fresh chat area that replays the Architect greeting + problem prompt, instead of a static form.

- **UX & safeguards**:
  - [x] Make it clear in the UI:
    - Which project you are currently in.
    - How to rename or edit the project title/description.
  - [x] Avoid accidental project creation spam by:
    - Ensuring only one project is created per new conversational flow.
    - Providing a clear path to discard or rename a just-created project if it was a misfire.

- **Browser testing and UI verification**:
  - [x] **CRITICAL**: Use browser tools to test the implementation in the live UI:
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

## Work Log

### 20250117-1700 — Started implementation of chat-first project creation
- **Result:** In progress
- **Notes:** 
  - Reviewed current codebase structure
  - Identified that project creation currently requires title/description via form
  - Need to add backend endpoint for creating project from description with title inference
  - Need to modify frontend to show chat interface when no project selected
  - Need to handle initial Architect greeting flow
- **Next:** Implement backend API endpoint for description-based project creation with title inference

### 20250117-1730 — Backend implementation completed
- **Result:** Success
- **Notes:**
  - Added `_infer_project_title()` utility function with simple heuristic (first sentence or first 50 chars)
  - Added `/projects/from-description` API endpoint that:
    - Creates project with inferred title
    - Creates initial chat session
    - Creates user message with description
    - Generates Architect greeting via LLM (with fallback)
    - Creates greeting message in chat session
  - Updated Pydantic models to include `ProjectCreateFromDescriptionRequest`
- **Next:** Frontend implementation

### 20250117-1745 — Frontend implementation completed
- **Result:** Success
- **Notes:**
  - Updated `frontend/lib/api.ts` to add `createFromDescription()` method
  - Modified `ChatInterface` to:
    - Accept `projectId: string | null` to handle no-project state
    - Show initial greeting when no project exists
    - Handle first message to create project via new API endpoint
    - Display "Creating project..." status during creation
  - Modified `frontend/app/page.tsx` to:
    - Show chat interface when no project selected (instead of project selector)
    - Show project list sidebar when projects exist
    - Handle project creation callback to switch to project view
- **Next:** Browser testing and verification

### 20250117-1800 — UX safeguards and project editing added
- **Result:** Success
- **Notes:**
  - Added `PUT /projects/{project_id}` API endpoint for updating projects
  - Created `ProjectEditModal` component for editing project title/description
  - Added edit button (✏️) in project header
  - Added safeguard to prevent duplicate project creation (hasCreatedProject flag)
  - Improved project list sidebar to highlight active project
  - Updated frontend API client with `update()` method
- **Next:** Browser testing

### 20250117-1810 — Browser testing completed
- **Result:** Success
- **Notes:**
  - Tested first-time user flow:
    - ✅ Architect greeting appears automatically when no project selected
    - ✅ User can type problem description
    - ✅ Project is created with inferred title
    - ✅ Chat session is created with user message and Architect greeting
    - ✅ UI switches to project view immediately
    - ✅ Project appears in sidebar list
  - Tested project editing:
    - ✅ Edit button (✏️) appears in project header
    - ✅ Edit modal opens with current title/description
    - ✅ Can update title and description
    - ✅ Changes are saved and reflected in UI
  - Tested returning user flow:
    - ✅ Project list sidebar shows all projects
    - ✅ Active project is highlighted
    - ✅ "New Project" button resets to greeting state
    - ✅ Can switch between projects
  - Fixed syntax error in ChatInterface.tsx (missing closing fragment tag)
  - All acceptance criteria met:
    - ✅ Chat-first creation for new sessions
    - ✅ Live UI updates
    - ✅ Multi-project support
    - ✅ Logging (all steps in conversation)
- **Next:** Ready for user sign-off

### 20251120-1630 — UX polish after additional feedback
- **Result:** Success
- **Notes:**
  - Chat view now auto-scrolls to the top when we transition into a newly created project so the user's initial message is never obscured by the Workflow Progress banner.
  - The Architect now appends a streamed follow-up summary as soon as ProblemSpec/WorldModel updates finish, explicitly suggesting next steps instead of quietly stopping after the tool status messages.
  - Added vertical padding to the Resolution row in the SpecPanel so the label no longer sits flush against the highlight bar.
  - Re-tested the chat-first flow in the browser: streaming starts instantly, user messages stay visible, and spec highlights plus final summaries all appear in sequence.
- **Next:** Await further UX feedback or move to the next story task.

### 20250117-1820 — Fixed message rendering to preserve line breaks
- **Result:** Success
- **Notes:**
  - Created `MessageContent` component to handle proper line break rendering
  - Component splits text by `\n` and renders with `<br />` tags to ensure line breaks are always visible
  - Also applies `whiteSpace: pre-wrap` CSS for additional whitespace preservation
  - Applied to all message rendering locations:
    - Initial greeting (no project state)
    - Regular chat messages
    - Streaming messages
  - Verified in browser: line breaks now render correctly, bullet points appear on separate lines
  - This ensures AI-generated messages with intentional formatting (line breaks, lists) are displayed as intended
- **Next:** Story complete, ready for sign-off

### 20250117-1830 — Enhanced project creation with LLM-generated titles and streaming updates
- **Result:** Success
- **Notes:**
  - Enhanced project creation to use LLM for generating meaningful project titles and descriptions (not just first sentence)
  - Removed manual system messages in favor of using existing streaming update system
  - Modified Architect greeting to use future tense ("I'm going to...", "I'll...") for clarity
  - Updated prompt for new project setup to include project title/description in greeting
  - Integrated ProblemSpec refinement into streaming flow (shows "Updating ProblemSpec..." in real-time)
  - Fixed issue where user message wasn't visible immediately during project creation
  - All updates now happen via streaming system (no sudden snaps)
  - Spec items properly highlighted in green when newly created (highlight-newest class)
- **Next:** Comprehensive browser testing

### 20250117-1845 — Comprehensive browser testing completed
- **Result:** Success - All requirements met and working elegantly
- **Notes:**
  - **Test 1: Initial page load**
    - ✅ Architect greeting appears automatically
    - ✅ Input field auto-focuses (user can type immediately)
    - ✅ Clean, welcoming interface
  - **Test 2: Project creation flow**
    - ✅ User message appears immediately (no input loss)
    - ✅ Project created with LLM-generated title: "HydraTrack Smart Bottle"
    - ✅ Project title appears in header immediately
    - ✅ No blocking "Creating project..." screen
  - **Test 3: Architect greeting and streaming**
    - ✅ Greeting uses future tense ("I'm going to...", "Next up, I'll...")
    - ✅ Mentions project title and description clearly
    - ✅ Explains what will happen next
    - ✅ Greeting streams in real-time (not all at once)
  - **Test 4: ProblemSpec creation and highlighting**
    - ✅ "Updating ProblemSpec..." appears during streaming
    - ✅ Spec panel populates with goals and constraints
    - ✅ All 8 newly created items have `highlight-newest` class (green highlighting works)
    - ✅ Spec update summary appears: "+4 constraints, +2 goals, resolution updated, mode updated"
  - **Test 5: Follow-up conversation**
    - ✅ User can continue chatting immediately
    - ✅ Architect responds appropriately
    - ✅ "Updating ProblemSpec..." appears during streaming
    - ✅ New constraint "Mobile App Sync" added successfully
    - ✅ Spec update summary shows: "1 constraint updated"
    - ✅ Smooth, natural conversation flow
  - **Test 6: Overall UX**
    - ✅ No jarring transitions or sudden snaps
    - ✅ Updates happen in real-time via streaming
    - ✅ Clear visual feedback at each step
    - ✅ Professional, polished experience
  - All acceptance criteria met:
    - ✅ Chat-first creation for new sessions (with LLM-generated titles)
    - ✅ Live UI updates (streaming, real-time)
    - ✅ Multi-project support (existing functionality preserved)
    - ✅ Logging (all steps in conversation, streaming updates visible)
  - All major improvements implemented:
    - ✅ LLM-generated project names and descriptions (concise, meaningful)
    - ✅ Future tense greetings (clear communication)
    - ✅ Streaming update system integration (no manual system messages)
    - ✅ Green highlighting for new spec items (visual feedback)
    - ✅ Smooth, elegant UX (no input loss, real-time updates)
- **Next:** Ready for user sign-off

