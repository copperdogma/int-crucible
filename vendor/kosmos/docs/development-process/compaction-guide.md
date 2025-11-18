# Comprehensive Compaction Guide for Kosmos Development

This guide consolidates all compaction-related documentation for Claude Code instances working on Kosmos.

## Table of Contents
1. [Quick Reference Decision Tree](#quick-reference-decision-tree)
2. [Pre-Compaction Checklist](#pre-compaction-checklist)
3. [Mid-Phase Compaction Process](#mid-phase-compaction-process)
4. [Checkpoint Document Template](#checkpoint-document-template)
5. [Quick Recovery Prompts](#quick-recovery-prompts)

---

## Quick Reference Decision Tree

### When to Compact?

```
Context Usage Check
├─ < 120K tokens (60%)
│  └─ ✅ Continue working normally
│
├─ 120K-160K tokens (60-80%)
│  ├─ Task nearly complete?
│  │  ├─ Yes → Finish task, then compact
│  │  └─ No → Create checkpoint now, compact
│  └─ Multiple tasks remaining?
│      └─ Yes → Compact now
│
└─ > 160K tokens (80%)
   └─ ⚠️ COMPACT IMMEDIATELY
```

### Compaction Decision Flow

```
Are you mid-task?
├─ YES
│  ├─ Can finish in < 10K tokens?
│  │  ├─ YES → Finish task, create checkpoint, compact
│  │  └─ NO  → Create checkpoint mid-task, compact
│  └─ Is task at logical breakpoint?
│      ├─ YES → Create checkpoint, compact
│      └─ NO  → Find nearest breakpoint, checkpoint, compact
│
└─ NO (between tasks)
   └─ ✅ IDEAL TIME TO COMPACT
      1. Create checkpoint
      2. Commit work
      3. Run /compact
```

### What to Do Before Compacting?

1. **Always Create Checkpoint Document**
   - Use template from [Checkpoint Document Template](#checkpoint-document-template)
   - Document current task status
   - List completed sub-tasks
   - Provide recovery instructions

2. **Always Commit to Git**
   - Commit all changes with detailed message
   - Push to GitHub
   - Verify commit shows in remote

3. **Provide Resume Prompt**
   - Clear, concise prompt for next Claude instance
   - Include current task number and status
   - List immediate next steps

---

## Pre-Compaction Checklist

### Essential Steps (Do Every Time)

- [ ] **Check context usage**: Verify approaching limit (run command to check)
- [ ] **Current task status**: Note what you're working on
- [ ] **Files modified**: List all files changed in current session
- [ ] **Tests passing**: Run tests if code was modified
- [ ] **Checkpoint document**: Create detailed checkpoint (see template below)
- [ ] **Commit changes**: `git add -A && git commit -m "..."`
- [ ] **Push to GitHub**: `git push origin master`
- [ ] **Resume prompt**: Prepare clear prompt for next instance
- [ ] **Verify commit**: Check GitHub shows latest commit

### Checkpoint Document Requirements

**Mandatory Sections**:
1. Current Task Status (what you're working on)
2. Completed Sub-Tasks (what's done)
3. Files Modified (full list with line counts)
4. Code Changes (key snippets or full diffs)
5. Decisions Made (technical decisions with rationale)
6. Next Steps (clear instructions)
7. Recovery Instructions (how to resume)
8. Quick Resume Prompt (copy-paste ready)

### Git Commit Best Practices

```bash
# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Task X: Brief description

- Completed: Sub-task 1
- Completed: Sub-task 2
- In Progress: Sub-task 3

Files modified:
- file1.py (~100 lines)
- file2.py (~50 lines)

Next: Complete sub-task 3

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin master
```

---

## Mid-Phase Compaction Process

### When Mid-Phase Compaction is Needed

**Triggers**:
- Context usage > 120K tokens (60%)
- Multiple tasks remaining in phase
- Task is complex and will take significant tokens
- Natural breakpoint in task (e.g., completed sub-task)

### Process Steps

#### 1. Assess Current State
```
Current Task: Task X - Description
Progress: Sub-task 1 ✅, Sub-task 2 ✅, Sub-task 3 🔄 (50%)
Context Usage: XXX,XXX / 200,000 tokens (XX%)
Files Modified: N files
Tests: Passing / Failing / Not Run
```

#### 2. Create Checkpoint Document

**Filename Format**: `docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md`

**Example**: `docs/PHASE_10_TASK_32_CHECKPOINT_2024-11-13.md`

Use the [Checkpoint Document Template](#checkpoint-document-template) below.

#### 3. Commit Work

```bash
# Review changes
git status
git diff

# Stage all
git add -A

# Commit with checkpoint reference
git commit -m "Task X checkpoint: Brief status

Current progress:
- ✅ Sub-task 1
- ✅ Sub-task 2
- 🔄 Sub-task 3 (50% complete)

Checkpoint: docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md

Next: Complete sub-task 3, then proceed to sub-task 4

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push
git push origin master
```

#### 4. Prepare Resume Information

**For User**: Provide a clear, copy-paste ready prompt:

```
Task X (Sub-task 3) checkpoint created.

Quick Resume Prompt:
---
Continue Task X: [Brief description]

Current status: Sub-task 3 is 50% complete
Completed: Sub-tasks 1, 2
Remaining: Complete sub-task 3, then sub-tasks 4, 5

Last work: [Brief description of what you were doing]
Next: [Clear next step]

Checkpoint: docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md
---

You can now run /compact
```

#### 5. User Runs /compact

User runs `/compact` command to compress context.

#### 6. Resume in New Instance

New Claude instance receives the resume prompt and:
1. Reads checkpoint document
2. Reviews recent git commits
3. Continues from documented state

---

## Checkpoint Document Template

Use this template for all checkpoint documents:

```markdown
# Phase X Task Y Checkpoint - YYYY-MM-DD

**Date**: YYYY-MM-DD HH:MM
**Phase**: X
**Task**: Y - Task Name
**Context Usage**: XXX,XXX / 200,000 tokens (XX%)
**Status**: In Progress / Blocked / Complete

---

## Current Task Status

**Task Y**: Task Name and Description

**Progress**:
- ✅ Sub-task 1: Description
- ✅ Sub-task 2: Description
- 🔄 Sub-task 3: Description (XX% complete)
- ⏳ Sub-task 4: Description (pending)
- ⏳ Sub-task 5: Description (pending)

**Current Focus**: Detailed description of what you're currently working on.

**Blockers**: None / List any blockers

---

## Completed This Session

### Sub-task 1: Description ✅
**Files**: `path/to/file1.py`, `path/to/file2.py`
**Changes**: Brief description of changes
**Lines**: ~XXX lines added/modified
**Tests**: Passing / Written / N/A

### Sub-task 2: Description ✅
**Files**: `path/to/file3.py`
**Changes**: Brief description
**Lines**: ~XXX lines
**Tests**: Passing

---

## Files Modified

| File | Lines Changed | Status | Description |
|------|---------------|--------|-------------|
| `path/to/file1.py` | +120, -5 | ✅ Complete | Brief description |
| `path/to/file2.py` | +80, -2 | ✅ Complete | Brief description |
| `path/to/file3.py` | +50, -0 | 🔄 In Progress | Brief description |

**Total**: X files, +XXX lines, -XX lines

---

## Code Changes

### File 1: path/to/file1.py

**Purpose**: Brief description

**Key Changes**:
```python
# Show important code snippets
def new_function():
    # Implementation
    pass
```

### File 2: path/to/file2.py

**Purpose**: Brief description

**Key Changes**:
```python
# Show important code snippets
class NewClass:
    pass
```

---

## Decisions Made

### Decision 1: Technical Decision
**Rationale**: Why this approach was chosen
**Alternatives Considered**: Other options and why they weren't chosen
**Impact**: What this affects

### Decision 2: Another Decision
**Rationale**: Explanation
**Impact**: What this changes

---

## Test Results

**Unit Tests**: XX/XX passing
**Integration Tests**: XX/XX passing
**E2E Tests**: Not run / XX/XX passing

**Test Command**:
```bash
pytest tests/specific/test_file.py -v
```

**Results**: All passing / X failing (list failures)

---

## Next Steps

### Immediate (Current Session if Continuing)
1. Complete sub-task 3: Specific next action
2. Sub-task 3 remaining work: Detailed steps
3. Test sub-task 3: Testing requirements

### After Sub-task 3 (Next Session if Compacting)
4. Sub-task 4: Description and approach
5. Sub-task 5: Description and approach
6. Final testing and documentation

---

## Recovery Instructions

### To Resume Work:

1. **Pull latest code**:
   ```bash
   git pull origin master
   git log -3  # Review recent commits
   ```

2. **Review this checkpoint**:
   - Read "Current Task Status" section
   - Review "Files Modified" to see what's changed
   - Check "Code Changes" for context on implementation

3. **Check current state**:
   ```bash
   # Review modified files
   git status

   # Run tests to verify state
   pytest tests/specific/ -v
   ```

4. **Continue work**:
   - Focus on sub-task 3 completion: [Specific guidance]
   - Next: [Clear next action]

---

## Quick Resume Prompt

**Copy-paste this to resume**:

```
Continue Phase X Task Y: Task Name

Current status: Sub-task 3 is XX% complete
Completed: Sub-tasks 1, 2
Remaining: Complete sub-task 3, then sub-tasks 4, 5

Last work: [Brief description of last activity]
Next immediate step: [Clear next action]

Files in progress:
- path/to/file3.py (needs: [specific work])

Checkpoint document: docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md

Please:
1. Review checkpoint document
2. Continue sub-task 3: [Specific guidance]
3. Then proceed to sub-tasks 4, 5
```

---

## Context for Next Instance

**Phase Progress**: XX/XX tasks complete
**Current Task Dependencies**: List any dependencies
**Known Issues**: List any issues encountered
**Technical Notes**: Any important technical context

---

*Checkpoint created*: YYYY-MM-DD HH:MM
*Next update*: After sub-task 3 completion or next compaction
```

---

## Quick Recovery Prompts

### After Compaction - Resume Work

**Prompt Template**:
```
I'm continuing work on Phase X Task Y after context compaction.

Last checkpoint: docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md

Quick summary:
- Completed: [List completed sub-tasks]
- In progress: [Current sub-task with status]
- Next: [Clear next action]

Please review the checkpoint document and continue from where we left off.

Focus on: [Specific guidance for what to do next]
```

### Starting New Task After Compaction

**Prompt Template**:
```
Starting Phase X Task Y: Task Name

Previous work (Phase X Task Y-1) is complete and committed.

Task Y objectives:
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

Plan:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Please begin with step 1: [Specific guidance]
```

### Mid-Task Resume

**Prompt Template**:
```
Resuming Phase X Task Y: Task Name (Sub-task Z)

Checkpoint: docs/PHASE_X_TASK_Y_CHECKPOINT_YYYY-MM-DD.md

Progress:
✅ Sub-tasks 1, 2
🔄 Sub-task 3: Currently [status]
⏳ Sub-tasks 4, 5: Pending

Current focus: Sub-task 3 - [Description]
Last action: [What was being done]
Next action: [Clear next step]

Files modified:
- file1.py - Complete
- file2.py - In progress (needs: [specific work])

Please continue with sub-task 3, specifically: [Detailed guidance]
```

---

## Best Practices

### DO:
✅ Create checkpoint before compaction (always)
✅ Commit all changes to git (always)
✅ Push to GitHub before compaction (always)
✅ Provide clear resume prompt
✅ Document decisions made
✅ Include code snippets in checkpoint
✅ List all modified files
✅ Specify exact next steps
✅ Run tests before checkpointing

### DON'T:
❌ Compact without checkpoint document
❌ Compact without committing changes
❌ Compact without pushing to GitHub
❌ Leave vague "continue working" instructions
❌ Forget to document technical decisions
❌ Skip test results in checkpoint
❌ Omit file modification details
❌ Leave unclear resume instructions

---

## Troubleshooting

### "I compacted but lost context"
- **Solution**: Read the checkpoint document you created
- **Location**: `docs/PHASE_X_*_CHECKPOINT_*.md`
- **Contains**: All the context needed to resume

### "I don't know what to do next"
- **Solution**: Check "Quick Resume Prompt" in checkpoint
- **Also check**: "Next Steps" and "Recovery Instructions" sections

### "Files were modified but I don't know what changed"
- **Solution**: Check "Code Changes" section in checkpoint
- **Also**: Run `git log` and `git diff` to see recent changes

### "Tests are failing after compaction"
- **Solution**: Check "Test Results" section in checkpoint
- **If tests were passing**: Review recent commits for what changed
- **If tests were failing**: Checkpoint should document known failures

---

## Example Workflow

### Scenario: Mid-Task Compaction

```
1. You're working on Task 32 (Health Monitoring)
2. You've completed sub-tasks 1-2
3. You're 50% through sub-task 3
4. Context usage hits 130K tokens (65%)

Action:
1. Create checkpoint: docs/PHASE_10_TASK_32_CHECKPOINT_2024-11-13.md
2. Commit: "Task 32 checkpoint: Health monitoring 50% complete"
3. Push to GitHub
4. Provide user with resume prompt
5. User runs /compact
6. New instance starts with resume prompt
7. New instance reads checkpoint
8. New instance continues sub-task 3
```

---

*This guide consolidates*:
- COMPACTION_DECISION_TREE.md
- MID_PHASE_COMPACTION_GUIDE.md
- MID_PHASE_COMPACTION_PROCESS.md
- MID_PHASE_QUICK_PROMPT.md
- PRE_COMPACTION_CHECKLIST.md

*Last updated*: 2024-11-13
*Version*: 2.0 (Consolidated)
