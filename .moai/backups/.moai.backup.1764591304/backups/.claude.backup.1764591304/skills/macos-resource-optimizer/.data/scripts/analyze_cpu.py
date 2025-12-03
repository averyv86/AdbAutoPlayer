#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - CPU Analyzer

Detailed CPU analysis with bottleneck detection and recommendations.

Usage:
    uv run analyze_cpu.py                         # Human-readable output
    uv run analyze_cpu.py --json                  # JSON output
    uv run analyze_cpu.py --threshold 80.0        # Custom threshold
    uv run analyze_cpu.py --verbose               # Detailed output

Exit Codes:
    0 - Healthy (CPU usage below threshold)
    1 - Warning (CPU usage elevated but manageable)
    2 - Critical (CPU usage at dangerous levels)
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
class CPUMetrics:
    """CPU performance metrics."""
    usage_percent: float
    core_count: int
    per_core_usage: list[float]
    temperature: Optional[float]
    frequency_current: float
    frequency_max: float
    load_average: tuple[float, float, float]
    context_switches: int
    interrupts: int


@dataclass
class CPUAnalysis:
    """CPU analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class CPUAnalyzer:
    """Detailed CPU analysis and recommendations."""

    # Default thresholds
    THRESHOLD_WARNING = 70.0
    THRESHOLD_CRITICAL = 85.0
    CORE_IMBALANCE_THRESHOLD = 30.0  # Percentage difference for imbalance detection

    def __init__(self, threshold: float = 70.0, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose
        self.recommendations = []

    def collect_metrics(self) -> CPUMetrics:
        """Collect comprehensive CPU metrics."""
        # Overall CPU usage
        usage_percent = psutil.cpu_percent(interval=1)

        # CPU core information
        core_count = psutil.cpu_count(logical=True)
        per_core_usage = psutil.cpu_percent(interval=1, percpu=True)

        # CPU frequency
        freq = psutil.cpu_freq()
        frequency_current = freq.current if freq else 0.0
        frequency_max = freq.max if freq else 0.0

        # Load average (1, 5, 15 minutes)
        try:
            load_average = psutil.getloadavg()
        except AttributeError:
            # Not available on all platforms
            load_average = (0.0, 0.0, 0.0)

        # System statistics
        cpu_stats = psutil.cpu_stats()
        context_switches = cpu_stats.ctx_switches
        interrupts = cpu_stats.interrupts

        # Temperature (if available)
        temperature = self._get_cpu_temperature()

        return CPUMetrics(
            usage_percent=usage_percent,
            core_count=core_count,
            per_core_usage=per_core_usage,
            temperature=temperature,
            frequency_current=frequency_current,
            frequency_max=frequency_max,
            load_average=load_average,
            context_switches=context_switches,
            interrupts=interrupts
        )

    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Try to find CPU-specific temperature
            cpu_temps = []

            # Look for CPU package or core temperatures
            for name, entries in temps.items():
                if 'cpu' in name.lower() or 'core' in name.lower():
                    for entry in entries:
                        if entry.current:
                            cpu_temps.append(entry.current)

            if cpu_temps:
                return sum(cpu_temps) / len(cpu_temps)

            # Fall back to any temperature sensor
            all_temps = []
            for entries in temps.values():
                for entry in entries:
                    if entry.current:
                        all_temps.append(entry.current)

            if all_temps:
                return sum(all_temps) / len(all_temps)

            return None
        except Exception:
            return None

    def detect_bottlenecks(self, metrics: CPUMetrics) -> list[str]:
        """Detect CPU bottlenecks and issues."""
        bottlenecks = []

        # High overall usage
        if metrics.usage_percent >= self.THRESHOLD_CRITICAL:
            bottlenecks.append("Critical: CPU usage at dangerous levels")
        elif metrics.usage_percent >= self.threshold:
            bottlenecks.append("Warning: CPU usage elevated")

        # Core imbalance detection
        if metrics.per_core_usage:
            max_core = max(metrics.per_core_usage)
            min_core = min(metrics.per_core_usage)
            difference = max_core - min_core

            if difference >= self.CORE_IMBALANCE_THRESHOLD:
                bottlenecks.append(
                    f"Core imbalance detected: {difference:.1f}% difference "
                    f"(max: {max_core:.1f}%, min: {min_core:.1f}%)"
                )

        # High load average
        load_1min, load_5min, load_15min = metrics.load_average
        if load_1min > metrics.core_count * 0.7:
            bottlenecks.append(
                f"High load average: {load_1min:.2f} (1min) on {metrics.core_count} cores"
            )

        # Temperature issues
        if metrics.temperature:
            if metrics.temperature >= 85.0:
                bottlenecks.append(f"Critical: High CPU temperature ({metrics.temperature:.1f}°C)")
            elif metrics.temperature >= 75.0:
                bottlenecks.append(f"Warning: Elevated CPU temperature ({metrics.temperature:.1f}°C)")

        # Frequency throttling detection
        if metrics.frequency_max > 0:
            frequency_ratio = metrics.frequency_current / metrics.frequency_max
            if frequency_ratio < 0.7:
                bottlenecks.append(
                    f"CPU frequency throttled: {metrics.frequency_current:.0f}MHz "
                    f"(max: {metrics.frequency_max:.0f}MHz)"
                )

        return bottlenecks

    def generate_recommendations(self, metrics: CPUMetrics, bottlenecks: list[str]) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # High CPU usage recommendations
        if metrics.usage_percent >= self.THRESHOLD_CRITICAL:
            recommendations.append("URGENT: Identify and terminate resource-intensive processes")
            recommendations.append("Check Activity Monitor for top CPU consumers")
            recommendations.append("Consider restarting affected applications")
        elif metrics.usage_percent >= self.threshold:
            recommendations.append("Monitor CPU usage trends over time")
            recommendations.append("Identify processes consuming most CPU")
            recommendations.append("Consider closing unused applications")

        # Core imbalance recommendations
        if any("imbalance" in b.lower() for b in bottlenecks):
            recommendations.append("Check for single-threaded workloads")
            recommendations.append("Consider process affinity optimization")
            recommendations.append("Review application multithreading implementation")

        # Temperature recommendations
        if metrics.temperature and metrics.temperature >= 75.0:
            recommendations.append("Clean dust from cooling vents")
            recommendations.append("Ensure adequate ventilation")
            recommendations.append("Check thermal paste condition")
            recommendations.append("Consider using cooling pad")

        # Frequency throttling recommendations
        if metrics.frequency_max > 0:
            frequency_ratio = metrics.frequency_current / metrics.frequency_max
            if frequency_ratio < 0.7:
                recommendations.append("CPU may be throttling due to heat or power limits")
                recommendations.append("Check power management settings")
                recommendations.append("Verify cooling system is working properly")

        # Load average recommendations
        load_1min = metrics.load_average[0]
        if load_1min > metrics.core_count:
            recommendations.append("System under heavy load")
            recommendations.append("Review running processes and services")
            recommendations.append("Consider upgrading hardware for workload")

        # General optimization recommendations
        if not recommendations:
            recommendations.append("CPU performance is healthy")
            recommendations.append("Continue monitoring for trend analysis")

        return recommendations

    def determine_risk_level(self, metrics: CPUMetrics) -> str:
        """Determine overall CPU risk level."""
        if metrics.usage_percent >= self.THRESHOLD_CRITICAL:
            return "critical"
        elif metrics.usage_percent >= self.threshold:
            return "warning"
        else:
            return "low"

    def analyze(self) -> CPUAnalysis:
        """Perform complete CPU analysis."""
        import time

        metrics = self.collect_metrics()
        bottlenecks = self.detect_bottlenecks(metrics)
        recommendations = self.generate_recommendations(metrics, bottlenecks)
        risk_level = self.determine_risk_level(metrics)

        status = "healthy"
        if risk_level == "critical":
            status = "critical"
        elif risk_level == "warning":
            status = "warning"

        analysis = CPUAnalysis(
            category="cpu",
            timestamp=time.time(),
            metrics=asdict(metrics),
            analysis={
                "status": status,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "warnings": bottlenecks
            }
        )

        return analysis


def format_human_readable(analysis: CPUAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} CPU Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Metrics
    metrics = analysis.metrics
    lines.append("CPU Metrics:")
    lines.append(f"  Overall Usage: {metrics['usage_percent']:.1f}%")
    lines.append(f"  Core Count: {metrics['core_count']}")

    if verbose and metrics['per_core_usage']:
        lines.append("  Per-Core Usage:")
        for i, usage in enumerate(metrics['per_core_usage']):
            lines.append(f"    Core {i}: {usage:.1f}%")

    if metrics['frequency_current'] > 0:
        lines.append(f"  Frequency: {metrics['frequency_current']:.0f} MHz (max: {metrics['frequency_max']:.0f} MHz)")

    if metrics['temperature'] is not None:
        lines.append(f"  Temperature: {metrics['temperature']:.1f}°C")

    load_avg = metrics['load_average']
    lines.append(f"  Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f} (1m, 5m, 15m)")

    if verbose:
        lines.append(f"  Context Switches: {metrics['context_switches']:,}")
        lines.append(f"  Interrupts: {metrics['interrupts']:,}")

    lines.append("")

    # Warnings (bottlenecks)
    warnings = analysis.analysis["warnings"]
    if warnings:
        lines.append("🔍 Detected Bottlenecks:")
        for warning in warnings:
            lines.append(f"  - {warning}")
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
@click.option('--threshold', type=float, default=70.0, help='CPU usage threshold (default: 70.0)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed CPU analysis with recommendations.

    Analyzes CPU usage, frequency, temperature, load average, and per-core utilization.
    Detects bottlenecks and provides specific optimization recommendations.
    """
    try:
        analyzer = CPUAnalyzer(threshold=threshold, verbose=verbose)
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
            "category": "cpu",
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
