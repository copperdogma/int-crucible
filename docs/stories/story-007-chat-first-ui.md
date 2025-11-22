# Story: Build minimal chat-first web UI

**Status**: Implementation Complete ✅ (Pending User Sign-Off)

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
- [x] Scaffold a Next.js + TypeScript frontend project (if not already done).
- [x] Implement project list/selector and basic routing/state for "current project".
- [x] Implement chat UI:
  - [x] Message list (user vs agent).
  - [x] Input box with send behaviour.
  - [x] Wiring to backend chat endpoints.
- [x] Implement a right/secondary panel for the live spec/world-model view.
- [x] Implement a simple run configuration panel and "Run" trigger wired to the backend.
- [x] Implement a basic results view:
  - [x] Ranked candidates with key scores (P, R, I, constraint warnings).
  - [x] Candidate detail modal/page with explanation text.
- [x] Add basic layout and styling so the UI is pleasant to use for long sessions.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This is intentionally a thin UI layer; most of the complexity should live in the backend and Kosmos-based agents.

## Work Log

### 20250117-1430 — Scaffolded Next.js frontend and added missing API endpoints
- **Result:** Success; created Next.js + TypeScript frontend with React Query, added all required API endpoints to backend
- **Actions:**
  - Created Next.js 16 project with TypeScript and Tailwind CSS in `frontend/` directory
  - Installed @tanstack/react-query for server state management
  - Created API client library (`lib/api.ts`) with typed functions for all endpoints
  - Added React Query provider setup
  - Created main app structure with project selector, chat interface, spec panel, run config, and results view
  - Added missing backend API endpoints:
    - GET/POST /projects (list/create projects)
    - GET /projects/{id} (get project)
    - GET/POST /chat-sessions (list/create chat sessions)
    - GET /projects/{id}/chat-sessions (list project chat sessions)
    - GET /chat-sessions/{id}/messages (list messages)
    - POST /chat-sessions/{id}/messages (create message)
    - GET/POST /runs (list/create runs)
    - GET /runs/{id}/candidates (get ranked candidates with scores)
- **Files Created:**
  - `frontend/` - Next.js project structure
  - `frontend/lib/api.ts` - API client
  - `frontend/app/providers.tsx` - React Query provider
  - `frontend/app/page.tsx` - Main app page
  - `frontend/components/ProjectSelector.tsx` - Project selection UI
  - `frontend/components/ChatInterface.tsx` - Chat UI component
  - `frontend/components/SpecPanel.tsx` - Live spec/world-model panel
  - `frontend/components/RunConfigPanel.tsx` - Run configuration UI
  - `frontend/components/ResultsView.tsx` - Results and candidate ranking view
- **Files Modified:**
  - `crucible/api/main.py` - Added project, chat session, message, and run endpoints
- **Next:** Test the UI end-to-end, fix any integration issues, and polish styling

### 20250117-1500 — Fixed CORS, text color issues, and 404 error handling
- **Result:** Success; UI is fully functional with proper error handling and visible text colors
- **Actions:**
  - Added CORS middleware to FastAPI backend to allow frontend requests
  - Fixed text color visibility in all input fields (added `text-gray-900` class and CSS rules)
  - Improved 404 error handling for optional resources (ProblemSpec, WorldModel)
  - Added retry logic that skips retries for expected 404 errors
  - Tested end-to-end: project creation, chat messaging, ProblemSpec generation all working
- **Files Modified:**
  - `crucible/api/main.py` - Added CORSMiddleware
  - `frontend/lib/api.ts` - Added NOT_FOUND error handling
  - `frontend/components/SpecPanel.tsx` - Added 404 error handling
  - `frontend/components/*.tsx` - Added `text-gray-900` to all input/textarea/select elements
  - `frontend/app/globals.css` - Added CSS rules to ensure input text is always visible
- **Testing:**
  - ✅ Project creation works
  - ✅ Chat interface sends messages
  - ✅ ProblemSpec is generated and displayed in spec panel
  - ✅ Text colors are visible in all input fields
  - ✅ 404 errors are handled gracefully (no console spam)
- **Note:** Backend server needs to be restarted for CORS changes to take effect

