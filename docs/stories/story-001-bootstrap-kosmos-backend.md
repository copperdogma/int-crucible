# Story: Bootstrap Kosmos-backed backend environment

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **Core Purpose** (Int Crucible as a general multi-agent reasoning system).
  - **Key Features** – Programmatic interface (API/CLI), Evaluators, I-Ranker, and Provenance tracker.

## Alignment with Design
- See `docs/design.md`:
  - **Architecture Overview** – Backend API + Orchestration Engine (Kosmos-backed).
  - **Feature: Run Configuration & Execution Pipeline** – pipeline stages and entities for runs and candidates.

## Acceptance Criteria
- Kosmos (vendored under `vendor/kosmos`) can be installed and imported from the Int Crucible backend environment.
- The backend has a minimal FastAPI app that can:
  - Connect to the same database engine used by Kosmos (or a compatible Postgres instance).
  - Invoke a simple Kosmos agent or workflow as a smoke test.
- A basic CLI or script exists to run a trivial Kosmos-backed operation (e.g., listing available agents or performing a no-op run).
- Configuration (environment variables, `.env`) is documented so that the backend can start with Kosmos enabled on a fresh checkout.

## Tasks
- [ ] Review Kosmos documentation and planning guides under `vendor/kosmos/docs` to understand core components (`kosmos/core`, `kosmos/agents`, `kosmos/db`, etc.).
- [ ] Decide how Int Crucible will import Kosmos (direct package import vs editable install from `vendor/kosmos`).
- [ ] Set up a Python backend environment (virtualenv/poetry) that can install Kosmos dependencies.
- [ ] Create an initial FastAPI app skeleton for Int Crucible and integrate Kosmos configuration (LLM provider, DB URL, logging).
- [ ] Implement a minimal test endpoint or CLI command that calls a simple Kosmos agent or workflow to verify integration.
- [ ] Document setup steps and configuration in `README.md` (or a dedicated backend setup section).
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- Kosmos’s production-ready architecture (multi-provider LLM, DB, orchestration) is reused as much as possible; Int Crucible will layer its own domain-specific agents and models on top. See [`jimmc414/Kosmos`](https://github.com/jimmc414/Kosmos) for overall structure.


