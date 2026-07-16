#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Disk Analyzer

Detailed disk I/O and storage analysis with bottleneck detection and recommendations.

Usage:
    uv run analyze_disk.py                         # Human-readable output
    uv run analyze_disk.py --json                  # JSON output
    uv run analyze_disk.py --threshold 90.0        # Custom threshold
    uv run analyze_disk.py --verbose               # Detailed output

Exit Codes:
    0 - Healthy (disk usage below threshold)
    1 - Warning (disk usage elevated but manageable)
    2 - Critical (disk usage at dangerous levels)
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
class PartitionInfo:
    """Disk partition information."""
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class DiskMetrics:
    """Disk performance metrics."""
    partitions: list[dict]
    io_stats: dict
    read_time_ms: float
    write_time_ms: float
    iops: float


@dataclass
class DiskAnalysis:
    """Disk analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class DiskAnalyzer:
    """Detailed disk analysis and recommendations."""

    # Default thresholds
    THRESHOLD_WARNING = 80.0
    THRESHOLD_CRITICAL = 90.0
    IO_TIME_WARNING = 100.0  # milliseconds
    IO_TIME_CRITICAL = 200.0  # milliseconds

    # Excluded filesystem types (not physical disks)
    EXCLUDED_FSTYPES = {'devfs', 'autofs', 'nullfs', 'apfs_snap'}

    def __init__(self, threshold: float = 90.0, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose

    def collect_metrics(self) -> DiskMetrics:
        """Collect comprehensive disk metrics."""
        # Partition information
        partitions = []
        for partition in psutil.disk_partitions(all=False):
            # Skip excluded filesystem types
            if partition.fstype in self.EXCLUDED_FSTYPES:
                continue

            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except PermissionError:
                # Skip partitions we can't access
                continue
            except Exception:
                # Skip problematic partitions
                continue

        # I/O statistics
        io_counters = psutil.disk_io_counters()

        if io_counters:
            io_stats = {
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes,
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count
            }

            # Calculate read/write time and IOPS
            read_time_ms = io_counters.read_time if hasattr(io_counters, 'read_time') else 0.0
            write_time_ms = io_counters.write_time if hasattr(io_counters, 'write_time') else 0.0

            # Calculate IOPS (I/O operations per second)
            total_io_ops = io_counters.read_count + io_counters.write_count
            # Estimate IOPS based on total operations (this is cumulative since boot)
            # For real-time IOPS, would need to sample over time
            iops = total_io_ops / max(read_time_ms + write_time_ms, 1) * 1000 if (read_time_ms + write_time_ms) > 0 else 0.0
        else:
            io_stats = {
                "read_bytes": 0,
                "write_bytes": 0,
                "read_count": 0,
                "write_count": 0
            }
            read_time_ms = 0.0
            write_time_ms = 0.0
            iops = 0.0

        return DiskMetrics(
            partitions=partitions,
            io_stats=io_stats,
            read_time_ms=read_time_ms,
            write_time_ms=write_time_ms,
            iops=iops
        )

    def detect_issues(self, metrics: DiskMetrics) -> list[str]:
        """Detect disk-related issues."""
        issues = []

        # Check each partition for space issues
        for partition in metrics.partitions:
            percent = partition['percent']
            mountpoint = partition['mountpoint']

            if percent >= self.THRESHOLD_CRITICAL:
                issues.append(
                    f"Critical: {mountpoint} is {percent:.1f}% full "
                    f"({self._format_bytes(partition['free'])} remaining)"
                )
            elif percent >= self.threshold:
                issues.append(
                    f"Warning: {mountpoint} is {percent:.1f}% full "
                    f"({self._format_bytes(partition['free'])} remaining)"
                )

        # I/O performance issues
        if metrics.read_time_ms >= self.IO_TIME_CRITICAL:
            issues.append(
                f"Critical: High disk read time ({metrics.read_time_ms:.0f}ms) - "
                "possible I/O bottleneck"
            )
        elif metrics.read_time_ms >= self.IO_TIME_WARNING:
            issues.append(
                f"Warning: Elevated disk read time ({metrics.read_time_ms:.0f}ms)"
            )

        if metrics.write_time_ms >= self.IO_TIME_CRITICAL:
            issues.append(
                f"Critical: High disk write time ({metrics.write_time_ms:.0f}ms) - "
                "possible I/O bottleneck"
            )
        elif metrics.write_time_ms >= self.IO_TIME_WARNING:
            issues.append(
                f"Warning: Elevated disk write time ({metrics.write_time_ms:.0f}ms)"
            )

        # Check for extremely low IOPS (potential performance issue)
        if metrics.iops > 0 and metrics.iops < 10:
            issues.append(
                f"Warning: Low IOPS detected ({metrics.iops:.1f}) - "
                "disk performance may be degraded"
            )

        return issues

    def generate_recommendations(
        self,
        metrics: DiskMetrics,
        issues: list[str]
    ) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Critical disk space recommendations
        critical_partitions = [p for p in metrics.partitions if p['percent'] >= self.THRESHOLD_CRITICAL]
        if critical_partitions:
            recommendations.append("URGENT: Free up disk space immediately")
            recommendations.append("Clear cache and temporary files")
            recommendations.append("Empty Trash/Downloads folder")
            recommendations.append("Use Storage Management to identify large files")
            recommendations.append("Consider archiving old files to external storage")

        # High disk usage recommendations
        warning_partitions = [p for p in metrics.partitions if p['percent'] >= self.threshold and p['percent'] < self.THRESHOLD_CRITICAL]
        if warning_partitions:
            recommendations.append("Monitor disk space trends")
            recommendations.append("Run disk cleanup utilities")
            recommendations.append("Remove unused applications")
            recommendations.append("Clear browser cache and downloads")

        # I/O performance recommendations
        if metrics.read_time_ms >= self.IO_TIME_WARNING or metrics.write_time_ms >= self.IO_TIME_WARNING:
            recommendations.append("Check for disk-intensive processes in Activity Monitor")
            recommendations.append("Consider using SSD for better I/O performance")
            recommendations.append("Verify disk health with Disk Utility")

            if metrics.read_time_ms >= self.IO_TIME_CRITICAL or metrics.write_time_ms >= self.IO_TIME_CRITICAL:
                recommendations.append("URGENT: Investigate I/O bottleneck")
                recommendations.append("Check for failing disk with S.M.A.R.T. status")
                recommendations.append("Backup important data immediately")

        # Low IOPS recommendations
        if metrics.iops > 0 and metrics.iops < 10:
            recommendations.append("Disk performance appears degraded")
            recommendations.append("Check for background processes performing heavy I/O")
            recommendations.append("Consider defragmentation (if HDD)")
            recommendations.append("Verify no disk errors in system logs")

        # General optimization recommendations
        if not recommendations:
            recommendations.append("Disk health and performance are good")
            recommendations.append("Continue monitoring disk usage trends")
            recommendations.append("Periodically clean temporary files")

        return recommendations

    def determine_risk_level(self, metrics: DiskMetrics) -> str:
        """Determine overall disk risk level."""
        # Check for critical conditions
        for partition in metrics.partitions:
            if partition['percent'] >= self.THRESHOLD_CRITICAL:
                return "critical"

        if (metrics.read_time_ms >= self.IO_TIME_CRITICAL or
            metrics.write_time_ms >= self.IO_TIME_CRITICAL):
            return "critical"

        # Check for warning conditions
        for partition in metrics.partitions:
            if partition['percent'] >= self.threshold:
                return "warning"

        if (metrics.read_time_ms >= self.IO_TIME_WARNING or
            metrics.write_time_ms >= self.IO_TIME_WARNING):
            return "warning"

        return "low"

    def analyze(self) -> DiskAnalysis:
        """Perform complete disk analysis."""
        metrics = self.collect_metrics()
        issues = self.detect_issues(metrics)
        recommendations = self.generate_recommendations(metrics, issues)
        risk_level = self.determine_risk_level(metrics)

        status = "healthy"
        if risk_level == "critical":
            status = "critical"
        elif risk_level == "warning":
            status = "warning"

        analysis = DiskAnalysis(
            category="disk",
            timestamp=datetime.now().timestamp(),
            metrics=asdict(metrics),
            analysis={
                "status": status,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "warnings": issues
            }
        )

        return analysis

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"


def format_human_readable(analysis: DiskAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} Disk Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Partition metrics
    partitions = analysis.metrics['partitions']
    if partitions:
        lines.append("Disk Partitions:")
        for partition in partitions:
            total_gb = partition['total'] / (1024 ** 3)
            used_gb = partition['used'] / (1024 ** 3)
            free_gb = partition['free'] / (1024 ** 3)

            lines.append(f"  {partition['mountpoint']}:")
            lines.append(f"    Total: {total_gb:.2f} GB")
            lines.append(f"    Used: {used_gb:.2f} GB ({partition['percent']:.1f}%)")
            lines.append(f"    Free: {free_gb:.2f} GB")

            if verbose:
                lines.append(f"    Device: {partition['device']}")
                lines.append(f"    Filesystem: {partition['fstype']}")

        lines.append("")

    # I/O statistics
    io_stats = analysis.metrics['io_stats']
    if io_stats:
        lines.append("I/O Statistics:")

        read_gb = io_stats['read_bytes'] / (1024 ** 3)
        write_gb = io_stats['write_bytes'] / (1024 ** 3)

        lines.append(f"  Read: {read_gb:.2f} GB ({io_stats['read_count']:,} operations)")
        lines.append(f"  Write: {write_gb:.2f} GB ({io_stats['write_count']:,} operations)")

        if verbose:
            lines.append(f"  Read Time: {analysis.metrics['read_time_ms']:.0f} ms")
            lines.append(f"  Write Time: {analysis.metrics['write_time_ms']:.0f} ms")

        if analysis.metrics['iops'] > 0:
            lines.append(f"  IOPS: {analysis.metrics['iops']:.1f}")

        lines.append("")

    # Warnings
    warnings = analysis.analysis["warnings"]
    if warnings:
        lines.append("🔍 Detected Issues:")
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
@click.option('--threshold', type=float, default=90.0, help='Disk usage threshold (default: 90.0)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed disk I/O and storage analysis with recommendations.

    Analyzes disk usage, I/O statistics, IOPS, and partition health.
    Detects storage bottlenecks and provides specific optimization recommendations.
    """
    try:
        analyzer = DiskAnalyzer(threshold=threshold, verbose=verbose)
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
            "category": "disk",
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
