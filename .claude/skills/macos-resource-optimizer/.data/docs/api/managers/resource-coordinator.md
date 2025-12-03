# manager-resource-coordinator API

## Overview

Main orchestrator for parallel 6-category resource analysis. Coordinates simultaneous execution of all expert optimizers (CPU, memory, disk, network, battery, thermal) and aggregates results.

**Key Features**:
- Parallel execution of 6 category analyses
- Built-in caching with configurable TTL
- Performance metrics tracking
- Error recovery and fallback handling
- JSON output format

## Classes

### ResourceCoordinator

Main coordinator class for managing parallel resource analysis.

```python
class ResourceCoordinator:
    """Orchestrates parallel 6-category resource analysis."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        cache_enabled: bool = True,
        cache_ttl: int = 30,
        timeout: int = 10
    ):
        """
        Initialize resource coordinator.

        Args:
            engine_path: Path to coordinator.py subprocess
            cache_enabled: Enable MetricsCache for result caching (default: True)
            cache_ttl: Cache TTL in seconds (default: 30, range: 5-300)
            timeout: Subprocess timeout in seconds (default: 10, range: 5-60)

        Raises:
            FileNotFoundError: If coordinator.py not found
            PermissionError: If unable to execute coordinator.py
            ValueError: If timeout < 5 or cache_ttl invalid

        Example:
            >>> coordinator = ResourceCoordinator(cache_ttl=60)
            >>> # Start using coordinator...
        """
```

### MetricsCache

Internal cache system for coordinator results.

```python
class MetricsCache:
    """In-memory cache for coordinator results with TTL."""

    def __init__(self, ttl_seconds: int = 30):
        """
        Initialize metrics cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default: 30)
        """

    def get(self, key: str) -> Optional[Dict]:
        """Get cached result if not expired."""

    def set(self, key: str, value: Dict) -> None:
        """Store result in cache."""

    def clear(self) -> None:
        """Clear all cached entries."""

    def hit_rate(self) -> float:
        """Return cache hit rate percentage (0.0-100.0)."""
```

## Methods

### coordinate_analysis

Execute parallel analysis across all 6 categories.

```python
async def coordinate_analysis(
    self,
    categories: Optional[List[str]] = None,
    use_cache: bool = True,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute parallel analysis across resource categories.

    Launches 6 parallel subprocess calls to coordinator.py, each handling
    one resource category. Results are aggregated into a single response.

    Args:
        categories: List of categories to analyze.
                   If None, analyzes all: ["cpu", "memory", "disk",
                                           "network", "battery", "thermal"]
                   Valid values: "cpu", "memory", "disk", "network",
                                "battery", "thermal"
        use_cache: Use cached results if available (default: True).
                   If False, forces fresh analysis.
        timeout: Override default timeout (in seconds). Range: 5-60.
                If None, uses coordinator's default timeout.

    Returns:
        Dictionary with structure:
        {
            "status": "success" | "partial" | "error",
            "execution_time_seconds": float,
            "cache_hit_rate": float,  # Percentage 0-100
            "timestamp": "ISO 8601 datetime",
            "categories": {
                "cpu": {
                    "usage_percent": float,
                    "core_count": int,
                    "per_core_usage": [float, ...],
                    "temperature": float,
                    "frequency_mhz": float,
                    "throttling_detected": bool
                },
                "memory": {
                    "usage_percent": float,
                    "available_gb": float,
                    "used_gb": float,
                    "swap_percent": float,
                    "pressure_level": "normal" | "moderate" | "high"
                },
                "disk": {
                    "usage_percent": float,
                    "total_gb": float,
                    "used_gb": float,
                    "free_gb": float,
                    "read_speed_mbs": float,
                    "write_speed_mbs": float
                },
                "network": {
                    "download_mbps": float,
                    "upload_mbps": float,
                    "latency_ms": float,
                    "packet_loss_percent": float,
                    "connected_devices": int
                },
                "battery": {
                    "percentage": float,
                    "health_percent": float,
                    "temperature": float,
                    "charging": bool,
                    "time_remaining_minutes": int,
                    "cycle_count": int
                },
                "thermal": {
                    "cpu_temp": float,
                    "gpu_temp": Optional[float],
                    "fan_rpm": int,
                    "throttling_active": bool,
                    "thermal_pressure": "normal" | "elevated" | "critical"
                }
            },
            "failed_categories": [str, ...]  # If status == "partial"
        }

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator.py fails
        PermissionError: If unable to execute subprocess
        ValueError: If invalid category specified

    Performance:
        - Full analysis (all 6 categories): 1.5-2.5s
        - With cache (60% hit rate): 1.5-1.8s
        - Single category: 0.3-0.5s
        - Parallel speedup: ~6x vs sequential

    Examples:
        >>> coordinator = ResourceCoordinator()
        >>>
        >>> # Full analysis with caching
        >>> result = await coordinator.coordinate_analysis()
        >>> print(f"CPU: {result['categories']['cpu']['usage_percent']}%")
        CPU: 45.2%
        >>> print(f"Time: {result['execution_time_seconds']}s")
        Time: 1.8s
        >>>
        >>> # Selective analysis (CPU + Thermal only)
        >>> result = await coordinator.coordinate_analysis(
        ...     categories=["cpu", "thermal"]
        ... )
        >>>
        >>> # Force fresh analysis (bypass cache)
        >>> result = await coordinator.coordinate_analysis(use_cache=False)
        >>>
        >>> # Custom timeout
        >>> result = await coordinator.coordinate_analysis(timeout=20)
        >>>
        >>> # Check cache effectiveness
        >>> print(f"Cache hit rate: {result['cache_hit_rate']}%")
        Cache hit rate: 67.3%
    """
```

