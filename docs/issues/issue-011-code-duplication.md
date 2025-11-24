# Issue 011: Code duplication in IssueService remediation methods (80%+ duplicate)

**Status**: Open
**Priority**: High
**Category**: Tech Debt
**Discovered**: 2025-11-24
**Related Story**: (TBD)

## Description
The `IssueService` class has three remediation methods with 80%+ duplicated code for patching ProblemSpec and WorldModel. This creates maintenance burden and high risk of inconsistent bug fixes.

## Current Behavior

### Duplicated Code Blocks
```python
# crucible/services/issue_service.py (799 lines)

# Lines 296-345: apply_patch_and_rescore - ProblemSpec patching
# Lines 347-402: apply_patch_and_rescore - WorldModel patching

# Lines 475-511: apply_partial_rerun - ProblemSpec patching (DUPLICATE)
# Lines 514-559: apply_partial_rerun - WorldModel patching (DUPLICATE)

# Lines 626-639: apply_full_rerun - ProblemSpec patching (PARTIAL DUPLICATE)
# Lines 641-657: apply_full_rerun - WorldModel patching (PARTIAL DUPLICATE)
```

### Duplication Analysis
- **ProblemSpec patching logic**: ~50 lines × 3 methods = 150 lines of duplication
- **WorldModel patching logic**: ~55 lines × 3 methods = 165 lines of duplication
- **Total duplication**: ~315 lines out of 799 (40% of file is duplicated code!)

## Impact

### Maintenance Burden
```python
# If we need to fix a bug in ProblemSpec patching:
def apply_patch_and_rescore(...):
    # Fix bug here
    if "problem_spec" in patch_data and problem_spec:
        updates = patch_data["problem_spec"]
        # ... 50 lines of logic ...

def apply_partial_rerun(...):
    # ❌ Must remember to fix bug here too!
    if "problem_spec" in patch_data and problem_spec:
        updates = patch_data["problem_spec"]
        # ... SAME 50 lines of logic ...

def apply_full_rerun(...):
    # ❌ Must remember to fix bug here too!
    if "problem_spec" in patch_data:
        # ... SIMILAR logic but slightly different ...
```

### Bug Multiplication
When AI (or human) fixes a bug in one method, they must:
1. Identify all other locations with same logic
2. Apply identical fix to all locations
3. Test all locations

**Failure modes:**
- Fix applied to 1 method but not others → inconsistent behavior
- Fix applied differently to each method → divergent behavior
- Tests only cover one method → bugs hide in others

### Testing Overhead
Must write nearly identical tests 3 times:
```python
def test_apply_patch_and_rescore_problem_spec():
    # Test ProblemSpec patching logic

def test_apply_partial_rerun_problem_spec():
    # ❌ Same test, duplicated

def test_apply_full_rerun_problem_spec():
    # ❌ Same test, duplicated
```

## Investigation Notes

### Root Cause
Methods were likely copied and modified rather than extracting shared logic. This is common in rapid prototyping but should be refactored.

### Affected Methods
1. `apply_patch_and_rescore()` - Lines 269-445 (177 lines)
2. `apply_partial_rerun()` - Lines 447-599 (153 lines)
3. `apply_full_rerun()` - Lines 601-722 (122 lines)

### Shared Logic
All three methods perform:
1. **Validate issue exists**
2. **Apply ProblemSpec patches** (if provided)
   - Get current spec
   - Merge updates with existing data
   - Update database
   - Record provenance
3. **Apply WorldModel patches** (if provided)
   - Get current model
   - Deep merge updates
   - Update database
   - Record provenance in model_data
4. **Execute action** (different per method)
   - patch_and_rescore → run evaluate + rank
   - partial_rerun → run evaluate + rank (same!)
   - full_rerun → create new run + execute full pipeline
5. **Mark issue resolved**

### Key Differences
- `apply_full_rerun`: Creates new run instead of reusing existing
- Others: Use same issue.run_id

## Proposed Solution

### Extract Shared Logic

