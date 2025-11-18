"""
Performance profiling infrastructure for Kosmos.

Provides comprehensive profiling capabilities including CPU profiling,
memory profiling, and bottleneck detection for experiments and workflows.
"""

import cProfile
import pstats
import tracemalloc
import time
import io
import logging
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProfilingMode(str, Enum):
    """Profiling mode enumeration."""
    LIGHT = "light"          # Basic timing + memory (~1% overhead)
    STANDARD = "standard"    # + cProfile (~5% overhead)
    FULL = "full"            # + line profiling (~10-15% overhead)


class Bottleneck(BaseModel):
    """Detected performance bottleneck."""

    function_name: str = Field(description="Function name")
    module_name: str = Field(description="Module name")
    cumulative_time: float = Field(description="Total time spent (seconds)")
    time_percent: float = Field(description="Percentage of total time")
    call_count: int = Field(description="Number of calls")
    per_call_time: float = Field(description="Average time per call (milliseconds)")
    severity: str = Field(description="Severity: critical, high, medium, low")

    @classmethod
    def from_stats(
        cls,
        function_name: str,
        module_name: str,
        cumulative_time: float,
        total_time: float,
        call_count: int
    ) -> "Bottleneck":
        """Create bottleneck from profiling stats."""
        time_percent = (cumulative_time / total_time * 100) if total_time > 0 else 0
        per_call_ms = (cumulative_time / call_count * 1000) if call_count > 0 else 0

        # Determine severity
        if time_percent > 30:
            severity = "critical"
        elif time_percent > 15:
            severity = "high"
        elif time_percent > 5:
            severity = "medium"
        else:
            severity = "low"

        return cls(
            function_name=function_name,
            module_name=module_name,
            cumulative_time=cumulative_time,
            time_percent=time_percent,
            call_count=call_count,
            per_call_time=per_call_ms,
            severity=severity
        )


class MemorySnapshot(BaseModel):
    """Memory usage snapshot."""

    timestamp: float = Field(description="Snapshot timestamp")
    current_mb: float = Field(description="Current memory usage (MB)")
    peak_mb: float = Field(description="Peak memory usage (MB)")
    allocated_mb: float = Field(description="Total allocated (MB)")


