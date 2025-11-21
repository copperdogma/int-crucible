# Project Stories

Int Crucible

**Note**: This document serves as an index for all story files in `/docs/stories/`, tracking their progress and status.

---

## Suggested Implementation Order (Remaining Stories)
1. DONE:**016 – Run advisor contract and explicit execution control**: Lock down how runs are authorized to avoid hidden/accidental costs before adding more automation and testing.
2. DONE:**008 – Provenance and candidate lineage**: Ensure every candidate and model change is traceable so debugging and feedback have a solid backbone.
3. DONE:**019 – Operational observability and cost dashboards**: Add run-level metrics and health visibility so both you and AI can see what the pipeline is doing in practice.
4. DONE:**018 – AI-first test pipeline and snapshot-based scenarios**: Build the AI-facing test harness on top of provenance + observability so snapshots and invariants are cheap and reliable.
5. DONE:**010 – Multiple chats and runs per project**: Turn projects into persistent reasoning environments once core runs, provenance, and tests are stable.
6. DONE:**020 – Fix SQLAlchemy metadata cache issue**: Resolve database schema sync problem blocking Run History feature. (Technical Debt - High Priority)
7. **009 – Feedback loop and issue handling**: Layer feedback and partial reruns on top of a well-observed, provenance-rich pipeline.
8. **017 – Candidate ranking explanations in UI**: Refine UX/interpretability of rankings after the core behavior and testing surface are in place.

## Story List
| Story ID | Title                                             | Priority | Status   | Link                                                     |
|----------|---------------------------------------------------|----------|----------|----------------------------------------------------------|
| 001      | Bootstrap Kosmos-backed backend environment       | High     | Done     | /docs/stories/story-001-bootstrap-kosmos-backend.md     |
| 002      | Define and persist Int Crucible domain schema     | High     | Done     | /docs/stories/story-002-domain-schema-and-storage.md    |
| 002b     | Establish verification pipeline for all work      | High     | Done     | /docs/stories/story-002b-verification-pipeline.md       |
| 003      | Implement ProblemSpec modelling flow              | High     | Done     | /docs/stories/story-003-problemspec-agent-and-flow.md   |
| 004      | Implement WorldModeller and world-model view      | High     | Done     | /docs/stories/story-004-worldmodeller-and-spec-view.md  |
| 005      | Implement Designers and ScenarioGenerator         | High     | Done     | /docs/stories/story-005-designers-and-scenarios.md      |
| 006      | Implement Evaluators and I-Ranker                 | High     | Done     | /docs/stories/story-006-evaluators-and-i-ranker.md      |
| 007      | Build minimal chat-first web UI                   | High     | Done     | /docs/stories/story-007-chat-first-ui.md                |
| 007b     | Implement interactive guidance and onboarding agent | High   | Done     | /docs/stories/story-007b-interactive-guidance-agent.md  |
| 008      | Implement provenance and candidate lineage        | Medium   | Done    | /docs/stories/story-008-provenance-and-lineage.md       |
| 008b     | Add test tooling and fix run execution issues     | High     | Done     | /docs/stories/story-008b-test-tooling-and-run-fixes.md  |
| 009      | Implement feedback loop and issue handling        | Medium   | To Do    | /docs/stories/story-009-feedback-and-issues.md          |
| 010      | Support multiple chats and runs per project       | Medium   | Done     | /docs/stories/story-010-multi-chat-and-run-history.md   |
| 011      | Native LLM function calling for Architect persona (Guidance) | High | Done | /docs/stories/story-011-native-llm-function-calling-for-guidance.md |
| 012      | Architect-led conversational loop and full interaction logging | High | Done | /docs/stories/story-012-architect-chat-loop-and-logging.md |
| 013      | Spec/world-model deltas and live highlighting     | High     | Done     | /docs/stories/story-013-spec-deltas-and-highlighting.md |
| 014      | Streaming architect responses and typing indicators | High   | Done     | /docs/stories/story-014-streaming-and-typing-indicators.md |
| 015      | Chat-first project creation and selection         | High     | Done     | /docs/stories/story-015-chat-first-project-creation.md  |
| 016      | Run advisor contract and explicit execution control | High   | Done    | /docs/stories/story-016-run-advisor-contract.md         |
| 017      | Candidate ranking explanations in UI              | Medium   | To Do    | /docs/stories/story-017-candidate-ranking-explanations.md |
| 018      | AI-first test pipeline and snapshot-based scenarios | Medium | Done    | /docs/stories/story-018-ai-first-test-pipeline.md       |
| 019      | Operational observability and cost dashboards     | Medium   | Done    | /docs/stories/story-019-operational-observability-and-cost-dashboards.md |
| 020      | Fix SQLAlchemy metadata cache issue for chat_session_id | Medium | Done | /docs/stories/story-020-sqlalchemy-metadata-cache-fix.md |

## Notes
- Initial stories are derived from the high-level epics in `docs/temp-story-map.md` and aligned with `docs/requirements.md`, `docs/design.md`, and `docs/architecture.md`. Additional stories can be added as the design evolves.