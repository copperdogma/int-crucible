# File Update Guide

**Purpose**: Clarify which files get updated/rewritten vs. which stay static across phases

---

## 📌 Quick Summary

### Files That NEVER Change (Static)
✅ **Use as-is for all phases, no updates needed**

| File | Purpose | Action Needed |
|------|---------|---------------|
| `QUICKSTART_AFTER_COMPACTION.md` | Recovery guide | ❌ None - always the same |
| `PHASE_COMPLETION_TEMPLATE.md` | Template for completion reports | ❌ None - copy to create new reports |
| `PHASE_IMPLEMENTATION_PROMPT.md` | Prompt templates | ❌ None - copy/paste with phase number |
| `PRE_COMPACTION_CHECKLIST.md` | Verification checklist | ❌ None - check relevant sections |

### Files That Get Updated Each Phase
📝 **Update these as you progress**

| File | What to Update | When |
|------|----------------|------|
| `IMPLEMENTATION_PLAN.md` | Mark checkboxes [x], update dashboard | During work, at phase completion |
| `docs/PHASE_[N]_COMPLETION.md` | **NEW FILE** each phase | Create at end of each phase |

---

## 🔄 Detailed Breakdown

### QUICKSTART_AFTER_COMPACTION.md
**Status**: ✅ **Static - Never Update**

**Why**:
- Generic recovery process that works for all phases
- Points to "latest PHASE_[N]_COMPLETION.md" dynamically
- "Quick Reference by Phase" section describes all phases upfront

**When to update**:
- Only if there's a fundamental change to the recovery process itself
- Extremely rare (maybe never)

**What NOT to do**:
- ❌ Don't add phase-specific information here
- ❌ Don't update for each phase
- ❌ Don't document what you built in a phase here

---

### PHASE_COMPLETION_TEMPLATE.md
**Status**: ✅ **Static - Template Only**

**Why**:
- Master template that defines structure
- Copy this to create new completion reports
- Template itself doesn't change

**When to update**:
- Only if you want to change the template structure for ALL future phases
- Add/remove sections that should be in every completion report

**What to do each phase**:
- ✅ Copy to `docs/PHASE_[N]_COMPLETION.md`
- ✅ Fill in the copied version
- ❌ Don't modify the template itself

---

### PHASE_IMPLEMENTATION_PROMPT.md
**Status**: ✅ **Static - Prompt Collection**

**Why**:
- Collection of reusable prompts
- Generic enough to work for any phase
- Phase-specific versions are just customizations of the base

**When to update**:
- Add new phase-specific prompts if you discover better patterns
- Improve the base prompt based on what works well

**What to do each phase**:
- ✅ Copy relevant prompt section
- ✅ Fill in phase number
- ✅ Paste to Claude
- ❌ Don't need to update the file itself

---

### PRE_COMPACTION_CHECKLIST.md
**Status**: ✅ **Static - Reusable Checklist**

**Why**:
- Generic verification process
- Has sections for all phases
- Check only the sections relevant to your current phase

**When to update**:
- Add new verification commands if you discover better checks
- Improve checklist items based on experience

**What to do each phase**:
- ✅ Read through and check relevant items
- ✅ Run phase-specific verification commands
- ❌ Don't create a new version for each phase

---

### IMPLEMENTATION_PLAN.md
**Status**: 📝 **Living Document - Update Frequently**

**Why**:
- Tracks overall progress
- Contains all 285 tasks across 10 phases
- Needs to reflect current state

**When to update**:
- ✅ Mark checkboxes as you complete tasks
- ✅ Update "Current Phase" indicator when phase changes
- ✅ Update "Overall Progress" percentage
- ✅ Update "Last Modified" date

**How often**:
- During work: Mark individual tasks complete
- At phase completion: Update dashboard section

**Example Updates**:
```markdown
# Before Phase 1
Current Phase: Phase 0 Complete ✅
Overall Progress: 6% (18/285 tasks)

# After Phase 1
Current Phase: Phase 1 Complete ✅
Overall Progress: 12% (35/285 tasks)
```

---

### docs/PHASE_[N]_COMPLETION.md
**Status**: 📝 **NEW FILE Each Phase**

**Why**:
- Documents what was accomplished in that specific phase
- Provides verification commands for that phase's deliverables
- Serves as permanent record of that phase's work

**When to create**:
- ✅ At the END of each phase
- Before marking phase complete
- Before compacting

