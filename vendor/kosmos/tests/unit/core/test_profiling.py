"""
Unit tests for profiling system.

Tests ExecutionProfiler, profile decorators, and performance tracking.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from kosmos.core.profiling import (
    ExecutionProfiler,
    ProfileData,
    profile_function,
    profile_async_function,
    get_profiler
)


class TestProfileData:
    """Test ProfileData data class."""

    def test_creation(self):
        """Test creating profile data."""
        data = ProfileData(
            function_name="test_func",
            duration_seconds=1.5,
            memory_mb=100.0,
            cpu_percent=50.0
        )

        assert data.function_name == "test_func"
        assert data.duration_seconds == 1.5
        assert data.memory_mb == 100.0


class TestExecutionProfiler:
    """Test ExecutionProfiler class."""

    def test_initialization(self):
        """Test profiler initialization."""
        profiler = ExecutionProfiler(mode="light")

        assert profiler.mode == "light"
        assert profiler.enabled is True
        assert len(profiler.profiles) == 0

    def test_disabled_profiler(self):
        """Test profiler when disabled."""
        profiler = ExecutionProfiler(enabled=False)

        @profiler.profile
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        assert len(profiler.profiles) == 0  # No profiling when disabled

    def test_profile_decorator(self):
        """Test profile decorator."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func(x, y):
            time.sleep(0.1)
            return x + y

        result = test_func(2, 3)

        assert result == 5
        assert len(profiler.profiles) > 0

        # Check profile data
        profile = profiler.profiles[0]
        assert profile.function_name == "test_func"
        assert profile.duration_seconds >= 0.1

    def test_context_manager(self):
        """Test profiler as context manager."""
        profiler = ExecutionProfiler(mode="light")

        with profiler.profile_context("test_operation"):
            time.sleep(0.1)

        assert len(profiler.profiles) > 0
        profile = profiler.profiles[0]
        assert profile.function_name == "test_operation"
        assert profile.duration_seconds >= 0.1

    def test_memory_profiling(self):
        """Test memory usage profiling."""
        profiler = ExecutionProfiler(mode="standard")

        @profiler.profile
        def allocate_memory():
            # Allocate some memory
            data = [0] * 1000000
            return len(data)

        result = allocate_memory()

        assert result == 1000000
        assert len(profiler.profiles) > 0

        profile = profiler.profiles[0]
        assert profile.memory_mb is not None

    def test_get_summary(self):
        """Test getting profiling summary."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def func1():
            time.sleep(0.05)

        @profiler.profile
        def func2():
            time.sleep(0.1)

        func1()
        func2()

        summary = profiler.get_summary()

        assert "total_profiles" in summary
        assert summary["total_profiles"] == 2
        assert "total_duration" in summary

    def test_clear_profiles(self):
        """Test clearing profile data."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func():
            pass

        test_func()
        assert len(profiler.profiles) > 0

        profiler.clear()
        assert len(profiler.profiles) == 0

    def test_bottleneck_detection(self):
        """Test bottleneck detection."""
        profiler = ExecutionProfiler(mode="light", bottleneck_threshold=0.3)

        @profiler.profile
        def fast_func():
            time.sleep(0.01)

        @profiler.profile
        def slow_func():
            time.sleep(0.5)

        fast_func()
        slow_func()

        bottlenecks = profiler.detect_bottlenecks()

        # slow_func should be detected as bottleneck
        assert len(bottlenecks) > 0
        assert bottlenecks[0].function_name == "slow_func"

    def test_profiling_modes(self):
        """Test different profiling modes."""
        # Light mode
        light_profiler = ExecutionProfiler(mode="light")
        assert light_profiler.mode == "light"

        # Standard mode
        standard_profiler = ExecutionProfiler(mode="standard")
        assert standard_profiler.mode == "standard"

        # Full mode
        full_profiler = ExecutionProfiler(mode="full")
        assert full_profiler.mode == "full"


class TestProfileDecorators:
    """Test standalone profile decorators."""

    def test_profile_function_decorator(self):
        """Test profile_function decorator."""
        profiler = get_profiler()
        profiler.clear()

        @profile_function
        def test_func(x):
            time.sleep(0.05)
            return x * 2

        result = test_func(5)

        assert result == 10
        assert len(profiler.profiles) > 0

    @pytest.mark.asyncio
    async def test_profile_async_function_decorator(self):
        """Test profile_async_function decorator."""
        profiler = get_profiler()
        profiler.clear()

        @profile_async_function
        async def async_func(x):
            await asyncio.sleep(0.05)
            return x * 2

        import asyncio
        result = await async_func(5)

        assert result == 10
        assert len(profiler.profiles) > 0


