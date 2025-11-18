# Story: Add test tooling and fix run execution issues

**Status**: To Do

---

## Related Requirement
- See `docs/requirements.md`:
  - **MVP Criteria** – enabling iterative use on Int Crucible itself.
  - The system should be reliable and debuggable.

## Alignment with Design
- See `docs/design.md`:
  - **Feature: Run-Time Views, Candidate Board, and Post-Run Exploration** – runs should execute reliably and provide clear feedback.
  - The system should support debugging and troubleshooting when runs fail.

## Problem Statement
During end-to-end testing, several issues were discovered:

1. **Run Execution Failures**: 
   - Runs fail with "ProblemSpec or WorldModel not found" errors even when these entities exist in the database
   - The error occurs in `RunService.execute_full_pipeline()` at lines 345-351 where it checks for prerequisites
   - This suggests either:
     - A database session/transaction isolation issue (entities not visible in current session)
     - Incorrect error handling or exception propagation
     - A race condition if entities are being created concurrently
   - **Root Cause Investigation Needed**: Check if `get_problem_spec()` and `get_world_model()` are using the correct session, if session needs refresh, or if there's a commit/transaction boundary issue

2. **Lack of Test Tooling**: There's no interactive tooling to:
   - Run full pipeline tests with detailed instrumentation
   - Debug why runs fail (what step failed, what error occurred)
   - Monitor pipeline execution in real-time
   - Inspect intermediate states (candidates generated, scenarios created, evaluations completed)
   - Verify that all pipeline phases completed successfully
   - Test with different project states (with/without ProblemSpec, with/without WorldModel)

3. **Poor Error Visibility**: When runs fail, it's unclear:
   - Which phase failed (design, scenario generation, evaluation, ranking)
   - What the actual error was (full stack trace, context)
   - What data was successfully created before the failure
   - How to reproduce or debug the issue
   - Whether the error is transient or persistent

4. **Incomplete Status Reporting**: 
   - Run status may show "failed" even when some phases completed successfully (e.g., candidates were generated and ranked, but status still shows failed)
   - No granular status tracking (which phases completed, which failed)
   - No intermediate status updates during long-running pipelines

## Acceptance Criteria
- **Test Tooling**:
  - A CLI command or script exists to run full pipeline tests with detailed output
  - The tooling provides step-by-step progress reporting
  - Each phase (design, scenario generation, evaluation, ranking) reports success/failure clearly
  - Intermediate results are logged/inspected (e.g., "Generated 5 candidates", "Created 8 scenarios")
  - Errors are captured with full stack traces and context
  - The tooling can verify that all expected entities were created (candidates, scenarios, evaluations)
- **Run Execution Fixes**:
  - Run service correctly checks for ProblemSpec and WorldModel existence
  - No race conditions when checking prerequisites
  - Clear error messages when prerequisites are missing
  - Run status accurately reflects completion state (not "failed" when candidates were successfully ranked)
  - Partial completion is handled gracefully (if design succeeds but evaluation fails, status reflects this)
- **Instrumentation**:
  - Each pipeline phase logs its start, progress, and completion
  - Timing information for each phase
  - Resource usage tracking (if applicable)
  - Clear indication of which phase is currently executing
- **Error Handling**:
  - Errors include context (which phase, which project/run, what data was available)
  - Errors are logged with sufficient detail for debugging
  - Partial results are preserved even when pipeline fails partway through
- **Verification**:
  - The tooling can verify a successful run by checking:
    - Run status is "completed"
    - Expected number of candidates exist
    - Expected number of scenarios exist
    - Evaluations exist for all candidate/scenario pairs
    - Rankings were computed
    - All entities have proper relationships (candidates linked to run, evaluations linked to candidates, etc.)

