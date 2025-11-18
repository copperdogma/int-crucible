# Int Crucible

A general multi-agent reasoning system built on world-model construction, candidate generation, stress-testing, and the intelligence metric I = P / R.

⸻

Overview

Int Crucible is a domain-agnostic reasoning engine.
It builds structured world models, generates solution candidates, stress-tests them with scenario suites, evaluates them through constraint-weighted scoring, and ranks them using the intelligence metric:

Intelligence = Prediction / Resources   (I = P / R)

Unlike research-only systems, Int Crucible is built for any domain:
	•	policy / constitutions
	•	engineering
	•	algorithms
	•	system design
	•	theoretical reasoning
	•	creative or conceptual exploration

The system is fully modular, transparent, and designed for multi-turn refinement, lineage tracking, and human feedback.

⸻

High-Level Architecture

Int Crucible uses a multi-agent pipeline:
	1.	ProblemSpec Agent
Parses user intent into constraints (with weights), goals, and required resolution.
	2.	WorldModeller
Builds a structured world model at appropriate fidelity.
Later versions may include research and knowledge-graph enrichment.
	3.	Designers
Generate diverse solution candidates from the world model.
	4.	ScenarioGenerator
Produces synthetic test cases that probe fragile assumptions and constraint boundaries.
	5.	Evaluators
Run scenario reasoning, compute P (prediction quality), R (resource/complexity cost), and constraint satisfaction.
	6.	I-Ranker
Computes I = P / R, applies weighted constraints, and produces a ranked candidate list.
	7.	Provenance Tracker
Maintains lineage, parentage, origin tags, and full transformation history.
	8.	FeedbackAgent
Allows human users to flag issues, diagnose model errors or missing constraints, and trigger selective re-runs.

The system is designed to become self-improving through pipeline-level introspection (future phase).

⸻

Repository Layout

The repo is structured to allow incremental development and clean isolation between Crucible components and external dependencies:

/core/               # Crucible agents (ProblemSpec, Modeller, Designers, Evaluators, Ranker)
/world_model/        # World model schema, nodes, templates
/design/             # Candidate-generation logic
/evaluation/         # Scenario generation, test runners, scoring
/ui/                 # Optional UI or CLI wrappers
/meta/               # System-level evaluation, logs, self-improvement
/vendor/kosmos/      # Kosmos code imported via git subtree (infrastructure only)

The Kosmos subtree provides long-horizon orchestration, knowledge-graph tooling, and sandbox execution, but all science-specific agents and pipelines will be replaced or removed.

⸻

Setup

This project uses the Cursor Project Bootstrapper:
https://github.com/copperdogma/cursor-project-bootstrapper

After cloning:

./bootstrap.sh

Then add the Kosmos subtree:

git remote add kosmos https://github.com/jimmc414/Kosmos.git
git subtree add --prefix=vendor/kosmos kosmos main --squash

Run the Kosmos examples to ensure the environment is functional.

⸻

Development Goals (MVP → Advanced)

MVP
	•	Structured ProblemSpec → WorldModel → Designers → Evaluators → Ranking
	•	No external research; world models built from prompt context
	•	Synthetic scenario generation
	•	Lineage tracking for all candidates
	•	Eval-only mode for user-supplied ideas
	•	Seeded search mode for refining user ideas

Phase 2
	•	Research-enhanced world models (web, corpora, APIs)
	•	World model stored in a typed knowledge graph
	•	Real simulation/test execution where applicable

Phase 3
	•	Designer ↔ Modeller kickback loops (challenge assumptions)
	•	Scenario test suite inheritance across runs
	•	High-resolution constraint modeling
	•	Implementer modeling (actors + hard constraints)

Phase 4
	•	SystemEvaluator agent analyzes logs and proposes pipeline improvements
	•	Self-refining world model schemas
	•	Multi-run architecture evolution guided by I=P/R at system level

⸻

Why “Int Crucible”?

A crucible is a vessel for refining raw material under heat and stress.
This system does the same for ideas:
generate → test → break → refine → converge.

The “Int” prefix nods both to intelligence and to the INT ability score from D&D—appropriate for a system whose core metric is I=P/R.

⸻

Status

Early development.
Architecture is complete; infrastructure integration and agent implementations are under construction.

⸻

License

To be determined.