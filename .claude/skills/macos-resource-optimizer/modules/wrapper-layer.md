# Wrapper Layer Architecture

PythonEngineWrapper implementation for coordinating existing macOS optimizer Python agents through subprocess execution with timeout management and error handling.

## Implementation Status

⚠️ **IMPORTANT**: This document describes the **conceptual wrapper architecture**. The actual implementation uses **direct UV script execution** via Bash() tool.

**Current Implementation** (as of 2025-11-30):
- ✅ 12 UV scripts as standalone executables
- ✅ Bash("uv run [script].py") execution pattern
- ✅ No wrapper class needed (direct CLI execution)
- ✅ JSON output parsing from stdout
- 🔄 2/8 manager agents use Bash(uv run) pattern
- 🔄 Performance benchmarking in progress

**This Document Describes**:
- Conceptual PythonEngineWrapper class design
- Subprocess execution patterns (theoretical)
- Error handling strategies
- Integration patterns with coordinator.py (conceptual)

**For Actual Implementation**: See agent patterns:
```python
# Manager agent pattern
Bash(
    command="uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json",
    description="Analyze CPU usage"
)
```

---

## Overview

**Purpose**: Execute .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py without modification through async subprocess wrapper.

**Design Principle**: Additive integration - zero changes to existing Python codebase.

**Key Components**:
- `PythonEngineWrapper` - Main wrapper class
- `AnalysisExecutor` - Subprocess management
- `ErrorHandler` - Exception handling and recovery
- `ResultParser` - JSON result parsing

## PythonEngineWrapper Class

### Core Implementation

