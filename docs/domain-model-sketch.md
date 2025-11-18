# Int Crucible Domain Model Sketch

## Core Entities

### Project
- **Purpose**: Top-level container for a problem domain
- **Fields**: id, title, description, created_at, updated_at
- **Relationships**: 
  - Has many ChatSessions
  - Has one ProblemSpec
  - Has one WorldModel
  - Has many Runs
  - Has many Issues

### ChatSession
- **Purpose**: A conversation thread within a project
- **Fields**: id, project_id, title, mode (setup/analysis), created_at, updated_at
- **Relationships**:
  - Belongs to Project
  - Has many Messages
  - Optionally linked to Run or Candidate (for focused analysis)

### Message
- **Purpose**: Individual message in a chat session
- **Fields**: id, chat_session_id, role (user/system/agent), content (text), metadata (JSON), created_at
- **Relationships**:
  - Belongs to ChatSession

### ProblemSpec
- **Purpose**: Structured problem specification
- **Fields**: id, project_id, constraints (JSON array: name, description, weight 0-100), goals (JSON array), resolution (coarse/medium/fine), mode (full_search/eval_only/seeded), created_at, updated_at
- **Relationships**:
  - Belongs to Project (one-to-one)

### WorldModel
- **Purpose**: Structured world model representation
- **Fields**: id, project_id, model_data (JSON: actors, mechanisms, resources, constraints, assumptions, simplifications), created_at, updated_at
- **Relationships**:
  - Belongs to Project (one-to-one)

### Run
- **Purpose**: An execution of the pipeline (ProblemSpec → WorldModeller → Designers → ScenarioGenerator → Evaluators → I-Ranker)
- **Fields**: id, project_id, mode (full_search/eval_only/seeded), config (JSON: budget, options), status (created/running/completed/failed), created_at, started_at, completed_at
- **Relationships**:
  - Belongs to Project
  - Has many Candidates
  - Has one ScenarioSuite
  - Has many Evaluations

### Candidate
- **Purpose**: A candidate solution generated or evaluated in a run
- **Fields**: id, run_id, project_id, origin (user/system), mechanism_description (text), predicted_effects (JSON), scores (JSON: P, R, I, constraint_satisfaction), provenance_log (JSON array), parent_ids (JSON array), status (new/under_test/promising/weak/rejected), created_at, updated_at
- **Relationships**:
  - Belongs to Run
  - Belongs to Project
  - Has many Evaluations
  - Can have parent Candidates (via parent_ids)

### ScenarioSuite
- **Purpose**: Collection of scenarios for a run
- **Fields**: id, run_id, scenarios (JSON array), created_at
- **Relationships**:
  - Belongs to Run (one-to-one)

### Evaluation
- **Purpose**: Evaluation of a candidate against a scenario
- **Fields**: id, candidate_id, scenario_id (string reference), P (prediction quality), R (resource cost), constraint_satisfaction (JSON), explanation (text), created_at
- **Relationships**:
  - Belongs to Candidate

### Issue
- **Purpose**: User-flagged or system-detected issue
- **Fields**: id, project_id, run_id (optional), candidate_id (optional), type (model/constraint/evaluator/scenario), severity (minor/important/catastrophic), description (text), resolution_status (open/resolved/invalidated), created_at, resolved_at
- **Relationships**:
  - Belongs to Project
  - Optionally linked to Run
  - Optionally linked to Candidate

## Relationship Summary

```
Project (1) ──< (N) ChatSession
Project (1) ──< (1) ProblemSpec
Project (1) ──< (1) WorldModel
Project (1) ──< (N) Run
Project (1) ──< (N) Issue

ChatSession (1) ──< (N) Message

Run (1) ──< (N) Candidate
Run (1) ──< (1) ScenarioSuite

Candidate (1) ──< (N) Evaluation
```

## Alignment with Kosmos

- **Kosmos ResearchSession** vs **Int Crucible Project**: Similar concept (grouping related work), but Project is more focused on problem-solving vs research
- **Kosmos Experiment** vs **Int Crucible Run**: Similar lifecycle (created → running → completed), but Run is a full pipeline execution
- **Kosmos Hypothesis** vs **Int Crucible Candidate**: Both represent proposed solutions, but Candidate is more design-focused
- **Kosmos Result** vs **Int Crucible Evaluation**: Both store evaluation results, but Evaluation is scenario-based
- **Kosmos AgentRecord**: Can be reused/adapted for tracking Crucible agent instances

## Design Decisions

1. **JSON Columns**: Used for flexible structures (constraints, world model, scenarios, provenance) to allow schema evolution
2. **String IDs**: Using string UUIDs for all primary keys (consistent with Kosmos)
3. **Timestamps**: All entities have created_at; mutable entities also have updated_at
4. **Provenance**: Stored as JSON array on Candidate; future can map to graph structure
5. **Status Enums**: Using string enums for status fields (compatible with SQLAlchemy and JSON serialization)

