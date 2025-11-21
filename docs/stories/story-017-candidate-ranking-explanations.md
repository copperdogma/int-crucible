# Story 017: Candidate ranking explanations in UI

**Status**: To Do  

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features – Evaluator agents, I-Ranker** – structured P, R, constraint satisfaction, and I = P/R scores.
  - **MVP Criteria** – “A brief, understandable explanation of why top candidates are ranked higher.”
- See `docs/design.md`:
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – ranked list and candidate detail view.

## Alignment with Design
- The current pipeline already computes:
  - Per-scenario evaluations (P, R, constraint satisfaction).
  - Aggregated P, R, and I = P/R per candidate.
- This story focuses on **exposing the “why” behind the ranking** in the UI and API:
  - Concise explanations for why a candidate is ranked where it is.
  - Clear linkage to constraints and scenarios that most influence the ranking.
  - Lightweight enough for streaming chat + Results view without overwhelming the user.

## Problem Statement
Today:

1. The backend computes structured scores (P, R, I) and constraint satisfaction per candidate.
2. The Results view shows P, R, I and any constraint flags at a glance.
3. However, the user does **not** get a compact, human-readable story of:
   - Why candidate #1 outranks candidate #2.
   - Which constraints or scenarios were decisive.
   - How hard-constraint violations factored into rejection.

This makes it harder to:
- Build **trust** in the ranking.
- Quickly understand tradeoffs between top candidates.
- Debug surprising rankings without drilling into raw JSON or logs.

We want:
- A **short, readable explanation** for each top candidate (especially #1–#3).
- A one-line summary in the list plus a richer explanation in the detail view.
- Explanations that are derived from existing structured data, not ad-hoc prose.

## Acceptance Criteria
- **Backend: ranking rationales**:
  - The ranking phase (`RankerService.rank_candidates`) computes, for each candidate:
    - A short `ranking_explanation` string (1–3 sentences) summarizing:
      - Relative P and R vs other candidates.
      - Any hard-constraint violations or key constraint tradeoffs.
      - Notable scenario outcomes (e.g., “performs best under stress tests, weaker on edge cases”).
    - An optional structured `ranking_factors` object with:
      - `top_positive_factors`: list of short labels (e.g., “high P under core scenarios”, “low implementation cost”).
      - `top_negative_factors`: list of short labels (e.g., “violates hard latency constraint”, “high complexity”).
  - These explanations and factors are persisted in `Candidate.scores` or a new, clearly defined field so they can be surfaced via the API.

- **API: expose explanations in responses**:
  - `GET /runs/{run_id}/candidates` includes:
    - `scores.I`, `scores.P`, `scores.R` (existing).
    - `scores.ranking_explanation` (string).
    - `scores.ranking_factors` (optional structured object).
  - API docs and Pydantic response models are updated to reflect the new fields.

- **Frontend: list-level explanation snippets**:
  - In `ResultsView`, each candidate card shows:
    - Existing P/R/I chips.
    - A short snippet of the ranking explanation (e.g., first sentence, truncated to one line).
  - For the **top-ranked candidate**, the explanation is visually emphasized (e.g., bolded label or subtle highlight) to draw attention.

- **Frontend: detail view explanation**:
  - The candidate detail modal/page includes:
    - Full `ranking_explanation` text.
    - A compact list of `top_positive_factors` and `top_negative_factors` (if available).
    - Clear indication of any hard-constraint violations and which constraints they are.
  - This view is readable without needing to inspect raw JSON.

- **Consistency and UX**:
  - Explanations are:
    - Short (1–3 sentences).
    - Plain language, non-technical where possible.
    - Consistent in tone and structure across runs.
  - If explanations are missing (e.g., legacy runs), the UI degrades gracefully with a neutral placeholder (“No ranking explanation available for this run.”).

## Tasks
- **Backend (ranking logic)**:
  - [ ] Extend `RankerService.rank_candidates` to compute:
    - `ranking_explanation` per candidate from aggregated P, R, constraint satisfaction, and hard-constraint flags.
    - `ranking_factors.top_positive_factors` and `top_negative_factors` (simple heuristics are acceptable for MVP).
  - [ ] Decide how to store these fields:
    - Either inside `Candidate.scores` (e.g., `scores.ranking_explanation`) or a separate JSON column, documented clearly.
  - [ ] Update any relevant unit tests (e.g., `test_ranker_service.py`) to cover explanation generation for:
    - Clear winner candidates.
    - Candidates with hard-constraint violations.
    - Candidates with similar P/R but different tradeoffs.

- **API**:
  - [ ] Update response models (`CandidateResponse` etc.) to include explanation fields.
  - [ ] Ensure `GET /runs/{run_id}/candidates` populates the new fields from the DB.
  - [ ] Add/extend tests to verify these fields appear correctly in API responses.

- **Frontend (ResultsView)**:
  - [ ] Update `Candidate` type in `frontend/lib/api.ts` to include explanation fields.
  - [ ] Render a one-line snippet from `ranking_explanation` in each candidate card (truncate with ellipsis if long).
  - [ ] Emphasize the top-ranked candidate’s explanation visually while keeping the UI clean.

- **Frontend (candidate detail modal)**:
  - [ ] Add a “Why this rank?” section that shows:
    - Full `ranking_explanation`.
    - Bullet lists for positive/negative factors, if present.
    - Any hard-constraint violations with constraint names / weights.
  - [ ] Ensure layout works well for both short and slightly longer explanations.

- **UX & validation**:
  - [ ] Run a sample pipeline, then:
    - Review the top 3 candidates’ explanations for clarity and usefulness.
    - Confirm they match the underlying P/R and constraint data.
  - [ ] Adjust wording templates or heuristics as needed for readability.

- **Sign-off**:
  - [ ] Capture a short example (screenshots or notes) showing:
    - Ranked list with explanation snippets.
    - Candidate detail with a clear, understandable “why” section.
  - [ ] User must sign off that the explanations are sufficient to understand ranking decisions at a glance.

## Notes
- This story is intentionally **MVP-simple**:
  - Explanations can be heuristic (e.g., derived from numeric comparisons) rather than generated by another LLM.
  - Future work could involve a dedicated “Explainer” agent that reads evaluations and produces richer narratives.
- Keeping explanations near the numeric scores helps reinforce the **I = P/R** framing and the role of constraints.


