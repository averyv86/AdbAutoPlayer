# expert-battery-optimizer API

## Overview

Battery health and power consumption specialist. Monitors battery charge, health, temperature, and cycle count. Generates recommendations for extending battery life and maintaining battery health.

**Key Metrics**:
- Battery percentage (0-100%)
- Health percentage (0-100%)
- Temperature (Celsius)
- Charging state (boolean)
- Cycle count

## Classes

### BatteryMetrics

Battery metrics dataclass.

```python
@dataclass
class BatteryMetrics:
    """Battery health and power metrics."""
    percentage: float          # 0-100
    health_percent: float      # Battery health 0-100
    temperature: float         # Celsius
    charging: bool            # Currently charging
    time_remaining_minutes: int # Estimated time
    cycle_count: int          # Battery cycles
    timestamp: datetime
```

### BatteryOptimizer

Main battery optimization class.

```python
class BatteryOptimizer:
    """Battery health analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """Initialize battery optimizer."""
```

## Methods

### analyze_battery

Analyze battery metrics.

```python
async def analyze_battery(self) -> BatteryMetrics:
    """
    Execute battery analysis via coordinator.py.

    Measures:
    - Current charge percentage
    - Battery health (capacity vs original)
    - Temperature
    - Charging state
    - Cycle count
    - Time remaining

    Returns:
        BatteryMetrics with current battery state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s

    Example:
        >>> optimizer = BatteryOptimizer()
        >>> metrics = await optimizer.analyze_battery()
        >>> print(f"Battery: {metrics.percentage}%")
        >>> print(f"Health: {metrics.health_percent}%")
        >>> print(f"Cycles: {metrics.cycle_count}")
    """
```

### generate_recommendations

Generate battery optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: BatteryMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on battery metrics.

    Analyzes battery state and produces recommendations for:
    - Extending battery life
    - Maintaining battery health
    - Reducing power consumption
    - Optimizing charging habits

    Args:
        metrics: BatteryMetrics from analyze_battery()
        risk_tolerance: "low", "medium", "high"

    Returns:
        List of Recommendation objects sorted by priority

    Examples:
    - Priority 90: "Battery health degraded (78%) - replace soon"
    - Priority 75: "High cycle count (450) - battery aging"
    - Priority 65: "Battery hot (48°C) - optimize charging"
    - Priority 40: "Battery low (15%) - consider charging"
    - Priority 20: "Battery healthy - no action needed"

    Example:
        >>> metrics = await optimizer.analyze_battery()
        >>> recs = optimizer.generate_recommendations(metrics)
        >>> for rec in recs[:3]:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Battery Health Levels

| Health | Status | Action |
|--------|--------|--------|
| 100% | Excellent | No action needed |
| 90-99% | Good | Monitor usage |
| 80-89% | Fair | Optimize charging |
| 70-79% | Poor | Consider replacement |
| <70% | Critical | Replace soon |

## Cycle Count Thresholds

| Cycles | Lifespan | Status |
|--------|----------|--------|
| <100 | New | Monitor |
| 100-300 | Good | Normal |
| 300-500 | Fair | Aging |
| 500-800 | Poor | Plan replacement |
| >800 | Critical | Replace now |

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_battery_optimizer import BatteryOptimizer

async def main():
    optimizer = BatteryOptimizer()
    metrics = await optimizer.analyze_battery()

    print(f"Battery: {metrics.percentage}%")
    print(f"Health: {metrics.health_percent}%")
    print(f"Temperature: {metrics.temperature}°C")
    print(f"Charging: {metrics.charging}")
    print(f"Time remaining: {metrics.time_remaining_minutes} min")
    print(f"Cycles: {metrics.cycle_count}")

asyncio.run(main())
```

### Example 2: Health Monitoring

```python
metrics = await optimizer.analyze_battery()

if metrics.health_percent < 80:
    print("Battery health degraded!")
    print(f"Health: {metrics.health_percent}%")
    print(f"Cycles: {metrics.cycle_count}")
    print("Consider battery replacement")

recs = optimizer.generate_recommendations(metrics)
for rec in recs:
    if "health" in rec.issue.lower():
        print(f"  {rec.suggestion}")
```

### Example 3: Temperature Monitoring

```python
metrics = await optimizer.analyze_battery()

if metrics.temperature > 45:
    print(f"Battery hot: {metrics.temperature}°C")
    print("Reduce power-intensive tasks")
    print("Improve device ventilation")
```

### Example 4: Charging Optimization

```python
metrics = await optimizer.analyze_battery()

if metrics.health_percent < 85 and metrics.percentage > 80:
    print("Tip: Keep battery between 20-80% to extend life")
    print("Current: charge to 80%, discharge to 20%")

if metrics.charging:
    print(f"Charging... {metrics.percentage}%")
    print(f"Time to full: ~{int(100/metrics.percentage * metrics.time_remaining_minutes)} min")
```

## Battery Longevity Tips

Recommendations may include:
- Avoid full charge cycles (keep 20-80%)
- Disable power-hungry features when on battery
- Reduce screen brightness on battery
- Enable Low Power Mode
- Avoid high ambient temperatures

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()

# Battery analysis included in full analysis
result = await coordinator.coordinate_analysis()
battery_metrics = result['categories']['battery']

# Or analyze battery directly
optimizer = BatteryOptimizer()
metrics = await optimizer.analyze_battery()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_battery() | 0.3-0.5s |
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
