# Scratchpad - Planning Phase

@scratchpad.md already exists and is your external memory. Use it to help you stay on track.

**Current Phase**: Planning

**Planning Phase Tasks**
- [ ] Create design document:
  - [ ] Use `/docs/templates/design-template.md` to create `/docs/design.md`
  - [ ] Discuss imagined workflow with user to get a sense of it. They may have no idea and you can make suggestions, but record the final agreed upon workflow within the design document.
  - [ ] Ensure alignment with requirements
  - [ ] Include UI/UX considerations if applicable
  - [ ] Document key design decisions
- [ ] Create architecture document:
  - [ ] Use `/docs/templates/architecture-template.md` to create `/docs/architecture.md`
  - [ ] Define system components and their interactions
  - [ ] Specify technologies and frameworks
  - [ ] Document architectural decisions and trade-offs
- [ ] Extract and move content from the "Non-Requirements Detail" section of `requirements.md`:
  - [ ] Review `/docs/requirements.md` for implementation details
  - [ ] Move relevant details to the appropriate design or architecture document
  - [ ] Remove the section from requirements.md after ensuring all details are captured
- [ ] Create user stories:
  - [ ] Use `/docs/templates/stories-template.md` to create `/docs/stories.md`
  - [ ] Break down requirements into implementable stories
  - [ ] Prioritize stories based on dependencies and importance
  - [ ] Ensure everything from `docs/requirements.md`, `docs/design.md`, and `docs/architecture.md` is covered by a story
  - [ ] Add a task item in this document for each story added to stories.md
- [ ] For each user story:
  - [ ] Use `/docs/templates/story-template.md` to create individual story files (e.g., `/docs/stories/story-001.md`), pulling from the `docs/requirements.md`, `docs/design.md`, and `docs/architecture.md` for details
  - [ ] Ensure each story has clear acceptance criteria
  - [ ] Link stories to requirements and design documents
  - [ ] For each user story, validate the contents against the `docs/requirements.md`, `docs/design.md`, and `docs/architecture.md` documents to ensure all requirements are covered, the story isn't inventing requirements, and the story makes sense.
  - [ ] Check in what we have so far to github (if the project is using github).


**Transition to Next Phase**
- When all planning tasks are complete, ask the user: "Are you ready to move to the Project Setup phase?"
- If yes, run: `./bootstrapping/scripts/transition_to_execute.sh programming project-setup`
  - This will copy all files to the correct places to start the Project Setup phase

**User Input**  
- 2025-11-20: User insists chat-first project creation use the existing real-time streaming pipeline end-to-end; no snap-in updates.
- 2025-11-20: UX feedback – spec panel must populate immediately with highlights; Architect must speak in future tense, and project names/descriptions must be inferred.
- 2025-11-20: Latest request – analyze entire streaming/rendering pipeline (frontend + backend) and rebuild if needed to ensure incremental updates stream correctly in the UI.
- 2025-11-20: Follow-up tweaks – keep the initial user message visible when the project view loads, have the Architect follow up with next steps after updates finish, and add padding around the resolution label in the spec panel.
- 2025-11-20: Clarification-only questions (e.g., “What is a world model?”) should not mutate the ProblemSpec/WorldModel unless the user explicitly asks for changes; apply heuristics (keyword combos, send data) to bias toward descriptive answers only.
- 2025-11-21: User invoked `/build-story` for Story 016 (Run advisor contract) to continue planning work.
- 2025-11-21: User approved continuing Story 016 planning (“go ahead”).
- 2025-11-21: User reiterated “go ahead” confirming we should keep expanding Story 016 planning.
- 2025-11-21: User requested decomposition of Story 016 (“Go ahead with the decompose”).
- 2025-11-21: User asked to proceed with the “next logical move steps” for Story 016.
- 2025-11-21: User instructed to start Phase 1 execution and continue working without stopping.
- 2025-11-21: User directed us to spin up the servers and perform QA end-to-end without pausing.
- 2025-11-21: User invoked `/build-story` for Story 008 (provenance + lineage) and asked us to review/improve its plan before implementation.

**Quick Start Assumptions**  
- [If quick start is used, list assumptions made, e.g., "Assumed minimal UI based on requirements."]

**Issues or Blockers**  
- [Note anything preventing progress]

**Decisions Made**
- [Log important decisions here]
- 2025-11-21: Added Story 017 (Candidate ranking explanations in UI, Medium priority) and Story 019 (Operational observability and cost dashboards, Medium priority) to `docs/stories.md`. Reserved Story 018 for an AI-first test pipeline and snapshot-based scenarios.