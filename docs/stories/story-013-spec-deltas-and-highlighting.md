# Story 013: Spec/world-model deltas and live highlighting

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features – ProblemSpec agent** – structured constraints, goals, and resolution.
  - **Key Features – WorldModeller (MVP)** – structured world model representation.
- See `docs/design.md`:
  - **Feature: Live Spec / World-Model View** – side-by-side spec and world model.

## Alignment with Design
- The ProblemSpec and WorldModel are already updated in response to chat.
- This story makes **those changes visible and inspectable** by:
  - Providing compact delta summaries in Architect replies.
  - Highlighting recently touched sections in the spec/world-model panel.
  - Persisting structured delta information for future analysis and provenance.

## Problem Statement
Today:

1. The system refines the ProblemSpec (and, via later stories, the WorldModel) based on chat messages.
2. The user sees the **final spec/world-model** but not what changed on each interaction.
3. There is no notion of:
   - “This section was most recently updated.”
   - “These constraints were just added/modified/removed.”
   - A compact log of spec/world-model evolution.

This makes it harder to:
- Understand the effect of each conversational turn.
- Trust that the model reflects what was just agreed verbally.
- Analyze past sessions and reconstruct model evolution.

## Acceptance Criteria
- **Backend: structured deltas for ProblemSpec and WorldModel**:
  - ProblemSpec refinement returns a machine-readable delta structure containing, at minimum:
    - Which sections were touched (e.g., `goals`, `constraints`, `resolution`).
    - For constraints/goals: added/updated/removed items (by name or id where available).
  - WorldModel refinement similarly returns:
    - Which segments were touched (e.g., `actors`, `mechanisms`, `resources`, `assumptions`, `constraints`, `simplifications`).
    - A coarse classification of changes (e.g., `added`, `modified`, `removed`).
  - These deltas are associated with the Architect response and stored in a structured form (e.g., in `message_metadata` of the Architect’s message).

- **Frontend: compact “Spec update” line in Architect replies**:
  - For each Architect reply that is associated with a refinement:
    - A compact one-line summary is shown, e.g.:
      - “Spec update: **+1 constraint**, **clarified 1 goal**.”
      - “World model update: **+1 actor**, **+1 assumption**.”
    - A small affordance (e.g., “[Details]” toggle) reveals a slightly more detailed list of changes (but still human-readable, not raw JSON).

- **Frontend: live highlighting of updated spec/world-model sections**:
  - The spec/world-model panel visually highlights recently changed sections:
    - Sections touched by the latest refinement are clearly indicated (e.g., background tint, border, or subtle pulse).
    - Older changes gradually fade back to neutral, indicating recency (e.g., via CSS classes or a time-decay scheme).
  - The highlight logic is driven by the structured deltas (not by fragile UI heuristics).

- **Logging and analysis**:
  - For a given chat session, it is possible to reconstruct a coarse **timeline of spec/world-model evolution** by reading:
    - Architect messages.
    - Their associated delta metadata.
  - The delta representation is stable enough to be used in future provenance work (Story 008) without needing a complete rewrite.

## Tasks
- **Backend (ProblemSpec/WorldModel services)**:
  - [ ] Extend `ProblemSpecService.refine_problem_spec` to compute and return:
    - A concise `spec_delta` structure (section-level + per-item changes).
  - [ ] Extend `WorldModelService.generate_or_refine_world_model` to compute and return:
    - A similar `world_model_delta` structure.
  - [ ] Ensure both services:
    - Attach deltas to their existing refine responses.
    - Provide enough identifiers (names, IDs) to be useful on the frontend.

- **Backend (Architect/Guidance integration)**:
  - [ ] Ensure the Architect (Guidance) call path can see the latest deltas.
  - [ ] Populate Architect `message_metadata` with:
    - `spec_delta` (if ProblemSpec changed).
    - `world_model_delta` (if WorldModel changed).
    - `touched_sections` (aggregated summary usable by the UI).

- **Frontend (ChatInterface + SpecPanel)**:
  - [ ] Update the chat rendering so Architect messages can show a compact “Spec update” / “World model update” line derived from `message_metadata`.
  - [ ] Add a small toggle/expander to reveal per-change detail when desired.
  - [ ] Update the spec/world-model panel to:
    - Accept a list of `touched_sections` and apply highlighting.
    - Implement a simple recency decay (e.g., storing a timestamp or “age” value per section).

- **UX & validation**:
  - [ ] Verify that the delta summary line remains **succinct** and doesn’t overwhelm the chat.
  - [ ] Confirm that spec highlighting feels helpful and not distracting (tune colors and timing).
  - [ ] Run through a setup session and visually confirm:
    - Each meaningful change is communicated in chat.
    - The spec panel clearly shows what was updated last.

- **Sign-off**:
  - [ ] Capture an example session in screenshots or notes, showing:
    - A few consecutive spec/world-model changes.
    - Their corresponding Architect messages and deltas.
    - The visual evolution in the spec panel.
  - [ ] User must sign off on the UX and delta representation before this story can be marked complete.