class ProfileResult(BaseModel):
    """Comprehensive profiling result."""

    # Basic metrics
    execution_time: float = Field(description="Total execution time (seconds)")
    cpu_time: float = Field(description="CPU time (seconds)")
    wall_time: float = Field(description="Wall clock time (seconds)")

    # Memory metrics
    memory_peak_mb: float = Field(description="Peak memory usage (MB)")
    memory_start_mb: float = Field(description="Starting memory usage (MB)")
    memory_end_mb: float = Field(description="Ending memory usage (MB)")
    memory_allocated_mb: float = Field(description="Total memory allocated (MB)")
    memory_snapshots: List[MemorySnapshot] = Field(
        default_factory=list,
        description="Memory usage over time"
    )

    # Function call statistics
    function_calls: Dict[str, int] = Field(
        default_factory=dict,
        description="Function call counts"
    )
    function_times: Dict[str, float] = Field(
        default_factory=dict,
        description="Function cumulative times"
    )

    # Bottlenecks
    bottlenecks: List[Bottleneck] = Field(
        default_factory=list,
        description="Detected performance bottlenecks"
    )

    # Metadata
    profiling_mode: ProfilingMode = Field(description="Profiling mode used")
    profiler_overhead_ms: float = Field(
        default=0.0,
        description="Estimated profiler overhead (milliseconds)"
    )
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")

    # Additional data
    profile_data: Optional[str] = Field(
        default=None,
        description="Raw profiling data (cProfile stats)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@dataclass
class ProfilingContext:
    """Context for active profiling session."""

    profiler: Optional[cProfile.Profile] = None
    start_time: float = 0.0
    start_cpu_time: float = 0.0
    memory_tracking: bool = False
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    mode: ProfilingMode = ProfilingMode.LIGHT


class ExecutionProfiler:
    """
    Comprehensive execution profiler for experiments and workflows.

    Supports multiple profiling modes:
    - Light: Basic timing + memory tracking (~1% overhead)
    - Standard: + cProfile for function-level CPU profiling (~5% overhead)
    - Full: + detailed analysis and line profiling (~10-15% overhead)

    Example:
        ```python
        profiler = ExecutionProfiler(mode=ProfilingMode.STANDARD)

        # Profile a function
        result = profiler.profile_function(my_function, arg1, arg2, kwarg1=value)

        # Profile with context manager
        with profiler.profile_context() as ctx:
            # Code to profile
            do_work()

        # Get results
        profile_result = profiler.get_result()
        ```
    """

    def __init__(
        self,
        mode: ProfilingMode = ProfilingMode.LIGHT,
        bottleneck_threshold_percent: float = 10.0,
        enable_memory_tracking: bool = True
    ):
        """
        Initialize profiler.

        Args:
            mode: Profiling mode (light, standard, full)
            bottleneck_threshold_percent: Threshold for bottleneck detection (%)
            enable_memory_tracking: Enable memory profiling
        """
        self.mode = mode
        self.bottleneck_threshold = bottleneck_threshold_percent
        self.enable_memory_tracking = enable_memory_tracking
        self._context: Optional[ProfilingContext] = None
        self._result: Optional[ProfileResult] = None

    @contextmanager
    def profile_context(self):
        """
        Context manager for profiling a code block.

        Example:
            ```python
            profiler = ExecutionProfiler()
            with profiler.profile_context():
                # Code to profile
                result = expensive_operation()

            profile_result = profiler.get_result()
            ```
        """
        self._start_profiling()
        try:
            yield self._context
        finally:
            self._stop_profiling()

    def profile_function(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, ProfileResult]:
        """
        Profile a single function call.

        Args:
            func: Function to profile
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Tuple of (function result, profile result)

        Example:
            ```python
            profiler = ExecutionProfiler()
            result, profile = profiler.profile_function(compute_something, data)
            print(f"Execution took {profile.execution_time:.2f}s")
            ```
        """
        with self.profile_context():
            result = func(*args, **kwargs)

        return result, self.get_result()

    def profile_experiment(
        self,
        experiment_id: str,
        code: str,
        local_vars: Optional[Dict[str, Any]] = None
    ) -> ProfileResult:
        """
        Profile experiment code execution.

        Args:
            experiment_id: Experiment identifier
            code: Code to execute and profile
            local_vars: Local variables for code execution

        Returns:
            ProfileResult with execution metrics
        """
        local_vars = local_vars or {}

        with self.profile_context():
            try:
                exec(code, {}, local_vars)
            except Exception as e:
                logger.error(f"Error executing experiment {experiment_id}: {e}")
                raise

        result = self.get_result()
        return result

    def _start_profiling(self):
        """Start profiling session."""
        self._context = ProfilingContext(mode=self.mode)

        # Record start time
        self._context.start_time = time.time()
        self._context.start_cpu_time = time.process_time()

        # Start memory tracking
        if self.enable_memory_tracking and self.mode != ProfilingMode.LIGHT:
            try:
                tracemalloc.start()
                self._context.memory_tracking = True
            except Exception as e:
                logger.warning(f"Failed to start memory tracking: {e}")

        # Start CPU profiling for standard and full modes
        if self.mode in (ProfilingMode.STANDARD, ProfilingMode.FULL):
            self._context.profiler = cProfile.Profile()
            self._context.profiler.enable()

    def _stop_profiling(self):
        """Stop profiling and compute results."""
        if not self._context:
            return

        # Stop timing
        end_time = time.time()
        end_cpu_time = time.process_time()

        wall_time = end_time - self._context.start_time
        cpu_time = end_cpu_time - self._context.start_cpu_time

        # Stop CPU profiling
        profile_stats = None
        if self._context.profiler:
            self._context.profiler.disable()
            profile_stats = pstats.Stats(self._context.profiler)

        # Get memory statistics
        memory_peak_mb = 0.0
        memory_current_mb = 0.0
        memory_allocated_mb = 0.0

        if self._context.memory_tracking:
            try:
                current, peak = tracemalloc.get_traced_memory()
                memory_current_mb = current / 1024 / 1024
                memory_peak_mb = peak / 1024 / 1024
                memory_allocated_mb = current / 1024 / 1024
                tracemalloc.stop()
            except Exception as e:
                logger.warning(f"Failed to get memory stats: {e}")

        # Build result
        self._result = ProfileResult(
            execution_time=wall_time,
            cpu_time=cpu_time,
            wall_time=wall_time,
            memory_peak_mb=memory_peak_mb,
            memory_start_mb=0.0,
            memory_end_mb=memory_current_mb,
            memory_allocated_mb=memory_allocated_mb,
            profiling_mode=self.mode,
            started_at=datetime.fromtimestamp(self._context.start_time),
            completed_at=datetime.fromtimestamp(end_time)
        )

        # Process detailed stats for standard and full modes
        if profile_stats and self.mode in (ProfilingMode.STANDARD, ProfilingMode.FULL):
            self._process_profile_stats(profile_stats)

    def _process_profile_stats(self, stats: pstats.Stats):
        """Process cProfile statistics."""
        if not self._result:
            return

        # Get function statistics
        function_calls = {}
        function_times = {}

        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = self._format_func_name(func)
            function_calls[func_name] = nc
            function_times[func_name] = ct

        self._result.function_calls = function_calls
        self._result.function_times = function_times

        # Detect bottlenecks
        self._result.bottlenecks = self._detect_bottlenecks(stats)

        # Store raw profile data if in full mode
        if self.mode == ProfilingMode.FULL:
            stream = io.StringIO()
            ps = pstats.Stats(stats.stream, stream=stream)
            ps.sort_stats('cumulative')
            ps.print_stats(50)  # Top 50 functions
            self._result.profile_data = stream.getvalue()

    def _detect_bottlenecks(
        self,
        stats: pstats.Stats,
        top_n: int = 20
    ) -> List[Bottleneck]:
        """
        Detect performance bottlenecks.

        Args:
            stats: Profile statistics
            top_n: Number of top functions to analyze

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        # Get total time
        total_time = sum(ct for _, (_, _, _, ct, _) in stats.stats.items())

        if total_time == 0:
            return bottlenecks

        # Sort by cumulative time
        sorted_stats = sorted(
            stats.stats.items(),
            key=lambda x: x[1][3],  # cumulative time
            reverse=True
        )

        # Analyze top functions
        for func, (cc, nc, tt, ct, callers) in sorted_stats[:top_n]:
            time_percent = (ct / total_time * 100) if total_time > 0 else 0

            # Only flag as bottleneck if above threshold
            if time_percent < self.bottleneck_threshold:
                continue

            func_name = self._format_func_name(func)
            module_name = func[0] if isinstance(func, tuple) else "unknown"

            bottleneck = Bottleneck.from_stats(
                function_name=func_name,
                module_name=module_name,
                cumulative_time=ct,
                total_time=total_time,
                call_count=nc
            )

            bottlenecks.append(bottleneck)

        return bottlenecks

    def _format_func_name(self, func) -> str:
        """Format function name from cProfile tuple."""
        if isinstance(func, tuple) and len(func) >= 3:
            filename, line, name = func[0], func[1], func[2]
            # Simplify path
            path = Path(filename)
            if len(path.parts) > 2:
                filename = "/".join(path.parts[-2:])
            return f"{filename}:{line}:{name}"
        return str(func)

    def get_result(self) -> Optional[ProfileResult]:
        """
        Get profiling result.

        Returns:
            ProfileResult if profiling was performed, None otherwise
        """
        return self._result

    def reset(self):
        """Reset profiler state."""
        self._context = None
        self._result = None


def profile_experiment_execution(
    experiment_id: str,
    code: str,
    data_path: Optional[str] = None,
    mode: ProfilingMode = ProfilingMode.STANDARD
) -> ProfileResult:
    """
    Convenience function to profile an experiment execution.

    Args:
        experiment_id: Experiment identifier
        code: Code to execute
        data_path: Optional data path
        mode: Profiling mode

    Returns:
        ProfileResult with execution metrics

    Example:
        ```python
        result = profile_experiment_execution(
            experiment_id="exp_123",
            code="import numpy as np; result = np.random.rand(1000, 1000).sum()",
            mode=ProfilingMode.STANDARD
        )
        print(f"Execution: {result.execution_time:.2f}s")
        print(f"Memory peak: {result.memory_peak_mb:.1f} MB")
        ```
    """
    profiler = ExecutionProfiler(mode=mode)
    local_vars = {"data_path": data_path} if data_path else {}

    return profiler.profile_experiment(
        experiment_id=experiment_id,
        code=code,
        local_vars=local_vars
    )


def format_profile_summary(result: ProfileResult) -> str:
    """
    Format profile result as human-readable summary.

    Args:
        result: ProfileResult to format

    Returns:
        Formatted string summary
    """
    summary = []
    summary.append("=" * 60)
    summary.append("PROFILE SUMMARY")
    summary.append("=" * 60)
    summary.append(f"Execution time: {result.execution_time:.3f}s")
    summary.append(f"CPU time: {result.cpu_time:.3f}s")
    summary.append(f"Memory peak: {result.memory_peak_mb:.1f} MB")
    summary.append(f"Memory allocated: {result.memory_allocated_mb:.1f} MB")
    summary.append(f"Profiling mode: {result.profiling_mode}")

    if result.bottlenecks:
        summary.append("\n" + "=" * 60)
        summary.append("BOTTLENECKS")
        summary.append("=" * 60)
        for i, bottleneck in enumerate(result.bottlenecks[:10], 1):
            summary.append(
                f"{i}. {bottleneck.function_name}"
                f" ({bottleneck.time_percent:.1f}%, "
                f"{bottleneck.call_count} calls, "
                f"{bottleneck.per_call_time:.2f}ms/call)"
                f" [{bottleneck.severity.upper()}]"
            )

    summary.append("=" * 60)
    return "\n".join(summary)
