# Story: Improve UI chat experience with streaming and automatic responses

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Target Audience** – The first user is the system's creator, a technically sophisticated solo user who should feel natural using the system.
  - **Key Features** – Interaction shell (MVP UI) should feel like a natural conversation.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – The user interacts via chat sessions with an "Architect/ProblemSpec" agent.
  - The system should feel natural and guide users through the workflow.
  - The chat interface should be responsive and provide clear feedback.

## Problem Statement
The current chat interface has several UX issues:

1. **No Busy Indicator**: When the AI is processing a response, there's no visual feedback to the user that the system is working. The user might think the system is frozen or unresponsive.

2. **No Streaming**: Chat responses appear all at once after the full response is generated, making the interface feel slow and unresponsive. Users expect to see responses stream in character-by-character or word-by-word like modern AI chat interfaces.

3. **"Get Help" Button is Awkward**: The current interface requires users to click a "Get Help" button to get agent responses. This breaks the natural flow of conversation. Users expect a back-and-forth chat where the agent responds automatically after each user message, just like a regular AI chat interface (ChatGPT, Claude, etc.).

## Acceptance Criteria
- **Busy Indicator**:
  - A visual indicator (spinner, loading animation, or typing indicator) appears when the AI is processing a response
  - The indicator is clearly visible and positioned appropriately (e.g., in the message area or input area)
  - The indicator disappears when the response is complete
  - The input field is disabled or shows appropriate feedback during processing
- **Streaming Responses**:
  - Agent responses stream in character-by-character or word-by-word as they are generated
  - The streaming feels smooth and natural (not choppy)
  - Users can see the response being built in real-time
  - The message area auto-scrolls to follow the streaming response
  - If streaming fails, the full response is still displayed
- **Automatic Agent Responses**:
  - The "Get Help" button is removed from the UI
  - After each user message, the agent automatically generates and displays a response
  - The agent response is contextual and relevant to the conversation
  - The agent can use the Guidance agent or a dedicated chat agent to provide responses
  - The response appears in the chat as a normal message (role: "agent")
  - The conversation feels natural and back-and-forth
- **Error Handling**:
  - If the agent fails to respond, an error message is shown
  - The user can retry sending the message
  - Errors don't break the chat flow
- **Performance**:
  - Streaming doesn't significantly impact performance
  - The UI remains responsive during streaming
  - Long responses don't cause UI lag

## Tasks
- [ ] Remove "Get Help" button from ChatInterface:
  - [ ] Remove the button from the UI
  - [ ] Remove `handleGetHelp` function and related state (`isRequestingGuidance`)
  - [ ] Clean up any unused imports or code
- [ ] Add busy/loading indicator:
  - [ ] Add visual indicator (spinner or typing indicator) that shows when AI is processing
  - [ ] Show indicator in message area (e.g., as a placeholder message bubble)
  - [ ] Show indicator in input area (e.g., disable input, show "AI is thinking..." text)
  - [ ] Ensure indicator appears immediately when user sends message
  - [ ] Ensure indicator disappears when response is complete
- [ ] Implement automatic agent responses:
  - [ ] Modify `handleSend` to trigger agent response after user message
  - [ ] Create or use existing endpoint for chat responses (may need to add new endpoint)
  - [ ] Ensure agent response is contextual (uses chat history, project state)
  - [ ] Add agent response as a message with role "agent"
  - [ ] Handle errors gracefully (show error message, allow retry)
- [ ] Implement streaming responses:
  - [ ] Add backend support for streaming (Server-Sent Events or similar)
  - [ ] Create streaming endpoint for chat responses
  - [ ] Update frontend to handle streaming responses
  - [ ] Display streaming text character-by-character or word-by-word
  - [ ] Auto-scroll message area during streaming
  - [ ] Handle streaming errors gracefully
- [ ] Update API client:
  - [ ] Add streaming support to `messagesApi` or create new streaming API
  - [ ] Handle Server-Sent Events or similar streaming protocol
  - [ ] Update TypeScript types if needed
- [ ] Test and refine:
  - [ ] Test with various message lengths
  - [ ] Test error cases (network errors, API errors)
  - [ ] Test streaming performance
  - [ ] Ensure UI remains responsive
  - [ ] Verify conversation flow feels natural
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- **Prerequisite**: This builds on existing chat infrastructure from stories 007 and 007b.
- **Design Approach**:
  - Use Server-Sent Events (SSE) for streaming if possible (simpler than WebSockets for one-way streaming)
  - Consider using the Guidance agent for automatic responses, or create a dedicated chat agent
  - The busy indicator should be subtle but clear
  - Streaming speed should feel natural (not too fast, not too slow)
- **Technical Considerations**:
  - FastAPI supports streaming responses via `StreamingResponse`
  - React can handle SSE with `EventSource` or fetch with streaming
  - Need to handle connection errors and retries
  - May need to buffer responses if streaming is too fast
- **Future Enhancements**:
  - Markdown rendering for agent responses
  - Code syntax highlighting
  - Copy/paste functionality for messages
  - Message editing/deletion
  - Conversation history search

## Work Log

### 20250118-XXXX — Story creation
- **Result:** Created story 008c for UI chat improvements
- **User Requirements:**
  1. UI needs a busy indicator when waiting for AI response
  2. Chat responses should stream in (character-by-character or word-by-word)
  3. Remove "Get Help" button - make it a regular back-and-forth chat where agent responds automatically
- **Next:** Begin implementation planning

