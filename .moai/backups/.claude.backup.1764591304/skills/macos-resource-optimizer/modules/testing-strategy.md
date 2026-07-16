# Testing Strategy

Comprehensive testing patterns for macOS Resource Optimizer wrapper layer using pytest-asyncio, mocking strategies, integration testing, and performance benchmarks.

## Implementation Status

⚠️ **IMPORTANT**: This document describes **conceptual testing architecture**. The actual tests use **pytest for UV scripts** in `.data/tests/`.

**Current Implementation** (as of 2025-11-30):
- ✅ 278 total test functions implemented
- ✅ 191/278 tests passing (68.7%)
- ✅ Test files: test_*.py (unit tests for each script)
- ✅ Test coverage: test_command_*.py (6 MoAI commands)
- 🔄 87 tests failing (error handling, edge cases)
- 🔄 Integration tests in progress

**This Document Describes**:
- Conceptual pytest-asyncio configuration
- Wrapper class mocking strategies (theoretical)
- Integration testing patterns (conceptual)
- Performance benchmark approaches

**For Actual Tests**: See:
- `.data/tests/test_*.py` (unit tests)
- `.data/tests/test_command_*.py` (command tests)
- `.data/tests/TEST_SUMMARY.md` (test status)

---

## Overview

**Testing Levels**:
1. **Unit Tests**: Wrapper components in isolation
2. **Integration Tests**: Wrapper + Python engine interaction
3. **Performance Tests**: Parallel execution benchmarks
4. **Error Handling Tests**: Timeout and failure scenarios

**Key Tools**:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking and patching
- `pytest-benchmark` - Performance benchmarks
- `pytest-timeout` - Timeout management

## pytest-asyncio Configuration

### conftest.py Setup

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from pathlib import Path
import json
import time
from typing import Dict, Any

# Configure asyncio for all tests
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for all tests"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

@pytest_asyncio.fixture
async def wrapper(tmp_path):
    """
    PythonEngineWrapper test fixture

    Creates wrapper with mock coordinator for isolated testing.
    """
    from wrapper import PythonEngineWrapper

    # Create mock coordinator script
    coordinator = tmp_path / "coordinator.py"
    coordinator.write_text(MOCK_COORDINATOR_SCRIPT)

    wrapper = PythonEngineWrapper(
        engine_path=str(coordinator),
        timeout=5,  # Shorter timeout for tests
        cache_ttl=2  # Shorter cache for tests
    )

    yield wrapper

    # Cleanup
    wrapper.cache.clear()

@pytest_asyncio.fixture
async def coordinator():
    """ResourceCoordinator fixture"""
    from wrapper import PythonEngineWrapper
    from coordinator import ResourceCoordinator

    wrapper = PythonEngineWrapper()
    coordinator = ResourceCoordinator(wrapper)

    yield coordinator

    # Cleanup
    wrapper.cache.clear()

@pytest.fixture
def mock_analysis_result():
    """Mock analysis result data"""
    return {
        "status": "success",
        "category": "cpu",
        "timestamp": time.time(),
        "metrics": {
            "usage_percent": 45.2,
            "user_percent": 30.1,
            "system_percent": 15.1,
            "idle_percent": 54.8
        },
        "recommendations": [
            {
                "type": "optimization",
                "priority": "medium",
                "description": "CPU usage within normal range"
            }
        ]
    }

# Mock coordinator.py script
MOCK_COORDINATOR_SCRIPT = """
import sys
import json
import time

def main():
    args = sys.argv[1:]

    if "--analyze" in args:
        category_idx = args.index("--category") + 1
        category = args[category_idx]

        result = {
            "status": "success",
            "category": category,
            "timestamp": time.time(),
            "metrics": {"usage_percent": 45.2}
        }

        # Simulate processing time
        time.sleep(0.1)

        print(json.dumps(result))

    elif "--analyze-all" in args:
        result = {
            "status": "success",
            "categories": ["cpu", "memory", "disk"]
        }
        print(json.dumps(result))

if __name__ == "__main__":
    main()
"""
```

## Unit Tests

### Test PythonEngineWrapper

```python
# tests/test_wrapper.py
import pytest
import pytest_asyncio
import asyncio
import time
from wrapper import (
    PythonEngineWrapper,
    AnalysisTimeoutError,
    AnalysisExecutionError,
    ResultParseError
)

