# Issue 008: Sequential evaluation causes 60-80% slower run times

**Status**: Open
**Priority**: Critical
**Category**: Performance
**Discovered**: 2025-11-24
**Related Story**: (TBD)

## Description
The evaluation phase runs all candidate-scenario pairs sequentially, causing significant performance degradation. With 5 candidates and 8 scenarios (40 LLM calls), runs take 2-5 minutes when they could complete in 30-60 seconds with parallelization.

## Current Behavior
```python
# In evaluator_service.py
for candidate in candidates:
    for scenario in scenarios:
        evaluate(candidate, scenario)  # Sequential blocking calls
```

Each evaluation makes an LLM API call (500ms-5s per call), and all 40 calls happen sequentially.

## Expected Behavior
Evaluations should run in parallel with concurrency limits to maximize throughput while respecting rate limits.

## Performance Impact
- **Current**: 40 calls × 3s average = 120 seconds (2 minutes)
- **With async**: 40 calls / 10 concurrent = 4 batches × 3s = 12 seconds
- **Speedup**: **60-80% faster** (120s → 12-30s)

## Investigation Notes

### Location
- File: `crucible/services/evaluator_service.py`
- Method: `evaluate_all_candidates()`

### Root Cause
The evaluation loop iterates sequentially through all candidate-scenario pairs without leveraging async/parallel execution. Python's GIL doesn't matter here since we're I/O bound (waiting on LLM API responses).

### Technical Details
- Candidates: Typically 5 per run
- Scenarios: Typically 8 per run
- Evaluation pairs: 5 × 8 = 40
- Average LLM call latency: 2-5 seconds
- Total sequential time: 80-200 seconds
- Potential parallel time: 10-30 seconds (with 10-20 concurrent requests)

## Proposed Solution

### Option 1: asyncio with semaphore (Recommended)
```python
import asyncio
from typing import List

class EvaluatorService:
    async def evaluate_all_candidates_async(
        self,
        run_id: str,
        max_concurrent: int = 10
    ) -> Dict[str, Any]:
        """Evaluate all candidates in parallel with concurrency limit."""
        candidates = list_candidates(self.session, run_id=run_id)
        scenario_suite = get_scenario_suite_by_run(self.session, run_id)
        scenarios = scenario_suite.scenarios or []

        # Create semaphore to limit concurrent LLM calls
        semaphore = asyncio.Semaphore(max_concurrent)

        async def evaluate_pair(candidate, scenario):
            async with semaphore:
                # Convert sync LLM call to async
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,  # Use default executor
                    self._evaluate_candidate_scenario,
                    candidate,
                    scenario,
                    run_id
                )
                return result

        # Create all tasks
        tasks = [
            evaluate_pair(candidate, scenario)
            for candidate in candidates
            for scenario in scenarios
        ]

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        evaluations = [r for r in results if not isinstance(r, Exception)]
        errors = [r for r in results if isinstance(r, Exception)]

        if errors:
            logger.warning(f"Evaluation had {len(errors)} failures: {errors[:3]}")

        return {
            "evaluations": evaluations,
            "count": len(evaluations),
            "candidates_evaluated": len(candidates),
            "scenarios_used": len(scenarios),
            "errors": len(errors)
        }
```

### Option 2: ThreadPoolExecutor (If async not viable)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class EvaluatorService:
    def evaluate_all_candidates_parallel(
        self,
        run_id: str,
        max_workers: int = 10
    ) -> Dict[str, Any]:
        """Evaluate using thread pool."""
        candidates = list_candidates(self.session, run_id=run_id)
        scenario_suite = get_scenario_suite_by_run(self.session, run_id)
        scenarios = scenario_suite.scenarios or []

        evaluations = []
        errors = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self._evaluate_candidate_scenario,
                    candidate,
                    scenario,
                    run_id
                ): (candidate.id, scenario['id'])
                for candidate in candidates
                for scenario in scenarios
            }

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    evaluations.append(result)
                except Exception as e:
                    candidate_id, scenario_id = futures[future]
                    logger.error(f"Evaluation failed for {candidate_id} × {scenario_id}: {e}")
                    errors.append(e)

        return {
            "evaluations": evaluations,
            "count": len(evaluations),
            "candidates_evaluated": len(candidates),
            "scenarios_used": len(scenarios),
            "errors": len(errors)
        }
```

## Implementation Requirements

1. **Session Management**: Ensure SQLAlchemy sessions are thread-safe or use session-per-thread pattern
2. **Rate Limiting**: Add configurable concurrency limit (default: 10)
3. **Error Handling**: Individual evaluation failures shouldn't crash entire run
4. **Backward Compatibility**: Keep sync method as fallback
5. **Testing**: Add integration tests for parallel execution
6. **Monitoring**: Track parallel execution metrics

## Dependencies
- asyncio (stdlib)
- Kosmos LLM provider async support (may need investigation)
- SQLAlchemy session thread-safety considerations

## Estimated Impact
- **User experience**: Dramatically improved (2-5min → 30-60s waits)
- **Scalability**: Can handle larger runs (10 candidates × 15 scenarios = 150 pairs)
- **Resource utilization**: Better CPU/network usage

## Estimated Effort
- **Investigation**: 2 hours (check Kosmos async support, SQLAlchemy thread safety)
- **Implementation**: 6-8 hours (async version + error handling + tests)
- **Testing**: 2-4 hours (integration tests, edge cases)
- **Total**: 10-14 hours

## Risk Assessment
- **Low risk**: Evaluation logic unchanged, only execution model
- **Mitigation**: Keep sequential fallback, add feature flag
- **Testing**: Run parallel version side-by-side with sequential for validation

## Notes
- This is the **#1 priority** for user-facing impact
- Consider implementing retry logic (Issue 009) simultaneously for maximum reliability
- May need to coordinate with Kosmos team if async LLM support is needed
