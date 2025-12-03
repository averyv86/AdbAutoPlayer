# expert-thermal-optimizer API

## Overview

Thermal management specialist. Monitors CPU and GPU temperatures, fan speeds, and thermal throttling. Generates recommendations for improving system cooling and preventing thermal-induced performance degradation.

**Key Metrics**:
- CPU temperature (Celsius)
- GPU temperature (Celsius, if available)
- Fan RPM
- Throttling state (boolean)
- Thermal pressure level

## Classes

### ThermalMetrics

Thermal metrics dataclass.

```python
@dataclass
class ThermalMetrics:
    """Thermal monitoring metrics."""
    cpu_temp: float           # CPU temperature in Celsius
    gpu_temp: Optional[float] # GPU temperature (if available)
    fan_rpm: int             # Fan speed
    throttling_active: bool  # CPU throttling state
    thermal_pressure: str    # "normal", "elevated", "critical"
    timestamp: datetime
```

### ThermalOptimizer

Main thermal optimization class.

```python
class ThermalOptimizer:
    """Thermal management analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """Initialize thermal optimizer."""
```

## Methods

### analyze_thermal

Analyze thermal metrics.

```python
async def analyze_thermal(self) -> ThermalMetrics:
    """
    Execute thermal analysis via coordinator.py.

    Measures:
    - CPU temperature
    - GPU temperature (if available)
    - Fan speed (RPM)
    - Thermal throttling state
    - Overall system thermal pressure
    - Heat dissipation rate

    Returns:
        ThermalMetrics with current thermal state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s

    Example:
        >>> optimizer = ThermalOptimizer()
        >>> metrics = await optimizer.analyze_thermal()
        >>> print(f"CPU Temp: {metrics.cpu_temp}°C")
        >>> print(f"Fan: {metrics.fan_rpm} RPM")
        >>> print(f"Throttling: {metrics.throttling_active}")
    """
```

### generate_recommendations

Generate thermal optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: ThermalMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on thermal metrics.

    Analyzes thermal state and produces recommendations for:
    - Improving system cooling
    - Preventing thermal throttling
    - Reducing heat generation
    - Maintaining optimal operating temperature

    Args:
        metrics: ThermalMetrics from analyze_thermal()
        risk_tolerance: "low", "medium", "high"

    Returns:
        List of Recommendation objects sorted by priority

    Examples:
    - Priority 100: "Critical temperature (95°C) - immediate cooling required"
    - Priority 90: "Thermal throttling active - reduce workload"
    - Priority 75: "High temperature (82°C) - improve ventilation"
    - Priority 50: "Elevated temperature (72°C) - monitor closely"
    - Priority 20: "Normal temperature (58°C) - no action needed"

    Example:
        >>> metrics = await optimizer.analyze_thermal()
        >>> recs = optimizer.generate_recommendations(metrics)
        >>> for rec in recs[:3]:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Temperature Thresholds

| Level | CPU Temp | GPU Temp | Action |
|-------|----------|----------|--------|
| Safe | <60°C | <65°C | Normal operation |
| Elevated | 60-75°C | 65-80°C | Monitor |
| High | 75-85°C | 80-90°C | Improve cooling |
| Critical | >85°C | >90°C | Urgent action |
| Throttling | >95°C | >100°C | Severe throttling |

## Thermal Pressure Levels

- **normal**: < 60°C, fan at normal speed
- **elevated**: 60-75°C, fan increasing
- **critical**: > 75°C, fan at high speed, possible throttling

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_thermal_optimizer import ThermalOptimizer

async def main():
    optimizer = ThermalOptimizer()
    metrics = await optimizer.analyze_thermal()

    print(f"CPU Temp: {metrics.cpu_temp}°C")
    if metrics.gpu_temp:
        print(f"GPU Temp: {metrics.gpu_temp}°C")
    print(f"Fan: {metrics.fan_rpm} RPM")
    print(f"Throttling: {metrics.throttling_active}")
    print(f"Pressure: {metrics.thermal_pressure}")

asyncio.run(main())
```

### Example 2: Temperature Alert

```python
metrics = await optimizer.analyze_thermal()

if metrics.cpu_temp > 85:
    print("CRITICAL: CPU temperature critical!")
    print(f"Temperature: {metrics.cpu_temp}°C")
    if metrics.throttling_active:
        print("CPU is being throttled - performance severely degraded")

if metrics.thermal_pressure == "critical":
    print("Thermal pressure critical - immediate cooling required")
    recs = optimizer.generate_recommendations(metrics)
    for rec in recs:
        if rec.priority >= 80:
            print(f"  URGENT: {rec.suggestion}")
```

### Example 3: Cooling Solutions

```python
metrics = await optimizer.analyze_thermal()

if metrics.cpu_temp > 75:
    print("Temperature elevated - recommended actions:")
    print("  1. Improve ventilation (clear vents)")
    print("  2. Reduce workload (close apps)")
    print("  3. Use external cooler")
    print("  4. Check thermal paste")

recs = optimizer.generate_recommendations(metrics)
for rec in recs:
    print(f"  {rec.suggestion}")
```

### Example 4: Continuous Monitoring

```python
async def monitor_thermal():
    optimizer = ThermalOptimizer()

    for i in range(10):
        metrics = await optimizer.analyze_thermal()
        status = "OK" if metrics.cpu_temp < 75 else "HOT" if metrics.cpu_temp < 85 else "CRITICAL"
        print(f"[{i+1:2d}] CPU: {metrics.cpu_temp:5.1f}°C | "
              f"Fan: {metrics.fan_rpm:4d} RPM | {status}")
        await asyncio.sleep(10)

asyncio.run(monitor_thermal())
```

## Cooling Recommendations

When temperature is high, recommendations may include:

**Hardware-level**:
- Check/replace thermal paste
- Clean heatsink and vents
- Improve case airflow
- Add external cooling

**Software-level**:
- Close CPU-intensive apps
- Reduce screen brightness
- Disable turbo/boost mode
- Enable Low Power Mode
- Check for thermal throttling

**Environmental**:
- Improve room ventilation
- Use cooler environment
- Avoid direct sunlight
- Use cooling pad

## Fan Analysis

```python
{
    "category": "thermal",
    "priority": 85,
    "issue": "Fan at maximum (5200 RPM) but CPU still 88°C",
    "suggestion": "Improve ventilation or reduce workload - thermal paste may need replacement",
    "risk_level": "medium"
}
```

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()

# Thermal analysis included in full analysis
result = await coordinator.coordinate_analysis()
thermal_metrics = result['categories']['thermal']

# Or analyze thermal directly
optimizer = ThermalOptimizer()
metrics = await optimizer.analyze_thermal()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_thermal() | 0.3-0.5s |
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
