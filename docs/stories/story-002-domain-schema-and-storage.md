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
- [x] Sketch the domain model (entities and relationships) for Int Crucible based on requirements and design documents.
- [x] Compare this domain model with Kosmos's DB models (`vendor/kosmos/kosmos/db`) to identify overlap and potential reuse.
- [x] Design a Postgres schema (tables and JSON columns) that supports Int Crucible's entities while staying compatible with Kosmos where reasonable.
- [x] Implement the schema and migrations (e.g., using Alembic or the same migration tooling used by Kosmos).
- [x] Add basic backend functions or repositories to create/read/update core entities (Project, Run, Candidate, etc.).
- [x] Document the schema (e.g., in `docs/architecture.md` or a dedicated section) and how it maps to Kosmos concepts.
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- The world model and provenance representations should keep future graph/knowledge-graph integration in mind but do not need to implement a full graph database in the MVP.

## Work Log

### 20251117-2050 — Domain model sketch and schema design
- **Result:** Success; created comprehensive domain model sketch document
- **Notes:** 
  - Documented all 10 core entities (Project, ChatSession, Message, ProblemSpec, WorldModel, Run, Candidate, ScenarioSuite, Evaluation, Issue)
  - Identified relationships and alignment points with Kosmos models
  - Created `docs/domain-model-sketch.md` as reference
- **Next:** Implement SQLAlchemy models

### 20251117-2055 — SQLAlchemy models implementation
- **Result:** Success; all models implemented with proper relationships
- **Notes:**
  - Created `crucible/db/models.py` with all 10 entity models
  - Used Kosmos Base for compatibility
  - Implemented string enums for all status fields
  - Fixed conflict: renamed `metadata` field to `message_metadata` in Message model (SQLAlchemy reserved word)
  - All tables prefixed with `crucible_` to avoid conflicts with Kosmos
- **Next:** Set up Alembic for migrations

### 20251117-2100 — Alembic setup and initial migration
- **Result:** Success; Alembic configured and initial migration created
- **Notes:**
  - Created `alembic.ini` and `alembic/env.py` 
  - Combined Kosmos and Crucible metadata in Alembic env for unified migration tracking
  - Generated initial migration: `alembic/versions/b88f38b6830a_initial_crucible_schema.py`
  - Migration includes all Crucible tables with proper foreign keys and constraints
- **Next:** Create CRUD operations/repositories

### 20251117-2110 — CRUD operations implementation
- **Result:** Success; comprehensive repository functions created
- **Notes:**
  - Created `crucible/db/repositories.py` with CRUD operations for all entities
  - Functions follow consistent patterns: create, get, list, update
  - All functions use UUID generation for IDs
  - Proper session management and transaction handling
- **Next:** Document schema in architecture.md

### 20251117-2115 — Schema documentation
- **Result:** Success; comprehensive schema documentation added
- **Notes:**
  - Added "Database Schema" section to `docs/architecture.md`
  - Documented all entities with fields, relationships, and purposes
  - Documented design decisions (naming, JSON columns, IDs, timestamps)
  - Documented alignment with Kosmos and migration process
- **Next:** User review and sign-off

### 20251117-2130 — Migration application and verification
- **Result:** Success; migration applied and all functionality verified
- **Notes:**
  - Applied migration: `alembic upgrade head` completed successfully
  - Verified database initialization works correctly
  - Tested CRUD operations: Project, ChatSession, Message create/read/list all working
  - Verified all models import correctly
  - Linter passes with no errors
  - All repository functions operational
- **Next:** User review and sign-off

