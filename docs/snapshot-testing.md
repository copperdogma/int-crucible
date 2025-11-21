# Snapshot Testing Guide

Int Crucible's snapshot testing system provides an AI-first approach to regression testing for non-deterministic LLM-based systems.

## Overview

Snapshot testing in Int Crucible allows you to:
- Capture system state (ProblemSpec, WorldModel, run configuration) at a point in time
- Replay snapshots to test if the pipeline still works correctly
- Define invariants (e.g., "at least 3 candidates generated", "run completes successfully")
- Run automated tests that validate invariants even when LLM outputs are non-deterministic

This is essential for AI agents that need to verify their changes don't break the system, despite non-deterministic LLM behavior.

## Core Concepts

### Snapshots

A **snapshot** is a frozen copy of:
- ProblemSpec (constraints, goals, resolution, mode)
- WorldModel (model_data)
- Run configuration (if captured from a run)
- Optional chat context (last N messages)
- Reference metrics (baseline run metrics for comparison)
- Invariants (expected behaviors to validate)

Snapshots are **immutable** - once created, the snapshot_data doesn't change. This ensures reproducibility.

### Invariants

**Invariants** are assertions about expected behavior that should hold true when replaying a snapshot. Unlike traditional unit tests that check exact values, invariants check ranges, bounds, and structural properties.

Example invariants:
- `min_candidates: 3` - At least 3 candidates must be generated
- `run_status: "COMPLETED"` - Run must complete successfully
- `min_top_i_score: 0.3` - Top candidate I-score must be >= 0.3
- `no_hard_constraint_violations: true` - No hard constraints (weight=100) should be violated

### Replay

**Replay** creates a new temporary project, restores the snapshot data, and executes the pipeline. The replay run will produce different candidates/scores (LLMs are non-deterministic), but should satisfy the invariants.

## Usage

### Creating Snapshots

#### Via CLI

```bash
# Create snapshot from a project
crucible snapshot create \
  --project-id abc123 \
  --name "Chat-first UI baseline" \
  --description "Baseline snapshot for chat-first UI spec modelling" \
  --tags "ui,chat,spec"

# Create snapshot from a project and run (captures metrics)
crucible snapshot create \
  --project-id abc123 \
  --run-id xyz789 \
  --name "Heavy constraints test" \
  --description "Tests constraint handling with many high-weight constraints" \
  --tags "constraints,test"

# Create snapshot with custom invariants
crucible snapshot create \
  --project-id abc123 \
  --name "My Snapshot" \
  --invariants-file invariants.json
```

Where `invariants.json` contains:
```json
[
  {
    "type": "min_candidates",
    "value": 5,
    "description": "At least 5 candidates must be generated"
  },
  {
    "type": "run_status",
    "value": "COMPLETED",
    "description": "Run must complete successfully"
  },
  {
    "type": "min_top_i_score",
    "value": 0.4,
    "description": "Top candidate I-score must be >= 0.4"
  }
]
```

#### Via API

```bash
curl -X POST http://localhost:8000/snapshots \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc123",
    "run_id": "xyz789",
    "name": "My Snapshot",
    "description": "Test snapshot",
    "tags": ["test", "automated"],
    "invariants": [
      {
        "type": "min_candidates",
        "value": 3,
        "description": "At least 3 candidates"
      }
    ]
  }'
```

### Listing Snapshots

```bash
# List all snapshots
crucible snapshot list

# Filter by project
crucible snapshot list --project-id abc123

# Filter by tags
crucible snapshot list --tags test,automated

# Filter by name
crucible snapshot list --name "baseline"

# JSON output for AI agents
crucible snapshot list --format json
```

### Viewing Snapshot Details

```bash
# Human-readable output
crucible snapshot show abc123

# JSON output
crucible snapshot show abc123 --json
```

### Replaying Snapshots

```bash
# Replay with full pipeline
crucible snapshot replay abc123

# Replay only design phase
crucible snapshot replay abc123 --phases design

# Replay with overridden parameters
crucible snapshot replay abc123 --num-candidates 3 --num-scenarios 5

# Reuse existing project instead of creating temp one
crucible snapshot replay abc123 --reuse-project
```

