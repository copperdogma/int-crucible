# Quick Start After Context Compaction

**Purpose**: Rapidly recover context and resume work on Kosmos implementation

---

## 🚀 30-Second Recovery

```bash
# 1. Check current status
cat IMPLEMENTATION_PLAN.md | head -30

# 2. Determine if phase was complete or in-progress
# Look for "Complete ✅" or "In Progress 🔄" and "Checkpoint:" reference

# 3a. If phase was COMPLETE: Find latest completion report
ls -lt docs/PHASE_*_COMPLETION.md | head -1

# 3b. If phase was IN PROGRESS: Find latest checkpoint
ls -lt docs/PHASE_*_CHECKPOINT*.md | head -1

# 4. Read the report/checkpoint
cat docs/PHASE_[N]_COMPLETION.md  # or CHECKPOINT file

# 5a. If complete: Continue from next phase
# 5b. If in-progress: Resume from "Next Immediate Steps" in checkpoint
```

---

## 📋 Step-by-Step Recovery Protocol

### Step 0: Determine Compaction Type (10 sec)
```bash
# Check if phase was complete or in-progress
head -30 IMPLEMENTATION_PLAN.md | grep -E "Current Phase|Checkpoint"
```

**If you see "Complete ✅"**: Phase was finished, follow normal recovery
**If you see "In Progress 🔄" or "Checkpoint:"**: Mid-phase compaction, see special recovery below

### Step 1: Identify Current Phase (30 sec)
```bash
# Check project status dashboard
head -30 IMPLEMENTATION_PLAN.md
```

**Look for**:
- "Current Phase: Phase X Complete ✅" or "Phase X In Progress"
- "Overall Progress: X%"

### Step 2: Read Latest Completion Report (3 min)
```bash
# Find most recent completion report
ls -lt docs/PHASE_*_COMPLETION.md | head -1

# Read it
cat docs/PHASE_[N]_COMPLETION.md
```

**Key Sections to Read**:
- Executive Summary (understand what was done)
- Deliverables (know what exists)
- Verification Checklist (confirm completion)
- Next Steps (know what to do next)

### Step 3: Verify Completion (2 min)
Run the verification commands from the completion report:

```bash
# Example from Phase 0:
ls docs/kosmos-figures-analysis.md
ls docs/integration-plan.md
ls docs/domain-roadmaps/*.md
ls -d kosmos-figures/
find kosmos-figures -type f | wc -l
grep -c "\[x\]" IMPLEMENTATION_PLAN.md
```

All should exist/pass.

### Step 4: Review Key Documents (5 min)

**Always read**:
1. Latest `PHASE_[N]_COMPLETION.md`
2. `IMPLEMENTATION_PLAN.md` - sections for current phase

**Phase-specific**:
- **Phase 0**: `docs/kosmos-figures-analysis.md`, `docs/integration-plan.md`
- **Phase 1**: `kosmos/core/` directory structure
- **Phase 2**: `kosmos/literature/` and knowledge system docs
- **Phase 5**: `kosmos/execution/` and analysis code
- **Phase 6**: `kosmos/analysis/` and visualization code
- **Phase 9**: `docs/domain-roadmaps/*.md`

### Step 5: Continue Work

**If Phase Was Complete**:
1. Open `IMPLEMENTATION_PLAN.md`
2. Find next phase section
3. Use prompt from `READY_TO_PASTE_PROMPTS.md` for next phase
4. Begin next phase

**If Phase Was In Progress** (see checkpoint):
1. Read checkpoint document's "Next Immediate Steps"
2. Create TodoWrite list with remaining tasks
3. Resume from checkpoint's specified location
4. Continue marking tasks complete as you finish

---

## 🔄 Special: Mid-Phase Recovery

**If you compacted mid-phase** (checkpoint exists):

### Quick Recovery (3 minutes):
```bash
# 1. Find latest checkpoint
ls -lt docs/PHASE_*_CHECKPOINT*.md | head -1

# 2. Read it
cat docs/PHASE_[N]_CHECKPOINT_[DATE].md

# 3. Look for these sections:
#    - "Current Task" - what was being worked on
#    - "Next Immediate Steps" - where to resume
#    - "Open Questions" - unresolved issues
#    - "Files Modified" - what changed
```

