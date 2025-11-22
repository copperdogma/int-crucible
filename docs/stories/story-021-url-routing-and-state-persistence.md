# Story 021: URL routing and state persistence

**Status**: To Do

---

## Related Requirement

- See `docs/requirements.md`:
  - **Target Audience** – technically sophisticated solo user who should feel natural using the system.
  - **Interaction shell (MVP UI)** – minimal UI where the user can enter a problem, inspect ranked candidates, see constraint scores and provenance, and iterate.

## Alignment with Design

- This story enhances the chat-first UI experience by making application state shareable and persistent via URL routing.
- Users should be able to bookmark specific project/chat contexts and share them with others.
- Page refreshes should restore the exact state the user was in (which project, which chat session, which run results view).

## Problem Statement

Currently:

1. The application uses client-side state only - no URL routing.
2. The URL never changes (`/` for all views).
3. When you refresh the page, you lose your place:
   - Selected project is lost
   - Selected chat session is lost
   - Active run/results view is lost
4. You cannot share links to specific project/chat contexts.
5. You cannot bookmark where you were in your work.

We want:
- URL to reflect the current application state (project, chat session, active run).
- Page refresh to restore the same state from the URL.
- Ability to share URLs that bring someone to the same project/chat context.
- Ability to bookmark specific project/chat contexts.

## Acceptance Criteria

- **URL structure**:
  - `/` - No project selected (home/initial state)
  - `/project/[projectId]` - Project selected, no specific chat
  - `/project/[projectId]/chat/[chatSessionId]` - Project and chat session selected
  - `/project/[projectId]/run/[runId]` - Project selected, viewing specific run results (optional enhancement)
  - URLs are clean and human-readable

- **State synchronization**:
  - When project is selected/changed, URL updates to `/project/[projectId]`
  - When chat session is selected/changed, URL updates to `/project/[projectId]/chat/[chatSessionId]`
  - When user navigates (e.g., selects a run from history), URL updates accordingly
  - Browser back/forward buttons work correctly

- **State restoration on page load**:
  - On initial page load, read URL parameters
  - If `/project/[projectId]` exists, restore that project selection
  - If `/project/[projectId]/chat/[chatSessionId]` exists, restore both project and chat
  - If `/project/[projectId]/run/[runId]` exists, restore project and open results view for that run
  - If URL is invalid (project/chat doesn't exist), show appropriate error and redirect to `/`

- **Shareability**:
  - URLs can be copied from the browser address bar and shared
  - When someone opens a shared URL, they see the same project/chat context
  - All necessary data loads from the API based on URL parameters

- **Backward compatibility**:
  - Existing bookmarks to `/` continue to work
  - Direct navigation to `/project/[projectId]` without chat defaults to the most recent chat (or creates one if none exists)

## Tasks

- **Frontend - Next.js routing setup**:
  - [ ] Set up Next.js App Router dynamic routes:
    - [ ] Create `app/project/[projectId]/page.tsx` for project view
    - [ ] Create `app/project/[projectId]/chat/[chatSessionId]/page.tsx` for chat view
    - [ ] Update root `app/page.tsx` to handle initial state (no project)
  - [ ] Implement URL parameter parsing and state initialization:
    - [ ] Read `projectId` from URL params on page load
    - [ ] Read `chatSessionId` from URL params on page load
    - [ ] Read `runId` from URL params on page load (optional)
    - [ ] Initialize component state from URL params

- **Frontend - URL synchronization**:
  - [ ] Update URL when project selection changes:
    - [ ] Use Next.js router to navigate to `/project/[projectId]` when project selected
    - [ ] Preserve chat session in URL if one is active
  - [ ] Update URL when chat session changes:
    - [ ] Navigate to `/project/[projectId]/chat/[chatSessionId]` when chat selected
    - [ ] Handle chat session creation with URL update
  - [ ] Update URL when navigating to run results:
    - [ ] Navigate to `/project/[projectId]/run/[runId]` when viewing run results (optional)
    - [ ] Consider using query params for runs: `/project/[projectId]/chat/[chatSessionId]?run=[runId]`
  - [ ] Implement browser back/forward navigation handling:
    - [ ] Listen to Next.js router events for popstate
    - [ ] Update component state when URL changes via browser navigation

- **Frontend - State management**:
  - [ ] Refactor state management to sync with URL:
    - [ ] Move project selection state to URL-driven initialization
    - [ ] Move chat session selection state to URL-driven initialization
    - [ ] Ensure all state changes update URL appropriately
  - [ ] Handle edge cases:
    - [ ] Invalid project ID in URL (project doesn't exist)
    - [ ] Invalid chat session ID in URL (chat doesn't exist or doesn't belong to project)
    - [ ] Missing permissions (future - if auth is added)
    - [ ] Loading states while fetching project/chat data

- **UX considerations**:
  - [ ] Ensure smooth transitions when navigating via URL:
    - [ ] No flash of wrong content
    - [ ] Loading indicators while data fetches
    - [ ] Graceful error handling for invalid URLs
  - [ ] Maintain existing UX features:
    - [ ] Project selector still works but updates URL
    - [ ] Chat session switcher still works but updates URL
    - [ ] All existing navigation paths continue to work

- **Testing**:
  - [ ] Test URL navigation scenarios:
    - [ ] Direct navigation to `/project/[projectId]`
    - [ ] Direct navigation to `/project/[projectId]/chat/[chatSessionId]`
    - [ ] Browser back/forward buttons
    - [ ] Page refresh on each URL state
    - [ ] Sharing URLs with different users/sessions
  - [ ] Test error cases:
    - [ ] Invalid project ID
    - [ ] Invalid chat session ID
    - [ ] Chat session from different project
    - [ ] Non-existent run ID
  - [ ] Manual browser testing:
    - [ ] Start frontend and backend servers
    - [ ] Test full workflow with URL changes
    - [ ] Test refresh at various stages
    - [ ] Test URL sharing (copy/paste in new tab)

## Implementation Notes

- **Next.js App Router**: Since this is a Next.js app using the App Router, use Next.js's built-in routing features:
  - Use `useParams()` to read URL parameters
  - Use `useRouter()` from `next/navigation` to update URLs
  - Use `router.push()` for navigation
  - Use `router.replace()` for state updates without adding history entries

- **URL structure considerations**:
  - Prefer clean, readable URLs without query params where possible
  - Consider query params for transient state (e.g., `?run=[runId]` for viewing run results)
  - Keep URLs as flat as possible for easier sharing

- **State initialization**:
  - On page load, check URL params first
  - If URL params exist, fetch and set state from them
  - If no URL params, use default behavior (current implementation)
  - Consider using Next.js Server Components to fetch initial data where appropriate

- **Migration strategy**:
  - Start with project selection URL routing
  - Then add chat session routing
  - Finally add run/view routing if needed
  - Ensure each step maintains backward compatibility

- **Optional enhancements** (future):
  - Add query params for modal states (e.g., `?modal=run-history`)
  - Add query params for scroll position or other UI state
  - Consider using URL hash for client-side only state

## Notes

- This is a UX enhancement that significantly improves the user experience.
- Priority: Medium (nice to have, not blocking core functionality).
- Consider this alongside any future authentication/sharing features.
- URL routing will also help with analytics and debugging (seeing what users are viewing).

---

## Work Log

_Work log entries will be added here as the story is implemented._