### get_coordinator_status

Check coordinator subprocess status and connectivity.

```python
async def get_coordinator_status(self) -> Dict[str, Any]:
    """
    Check coordinator.py subprocess status.

    Returns:
        {
            "status": "running" | "stopped" | "error",
            "engine_path": str,
            "version": str,
            "last_execution": "ISO 8601 datetime" | None,
            "uptime_seconds": float,
            "process_id": int | None,
            "memory_mb": float,
            "cpu_percent": float
        }

    Raises:
        SubprocessError: If unable to check status

    Example:
        >>> status = await coordinator.get_coordinator_status()
        >>> print(f"Coordinator: {status['status']}")
        Coordinator: running
    """
```

### get_cache_stats

Get cache performance statistics.

```python
def get_cache_stats(self) -> Dict[str, Any]:
    """
    Get cache performance metrics.

    Returns:
        {
            "enabled": bool,
            "total_entries": int,
            "hit_count": int,
            "miss_count": int,
            "hit_rate": float,  # Percentage 0-100
            "memory_mb": float,
            "ttl_seconds": int,
            "last_cleared": "ISO 8601 datetime" | None
        }

    Example:
        >>> stats = coordinator.get_cache_stats()
        >>> print(f"Hit rate: {stats['hit_rate']}%")
        Hit rate: 67.3%
    """
```

### clear_cache

Clear all cached results.

```python
def clear_cache(self) -> None:
    """
    Clear all cached coordinator results.

    Useful for:
    - Forcing fresh analysis
    - Freeing memory
    - Testing without cache

    Example:
        >>> coordinator.clear_cache()
        >>> result = await coordinator.coordinate_analysis()
    """
```

## Data Structures

### CoordinatorConfig

```python
@dataclass
class CoordinatorConfig:
    """Configuration for resource coordinator."""
    engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py"
    cache_enabled: bool = True
    cache_ttl: int = 30
    timeout: int = 10
    max_retries: int = 3
    retry_backoff: float = 0.5  # seconds
    log_level: str = "info"
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    """Result from coordinate_analysis()."""
    status: str                  # "success", "partial", "error"
    execution_time_seconds: float
    cache_hit_rate: float       # Percentage 0-100
    timestamp: datetime
    categories: Dict[str, Dict]
    failed_categories: List[str]
    error_details: Optional[str]
```

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from manager_resource_coordinator import ResourceCoordinator

async def main():
    coordinator = ResourceCoordinator()

    # Perform full analysis
    result = await coordinator.coordinate_analysis()

    # Access results
    cpu_usage = result['categories']['cpu']['usage_percent']
    memory_usage = result['categories']['memory']['usage_percent']

    print(f"CPU: {cpu_usage}% | Memory: {memory_usage}%")
    print(f"Execution time: {result['execution_time_seconds']:.2f}s")

asyncio.run(main())
```

### Example 2: Selective Category Analysis

```python
# Analyze only CPU and thermal
result = await coordinator.coordinate_analysis(
    categories=["cpu", "thermal"]
)