```python
# crucible/services/issue_service.py (refactored)

class IssueService:
    """Service for issue management and remediation."""

    def __init__(self, session: Session):
        self.session = session
        self.run_service = RunService(session)
        self.patch_service = PatchService(session)  # New helper

    def _apply_problem_spec_patch(
        self,
        project_id: str,
        patch_data: Dict[str, Any],
        issue_id: str,
        action: str
    ) -> bool:
        """
        Shared logic for patching ProblemSpec.

        Returns:
            True if patch was applied, False otherwise
        """
        problem_spec = get_problem_spec(self.session, project_id)
        if "problem_spec" not in patch_data or not problem_spec:
            return False

        updates = patch_data["problem_spec"]

        # Get current values
        current_constraints = problem_spec.constraints or []
        current_goals = problem_spec.goals or []
        current_resolution = (
            problem_spec.resolution.value
            if hasattr(problem_spec.resolution, "value")
            else str(problem_spec.resolution)
        )
        current_mode = (
            problem_spec.mode.value
            if hasattr(problem_spec.mode, "value")
            else str(problem_spec.mode)
        )

        # Apply updates
        new_constraints = updates.get("constraints", current_constraints)
        new_goals = updates.get("goals", current_goals)
        new_resolution = updates.get("resolution", current_resolution)
        new_mode = updates.get("mode", current_mode)

        # Update ProblemSpec
        updated_spec = update_problem_spec(
            self.session,
            project_id=project_id,
            constraints=new_constraints,
            goals=new_goals,
            resolution=new_resolution,
            mode=new_mode
        )

        if updated_spec:
            # Record provenance
            provenance_entry = build_provenance_entry(
                event_type="feedback_patch",
                actor="system",
                source=f"issue_service:{action}",
                description=f"ProblemSpec patched due to issue {issue_id}",
                reference_ids=[issue_id, project_id],
                metadata={"patch_type": "problem_spec", "updates": updates},
            )
            if updated_spec.provenance_log is None:
                updated_spec.provenance_log = []
            updated_spec.provenance_log.append(provenance_entry)
            self.session.commit()
            return True

        return False

    def _apply_world_model_patch(
        self,
        project_id: str,
        patch_data: Dict[str, Any],
        issue_id: str,
        action: str
    ) -> bool:
        """
        Shared logic for patching WorldModel.

        Returns:
            True if patch was applied, False otherwise
        """
        world_model = get_world_model(self.session, project_id)
        if "world_model" not in patch_data or not world_model:
            return False

        updates = patch_data["world_model"]

        # Merge updates with existing model_data
        current_model_data = world_model.model_data or {}
        if not isinstance(current_model_data, dict):
            current_model_data = {}

        # Deep merge
        new_model_data = current_model_data.copy()
        for key, value in updates.items():
            if key == "provenance":
                # Preserve existing provenance
                if "provenance" not in new_model_data:
                    new_model_data["provenance"] = []
                if isinstance(value, list):
                    new_model_data["provenance"].extend(value)
            elif isinstance(value, dict) and key in new_model_data and isinstance(new_model_data[key], dict):
                # Merge nested dicts
                new_model_data[key] = {**new_model_data[key], **value}
            else:
                # Replace or add new keys
                new_model_data[key] = value

        # Update WorldModel
        updated_model = update_world_model(
            self.session,
            project_id=project_id,
            model_data=new_model_data
        )

        if updated_model:
            # Record provenance in world model
            if isinstance(updated_model.model_data, dict):
                if "provenance" not in updated_model.model_data:
                    updated_model.model_data["provenance"] = []
                provenance_entry = build_provenance_entry(
                    event_type="feedback_patch",
                    actor="system",
                    source=f"issue_service:{action}",
                    description=f"WorldModel patched due to issue {issue_id}",
                    reference_ids=[issue_id, project_id],
                    metadata={"patch_type": "world_model", "updates": updates},
                )
                updated_model.model_data["provenance"].append(provenance_entry)
                update_world_model(
                    self.session,
                    project_id=project_id,
                    model_data=updated_model.model_data
                )

            self.session.commit()
            return True

        return False

    def _apply_patches(
        self,
        project_id: str,
        patch_data: Dict[str, Any],
        issue_id: str,
        action: str
    ) -> List[str]:
        """
        Apply all patches (ProblemSpec + WorldModel).

        Returns:
            List of patch types applied (e.g., ["problem_spec", "world_model"])
        """
        patches_applied = []

        if self._apply_problem_spec_patch(project_id, patch_data, issue_id, action):
            patches_applied.append("problem_spec")

        if self._apply_world_model_patch(project_id, patch_data, issue_id, action):
            patches_applied.append("world_model")

        return patches_applied

    def _record_rerun_provenance(
        self,
        project_id: str,
        issue_id: str,
        run_id: str,
        action: str,
        patches_applied: List[str]
    ):
        """Record provenance for rerun actions."""
        problem_spec = get_problem_spec(self.session, project_id)
        if problem_spec:
            provenance_entry = build_provenance_entry(
                event_type="feedback_patch",
                actor="system",
                source=f"issue_service:{action}",
                description=f"Rerun executed for run {run_id}",
                reference_ids=[issue_id, run_id],
                metadata={"action": action, "patches_applied": patches_applied},
            )
            if problem_spec.provenance_log is None:
                problem_spec.provenance_log = []
            problem_spec.provenance_log.append(provenance_entry)
            self.session.commit()

    def _mark_issue_resolved(self, issue_id: str):
        """Mark issue as resolved."""
        repo_update_issue(
            self.session,
            issue_id=issue_id,
            resolution_status=IssueResolutionStatus.RESOLVED.value,
            resolved_at=datetime.utcnow(),
        )

    # Now the public methods become much simpler:

    def apply_patch_and_rescore(
        self,
        issue_id: str,
        patch_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply patches and re-run evaluation+ranking."""
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        if not issue.run_id:
            raise ValueError(f"Issue {issue_id} has no associated run_id")

        # Apply patches (shared logic)
        patches_applied = self._apply_patches(
            issue.project_id,
            patch_data,
            issue_id,
            "apply_patch_and_rescore"
        )

        # Re-run evaluation and ranking
        try:
            result = self.run_service.execute_evaluate_and_rank_phase(issue.run_id)

            # Record provenance
            self._record_rerun_provenance(
                issue.project_id,
                issue_id,
                issue.run_id,
                "patch_and_rescore",
                patches_applied
            )

            # Mark resolved
            self._mark_issue_resolved(issue_id)

            return {
                "status": "success",
                "action": "patch_and_rescore",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in patch_and_rescore for issue {issue_id}: {e}", exc_info=True)
            raise

    def apply_partial_rerun(
        self,
        issue_id: str,
        patch_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply patches and re-run evaluation+ranking (same as patch_and_rescore)."""
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        if not issue.run_id:
            raise ValueError(f"Issue {issue_id} has no associated run_id")

        # Apply patches (shared logic)
        patches_applied = self._apply_patches(
            issue.project_id,
            patch_data,
            issue_id,
            "apply_partial_rerun"
        )

        # Re-run evaluation and ranking
        try:
            result = self.run_service.execute_evaluate_and_rank_phase(issue.run_id)

            # Record provenance
            self._record_rerun_provenance(
                issue.project_id,
                issue_id,
                issue.run_id,
                "partial_rerun",
                patches_applied
            )

            # Mark resolved
            self._mark_issue_resolved(issue_id)

            return {
                "status": "success",
                "action": "partial_rerun",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in partial_rerun for issue {issue_id}: {e}", exc_info=True)
            raise

    def apply_full_rerun(
        self,
        issue_id: str,
        patch_data: Dict[str, Any],
        run_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply patches and create new full run."""
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        # Apply patches (shared logic)
        patches_applied = self._apply_patches(
            issue.project_id,
            patch_data,
            issue_id,
            "apply_full_rerun"
        )

        # Create new run
        config = run_config or {}
        mode = config.get("mode", RunMode.FULL_SEARCH.value)
        num_candidates = config.get("num_candidates", 5)
        num_scenarios = config.get("num_scenarios", 8)

        new_run = create_run(
            self.session,
            project_id=issue.project_id,
            mode=mode,
            config={
                "num_candidates": num_candidates,
                "num_scenarios": num_scenarios,
                **{k: v for k, v in config.items() if k not in ["mode", "num_candidates", "num_scenarios"]},
            },
        )

        # Execute full pipeline
        try:
            result = self.run_service.execute_full_pipeline(
                run_id=new_run.id,
                num_candidates=num_candidates,
                num_scenarios=num_scenarios,
            )

            # Record provenance
            self._record_rerun_provenance(
                issue.project_id,
                issue_id,
                new_run.id,
                "full_rerun",
                patches_applied
            )

            # Mark resolved
            self._mark_issue_resolved(issue_id)

            return {
                "status": "success",
                "action": "full_rerun",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "new_run_id": new_run.id,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in full_rerun for issue {issue_id}: {e}", exc_info=True)
            raise
```

