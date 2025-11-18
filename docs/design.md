# Project Design

Int Crucible

**Note**: This document outlines the technical design and implementation details (HOW), based on the requirements in `requirements.md`.

---

## Architecture Overview

For the MVP, Int Crucible will be implemented as a **single web application** with a clear separation between:

- **Frontend UI**: A chat-first, project-oriented web interface that provides:
  - Project management and chat sessions.
  - A live, human-readable spec/world-model view.
  - Run configuration controls.
  - Run-time status and candidate views.
  - Post-run exploration and feedback tools.
- **Backend API + Orchestration Engine (Kosmos-backed)**:
  - Manages projects, chats, specs, world models, runs, and candidates.
  - Wraps the Kosmos backend (vendored under `vendor/kosmos`) for core infrastructure: configuration, logging, LLM access, agent framework, and persistence patterns ([`jimmc414/Kosmos`](https://github.com/jimmc414/Kosmos)).
  - Hosts Crucible-specific agents (ProblemSpec, WorldModeller, Designers, ScenarioGenerator, Evaluators, I-Ranker, Feedback) implemented on top of Kosmos’s agent framework.
  - Orchestrates the end-to-end pipeline for each run (ProblemSpec → WorldModeller → Designers → ScenarioGenerator → Evaluators → I-Ranker) using Kosmos’s workflow primitives.
  - Exposes a programmatic interface (HTTP/JSON and CLI entrypoint) that mirrors what the UI uses.
- **Persistence Layer**:
  - Stores projects, chats, problem specs, world models, runs, candidates, scores, and provenance.
  - MVP: relational schema (e.g., PostgreSQL) for core entities and simple JSON fields for world models and scenario suites.
  - Future: optional graph storage for higher-fidelity world models and lineage.

The overall style is a **modular monolith**: one deployable backend service containing the orchestration engine and agents, plus one frontend app. Internal modules (e.g., agents, feedback, provenance) are kept logically separate so they can later be extracted or swapped. Integration with external systems like Kosmos, graph databases, or research APIs is treated as a **post-MVP concern** and designed behind clear interfaces.

---

## Technology Stack

MVP technology choices (subject to refinement before implementation):

- **Frontend**
  - Framework: React (likely Next.js) with TypeScript.
  - Styling: Tailwind CSS (or similar utility-first framework) for rapid iteration.
  - State management: React Query (or equivalent) for server state; local component state for UI-only concerns.
- **Backend**
  - Language: Python 3.x.
  - Web framework: FastAPI (or similar async framework) for HTTP API and background tasks.
  - Orchestration: Internal Python modules implementing the agents and pipeline; future compatibility with Kosmos as an orchestration backend.
- **Data & Infrastructure**
  - Database: PostgreSQL for projects, chats, runs, candidates, and provenance logs; JSON columns for world models and scenario suites.
  - Vector / embedding store: deferred until needed; MVP can operate without a dedicated vector DB.
  - LLM access: OpenAI-compatible client abstraction, configured per-environment.
- **Tooling**
  - Testing: Pytest for backend; Jest/Testing Library for frontend.
  - Packaging & build: standard Python tooling (poetry/pip) and Node tooling for frontend.

---

## Feature Implementations

### Feature: Chat-First Project & ProblemSpec Modelling

**Related Requirement**: See “Target Audience” and “Key Features – ProblemSpec agent” in `requirements.md`.  

- **UX / Flow**
  - The primary entry point is a **Project**. A project encapsulates:
    - A problem description and evolving ProblemSpec.
    - A world model.
    - Multiple chat sessions.
    - A history of runs and candidates.
  - Within a project, the user interacts via **chat sessions**:
    - The user describes the problem in free text.
    - An “Architect/ProblemSpec” agent asks structured follow-up questions (goals, constraints and weights, actors, resolution).
    - The UI renders these questions and answers as normal chat turns.
  - The backend maintains a structured `ProblemSpec` object per project that is updated incrementally as the chat progresses.
- **Backend Design**
  - Entities:
    - `Project`: id, title, description, created_at, updated_at.
    - `ChatSession`: id, project_id, title, mode (setup / analysis), created_at.
    - `Message`: id, chat_session_id, role (user/system/agent), content (text + metadata), created_at.
    - `ProblemSpec`: project_id, constraints (name, description, weight), goals, resolution, mode (full search / eval-only / seeded), stored as structured JSON.
  - The ProblemSpec agent:
    - Runs as an orchestrated function that consumes recent chat history and current ProblemSpec.
    - Produces:
      - Suggested updates to constraints, goals, resolution.
      - Follow-up questions for the user.
    - Is invoked when:
      - The user posts a message in “setup mode”.
      - The user explicitly clicks “Refine spec” or similar.
- **Programmatic Interface**
  - API endpoints to:
    - Create/list projects and chat sessions.
    - Post chat messages and receive agent responses.
    - Retrieve the current `ProblemSpec` for a project.

---

### Feature: Live Spec / World-Model View

**Related Requirement**: See “Key Features – WorldModeller (MVP)” and “Provenance tracker” in `requirements.md`.  

- **UX / Flow**
  - Alongside the chat, the UI shows a **live spec panel**:
    - Human-readable sections: Objectives, Constraints (with weights), Actors/Implementers, Assumptions & Simplifications.
    - This panel is editable as Markdown (or rich text) by the user.
  - A second view (toggled or side-by-side in later versions) can expose the structured internal representation (JSON-like/world-model graph).
  - The user can:
    - Edit the human-readable spec; the system parses changes and updates the structured `ProblemSpec` / world model.
    - Accept suggestions from the WorldModeller agent (e.g., “Add assumption A”, “Introduce actor B”).
- **Backend Design**
  - `WorldModel` stored as a structured JSON attached to the project:
    - `actors`, `mechanisms`, `resources`, `constraints`, `assumptions`, `simplifications`.
  - A WorldModeller agent:
    - Takes the current ProblemSpec and possibly a snapshot of chat messages.
    - Proposes changes to the WorldModel (add/update/remove nodes/relations).
    - Maintains a simple provenance log for each change (source message, agent, timestamp).
  - A bidirectional mapping layer:
    - Textual spec ⇄ `ProblemSpec`/WorldModel JSON.
    - MVP: simple heuristics + LLM-based parsing/formatting rather than a full DSL.

---

### Feature: Run Configuration & Execution Pipeline

**Related Requirement**: See “MVP Criteria” and all “Key Features”.  

- **UX / Flow**
  - Once the spec/world model is “good enough”, the user opens a **Run Configuration** panel:
    - Select mode: full search, eval-only, or seeded search.
    - Set a budget/depth slider (“fast & cheap” ↔ “deep & expensive”).
    - For eval-only / seeded:
      - Add or select candidate ideas from text inputs or previous runs.
  - The user starts a run; the UI shows:
    - A pipeline status bar: World modelling → Design → Evaluation → Ranking.
    - Basic progress indicators (stage status, candidate counts).
- **Backend Design**
  - Entities:
    - `Run`: id, project_id, mode, config (budget, options), status, created_at, completed_at.
    - `Candidate`: id, run_id, project_id, origin (user/system), mechanism description, predicted effects, scores, provenance_log, parent_ids.
    - `ScenarioSuite`: run_id, scenarios (JSON).
    - `Evaluation`: candidate_id, scenario_id, P, R, constraint_satisfaction, explanation.
  - Orchestration:
    - Each run triggers a pipeline:
      1. Use current ProblemSpec + WorldModel.
      2. Designers generate initial candidates (unless eval-only).
      3. ScenarioGenerator builds a minimal scenario suite.
      4. Evaluators score each candidate over scenarios.
      5. I-Ranker computes I = P/R and constraint-weighted rankings.
    - Implemented as an async workflow (e.g., background tasks or simple in-process queue for MVP).

---

### Feature: Run-Time Views, Candidate Board, and Post-Run Exploration

**Related Requirement**: See “I-Ranker”, “Provenance tracker”, and MVP criteria in `requirements.md`.  

- **UX / Flow**
  - During a run:
    - A **pipeline view** shows which stage each run is in and aggregate counters.
    - A **candidate board** shows candidate cards grouped by status (e.g., New, Under Test, Promising, Weak, Rejected).
    - An **issues panel** surfaces notable problems:
      - Model issues (conflicting assumptions).
      - Constraint issues (hard constraints being violated).
      - Evaluation issues (weak scenario coverage).
  - After a run:
    - The user sees a **ranked list** of final candidates:
      - Summary, P/R scores, constraint satisfaction, I score, and warnings.
    - Clicking a candidate opens a **detail view**:
      - Mechanism description.
      - Scenario results and explanations.
      - Constraint breakdown.
      - Lineage (parents and key transformation steps).
    - “Discuss this candidate” launches a focused chat session seeded with the candidate and relevant model context.
- **Backend Design**
  - Candidate status fields and computed flags support board grouping.
  - Provenance tracking:
    - `provenance_log` on candidates and possibly world-model entries.
    - Each log entry: type (design_refine, eval_result, feedback_patch), timestamp, actor (user/system/agent), reference ids.
  - API endpoints to:
    - Stream or poll run status and candidate summaries.
    - Fetch full details for a selected candidate.

---

### Feature: Feedback Loop on Model, Constraints, and Evaluations

**Related Requirement**: See “Provenance tracker” and Future roadmap in `requirements.md` (feedback & self-improvement are post-MVP, but a minimal feedback loop is highly desirable).  

- **UX / Flow**
  - The user can flag issues directly from:
    - The spec/world-model view (e.g., “Assumption X is wrong”).
    - A candidate detail view (e.g., “This ignores constraint Y”).
  - A Feedback agent:
    - Asks a small number of clarifying questions in chat.
    - Classifies the issue (model / constraint / evaluator / scenario).
    - Proposes actions:
      - Minor patch + re-score.
      - Update constraints and partially rerun.
      - Invalidate affected candidates and rerun from an earlier stage.
  - The user chooses whether an issue is minor, important, or catastrophic, which controls the scope of re-computation.
- **Backend Design**
  - `Issue` entity: id, project_id, run_id (optional), candidate_id (optional), type, severity, description, resolution_status.
  - Feedback agent runs like other agents but with a specialized prompt and access to context (ProblemSpec, WorldModel, candidate, evaluations).
  - Integration points:
    - When an issue is resolved, the orchestrator may:
      - Schedule partial re-runs.
      - Update ProblemSpec/WorldModel.
      - Mark candidates as invalidated or superseded.

---

### Feature: Multiple Chats Per Project

**Related Requirement**: Implied by “Interaction shell (MVP UI)” and the need for iterative use in `requirements.md`.  

- **UX / Flow**
  - Each project can have multiple chat sessions:
    - Setup chats (spec/world-model construction).
    - Analysis chats (deep dives on specific runs or candidates).
    - “What-if” branch chats exploring alternative assumptions.
  - Chats share the same underlying project state (ProblemSpec, WorldModel, run history) but can focus on different slices of that state.
- **Backend Design**
  - `ChatSession` and `Message` entities (as above) support multiple threads per project.
  - Each chat can be associated with a specific run or candidate for context.
  - The orchestrator uses the chat’s context (linked project/run/candidate) to load the right subset of state when generating responses.

---