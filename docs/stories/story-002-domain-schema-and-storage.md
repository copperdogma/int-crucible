# Story: Define and persist Int Crucible domain schema

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Key Features** – ProblemSpec agent, WorldModeller, Designer agents, ScenarioGenerator, Evaluators, I-Ranker, Provenance tracker.
  - **MVP Criteria** – structured scores, world model, candidate lineage.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Chat-First Project & ProblemSpec Modelling** – `Project`, `ChatSession`, `Message`, `ProblemSpec`.
  - **Feature: Live Spec / World-Model View** – `WorldModel` JSON structure.
  - **Feature: Run Configuration & Execution Pipeline** – `Run`, `Candidate`, `ScenarioSuite`, `Evaluation`.
  - **Feature: Feedback Loop on Model, Constraints, and Evaluations** – `Issue`.

## Acceptance Criteria
- A first-pass domain schema for Int Crucible exists and is documented (ERD or equivalent) for:
  - Project, ChatSession, Message, ProblemSpec, WorldModel.
  - Run, Candidate, ScenarioSuite, Evaluation, Issue.
- The schema is implemented in the database layer (Postgres) with migrations.
- Core CRUD operations for these entities are available from the backend (even if not all are exposed via the UI yet).
- The schema aligns with and does not conflict with Kosmos’s DB models; future integration with `kosmos/db` is feasible.
- User reviews and approves the schema as “good enough for MVP”.

## Tasks
- [ ] Sketch the domain model (entities and relationships) for Int Crucible based on requirements and design documents.
- [ ] Compare this domain model with Kosmos’s DB models (`vendor/kosmos/kosmos/db`) to identify overlap and potential reuse.
- [ ] Design a Postgres schema (tables and JSON columns) that supports Int Crucible’s entities while staying compatible with Kosmos where reasonable.
- [ ] Implement the schema and migrations (e.g., using Alembic or the same migration tooling used by Kosmos).
- [ ] Add basic backend functions or repositories to create/read/update core entities (Project, Run, Candidate, etc.).
- [ ] Document the schema (e.g., in `docs/architecture.md` or a dedicated section) and how it maps to Kosmos concepts.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The world model and provenance representations should keep future graph/knowledge-graph integration in mind but do not need to implement a full graph database in the MVP.


