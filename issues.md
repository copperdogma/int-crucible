# Issue Tracking

Int Crucible

**Note**: This document tracks issues discovered during testing and development. Issues may be bugs, performance problems, UX issues, or feature gaps that need investigation before potentially becoming user stories.

---

## Issue Status Legend

- **Open** - Issue discovered, not yet investigated
- **Investigating** - Currently being investigated by AI agent or developer
- **Needs Story** - Investigation complete, issue should become a user story
- **Resolved** - Issue fixed or addressed
- **Won't Fix** - Issue documented but won't be addressed (with rationale)

## Priority Levels

- **Critical** - System breaking, blocks core functionality
- **High** - Significant impact, should be addressed soon
- **Medium** - Moderate impact, address when convenient
- **Low** - Minor impact, nice to have

---

## Issue List

| Issue ID | Title | Status | Priority | Category | Discovered | Related Story |
|----------|-------|--------|----------|----------|------------|---------------|
| 001 | Message role enum mismatch: 'assistant' not accepted | Resolved | High | Bug | 2025-01-21 | |
| 002 | Flag Issue dialog needs better Issue Type descriptions | Open | Medium | UX | 2025-01-21 | |
| 003 | Results don't match goals - minimal constitution solutions not generated | Open | Critical | Bug/Logic | 2025-01-21 | |
| 004 | "View In Chat" button doesn't trigger feedback properly | Open | High | Bug | 2025-01-22 | |
| 005 | Chat history not loading when opening existing project | Resolved | Critical | Bug | 2025-01-22 | |
| 006 | Remediation "Approve & Apply" fails when issue has no run_id | Resolved | High | Bug | 2025-01-22 | ✅ Validated 2025-01-22 |
| 007 | Remediation "Approve & Apply" button unclear about what it will do | Resolved | High | UX | 2025-01-22 | ✅ Validated 2025-01-22 |

---

## How to Use This System

### For Humans
1. **Add new issues**: Add a row to the table above with issue ID, title, status (Open), priority, category, and date discovered
2. **Investigate issues**: Create detailed investigation notes (can be in issue files in `/docs/issues/` if complex)
3. **Update status**: Change status as you investigate (Open → Investigating → Needs Story / Resolved / Won't Fix)
4. **Link stories**: When an issue becomes a story, add the story ID in the "Related Story" column

### For AI Agents
1. **Read issues**: Check this file to see what needs investigation
2. **Investigate**: When status is "Open" or "Investigating", gather information, reproduce, analyze root cause
3. **Document findings**: Add investigation notes (in issue files or inline comments)
4. **Recommend action**: Suggest whether issue should become a story, be fixed directly, or be closed
5. **Update status**: Update the status based on investigation outcome

### Issue File Format
For complex issues, create individual issue files in `/docs/issues/` following this format:

```markdown
# Issue [ID]: [Title]

**Status**: Open  
**Priority**: High  
**Category**: Bug  
**Discovered**: 2025-11-21  
**Related Story**: (if applicable)

## Description
[Clear description of the issue]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Investigation Notes
[Notes from investigation]

## Root Cause
[If identified]

## Proposed Solution
[If identified]

## Resolution
[How it was resolved, or why it won't be fixed]
```

---

## Notes
- Issues can be discovered during testing, user reports, code review, or system monitoring
- Investigation should determine if issue warrants a story or can be fixed directly
- Critical and High priority issues should be investigated promptly
- Keep investigation notes concise but actionable