### Resume Prompt:
```
I need to resume Phase [N] which was interrupted mid-phase.

Recovery Steps:
1. Read @QUICKSTART_AFTER_COMPACTION.md for general context
2. Read @docs/PHASE_[N]_CHECKPOINT_[YYYY-MM-DD].md for exact state
3. Review @IMPLEMENTATION_PLAN.md Phase [N] section

Current Status: [copy from checkpoint]
Resume from: [copy "Next Immediate Steps"]

Please confirm you've recovered context and continue from checkpoint.
```

**Full Guide**: See `MID_PHASE_COMPACTION_PROCESS.md` for complete instructions

---

## 🎯 Quick Reference by Phase

### Phase 0: Repository Analysis (COMPLETE ✅)
**Deliverables**: `docs/kosmos-figures-analysis.md`, `docs/integration-plan.md`, `docs/domain-roadmaps/`
**What it provides**: Understanding of kosmos-figures code, integration strategy
**Read if**: You need to understand kosmos-figures patterns or integration approach

### Phase 1: Core Infrastructure
**Deliverables**: `kosmos/` package, `pyproject.toml`, `.env.example`, agent framework
**What it provides**: Basic project structure, Claude API integration, agent orchestration
**Read if**: You're implementing core systems or setting up the project

### Phase 2: Knowledge & Literature
**Deliverables**: `kosmos/literature/`, `kosmos/knowledge/`, literature APIs
**What it provides**: Paper search, summarization, knowledge graph
**Read if**: You're working on literature integration or novelty checking

### Phase 3: Hypothesis Generation
**Deliverables**: `kosmos/agents/hypothesis_generator.py`, `kosmos/models/hypothesis.py`
**What it provides**: Claude-powered hypothesis generation
**Read if**: You're working on research question → hypothesis pipeline

### Phase 4: Experimental Design
**Deliverables**: `kosmos/agents/experiment_designer.py`, experiment templates
**What it provides**: Hypothesis → experiment protocol conversion
**Read if**: You're implementing experiment design or templates

### Phase 5: Experiment Execution
**Deliverables**: `kosmos/execution/`, statistical analysis, code generation
**What it provides**: Sandboxed execution, data analysis, statistical tests
**Read if**: You're implementing analysis code from kosmos-figures patterns

### Phase 6: Analysis & Interpretation
**Deliverables**: `kosmos/analysis/`, `kosmos/agents/data_analyst.py`
**What it provides**: Result interpretation, visualization generation
**Read if**: You're working on plots, statistical interpretation, or insights

### Phase 7: Iterative Learning
**Deliverables**: `kosmos/core/feedback.py`, `kosmos/agents/research_director.py`
**What it provides**: Autonomous iteration, hypothesis refinement
**Read if**: You're implementing the autonomous research loop

### Phase 8: Safety & Validation
**Deliverables**: `kosmos/safety/`, testing suite
**What it provides**: Code safety, result verification, reproducibility
**Read if**: You're implementing safety checks or testing

### Phase 9: Multi-Domain Support
**Deliverables**: `kosmos/domains/biology/`, `kosmos/domains/neuroscience/`, etc.
**What it provides**: Domain-specific tools, APIs, templates
**Read if**: You're adding domain-specific capabilities

### Phase 10: Optimization & Production
**Deliverables**: Web interface, optimization, deployment
**What it provides**: Production-ready system
**Read if**: You're finalizing the system for deployment

---

## 🔍 Finding Specific Information

### "What statistical methods are available?"
→ `docs/kosmos-figures-analysis.md` - "Common Analysis Patterns" section

### "How do I integrate kosmos-figures code?"
→ `docs/integration-plan.md` - "Phase-by-Phase Integration Mapping"

### "What APIs should I use for biology?"
→ `docs/domain-roadmaps/biology.md` - "Key Tools & APIs" sections

### "What should I implement next?"
→ `IMPLEMENTATION_PLAN.md` - Find current phase, look for `[ ]` unchecked tasks

### "How does the agent system work?"
→ Current phase completion report - "Implementation Details" section