**How to create**:
1. Copy `PHASE_COMPLETION_TEMPLATE.md`
2. Rename to `docs/PHASE_[N]_COMPLETION.md`
3. Fill in all sections based on what you built
4. Include specific verification commands

**Examples**:
- `docs/PHASE_0_COMPLETION.md` ✅ (exists)
- `docs/PHASE_1_COMPLETION.md` (create after Phase 1)
- `docs/PHASE_2_COMPLETION.md` (create after Phase 2)
- etc.

---

## 🎯 Decision Tree: Should I Update This File?

```
Question: Should I update [FILENAME] for this phase?

↓
Is it IMPLEMENTATION_PLAN.md?
├─ YES → ✅ Update it (mark checkboxes, update dashboard)
└─ NO → Continue

↓
Am I creating a NEW PHASE_[N]_COMPLETION.md?
├─ YES → ✅ Create new file from template
└─ NO → Continue

↓
Is it QUICKSTART, TEMPLATE, PROMPT, or CHECKLIST?
├─ YES → ❌ Don't update (use as-is)
└─ NO → ❓ Ask if unsure
```

---

## 📋 Workflow Summary

### At Start of Phase (After Compaction)
1. ✅ **Read**: `QUICKSTART_AFTER_COMPACTION.md` (no changes needed)
2. ✅ **Verify**: Previous `PHASE_[N-1]_COMPLETION.md` exists
3. ✅ **Review**: `IMPLEMENTATION_PLAN.md` for your phase
4. ✅ **Prompt**: Copy from `PHASE_IMPLEMENTATION_PROMPT.md`

### During Phase
1. ✅ **Update**: `IMPLEMENTATION_PLAN.md` - mark tasks complete
2. ✅ **Track**: TodoWrite list
3. ❌ **Don't touch**: QUICKSTART, templates, checklists

### At End of Phase
1. ✅ **Create**: `docs/PHASE_[N]_COMPLETION.md` (NEW FILE)
2. ✅ **Update**: `IMPLEMENTATION_PLAN.md` dashboard
3. ✅ **Verify**: Run `PRE_COMPACTION_CHECKLIST.md` (no updates)
4. ✅ **Clear**: TodoWrite

---

## 🚨 Common Mistakes

### ❌ WRONG: Updating QUICKSTART for each phase
```markdown
# DON'T DO THIS
# QUICKSTART_AFTER_COMPACTION.md

Phase 1 Recovery:
1. Check these Phase 1 files...
2. Run these Phase 1 commands...

Phase 2 Recovery:
1. Check these Phase 2 files...
```

**Why wrong**: QUICKSTART should stay generic. Phase-specific info goes in `PHASE_[N]_COMPLETION.md`

### ✅ RIGHT: Creating new completion report each phase
```bash
# DO THIS
cp PHASE_COMPLETION_TEMPLATE.md docs/PHASE_1_COMPLETION.md
# Edit PHASE_1_COMPLETION.md with Phase 1 specifics

cp PHASE_COMPLETION_TEMPLATE.md docs/PHASE_2_COMPLETION.md
# Edit PHASE_2_COMPLETION.md with Phase 2 specifics
```

**Why right**: Each phase gets its own completion report with phase-specific details

---

## 📊 File Lifecycle Example

```
Project Start:
├── QUICKSTART_AFTER_COMPACTION.md ✅ (created once, never changes)
├── PHASE_COMPLETION_TEMPLATE.md ✅ (created once, used as template)
├── PHASE_IMPLEMENTATION_PROMPT.md ✅ (created once, reused)
├── PRE_COMPACTION_CHECKLIST.md ✅ (created once, reused)
└── IMPLEMENTATION_PLAN.md ✅ (created once, updated continuously)

After Phase 0:
└── docs/PHASE_0_COMPLETION.md ✅ (NEW - phase 0 specific)

After Phase 1:
└── docs/PHASE_1_COMPLETION.md ✅ (NEW - phase 1 specific)

After Phase 2:
└── docs/PHASE_2_COMPLETION.md ✅ (NEW - phase 2 specific)

...and so on for all 10 phases
```

---

## 🎓 Key Principle

**Generic → Static | Specific → Create New**

- Generic files (recovery process, templates, checklists) → Keep static, reuse
- Specific files (completion reports) → Create new for each phase
- Progress tracking (IMPLEMENTATION_PLAN.md) → Update continuously

---

**Created**: 2025-11-06
**Purpose**: Eliminate confusion about file updates
**Last Updated**: 2025-11-06
