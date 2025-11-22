# Issue 003: Results don't match goals - minimal constitution solutions not generated

**Status**: Open  
**Priority**: Critical  
**Category**: Bug/Logic  
**Discovered**: 2025-01-21  
**Related Story**: (if applicable)

## Description

For the "Human-Centric Constitutional Framework" project, the goals clearly specified wanting a **minimal constitution**. However, the generated candidate solutions did not address this goal - they produced solutions that were not minimal.

This indicates a failure in the pipeline where either:
1. The ProblemSpec goals were not properly captured/understood
2. The WorldModeller did not emphasize the "minimal" requirement
3. The Designer agents did not respect the "minimal" constraint
4. The Evaluators did not penalize non-minimal solutions
5. The ranking system did not prioritize minimal solutions

## Steps to Reproduce

1. Create/open project: "Human-Centric Constitutional Framework"
2. Review the ProblemSpec goals - should include "minimal constitution" requirement
3. Review the generated candidates from runs
4. Observe that candidates are not minimal constitutions
5. Confirm this is a systematic issue, not just one bad candidate

## Expected Behavior

Candidates should respect the "minimal" requirement in the goals. Minimal constitution solutions should:
- Be prioritized in ranking
- Have higher scores for meeting the minimal requirement
- Be designed with minimalism as a core principle

## Actual Behavior

Candidates generated do not appear to be minimal constitutions. The system did not produce solutions that addressed the minimal requirement, despite it being in the goals.

## Environment

- **Project**: Human-Centric Constitutional Framework
- **Affected Phase**: Potentially any/all phases (ProblemSpec → WorldModeller → Designer → Evaluator → Ranker)
- **Impact**: High - core functionality not working as intended

## Investigation Notes

### Initial Observations

- Issue was flagged via "Flag Issue" feature, but may not have been saved properly (related to Issue #001)
- Need to trace the full pipeline to identify where the "minimal" requirement was lost
- This could be a data flow issue, prompt engineering issue, or evaluation logic issue

### Analysis Required

**Phase 1: ProblemSpec Verification**
- [ ] Check the stored ProblemSpec for this project
- [ ] Verify that "minimal" or "minimal constitution" is in the goals
- [ ] Check if goals were properly structured/parsed

**Phase 2: WorldModel Verification**
- [ ] Review the WorldModel generated for this project
- [ ] Check if "minimal" is captured in the model_data
- [ ] Verify if world model properly emphasizes the minimal requirement

**Phase 3: Candidate Generation Verification**
- [ ] Review candidate descriptions for this project's runs
- [ ] Check if Designer prompts included the minimal requirement
- [ ] Verify if Designer agents understood and respected minimalism

**Phase 4: Evaluation Verification**
- [ ] Review evaluation scores for candidates
- [ ] Check if evaluators penalized non-minimal solutions
- [ ] Verify if constraint/goal satisfaction included minimalism checks

**Phase 5: Ranking Verification**
- [ ] Review ranking explanations
- [ ] Check if minimal solutions were ranked higher
- [ ] Verify if I-score calculation properly weights goal satisfaction

### Key Questions

1. Was "minimal" in the goals from the start, or was it lost during ProblemSpec refinement?
2. How does the system ensure goals are translated into actionable constraints/guidance?
3. Are Designer agents explicitly instructed to respect all goals?
4. Do Evaluators check goal satisfaction beyond just constraint satisfaction?
5. Does the ranking system properly weight goal alignment?

### Data Needed

- Project ID for "Human-Centric Constitutional Framework"
- Run IDs that produced non-minimal candidates
- ProblemSpec JSON (goals, constraints)
- WorldModel JSON (model_data)
- Sample candidate descriptions
- Evaluation scores and breakdowns
- Ranking explanations

## Root Cause

[To be determined through investigation]

Possible causes:
1. **Goal translation failure** - "minimal" not converted to actionable constraint/guidance
2. **Prompt engineering gap** - Designer prompts don't emphasize goal requirements
3. **Evaluation blind spot** - Evaluators don't check goal satisfaction, only constraints
4. **Ranking weighting issue** - Goal satisfaction not properly weighted in I-score
5. **WorldModeller issue** - "minimal" requirement not captured in world model structure

## Proposed Solution

[To be determined based on root cause]

Potential fixes:
1. Enhance ProblemSpec → WorldModel translation to extract goal requirements
2. Update Designer prompts to explicitly mention all goal requirements
3. Add goal satisfaction scoring to Evaluators
4. Update ranking logic to weight goal satisfaction appropriately
5. Add validation checks to ensure goals are being addressed

## Resolution

[Pending investigation and fix]

---

**Last Updated**: 2025-01-21  
**Updated By**: AI Agent

