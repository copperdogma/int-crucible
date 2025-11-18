Document 3 — High-Level Story Map (Assuming We Use Kosmos as Base)

Created via congo with GPT5.1: https://chatgpt.com/share/691bb29e-79c4-800a-8efb-e941fe8b24c8

This is a very high-level guide to the implementation stories (epic → stories).

⸻

Epic 1 — Environment Bootstrap

Story 1.1 — Clone Kosmos Repo & Run Locally
	•	Clone jimmc414/Kosmos
	•	Install deps
	•	Run the example pipelines
	•	Verify:
	•	LLM access
	•	Knowledge graph ready
	•	Jupyter sandbox operational

Story 1.2 — Create Int Crucible Repo Structure
	•	New repo
	•	Subfolders:
	•	core/ (agents)
	•	world_model/
	•	design/
	•	evaluation/
	•	ui/
	•	meta/
	•	Add build instructions

⸻

Epic 2 — Replace Scientific WorldModel with Crucible WorldModel

Story 2.1 — Define WorldModel Schema
	•	actors
	•	constraints
	•	mechanisms
	•	assumptions
	•	scenarios
	•	lineage

Story 2.2 — Implement WorldModeller Agent
	•	Replaces literature analyzer
	•	Writes nodes to graph
	•	Outputs simplified world model

⸻

Epic 3 — Introduce Core Crucible Agents

Story 3.1 — ProblemSpec Agent
	•	Parse user input to constraints, goals, resolution.

Story 3.2 — Designer Agents
	•	Generate candidate solutions using world model graph.

Story 3.3 — ScenarioGenerator
	•	Convert world model to scenario suite.

Story 3.4 — Evaluator Agent
	•	Run scenario tests in notebook sandbox
	•	Insert results into world graph.

Story 3.5 — I-Ranker
	•	Compute P, R
	•	Compute weighted constraint satisfaction
	•	Rank candidates
	•	Produce summary

⸻

Epic 4 — Provenance & Lineage

Story 4.1 — Candidate Lineage Tracking
	•	parent_ids
	•	origin
	•	history events

Story 4.2 — UI Concept: Lineage Graph
	•	simple textual + graph view of candidate evolution.

⸻

Epic 5 — Feedback & Interactive Correction

Story 5.1 — FeedbackAgent
	•	asks user clarifying questions
	•	identifies model flaw vs constraint vs evaluator misstep
	•	produces Issue objects

Story 5.2 — Orchestrator Fix Handling
	•	apply patches
	•	determine whether re-run is needed
	•	re-execute agents from appropriate stage

⸻

Epic 6 — System Evaluation & Self-Improvement (Later)

Story 6.1 — SystemEvaluator Agent
	•	analyze logs for:
	•	bottlenecks
	•	model resolution issues
	•	redundant cycles
	•	output structured improvement suggestions.

Story 6.2 — Meta-cycle Runner
	•	perform self-run
	•	evaluate changes
	•	integrate improvements
	•	produce next version of Int Crucible pipeline

⸻
