# expert-disk-optimizer API

## Overview

Disk storage and I/O performance specialist. Monitors disk space usage, I/O throughput, and storage performance. Generates recommendations for freeing space and optimizing disk performance.

**Key Metrics**:
- Usage percentage (0-100%)
- Total/used/free space (GB)
- Read/write speeds (MB/s)

## Classes

### DiskMetrics

Disk metrics dataclass.

```python
@dataclass
class DiskMetrics:
    """Disk storage metrics."""
    usage_percent: float      # 0-100
    total_gb: float          # Total capacity
    used_gb: float           # Used space
    free_gb: float           # Free space
    read_speed_mbs: float    # Read speed
    write_speed_mbs: float   # Write speed
    timestamp: datetime
```

### DiskOptimizer

Main disk optimization class.

```python
class DiskOptimizer:
    """Disk storage analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """Initialize disk optimizer."""
```

## Methods

### analyze_disk

Analyze disk metrics.

```python
async def analyze_disk(self) -> DiskMetrics:
    """
    Execute disk analysis via coordinator.py.

    Measures:
    - Storage capacity and usage
    - Available free space
    - Read/write performance
    - I/O throughput

    Returns:
        DiskMetrics with current disk state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s

    Example:
        >>> optimizer = DiskOptimizer()
        >>> metrics = await optimizer.analyze_disk()
        >>> print(f"Disk usage: {metrics.usage_percent}%")
        >>> print(f"Free space: {metrics.free_gb:.1f} GB")
    """
```

### generate_recommendations

Generate disk optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: DiskMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on disk metrics.

    Analyzes disk state and produces recommendations for:
    - Clearing temporary files
    - Removing large files
    - Optimizing storage layout
    - Improving I/O performance

    Args:
        metrics: DiskMetrics from analyze_disk()
        risk_tolerance: "low", "medium", "high"

    Returns:
        List of Recommendation objects sorted by priority

    Examples:
    - Priority 95: "Disk critical (95%) - delete old backups (42 GB)"
    - Priority 85: "Disk high (88%) - clear cache (15 GB)"
    - Priority 60: "Disk moderate (75%) - consider cleanup"
    - Priority 30: "Disk normal (55%) - no action needed"

    Example:
        >>> metrics = await optimizer.analyze_disk()
        >>> recs = optimizer.generate_recommendations(metrics)
        >>> for rec in recs[:3]:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Thresholds

| Metric | Normal | Elevated | High | Critical |
|--------|--------|----------|------|----------|
| Usage | 0-70% | 70-80% | 80-90% | 90%+ |
| Free Space | >5 GB | 3-5 GB | 1-3 GB | <1 GB |

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_disk_optimizer import DiskOptimizer

async def main():
    optimizer = DiskOptimizer()
    metrics = await optimizer.analyze_disk()

    print(f"Disk Usage: {metrics.usage_percent}%")
    print(f"Total: {metrics.total_gb:.1f} GB")
    print(f"Used: {metrics.used_gb:.1f} GB")
    print(f"Free: {metrics.free_gb:.1f} GB")
    print(f"Read speed: {metrics.read_speed_mbs:.1f} MB/s")
    print(f"Write speed: {metrics.write_speed_mbs:.1f} MB/s")

asyncio.run(main())
```

### Example 2: Critical Low Disk Space

```python
metrics = await optimizer.analyze_disk()

if metrics.free_gb < 1:
    print("CRITICAL: Disk space critical!")
    print(f"Only {metrics.free_gb:.1f} GB free")
    recs = optimizer.generate_recommendations(metrics)
    for rec in recs:
        if rec.priority >= 85:
            print(f"  {rec.suggestion}")
```

### Example 3: Performance Analysis

```python
metrics = await optimizer.analyze_disk()

print(f"Read speed: {metrics.read_speed_mbs:.1f} MB/s")
print(f"Write speed: {metrics.write_speed_mbs:.1f} MB/s")

if metrics.read_speed_mbs < 100:
    print("WARNING: Slow read speed - disk may be failing")

if metrics.write_speed_mbs < 50:
    print("WARNING: Slow write speed - consider disk check")
```

## Large File Cleanup

When disk is critical, recommendations identify:
- Large unused applications
- Old backups and archives
- Cache files
- Duplicate files

```python
{
    "category": "disk",
    "priority": 92,
    "issue": "Disk at 94% - delete old backups",
    "suggestion": "Remove backup files from /Volumes/Backup (42 GB)",
    "expected_improvement": "Free 42 GB, disk 94% → 52%",
    "risk_level": "medium"
}
```

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()

# Disk analysis included in full analysis
result = await coordinator.coordinate_analysis()
disk_metrics = result['categories']['disk']

# Or analyze disk directly
optimizer = DiskOptimizer()
metrics = await optimizer.analyze_disk()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_disk() | 0.3-0.5s |
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
