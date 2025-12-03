# expert-memory-optimizer API

## Overview

Memory resource analysis and optimization specialist. Monitors RAM usage, swap usage, and memory pressure. Generates recommendations for reducing memory consumption and improving system stability.

**Key Metrics**:
- Usage percentage (0-100%)
- Available/used GB
- Swap usage percentage
- Memory pressure level

## Classes

### MemoryMetrics

Memory metrics dataclass.

```python
@dataclass
class MemoryMetrics:
    """Memory resource metrics."""
    usage_percent: float       # 0-100
    available_gb: float        # Available RAM in GB
    used_gb: float            # Used RAM in GB
    swap_percent: float       # Swap usage 0-100
    pressure_level: str       # "normal", "moderate", "high"
    timestamp: datetime
```

### MemoryOptimizer

Main memory optimization class.

```python
class MemoryOptimizer:
    """Memory resource analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """Initialize memory optimizer."""
```

## Methods

### analyze_memory

Analyze memory metrics.

```python
async def analyze_memory(self) -> MemoryMetrics:
    """
    Execute memory analysis via coordinator.py.

    Measures:
    - Total and available RAM
    - Used memory percentage
    - Swap usage
    - Memory pressure (macOS-specific)

    Returns:
        MemoryMetrics with current memory state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s

    Example:
        >>> optimizer = MemoryOptimizer()
        >>> metrics = await optimizer.analyze_memory()
        >>> print(f"Memory: {metrics.usage_percent}%")
        >>> print(f"Available: {metrics.available_gb:.1f} GB")
    """
```

### generate_recommendations

Generate memory optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: MemoryMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on memory metrics.

    Analyzes memory state and produces recommendations for:
    - Terminating memory-heavy processes
    - Clearing caches
    - Reducing swap usage
    - Improving memory stability

    Args:
        metrics: MemoryMetrics from analyze_memory()
        risk_tolerance: "low", "medium", "high"

    Returns:
        List of Recommendation objects sorted by priority

    Examples:
    - Priority 95: "Memory critical (92%) - terminate Chrome (3.2 GB)"
    - Priority 85: "High swap usage (78%) - free memory urgently"
    - Priority 60: "Moderate memory (72%) - close background apps"
    - Priority 30: "Memory normal (45%) - no action needed"

    Example:
        >>> metrics = await optimizer.analyze_memory()
        >>> recs = optimizer.generate_recommendations(metrics)
        >>> for rec in recs[:3]:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Thresholds

| Metric | Normal | Moderate | High | Critical |
|--------|--------|----------|------|----------|
| RAM Usage | 0-60% | 60-75% | 75-85% | 85%+ |
| Swap Usage | 0-20% | 20-40% | 40-60% | 60%+ |
| Pressure | normal | moderate | high | critical |

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_memory_optimizer import MemoryOptimizer

async def main():
    optimizer = MemoryOptimizer()
    metrics = await optimizer.analyze_memory()

    print(f"Memory Usage: {metrics.usage_percent}%")
    print(f"Used: {metrics.used_gb:.1f} GB")
    print(f"Available: {metrics.available_gb:.1f} GB")
    print(f"Swap: {metrics.swap_percent}%")
    print(f"Pressure: {metrics.pressure_level}")

asyncio.run(main())
```

### Example 2: Swap Pressure

```python
metrics = await optimizer.analyze_memory()

if metrics.swap_percent > 60:
    print("CRITICAL: Excessive swap usage!")
    print(f"Swap at {metrics.swap_percent}% - performance severely degraded")
    recs = optimizer.generate_recommendations(metrics)
    for rec in recs:
        if rec.priority >= 80:
            print(f"  URGENT: {rec.suggestion}")
```

### Example 3: Cache Clearing

```python
metrics = await optimizer.analyze_memory()

if metrics.usage_percent > 75:
    print("Memory critical - recommend clearing caches:")
    recs = optimizer.generate_recommendations(metrics)
    cleanup_recs = [r for r in recs if "cache" in r.suggestion.lower()]
    for rec in cleanup_recs:
        print(f"  {rec.suggestion}")
```

## Pressure Level

Memory pressure (macOS-specific):
- **normal**: < 60% usage, plenty of headroom
- **moderate**: 60-75% usage, app responsiveness may decrease
- **high**: 75-85% usage, noticeable slowdowns
- **critical**: 85%+ usage, severe performance degradation

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()

# Memory analysis included in full analysis
result = await coordinator.coordinate_analysis()
memory_metrics = result['categories']['memory']

# Or analyze memory directly
optimizer = MemoryOptimizer()
metrics = await optimizer.analyze_memory()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_memory() | 0.3-0.5s |
| generate_recommendations() | 0.05-0.1s |

## API Stability

Stable as of version 1.0.0.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-30 | Initial release |

---

**Status**: Production Ready
**Last Updated**: 2025-11-30
