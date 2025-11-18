# Ready-to-Paste Prompts for Each Phase

**Purpose**: Copy-paste these prompts exactly as written. No editing needed!

---

## Phase 1: Core Infrastructure Setup

```
Please implement Phase 1 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_0_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 1 section (Project Structure, Claude API, Config, Agents, Logging, Database)

Planning:
4. Create comprehensive TodoWrite list for all Phase 1 tasks (6 subsections)
5. Present execution plan for approval including:
   - High-level approach
   - Key deliverables
   - Potential challenges
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build components
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_1_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist to ensure everything works
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 1 status as "✅ Complete"
    - Update "Overall Progress" to ~12% (35/285 tasks)
    - Update "Current Phase" to "Phase 1 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 2
```

---

## Phase 2: Knowledge & Literature System

```
Please implement Phase 2 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_1_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 2 section (Literature APIs, Literature Analyzer Agent, Vector DB, Knowledge Graph, Citations)

Planning:
4. Create comprehensive TodoWrite list for all Phase 2 tasks (5 subsections)
5. Present execution plan for approval including:
   - API integration approach (arXiv, Semantic Scholar, PubMed)
   - Vector database choice
   - Knowledge graph implementation strategy
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Reference @docs/domain-roadmaps/ for API details
8. Write tests as you build
9. Ask before deviating from plan

Phase Completion:
10. Create docs/PHASE_2_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
11. Run verification checklist (test literature search, embedding generation, knowledge graph queries)
12. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 2 status as "✅ Complete"
    - Update "Overall Progress" to ~18% (52/285 tasks)
    - Update "Current Phase" to "Phase 2 Complete ✅"
13. Clear TodoWrite list
14. Summarize accomplishments and preview Phase 3
```

---

## Phase 3: Hypothesis Generation

```
Please implement Phase 3 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_2_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 3 section (Hypothesis Generator Agent, Novelty Checking, Prioritization, Testability)

Planning:
4. Create comprehensive TodoWrite list for all Phase 3 tasks (4 subsections)
5. Present execution plan for approval including:
   - Claude prompt design for hypothesis generation
   - Novelty checking strategy using Phase 2 literature system
   - Prioritization framework
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_3_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist (test hypothesis generation, novelty checking, prioritization)
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 3 status as "✅ Complete"
    - Update "Overall Progress" to ~24% (68/285 tasks)
    - Update "Current Phase" to "Phase 3 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 4
```

---

## Phase 4: Experimental Design

```
Please implement Phase 4 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_3_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 4 section (Experiment Designer Agent, Protocol Templates, Resource Estimation, Validation)

Planning:
4. Create comprehensive TodoWrite list for all Phase 4 tasks (4 subsections)
5. Present execution plan for approval including:
   - Claude prompt design for experiment design
   - Template creation strategy
   - Scientific rigor validation approach
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_4_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist (test experiment generation, template instantiation, validation)
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 4 status as "✅ Complete"
    - Update "Overall Progress" to ~30% (85/285 tasks)
    - Update "Current Phase" to "Phase 4 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 5
```

---

## Phase 5: Experiment Execution Engine

```
Please implement Phase 5 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_4_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 5 section (Sandbox, Code Generation, Data Analysis, Statistics, Results)
4. **CRITICAL**: Review @docs/kosmos-figures-analysis.md for analysis patterns to implement
5. **CRITICAL**: Review @docs/integration-plan.md Phase 5-6 section for code templates

Planning:
6. Create comprehensive TodoWrite list for all Phase 5 tasks (5 subsections)
7. Present execution plan showing:
   - How you'll integrate kosmos-figures patterns
   - DataAnalyzer class implementation (t-test, correlation, log-log)
   - Sandbox architecture
   - Code generation approach
   - Any clarifying questions

Execution:
8. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
9. Extract and adapt code from kosmos-figures notebooks as per integration plan
10. Implement analysis library matching kosmos-figures patterns exactly
11. Write comprehensive tests against kosmos-figures expected outputs
12. Ask before deviating from plan

Phase Completion:
13. Create docs/PHASE_5_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
14. Run verification checklist (compare outputs with kosmos-figures notebooks)
15. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 5 status as "✅ Complete"
    - Update "Overall Progress" to ~47% (135/285 tasks)
    - Update "Current Phase" to "Phase 5 Complete ✅"
16. Clear TodoWrite list
17. Summarize accomplishments and preview Phase 6
```

---

## Phase 6: Analysis & Interpretation

```
Please implement Phase 6 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_5_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 6 section (Data Analyst Agent, Statistics, Visualization, Summarization)
4. **CRITICAL**: Review @docs/kosmos-figures-analysis.md visualization patterns section
5. **CRITICAL**: Review @docs/integration-plan.md for PublicationVisualizer templates

Planning:
6. Create comprehensive TodoWrite list for all Phase 6 tasks (4 subsections)
7. Present execution plan showing:
   - PublicationVisualizer implementation (volcano, heatmap, scatter, log-log)
   - Exact formatting match with kosmos-figures (Arial, colors, DPI)
   - Claude-powered result interpretation
   - Any clarifying questions

Execution:
8. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
9. Match kosmos-figures visualization formatting exactly
10. Test visualizations against kosmos-figures outputs (visual comparison)
11. Ask before deviating from plan

Phase Completion:
12. Create docs/PHASE_6_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
13. Run verification checklist (visual comparison with kosmos-figures)
14. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 6 status as "✅ Complete"
    - Update "Overall Progress" to ~59% (169/285 tasks)
    - Update "Current Phase" to "Phase 6 Complete ✅"
15. Clear TodoWrite list
16. Summarize accomplishments and preview Phase 7
```

