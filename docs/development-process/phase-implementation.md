# Phase Implementation Prompt Template

Use this prompt to implement each phase of the Kosmos project.

---

## Standard Prompt for Phase [N]

```
Please implement Phase [N] from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Run verification commands from the latest @PHASE_[N-1]_COMPLETION.md to confirm previous phase is complete
3. Review @IMPLEMENTATION_PLAN.md Phase [N] section
4. If Phase 0 is complete, review relevant domain roadmaps or integration plans as needed

Planning:
5. Create a comprehensive todo list using TodoWrite for all Phase [N] tasks
6. Present your execution plan for my approval, including:
   - High-level approach
   - Key deliverables
   - Potential challenges
   - Estimated time/complexity
   - Any clarifying questions

Execution:
7. Execute tasks sequentially, marking them complete in both:
   - TodoWrite (pending → in_progress → completed)
   - IMPLEMENTATION_PLAN.md ([ ] → [x])
8. Commit logical units of work if using git
9. Write tests as you go (don't batch at end)
10. If you encounter issues or need to deviate from the plan, ask before proceeding

Phase Completion:
11. When all tasks are complete, create phase completion report:
    - Copy @PHASE_COMPLETION_TEMPLATE.md to docs/PHASE_[N]_COMPLETION.md
    - Fill in all sections based on work completed
    - Include verification checklist with commands
12. Run the verification checklist to ensure everything works
13. Update IMPLEMENTATION_PLAN.md:
    - Mark Phase [N] status as "✅ Complete"
    - Update "Overall Progress" percentage
    - Update "Current Phase" indicator
14. Clear TodoWrite list
15. Summarize what was accomplished and what's next

Additional Guidelines:
- Reference kosmos-figures patterns from @docs/kosmos-figures-analysis.md when implementing analysis code
- Follow integration strategy from @docs/integration-plan.md for Phases 5-6
- Consult domain roadmaps from @docs/domain-roadmaps/ for domain-specific implementations
- Ask for clarification before making major architectural decisions
- Prioritize working code over perfect code (can refactor later)
- Test incrementally, not just at the end
```

---

## Quick Copy Prompts by Phase

### Phase 1: Core Infrastructure Setup
```
Please implement Phase 1 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Verify Phase 0 completion using @PHASE_0_COMPLETION.md verification checklist
3. Review @IMPLEMENTATION_PLAN.md Phase 1 section (Project Structure, Claude API, Config, Agents, Logging, Database)

Planning:
4. Create comprehensive TodoWrite list for all Phase 1 tasks (6 subsections)
5. Present execution plan for approval

Execution:
6. Execute sequentially, marking complete in TodoWrite and IMPLEMENTATION_PLAN.md
7. Write tests as you build
8. Ask before deviating from plan

Phase Completion:
9. Create docs/PHASE_1_COMPLETION.md from template
10. Run verification checklist
11. Update IMPLEMENTATION_PLAN.md progress (Phase 1 → ✅ Complete, overall → ~12%)
12. Clear todos
13. Summarize and preview Phase 2
```

### Phase 2: Knowledge & Literature System
```
Please implement Phase 2 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Verify Phase 1 completion using @PHASE_1_COMPLETION.md verification checklist
3. Review @IMPLEMENTATION_PLAN.md Phase 2 section (Literature APIs, Literature Analyzer Agent, Vector DB, Knowledge Graph, Citations)

Planning:
4. Create comprehensive TodoWrite list for all Phase 2 tasks (5 subsections)
5. Present execution plan for approval

Execution:
6. Execute sequentially, marking complete in TodoWrite and IMPLEMENTATION_PLAN.md
7. Reference @docs/domain-roadmaps/ for API information (arXiv, Semantic Scholar, PubMed)
8. Write tests as you build
9. Ask before deviating from plan

Phase Completion:
10. Create docs/PHASE_2_COMPLETION.md from template
11. Run verification checklist (test literature search, embedding generation, knowledge graph)
12. Update IMPLEMENTATION_PLAN.md progress (Phase 2 → ✅ Complete, overall → ~18%)
13. Clear todos
14. Summarize and preview Phase 3
```

### Phase 5: Experiment Execution Engine
```
Please implement Phase 5 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Verify Phase 4 completion using @PHASE_4_COMPLETION.md verification checklist
3. Review @IMPLEMENTATION_PLAN.md Phase 5 section (Sandbox, Code Generation, Data Analysis, Statistics, Results)
4. **CRITICAL**: Review @docs/kosmos-figures-analysis.md for analysis patterns to implement
5. **CRITICAL**: Review @docs/integration-plan.md Phase 5-6 section for code templates

Planning:
6. Create comprehensive TodoWrite list for all Phase 5 tasks (5 subsections)
7. Present execution plan showing how you'll integrate kosmos-figures patterns
8. Get approval before proceeding

Execution:
9. Execute sequentially, marking complete in TodoWrite and IMPLEMENTATION_PLAN.md
10. Extract and adapt code from kosmos-figures notebooks as per integration plan
11. Implement analysis library (DataAnalyzer class with t-test, correlation, log-log)
12. Write comprehensive tests against kosmos-figures expected outputs
13. Ask before deviating from plan

Phase Completion:
14. Create docs/PHASE_5_COMPLETION.md from template
15. Run verification checklist (compare outputs with kosmos-figures notebooks)
16. Update IMPLEMENTATION_PLAN.md progress (Phase 5 → ✅ Complete, overall → ~47%)
17. Clear todos
18. Summarize and preview Phase 6
```

