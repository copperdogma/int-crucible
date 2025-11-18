# Story: Implement native LLM function calling for guidance agent

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Interaction shell (MVP UI) should guide users through the process.
  - The system should feel natural and guide users through the workflow.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – The user interacts via chat sessions with guidance agents.
  - The system should provide intelligent, adaptive guidance that can query the system dynamically.

## Problem Statement
Currently, the guidance agent has access to tools conceptually (they're described in prompts), but it cannot actually invoke them. The agent receives tool descriptions in its prompt and can reference them, but there's no mechanism for the LLM to:
1. Decide which tool to call based on the user's question
2. Automatically invoke the tool with the correct parameters
3. Receive tool results and continue reasoning
4. Make multiple tool calls in a single guidance session

This limits the agent's ability to provide accurate, real-time guidance. For example, if a user asks "What constraints are in my ProblemSpec?", the agent can only guess based on initial context rather than querying the actual ProblemSpec.

## Acceptance Criteria
- The guidance agent uses native LLM function calling (Claude tool use API or OpenAI functions):
  - LLM can decide to call tools based on user queries
  - Tools are automatically invoked with correct parameters
  - Tool results are fed back to the LLM for continued reasoning
  - Multi-turn tool calling is supported (agent can call multiple tools in sequence)
- Tool integration:
  - Tool functions are properly registered with the LLM provider
  - Tool schemas are correctly defined (parameters, return types)
  - Tool execution errors are handled gracefully
  - Tool results are formatted appropriately for the LLM
- The agent can:
  - Answer specific questions by querying relevant data (e.g., "What are my constraints?" → calls `get_problem_spec`)
  - Provide accurate guidance based on real-time system state
  - Explore the system dynamically to answer complex questions
  - Chain tool calls when needed (e.g., get ProblemSpec, then get WorldModel, then compare)
- Backward compatibility:
  - Falls back gracefully if LLM provider doesn't support function calling
  - Falls back to context-based approach if tools unavailable
- Performance:
  - Tool calls don't significantly slow down guidance responses
  - Tool results are cached when appropriate to avoid redundant queries

## Tasks
- [ ] Research and select LLM function calling approach:
  - [ ] Evaluate Claude tool use API support in Kosmos
  - [ ] Evaluate OpenAI function calling support in Kosmos
  - [ ] Determine which provider(s) to support initially
  - [ ] Document the chosen approach
- [ ] Extend LLM provider interface (if needed):
  - [ ] Add function calling support to `LLMProvider` base class (or verify existing support)
  - [ ] Implement function calling in provider implementations (Anthropic, OpenAI)
  - [ ] Add tool schema definition format
  - [ ] Add tool result handling
- [ ] Implement tool schema generation:
  - [ ] Create function to generate tool schemas from tool functions
  - [ ] Define parameter types and descriptions
  - [ ] Handle optional parameters and defaults
  - [ ] Validate tool schemas
- [ ] Implement tool execution loop:
  - [ ] Parse LLM function call requests
  - [ ] Validate function call parameters
  - [ ] Execute tool functions with parameters
  - [ ] Format tool results for LLM
  - [ ] Continue LLM conversation with tool results
  - [ ] Support multi-turn tool calling (agent can call multiple tools)
- [ ] Update GuidanceAgent to use function calling:
  - [ ] Register tools with LLM provider using schemas
  - [ ] Handle function call responses from LLM
  - [ ] Execute tools and feed results back
  - [ ] Support iterative tool calling until guidance is complete
- [ ] Update GuidanceService:
  - [ ] Ensure tool functions are properly defined and callable
  - [ ] Add error handling for tool execution
  - [ ] Add logging for tool calls (for debugging and monitoring)
- [ ] Add tests:
  - [ ] Test tool schema generation
  - [ ] Test tool execution loop
  - [ ] Test multi-turn tool calling
  - [ ] Test error handling (invalid tool calls, tool execution errors)
  - [ ] Test fallback behavior when function calling unavailable
- [ ] Update documentation:
  - [ ] Document tool calling architecture
  - [ ] Document how to add new tools
  - [ ] Document tool schema format
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- **Prerequisite:** Story 007b (interactive guidance agent) must be complete, as this builds on the tool infrastructure established there.
- **Current State:** The guidance agent has tool functions available, but they're only described in prompts. This story implements true tool invocation.
- **Design Philosophy:** 
  - Use native LLM function calling APIs rather than prompt-based tool descriptions
  - Support multi-turn conversations where the agent can call tools, see results, and continue reasoning
  - Maintain backward compatibility with providers that don't support function calling
- **Technical Considerations:**
  - Claude's tool use API uses a different format than OpenAI's function calling
  - May need to abstract tool calling behind a unified interface
  - Tool execution should be fast - consider async execution for multiple tools
  - Tool results should be concise but informative (token efficiency)
- **Future Enhancements:**
  - Tool result caching to avoid redundant queries
  - Tool call analytics (which tools are used most, etc.)
  - Dynamic tool discovery (agent can discover available tools)
  - Tool composition (tools that call other tools)