```python
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio
import subprocess
import json
import time
from dataclasses import dataclass

class PythonEngineWrapper:
    """
    Wrapper for .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py

    Provides async interface to existing Python engine without modification.
    Includes timeout protection, caching, and error handling.
    """

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10,
        cache_ttl: int = 30,
        retry_attempts: int = 3,
        retry_backoff: float = 1.0
    ):
        """
        Initialize wrapper with configuration

        Args:
            engine_path: Path to coordinator.py
            timeout: Subprocess timeout in seconds
            cache_ttl: Cache time-to-live in seconds
            retry_attempts: Number of retry attempts
            retry_backoff: Backoff multiplier for retries
        """
        self.engine_path = Path(engine_path)
        self.timeout = timeout
        self.cache = MetricsCache(ttl=cache_ttl)
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self.monitor = PerformanceMonitor()

        # Validate engine exists
        if not self.engine_path.exists():
            raise FileNotFoundError(f"Engine not found: {self.engine_path}")

    async def execute_analysis(
        self,
        category: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute single category analysis with caching and retry

        Args:
            category: Analysis category (cpu, memory, disk, etc.)
            options: Additional analysis options

        Returns:
            Analysis results dictionary

        Raises:
            AnalysisTimeoutError: Analysis exceeded timeout
            AnalysisExecutionError: Analysis failed to execute
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._cache_key(category, options)
        cached = self.cache.get(cache_key)
        if cached:
            duration = time.time() - start_time
            self.monitor.record_analysis(duration, cached=True, error=False)
            return cached

        # Execute with retry
        result = await self._execute_with_retry(category, options)

        # Cache and monitor
        self.cache.set(cache_key, result)
        duration = time.time() - start_time
        self.monitor.record_analysis(duration, cached=False, error=False)

        return result

    async def _execute_with_retry(
        self,
        category: str,
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute analysis with exponential backoff retry"""
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                return await self._execute_once(category, options)
            except AnalysisExecutionError as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    delay = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries failed
        self.monitor.record_analysis(0, cached=False, error=True)
        raise last_error

    async def _execute_once(
        self,
        category: str,
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute analysis once (no retry)"""
        # Build command
        cmd = self._build_command(category, options)

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._run_subprocess(cmd),
                timeout=self.timeout
            )

            # Parse JSON result
            return self._parse_result(result.stdout)

        except asyncio.TimeoutError:
            raise AnalysisTimeoutError(
                f"{category} analysis exceeded {self.timeout}s timeout"
            )
        except subprocess.CalledProcessError as e:
            raise AnalysisExecutionError(
                f"Failed to analyze {category}: {e.stderr.decode()}"
            )
        except json.JSONDecodeError as e:
            raise ResultParseError(
                f"Failed to parse {category} results: {e}"
            )

    def _build_command(
        self,
        category: str,
        options: Optional[Dict[str, Any]]
    ) -> str:
        """Build coordinator.py command"""
        cmd_parts = [
            "uv run",
            str(self.engine_path),
            "--analyze",
            f"--category={category}"
        ]

        # Add optional parameters
        if options:
            if "detailed" in options and options["detailed"]:
                cmd_parts.append("--detailed")
            if "format" in options:
                cmd_parts.append(f"--format={options['format']}")
            if "metrics" in options:
                metrics_str = ",".join(options["metrics"])
                cmd_parts.append(f"--metrics={metrics_str}")

        return " ".join(cmd_parts)

    async def _run_subprocess(self, cmd: str) -> subprocess.CompletedProcess:
        """Run subprocess asynchronously"""
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                stdout,
                stderr
            )

        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout, stderr
        )

    def _parse_result(self, stdout: bytes) -> Dict[str, Any]:
        """Parse JSON result from coordinator.py"""
        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError as e:
            # Log raw output for debugging
            print(f"Failed to parse: {stdout.decode()}")
            raise ResultParseError(f"Invalid JSON: {e}")

    def _cache_key(
        self,
        category: str,
        options: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key from category and options"""
        if not options:
            return category

        # Sort options for consistent key
        opts_str = json.dumps(options, sort_keys=True)
        return f"{category}:{opts_str}"

    async def execute_all(self) -> Dict[str, Any]:
        """Execute full system analysis"""
        cmd = f"uv run {self.engine_path} --analyze-all"

        try:
            result = await asyncio.wait_for(
                self._run_subprocess(cmd),
                timeout=self.timeout * 2  # 2x timeout for full analysis
            )
            return self._parse_result(result.stdout)
        except asyncio.TimeoutError:
            raise AnalysisTimeoutError(
                f"Full analysis exceeded {self.timeout * 2}s timeout"
            )

    async def execute_optimize(
        self,
        categories: List[str],
        apply: bool = False
    ) -> Dict[str, Any]:
        """Execute optimization mode"""
        categories_str = ",".join(categories)
        cmd_parts = [
            "uv run",
            str(self.engine_path),
            "--optimize",
            f"--categories={categories_str}"
        ]

        if apply:
            cmd_parts.append("--apply")

        cmd = " ".join(cmd_parts)

        try:
            result = await asyncio.wait_for(
                self._run_subprocess(cmd),
                timeout=self.timeout * 3  # 3x timeout for optimization
            )
            return self._parse_result(result.stdout)
        except asyncio.TimeoutError:
            raise AnalysisTimeoutError(
                f"Optimization exceeded {self.timeout * 3}s timeout"
            )
```

## Exception Classes

```python
class WrapperError(Exception):
    """Base exception for wrapper errors"""
    pass

class AnalysisTimeoutError(WrapperError):
    """Analysis exceeded timeout"""
    pass

class AnalysisExecutionError(WrapperError):
    """Analysis failed to execute"""
    pass

class ResultParseError(WrapperError):
    """Failed to parse analysis results"""
    pass
```

## Performance Monitor