### Running Snapshot Tests

```bash
# Test all snapshots
crucible snapshot test --all

# Test specific snapshots
crucible snapshot test --snapshot-ids abc123,xyz789

# Test with limits
crucible snapshot test --all --max-snapshots 5 --cost-limit-usd 10.0

# Stop on first failure
crucible snapshot test --all --stop-on-failure

# JSON output for AI agents
crucible snapshot test --all --format json
```

## Invariant Types

### Count Invariants

- `min_candidates` - Minimum number of candidates (value: integer)
- `max_candidates` - Maximum number of candidates (value: integer)
- `min_scenarios` - Minimum number of scenarios (value: integer)
- `max_scenarios` - Maximum number of scenarios (value: integer)

### Status Invariants

- `run_status` - Expected final run status (value: "COMPLETED", "FAILED", etc.)

### Score Invariants

- `min_top_i_score` - Minimum I-score for top candidate (value: float)
- `max_top_i_score` - Maximum I-score for top candidate (value: float)

### Constraint Invariants

- `no_hard_constraint_violations` - No hard constraints (weight=100) should be violated (value: true/false)

### Performance Invariants

- `max_duration_seconds` - Maximum run duration in seconds (value: float)

### Coverage Invariants

- `min_evaluation_coverage` - Minimum fraction of expected evaluations that must exist (value: float, 0.0-1.0)

## Best Practices

### When to Create Snapshots

1. **After successful runs** - Capture working states as baselines
2. **Before major changes** - Create snapshots to test against after refactoring
3. **For interesting scenarios** - Capture edge cases, heavy constraints, failure modes
4. **For regression testing** - Create snapshots that previously failed to ensure they're fixed

### What Makes a Good Snapshot

- **Complete state** - Includes ProblemSpec, WorldModel, and ideally a run reference
- **Clear invariants** - Defines what "success" means for this snapshot
- **Descriptive names** - Names that explain what the snapshot tests
- **Relevant tags** - Tags that help categorize and find snapshots

### Interpreting Test Results

- **Passed** - All invariants satisfied, pipeline completed successfully
- **Failed** - One or more invariants violated
- **Skipped** - Test skipped (e.g., cost limit exceeded, snapshot not found)

When a snapshot test fails:
1. Check which invariants failed
2. Compare metrics_delta to see what changed
3. Consider if the change is a regression or acceptable variance
4. Update invariants if needed (create new snapshot with updated invariants)

### Cost Management

- Use `--cost-limit-usd` to bound test costs
- Use `--max-snapshots` to limit how many snapshots are tested
- Consider using `--phases design` for faster tests (skips expensive evaluation phase)
- Use `--num-candidates` and `--num-scenarios` to reduce per-snapshot cost

## AI Agent Usage Patterns

### Regression Testing Workflow

```python
# 1. List snapshots
snapshots = GET /snapshots

# 2. Run tests before change
results_before = POST /snapshots/run-tests {"snapshot_ids": ["id1", "id2"]}

# 3. Make code changes
# ... modify code ...

# 4. Run tests after change
results_after = POST /snapshots/run-tests {"snapshot_ids": ["id1", "id2"]}

# 5. Compare results
if results_after["summary"]["failed"] > results_before["summary"]["failed"]:
    # Regression detected
    analyze_failures(results_after)
```

### Creating Snapshots Programmatically

```python
# After a successful run, create a snapshot
snapshot = POST /snapshots {
    "project_id": project_id,
    "run_id": run_id,
    "name": f"Baseline {datetime.now()}",
    "tags": ["automated", "baseline"],
    "invariants": [
        {"type": "min_candidates", "value": 3},
        {"type": "run_status", "value": "COMPLETED"}
    ]
}
```

### Interpreting Test Results

```python
results = POST /snapshots/run-tests {"snapshot_ids": ["id1"]}

for result in results["results"]:
    if result["status"] == "failed":
        for inv in result["invariants"]:
            if inv["status"] == "failed":
                print(f"Failed: {inv['type']} - {inv['message']}")
```

## Example Snapshots

### Example 1: Chat-First UI Spec Modelling

