Document 1 — Int Crucible: Specification (MVP → Advanced)

Created via congo with GPT5.1: https://chatgpt.com/share/691bb29e-79c4-800a-8efb-e941fe8b24c8

Int Crucible — System Specification (v0.1)

A general multi-agent reasoning architecture grounded in I = P/R.

⸻

I. Purpose & Design Goals

Int Crucible is a multi-agent reasoning system that:
	•	Constructs world-models at appropriate resolution.
	•	Generates solution candidates from those models.
	•	Evaluates those candidates via scenario tests and constraint satisfaction.
	•	Ranks them using the user-defined intelligence metric I = P/R (Prediction quality / Resource cost).
	•	Iterates, self-corrects, and eventually self-improves.

The design must be:
	•	Domain-agnostic (constitutions, engineering, algorithms, policy, etc.)
	•	Transparent (full provenance, lineage, traceability)
	•	Composable (replace any agent or module)
	•	Resource-aware (explicit R tracking and optimization)

This spec intentionally avoids assuming any specific implementation (Kosmos, LangGraph, custom infra, etc.).

⸻

II. MVP Scope (Minimum Viable System)

The MVP focuses on core reasoning and basic world modelling.

A. Required Components

1. ProblemSpec Agent
	•	Parses user intent into:
	•	Constraints (each with a weight 0–100)
	•	Goals/objectives
	•	Resolution requirement (coarse/medium/fine)
	•	Whether Designers are allowed or only evaluators (full search vs eval-only vs seeded search)
	•	Outputs a structured ProblemSpec document.

⸻

2. WorldModeller (MVP)

Responsible for producing a usable world model, not a complete one.

Capabilities:
	•	Build a domain model from ProblemSpec alone (textual).
	•	Identify actors, mechanisms, resources, limits.
	•	Encode model assumptions and simplifications.
	•	Produce a structured output (e.g., typed graph, but MVP can be nested JSON).

No external research in MVP.
All knowledge comes from model priors + prompt context.

⸻

3. Designers (MVP)
	•	Generate initial solution candidates using only the world model.
	•	Each candidate includes:
	•	Mechanism description
	•	Expected effects on actors/resources
	•	Constraint compliance estimates
	•	Designers produce multiple, diverse candidates.

⸻

4. ScenarioGenerator
	•	Builds a minimal suite of test scenarios that:
	•	Probe critical mechanisms
	•	Attempt to break fragile assumptions
	•	Stress constraints (esp. high-weight ones)

MVP: purely synthetic scenarios derived from world model.

⸻

5. Evaluators
	•	Run scenario analyses in language (no code execution in MVP).
	•	Evaluate each candidate along:
	•	P: prediction consistency across scenarios
	•	R: resource/complexity cost inferred from world model
	•	Constraint satisfaction (weighted)
	•	Output structured scores + an explanation.

⸻

6. I-Ranker
	•	Compute final ranking:
	•	For each candidate:
I_score = P_score / R_score
	•	Includes constraint-weighted report.
	•	Flags candidates that violate 100-weight ("hard") constraints.

⸻

7. Provenance Tracker

Tracks:
	•	Candidate lineage (parent_ids)
	•	Origin (user/system)
	•	Transformations (refinements, rejections, revivals)

MVP: a simple record list attached to each candidate object.

⸻

III. MVP Workflows

A. Full Search Mode
	1.	User inputs problem.
	2.	ProblemSpec agent structures it.
	3.	WorldModeller creates initial world model.
	4.	Designers create candidate solutions.
	5.	ScenarioGenerator makes tests.
	6.	Evaluators score them.
	7.	Ranker orders them.
	8.	Output: ranked list + explanations + provenance.

⸻

B. Eval-Only Mode
	1.	User supplies existing ideas.
	2.	Intake agent converts them to candidates.
	3.	No designer phase.
	4.	Evaluators score.
	5.	Ranker outputs ordering.

⸻

IV. MVP Data Structures

A. Constraint

{
  "name": "...",
  "description": "...",
  "weight": 0-100
}

B. Candidate

{
  "id": "...",
  "parents": [...],
  "origin": "user|system",
  "mechanism": "...",
  "predicted_effects": "...",
  "scores": { "P": ..., "R": ..., "constraint_satisfaction": {...} },
  "provenance_log": [...]
}

C. WorldModel

Flexible JSON:
	•	actors
	•	mechanisms
	•	constraints
	•	assumptions
	•	simplifications

⸻

V. MVP Non-Goals
	•	No code execution (no real experiments)
	•	No external research APIs
	•	No long-horizon orchestration
	•	No self-improvement cycles
	•	No high-fidelity simulations

⸻

VI. Roadmap Beyond MVP

Phase 2: Research-Enhanced World Models
	•	Integrate research APIs (web search, legal corpora, academic sources).
	•	Attach sources to world-model nodes.
	•	Automatic resolution selection via I=P/R.

Phase 3: Real Scenario Execution
	•	Execute code, simulations, legal queries, or math computations.

Phase 4: WorldModel & Candidate Evolution Loops
	•	Designers challenge world-model assumptions.
	•	Kickback loops improve the model.

Phase 5: Self-Evaluation & Self-Improvement
	•	Meta-agent analyzes logs.
	•	Suggests:
	•	new agent types
	•	improved workflows
	•	changes to model-schema
	•	I=P/R inefficiencies

⸻

VII. Final Objective

A fully general reasoning engine that constructs world models, debates candidate solutions, stress-tests them, refines them, and ranks them using an explicit intelligence metric.

⸻
