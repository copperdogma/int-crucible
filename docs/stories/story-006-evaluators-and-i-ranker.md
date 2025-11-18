# Story: Implement Evaluators and I-Ranker

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – Evaluator agents, I-Ranker, Provenance tracker.
  - **MVP Criteria** – structured P, R, constraint satisfaction, and I = P/R scores.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run Configuration & Execution Pipeline** – Evaluations, scores, ranking.
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – ranked list, candidate detail view.

## Acceptance Criteria
- Evaluator agents can:
  - Consume a candidate and a set of scenarios.
  - Produce consistent scores for P (prediction quality), R (resource/complexity cost), and constraint satisfaction per scenario.
- The I-Ranker can:
  - Aggregate evaluator outputs into final scores per candidate.
  - Compute I = P/R for each candidate.
  - Flag violations of “hard” (weight 100) constraints.
- Evaluation remains language-level only (no real code execution) for the MVP.
- The pipeline can run a full “evaluate + rank” phase:
  - Input: candidate set + scenarios.
  - Output: ranked list with explanations and flags.
- The system stores evaluation results and rankings in the DB and exposes them via the backend for UI consumption.

## Tasks
- [ ] Design the Evaluation record structure (per-candidate, per-scenario) and integrate it into the schema (Story 002).
- [ ] Implement Evaluator agents that:
  - [ ] Accept candidate + scenario descriptions.
  - [ ] Produce structured P, R, and constraint satisfaction scores, plus a brief explanation.
- [ ] Implement I-Ranker logic that:
  - [ ] Aggregates evaluations.
  - [ ] Computes I = P/R and highlights hard-constraint violations.
- [ ] Integrate Evaluators and I-Ranker into the run pipeline orchestration.
- [ ] Expose ranked results and evaluation summaries via backend endpoints.
- [ ] Add tests or demo runs showing evaluation and ranking for sample candidates and scenarios.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The MVP can use relatively simple scoring heuristics as long as they are structured and explainable; more advanced scoring and uncertainty modelling can be added later.


