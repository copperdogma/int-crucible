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

## Setup Progress
- [ ] Initialize backend (FastAPI project structure, dependencies, configuration).
- [ ] Initialize frontend (Next.js project structure, shared UI components).
- [ ] Define initial database schema and migrations for projects, chats, runs, candidates, issues, and provenance.
- [ ] Implement LLM client abstraction and environment-based configuration.
- [ ] Implement basic orchestration scaffolding (run lifecycle, pipeline stages, background execution).
- [ ] Set up local development environment (docker-compose or equivalent for Postgres and services).

## Notes
- The architecture is intentionally biased toward a single deployment unit for the backend to keep the MVP simple, while keeping internal module boundaries clear for future extraction.
- Kosmos is treated as the primary orchestration and infrastructure backbone for the backend; the Int Crucible layer focuses on domain-specific agents, world modelling, and the I = P/R reasoning pipeline.
- The world model, candidate, and provenance schemas are designed to be compatible with a future graph-based representation, aligning with the intent to reuse or interoperate with Kosmos’s knowledge graph and provenance machinery.
- Future phases can introduce separate services for heavy workloads (e.g., scenario evaluation or research-enhanced world modelling) if I/O or compute demands grow beyond a single service.