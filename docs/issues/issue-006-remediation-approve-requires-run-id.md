# Issue 006: Remediation "Approve & Apply" fails when issue has no run_id

**Status**: Resolved  
**Priority**: High  
**Category**: Bug  
**Discovered**: 2025-01-22  
**Resolved**: 2025-01-22  
**Related Story**: (if applicable)

## Description

When clicking "Approve & Apply" on a remediation proposal for an issue, the system throws an error:

```
Issue aa3c0c60-4f7c-4d80-b999-2edb9e3bb1b1 has no associated run_id for rescoring
```

This occurs when an issue doesn't have a `run_id` but the remediation action (likely "patch_and_rescore" or similar) requires one.

## Steps to Reproduce

1. Open a project (e.g., "Human-Centric Constitutional Framework")
2. Flag an issue (without a specific run context, or from the Spec Panel)
3. View the issue in the Issues panel
4. Click "View in Chat" to trigger feedback agent
5. Receive remediation proposal in chat
6. Click "Approve & Apply" button
7. Error appears: "Issue ... has no associated run_id for rescoring"

## Expected Behavior

When approving a remediation action:
1. System should check if the remediation action requires a `run_id`
2. If issue doesn't have `run_id` and action requires it:
   - Either: Use a different remediation action that doesn't require run_id
   - Or: Show a helpful error message explaining why the action can't be applied
   - Or: Allow user to select a run_id if multiple runs exist
3. If issue has `run_id` or action doesn't require it, proceed with remediation

## Actual Behavior

- Clicking "Approve & Apply" immediately throws an error
- No validation before attempting to apply remediation
- Error message is technical and not user-friendly
- User has no way to resolve the issue (can't select a run_id)

## Environment

- **Frontend**: React/Next.js
- **Component**: `frontend/components/RemediationProposalCard.tsx`
- **API Call**: Remediation action endpoint
- **Issue ID**: `aa3c0c60-4f7c-4d80-b999-2edb9e3bb1b1`
- **Error Location**: `lib/api.ts:253` in `apiFetch`

## Investigation Notes

### Current Implementation Flow

1. **RemediationProposalCard.tsx** - User clicks "Approve & Apply"
2. Calls API endpoint to resolve issue with remediation action
3. API checks if action requires `run_id`
4. If issue has no `run_id`, API returns error
5. Error bubbles up to frontend and displays as error

### Error Analysis

The error message "Issue ... has no associated run_id for rescoring" suggests:
- The remediation action type (likely `patch_and_rescore`) requires a `run_id`
- The issue was created without a `run_id` (possibly from Spec Panel, not from Results View)
- No fallback or alternative remediation path exists

### Remediation Action Types

Based on Story 009, remediation actions include:
- `patch_and_rescore` - Updates ProblemSpec/WorldModel and re-scores existing candidates (requires run_id)
- `partial_rerun` - Updates ProblemSpec/WorldModel and re-runs evaluation/ranking (may require run_id)
- `full_rerun` - Creates new run from scratch (doesn't require run_id)
- `invalidate_candidates` - Marks candidates as rejected (requires run_id and candidate_ids)

### Root Cause Hypothesis

1. **Issue created without run context**: Issues can be created from Spec Panel, which doesn't have a run_id
2. **Remediation action selection**: Feedback agent may recommend `patch_and_rescore` or `partial_rerun` for issues without run_id
3. **Missing validation**: No validation checks if issue has required context before recommending/approving remediation
4. **No fallback logic**: System doesn't automatically choose alternative actions when prerequisites aren't met

### Related Code

- `frontend/components/RemediationProposalCard.tsx` - Approval handler
- `frontend/lib/api.ts` - API call to resolve issue
- `crucible/api/main.py` - Remediation action endpoint
- `crucible/services/issue_service.py` - Remediation action logic
- `crucible/services/feedback_service.py` - Remediation proposal generation

## Root Cause

**Identified**: The remediation actions `patch_and_rescore` and `partial_rerun` require a `run_id` to operate (they need to re-score or re-evaluate existing candidates from a run). However:

1. **Issues can be created without run context** - Issues can be flagged from the Spec Panel, which doesn't have a `run_id`
2. **Feedback agent doesn't check context** - The feedback agent may recommend `patch_and_rescore` or `partial_rerun` without checking if the issue has a `run_id`
3. **No validation before execution** - The API endpoint doesn't validate prerequisites before attempting remediation
4. **No graceful fallback** - When prerequisites aren't met, system throws error instead of using alternative actions

## Proposed Solution

**Option 1: Pre-validate before applying**
- Check if issue has required context before attempting remediation
- Show user-friendly error if prerequisites not met
- Suggest which runs exist that could be used

**Option 2: Auto-select appropriate action**
- If action requires run_id but issue doesn't have one, automatically use `full_rerun` instead
- Or prompt user to select which run to use

**Option 3: Better feedback agent logic**
- Feedback agent should check issue context before recommending actions
- Recommend `full_rerun` for issues without run_id
- Only recommend `patch_and_rescore` / `partial_rerun` if run_id exists

**Option 4: Allow run selection in UI**
- If issue has no run_id but action requires it, show a dropdown to select a run
- Or prompt user to select run before approving

**Recommended Approach**: Combine Option 1 and Option 3:
- Improve feedback agent to recommend appropriate actions based on issue context
- Add validation in remediation approval to check prerequisites
- Show user-friendly error with suggestions if prerequisites not met
- Consider auto-upgrading to `full_rerun` if `patch_and_rescore` requested but no run_id

## Resolution

**Fixed on 2025-01-22**

### Changes Made

1. **Backend - Auto-upgrade logic** (`crucible/api/main.py`):
   - Added validation in `resolve_issue` endpoint to check if remediation action requires `run_id`
   - If `patch_and_rescore` or `partial_rerun` is requested but issue has no `run_id`, automatically upgrade to `full_rerun`
   - Return informative message explaining the auto-upgrade
   - Return metadata (`action_upgraded`, `original_remediation_action`) in response

2. **Frontend - Enhanced user feedback** (`frontend/components/RemediationProposalCard.tsx`):
   - Updated to handle auto-upgrade scenario
   - Show informative success message when action is auto-upgraded
   - Display both original and actual action types for transparency

3. **API Response Type** (`frontend/lib/api.ts`):
   - Added `original_remediation_action` and `action_upgraded` fields to response type
   - Frontend can now detect and display upgrade information

### Solution Details

**Auto-upgrade logic:**
- If issue has no `run_id` and action requires it (`patch_and_rescore`, `partial_rerun`), automatically use `full_rerun` instead
- `full_rerun` doesn't require a `run_id` because it creates a new run from scratch
- User is informed about the upgrade via success message

**User Experience:**
- No error thrown - remediation still proceeds
- User sees clear message explaining what happened
- Action is appropriate for the context (full rerun when no run exists)

### Testing Completed ✅

- ✅ Test remediation approval for issue without run_id - **PASSED**
- ✅ Verify auto-upgrade message is displayed - **PASSED**
- ✅ Test remediation approval for issue with run_id (should proceed normally) - **PASSED**
- ✅ Verify `full_rerun` actually executes correctly when auto-upgraded - **PASSED**
- ✅ Integration tests added: 4 new tests covering all scenarios - **ALL PASSING**
- ✅ Browser testing confirmed UI improvements work correctly - **VERIFIED**

**Validation Status**: ✅ Validated and verified on 2025-01-22

---

**Last Updated**: 2025-01-22  
**Updated By**: AI Agent  
**Resolved By**: AI Agent  
**Validated By**: AI Agent (2025-01-22)

