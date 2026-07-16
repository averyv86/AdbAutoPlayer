# MoAI Wrapper Agents - API Reference

## Overview

MoAI wrapper agents provide async Python APIs for macOS resource optimization through subprocess-based coordination with a central coordinator.py engine. This API reference documents all 8 wrapper agents (2 managers + 6 experts) with complete class signatures, methods, parameters, return types, and usage examples.

## Architecture

### Agent Hierarchy

```
manager-resource-coordinator (Orchestrator)
├── expert-cpu-optimizer
├── expert-memory-optimizer
├── expert-disk-optimizer
├── expert-network-optimizer
├── expert-battery-optimizer
└── expert-thermal-optimizer

manager-resource-strategy (Strategy Planner)
└── Uses results from coordinator for recommendations
```

### Subprocess Model

All agents use a wrapper pattern that:

1. Invokes coordinator.py via subprocess
2. Parses JSON output
3. Caches results for performance
4. Provides async/await interfaces

## Common Patterns

### PythonEngineWrapper Base Class

```python
class PythonEngineWrapper:
    """Base wrapper for Python engine subprocess communication."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10,
        cache_enabled: bool = True,
        cache_ttl: int = 30
    ):
        """
        Initialize wrapper for Python engine subprocess.

        Args:
            engine_path: Path to coordinator.py script
            timeout: Subprocess timeout in seconds (default: 10)
            cache_enabled: Enable MetricsCache for result caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 30)

        Raises:
            FileNotFoundError: If coordinator.py not found at engine_path
            PermissionError: If unable to execute coordinator.py
        """
```

### Metrics Dataclasses

All metrics follow this pattern:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class BaseMetrics:
    """Base metrics with timestamp."""
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""

    def to_json(self) -> str:
        """Convert metrics to JSON string."""
```

### Optimizer Class Pattern

```python
class Optimizer:
    """Base optimizer class for all experts."""

    async def analyze(self) -> Metrics:
        """Execute category analysis via subprocess."""

    def generate_recommendations(
        self,
        metrics: Metrics,
        risk_tolerance: str = "medium"
    ) -> List[Recommendation]:
        """Generate prioritized recommendations from metrics."""
```

### Recommendation Data Structure

```python
@dataclass
class Recommendation:
    """Optimization recommendation."""
    category: str              # "cpu", "memory", "disk", "network", "battery", "thermal"
    priority: int              # 0-100, higher = more urgent
    issue: str                 # Description of detected issue
    suggestion: str            # Recommended action
    expected_improvement: str  # e.g., "15-20% improvement"
    risk_level: str           # "low", "medium", "high"
    rollback_available: bool  # Can be reverted
    timestamp: datetime
```

## Agent Quick Links

### Managers

- **[manager-resource-coordinator](managers/resource-coordinator.md)** - Main orchestrator for 6-category parallel analysis
- **[manager-resource-strategy](managers/resource-strategy.md)** - Strategy planner with priority scoring and approval workflow

### Experts

- **[expert-cpu-optimizer](experts/cpu-optimizer.md)** - CPU usage and thermal analysis
- **[expert-memory-optimizer](experts/memory-optimizer.md)** - RAM and swap usage optimization
- **[expert-disk-optimizer](experts/disk-optimizer.md)** - Storage and I/O performance
- **[expert-network-optimizer](experts/network-optimizer.md)** - Network bandwidth and connectivity
- **[expert-battery-optimizer](experts/battery-optimizer.md)** - Power consumption and battery health
- **[expert-thermal-optimizer](experts/thermal-optimizer.md)** - Temperature and thermal management

## Common Usage Patterns

### Pattern 1: Sequential Analysis

```python
import asyncio
from manager_resource_coordinator import ResourceCoordinator

async def analyze_system():
    coordinator = ResourceCoordinator()

    # Execute all 6 analyses in parallel
    result = await coordinator.coordinate_analysis()

    print(f"Execution time: {result['execution_time_seconds']}s")
    print(f"CPU usage: {result['categories']['cpu']['usage_percent']}%")
    print(f"Memory usage: {result['categories']['memory']['usage_percent']}%")

asyncio.run(analyze_system())
```

### Pattern 2: Selective Analysis

```python
# Analyze only specific categories
result = await coordinator.coordinate_analysis(
    categories=["cpu", "thermal"]  # Skip others
)
```

### Pattern 3: Strategy Generation

```python
from manager_resource_strategy import ResourceStrategy

strategy = ResourceStrategy()
recommendations = strategy.analyze_metrics(analysis_result)

# Filter by risk tolerance
safe_recommendations = [
    r for r in recommendations
    if r.risk_level == "low"
]
```

### Pattern 4: Error Handling

```python
try:
    result = await coordinator.coordinate_analysis()