class TestPythonEngineWrapper:
    """Unit tests for PythonEngineWrapper"""

    @pytest.mark.asyncio
    async def test_execute_analysis_success(self, wrapper):
        """Test successful analysis execution"""
        result = await wrapper.execute_analysis("cpu")

        assert result["status"] == "success"
        assert result["category"] == "cpu"
        assert "metrics" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_execute_analysis_with_options(self, wrapper):
        """Test analysis with options"""
        result = await wrapper.execute_analysis(
            "cpu",
            options={"detailed": True, "metrics": ["usage", "processes"]}
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_analysis_timeout(self, wrapper):
        """Test timeout handling"""
        # Reduce timeout for faster test
        wrapper.timeout = 0.1

        with pytest.raises(AnalysisTimeoutError) as exc_info:
            await wrapper.execute_analysis("slow_category")

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_analysis_retry(self, wrapper, mocker):
        """Test retry mechanism"""
        # Mock subprocess to fail twice then succeed
        call_count = 0

        async def mock_run(cmd):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise subprocess.CalledProcessError(1, cmd, b"", b"Error")

            return subprocess.CompletedProcess(
                cmd, 0, b'{"status": "success"}', b""
            )

        mocker.patch.object(wrapper, "_run_subprocess", mock_run)

        result = await wrapper.execute_analysis("cpu")

        assert result["status"] == "success"
        assert call_count == 3  # Failed twice, succeeded third time

    @pytest.mark.asyncio
    async def test_cache_hit(self, wrapper):
        """Test cache hit scenario"""
        # First call - cache miss
        result1 = await wrapper.execute_analysis("cpu")
        stats1 = wrapper.cache.get_stats()

        # Second call - cache hit
        result2 = await wrapper.execute_analysis("cpu")
        stats2 = wrapper.cache.get_stats()

        assert result1 == result2
        assert stats2["hits"] == stats1["hits"] + 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self, wrapper):
        """Test cache expiration"""
        # Set very short TTL
        wrapper.cache.ttl = 1

        # First call
        result1 = await wrapper.execute_analysis("cpu")

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Second call - should be cache miss
        result2 = await wrapper.execute_analysis("cpu")

        stats = wrapper.cache.get_stats()
        assert stats["misses"] >= 1

    @pytest.mark.asyncio
    async def test_error_handling(self, wrapper, mocker):
        """Test error handling and recovery"""
        # Mock subprocess failure
        mocker.patch.object(
            wrapper,
            "_run_subprocess",
            side_effect=subprocess.CalledProcessError(
                1, "cmd", b"", b"Analysis failed"
            )
        )

        with pytest.raises(AnalysisExecutionError) as exc_info:
            await wrapper.execute_analysis("cpu")

        assert "failed" in str(exc_info.value).lower()
```

### Test MetricsCache

```python
# tests/test_cache.py
import pytest
import time
from cache import MetricsCache

class TestMetricsCache:
    """Unit tests for MetricsCache"""

    def test_cache_set_get(self):
        """Test basic set and get"""
        cache = MetricsCache(ttl=30)
        data = {"value": 42}

        cache.set("key1", data)
        result = cache.get("key1")

        assert result == data

    def test_cache_miss(self):
        """Test cache miss"""
        cache = MetricsCache(ttl=30)
        result = cache.get("nonexistent")

        assert result is None

    def test_cache_expiration(self):
        """Test TTL expiration"""
        cache = MetricsCache(ttl=1)
        cache.set("key1", {"value": 42})

        # Wait for expiration
        time.sleep(1.5)

        result = cache.get("key1")
        assert result is None

    def test_lru_eviction(self):
        """Test LRU eviction"""
        cache = MetricsCache(ttl=30, max_size=3)

        # Fill cache
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        cache.set("key3", {"value": 3})

        # Access key1 (make it most recently used)
        cache.get("key1")

        # Add new item - should evict key2 (least recently used)
        cache.set("key4", {"value": 4})

        assert cache.get("key1") is not None
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_stale_cache(self):
        """Test stale cache retrieval"""
        cache = MetricsCache(ttl=1, stale_threshold=10)
        cache.set("key1", {"value": 42})

        # Wait for expiration but within stale threshold
        time.sleep(1.5)

        # Normal get should return None
        result = cache.get("key1")
        assert result is None

        # Stale get should return data
        stale = cache.get_stale("key1")
        assert stale == {"value": 42}

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = MetricsCache(ttl=30)

        cache.set("key1", {"value": 1})
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
```

## Integration Tests

### Test Wrapper + Python Engine

```python
# tests/integration/test_wrapper_integration.py
import pytest
import pytest_asyncio
from pathlib import Path