### Phase 6: Analysis & Interpretation
```
Please implement Phase 6 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Verify Phase 5 completion using @PHASE_5_COMPLETION.md verification checklist
3. Review @IMPLEMENTATION_PLAN.md Phase 6 section (Data Analyst Agent, Statistics, Visualization, Summarization)
4. **CRITICAL**: Review @docs/kosmos-figures-analysis.md visualization patterns
5. **CRITICAL**: Review @docs/integration-plan.md for PublicationVisualizer templates

Planning:
6. Create comprehensive TodoWrite list for all Phase 6 tasks (4 subsections)
7. Present execution plan showing visualization templates to implement
8. Get approval before proceeding

Execution:
9. Execute sequentially, marking complete in TodoWrite and IMPLEMENTATION_PLAN.md
10. Implement PublicationVisualizer (volcano plot, heatmap, scatter+regression, log-log)
11. Match kosmos-figures formatting exactly (Arial font, colors, DPI)
12. Test visualizations against kosmos-figures outputs
13. Ask before deviating from plan

Phase Completion:
14. Create docs/PHASE_6_COMPLETION.md from template
15. Run verification checklist (visual comparison with kosmos-figures)
16. Update IMPLEMENTATION_PLAN.md progress (Phase 6 → ✅ Complete, overall → ~59%)
17. Clear todos
18. Summarize and preview Phase 7
```

### Phase 9: Multi-Domain Support
```
Please implement Phase 9 from @IMPLEMENTATION_PLAN.md.

Pre-Implementation:
1. Read @QUICKSTART_AFTER_COMPACTION.md to recover context
2. Verify Phase 8 completion using @PHASE_8_COMPLETION.md verification checklist
3. Review @IMPLEMENTATION_PLAN.md Phase 9 section (Domain Tools, Knowledge Bases, Routing, Templates)
4. **CRITICAL**: Review @docs/domain-roadmaps/biology.md for biology implementation
5. **CRITICAL**: Review @docs/domain-roadmaps/neuroscience.md for neuroscience implementation
6. **CRITICAL**: Review @docs/domain-roadmaps/materials_physics.md for materials science implementation

Planning:
7. Create comprehensive TodoWrite list for all Phase 9 tasks (4 subsections)
8. Present execution plan showing domain-by-domain implementation
9. Get approval before proceeding

Execution:
10. Execute sequentially, marking complete in TodoWrite and IMPLEMENTATION_PLAN.md
11. Implement domain-specific tools following roadmap guidance
12. Integrate APIs (KEGG, FlyWire, Materials Project, etc.)
13. Create experiment templates per domain
14. Ask before deviating from plan

Phase Completion:
15. Create docs/PHASE_9_COMPLETION.md from template
16. Run verification checklist (test each domain's capabilities)
17. Update IMPLEMENTATION_PLAN.md progress (Phase 9 → ✅ Complete, overall → ~88%)
18. Clear todos
19. Summarize and preview Phase 10
```

---

## Verification Command Template

Include these in each phase completion report:

```bash
# Files exist
ls [critical/files/for/this/phase]

# Tests pass
pytest tests/phase_[N]/ -v

# Functionality works
python -c "from kosmos.[module] import [Class]; [Class]().test_method()"

# Integration points verified
python scripts/verify_phase_[N].py

# Documentation updated
grep "Phase [N]" IMPLEMENTATION_PLAN.md
grep "\[x\]" IMPLEMENTATION_PLAN.md | wc -l
```

---

## Common Pitfalls to Avoid

1. **Skipping context recovery**: Always read QUICKSTART first
2. **Not verifying previous phase**: Run verification before starting
3. **Forgetting to update todos**: Mark in_progress when starting tasks
4. **Batching checkbox updates**: Mark complete immediately after finishing each task
5. **Skipping tests**: Write tests as you go, not at the end
6. **Not asking when stuck**: Ask for help rather than guessing
7. **Forgetting completion report**: Create it at the end, don't skip it
8. **Not running verification**: Always verify everything works before marking complete

---

## Success Criteria for Phase Completion

A phase is only complete when:
- [x] All checkboxes in IMPLEMENTATION_PLAN.md marked for this phase
- [x] All tests written and passing
- [x] PHASE_[N]_COMPLETION.md created with all sections filled
- [x] Verification checklist run and all items pass
- [x] Project Status Dashboard updated (current phase, overall progress)
- [x] TodoWrite list cleared
- [x] Summary provided to user

---

**Last Updated**: 2025-11-06 (After Phase 0 completion)
**Template Version**: 1.0
