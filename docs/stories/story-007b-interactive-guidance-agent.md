# Story: Implement interactive guidance and onboarding agent

**Status**: Implementation Complete ✅ (Pending User Sign-Off)

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
- [x] Design the Guidance agent interface and behavior:
  - [x] Define when the agent should proactively intervene vs. wait for user request
  - [x] Define the agent's knowledge base (workflow steps, component explanations, common questions)
  - [x] Define how the agent accesses project state to provide contextual guidance (via dynamic tool creation)
- [x] Implement the Guidance agent (on Kosmos framework):
  - [x] Create `GuidanceAgent` class extending `BaseAgent`
  - [x] Implement state detection logic (check for ProblemSpec, WorldModel, runs, etc.)
  - [x] Implement guidance prompts that explain workflow and suggest next steps
  - [x] Implement question-answering about the system (AI-native tool-based approach)
- [x] Integrate with chat interface:
  - [x] Add guidance agent responses to chat flow
  - [x] Allow users to explicitly request guidance (e.g., "help", "what's next?", "guide me")
  - [x] Support proactive suggestions (workflow state detection)
- [x] Add UI affordances:
  - [x] "Get Help" or "Guide Me" button in the UI
  - [x] Progress indicators showing workflow state (WorkflowProgress component)
  - [x] Contextual hints/tooltips (can be toggled on/off)
  - [x] Visual indicators for missing prerequisites
- [x] Add backend API endpoints:
  - [x] `POST /chat-sessions/{chat_session_id}/guidance` - Request guidance
  - [x] `GET /projects/{project_id}/workflow-state` - Get current workflow state for contextual guidance
- [x] Add tests or sample flows showing:
  - [x] New user onboarding flow
  - [x] Contextual help at different workflow stages
  - [x] Question-answering about the system
  - [x] Comprehensive unit tests for GuidanceAgent (test_guidance_agent.py)
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- This agent is different from the ProblemSpec agent:
  - ProblemSpec agent: Focuses on structuring the problem (constraints, goals, resolution)
  - Guidance agent: Focuses on explaining the system and guiding workflow
- The guidance agent should feel helpful but not intrusive - it should wait for explicit requests or provide subtle suggestions
- This can build on the prerequisite checking we've already added to RunConfigPanel
- **Design Philosophy**: The guidance agent is designed to be AI-native rather than template-driven:
  - It receives strong direction and knowledge through system prompts
  - It adapts naturally to context and user experience level
  - It provides conversational guidance rather than rigid templates
  - Structured data (like workflow progress) is computed programmatically, but guidance text is natural language
- Future enhancements could include:
  - Interactive tutorials
  - Workflow templates
  - Domain-specific guidance

## Work Log

### 20250117-XXXX — Initial implementation of guidance agent
- **Result:** Successfully implemented GuidanceAgent, GuidanceService, API endpoints, and frontend integration
- **Approach Evolution:**
  1. **Initial:** Scaffolded with rigid JSON structure (over-engineered)
  2. **Refactored to AI-native:** Natural language output, adaptive prompts, higher temperature
  3. **Added tool support:** Agent can use tools to query system dynamically
- **Key Design Decisions:**
  - **AI-Native vs Template-Driven:** Chose AI-native approach - agent receives strong direction through system prompts but adapts naturally to context
  - **Tool-Based vs Context-Based:** Implemented hybrid approach - agent has tools available but falls back to context-based if tools unavailable
  - **Tool Implementation:** Currently uses prompt-based tool descriptions (agent knows about tools in prompt). Future: Could use native LLM function calling (Claude tool use, OpenAI functions) for true tool invocation
- **Tool Architecture:**
  - GuidanceService creates tool functions that wrap repository calls
  - Tools available: `get_workflow_state`, `get_problem_spec`, `get_world_model`, `list_runs`, `get_chat_history`
  - Agent receives tool descriptions in prompt and can "use" them conceptually
  - **Current limitation:** Not using native LLM function calling - tools are described but not automatically invoked. This is a pragmatic first step.
  - **Future enhancement:** Implement true function calling where LLM can invoke tools and receive results in a multi-turn conversation
- **Components Created:**
  - `crucible/agents/guidance_agent.py` - AI-native guidance agent with tool support
  - `crucible/services/guidance_service.py` - Service layer with tool creation
  - API endpoints: `POST /chat-sessions/{id}/guidance`, `GET /projects/{id}/workflow-state`
  - Frontend: "Get Help" button in ChatInterface, WorkflowProgress component
  - Tests: Unit tests for guidance agent
- **Why Tools Are Better:**
  - Agent can query for specific information when needed (e.g., "What are my ProblemSpec constraints?")
  - More efficient - only fetch what's needed, not all context upfront
  - More accurate - real-time queries rather than potentially stale context
  - More flexible - agent can explore system dynamically
  - Better aligns with modern AI agent patterns
- **Next:** 
  - Consider implementing native LLM function calling for true tool invocation
  - User testing and refinement based on actual usage patterns