**Purpose:** Tests ProblemSpec/WorldModel creation flow through chat interface.

**Snapshot Data:**
- ProblemSpec with constraints from chat conversation
- WorldModel generated from ProblemSpec
- No run reference (setup-only snapshot)

**Invariants:**
```json
[
  {
    "type": "run_status",
    "value": "COMPLETED",
    "description": "Pipeline must complete when run is executed"
  }
]
```

**Usage:**
```bash
crucible snapshot create \
  --project-id <project-with-chat-spec> \
  --name "Chat-first UI spec baseline" \
  --tags "ui,chat,spec"
```

### Example 2: Heavy Constraints Evaluation

**Purpose:** Tests constraint handling with many high-weight constraints.

**Snapshot Data:**
- ProblemSpec with 10+ constraints, many with weight=100
- WorldModel with complex constraint relationships
- Run reference with baseline metrics

**Invariants:**
```json
[
  {
    "type": "min_candidates",
    "value": 3,
    "description": "At least 3 candidates must be generated"
  },
  {
    "type": "no_hard_constraint_violations",
    "value": true,
    "description": "No hard constraints should be violated"
  },
  {
    "type": "run_status",
    "value": "COMPLETED",
    "description": "Run must complete successfully"
  }
]
```

**Usage:**
```bash
# First, create a run with heavy constraints
# Then capture as snapshot:
crucible snapshot create \
  --project-id <project-id> \
  --run-id <run-id> \
  --name "Heavy constraints test" \
  --tags "constraints,test"
```

### Example 3: Failure Mode Scenario

**Purpose:** Tests error handling and partial completion recovery.

**Snapshot Data:**
- ProblemSpec that previously caused failures
- WorldModel that triggered edge cases
- Run reference showing failure metrics

**Invariants:**
```json
[
  {
    "type": "run_status",
    "value": "COMPLETED",
    "description": "Run should now complete (regression test)"
  },
  {
    "type": "min_evaluation_coverage",
    "value": 0.8,
    "description": "At least 80% evaluation coverage"
  }
]
```

**Usage:**
```bash
# Capture a snapshot from a project that previously failed
crucible snapshot create \
  --project-id <previously-failing-project> \
  --name "Failure mode regression test" \
  --tags "regression,error-handling"
```

## Troubleshooting

### Snapshot Creation Fails

**Error:** "ProblemSpec not found" or "WorldModel not found"
- **Solution:** Ensure the project has both ProblemSpec and WorldModel before creating snapshot

**Error:** "UNIQUE constraint failed: crucible_snapshots.name"
- **Solution:** Use a unique name for the snapshot

### Replay Fails

**Error:** Pipeline execution fails during replay
- **Check:** Verify the snapshot data is valid (use `snapshot show`)
- **Check:** Ensure LLM provider is configured correctly
- **Check:** Review error_summary in replay run results

### Invariant Validation Fails

**Issue:** Invariants fail due to LLM variance (not actual regressions)
- **Solution:** Use ranges/bounds rather than exact values
- **Solution:** Consider statistical tests (future enhancement)
- **Solution:** Manually review failures to distinguish variance from regressions

### Cost Concerns

**Issue:** Snapshot tests are too expensive
- **Solution:** Use `--cost-limit-usd` to bound costs
- **Solution:** Use `--max-snapshots` to limit scope
- **Solution:** Use `--phases design` for faster tests
- **Solution:** Reduce `--num-candidates` and `--num-scenarios` for replay

## Future Enhancements

- **Custom invariants** - User-defined Python expressions for invariants
- **Statistical tests** - Compare distributions rather than exact values
- **Snapshot versioning** - Automatic migration of old snapshot formats
- **Parallel execution** - Run multiple snapshot tests in parallel
- **Snapshot comparison** - Compare metrics between snapshots
- **Automated snapshot creation** - Create snapshots automatically after successful runs

## Related Documentation

- `docs/stories/story-018-ai-first-test-pipeline.md` - Implementation story
- `AGENTS.md` - AI agent usage patterns
- `docs/architecture.md` - System architecture
- `docs/design.md` - Design decisions

