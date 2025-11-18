Imagined Workflow & UX for Int Crucible

I want Int Crucible to feel like a chat-first modelling and reasoning environment, with persistent project state and a few structured views around that.

1. Project + chat as the main entry point
	•	I create a project (e.g., “Design a rights-respecting incarceration system” or “Find a better algorithmic approach for X”).
	•	The primary interaction is a chat:
	•	I describe what I’m after in natural language.
	•	An AI “Architect” agent asks targeted questions to clarify:
	•	goals,
	•	constraints (with weights),
	•	actors/implementers,
	•	how much detail I care about (resolution).
	•	As we talk, it incrementally builds a ProblemSpec and an initial WorldModel.

2. Live spec / world-model view
Alongside the chat, I want a live, human-readable document that the system keeps updating:
	•	Sections like:
	•	Objectives
	•	Constraints (with weights)
	•	Actors / Implementers
	•	Assumptions and simplifications
	•	Under the hood, this maps to a structured format (JSON / graph).
	•	Ideally a two-panel view:
	•	Left: a Markdown-style spec (“spec.md”).
	•	Right: the internal structured representation.
	•	I should be able to edit either side and see the other update, so I can inspect and correct how my words are being formalized.

There should be a clear sense of being in a “modelling/setup” phase: no runs happen until we explicitly decide the spec is “good enough to try”.

3. Run configuration
Once the spec and world-model feel right, I want to configure and launch a run:
	•	Choose mode:
	•	Full search (system generates candidates from scratch)
	•	Eval-only (I supply 1+ existing ideas, it just evaluates and ranks them)
	•	Seeded search (I supply ideas that can be mutated/refined)
	•	Choose a budget / depth level:
	•	Simple slider: “fast & cheap” ↔ “deep & expensive”
	•	Optionally toggle capabilities (in later versions):
	•	e.g., “use external research” vs “stay within current knowledge”.

The system can propose default parameters based on the problem; I can accept or tweak them, then hit Run.

4. Run-time views: pipeline + candidates + issues
While a run is executing, I want a few key views:
	•	Pipeline view
	•	Shows the stages: World modelling → Design → Evaluation → Ranking.
	•	For each stage: is it running, done, or waiting.
	•	Counters: how many candidates created, under test, rejected, etc.
	•	Candidate board
	•	Cards representing candidates, grouped by status, e.g.:
	•	New
	•	Under test
	•	Promising
	•	Weak
	•	Rejected
	•	Each card shows:
	•	a short name/summary,
	•	some quick indicators (e.g. relative P, R, constraint warnings).
	•	Issues / warnings panel
	•	Model issues (e.g., conflicting assumptions)
	•	Constraint issues (e.g., a high-weight constraint is systematically bent)
	•	Evaluation/test issues (e.g., scenario suite too weak, or lots of uninformative tests)

A rough progress indicator is useful (e.g. “cycle N of M, stages completed”), but I don’t need precise timing, just a sense of where we are.

5. Post-run exploration and conversation
After a run finishes, I want:
	•	A ranked list of final candidates with:
	•	high-level description,
	•	P/R characterization,
	•	constraint satisfaction summary,
	•	and provenance (where the idea came from, what it evolved from).
	•	For each candidate, I want to be able to:
	•	Open a detail view:
	•	mechanism description,
	•	scenario results,
	•	constraint breakdown,
	•	lineage (which earlier ideas and decisions it came from).
	•	Click “Discuss this candidate” to start a focused chat:
	•	That chat has the ProblemSpec, relevant parts of the WorldModel, and this candidate preloaded as context.
	•	I can ask “what if” questions, challenge parts of the design, or propose tweaks.
	•	The system can, if I choose, spin those discussions into new runs (e.g. “start a seeded search using this as a parent”).

I may also have eval-only runs where the output is simply: “Here are the 6 ideas you provided, ranked with reasoning; no new ideas generated.”

6. Human feedback loop on model and constraints
If I spot something obviously wrong—either in the world-model, a candidate, or the way constraints were applied—I want a simple way to flag it:
	•	e.g., “This assumption is just wrong for my domain” or “We’re missing an important constraint here.”
	•	This should trigger a Feedback agent that:
	•	asks a few clarifying questions,
	•	classifies the issue (model / constraint / evaluator / scenarios),
	•	and proposes an action:
	•	small patch and re-score,
	•	update constraints and partially rerun,
	•	or (in rare cases) restart from a revised world-model.

I should be able to choose whether the issue is:
	•	minor (note it but keep current results),
	•	important (update and re-run some parts),
	•	or catastrophic (invalidate affected candidates and rerun properly).

7. Multiple chats per project
Finally, I want to be able to have multiple chat sessions tied to the same project:
	•	Each project keeps:
	•	its spec,
	•	its evolving world-model,
	•	and its run history.
	•	Different chats can:
	•	examine different runs or candidates,
	•	explore different “what-if” branches,
	•	or represent different modes (setup vs analysis).
	•	Under the hood, all chats share the same core project state, but each chat can request new runs or modifications.