```python
@dataclass
class AnalysisMetrics:
    """Metrics for single analysis"""
    category: str
    duration: float
    cached: bool
    error: bool
    timestamp: float

class PerformanceMonitor:
    """Track wrapper performance metrics"""

    def __init__(self):
        self.metrics: List[AnalysisMetrics] = []
        self.aggregated = {
            "total_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "avg_duration": 0.0,
            "avg_cached_duration": 0.0,
            "avg_uncached_duration": 0.0
        }

    def record_analysis(
        self,
        duration: float,
        cached: bool,
        error: bool,
        category: Optional[str] = None
    ):
        """Record single analysis metrics"""
        metric = AnalysisMetrics(
            category=category or "unknown",
            duration=duration,
            cached=cached,
            error=error,
            timestamp=time.time()
        )

        self.metrics.append(metric)
        self._update_aggregated(metric)

    def _update_aggregated(self, metric: AnalysisMetrics):
        """Update aggregated statistics"""
        self.aggregated["total_analyses"] += 1

        if metric.cached:
            self.aggregated["cache_hits"] += 1
        else:
            self.aggregated["cache_misses"] += 1

        if metric.error:
            self.aggregated["errors"] += 1

        # Update rolling averages
        total = self.aggregated["total_analyses"]
        avg = self.aggregated["avg_duration"]
        self.aggregated["avg_duration"] = (
            (avg * (total - 1) + metric.duration) / total
        )

        if metric.cached:
            hits = self.aggregated["cache_hits"]
            avg_cached = self.aggregated["avg_cached_duration"]
            self.aggregated["avg_cached_duration"] = (
                (avg_cached * (hits - 1) + metric.duration) / hits
            )
        else:
            misses = self.aggregated["cache_misses"]
            avg_uncached = self.aggregated["avg_uncached_duration"]
            self.aggregated["avg_uncached_duration"] = (
                (avg_uncached * (misses - 1) + metric.duration) / misses
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_hit_rate = 0.0
        if self.aggregated["total_analyses"] > 0:
            cache_hit_rate = (
                self.aggregated["cache_hits"] /
                self.aggregated["total_analyses"]
            )

        error_rate = 0.0
        if self.aggregated["total_analyses"] > 0:
            error_rate = (
                self.aggregated["errors"] /
                self.aggregated["total_analyses"]
            )

        return {
            **self.aggregated,
            "cache_hit_rate": cache_hit_rate,
            "error_rate": error_rate,
            "speedup": self._calculate_speedup()
        }

    def _calculate_speedup(self) -> float:
        """Calculate speedup from caching"""
        if self.aggregated["cache_misses"] == 0:
            return 1.0

        uncached = self.aggregated["avg_uncached_duration"]
        overall = self.aggregated["avg_duration"]

        if overall == 0:
            return 1.0

        return uncached / overall
```

## Integration with coordinator.py

### Expected coordinator.py Interface

```python
# .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py (existing, unchanged)

def main():
    """Main entry point for coordinator"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--analyze-all", action="store_true")
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--category", type=str)
    parser.add_argument("--categories", type=str)
    parser.add_argument("--detailed", action="store_true")
    parser.add_argument("--format", type=str, default="json")
    parser.add_argument("--metrics", type=str)
    parser.add_argument("--apply", action="store_true")

    args = parser.parse_args()

    if args.analyze:
        result = analyze_category(args.category, args.detailed)
        print(json.dumps(result))
    elif args.analyze_all:
        result = analyze_all_categories()
        print(json.dumps(result))
    elif args.optimize:
        categories = args.categories.split(",")
        result = optimize_categories(categories, args.apply)
        print(json.dumps(result))
```

### Expected JSON Output Format

```json
{
  "status": "success",
  "category": "cpu",
  "timestamp": 1701234567.89,
  "metrics": {
    "usage_percent": 45.2,
    "user_percent": 30.1,
    "system_percent": 15.1,
    "idle_percent": 54.8,
    "processes": [
      {"pid": 1234, "name": "process1", "cpu_percent": 12.5},
      {"pid": 5678, "name": "process2", "cpu_percent": 8.3}
    ]
  },
  "recommendations": [
    {
      "type": "optimization",
      "priority": "high",
      "description": "High CPU usage detected",
      "action": "Terminate resource-intensive processes"
    }
  ]
}
```

## Usage Examples

### Basic Analysis

```python
# Initialize wrapper
wrapper = PythonEngineWrapper()

# Execute single category
result = await wrapper.execute_analysis("cpu")
print(f"CPU usage: {result['metrics']['usage_percent']}%")
```

### Detailed Analysis

```python
# Execute with options
result = await wrapper.execute_analysis(
    "memory",
    options={
        "detailed": True,
        "metrics": ["usage", "swap", "pressure"]
    }
)
```

### Full System Analysis

```python
# Execute all categories
result = await wrapper.execute_all()
for category, data in result.items():
    print(f"{category}: {data['status']}")
```

### Optimization Mode

```python
# Generate optimization plan
result = await wrapper.execute_optimize(
    categories=["cpu", "memory"],
    apply=False  # Dry run
)

# Apply optimizations
result = await wrapper.execute_optimize(
    categories=["cpu", "memory"],
    apply=True  # Execute changes
)
```

