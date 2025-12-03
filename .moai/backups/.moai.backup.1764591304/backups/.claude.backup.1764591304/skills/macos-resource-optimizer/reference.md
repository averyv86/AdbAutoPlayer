# API Reference and External Resources

Complete API reference for macOS Resource Optimizer wrapper layer components, configuration options, and troubleshooting guide.

## PythonEngineWrapper API

### Constructor

```python
PythonEngineWrapper(
    engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
    timeout: int = 10,
    cache_ttl: int = 30,
    retry_attempts: int = 3,
    retry_backoff: float = 1.0
)
```

**Parameters**:
- `engine_path` - Path to coordinator.py (absolute or relative)
- `timeout` - Subprocess timeout in seconds (default: 10)
- `cache_ttl` - Cache time-to-live in seconds (default: 30)
- `retry_attempts` - Number of retry attempts (default: 3)
- `retry_backoff` - Exponential backoff multiplier (default: 1.0)

**Example**:
```python
wrapper = PythonEngineWrapper(
    engine_path="/absolute/path/to/coordinator.py",
    timeout=15,
    cache_ttl=60
)
```

### Methods

#### execute_analysis()

```python
async def execute_analysis(
    category: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

Execute single category analysis with caching and retry.

**Parameters**:
- `category` - Analysis category (cpu, memory, disk, network, battery, thermal)
- `options` - Optional analysis parameters
  - `detailed` (bool) - Enable detailed analysis
  - `format` (str) - Output format (json, yaml, etc.)
  - `metrics` (List[str]) - Specific metrics to analyze

**Returns**: Analysis results dictionary

**Raises**:
- `AnalysisTimeoutError` - Analysis exceeded timeout
- `AnalysisExecutionError` - Analysis execution failed
- `ResultParseError` - Failed to parse results

**Example**:
```python
result = await wrapper.execute_analysis(
    "cpu",
    options={"detailed": True, "metrics": ["usage", "processes"]}
)
```

#### execute_all()

```python
async def execute_all() -> Dict[str, Any]
```

Execute full system analysis (all categories).

**Returns**: Aggregated analysis results

**Timeout**: 2× normal timeout (20s default)

**Example**:
```python
result = await wrapper.execute_all()
print(f"Analyzed {len(result['categories'])} categories")
```

#### execute_optimize()

```python
async def execute_optimize(
    categories: List[str],
    apply: bool = False
) -> Dict[str, Any]
```

Execute optimization mode.

**Parameters**:
- `categories` - Categories to optimize
- `apply` - Apply changes (default: False for dry-run)

**Returns**: Optimization plan with recommendations

**Timeout**: 3× normal timeout (30s default)

**Example**:
```python
# Dry run
plan = await wrapper.execute_optimize(["cpu", "memory"], apply=False)

# Apply optimizations
result = await wrapper.execute_optimize(["cpu", "memory"], apply=True)
```

## MetricsCache API

### Constructor

```python
MetricsCache(
    ttl: int = 30,
    max_size: int = 50,
    stale_threshold: int = 300
)
```

**Parameters**:
- `ttl` - Time-to-live in seconds (default: 30)
- `max_size` - Maximum cache entries (default: 50)
- `stale_threshold` - Stale cache threshold in seconds (default: 300)

### Methods

#### get()

```python
def get(key: str) -> Optional[Dict[str, Any]]
```

Retrieve cached value if not expired.

**Returns**: Cached data or None

#### get_stale()

```python
def get_stale(
    key: str,
    max_age: Optional[int] = None
) -> Optional[Dict[str, Any]]
```

Retrieve potentially stale cache (expired but recent).

**Parameters**:
- `key` - Cache key
- `max_age` - Maximum age in seconds (default: stale_threshold)

**Returns**: Stale cached data or None

#### set()

```python
def set(key: str, data: Dict[str, Any]) -> None
```

Store value with timestamp.

#### get_stats()

```python
def get_stats() -> Dict[str, Any]
```

Get cache statistics.

**Returns**:
```python
{
    "hits": 150,
    "misses": 50,
    "total_requests": 200,
    "hit_rate": 0.75,
    "evictions": 10,
    "stale_hits": 5,
    "size": 45,
    "capacity": 50
}
```

## ResourceCoordinator API

### Constructor

```python
ResourceCoordinator(wrapper: PythonEngineWrapper)
```

**Parameters**:
- `wrapper` - PythonEngineWrapper instance

### Methods

#### analyze_all()

```python
async def analyze_all() -> Dict[str, Any]
```

Execute all analyses in parallel.

**Returns**:
```python
{
    "status": "success",  # or "partial", "failed"
    "results": {
        "cpu": {...},
        "memory": {...},
        ...
    },
    "errors": [],
    "warnings": [],
    "timestamp": 1701234567.89,
    "categories_analyzed": 6,
    "categories_failed": 0
}
```

#### analyze_selective()

```python
async def analyze_selective(
    categories: List[str],
    parallel: bool = True
) -> Dict[str, Any]
```

Execute specific category analyses.

**Parameters**:
- `categories` - List of categories to analyze
- `parallel` - Execute in parallel (default: True)

**Returns**: Aggregated results

#### analyze_prioritized()

```python
async def analyze_prioritized(
    high_priority: List[str],
    low_priority: List[str]
) -> Dict[str, Any]
```

Execute analyses with priority levels.

**Parameters**:
- `high_priority` - High priority categories (execute first)
- `low_priority` - Low priority categories (execute after)

**Returns**: Aggregated results

## Configuration Options

### Category Configuration

```json
{
  "category_timeouts": {
    "cpu": {
      "priority": "high",
      "timeout": 5,
      "cache_ttl": 20,
      "enabled": true
    }
  }
}
```

**Fields**:
- `priority` - "high", "medium", "low"
- `timeout` - Category-specific timeout in seconds
- `cache_ttl` - Category-specific cache TTL
- `enabled` - Enable/disable category analysis

### Monitoring Configuration

```json
{
  "monitoring": {
    "enabled": true,
    "metrics_retention": 1000,
    "performance_warnings": true,
    "warn_threshold_seconds": 2.5
  }
}
```

**Fields**:
- `enabled` - Enable performance monitoring
- `metrics_retention` - Number of metrics to retain
- `performance_warnings` - Warn on slow analyses
- `warn_threshold_seconds` - Warning threshold

### Error Handling Configuration

```json
{
  "error_handling": {
    "graceful_degradation": true,
    "use_stale_cache_on_timeout": true,
    "partial_results_acceptable": true,
    "log_errors": true,
    "error_log_path": ".moai/logs/macos-optimizer-errors.log"
  }
}
```

**Fields**:
- `graceful_degradation` - Continue on errors
- `use_stale_cache_on_timeout` - Fallback to stale cache
- `partial_results_acceptable` - Accept partial results
- `log_errors` - Enable error logging
- `error_log_path` - Error log file path

## Exception Reference

### WrapperError

Base exception for all wrapper errors.

```python
class WrapperError(Exception):
    """Base exception for wrapper errors"""
    pass
