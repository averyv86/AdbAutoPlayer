"""
Resource Monitor for Dynamic Parallelism Adjustment

Monitors system resources (CPU, memory, tokens) and dynamically adjusts
parallel execution to prevent resource exhaustion.

Token Efficiency: Provides recommendations rather than enforcing limits,
allowing executor to make final decisions.
"""

import psutil
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceMetrics:
    """Current system resource usage"""
    cpu_percent: float
    memory_percent: float
    token_usage: int
    disk_io_percent: float
    timestamp: float


@dataclass
class ParallelismRecommendation:
    """Recommended parallelism adjustment"""
    recommended_parallel: int
    current_parallel: int
    reason: str
    severity: str  # "critical" | "warning" | "info"
    metrics: ResourceMetrics


class ResourceMonitor:
    """
    Monitor system resources and recommend parallelism adjustments

    Usage:
        monitor = ResourceMonitor(
            cpu_threshold=80,
            memory_threshold=75,
            token_threshold=150000
        )

        # Check if adjustment needed
        recommendation = monitor.check_resources(
            current_parallel=5,
            token_usage=120000
        )

        if recommendation:
            print(f"Adjust to {recommendation.recommended_parallel}: {recommendation.reason}")
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 75.0,
        token_threshold: int = 150000,
        disk_io_threshold: float = 70.0,
        check_interval: int = 180,  # 3 minutes in seconds
    ):
        """
        Initialize resource monitor

        Args:
            cpu_threshold: CPU usage % threshold
            memory_threshold: Memory usage % threshold
            token_threshold: Token usage threshold
            disk_io_threshold: Disk I/O % threshold
            check_interval: Minimum seconds between checks
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.token_threshold = token_threshold
        self.disk_io_threshold = disk_io_threshold
        self.check_interval = check_interval
        self.last_check: Optional[float] = None
        self.metrics_history: list[ResourceMetrics] = []

    def get_current_metrics(self, token_usage: int = 0) -> ResourceMetrics:
        """
        Get current system resource metrics

        Args:
            token_usage: Current token usage (provided by caller)

        Returns:
            ResourceMetrics with current usage
        """
        # CPU usage (average over 1 second)
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk I/O (if available)
        try:
            disk_io = psutil.disk_io_counters()
            # Simplified disk I/O metric (read/write bytes per second)
            # This is a rough estimate
            disk_io_percent = min(100.0, (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024 * 100))
        except Exception:
            disk_io_percent = 0.0

        metrics = ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            token_usage=token_usage,
            disk_io_percent=disk_io_percent,
            timestamp=time.time()
        )

        # Store in history (keep last 100)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        return metrics

    def check_resources(
        self,
        current_parallel: int,
        token_usage: int = 0,
        force_check: bool = False
    ) -> Optional[ParallelismRecommendation]:
        """
        Check if resources require parallelism adjustment

        Args:
            current_parallel: Current number of parallel agents
            token_usage: Current token usage
            force_check: Bypass interval check

        Returns:
            ParallelismRecommendation if adjustment needed, None otherwise
        """
        # Check if enough time has passed since last check
        now = time.time()
        if not force_check and self.last_check is not None:
            if (now - self.last_check) < self.check_interval:
                return None  # Too soon to check again

        self.last_check = now

        # Get current metrics
        metrics = self.get_current_metrics(token_usage)

        # Determine if adjustment needed
        recommended = current_parallel
        reason = ""
        severity = "info"

        # Critical: CPU over threshold
        if metrics.cpu_percent > self.cpu_threshold:
            reduction = max(1, int(current_parallel * 0.4))  # Reduce by 40%
            recommended = max(1, current_parallel - reduction)
            reason = f"CPU usage critical: {metrics.cpu_percent:.1f}% > {self.cpu_threshold}%"
            severity = "critical"

        # Critical: Memory over threshold
        elif metrics.memory_percent > self.memory_threshold:
            reduction = max(1, int(current_parallel * 0.3))  # Reduce by 30%
            recommended = max(1, current_parallel - reduction)
            reason = f"Memory usage critical: {metrics.memory_percent:.1f}% > {self.memory_threshold}%"
            severity = "critical"

        # Critical: Token usage near limit
        elif token_usage > self.token_threshold:
            recommended = max(1, current_parallel - 1)
            reason = f"Token usage high: {token_usage} > {self.token_threshold}"
            severity = "critical"

        # Warning: Disk I/O high
        elif metrics.disk_io_percent > self.disk_io_threshold:
            reduction = max(1, int(current_parallel * 0.2))  # Reduce by 20%
            recommended = max(1, current_parallel - reduction)
            reason = f"Disk I/O high: {metrics.disk_io_percent:.1f}% > {self.disk_io_threshold}%"
            severity = "warning"

        # Info: Resources healthy, can increase
        elif (metrics.cpu_percent < self.cpu_threshold * 0.5 and
              metrics.memory_percent < self.memory_threshold * 0.5 and
              token_usage < self.token_threshold * 0.5):
            # Only suggest increase if currently limited
            if current_parallel < 10:  # Max parallel limit
                recommended = min(10, current_parallel + 1)
                reason = f"Resources healthy - can increase parallelism"
                severity = "info"

        # Return recommendation only if change needed
        if recommended != current_parallel:
            return ParallelismRecommendation(
                recommended_parallel=recommended,
                current_parallel=current_parallel,
                reason=reason,
                severity=severity,
                metrics=metrics
            )

        return None

    def get_average_metrics(self, last_n: int = 10) -> Optional[ResourceMetrics]:
        """
        Get average metrics over last N checks

        Args:
            last_n: Number of recent metrics to average

        Returns:
            Averaged ResourceMetrics or None if insufficient history
        """
        if len(self.metrics_history) < 1:
            return None

        recent = self.metrics_history[-last_n:]

        avg_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        avg_memory = sum(m.memory_percent for m in recent) / len(recent)
        avg_tokens = sum(m.token_usage for m in recent) / len(recent)
        avg_disk_io = sum(m.disk_io_percent for m in recent) / len(recent)

        return ResourceMetrics(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            token_usage=int(avg_tokens),
            disk_io_percent=avg_disk_io,
            timestamp=time.time()
        )

    def format_metrics(self, metrics: ResourceMetrics) -> str:
        """
        Format metrics for human-readable display

        Args:
            metrics: ResourceMetrics to format

        Returns:
            Formatted string
        """
        return (
            f"CPU: {metrics.cpu_percent:.1f}% | "
            f"Memory: {metrics.memory_percent:.1f}% | "
            f"Tokens: {metrics.token_usage:,} | "
            f"Disk I/O: {metrics.disk_io_percent:.1f}%"
        )


# Module-level convenience function
def create_monitor(
    cpu_threshold: float = 80.0,
    memory_threshold: float = 75.0,
    token_threshold: int = 150000
) -> ResourceMonitor:
    """
    Create a ResourceMonitor with default or custom thresholds

    Args:
        cpu_threshold: CPU usage % threshold (default: 80%)
        memory_threshold: Memory usage % threshold (default: 75%)
        token_threshold: Token usage threshold (default: 150K)

    Returns:
        Configured ResourceMonitor instance

    Example:
        monitor = create_monitor(cpu_threshold=70, token_threshold=120000)
        recommendation = monitor.check_resources(current_parallel=5, token_usage=100000)
    """
    return ResourceMonitor(
        cpu_threshold=cpu_threshold,
        memory_threshold=memory_threshold,
        token_threshold=token_threshold
    )
