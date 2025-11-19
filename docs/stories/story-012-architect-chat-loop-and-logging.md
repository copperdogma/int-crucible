# Story 012: Architect-led conversational loop and full interaction logging

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **Target Audience** – The first user is the system's creator, a technically sophisticated solo user who should feel natural using the system.
  - **Key Features** – Interaction shell (MVP UI) should feel like a natural conversation.
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – project + chat entry point.
  - **Feature: Multiple Chats Per Project** – chat sessions as first-class objects.

## Alignment with Design
- The chat interface becomes a **single Architect/ProblemSpec persona** that:
  - Owns ProblemSpec + WorldModel refinement.
  - Provides workflow-aware guidance.
  - Orchestrates other agents “backstage”.
- Every interaction is captured as **structured conversational data** for:
  - Repeatable chat history.
  - Future analysis and improvement of agents and UX.

## Problem Statement
Currently:

1. The user types messages that:
   - Are stored as `crucible_messages`.
   - Trigger ProblemSpec refinement in the background.
2. The user must click a **"Get Help"** button to see guidance from the Guidance agent.
3. Architect / guidance responses are **not automatically produced** after each user message.
4. Some important system actions (e.g., spec refinement results, workflow state, suggestions) are **not consistently represented** as first-class conversational events with structured metadata.

This leads to:
- A chat that feels half-manual, half-automatic.
- Gaps in the interaction log that make future analysis and improvement harder.
- Confusion about which agent is speaking and what the system actually did after each user message.

## Acceptance Criteria
- **Architect persona and auto-responses**:
  - After every user message in a chat session, the system automatically produces an **Architect** response (no "Get Help" button required for basic guidance).
  - The Architect response:
    - Interprets the user’s message in context.
    - Reflects current workflow stage (e.g., setup / ready_to_run / completed).
    - Optionally surfaces next-step suggestions.
  - The Architect is clearly labeled in the UI as the **single front-of-house persona** (e.g., role `agent` with display name “Architect”).

- **Full conversational logging**:
  - Every user message and every Architect response is stored in `crucible_messages` with:
    - `role` (`user` / `agent` / `system`).
    - `content` (human-readable text).
    - `message_metadata` (JSON) capturing structured details.
  - The Architect’s `message_metadata` includes, at minimum:
    - `workflow_stage` (e.g., `setup`, `ready_to_run`, `completed`).
    - `guidance_type` or similar categorization (e.g., `spec_refinement`, `clarification`, `run_recommendation`).
    - References to any associated domain events (e.g., `problem_spec_refine_id`, `world_model_refine_id` if available).
  - No “hidden” decisions that affect user-visible state are made without being represented either:
    - As a message, or
    - As metadata on a message.

- **Removal of Get Help as primary flow**:
  - The **"Get Help"** button is removed from the main chat header for normal usage.
  - If a secondary explicit “Help” affordance remains, it:
    - Still produces an Architect response.
    - Is logged like any other interaction.
    - Is clearly optional rather than required for normal back-and-forth.

- **Error handling in the conversation**:
  - Failures to generate Architect responses (network, backend errors, etc.) result in a **system message** in the chat:
    - Human-readable explanation.
    - Suggestion to retry or continue.
  - These system messages are stored in `crucible_messages` with `role = "system"` and basic error metadata.
  - The overall conversation flow remains natural and back-and-forth (no extra UI steps are required beyond typing and sending messages).

## Tasks
- **Backend / services**:
  - [ ] Confirm that Guidance/Architect logic can be invoked **idempotently and cheaply** for each user message (e.g., via `GuidanceService`).
  - [ ] Define the minimal `message_metadata` schema for Architect responses (e.g., `workflow_stage`, `guidance_type`, related IDs).
  - [ ] Ensure that every Architect response is stored as a `crucible_messages` row with structured metadata.

- **API**:
  - [ ] If needed, introduce a small wrapper endpoint (e.g., `/chat-sessions/{id}/architect-reply`) that:
    - Uses Guidance + ProblemSpec/WorldModel state to produce a single Architect reply.
    - Returns both `content` and structured metadata.
  - [ ] Document expected JSON shape so the frontend can attach it cleanly to messages.

- **Frontend (ChatInterface)**:
  - [ ] Remove the **"Get Help"** button from `ChatInterface` as the primary way to get responses.
  - [ ] Update `handleSend` (or equivalent) to:
    - Send the user message.
    - Trigger the Architect reply via the appropriate endpoint.
    - Append both to the visible message list.
  - [ ] Render Architect messages as `role: "agent"` with a clear label (e.g., “Architect”).
  - [ ] Surface system/error messages inline in the chat instead of using `alert(...)`.

- **Logging and analysis readiness**:
  - [ ] Verify that the database now contains a **complete conversational log** for a session:
    - All user turns.
    - All Architect turns.
    - Relevant system/error turns.
  - [ ] Add a short note in `docs/architecture.md` or `docs/design.md` capturing the decision to treat conversations as the canonical interaction log for analysis.

- **Sign-off**:
  - [ ] Run through an end-to-end session:
    - New project.
    - Several setup messages.
    - Guidance/Architect replies after each message.
  - [ ] Verify that the stored messages and metadata are sufficient to reconstruct and analyze the interaction.
  - [ ] User must sign off on functionality before this story can be marked complete.


