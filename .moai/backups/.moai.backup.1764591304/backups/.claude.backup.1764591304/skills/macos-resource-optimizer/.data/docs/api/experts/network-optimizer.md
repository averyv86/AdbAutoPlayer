# expert-network-optimizer API

## Overview

Network performance and connectivity specialist. Monitors bandwidth, latency, packet loss, and connection quality. Generates recommendations for optimizing network performance and identifying connectivity issues.

**Key Metrics**:
- Download/upload speed (Mbps)
- Latency (ms)
- Packet loss (%)
- Connected devices count

## Classes

### NetworkMetrics

Network metrics dataclass.

```python
@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    download_mbps: float      # Download speed
    upload_mbps: float        # Upload speed
    latency_ms: float         # Latency in milliseconds
    packet_loss_percent: float # Packet loss 0-100
    connected_devices: int    # Number of connections
    timestamp: datetime
```

### NetworkOptimizer

Main network optimization class.

```python
class NetworkOptimizer:
    """Network performance analyzer and optimizer."""

    def __init__(
        self,
        engine_path: str = ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
        timeout: int = 10
    ):
        """Initialize network optimizer."""
```

## Methods

### analyze_network

Analyze network metrics.

```python
async def analyze_network(self) -> NetworkMetrics:
    """
    Execute network analysis via coordinator.py.

    Measures:
    - Download/upload speed
    - Network latency
    - Packet loss
    - Connection count
    - Link quality

    Returns:
        NetworkMetrics with current network state

    Raises:
        TimeoutError: If analysis exceeds timeout
        SubprocessError: If coordinator fails

    Performance:
        - Typical execution: 0.3-0.5s

    Example:
        >>> optimizer = NetworkOptimizer()
        >>> metrics = await optimizer.analyze_network()
        >>> print(f"Download: {metrics.download_mbps:.1f} Mbps")
        >>> print(f"Latency: {metrics.latency_ms:.1f} ms")
    """
```

### generate_recommendations

Generate network optimization recommendations.

```python
def generate_recommendations(
    self,
    metrics: NetworkMetrics,
    risk_tolerance: str = "medium"
) -> List[Recommendation]:
    """
    Generate recommendations based on network metrics.

    Analyzes network state and produces recommendations for:
    - Improving connection quality
    - Reducing latency
    - Optimizing bandwidth usage
    - Identifying network issues

    Args:
        metrics: NetworkMetrics from analyze_network()
        risk_tolerance: "low", "medium", "high"

    Returns:
        List of Recommendation objects sorted by priority

    Examples:
    - Priority 85: "High latency (85ms) - switch to 5GHz WiFi"
    - Priority 75: "Packet loss (2.3%) - check WiFi signal strength"
    - Priority 60: "Slow download (8 Mbps) - move closer to router"
    - Priority 30: "Network optimal - no action needed"

    Example:
        >>> metrics = await optimizer.analyze_network()
        >>> recs = optimizer.generate_recommendations(metrics)
        >>> for rec in recs[:3]:
        ...     print(f"{rec.priority:3d} {rec.issue}")
    """
```

## Thresholds

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| Download | >50 Mbps | 20-50 | 5-20 | <5 |
| Upload | >10 Mbps | 5-10 | 1-5 | <1 |
| Latency | <20 ms | 20-50 | 50-100 | >100 |
| Packet Loss | 0% | <0.5% | 0.5-2% | >2% |

## Usage Examples

### Example 1: Basic Analysis

```python
import asyncio
from expert_network_optimizer import NetworkOptimizer

async def main():
    optimizer = NetworkOptimizer()
    metrics = await optimizer.analyze_network()

    print(f"Download: {metrics.download_mbps:.1f} Mbps")
    print(f"Upload: {metrics.upload_mbps:.1f} Mbps")
    print(f"Latency: {metrics.latency_ms:.1f} ms")
    print(f"Packet Loss: {metrics.packet_loss_percent:.2f}%")
    print(f"Devices: {metrics.connected_devices}")

asyncio.run(main())
```

### Example 2: Connection Quality

```python
metrics = await optimizer.analyze_network()

if metrics.latency_ms > 100:
    print("WARNING: High latency detected")
    print(f"Latency: {metrics.latency_ms:.1f} ms")

if metrics.packet_loss_percent > 1:
    print("WARNING: Packet loss detected")
    print(f"Loss rate: {metrics.packet_loss_percent:.2f}%")
```

### Example 3: Bandwidth Optimization

```python
metrics = await optimizer.analyze_network()

if metrics.download_mbps < 10:
    print("Slow network - consider:")
    recs = optimizer.generate_recommendations(metrics)
    for rec in recs:
        if rec.category == "network":
            print(f"  {rec.suggestion}")
```

## WiFi Optimization

Common recommendations:
- Switch to 5GHz band (less interference)
- Move closer to router
- Reduce number of concurrent connections
- Disable bandwidth-heavy background apps
- Update router firmware

## Integration with Coordinator

```python
coordinator = ResourceCoordinator()

# Network analysis included in full analysis
result = await coordinator.coordinate_analysis()
network_metrics = result['categories']['network']

# Or analyze network directly
optimizer = NetworkOptimizer()
metrics = await optimizer.analyze_network()
```

## Performance

| Operation | Time |
|-----------|------|
| analyze_network() | 0.3-0.5s |
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
