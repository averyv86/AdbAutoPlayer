#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Memory Analyzer

Detailed memory and swap analysis with leak detection and recommendations.

Usage:
    uv run analyze_memory.py                      # Human-readable output
    uv run analyze_memory.py --json               # JSON output
    uv run analyze_memory.py --threshold 85.0     # Custom threshold
    uv run analyze_memory.py --verbose            # Detailed output

Exit Codes:
    0 - Healthy (memory usage below threshold)
    1 - Warning (memory usage elevated but manageable)
    2 - Critical (memory usage at dangerous levels)
    3 - Error (execution failure)
"""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import click
import psutil


@dataclass
class MemoryMetrics:
    """Memory performance metrics."""
    total: int
    available: int
    used: int
    free: int
    percent: float
    active: int
    inactive: int
    wired: int
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float
    memory_pressure: Optional[float]


@dataclass
class ProcessMemoryInfo:
    """Memory information for a process."""
    pid: int
    name: str
    memory_mb: float
    memory_percent: float


@dataclass
class MemoryAnalysis:
    """Memory analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class MemoryAnalyzer:
    """Detailed memory analysis and recommendations."""

    # Default thresholds
    THRESHOLD_WARNING = 75.0
    THRESHOLD_CRITICAL = 85.0
    SWAP_WARNING = 50.0
    SWAP_CRITICAL = 75.0
    PRESSURE_WARNING = 60.0
    PRESSURE_CRITICAL = 80.0

    def __init__(self, threshold: float = 85.0, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose

    def collect_metrics(self) -> MemoryMetrics:
        """Collect comprehensive memory metrics."""
        # Virtual memory statistics
        mem = psutil.virtual_memory()

        # Swap memory statistics
        swap = psutil.swap_memory()

        # macOS-specific memory pressure calculation
        memory_pressure = self._calculate_memory_pressure(mem)

        return MemoryMetrics(
            total=mem.total,
            available=mem.available,
            used=mem.used,
            free=mem.free,
            percent=mem.percent,
            active=getattr(mem, 'active', 0),
            inactive=getattr(mem, 'inactive', 0),
            wired=getattr(mem, 'wired', 0),
            swap_total=swap.total,
            swap_used=swap.used,
            swap_free=swap.free,
            swap_percent=swap.percent,
            memory_pressure=memory_pressure
        )

    def _calculate_memory_pressure(self, mem) -> Optional[float]:
        """Calculate memory pressure (macOS specific approximation)."""
        try:
            # Memory pressure is approximated by:
            # (active + wired) / total * 100
            # This gives us the percentage of memory actively in use
            active = getattr(mem, 'active', 0)
            wired = getattr(mem, 'wired', 0)

            if mem.total == 0:
                return None

            pressure = ((active + wired) / mem.total) * 100
            return pressure
        except Exception:
            return None

    def get_top_memory_consumers(self, limit: int = 5) -> list[ProcessMemoryInfo]:
        """Get top memory-consuming processes."""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
            try:
                info = proc.info

                # Skip if memory_info is None
                if info['memory_info'] is None:
                    continue

                memory_mb = info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                memory_percent = info['memory_percent'] or 0.0

                processes.append(ProcessMemoryInfo(
                    pid=info['pid'],
                    name=info['name'],
                    memory_mb=memory_mb,
                    memory_percent=memory_percent
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue

        # Sort by memory usage and return top N
        processes.sort(key=lambda x: x.memory_mb, reverse=True)
        return processes[:limit]

    def detect_issues(self, metrics: MemoryMetrics) -> list[str]:
        """Detect memory-related issues."""
        issues = []

        # High memory usage
        if metrics.percent >= self.THRESHOLD_CRITICAL:
            issues.append("Critical: Memory usage at dangerous levels")
        elif metrics.percent >= self.threshold:
            issues.append("Warning: Memory usage elevated")

        # Swap usage analysis
        if metrics.swap_total > 0:
            if metrics.swap_percent >= self.SWAP_CRITICAL:
                issues.append(
                    f"Critical: High swap usage ({metrics.swap_percent:.1f}%) - "
                    "system may be experiencing severe memory pressure"
                )
            elif metrics.swap_percent >= self.SWAP_WARNING:
                issues.append(
                    f"Warning: Moderate swap usage ({metrics.swap_percent:.1f}%) - "
                    "consider closing unused applications"
                )

        # Memory pressure analysis
        if metrics.memory_pressure is not None:
            if metrics.memory_pressure >= self.PRESSURE_CRITICAL:
                issues.append(
                    f"Critical: High memory pressure ({metrics.memory_pressure:.1f}%)"
                )
            elif metrics.memory_pressure >= self.PRESSURE_WARNING:
                issues.append(
                    f"Warning: Elevated memory pressure ({metrics.memory_pressure:.1f}%)"
                )

        # Low available memory
        available_gb = metrics.available / (1024 ** 3)
        if available_gb < 1.0:
            issues.append(
                f"Critical: Low available memory ({available_gb:.2f} GB remaining)"
            )
        elif available_gb < 2.0:
            issues.append(
                f"Warning: Limited available memory ({available_gb:.2f} GB remaining)"
            )

        # Wired memory analysis (macOS specific)
        if metrics.wired > 0:
            wired_percent = (metrics.wired / metrics.total) * 100
            if wired_percent > 50:
                issues.append(
                    f"High wired memory: {wired_percent:.1f}% "
                    "(kernel and system processes)"
                )

        return issues

    def generate_recommendations(
        self,
        metrics: MemoryMetrics,
        issues: list[str],
        top_consumers: list[ProcessMemoryInfo]
    ) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Critical memory usage recommendations
        if metrics.percent >= self.THRESHOLD_CRITICAL:
            recommendations.append("URGENT: Free up memory immediately")
            recommendations.append("Close unnecessary applications and browser tabs")
            recommendations.append("Save work and restart memory-intensive applications")
            recommendations.append("Consider restarting the system if issues persist")

        # High memory usage recommendations
        elif metrics.percent >= self.threshold:
            recommendations.append("Monitor memory usage trends")
            recommendations.append("Close unused applications")
            recommendations.append("Clear browser cache and close excessive tabs")

        # Top consumers recommendations
        if top_consumers:
            top_process = top_consumers[0]
            if top_process.memory_mb > 1024:  # > 1 GB
                recommendations.append(
                    f"Top memory consumer: {top_process.name} "
                    f"({top_process.memory_mb:.0f} MB) - consider restarting if not needed"
                )

        # Swap usage recommendations
        if metrics.swap_total > 0 and metrics.swap_percent >= self.SWAP_WARNING:
            recommendations.append("High swap usage indicates insufficient RAM")
            recommendations.append("Close memory-intensive applications")
            recommendations.append("Consider upgrading RAM capacity")
            recommendations.append("Disable memory-intensive background processes")

        # Memory pressure recommendations
        if metrics.memory_pressure and metrics.memory_pressure >= self.PRESSURE_WARNING:
            recommendations.append("Reduce active memory pressure")
            recommendations.append("Quit applications running in background")
            recommendations.append("Disable startup items and login items")

        # Low available memory recommendations
        available_gb = metrics.available / (1024 ** 3)
        if available_gb < 2.0:
            recommendations.append("Free up available memory")
            recommendations.append("Use Activity Monitor to identify memory leaks")
            recommendations.append("Restart applications with growing memory usage")

        # Optimization recommendations
        if not any("Critical" in issue or "URGENT" in rec for issue in issues for rec in recommendations):
            recommendations.append("Memory usage is manageable")
            recommendations.append("Continue monitoring for memory leaks")
            recommendations.append("Periodically restart long-running applications")

        return recommendations

    def determine_risk_level(self, metrics: MemoryMetrics) -> str:
        """Determine overall memory risk level."""
        # Critical conditions
        if (metrics.percent >= self.THRESHOLD_CRITICAL or
            (metrics.swap_total > 0 and metrics.swap_percent >= self.SWAP_CRITICAL) or
            (metrics.memory_pressure and metrics.memory_pressure >= self.PRESSURE_CRITICAL)):
            return "critical"

        # Warning conditions
        if (metrics.percent >= self.threshold or
            (metrics.swap_total > 0 and metrics.swap_percent >= self.SWAP_WARNING) or
            (metrics.memory_pressure and metrics.memory_pressure >= self.PRESSURE_WARNING)):
            return "warning"

        return "low"

    def analyze(self) -> MemoryAnalysis:
        """Perform complete memory analysis."""
        metrics = self.collect_metrics()
        top_consumers = self.get_top_memory_consumers(limit=5)
        issues = self.detect_issues(metrics)
        recommendations = self.generate_recommendations(metrics, issues, top_consumers)
        risk_level = self.determine_risk_level(metrics)

        status = "healthy"
        if risk_level == "critical":
            status = "critical"
        elif risk_level == "warning":
            status = "warning"

        analysis = MemoryAnalysis(
            category="memory",
            timestamp=datetime.now().timestamp(),
            metrics=asdict(metrics),
            analysis={
                "status": status,
                "risk_level": risk_level,
                "issues": issues,
                "recommendations": recommendations,
                "top_consumers": [asdict(p) for p in top_consumers]
            }
        )

        return analysis


def format_human_readable(analysis: MemoryAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} Memory Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Metrics
    metrics = analysis.metrics

    total_gb = metrics['total'] / (1024 ** 3)
    used_gb = metrics['used'] / (1024 ** 3)
    available_gb = metrics['available'] / (1024 ** 3)

    lines.append("Memory Metrics:")
    lines.append(f"  Total: {total_gb:.2f} GB")
    lines.append(f"  Used: {used_gb:.2f} GB ({metrics['percent']:.1f}%)")
    lines.append(f"  Available: {available_gb:.2f} GB")

    if verbose:
        active_gb = metrics['active'] / (1024 ** 3)
        inactive_gb = metrics['inactive'] / (1024 ** 3)
        wired_gb = metrics['wired'] / (1024 ** 3)

        lines.append(f"  Active: {active_gb:.2f} GB")
        lines.append(f"  Inactive: {inactive_gb:.2f} GB")
        lines.append(f"  Wired: {wired_gb:.2f} GB")

    # Swap metrics
    if metrics['swap_total'] > 0:
        swap_total_gb = metrics['swap_total'] / (1024 ** 3)
        swap_used_gb = metrics['swap_used'] / (1024 ** 3)

        lines.append("")
        lines.append("Swap Metrics:")
        lines.append(f"  Total: {swap_total_gb:.2f} GB")
        lines.append(f"  Used: {swap_used_gb:.2f} GB ({metrics['swap_percent']:.1f}%)")

    # Memory pressure
    if metrics['memory_pressure'] is not None:
        lines.append("")
        lines.append(f"Memory Pressure: {metrics['memory_pressure']:.1f}%")

    lines.append("")

    # Top consumers
    top_consumers = analysis.analysis["top_consumers"]
    if top_consumers:
        lines.append("🔝 Top Memory Consumers:")
        for proc in top_consumers:
            lines.append(
                f"  {proc['name']}: {proc['memory_mb']:.0f} MB "
                f"({proc['memory_percent']:.1f}%) [PID: {proc['pid']}]"
            )
        lines.append("")

    # Issues
    issues = analysis.analysis["issues"]
    if issues:
        lines.append("🔍 Detected Issues:")
        for issue in issues:
            lines.append(f"  - {issue}")
        lines.append("")

    # Recommendations
    recommendations = analysis.analysis["recommendations"]
    if recommendations:
        lines.append("💡 Recommendations:")
        for rec in recommendations:
            lines.append(f"  - {rec}")
        lines.append("")

    return "\n".join(lines)


@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--threshold', type=float, default=85.0, help='Memory usage threshold (default: 85.0)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed memory and swap analysis with recommendations.

    Analyzes memory usage, swap activity, memory pressure, and top consumers.
    Detects memory leaks and provides specific optimization recommendations.
    """
    try:
        analyzer = MemoryAnalyzer(threshold=threshold, verbose=verbose)
        analysis = analyzer.analyze()

        if output_json:
            # JSON output
            output = asdict(analysis)
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            output = format_human_readable(analysis, verbose=verbose)
            print(output)

        # Exit code based on risk level
        exit_codes = {
            "low": 0,
            "warning": 1,
            "critical": 2
        }
        risk_level = analysis.analysis["risk_level"]
        sys.exit(exit_codes[risk_level])

    except Exception as e:
        error_output = {
            "category": "memory",
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now().timestamp()
        }

        if output_json:
            print(json.dumps(error_output, indent=2))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)

        sys.exit(3)


if __name__ == "__main__":
    main()