### "What templates exist?"
→ `docs/integration-plan.md` - "Experiment Templates" section
→ `docs/domain-roadmaps/` - Each has "Experiment Templates" section

---

## ⚠️ Common Mistakes to Avoid

1. **Don't start without reading completion reports**
   - You'll miss critical context and decisions made

2. **Don't skip verification**
   - Ensure previous work is complete before continuing

3. **Don't forget to update IMPLEMENTATION_PLAN.md**
   - Mark checkboxes as you complete tasks

4. **Don't forget TodoWrite**
   - Create todo list for current phase work

5. **Don't re-implement existing code**
   - Check completion reports to see what's already done

---

## 📊 Project Status Commands

```bash
# Overall progress
grep "Overall Progress" IMPLEMENTATION_PLAN.md

# Current phase
grep "Current Phase" IMPLEMENTATION_PLAN.md

# Completed tasks count
grep -c "\[x\]" IMPLEMENTATION_PLAN.md

# Total tasks
grep -c "\[ \]" IMPLEMENTATION_PLAN.md
grep -c "\[x\]" IMPLEMENTATION_PLAN.md
# Add both numbers for total

# List all phases and status
grep "^## Phase" IMPLEMENTATION_PLAN.md

# Find in-progress phase
grep "in_progress" IMPLEMENTATION_PLAN.md

# Check git status (if initialized)
git status
git log --oneline -10
```

---

## 🎓 Understanding the Project

### Core Concept
Build a fully autonomous AI scientist by combining:
- **kosmos-figures**: Proven statistical analysis and visualization patterns
- **Claude Sonnet 4.5**: Autonomous hypothesis generation, experimental design, interpretation

### Architecture
```
Research Question
    ↓
Claude: Generate Hypotheses (Phase 3)
    ↓
Claude: Design Experiments (Phase 4)
    ↓
kosmos-figures patterns: Execute Analysis (Phase 5)
    ↓
Claude: Interpret Results (Phase 6)
    ↓
Claude: Refine & Iterate (Phase 7)
    ↓
Scientific Discovery
```

### Key Insight
We're not rewriting kosmos-figures code. We're wrapping their proven analysis methods with Claude-powered intelligence to create autonomous iteration.

---

## 📞 Emergency Recovery

### "I'm completely lost"
1. Start at top of this document
2. Run 30-second recovery commands
3. Read latest `PHASE_[N]_COMPLETION.md`
4. Read `IMPLEMENTATION_PLAN.md` dashboard (top 30 lines)
5. Ask user for clarification if still unclear

### "Files are missing"
1. Check if in correct directory: `pwd` (should be `/mnt/c/python/Kosmos`)
2. Run verification commands from completion report
3. If Phase 0 deliverables missing, Phase 0 needs to be redone
4. If later phase deliverables missing, that phase needs to be redone

### "Tests are failing"
1. Check which phase's tests: `pytest tests/ -v`
2. Read that phase's completion report for known issues
3. Check "Known Issues & Technical Debt" section
4. May need to debug or re-implement failing component

---

## ✅ Daily Workflow

1. **Morning**: Read latest completion report, check IMPLEMENTATION_PLAN.md
2. **Start work**: Create TodoWrite list for tasks
3. **During work**: Mark todos as in_progress → completed
4. **End of session**: Update IMPLEMENTATION_PLAN.md checkboxes
5. **End of phase**: Create `PHASE_[N]_COMPLETION.md` using template

---

## 📝 Creating Phase Completion Reports

When finishing a phase:

1. Copy `docs/PHASE_COMPLETION_TEMPLATE.md`
2. Rename to `docs/PHASE_[N]_COMPLETION.md`
3. Fill in all sections based on work done
4. Run verification checklist to ensure everything works
5. Update `IMPLEMENTATION_PLAN.md`:
   - Mark all phase checkboxes as `[x]`
   - Update "Current Phase"
   - Update "Overall Progress" percentage
6. Commit completion report to git (if using git)

---

**Last Updated**: 2025-11-06 (Phase 0 completion)
**Document Purpose**: Rapid context recovery after compaction
**Estimated Recovery Time**: 5-10 minutes