### Error Handling

```python
try:
    result = await wrapper.execute_analysis("cpu")
except AnalysisTimeoutError:
    # Try stale cache
    stale = wrapper.cache.get_stale("cpu")
    if stale:
        result = {"data": stale, "stale": True}
except AnalysisExecutionError as e:
    # Log and fallback
    print(f"Analysis failed: {e}")
    result = {"status": "error", "message": str(e)}
```

## Testing Patterns

### Mock Coordinator

```python
@pytest.fixture
async def mock_coordinator(tmp_path):
    """Mock coordinator.py for testing"""
    script = tmp_path / "coordinator.py"
    script.write_text("""
import sys
import json

if "--analyze" in sys.argv:
    result = {
        "status": "success",
        "category": "cpu",
        "metrics": {"usage_percent": 45.2}
    }
    print(json.dumps(result))
""")

    return script

@pytest.mark.asyncio
async def test_wrapper_with_mock(mock_coordinator):
    """Test wrapper with mock coordinator"""
    wrapper = PythonEngineWrapper(engine_path=str(mock_coordinator))
    result = await wrapper.execute_analysis("cpu")
    assert result["status"] == "success"
```

### Performance Benchmarks

```python
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_wrapper_performance(wrapper, benchmark):
    """Benchmark wrapper execution"""
    result = await benchmark(wrapper.execute_analysis, "cpu")
    assert result["status"] == "success"
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: AnalysisTimeoutError

**Symptom**: "CPU analysis exceeded 10s timeout"

**Root Causes**:
1. System overload (high CPU/memory usage)
2. Slow disk I/O interfering with subprocess
3. Too many concurrent analyses

**Solutions**:

```python
# Solution 1: Increase timeout for specific category
wrapper = PythonEngineWrapper(timeout=15)

# Solution 2: Reduce parallel load
# Instead of: asyncio.gather(cpu, memory, disk, network, battery, thermal)
# Use: asyncio.gather(cpu, memory, disk)  # Analyze in batches

# Solution 3: Check system resources
import psutil
if psutil.virtual_memory().percent > 85:
    print("System memory high, timeout may occur")

# Solution 4: Use stale cache as fallback
try:
    result = await wrapper.execute_analysis("cpu")
except AnalysisTimeoutError:
    stale = wrapper.cache.get_stale("cpu")
    if stale:
        result = {"data": stale, "stale": True, "warning": "Timeout"}
```

#### Issue 2: ResultParseError

**Symptom**: "Failed to parse cpu results: Invalid JSON"

**Root Causes**:
1. coordinator.py outputting non-JSON data
2. Stderr mixed with stdout
3. Partial output before crash

**Solutions**:

```python
# Solution 1: Debug output to see raw result
async def debug_execute(wrapper, category):
    cmd = wrapper._build_command(category, None)
    print(f"Executing: {cmd}")

    result = await wrapper._run_subprocess(cmd)
    print(f"Stdout: {result.stdout.decode()[:500]}")
    print(f"Stderr: {result.stderr.decode()[:500]}")
    print(f"Return code: {result.returncode}")

# Solution 2: Check coordinator.py output format
# Verify coordinator.py outputs valid JSON to stdout

# Solution 3: Validate JSON before parsing
def safe_parse(stdout_bytes):
    text = stdout_bytes.decode()
    # Remove any debug output before JSON
    if '[' in text or '{' in text:
        text = text[text.index('{'):]
    return json.loads(text)
```

#### Issue 3: Cache Not Effective

**Symptom**: "Cache hit rate: 0.0% (expected 60%)"

**Root Causes**:
1. TTL too short (30s)
2. Different options for same category
3. Cache being cleared prematurely

**Solutions**:

```python
# Solution 1: Increase TTL
wrapper = PythonEngineWrapper(
    cache_ttl=60  # Increase from 30 to 60 seconds
)

# Solution 2: Use consistent options
# Bad: Same category with different options each time
await wrapper.execute_analysis("cpu", {"detailed": True})
await wrapper.execute_analysis("cpu", {"detailed": False})  # Cache miss

# Good: Use same options or no options
await wrapper.execute_analysis("cpu")
await wrapper.execute_analysis("cpu")  # Cache hit