### 20250117-1515 — Fixed all text visibility issues across all pages
- **Result:** Success; all text is now dark and legible throughout the application
- **Actions:**
  - Fixed "Int Crucible" heading text color (added `text-gray-900`)
  - Fixed "Select or Create a Project" heading text color (added `text-gray-900`)
  - Fixed all modal headings (Run Configuration, Run Results, Candidate Details)
  - Fixed all loading states text colors
  - Fixed all empty state messages text colors
  - Fixed all section headings in SpecPanel (Problem Specification, World Model)
  - Improved contrast for secondary text (changed `text-gray-500` to `text-gray-700` where appropriate)
- **Files Modified:**
  - `frontend/app/page.tsx` - Fixed main headings and loading text
  - `frontend/components/ProjectSelector.tsx` - Fixed all headings and empty states
  - `frontend/components/ChatInterface.tsx` - Fixed loading and empty state text
  - `frontend/components/SpecPanel.tsx` - Fixed all headings and loading text
  - `frontend/components/ResultsView.tsx` - Fixed headings and loading text
- **Testing:**
  - ✅ Project selector page - all text legible
  - ✅ Project view with chat - all text legible
  - ✅ Spec panel - all headings and content legible
  - ✅ Run Config modal - all text legible
  - ✅ All headings use `text-gray-900` for maximum contrast
  - ✅ Secondary text uses `text-gray-700` for good readability

### 20250117-1520 — Fixed chat session persistence issue when creating new projects
- **Result:** Success; new projects now start with a fresh chat session
- **Actions:**
  - Added useEffect to reset chat session state when project changes
  - Added cache invalidation to clear old messages when switching projects
  - Improved ChatInterface to validate chat session belongs to current project
- **Files Modified:**
  - `frontend/app/page.tsx` - Added project change effect to reset chat session and clear cache
  - `frontend/components/ChatInterface.tsx` - Added validation to ensure chat session belongs to current project
- **Testing:**
  - ✅ Creating a new project now shows empty chat (no old messages)
  - ✅ Switching between projects properly resets chat state
  - ✅ Messages cache is cleared when project changes

### 20250117-1530 — Added auto-focus, hid devtools indicator, and suppressed hydration warning
- **Result:** Success; improved UX with auto-focus and cleaner interface
- **Actions:**
  - Added auto-focus to project title input when create form opens
  - Hid Next.js devtools indicators and error overlays via CSS to prevent blocking chat input
  - Added `suppressHydrationWarning` to body tag to suppress browser extension hydration warnings
  - Added extra padding to chat input area to prevent overlap with any remaining indicators
- **Files Modified:**
  - `frontend/components/ProjectSelector.tsx` - Added useRef and useEffect for auto-focus
  - `frontend/app/layout.tsx` - Added suppressHydrationWarning to body
  - `frontend/app/globals.css` - Added CSS rules to hide devtools indicators
  - `frontend/components/ChatInterface.tsx` - Added chat-input-area class for padding
  - `frontend/next.config.ts` - Disabled build activity indicator
- **Testing:**
  - ✅ Title input auto-focuses when create form opens
  - ✅ Devtools indicators are hidden (won't block chat input)
  - ✅ Hydration warning suppressed (browser extension modifications ignored)
  - ✅ Chat input area has proper padding

### 20250117-1600 — Fixed Run Config error handling and timezone display
- **Result:** Success; improved error messages and correct timezone display
- **Actions:**
  - Improved error handling in RunConfigPanel to show specific message when ProblemSpec/WorldModel are missing
  - Fixed timezone display issue by properly parsing ISO date strings and handling timezone conversion
  - Added logic to detect if date strings have timezone info and append 'Z' (UTC) if missing
- **Files Modified:**
  - `frontend/components/RunConfigPanel.tsx` - Better error message for NOT_FOUND (missing ProblemSpec/WorldModel)
  - `frontend/components/ChatInterface.tsx` - Fixed timezone parsing to correctly convert UTC to local time
- **Testing:**
  - ✅ Run Config now shows helpful error when ProblemSpec/WorldModel are missing
  - ✅ Time displays correctly in user's local timezone (converts from UTC properly)