---

## Phase 7: Iterative Learning Loop

```
Please implement Phase 7 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_6_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 7 section (Research Director, Hypothesis Refinement, Feedback Loops, Convergence)

Planning:
4. Create comprehensive TodoWrite list for all Phase 7 tasks (4 subsections)
5. Present execution plan for approval including:
   - Research Director orchestration strategy
   - Autonomous iteration approach (replacing manual r1, r2, r3...)
   - Feedback loop design
   - Convergence detection criteria
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_7_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist (test full autonomous research cycle)
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 7 status as "✅ Complete"
    - Update "Overall Progress" to ~71% (203/285 tasks)
    - Update "Current Phase" to "Phase 7 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 8
```

---

## Phase 8: Safety & Validation

```
Please implement Phase 8 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_7_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 8 section (Safety Guardrails, Result Verification, Human Oversight, Reproducibility, Testing)

Planning:
4. Create comprehensive TodoWrite list for all Phase 8 tasks (5 subsections)
5. Present execution plan for approval including:
   - Code safety validation strategy
   - Result verification approach
   - Testing framework (unit, integration, e2e)
   - Target test coverage (>80%)
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write comprehensive test suite
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_8_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
10. Run verification checklist (all tests pass, coverage >80%)
11. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 8 status as "✅ Complete"
    - Update "Overall Progress" to ~82% (235/285 tasks)
    - Update "Current Phase" to "Phase 8 Complete ✅"
12. Clear TodoWrite list
13. Summarize accomplishments and preview Phase 9
```

---

## Phase 9: Multi-Domain Support

```
Please implement Phase 9 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_8_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 9 section (Domain Tools, Knowledge Bases, Routing, Templates)
4. **CRITICAL**: Review @docs/domain-roadmaps/biology.md for biology implementation
5. **CRITICAL**: Review @docs/domain-roadmaps/neuroscience.md for neuroscience implementation
6. **CRITICAL**: Review @docs/domain-roadmaps/materials_physics.md for materials science implementation

Planning:
7. Create comprehensive TodoWrite list for all Phase 9 tasks (4 subsections)
8. Present execution plan showing:
   - Domain-by-domain implementation approach
   - API integrations (KEGG, FlyWire, Materials Project, etc.)
   - Domain-specific experiment templates
   - Any clarifying questions

Execution:
9. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
10. Implement biology domain (metabolomics, genomics) per roadmap
11. Implement neuroscience domain (connectomics, neurodegeneration) per roadmap
12. Implement materials science domain (parameter optimization) per roadmap
13. Ask before deviating from plan

Phase Completion:
14. Create docs/PHASE_9_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
15. Run verification checklist (test each domain's capabilities independently)
16. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 9 status as "✅ Complete"
    - Update "Overall Progress" to ~88% (252/285 tasks)
    - Update "Current Phase" to "Phase 9 Complete ✅"
17. Clear TodoWrite list
18. Summarize accomplishments and preview Phase 10
```

---

## Phase 10: Optimization & Production

```
Please implement Phase 10 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from @PHASE_9_COMPLETION.md to confirm previous phase complete
3. Review @IMPLEMENTATION_PLAN.md Phase 10 section (API Optimization, Caching, Documentation, UI, Deployment)

Planning:
4. Create comprehensive TodoWrite list for all Phase 10 tasks (5 subsections)
5. Present execution plan for approval including:
   - Claude API optimization strategy
   - Caching implementation
   - Documentation approach (Sphinx/MkDocs)
   - UI choice (CLI with rich / optional web interface)
   - Deployment strategy
   - Any clarifying questions

Execution:
6. Execute tasks sequentially, marking complete in BOTH TodoWrite and IMPLEMENTATION_PLAN.md
7. Write final documentation and examples
8. Create deployment guides
9. Ask before deviating from plan

Phase Completion:
10. Create docs/PHASE_10_COMPLETION.md from @PHASE_COMPLETION_TEMPLATE.md
11. Run verification checklist (full end-to-end research cycle works)
12. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase 10 status as "✅ Complete"
    - Update "Overall Progress" to 100% (285/285 tasks)
    - Update "Current Phase" to "🎉 PROJECT COMPLETE"
13. Clear TodoWrite list
14. Create final project summary

🎉 PROJECT COMPLETE! 🎉
```

---

## 🎯 How to Use These Prompts

### Simple 3-Step Process:

1. **After compacting**, scroll to the section for your next phase
2. **Copy the entire prompt** (including the triple backticks code block)
3. **Paste to Claude** - no editing needed!

### The model will automatically:
- ✅ Read QUICKSTART to recover context
- ✅ Verify previous phase completion
- ✅ Review relevant documentation
- ✅ Create TodoWrite list
- ✅ Present plan for your approval
- ✅ Execute the phase
- ✅ Create completion report
- ✅ Update IMPLEMENTATION_PLAN.md

---

## 🔄 Your Workflow (Super Simple)

```
End of Phase N:
You: "Check PRE_COMPACTION_CHECKLIST.md"
Model: ✅ All verified
You: /compact

Start of Phase N+1:
You: [paste Phase N+1 prompt from above]
Model: [does everything automatically]
```

---

**Created**: 2025-11-06
**Purpose**: Eliminate all manual editing - just copy & paste
**Last Updated**: 2025-11-06
