# Story: Implement interactive guidance and onboarding agent

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Target Audience** – The first user is the system's creator, a technically sophisticated solo user who should feel natural using the system.
  - **Key Features** – Interaction shell (MVP UI) should guide users through the process.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – The user interacts via chat sessions with an "Architect/ProblemSpec" agent.
  - The system should feel natural and guide users through the workflow.

## Problem Statement
Currently, users must understand the Int Crucible workflow themselves:
1. Create a project
2. Chat to generate ProblemSpec
3. Generate WorldModel
4. Configure and run the pipeline
5. Review results

There's no proactive agent that:
- Explains what each step does
- Guides users through the process
- Suggests next actions
- Provides contextual help
- Explains why certain prerequisites are needed (e.g., "You need a ProblemSpec and WorldModel before running")

## Acceptance Criteria
- An interactive Guidance agent exists that:
  - Proactively explains the Int Crucible workflow to new users
  - Provides contextual help based on the current state (e.g., "You need to generate a WorldModel before running")
  - Suggests next steps at appropriate moments
  - Explains what each component does (ProblemSpec, WorldModel, runs, candidates)
  - Can be invoked explicitly via chat or UI button
  - Integrates with the chat interface seamlessly
- The agent can:
  - Detect the current project state (has ProblemSpec? has WorldModel? has runs?)
  - Provide state-aware guidance (e.g., "Great! You have a ProblemSpec. Next, let's generate a WorldModel...")
  - Answer questions about the system and workflow
  - Guide users through creating their first project and running their first pipeline
- The UI provides:
  - A way to invoke the guidance agent (e.g., "Get Help" button or "Guide me" command)
  - Visual indicators showing progress through the workflow
  - Contextual tooltips or hints that can be toggled
- The guidance agent is distinct from but can work alongside:
  - The ProblemSpec agent (which focuses on problem structuring)
  - The FeedbackAgent (which handles post-run issues)

## Tasks
- [ ] Design the Guidance agent interface and behavior:
  - [ ] Define when the agent should proactively intervene vs. wait for user request
  - [ ] Define the agent's knowledge base (workflow steps, component explanations, common questions)
  - [ ] Define how the agent accesses project state to provide contextual guidance
- [ ] Implement the Guidance agent (on Kosmos framework):
  - [ ] Create `GuidanceAgent` class extending `BaseAgent`
  - [ ] Implement state detection logic (check for ProblemSpec, WorldModel, runs, etc.)
  - [ ] Implement guidance prompts that explain workflow and suggest next steps
  - [ ] Implement question-answering about the system
- [ ] Integrate with chat interface:
  - [ ] Add guidance agent responses to chat flow
  - [ ] Allow users to explicitly request guidance (e.g., "help", "what's next?", "guide me")
  - [ ] Support proactive suggestions (e.g., when user opens Run Config without prerequisites)
- [ ] Add UI affordances:
  - [ ] "Get Help" or "Guide Me" button in the UI
  - [ ] Progress indicators showing workflow state
  - [ ] Contextual hints/tooltips (can be toggled on/off)
  - [ ] Visual indicators for missing prerequisites
- [ ] Add backend API endpoints:
  - [ ] `POST /chat-sessions/{chat_session_id}/guidance` - Request guidance
  - [ ] `GET /projects/{project_id}/workflow-state` - Get current workflow state for contextual guidance
- [ ] Add tests or sample flows showing:
  - [ ] New user onboarding flow
  - [ ] Contextual help at different workflow stages
  - [ ] Question-answering about the system
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This agent is different from the ProblemSpec agent:
  - ProblemSpec agent: Focuses on structuring the problem (constraints, goals, resolution)
  - Guidance agent: Focuses on explaining the system and guiding workflow
- The guidance agent should feel helpful but not intrusive - it should wait for explicit requests or provide subtle suggestions
- This can build on the prerequisite checking we've already added to RunConfigPanel
- Future enhancements could include:
  - Interactive tutorials
  - Workflow templates
  - Domain-specific guidance

