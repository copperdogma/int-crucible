# Project Architecture

Int Crucible

**Note**: This document details the architectural decisions and setup progress for the project.

---

## Architectural Decisions
- **Architecture style**: Modular monolith with a TypeScript React/Next.js frontend and a Python/FastAPI backend.
- **Frontend**: Next.js (React + TypeScript) SPA/SSR hybrid for chat UI, project views, live spec/world-model panels, run configuration, and candidate/issue views.
- **Backend**: FastAPI-based service that exposes HTTP/JSON endpoints for projects, chats, specs/world models, runs, candidates, and feedback; wraps and extends the Kosmos Python package (vendored under `vendor/kosmos`) for orchestration, knowledge, and storage concerns.
- **Orchestration**: Python orchestration layer that uses Kosmos’s agent framework and workflow primitives (from `kosmos/core` and `kosmos/agents`) to implement the Int Crucible pipeline (ProblemSpec, WorldModeller, Designers, ScenarioGenerator, Evaluators, I-Ranker, Feedback) as a composed run graph.
- **Persistence**: PostgreSQL as the primary store for projects, chats, runs, candidates, issues, and provenance logs, reusing or aligning with Kosmos’s existing DB layer and migrations (from `kosmos/db`) where appropriate; JSON columns for Int Crucible-specific world models and scenario suites.
- **LLM access**: A thin abstraction over an OpenAI-compatible API, configured per environment, so agents can share token accounting and logging.
- **World model representation**: MVP uses structured JSON stored in Postgres; future versions may project this into a graph database when higher-fidelity modelling or lineage queries are needed.
- **Provenance & lineage**: Provenance information is attached to candidates, world-model changes, and issues via structured logs; the schema is chosen so it can later be mapped to a graph model inspired by Kosmos’s knowledge graph and provenance patterns.
- **Extensibility**: Agents are implemented as Python classes/functions behind clear interfaces so they can be swapped or extended (e.g., alternative Designers or Evaluators) without changing the UI.

## Kosmos Integration

