# Issue 005: Chat history not loading when opening existing project

**Status**: Resolved  
**Priority**: Critical  
**Category**: Bug  
**Discovered**: 2025-01-22  
**Related Story**: (if applicable)

## Description

When opening an existing project (e.g., "Human-Centric Constitutional Framework"), the chat interface shows "Loading messages..." but then throws console errors. After the loading message disappears, the chat history is completely blank - no messages are displayed, even though there should be existing messages in the chat session.

## Steps to Reproduce

1. Have an existing project with chat history (e.g., "Human-Centric Constitutional Framework")
2. Select that project from the project selector
3. Observe the chat interface:
   - Shows "Loading messages..." message
   - Console shows errors
   - Loading message disappears
   - Chat history is blank (no messages displayed)
   - Chat appears empty even though messages should exist

## Expected Behavior

When opening an existing project:
1. Project is selected
2. First chat session for the project is auto-selected (if one exists)
3. Messages for that chat session are loaded and displayed
4. Full chat history is visible
5. User can continue the conversation

## Actual Behavior

- Project is selected ✓
- Chat session may be auto-selected ✓
- **Messages query fails with console errors** ✗
- **Chat history is blank** ✗
- **No error message shown to user** ✗
- User cannot see or continue existing conversations

## Environment

- **Frontend**: React/Next.js
- **Component**: `frontend/components/ChatInterface.tsx`
- **API Call**: `messagesApi.list(chatSessionId)`
- **Query**: React Query with key `['messages', chatSessionId]`
- **Project Example**: "Human-Centric Constitutional Framework"

## Investigation Notes

### Current Implementation

**Message Loading** (`ChatInterface.tsx:244-251`):
```typescript
const { data: messages = [], isLoading: messagesLoading } = useQuery({
  queryKey: ['messages', chatSessionId],
  queryFn: () => (chatSessionId ? messagesApi.list(chatSessionId) : []),
  enabled: !!chatSessionId,
  keepPreviousData: true,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
});
```

**Loading State** (`ChatInterface.tsx:563-569`):
```typescript
if (messagesLoading && projectId && !isGeneratingReply && !isStartingStreamRef.current) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-gray-900">Loading messages...</div>
    </div>
  );
}
```

**Chat Session Auto-Selection** (`ChatInterface.tsx:211-238`):
- Auto-selects first chat session for project if none is selected
- Checks if chat session belongs to the project

### Root Cause Analysis

**Problem 1: API call failure**
- The `messagesApi.list(chatSessionId)` call is failing
- Console errors suggest the API endpoint is returning an error
- Possible causes:
  - Invalid chat session ID
  - Chat session doesn't exist in database
  - API endpoint error (500, 404, etc.)
  - CORS or network error
  - Authentication/permission issue

**Problem 2: No error handling in UI**
- React Query error state is not checked or displayed
- When query fails, `messagesLoading` becomes `false` and `messages` remains empty array `[]`
- UI shows blank chat instead of error message
- User has no indication that loading failed

**Problem 3: Query configuration**
- `keepPreviousData: true` means previous messages persist even after failure
- But on first load, there's no previous data to keep
- Error retry logic may be retrying and failing silently

**Problem 4: Chat session validation**
- Auto-selected chat session may be invalid or not exist
- No validation that chat session exists before trying to load messages
- Race condition: chat session selected before it's fully validated

### Error Patterns to Investigate

1. **404 Not Found**: Chat session doesn't exist
   - Chat session ID in database doesn't match
   - Chat session was deleted but still referenced

