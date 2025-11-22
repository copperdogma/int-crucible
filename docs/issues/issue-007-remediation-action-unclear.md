# Issue 007: Remediation "Approve & Apply" button unclear about what it will do

**Status**: Resolved  
**Priority**: High  
**Category**: UX  
**Discovered**: 2025-01-22  
**Resolved**: 2025-01-22  
**Related Story**: (if applicable)

## Description

When viewing a remediation proposal in the chat, the "Approve & Apply" button doesn't clearly communicate what action will be taken. Users are unsure if it will:
- Re-run the entire pipeline (time-consuming, expensive)
- Just update the ProblemSpec/WorldModel
- Re-score existing candidates
- Create a new run

The lack of clarity makes users hesitant to click the button, especially since full reruns can be time-consuming and expensive.

## Steps to Reproduce

1. Flag an issue (e.g., from Spec Panel or Results View)
2. View the issue in chat (via "View in Chat" button)
3. Receive remediation proposal from feedback agent
4. Observe the "Approve & Apply" button
5. Notice it's unclear what will happen when clicked

## Expected Behavior

The remediation proposal should clearly communicate:
1. **What action will be taken** - e.g., "This will create a new full run" or "This will update the spec and re-score existing candidates"
2. **Estimated impact** - Time, cost, what will be affected
3. **Confirmation for expensive actions** - For `full_rerun`, show a confirmation dialog explaining it will take time and cost money
4. **Visual indicators** - Use colors/icons to indicate severity/cost of action

## Actual Behavior

- Button just says "Approve & Apply" with no context
- Remediation proposal card shows action type but doesn't explain what it means
- No indication of time/cost implications
- No confirmation for expensive actions
- User has to guess what will happen

## Environment

- **Frontend**: React/Next.js
- **Component**: `frontend/components/RemediationProposalCard.tsx`
- **Remediation Actions**: `patch_and_rescore`, `partial_rerun`, `full_rerun`, `invalidate_candidates`

## Investigation Notes

### Current Implementation

**RemediationProposalCard.tsx** shows:
- Action type label (e.g., "Patch and Rescore", "Full Rerun")
- Description from feedback agent
- Estimated impact (text from feedback agent)
- Rationale (text from feedback agent)
- "Approve & Apply" button

**Remediation Action Types:**
- `patch_and_rescore` - Updates ProblemSpec/WorldModel, re-runs evaluation+ranking only (fast, low cost)
- `partial_rerun` - Updates ProblemSpec/WorldModel, re-runs evaluation+ranking phases (moderate time/cost)
- `full_rerun` - Updates ProblemSpec/WorldModel, creates new full run (slow, expensive)
- `invalidate_candidates` - Marks candidates as rejected (fast, no cost)

### User Confusion Points

1. **Action type labels are technical** - "Patch and Rescore" doesn't clearly communicate what it does
2. **No time/cost estimates** - User doesn't know if it will take seconds or minutes
3. **No confirmation for expensive actions** - `full_rerun` should have a confirmation step
4. **Description may be vague** - Feedback agent's description might not be clear enough
5. **No visual hierarchy** - All actions look the same, no indication of severity/cost

### Related Code

- `frontend/components/RemediationProposalCard.tsx` - Remediation proposal display
- `crucible/services/issue_service.py` - Remediation action implementations
- `crucible/agents/feedback_agent.py` - Remediation proposal generation

## Root Cause

The UI doesn't provide enough context about:
1. What the remediation action will actually do
2. How long it will take
3. What resources it will consume
4. What will be affected

The remediation proposal relies on the feedback agent's description, which may not be clear enough for users to understand the implications.

## Proposed Solution

**Option 1: Enhanced action descriptions**
- Add clear, user-friendly descriptions for each action type
- Explain what will happen in simple terms
- Include time/cost estimates if available

**Option 2: Confirmation dialog for expensive actions**
- Show confirmation dialog for `full_rerun` actions
- Explain that it will create a new run and may take time
- Allow user to cancel or proceed

**Option 3: Visual indicators**
- Use color coding or icons to indicate action severity/cost
- Green for fast/cheap actions, yellow for moderate, red for expensive
- Add warning icons for expensive actions

**Option 4: Action summary section**
- Add a prominent "What will happen" section at the top
- Bullet points explaining the steps
- Estimated duration and cost

**Recommended Approach**: Combine all options:
- Add clear action descriptions with "What will happen" section
- Add visual indicators (colors, icons) for action severity
- Add confirmation dialog for `full_rerun` actions
- Show time/cost estimates if available from run history

## Resolution

**Fixed on 2025-01-22**

### Changes Made

1. **Added "What will happen" section** (`frontend/components/RemediationProposalCard.tsx`):
   - Prominent section at the top of the remediation card
   - Clear explanation of what the action will do
   - Shows time estimate (Fast/Moderate/Slow)
   - Shows cost estimate (Low/Moderate/High)
   - Shows impact (what will be affected)

2. **Action-specific explanations**:
   - `patch_and_rescore`: "Update ProblemSpec/WorldModel, then re-score existing candidates" - Fast, Low cost
   - `partial_rerun`: "Update ProblemSpec/WorldModel, then re-run evaluation and ranking" - Moderate, Moderate cost
   - `full_rerun`: "Update ProblemSpec/WorldModel, then create a completely new run from scratch" - Slow, High cost
   - `invalidate_candidates`: "Mark specific candidates as rejected" - Instant, No cost

3. **Confirmation dialog for expensive actions**:
   - `full_rerun` actions now show a confirmation dialog before proceeding
   - Dialog clearly explains what will happen
   - Warns about time (several minutes to hours) and cost (LLM resources)
   - User must explicitly confirm to proceed

4. **Visual indicators**:
   - Warning icon (⚠️) for actions requiring confirmation
   - Red button color for expensive actions (`full_rerun`)
   - Green button color for safe actions
   - Button text changes: "⚠️ Approve & Start Full Run" for full_rerun

5. **Enhanced button text**:
   - Button text is more descriptive based on action type
   - Shows warning icon for expensive actions
   - Makes it clear what will happen when clicked

### User Experience Improvements

**Before:**
- Button just said "Approve & Apply"
- No indication of what would happen
- No time/cost information
- No confirmation for expensive actions

**After:**
- Clear "What will happen" section with action, time, cost, and impact
- Visual warning indicators for expensive actions
- Confirmation dialog for `full_rerun` actions
- More descriptive button text
- Users can make informed decisions before clicking

### Testing Completed ✅

- ✅ Test remediation proposal display for each action type - **VERIFIED**
- ✅ Verify "What will happen" section shows correct information - **VERIFIED**
- ✅ Test confirmation dialog appears for `full_rerun` actions - **VERIFIED**
- ✅ Verify confirmation dialog can be cancelled - **VERIFIED**
- ✅ Test that confirmation dialog proceeds correctly when confirmed - **VERIFIED**
- ✅ Verify button colors and text are appropriate for each action type - **VERIFIED**
- ✅ Browser testing confirmed all UI elements work correctly - **VERIFIED**

**Validation Status**: ✅ Validated and verified on 2025-01-22

---

**Last Updated**: 2025-01-22  
**Updated By**: AI Agent  
**Resolved By**: AI Agent  
**Validated By**: AI Agent (2025-01-22)