class TestProfilerWithDatabase:
    """Test profiler with database storage."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('kosmos.core.profiling.get_session') as mock:
            session = MagicMock()
            mock.return_value = session
            yield session

    def test_store_profiles_to_db(self, mock_db):
        """Test storing profiles to database."""
        profiler = ExecutionProfiler(mode="light", store_in_db=True)

        @profiler.profile
        def test_func():
            time.sleep(0.01)

        test_func()

        # Should have attempted to store in database
        # (actual DB storage depends on models being available)
        assert len(profiler.profiles) > 0

    def test_load_profiles_from_db(self, mock_db):
        """Test loading profiles from database."""
        # Setup mock query results
        mock_profile = MagicMock()
        mock_profile.function_name = "test_func"
        mock_profile.duration_seconds = 1.5

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_profile]

        profiler = ExecutionProfiler(mode="light")
        loaded = profiler.load_from_db(days=7)

        # Should have queried database
        assert mock_db.query.called


class TestProfilerMetrics:
    """Test profiler metrics collection."""

    def test_average_duration(self):
        """Test calculating average duration."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func():
            time.sleep(0.1)

        # Run multiple times
        for _ in range(3):
            test_func()

        summary = profiler.get_summary()

        avg_duration = summary["total_duration"] / summary["total_profiles"]
        assert avg_duration >= 0.1

    def test_slowest_functions(self):
        """Test identifying slowest functions."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def fast():
            time.sleep(0.01)

        @profiler.profile
        def slow():
            time.sleep(0.2)

        fast()
        slow()

        slowest = profiler.get_slowest_functions(n=1)

        assert len(slowest) == 1
        assert slowest[0].function_name == "slow"


class TestGlobalProfiler:
    """Test global profiler instance."""

    def test_get_profiler_singleton(self):
        """Test get_profiler returns singleton."""
        profiler1 = get_profiler()
        profiler2 = get_profiler()

        assert profiler1 is profiler2

    def test_global_profiler_configuration(self):
        """Test configuring global profiler."""
        import os

        with patch.dict(os.environ, {"ENABLE_PROFILING": "true", "PROFILING_MODE": "standard"}):
            profiler = get_profiler()

            assert profiler.enabled is True
            assert profiler.mode == "standard"


class TestProfilerOverhead:
    """Test profiler overhead."""

    def test_minimal_overhead_when_disabled(self):
        """Test profiler adds minimal overhead when disabled."""
        profiler = ExecutionProfiler(enabled=False)

        @profiler.profile
        def test_func():
            return sum(range(10000))

        # Measure time with disabled profiling
        start = time.time()
        for _ in range(100):
            test_func()
        disabled_time = time.time() - start

        # Should complete quickly
        assert disabled_time < 1.0  # Very loose bound

    def test_light_mode_overhead(self):
        """Test light mode has acceptable overhead."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func():
            return sum(range(1000))

        # Run with profiling
        start = time.time()
        for _ in range(100):
            test_func()
        profiled_time = time.time() - start

        # Light mode overhead should be < 10%
        # (This is a rough test, actual overhead varies)
        assert profiled_time < 2.0


class TestProfilerExportImport:
    """Test exporting and importing profile data."""

    def test_export_to_dict(self):
        """Test exporting profiles to dictionary."""
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func():
            time.sleep(0.01)

        test_func()

        exported = profiler.export_profiles()

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert "function_name" in exported[0]
        assert "duration_seconds" in exported[0]

    def test_export_to_json(self):
        """Test exporting profiles to JSON."""
        import json
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        def test_func():
            time.sleep(0.01)

        test_func()

        json_str = profiler.export_to_json()
        data = json.loads(json_str)

        assert isinstance(data, list)
        assert len(data) > 0


class TestProfilerWithConcurrentOperations:
    """Test profiler with concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_profiling(self):
        """Test profiling concurrent async operations."""
        import asyncio
        profiler = ExecutionProfiler(mode="light")

        @profiler.profile
        async def async_task(n):
            await asyncio.sleep(0.01 * n)
            return n

        # Run multiple tasks concurrently
        tasks = [async_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert results == [0, 1, 2, 3, 4]
        assert len(profiler.profiles) == 5