class TestWrapperIntegration:
    """Integration tests for wrapper + Python engine"""

    @pytest.mark.asyncio
    async def test_real_coordinator_execution(self):
        """Test with real coordinator.py"""
        from wrapper import PythonEngineWrapper

        # Use actual coordinator
        wrapper = PythonEngineWrapper(
            engine_path=".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py"
        )

        result = await wrapper.execute_analysis("cpu")

        assert result["status"] == "success"
        assert "metrics" in result
        assert "usage_percent" in result["metrics"]

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        from wrapper import PythonEngineWrapper
        from coordinator import ResourceCoordinator

        wrapper = PythonEngineWrapper()
        coordinator = ResourceCoordinator(wrapper)

        # Execute parallel analysis
        result = await coordinator.analyze_all()

        assert result["status"] in ["success", "partial"]
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_optimization_workflow(self):
        """Test optimization workflow"""
        from wrapper import PythonEngineWrapper

        wrapper = PythonEngineWrapper()

        # Get analysis
        analysis = await wrapper.execute_analysis("cpu")

        # Generate optimization plan
        optimization = await wrapper.execute_optimize(
            categories=["cpu"],
            apply=False  # Dry run
        )

        assert optimization["status"] == "success"
        assert "recommendations" in optimization
```

### Test ResourceCoordinator

```python
# tests/integration/test_coordinator.py
import pytest
import pytest_asyncio
import asyncio
from coordinator import ResourceCoordinator

class TestResourceCoordinator:
    """Integration tests for ResourceCoordinator"""

    @pytest.mark.asyncio
    async def test_parallel_analysis(self, coordinator):
        """Test parallel category analysis"""
        result = await coordinator.analyze_selective(
            ["cpu", "memory", "disk"],
            parallel=True
        )

        assert result["status"] in ["success", "partial"]
        assert result["categories_analyzed"] >= 0

    @pytest.mark.asyncio
    async def test_prioritized_analysis(self, coordinator):
        """Test prioritized analysis execution"""
        result = await coordinator.analyze_prioritized(
            high_priority=["cpu", "memory"],
            low_priority=["battery", "thermal"]
        )

        assert result["status"] in ["success", "partial"]

    @pytest.mark.asyncio
    async def test_error_aggregation(self, coordinator, mocker):
        """Test error aggregation from multiple analyses"""
        # Mock to cause some failures
        async def mock_execute(category):
            if category == "cpu":
                raise Exception("CPU analysis failed")
            return {"status": "success", "category": category}

        mocker.patch.object(
            coordinator.wrapper,
            "execute_analysis",
            mock_execute
        )

        result = await coordinator.analyze_all()

        assert result["status"] == "partial"
        assert len(result["errors"]) > 0
        assert any(e["category"] == "cpu" for e in result["errors"])
```

## Performance Tests

### Benchmark Parallel vs Sequential

```python
# tests/performance/test_benchmarks.py
import pytest
import pytest_asyncio
import time
from coordinator import ResourceCoordinator

