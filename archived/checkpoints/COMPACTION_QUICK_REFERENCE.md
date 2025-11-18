# Compaction Quick Reference

**Purpose**: One-page guide for both end-of-phase and mid-phase compaction

---

## 🎯 Which Process Do I Use?

```
Is the phase complete?
├─ YES → Use End-of-Phase Process
└─ NO → Use Mid-Phase Process
```

---

## ✅ End-of-Phase Compaction (Phase Complete)

### Before Compacting:
```
You: "Check PRE_COMPACTION_CHECKLIST.md"
Model: [Runs verification, confirms all ✅]
You: /compact
```

### After Compacting:
```
You: [Open READY_TO_PASTE_PROMPTS.md]
You: [Copy entire Phase N+1 prompt]
You: [Paste to Claude]
Model: [Recovers context, starts next phase]
```

**Documents**:
- Checklist: `PRE_COMPACTION_CHECKLIST.md`
- Prompts: `READY_TO_PASTE_PROMPTS.md`
- Created: `docs/PHASE_[N]_COMPLETION.md`

---

## 🔄 Mid-Phase Compaction (Phase Incomplete)

### Before Compacting:
```
You: "We need to compact mid-phase. Create checkpoint using
     MID_PHASE_COMPACTION_GUIDE.md as template.
     Save as docs/PHASE_[N]_CHECKPOINT_[YYYY-MM-DD].md"

Model: [Creates detailed checkpoint]

You: "Update IMPLEMENTATION_PLAN.md:
     - Mark completed tasks [x]
     - Note in-progress tasks
     - Add checkpoint reference"

Model: [Updates plan]

You: /compact
```

### After Compacting:
```
You: "Resume Phase [N] from checkpoint.

     Read:
     1. @QUICKSTART_AFTER_COMPACTION.md
     2. @docs/PHASE_[N]_CHECKPOINT_[YYYY-MM-DD].md
     3. @IMPLEMENTATION_PLAN.md Phase [N]

     Continue from 'Next Immediate Steps' in checkpoint."

Model: [Recovers context, resumes work]
```

**Documents**:
- Template: `MID_PHASE_COMPACTION_GUIDE.md`
- Process: `MID_PHASE_COMPACTION_PROCESS.md`
- Created: `docs/PHASE_[N]_CHECKPOINT_[DATE].md`

---

## 📊 Quick Comparison

| Aspect | End-of-Phase | Mid-Phase |
|--------|-------------|-----------|
| **When** | Phase 100% complete | Need to stop mid-phase |
| **Creates** | PHASE_[N]_COMPLETION.md | PHASE_[N]_CHECKPOINT_[DATE].md |
| **PLAN Status** | "✅ Complete" | "🔄 In Progress" |
| **Next Action** | Start next phase | Resume current phase |
| **Use** | PRE_COMPACTION_CHECKLIST | MID_PHASE_COMPACTION_PROCESS |
| **Recovery** | READY_TO_PASTE_PROMPTS | Custom resume prompt |

---

## 🔍 How to Tell After Compaction

```bash
# Check current status
head -30 IMPLEMENTATION_PLAN.md

# Look for:
"Complete ✅"        → End-of-phase compaction
"In Progress 🔄"    → Mid-phase compaction
"Checkpoint:"       → Mid-phase (checkpoint file listed)
```

---

## 📁 File Organization

```
End-of-Phase:
docs/
├── PHASE_0_COMPLETION.md ✅
├── PHASE_1_COMPLETION.md ✅
└── PHASE_2_COMPLETION.md ✅

Mid-Phase:
docs/
├── PHASE_0_COMPLETION.md ✅
├── PHASE_1_CHECKPOINT_2025-11-07.md 🔄
├── PHASE_1_CHECKPOINT_2025-11-08.md 🔄 (if multiple checkpoints)
└── PHASE_1_COMPLETION.md ✅ (when finally complete)
```

---

## ⚡ Emergency Quick Checkpoint

**If context is critical**:
```
You: "Emergency checkpoint! Capture:
     1. Current file: [name]
     2. What's done
     3. What's not done
     4. Next 3 steps
     Save as docs/PHASE_[N]_EMERGENCY_[TIME].md"

You: /compact
```

**After recovery**: Expand emergency checkpoint before continuing.

---

## 🎓 Best Practices

### Always:
- ✅ Create checkpoint/completion report BEFORE compacting
- ✅ Update IMPLEMENTATION_PLAN.md to match reality
- ✅ Commit to git (if using)
- ✅ Be specific about next steps

### Never:
- ❌ Compact without documentation
- ❌ Leave vague "mostly done" descriptions
- ❌ Forget to note open questions
- ❌ Skip updating IMPLEMENTATION_PLAN.md

---

## 📞 Quick Help

**Lost after compaction?**
1. Run: `head -30 IMPLEMENTATION_PLAN.md`
2. Look for "Complete" or "In Progress"
3. Read the relevant doc (completion or checkpoint)
4. Follow recovery steps

**Can't find checkpoint?**
```bash
ls -lt docs/PHASE_*_CHECKPOINT*.md
ls -lt docs/PHASE_*_COMPLETION.md
```

**Not sure what to do?**
- Read `QUICKSTART_AFTER_COMPACTION.md`
- It has a decision tree for both scenarios

---

**Created**: 2025-11-07
**Purpose**: One-page reference for all compaction scenarios
