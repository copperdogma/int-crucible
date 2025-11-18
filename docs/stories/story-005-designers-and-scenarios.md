# Story: Implement Designers and ScenarioGenerator

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Designer agents (MVP), ScenarioGenerator.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run Configuration & Execution Pipeline** – Designers, ScenarioGenerator, ScenarioSuite.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – candidate statuses and summaries.

## Acceptance Criteria
- Designer agents can generate multiple, diverse candidate solutions from the WorldModel.
- Each candidate includes at least:
  - Mechanism description.
  - Expected effects on actors/resources.
  - Rough constraint compliance estimates.
- The ScenarioGenerator can produce a minimal, structured scenario suite:
  - Scenarios that stress high-weight constraints and fragile assumptions.
  - Represented in a format that Evaluators can consume.
- The pipeline can run a “design + scenario generation” phase for a run:
  - Given a ProblemSpec + WorldModel, produce candidate list + scenarios.
- Candidate creation and scenario generation are visible in logs/DB for debugging.

## Tasks
- [ ] Design the candidate representation and ScenarioSuite structure (aligned with Story 002 schema).
- [ ] Implement Designer agents (on top of Kosmos agent framework) that:
  - [ ] Generate multiple candidate mechanisms from the WorldModel.
  - [ ] Provide rough constraint compliance estimates for each candidate.
- [ ] Implement ScenarioGenerator agent that:
  - [ ] Takes WorldModel and candidate set as input.
  - [ ] Produces a minimal ScenarioSuite focused on critical constraints and assumptions.
- [ ] Integrate Designers and ScenarioGenerator into the run pipeline orchestration.
- [ ] Add basic logging and provenance entries for candidate and scenario generation.
- [ ] Add tests or demo runs showing candidate and scenario generation for a sample problem.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- Diversity of candidates is more important than completeness; the MVP should surface clearly distinct approaches rather than many small variants.


