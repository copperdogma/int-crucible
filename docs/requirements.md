# Project Requirements

Int Crucible

**Notes -- DO NOT REMOVE**
- This document focuses on WHAT the system should do and WHY, not HOW it should be implemented.
- When recording requirements that go beyond high-level requirements this document, refer back to `scratchpad.mdc`. Should we transition to the next phase? `scratchpad.mdc` will explain what script to run to do that.
**Notes -- DO NOT REMOVE**

---

## Core Purpose
Int Crucible is a general multi-agent reasoning system that helps its creator (the initial user) iteratively improve complex systems and designs, starting with improving Int Crucible itself. It does this by constructing world models, generating candidate solutions, stress-testing them, and ranking them according to an explicit intelligence metric \(I = P/R\) (prediction quality divided by resource cost).

## Fundamental Principles
- **Domain-agnostic reasoning**: The system must work across problem domains (e.g., constitutions, engineering systems, algorithms, policy), without being hard-coded to a single domain.
- **Transparency and provenance**: For every candidate and conclusion, the system must expose how it was produced, including assumptions, scenarios, and lineage.
- **Composable architecture**: Agents and modules (ProblemSpec, WorldModeller, Designers, Evaluators, Ranker, etc.) should be conceptually separable so they can be replaced or extended later.
- **Resource awareness**: The system must explicitly track and reason about resources/costs (the \(R\) in \(I = P/R\)), even if in a coarse way in the MVP.
- **MVP-first**: The initial implementation should favor a simple, end-to-end usable loop for a single user (the creator) over completeness or optimization.

## Target Audience
The first user is the system’s creator (you), a software developer using Int Crucible to iteratively improve Int Crucible itself and other complex designs. The system should feel natural to a technically sophisticated solo user, with enough structure to later be extended for teams or external consumers.

## Key Features
- **ProblemSpec agent**: Takes a free-form problem description and structures it into constraints (with weights 0–100), goals/objectives, resolution requirements (coarse/medium/fine), and mode (full search vs eval-only vs seeded search).
- **WorldModeller (MVP)**: Builds a usable (not exhaustive) world model from the ProblemSpec using only model priors and prompt context; identifies actors, mechanisms, resources, limits, assumptions, and simplifications; outputs a structured representation (JSON-like).
- **Designer agents (MVP)**: Generate multiple, diverse candidate solutions using the world model; each candidate includes mechanism description, expected effects, and rough constraint-compliance estimates.
- **ScenarioGenerator**: Produces a minimal suite of synthetic scenarios that stress critical assumptions and high-weight constraints derived from the world model.
- **Evaluator agents**: Perform language-level scenario analysis (no code execution in MVP), scoring each candidate on prediction consistency (P), resource/complexity cost (R), and weighted constraint satisfaction; output structured scores plus explanations.
- **I-Ranker**: Computes an intelligence score for each candidate \(I = P/R\), applies constraint weights (flagging violations of hard constraints), and produces a ranked list with rationale.
- **Provenance tracker**: Maintains lineage information for each candidate (parents, origin, transformation history) and attaches a simple provenance log to candidates and key outputs.
- **Interaction shell (MVP UI)**: A minimal UI where the user can enter a problem, inspect the ranked candidates, see constraint scores and provenance, and iterate.
- **Programmatic interface (API/CLI)**: A callable interface (e.g., API or CLI entrypoint) that accepts a problem spec and returns structured outputs (world model summary, candidate list, scores, and explanations).

## MVP Criteria
The MVP is considered successful when, for a moderately complex design or reasoning problem:
- The user can submit a problem via a simple interface (CLI/API and thin UI).
- The system runs a complete end-to-end loop: ProblemSpec → WorldModeller → Designers → ScenarioGenerator → Evaluators → I-Ranker → Provenance-backed output.
- The system produces at least 3–5 diverse candidate solutions with:
  - Structured scores for \(P\), \(R\), and constraint satisfaction.
  - An explicit \(I = P/R\) score per candidate.
  - A brief, understandable explanation of why top candidates are ranked higher.
- The user can inspect the provenance/lineage of candidates at a basic level (e.g., parent relationships and key transformation steps).
- All of the above can be driven by a single technical user (you) without additional tooling, and can be applied to improving Int Crucible itself.

## Outstanding Questions

### High Priority
- What is the minimal interaction model for the MVP UI (single text box + results view vs step-by-step wizard)?
- How much manual control should the user have over constraint weights vs automatic suggestions?

### Medium Priority
- Should the MVP support both “full search” and “eval-only” modes at launch, or can one mode be deferred?
- How configurable should world model schema be in the MVP vs being a fixed JSON shape?

### Future Consideration
- How will the system support multi-user/team workflows (shared problems, shared candidate sets, comments)?
- What integrations (e.g., external research APIs, simulation backends, real code execution) should be prioritized after the MVP?

---

## Non-Requirements Detail
**Note**: This section is intentionally left empty during the Planning phase after its previous contents were migrated into `docs/design.md` and `docs/architecture.md`.