except TimeoutError:
    print("Analysis timeout - retrying with cache")
    result = await coordinator.coordinate_analysis(use_cache=True)
except SubprocessError as e:
    print(f"Coordinator error: {e}")
except PermissionError as e:
    print(f"Permission denied: {e}")
```

## Data Structures Reference

### Metrics Base Fields

All metrics include:
- `timestamp`: ISO 8601 datetime
- `metric_version`: Version of metric format (for compatibility)

### Performance Metrics

**CPU**:
- `usage_percent`: 0-100
- `core_count`: Number of cores
- `per_core_usage`: List of per-core percentages
- `temperature`: Celsius
- `frequency_mhz`: Current frequency
- `throttling_detected`: Boolean

**Memory**:
- `usage_percent`: 0-100
- `available_gb`: Available RAM
- `used_gb`: Used RAM
- `swap_percent`: Swap usage 0-100
- `pressure_level`: "normal", "moderate", "high"

**Disk**:
- `usage_percent`: 0-100
- `total_gb`: Total capacity
- `used_gb`: Used space
- `free_gb`: Free space
- `read_speed_mbs`: MB/s
- `write_speed_mbs`: MB/s

**Network**:
- `download_mbps`: Download speed
- `upload_mbps`: Upload speed
- `latency_ms`: Latency in milliseconds
- `packet_loss_percent`: 0-100
- `connected_devices`: Number of connections

**Battery**:
- `percentage`: 0-100
- `health_percent`: Battery health 0-100
- `temperature`: Battery temperature
- `charging`: Boolean
- `time_remaining_minutes`: Estimated minutes
- `cycle_count`: Battery cycle count

**Thermal**:
- `cpu_temp`: CPU temperature
- `gpu_temp`: GPU temperature (if available)
- `fan_rpm`: Fan speed
- `throttling_active`: Boolean
- `thermal_pressure`: "normal", "elevated", "critical"

## Performance Characteristics

### Execution Times

| Operation | Expected Time | With Cache (60% hit) |
|-----------|--------------|----------------------|
| Full analysis (6 categories) | 2.0-2.5s | 1.5-1.8s |
| Single category | 0.3-0.5s | 0.1-0.2s |
| Strategy generation | 0.2-0.3s | Same |
| Recommendation ranking | 0.1-0.2s | Same |

### Memory Usage

| Component | Memory |
|-----------|--------|
| ResourceCoordinator | 5-10 MB |
| Per Expert | 2-3 MB |
| MetricsCache (full) | 10-15 MB |

### Subprocess Details

- **Timeout**: 10 seconds default (configurable)
- **Max concurrent subprocesses**: 6 (experts) + 1 (coordinator)
- **JSON parsing**: Direct subprocess.run() → json.loads()

## Integration Patterns

### With Python Services

```python
from fastapi import FastAPI
from manager_resource_coordinator import ResourceCoordinator

app = FastAPI()
coordinator = ResourceCoordinator()

@app.get("/api/metrics")
async def get_metrics():
    result = await coordinator.coordinate_analysis()
    return result["categories"]
```

### With Monitoring Systems

```python
# Integration with Prometheus, Grafana, etc.
async def continuous_monitoring():
    coordinator = ResourceCoordinator()

    while True:
        result = await coordinator.coordinate_analysis()

        # Export to monitoring system
        export_prometheus_metrics(result)

        await asyncio.sleep(30)  # Check every 30s
```

## Error Codes & Recovery

### Common Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `TimeoutError` | Analysis > 10s | Retry with cache enabled |
| `SubprocessError` | Coordinator.py crashed | Check logs, restart |
| `PermissionError` | No execute permission | Fix file permissions |
| `FileNotFoundError` | coordinator.py missing | Verify installation |
| `JSONDecodeError` | Invalid coordinator output | Check coordinator logs |

## File Organization

```
.claude/skills/macos-resource-optimizer/.data/docs/api/
├── README.md (this file)
├── managers/
│   ├── resource-coordinator.md (coordinator API)
│   └── resource-strategy.md (strategy API)
└── experts/
    ├── cpu-optimizer.md
    ├── memory-optimizer.md
    ├── disk-optimizer.md
    ├── network-optimizer.md
    ├── battery-optimizer.md
    └── thermal-optimizer.md
```

## Version Information

| Component | Version | Status |
|-----------|---------|--------|
| API Reference | 1.0.0 | Stable |
| Coordinator | 1.0.0 | Stable |
| Python | 3.13+ | Required |
| Cache System | MetricsCache v1 | Active |

## License & Attribution

These APIs are part of the MoAI macOS Optimizer project.

---

**Last Updated**: 2025-11-30
**Maintainer**: MoAI Development Team
**Status**: Production Ready