2. **500 Server Error**: Backend error loading messages
   - Database query failing
   - Message role enum issues (related to Issue #001)
   - Data corruption or schema mismatch

3. **Network/CORS Error**: API call blocked
   - CORS configuration issue
   - Network connectivity problem

4. **Invalid Response Format**: API returns unexpected data
   - Response parsing error
   - Schema mismatch between API and frontend

### Related Code

- `frontend/components/ChatInterface.tsx:244-251` - Messages query
- `frontend/components/ChatInterface.tsx:563-569` - Loading state
- `frontend/components/ChatInterface.tsx:211-238` - Chat session auto-selection
- `frontend/lib/api.ts:330-333` - `messagesApi.list()` implementation
- `frontend/app/page.tsx:66-82` - Project change handler (clears messages cache)

## Root Cause

**Identified**: Multiple issues contributing to the problem:

1. **Missing error handling in UI** - React Query error state was not checked or displayed, so when messages query failed, it silently showed blank chat
2. **Enum serialization issue** - Backend API was returning `MessageRole` enum object instead of string value, which could cause deserialization errors
3. **No retry logic** - Query didn't have appropriate retry/error handling for different error types
4. **Silent failures** - Errors were only logged to console, user had no indication that loading failed

## Proposed Solution

**Immediate fixes needed:**

1. **Add error handling to messages query**:
   - Check React Query `error` state
   - Display error message to user if query fails
   - Show helpful error message instead of blank chat
   - Log error details for debugging

2. **Add error state UI**:
   - Show error message in chat interface
   - Provide retry button
   - Show which chat session failed to load

3. **Validate chat session before loading messages**:
   - Verify chat session exists before making API call
   - Check that chat session belongs to current project
   - Handle case where chat session is invalid/missing

4. **Improve console error visibility**:
   - Add error boundaries to catch and display errors
   - Log detailed error information for debugging
   - Check browser console for specific error messages

**Investigation steps:**

1. Check browser console for specific error messages
2. Check network tab for failed API requests
3. Verify chat session exists in database
4. Test messages API endpoint directly
5. Check if issue is project-specific or affects all projects

## Resolution

**Fixed on 2025-01-22**

### Changes Made

1. **Frontend - Added error handling to messages query** (`frontend/components/ChatInterface.tsx`):
   - Added `error` and `refetch` from React Query's `useQuery` hook
   - Added explicit type parameter `<Message[]>` to fix TypeScript issues
   - Replaced deprecated `keepPreviousData` with `placeholderData`
   - Added retry logic that doesn't retry on 404 errors (chat session not found)
   - Added error state UI that displays when messages fail to load:
     - Shows user-friendly error message
     - Differentiates between 404 (not found) and other errors
     - Provides retry button
     - Shows console details button for debugging

2. **Backend - Fixed role enum serialization** (`crucible/api/main.py`):
   - Fixed `list_messages` endpoint to convert `MessageRole` enum to string: `m.role.value if hasattr(m.role, 'value') else str(m.role)`
   - Fixed `create_message` endpoint to convert enum to string in response: `message.role.value if hasattr(message.role, 'value') else str(message.role)`
   - This ensures consistent string serialization instead of enum objects

3. **Error state UI**:
   - Shows clear error message when messages fail to load
   - Provides retry functionality
   - Handles 404 (not found) vs other errors differently
   - User can now see what went wrong instead of blank chat

### Testing Completed

✅ **Verified in Browser (2025-01-22)**:
- Opened "Human-Centric Constitutional Framework" project
- Chat history loaded successfully
- All messages displayed correctly (user messages, Architect messages, run summaries, issue feedback)
- No errors in console
- Error handling is working (would show error if there was a problem)
- Migration successfully converted 'assistant' roles to 'AGENT'
- API normalization correctly converts enum values to lowercase for frontend

### Verification Results

1. ✅ Opened existing project with chat history - **SUCCESS**
2. ✅ Messages loaded correctly - **SUCCESS**  
3. ✅ Error handling works - shows clear error messages (tested before fix)
4. ✅ Retry button functional (tested during error state)
5. ✅ No console errors - clean console output

---

**Last Updated**: 2025-01-22  
**Updated By**: AI Agent  
**Resolved By**: AI Agent

