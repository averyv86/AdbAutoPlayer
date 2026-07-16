# expert-cpu-optimizer API

## Overview

CPU resource analysis and optimization specialist. Monitors CPU usage, temperature, frequency, and thermal throttling. Generates recommendations for reducing CPU load and managing thermal output.

**Key Metrics**:
- Usage percentage (0-100%)
- Per-core usage breakdown
- CPU frequency (MHz)
- Temperature (Celsius)
- Throttling detection

## Classes

### CPUMetrics

CPU metrics dataclass.

```python
@dataclass
class CPUMetrics:
    """CPU resource metrics."""
    usage_percent: float          # 0-100
    core_count: int               # Number of CPU cores
    per_core_usage: List[float]  # Usage per core
    temperature: float            # Celsius
    frequency_mhz: float         # Current frequency
    throttling_detected: bool    # Thermal throttling active
    timestamp: datetime
```

### CPUOptimizer

Main CPU optimization class.

```python
class CPUOptimizer:
    """CPU resource analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """
        Initialize CPU optimizer.

        Args:
            engine_path: Path to coordinator.py
            timeout: Subprocess timeout in seconds
        """
```

## Methods

### analyze_cpu

Analyze CPU metrics.

```python
async def analyze_cpu(self) -> CPUMetrics:
    """
    Execute CPU analysis via coordinator.py subprocess.

    Measures:
    - Overall CPU usage percentage
    - Per-core breakdown
    - Current frequency
    - Temperature
    - Throttling state

    Returns:
        CPUMetrics with current CPU state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s
        - Includes subprocess startup + measurement

    Example:
        >>> optimizer = CPUOptimizer()
        >>> metrics = await optimizer.analyze_cpu()
        >>> print(f"CPU usage: {metrics.usage_percent}%")
        >>> print(f"Cores: {metrics.core_count}")
        >>> print(f"Temp: {metrics.temperature}°C")
    """
```

### generate_recommendations

Generate optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: CPUMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on CPU metrics.

    Analyzes current CPU state and produces actionable recommendations
    for reducing CPU load and managing thermal output.

    Args:
        metrics: CPUMetrics from analyze_cpu()
        risk_tolerance: "low" (safe), "medium" (default), "high" (aggressive)

    Returns:
        List of Recommendation objects sorted by priority

    Recommendation Examples:
    - Priority 100: "CPU at 96% usage - terminate Firefox (45% CPU)"
    - Priority 95: "Thermal throttling detected - improve cooling"
    - Priority 75: "High per-core variance - distribute load"
    - Priority 50: "CPU frequency reduced - check thermals"
    - Priority 30: "Normal CPU usage - no action needed"

    Raises:
        ValueError: If invalid risk_tolerance

    Example:
        >>> metrics = await optimizer.analyze_cpu()
        >>> recommendations = optimizer.generate_recommendations(metrics)
        >>> for rec in recommendations:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Thresholds

CPU severity levels are based on:

| Metric | Normal | Elevated | High | Critical |
|--------|--------|----------|------|----------|
| Usage | 0-50% | 50-70% | 70-85% | 85%+ |
| Temp | <60°C | 60-75°C | 75-85°C | 85°C+ |
| Throttling | No | Watch | Alert | Critical |

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_cpu_optimizer import CPUOptimizer

async def main():
    optimizer = CPUOptimizer()

    # Analyze CPU
    metrics = await optimizer.analyze_cpu()

    print(f"CPU Usage: {metrics.usage_percent}%")
    print(f"Temperature: {metrics.temperature}°C")
    print(f"Cores: {metrics.core_count}")
    print(f"Per-core usage: {metrics.per_core_usage}")

asyncio.run(main())
```

### Example 2: Recommendations

```python
metrics = await optimizer.analyze_cpu()
recommendations = optimizer.generate_recommendations(metrics)

# Show top issues
for rec in recommendations[:3]:
    print(f"Priority {rec.priority}: {rec.issue}")
    print(f"  Suggestion: {rec.suggestion}\n")
```

### Example 3: Thermal Monitoring

```python
# Check thermal status
metrics = await optimizer.analyze_cpu()

if metrics.temperature > 85:
    print("CPU CRITICAL TEMPERATURE!")
    print(f"Temperature: {metrics.temperature}°C")
    print(f"Throttling: {metrics.throttling_detected}")

if metrics.throttling_detected:
    print("CPU is being throttled - performance degraded")
```

### Example 4: Per-Core Analysis

```python
metrics = await optimizer.analyze_cpu()

# Find hottest cores
for i, usage in enumerate(metrics.per_core_usage):
    if usage > 85:
        print(f"Core {i}: {usage}% (HOT)")
    elif usage > 70:
        print(f"Core {i}: {usage}% (High)")
    else:
        print(f"Core {i}: {usage}% (Normal)")
```

### Example 5: Continuous Monitoring

```python
async def monitor_cpu():
    optimizer = CPUOptimizer()

    for i in range(10):
        metrics = await optimizer.analyze_cpu()
        print(f"[{i+1:2d}] CPU: {metrics.usage_percent:5.1f}% | "
              f"Temp: {metrics.temperature:5.1f}°C | "
              f"Throttle: {metrics.throttling_detected}")
        await asyncio.sleep(5)

asyncio.run(monitor_cpu())
```

## Severity Calculation

Recommendations prioritized by:

```
Severity = (usage_factor * 40) +
           (temperature_factor * 35) +
           (throttle_factor * 25) -
           (risk_adjustment)

Usage factor: 0-100 based on CPU % (0% = 0, 100% = 100)
Temperature factor: 0-100 based on temp (< 60°C = 0, > 85°C = 100)
Throttle factor: 0-100 (not throttling = 0, throttling = 100)
Risk adjustment: 0-50 based on risk_tolerance
```

## Process Termination Recommendations

When CPU usage is critical, recommendations may suggest:

```python
{
    "category": "cpu",
    "priority": 100,
    "issue": "CPU at 96% usage - Firefox consuming 45% CPU",
    "suggestion": "Terminate Firefox process (PID: 1234)",
    "expected_improvement": "CPU: 96% → 51%",
    "risk_level": "medium",
    "rollback_available": False  # Cannot restart automatically
}
```

## Integration with Coordinator

CPU optimizer is automatically invoked by coordinator:

```python
coordinator = ResourceCoordinator()

# CPU analysis included in full analysis
result = await coordinator.coordinate_analysis()
cpu_metrics = result['categories']['cpu']

# Or analyze CPU directly
optimizer = CPUOptimizer()
metrics = await optimizer.analyze_cpu()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_cpu() | 0.3-0.5s |
| generate_recommendations() | 0.05-0.1s |
| Memory usage | 2-3 MB |

## API Stability

Stable as of version 1.0.0.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-30 | Initial release |

---

**Status**: Production Ready
**Last Updated**: 2025-11-30
