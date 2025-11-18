# Project Architecture

Int Crucible

**Note**: This document details the architectural decisions and setup progress for the project.

---

## Architectural Decisions
- **Architecture style**: Modular monolith with a TypeScript React/Next.js frontend and a Python/FastAPI backend.
- **Frontend**: Next.js (React + TypeScript) SPA/SSR hybrid for chat UI, project views, live spec/world-model panels, run configuration, and candidate/issue views.
- **Backend**: FastAPI-based service that exposes HTTP/JSON endpoints for projects, chats, specs/world models, runs, candidates, and feedback; hosts the orchestration engine and agents.
- **Orchestration**: In-process Python orchestration of agents (ProblemSpec, WorldModeller, Designers, ScenarioGenerator, Evaluators, I-Ranker, Feedback) using async tasks; designed so that orchestration could later be delegated to Kosmos or a similar system.
- **Persistence**: PostgreSQL as the primary store for projects, chats, runs, candidates, issues, and provenance logs, with JSON columns for world models and scenario suites.
- **LLM access**: A thin abstraction over an OpenAI-compatible API, configured per environment, so agents can share token accounting and logging.
- **World model representation**: MVP uses structured JSON stored in Postgres; future versions may project this into a graph database when higher-fidelity modelling or lineage queries are needed.
- **Provenance & lineage**: Provenance information is attached to candidates, world-model changes, and issues via structured logs; the schema is chosen so it can later be mapped to a graph model inspired by Kosmos’s knowledge graph and provenance patterns.
- **Extensibility**: Agents are implemented as Python classes/functions behind clear interfaces so they can be swapped or extended (e.g., alternative Designers or Evaluators) without changing the UI.

## Setup Progress
- [ ] Initialize backend (FastAPI project structure, dependencies, configuration).
- [ ] Initialize frontend (Next.js project structure, shared UI components).
- [ ] Define initial database schema and migrations for projects, chats, runs, candidates, issues, and provenance.
- [ ] Implement LLM client abstraction and environment-based configuration.
- [ ] Implement basic orchestration scaffolding (run lifecycle, pipeline stages, background execution).
- [ ] Set up local development environment (docker-compose or equivalent for Postgres and services).

## Notes
- The architecture is intentionally biased toward a single deployment unit for the backend to keep the MVP simple, while keeping internal module boundaries clear for future extraction.
- Integration with Kosmos is treated as a future enhancement: the current orchestration layer is designed so that Kosmos could later take over responsibilities like multi-agent rollouts, knowledge graph storage, and sandboxed execution.
- The world model, candidate, and provenance schemas are designed to be compatible with a future graph-based representation, aligning with the intent to eventually reuse or interoperate with a Kosmos-style knowledge graph.
- Future phases can introduce separate services for heavy workloads (e.g., scenario evaluation or research-enhanced world modelling) if I/O or compute demands grow beyond a single service.