class TestPerformanceBenchmarks:
    """Performance benchmarks for wrapper"""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_single_analysis_performance(self, wrapper, benchmark):
        """Benchmark single analysis execution"""

        async def analyze():
            return await wrapper.execute_analysis("cpu")

        result = await benchmark(analyze)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_parallel_speedup(self, coordinator):
        """Test parallel execution speedup"""
        categories = ["cpu", "memory", "disk", "network"]

        # Sequential execution
        start_seq = time.time()
        for cat in categories:
            await coordinator.wrapper.execute_analysis(cat)
        seq_duration = time.time() - start_seq

        # Clear cache for fair comparison
        coordinator.wrapper.cache.clear()

        # Parallel execution
        start_par = time.time()
        await coordinator.analyze_selective(categories, parallel=True)
        par_duration = time.time() - start_par

        # Calculate speedup
        speedup = seq_duration / par_duration

        print(f"\nSequential: {seq_duration:.2f}s")
        print(f"Parallel: {par_duration:.2f}s")
        print(f"Speedup: {speedup:.2f}x")

        # Expect at least 2x speedup for 4 categories
        assert speedup >= 2.0

    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, wrapper):
        """Test cache performance improvement"""
        # First call - cache miss
        start_miss = time.time()
        await wrapper.execute_analysis("cpu")
        miss_duration = time.time() - start_miss

        # Second call - cache hit
        start_hit = time.time()
        await wrapper.execute_analysis("cpu")
        hit_duration = time.time() - start_hit

        # Cache should be much faster
        speedup = miss_duration / hit_duration

        print(f"\nCache miss: {miss_duration:.4f}s")
        print(f"Cache hit: {hit_duration:.4f}s")
        print(f"Speedup: {speedup:.2f}x")

        assert speedup >= 100  # Expect at least 100x speedup

    @pytest.mark.asyncio
    async def test_performance_target(self, coordinator):
        """Test 1.5-2.0s performance target"""
        categories = ["cpu", "memory", "disk"]

        start = time.time()
        result = await coordinator.analyze_selective(categories)
        duration = time.time() - start

        print(f"\nAnalysis duration: {duration:.2f}s")
        print(f"Target: 1.5-2.0s")

        # Should meet or exceed target
        assert duration <= 2.0
```

## Error Handling Tests

### Test Timeout Scenarios

```python
# tests/test_error_handling.py
import pytest
import pytest_asyncio
import asyncio
from wrapper import (
    PythonEngineWrapper,
    AnalysisTimeoutError,
    AnalysisExecutionError
)

class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_timeout_with_fallback(self, wrapper, mocker):
        """Test timeout with stale cache fallback"""
        # First call - populate cache
        await wrapper.execute_analysis("cpu")

        # Wait for expiration
        await asyncio.sleep(wrapper.cache.ttl + 1)

        # Mock timeout on fresh analysis
        async def mock_timeout(cmd):
            raise asyncio.TimeoutError()

        mocker.patch.object(wrapper, "_run_subprocess", mock_timeout)

        # Should raise timeout
        with pytest.raises(AnalysisTimeoutError):
            await wrapper.execute_analysis("cpu")

        # But stale cache should be available
        stale = wrapper.cache.get_stale("cpu")
        assert stale is not None

    @pytest.mark.asyncio
    async def test_subprocess_error_recovery(self, wrapper, mocker):
        """Test subprocess error recovery"""
        call_count = 0

        async def mock_subprocess(cmd):
            nonlocal call_count
            call_count += 1

            # Fail first time, succeed second
            if call_count == 1:
                raise subprocess.CalledProcessError(1, cmd, b"", b"Error")

            return subprocess.CompletedProcess(
                cmd, 0, b'{"status": "success"}', b""
            )

        mocker.patch.object(wrapper, "_run_subprocess", mock_subprocess)

        result = await wrapper.execute_analysis("cpu")

        assert result["status"] == "success"
        assert call_count == 2  # Retried once

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, coordinator, mocker):
        """Test handling of partial failures"""
        async def mock_selective_failure(category):
            if category in ["cpu", "memory"]:
                return {"status": "success", "category": category}
            raise Exception(f"{category} failed")

        mocker.patch.object(
            coordinator.wrapper,
            "execute_analysis",
            mock_selective_failure
        )

        result = await coordinator.analyze_all()

        assert result["status"] == "partial"
        assert len(result["results"]) == 2  # cpu and memory
        assert len(result["errors"]) == 4  # disk, network, battery, thermal
```

## Test Coverage and Quality

### Coverage Configuration

```ini
# .coveragerc
[run]
source = .
omit =
    tests/*
    */venv/*
    */virtualenv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

precision = 2
show_missing = True
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov --cov-report=html

# Run specific category
pytest tests/test_wrapper.py -v

# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Run with timeout protection
pytest tests/ -v --timeout=30
```

---

**Status**: ✅ Active (450 lines)
**Last Updated**: 2025-11-29
