# Issue 001: Message role enum mismatch: 'assistant' not accepted

**Status**: Resolved  
**Priority**: High  
**Category**: Bug  
**Discovered**: 2025-01-21  
**Resolved**: 2025-01-21  
**Related Story**: (if applicable)

## Description

When opening the Issues view via the Issues button and selecting an issue to get feedback, the system throws an error:

```
Error creating message: 'assistant' is not among the defined enum values. Enum name: messagerole. Possible values: USER, SYSTEM, AGENT
```

This occurs in `ChatInterface.tsx` when calling `triggerIssueFeedback()` to create feedback messages in the chat.

## Steps to Reproduce

1. Open a project
2. Click the "Issues" button to open the Issues panel
3. Select an issue from the list
4. Error appears in console and feedback message fails to create

## Expected Behavior

The feedback message should be created successfully with the role 'agent' (matching the MessageRole enum).

## Actual Behavior

The code attempts to create a message with role 'assistant', which is not a valid enum value. The database enum `MessageRole` only accepts: `USER`, `SYSTEM`, `AGENT`.

## Environment

- **Frontend**: React/Next.js
- **Backend**: FastAPI
- **Database**: PostgreSQL/SQLite with MessageRole enum
- **Location**: `frontend/components/ChatInterface.tsx:510`

## Investigation Notes

### Root Cause Identified

In `frontend/components/ChatInterface.tsx`, line 510:
```typescript
await messagesApi.create(chatSessionId, feedbackMessage, 'assistant', messageMetadata);
```

The code is using `'assistant'` as the role, but the `MessageRole` enum in `crucible/db/models.py` defines:
- `USER = "user"`
- `SYSTEM = "system"`  
- `AGENT = "agent"`

There is no `ASSISTANT` or `'assistant'` value.

### Related Code

- Database model: `crucible/db/models.py` defines `MessageRole` enum
- Frontend API: `frontend/lib/api.ts` defines `Message` interface with role as `'user' | 'system' | 'agent'`
- The mismatch is specifically in `ChatInterface.tsx` where it's hardcoded as `'assistant'`

## Root Cause

The frontend code uses `'assistant'` which doesn't match the database enum. The correct value should be `'agent'` to match the `AGENT` enum value.

## Proposed Solution

Change line 510 in `frontend/components/ChatInterface.tsx` from:
```typescript
await messagesApi.create(chatSessionId, feedbackMessage, 'assistant', messageMetadata);
```

To:
```typescript
await messagesApi.create(chatSessionId, feedbackMessage, 'agent', messageMetadata);
```

Also check line 503 comment that says "Create assistant message" - update to "Create agent message" for consistency.

## Resolution

**Fixed on 2025-01-21**

Changed line 510 in `frontend/components/ChatInterface.tsx` from:
```typescript
await messagesApi.create(chatSessionId, feedbackMessage, 'assistant', messageMetadata);
```

To:
```typescript
await messagesApi.create(chatSessionId, feedbackMessage, 'agent', messageMetadata);
```

Also updated the comment on line 503 from "Create assistant message" to "Create agent message" for consistency.

The fix ensures that the message role matches the `MessageRole` enum values: `USER`, `SYSTEM`, `AGENT` (using `'agent'` instead of `'assistant'`).

---

**Last Updated**: 2025-01-21  
**Updated By**: AI Agent  
**Resolved By**: AI Agent

