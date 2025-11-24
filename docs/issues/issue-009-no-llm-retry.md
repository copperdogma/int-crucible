# Issue 009: No LLM retry logic for transient failures

**Status**: Open
**Priority**: Critical
**Category**: Reliability
**Discovered**: 2025-11-24
**Related Story**: (TBD)

## Description
The system has no retry logic for LLM API calls, causing runs to fail on transient errors like rate limits, timeouts, and network issues. This results in a poor user experience where runs fail randomly and unpredictably.

## Current Behavior
```python
# In agent implementations
try:
    response = self.llm_provider.generate(prompt, **kwargs)
    # Use response
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    # Return fallback or re-raise
```

No retry attempts are made, so any transient failure causes immediate error.

## Expected Behavior
Transient LLM failures should be automatically retried with exponential backoff:
- Rate limit errors → retry with backoff
- Timeout errors → retry with backoff
- Network errors → retry with backoff
- Other errors → fail immediately (no retry)

## Impact on Users
- **Run failures**: Users see runs fail mid-execution
- **Wasted resources**: Partial work lost on failure
- **Frustration**: Users must manually retry entire runs
- **Unreliable system**: System appears broken

## Investigation Notes

### Common Transient Failures

1. **Rate Limit Errors** (HTTP 429)
   - Provider: Anthropic, OpenAI
   - Frequency: Moderate to high
   - Solution: Exponential backoff

2. **Timeout Errors** (HTTP 504, socket timeout)
   - Provider: All
   - Frequency: Low to moderate
   - Solution: Retry with increased timeout

3. **Network Errors** (Connection reset, DNS failure)
   - Provider: All
   - Frequency: Low
   - Solution: Retry with exponential backoff

4. **Overloaded Errors** (HTTP 503)
   - Provider: All
   - Frequency: Low
   - Solution: Exponential backoff

### Affected Components
- All agent implementations (6 agents)
- `crucible/core/tool_calling.py` (tool execution)
- Any service calling LLM directly

### Files to Modify
```
crucible/
  agents/
    problemspec_agent.py
    worldmodeller_agent.py
    designer_agent.py
    scenario_generator_agent.py
    evaluator_agent.py
    feedback_agent.py
  core/
    tool_calling.py
  services/
    (any direct LLM calls)
```

## Root Cause
No centralized retry mechanism was implemented. Each LLM call is a single attempt without error recovery.

## Proposed Solution

### Option 1: tenacity library (Recommended)
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

# Define retryable exceptions
RETRYABLE_LLM_ERRORS = (
    # Add provider-specific exceptions
    # anthropic.RateLimitError,
    # openai.RateLimitError,
    # requests.exceptions.Timeout,
    # requests.exceptions.ConnectionError,
    TimeoutError,
    ConnectionError,
)

class LLMRetryMixin:
    """Mixin to add retry logic to agents."""

    @retry(
        retry=retry_if_exception_type(RETRYABLE_LLM_ERRORS),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_llm_with_retry(self, prompt: str, **kwargs):
        """Call LLM with automatic retry on transient failures."""
        return self.llm_provider.generate(prompt, **kwargs)

# Usage in agents
class ProblemSpecAgent(BaseAgent, LLMRetryMixin):
    def refine_spec(self, ...):
        # Use retry-wrapped call
        response = self._call_llm_with_retry(prompt, **kwargs)
```

### Option 2: Custom Retry Decorator
```python
import time
import functools
from typing import Callable, Type, Tuple

def retry_llm_call(
    max_attempts: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (TimeoutError, ConnectionError)
):
    """Decorator to retry LLM calls with exponential backoff."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"LLM call failed after {max_attempts} attempts: {e}")
                        raise

                    # Calculate backoff delay
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                except Exception as e:
                    # Non-retryable exception, fail immediately
                    logger.error(f"LLM call failed with non-retryable error: {e}")
                    raise

            # Shouldn't reach here, but safety net
            raise last_exception

        return wrapper
    return decorator

# Usage
class ProblemSpecAgent(BaseAgent):
    @retry_llm_call(max_attempts=5, base_delay=2.0)
    def _call_llm(self, prompt, **kwargs):
        return self.llm_provider.generate(prompt, **kwargs)
```

### Option 3: Kosmos-level Retry (Best long-term)
```python
# In Kosmos LLM provider base class
class LLMProvider:
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()

    def generate(self, prompt, **kwargs):
        """Generate with built-in retry logic."""
        return self._generate_with_retry(prompt, **kwargs)

    @retry(...)  # Kosmos handles retry
    def _generate_with_retry(self, prompt, **kwargs):
        return self._raw_generate(prompt, **kwargs)
```

This would be the cleanest but requires Kosmos changes.

## Implementation Plan

### Phase 1: Quick Win (4-6 hours)
1. Add `tenacity` to dependencies
2. Create `LLMRetryMixin` in `crucible/core/llm_retry.py`
3. Apply to all 6 agent classes
4. Test with rate limit simulation

### Phase 2: Tool Calling (2 hours)
1. Add retry to `tool_calling.py`
2. Wrap provider calls with retry logic

### Phase 3: Configuration (2 hours)
1. Add retry config to `crucible/config.py`
2. Make retry parameters configurable
3. Add metrics tracking

## Configuration
```python
# In config.py
class LLMRetryConfig(BaseModel):
    max_attempts: int = 5
    base_delay_seconds: float = 2.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0

class Config(BaseModel):
    # ...
    llm_retry: LLMRetryConfig = LLMRetryConfig()
```

## Testing Strategy

1. **Unit Tests**: Mock LLM provider to simulate transient failures
2. **Integration Tests**: Use real providers with rate limit testing
3. **Chaos Testing**: Inject random failures to verify retry behavior

```python
# Test example
def test_llm_retry_on_rate_limit():
    """Test that rate limit errors trigger retry."""
    provider = MockLLMProvider()
    provider.set_failure_sequence([
        RateLimitError(),  # Attempt 1: fail
        RateLimitError(),  # Attempt 2: fail
        "Success"          # Attempt 3: succeed
    ])

    agent = ProblemSpecAgent(llm_provider=provider)
    result = agent.refine_spec(...)

    assert result == "Success"
    assert provider.call_count == 3
```

## Dependencies
- `tenacity>=8.0.0` (or custom retry logic)
- Provider-specific exception types

## Estimated Impact
- **Reliability**: 90%+ reduction in transient failures
- **User experience**: Dramatically improved (no more random failures)
- **Success rate**: Run completion rate improves from ~85% to ~99%

## Estimated Effort
- **Phase 1** (agents): 4-6 hours
- **Phase 2** (tool calling): 2 hours
- **Phase 3** (config): 2 hours
- **Testing**: 2-3 hours
- **Total**: 10-13 hours

## Risk Assessment
- **Low risk**: Only adds retry behavior, doesn't change logic
- **Mitigation**: Start with conservative retry limits
- **Monitoring**: Track retry metrics to tune parameters

## Related Issues
- Issue 008: Should implement together with async evaluation
- Consider combining retry with circuit breaker pattern for persistent failures

## Notes
- This is **#2 priority** for user-facing reliability
- Synergizes well with Issue 008 (parallel evaluation)
- Consider adding metrics: retry_count, retry_duration, failure_rate