print(result['categories']['cpu'])
print(result['categories']['thermal'])
```

### Example 3: Cache Monitoring

```python
# First call - cache miss
result1 = await coordinator.coordinate_analysis()
print(f"Cache hit: {result1['cache_hit_rate']}%")  # 0% (fresh)

# Second call within 30s - cache hit
result2 = await coordinator.coordinate_analysis()
print(f"Cache hit: {result2['cache_hit_rate']}%")  # ~100% (cached)

# Check cache stats
stats = coordinator.get_cache_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Overall hit rate: {stats['hit_rate']}%")
```

### Example 4: Error Handling

```python
try:
    result = await coordinator.coordinate_analysis(timeout=5)

except TimeoutError:
    print("Analysis timeout - using cache")
    result = await coordinator.coordinate_analysis(use_cache=True)

except SubprocessError as e:
    print(f"Coordinator error: {e}")
    status = await coordinator.get_coordinator_status()
    print(f"Status: {status['status']}")

except PermissionError:
    print("Permission denied - check file permissions")
```

### Example 5: Comparison with Previous Analysis

```python
# Get baseline
baseline = await coordinator.coordinate_analysis()
baseline_cpu = baseline['categories']['cpu']['usage_percent']

# Wait and get new analysis
await asyncio.sleep(60)
current = await coordinator.coordinate_analysis()
current_cpu = current['categories']['cpu']['usage_percent']

# Calculate change
change = current_cpu - baseline_cpu
print(f"CPU change: {change:+.1f}% (now {current_cpu}%)")
```

## Performance Tuning

### Cache Configuration

```python
# Aggressive caching (60s TTL)
coordinator = ResourceCoordinator(
    cache_enabled=True,
    cache_ttl=60
)

# Minimal caching (5s TTL)
coordinator = ResourceCoordinator(
    cache_enabled=True,
    cache_ttl=5
)

# No caching
coordinator = ResourceCoordinator(cache_enabled=False)
```

### Timeout Configuration

```python
# Fast timeout for responsive UI
coordinator = ResourceCoordinator(timeout=5)

# Tolerant timeout for slow systems
coordinator = ResourceCoordinator(timeout=30)

# Per-call override
result = await coordinator.coordinate_analysis(timeout=15)
```

## Monitoring & Metrics

### Execution Time Breakdown

```python
result = await coordinator.coordinate_analysis()

# Total execution time
total_time = result['execution_time_seconds']

# Categories that contributed most time
for category, metrics in result['categories'].items():
    if category in result.get('slow_categories', []):
        print(f"{category}: slow")
```

### Cache Effectiveness

```python
stats = coordinator.get_cache_stats()

if stats['hit_rate'] < 50:
    # Cache is not effective, may need larger TTL
    print("Consider increasing cache_ttl")

if stats['memory_mb'] > 50:
    # Cache is consuming lots of memory
    print("Consider decreasing cache_ttl or clearing cache")
```

## Thread Safety

ResourceCoordinator is **not thread-safe** by default. For multi-threaded use:

```python
import threading
from asyncio import Lock

coordinator = ResourceCoordinator()
lock = Lock()

async def thread_safe_analysis():
    async with lock:
        return await coordinator.coordinate_analysis()
```

## Integration Points

### With Strategy Manager

```python
from manager_resource_strategy import ResourceStrategy

coordinator = ResourceCoordinator()
strategy = ResourceStrategy()

# Get metrics from coordinator
metrics = await coordinator.coordinate_analysis()

# Generate strategy from metrics
recommendations = strategy.analyze_metrics(metrics)
```

## Troubleshooting

### Timeout Issues

**Problem**: Frequent TimeoutError
**Solution**:
1. Check system load: `coordinator.get_coordinator_status()`
2. Increase timeout: `ResourceCoordinator(timeout=20)`
3. Check coordinator.py logs

### Cache Hit Rate Low

**Problem**: Cache hit rate < 50%
**Solution**:
1. Increase TTL: `ResourceCoordinator(cache_ttl=60)`
2. Reduce analysis frequency (don't call too often)
3. Check if cache_enabled=True

### Partial Failures

**Problem**: Some categories fail (status == "partial")
**Solution**:
1. Check failed_categories list
2. Retry with longer timeout
3. Verify coordinator.py can access all system resources

## API Stability

This API is **stable** as of version 1.0.0. Breaking changes will be announced with version bump to 2.0.0.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-30 | Initial release |

---

**Status**: Production Ready
**Last Updated**: 2025-11-30
**Maintainer**: MoAI Development Team