- **Repository integration**: The Kosmos project is vendored as a git subtree under `vendor/kosmos` and used as a Python package within the backend ([`jimmc414/Kosmos`](https://github.com/jimmc414/Kosmos)).
- **Core reuse**:
  - Int Crucible’s backend uses `kosmos/core` for configuration, logging, and LLM provider abstractions.
  - The agent framework from `kosmos/agents` is extended to implement Crucible-specific agents (ProblemSpec, WorldModeller, Designers, ScenarioGenerator, Evaluators, I-Ranker, Feedback).
- **Knowledge and storage**:
  - Kosmos’s database models and migrations in `kosmos/db` inform the schema for runs, experiments, and provenance.
  - Where compatible, Crucible reuses or adapts Kosmos’s knowledge and graph-related modules (e.g., from `kosmos/knowledge`) to represent world models and lineage, even if MVP initially persists them as JSON in Postgres.
- **Execution and evaluation**:
  - Int Crucible’s evaluation/scenario pipeline can later leverage Kosmos’s execution and analysis layers (`kosmos/execution`, `kosmos/analysis`, `kosmos/experiments`) for more sophisticated scenario tests and code-backed experiments.
  - For the MVP, Crucible primarily uses Kosmos’s orchestration and logging infrastructure while keeping evaluation language-level (no external experiment execution).
- **Boundary**:
  - Int Crucible maintains its own domain-specific models (ProblemSpec, WorldModel, Candidate, Issue) and UI/API contracts, while treating Kosmos as underlying infrastructure for multi-agent orchestration, storage, and (eventually) experimentation.

## Database Schema

Int Crucible uses a shared database (PostgreSQL or SQLite) with Kosmos. Crucible-specific tables are prefixed with `crucible_` to avoid conflicts.

### Core Entities

#### Project (`crucible_projects`)
- **Purpose**: Top-level container for a problem domain
- **Fields**: `id` (PK), `title`, `description`, `created_at`, `updated_at`
- **Relationships**: One-to-many with ChatSession, Run, Issue; One-to-one with ProblemSpec, WorldModel

#### ChatSession (`crucible_chat_sessions`)
- **Purpose**: A conversation thread within a project
- **Fields**: `id` (PK), `project_id` (FK), `title`, `mode` (setup/analysis), `run_id`, `candidate_id`, `created_at`, `updated_at`
- **Relationships**: Many-to-one with Project; One-to-many with Message

#### Message (`crucible_messages`)
- **Purpose**: Individual message in a chat session
- **Fields**: `id` (PK), `chat_session_id` (FK), `role` (user/system/agent), `content`, `message_metadata` (JSON), `created_at`
- **Relationships**: Many-to-one with ChatSession

#### ProblemSpec (`crucible_problem_specs`)
- **Purpose**: Structured problem specification
- **Fields**: `id` (PK), `project_id` (FK, unique), `constraints` (JSON array), `goals` (JSON array), `resolution` (coarse/medium/fine), `mode` (full_search/eval_only/seeded), `created_at`, `updated_at`
- **Relationships**: One-to-one with Project

#### WorldModel (`crucible_world_models`)
- **Purpose**: Structured world model representation
- **Fields**: `id` (PK), `project_id` (FK, unique), `model_data` (JSON), `created_at`, `updated_at`
- **Relationships**: One-to-one with Project

#### Run (`crucible_runs`)
- **Purpose**: An execution of the full pipeline
- **Fields**: `id` (PK), `project_id` (FK), `mode`, `config` (JSON), `status` (created/running/completed/failed/cancelled), `created_at`, `started_at`, `completed_at`
- **Relationships**: Many-to-one with Project; One-to-many with Candidate, Evaluation; One-to-one with ScenarioSuite

#### Candidate (`crucible_candidates`)
- **Purpose**: A candidate solution
- **Fields**: `id` (PK), `run_id` (FK), `project_id` (FK), `origin` (user/system), `mechanism_description`, `predicted_effects` (JSON), `scores` (JSON), `provenance_log` (JSON array), `parent_ids` (JSON array), `status` (new/under_test/promising/weak/rejected), `created_at`, `updated_at`
- **Relationships**: Many-to-one with Run, Project; One-to-many with Evaluation

#### ScenarioSuite (`crucible_scenario_suites`)
- **Purpose**: Collection of scenarios for a run
- **Fields**: `id` (PK), `run_id` (FK, unique), `scenarios` (JSON array), `created_at`
- **Relationships**: One-to-one with Run

#### Evaluation (`crucible_evaluations`)
- **Purpose**: Evaluation of a candidate against a scenario
- **Fields**: `id` (PK), `candidate_id` (FK), `run_id` (FK), `scenario_id` (string), `P` (JSON), `R` (JSON), `constraint_satisfaction` (JSON), `explanation`, `created_at`
- **Relationships**: Many-to-one with Candidate, Run

#### Issue (`crucible_issues`)
- **Purpose**: User-flagged or system-detected issue
- **Fields**: `id` (PK), `project_id` (FK), `run_id`, `candidate_id`, `type` (model/constraint/evaluator/scenario), `severity` (minor/important/catastrophic), `description`, `resolution_status` (open/resolved/invalidated), `created_at`, `resolved_at`
- **Relationships**: Many-to-one with Project

### Schema Design Decisions

1. **Table Naming**: All Crucible tables prefixed with `crucible_` to avoid conflicts with Kosmos tables
2. **JSON Columns**: Used for flexible structures (constraints, world model, scenarios, provenance) to allow schema evolution
3. **String IDs**: Using string UUIDs for all primary keys (consistent with Kosmos)
4. **Timestamps**: All entities have `created_at`; mutable entities also have `updated_at`
5. **Status Enums**: Using string enums for status fields (compatible with SQLAlchemy and JSON serialization)
6. **Provenance**: Stored as JSON array on Candidate; future can map to graph structure

### Alignment with Kosmos

- **Shared Database**: Crucible and Kosmos share the same database instance
- **Compatible Patterns**: Both use SQLAlchemy, string UUIDs, JSON columns, similar timestamp patterns
- **No Conflicts**: Crucible tables use `crucible_` prefix; Kosmos tables remain unchanged
- **Future Integration**: Schema designed to allow future graph/knowledge-graph integration similar to Kosmos

### Migrations

Migrations are managed via Alembic. The Alembic configuration (`alembic/env.py`) combines metadata from both Kosmos and Crucible models to ensure all tables are tracked.

- Initial migration: `alembic/versions/b88f38b6830a_initial_crucible_schema.py`
- To create new migration: `alembic revision --autogenerate -m "description"`
- To apply migrations: `alembic upgrade head`

## Setup Progress
- [x] Initialize backend (FastAPI project structure, dependencies, configuration).
- [ ] Initialize frontend (Next.js project structure, shared UI components).
- [x] Define initial database schema and migrations for projects, chats, runs, candidates, issues, and provenance.
- [ ] Implement LLM client abstraction and environment-based configuration.
- [ ] Implement basic orchestration scaffolding (run lifecycle, pipeline stages, background execution).
- [ ] Set up local development environment (docker-compose or equivalent for Postgres and services).

## Notes
- The architecture is intentionally biased toward a single deployment unit for the backend to keep the MVP simple, while keeping internal module boundaries clear for future extraction.
- Kosmos is treated as the primary orchestration and infrastructure backbone for the backend; the Int Crucible layer focuses on domain-specific agents, world modelling, and the I = P/R reasoning pipeline.
- The world model, candidate, and provenance schemas are designed to be compatible with a future graph-based representation, aligning with the intent to reuse or interoperate with Kosmos’s knowledge graph and provenance machinery.
- Future phases can introduce separate services for heavy workloads (e.g., scenario evaluation or research-enhanced world modelling) if I/O or compute demands grow beyond a single service.