```

### AnalysisTimeoutError

Analysis exceeded timeout.

```python
class AnalysisTimeoutError(WrapperError):
    """Analysis exceeded timeout"""
    pass
```

**Example**:
```python
try:
    result = await wrapper.execute_analysis("cpu")
except AnalysisTimeoutError as e:
    print(f"Analysis timed out: {e}")
    # Fallback to stale cache
    result = wrapper.cache.get_stale("cpu")
```

### AnalysisExecutionError

Analysis failed to execute.

```python
class AnalysisExecutionError(WrapperError):
    """Analysis failed to execute"""
    pass
```

**Example**:
```python
try:
    result = await wrapper.execute_analysis("cpu")
except AnalysisExecutionError as e:
    print(f"Analysis failed: {e}")
    # Log error and continue
```

### ResultParseError

Failed to parse analysis results.

```python
class ResultParseError(WrapperError):
    """Failed to parse analysis results"""
    pass
```

## Troubleshooting Guide

### Analysis Timeout

**Symptom**: `AnalysisTimeoutError` raised frequently

**Causes**:
- Slow system performance
- Network latency (for network analysis)
- Heavy system load

**Solutions**:
1. Increase timeout:
   ```python
   wrapper = PythonEngineWrapper(timeout=20)
   ```

2. Use stale cache fallback:
   ```python
   try:
       result = await wrapper.execute_analysis("cpu")
   except AnalysisTimeoutError:
       result = wrapper.cache.get_stale("cpu")
   ```

3. Adjust category-specific timeouts:
   ```json
   {
     "category_timeouts": {
       "disk": {"timeout": 15}
     }
   }
   ```

### Low Cache Hit Rate

**Symptom**: Cache hit rate <40%

**Causes**:
- TTL too short for usage pattern
- High variability in metrics
- Infrequent repeated analyses

**Solutions**:
1. Increase TTL:
   ```python
   wrapper.cache.ttl = 60  # Increase to 60s
   ```

2. Use category-specific TTLs:
   ```json
   {
     "category_timeouts": {
       "battery": {"cache_ttl": 120}
     }
   }
   ```

3. Increase cache size:
   ```python
   wrapper.cache.max_size = 100
   ```

### Subprocess Execution Errors

**Symptom**: `AnalysisExecutionError` with subprocess failures

**Causes**:
- coordinator.py not found
- Python interpreter issues
- Missing dependencies

**Solutions**:
1. Verify coordinator.py path:
   ```bash
   ls -la .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py
   ```

2. Test coordinator.py directly:
   ```bash
   python .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py --help
   uv run .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py --analyze --category=cpu
   ```

3. Check dependencies:
   ```bash
   cd .claude/skills/macos-resource-optimizer/.data
   pip list
   ```

### Poor Parallel Performance

**Symptom**: Parallel execution not much faster than sequential

**Causes**:
- Python GIL limitations
- I/O-bound analyses not benefiting
- Shared resource contention

**Solutions**:
1. Reduce concurrent analyses:
   ```python
   coordinator = ResourceCoordinator(wrapper)
   # Analyze in batches of 3 instead of 6
   ```

2. Use prioritized execution:
   ```python
   result = await coordinator.analyze_prioritized(
       high_priority=["cpu", "memory"],
       low_priority=["battery", "thermal"]
   )
   ```

3. Monitor system resources during parallel execution

## External Resources

### Python asyncio Documentation
- [asyncio — Asynchronous I/O](https://docs.python.org/3/library/asyncio.html)
- [asyncio.gather()](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)
- [asyncio subprocess](https://docs.python.org/3/library/asyncio-subprocess.html)

### pytest-asyncio Documentation
- [pytest-asyncio GitHub](https://github.com/pytest-dev/pytest-asyncio)
- [Async Testing Guide](https://pytest-asyncio.readthedocs.io/)

### MoAI-ADK Resources
- [SPEC-First TDD](../moai-foundation-core/modules/spec-first-tdd.md)
- [Delegation Patterns](../moai-foundation-core/modules/delegation-patterns.md)
- [TRUST 5 Framework](../moai-foundation-core/modules/trust-5-framework.md)

### Performance Optimization
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [asyncio Performance](https://docs.python.org/3/library/asyncio-dev.html#performance)
- [Caching Strategies](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))

---

**Version**: 1.0.0
**Last Updated**: 2025-11-29
**Status**: ✅ Active (400 lines)