## Tasks
- [ ] Investigate and fix run execution issues:
  - [ ] **Debug the "not found" error**:
    - [ ] Add detailed logging to `execute_full_pipeline()` to log project_id, run_id, and what was found/not found
    - [ ] Verify database session is correct (check if `get_session()` context manager is working properly)
    - [ ] Check if entities need to be refreshed or if query needs explicit commit/flush
    - [ ] Test with CLI queries to verify entities exist: `crucible get-problem-spec <project_id>` and `crucible get-world-model <project_id>`
    - [ ] Add session refresh or explicit query with `session.query().filter().first()` to ensure we're seeing committed data
    - [ ] Consider adding retry logic or better error messages that show what was actually found
  - [ ] **Fix error handling**:
    - [ ] Ensure exceptions are properly caught and logged with full context
    - [ ] Add validation that provides clear error messages (e.g., "ProblemSpec not found for project X. Available projects: Y, Z")
    - [ ] Ensure ValueError exceptions from prerequisite checks are properly handled
  - [ ] **Fix run status reporting**:
    - [ ] Ensure "completed" status is set correctly when pipeline succeeds
    - [ ] Ensure "failed" status is only set when pipeline actually fails (not when some phases succeed)
    - [ ] Add partial completion tracking (e.g., "design_completed", "scenario_completed", etc.)
  - [ ] **Test fixes**:
    - [ ] Test with the E2E test project that previously failed
    - [ ] Test with fresh project (create ProblemSpec and WorldModel via chat, then run pipeline)
    - [ ] Test error cases (missing ProblemSpec, missing WorldModel) to ensure proper error messages
- [ ] Create test tooling CLI command:
  - [ ] Add `crucible test-run` command to CLI
  - [ ] Command accepts project_id (or creates test project)
  - [ ] Command runs full pipeline with detailed progress reporting
  - [ ] Command verifies all expected entities were created
  - [ ] Command reports success/failure with clear summary
- [ ] Add instrumentation to pipeline phases:
  - [ ] Add logging at start/end of each phase (design, scenario, evaluate, rank)
  - [ ] Log timing information for each phase
  - [ ] Log counts of entities created (candidates, scenarios, evaluations)
  - [ ] Log any warnings or non-fatal issues
- [ ] Add run status tracking improvements:
  - [ ] Track which phases have completed
  - [ ] Set intermediate statuses (e.g., "designing", "evaluating", "ranking")
  - [ ] Only set "completed" when all phases succeed
  - [ ] Set "failed" with clear indication of which phase failed
- [ ] Add verification utilities:
  - [ ] Function to verify run completeness (all expected entities exist)
  - [ ] Function to check data integrity (relationships are correct)
  - [ ] Function to report run statistics (candidate count, scenario count, evaluation count, etc.)
- [ ] Update API to expose run progress:
  - [ ] Add endpoint to get detailed run status (which phases completed, current phase, etc.)
  - [ ] Add endpoint to get run statistics (entity counts, timing, etc.)
- [ ] Add tests:
  - [ ] Test successful full pipeline run
  - [ ] Test pipeline with missing prerequisites (should fail gracefully)
  - [ ] Test partial completion handling
  - [ ] Test verification utilities
- [ ] Document test tooling usage:
  - [ ] Add to CLI help text
  - [ ] Add examples to README or docs
- [ ] User must sign off on functionality before story can be marked complete.

## Notes
- **Prerequisite**: This builds on existing run execution infrastructure from stories 005 and 006.
- **Issues to Fix** (from E2E test):
  1. Run service incorrectly reports "ProblemSpec or WorldModel not found" when they exist
  2. Run status shows "failed" even when candidates were generated and ranked successfully
  3. Need better visibility into what's happening during pipeline execution
- **Design Approach**:
  - Test tooling should be developer-friendly and provide detailed output
  - Instrumentation should not significantly impact performance
  - Error handling should preserve partial results for debugging
  - Status tracking should be granular enough to show progress
- **Future Enhancements**:
  - Web UI for monitoring run progress in real-time
  - Run replay/debugging interface
  - Performance profiling and optimization recommendations
  - Automated test suite that runs on every commit

## Work Log

### 20250118-XXXX — Story creation
- **Result:** Created story 008b for test tooling and run execution fixes
- **Issues Identified from E2E Test:**
  1. Run fails with "ProblemSpec or WorldModel not found" error even when they exist
  2. Run status shows "failed" but candidates were successfully generated and ranked
  3. No visibility into pipeline execution progress or which phase failed
  4. No tooling for interactive testing and debugging
- **Next:** Begin investigation of run service error handling