# Solution 3: Check cache stats
stats = wrapper.monitor.get_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Avg duration: {stats['avg_duration']:.3f}s")
```

#### Issue 4: Wrapper Process Consuming Too Much Memory

**Symptom**: "Memory usage growing over time"

**Root Causes**:
1. Metrics list growing unbounded
2. Cached results accumulating
3. Subprocess handles not closing

**Solutions**:

```python
# Solution 1: Limit metrics history
class PerformanceMonitor:
    def __init__(self, max_history=1000):
        self.metrics: List[AnalysisMetrics] = []
        self.max_history = max_history

    def record_analysis(self, ...):
        self.metrics.append(metric)
        # Keep only recent metrics
        if len(self.metrics) > self.max_history:
            self.metrics = self.metrics[-self.max_history:]

# Solution 2: Clear cache periodically
async def periodic_cache_clear():
    while True:
        await asyncio.sleep(3600)  # Every hour
        wrapper.cache.clear()

# Solution 3: Use context manager for cleanup
class ManagedWrapper(PythonEngineWrapper):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.cache.clear()
        self.metrics.clear()

# Usage:
async with ManagedWrapper() as wrapper:
    result = await wrapper.execute_analysis("cpu")
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugWrapper(PythonEngineWrapper):
    async def _run_subprocess(self, cmd: str):
        logger.debug(f"Running command: {cmd}")
        start = time.time()

        result = await super()._run_subprocess(cmd)

        duration = time.time() - start
        logger.debug(f"Command completed in {duration:.3f}s")
        logger.debug(f"Stdout length: {len(result.stdout)} bytes")
        logger.debug(f"Stderr length: {len(result.stderr)} bytes")

        return result
```

## Best Practices

### 1. Initialize Once, Reuse

**Bad**:
```python
# Creating new wrapper for each analysis
for category in categories:
    wrapper = PythonEngineWrapper()
    result = await wrapper.execute_analysis(category)
```

**Good**:
```python
# Create once, reuse across analyses
wrapper = PythonEngineWrapper()
for category in categories:
    result = await wrapper.execute_analysis(category)
```

### 2. Use Selective Timeout

**Bad**:
```python
# Same timeout for all categories
wrapper = PythonEngineWrapper(timeout=10)
```

**Good**:
```python
# Category-specific timeouts in config
timeouts = {
    "cpu": 3,
    "memory": 3,
    "disk": 10,  # Slower I/O
    "network": 10,
    "battery": 5,
    "thermal": 5
}
```

### 3. Handle Errors Gracefully

**Bad**:
```python
# Crashes on any error
result = await wrapper.execute_analysis("cpu")
```

**Good**:
```python
# Graceful error handling
try:
    result = await wrapper.execute_analysis("cpu")
except AnalysisTimeoutError:
    stale = wrapper.cache.get_stale("cpu")
    result = {"data": stale, "stale": True} if stale else {"error": "timeout"}
except AnalysisExecutionError as e:
    logger.error(f"Analysis failed: {e}")
    result = {"error": str(e)}
```

### 4. Monitor Performance

**Good Practice**:
```python
# Regularly check performance metrics
stats = wrapper.monitor.get_stats()

if stats['cache_hit_rate'] < 0.5:
    logger.warning(f"Low cache hit rate: {stats['cache_hit_rate']:.1%}")
    # Consider increasing TTL or reducing analysis frequency

if stats['error_rate'] > 0.05:
    logger.error(f"High error rate: {stats['error_rate']:.1%}")
    # Investigate subprocess failures

if stats['avg_duration'] > 2.0:
    logger.warning(f"Slow analyses: {stats['avg_duration']:.2f}s avg")
    # Consider optimization or more resources
```

### 5. Cache Management

**Good Practice**:
```python
# Implement cache warming
async def warm_cache(wrapper, categories):
    """Pre-populate cache with latest data"""
    tasks = [wrapper.execute_analysis(cat) for cat in categories]
    results = await asyncio.gather(*tasks)
    logger.info(f"Cache warmed with {len(results)} entries")

# Call during initialization
await warm_cache(wrapper, ["cpu", "memory", "disk", "network", "battery", "thermal"])
```

---

**Status**: ✅ Active (750 lines, comprehensive)
**Last Updated**: 2025-11-29