## Benefits of Refactor

### Before (Current)
- **799 lines** total
- **~315 lines** duplicated (40%)
- Bug fixes require 3 changes
- Tests require 3× duplication
- High risk of inconsistency

### After (Refactored)
- **~550 lines** total (31% reduction)
- **~0 lines** duplicated
- Bug fixes require 1 change
- Tests focus on shared logic
- No risk of inconsistency

## Implementation Plan

### Phase 1: Extract Helpers (2 hours)
1. Create `_apply_problem_spec_patch()` method
2. Create `_apply_world_model_patch()` method
3. Create `_apply_patches()` method
4. Create `_record_rerun_provenance()` method
5. Create `_mark_issue_resolved()` method

### Phase 2: Refactor Methods (2 hours)
1. Refactor `apply_patch_and_rescore()` to use helpers
2. Refactor `apply_partial_rerun()` to use helpers
3. Refactor `apply_full_rerun()` to use helpers

### Phase 3: Update Tests (1-2 hours)
1. Add tests for helper methods
2. Update existing integration tests
3. Verify all scenarios still work

### Total Effort: 5-6 hours

## Testing Strategy
```python
# Test shared logic once
def test_apply_problem_spec_patch():
    """Test shared ProblemSpec patching logic."""
    service = IssueService(session)
    result = service._apply_problem_spec_patch(
        project_id="proj1",
        patch_data={"problem_spec": {"constraints": [...]}},
        issue_id="issue1",
        action="test"
    )
    assert result is True

# Then test each public method lightly
def test_apply_patch_and_rescore():
    """Test patch_and_rescore uses shared logic correctly."""
    # Simpler test - just verify method works end-to-end
    ...
```

## Risk Assessment
- **Very low risk**: Pure refactor, no logic changes
- **Testing**: Existing tests should pass unchanged
- **Rollback**: Easy to revert if issues found

## Estimated Impact
- **Code quality**: 40% reduction in duplication
- **Maintainability**: Bug fixes 3× faster
- **Testing**: Test coverage improves (focus on shared logic)
- **AI modifications**: Much easier for AI to modify consistently

## Notes
- This is **#4 priority** for AI code quality
- Can be done independently of other issues
- Low risk, high reward refactor
- Should be done before any future enhancements to remediation logic
