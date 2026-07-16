#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "psutil>=5.9.0",
#   "click>=8.1.0",
# ]
# ///
"""
Disk Analysis Script for macOS Resource Optimizer

Analyzes disk I/O performance, storage usage, and provides actionable recommendations.
Exit codes: 0 (healthy), 1 (medium risk), 2 (high risk), 3 (error)
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
import psutil
import click


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_THRESHOLD = 85.0    # Default disk usage threshold (%)
USAGE_WARNING = 75.0        # Disk usage warning threshold (%)
USAGE_CRITICAL = 90.0       # Disk usage critical threshold (%)
FREE_SPACE_WARNING = 10.0   # Free space warning threshold (GB)
FREE_SPACE_CRITICAL = 5.0   # Free space critical threshold (GB)
IO_SAMPLE_INTERVAL = 1.0    # I/O sampling interval (seconds)
IO_SAMPLE_COUNT = 3         # Number of I/O samples to collect


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class DiskMetrics:
    """Complete disk metrics data structure"""
    # Storage metrics
    total_space: float  # GB
    used_space: float   # GB
    free_space: float   # GB
    percent_used: float

    # I/O metrics
    read_bytes: int
    write_bytes: int
    read_time: int      # milliseconds
    write_time: int     # milliseconds
    iops: float         # I/O operations per second

    # Partition details
    partitions: List[Dict[str, Any]]

    # Risk assessment
    risk_level: str  # "low", "medium", "high"
    exit_code: int   # 0, 1, 2

    # Recommendations
    recommendations: List[str]
    warnings: List[str]


# ============================================================================
# Disk Analyzer
# ============================================================================

class DiskAnalyzer:
    """Main disk analysis engine"""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, verbose: bool = False):
        """
        Initialize disk analyzer

        Args:
            threshold: Disk usage threshold for warnings (%)
            verbose: Enable verbose output
        """
        self.threshold = threshold
        self.verbose = verbose
        self._log(f"Initialized disk analyzer (threshold={threshold}%)")

    def _log(self, message: str):
        """Print verbose log message"""
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)

    def collect_metrics(self) -> DiskMetrics:
        """
        Collect all disk metrics

        Returns:
            DiskMetrics object with complete disk state
        """
        self._log("Collecting disk metrics...")

        # Get primary disk usage (root partition)
        disk_usage = psutil.disk_usage('/')

        total_gb = disk_usage.total / (1024 ** 3)
        used_gb = disk_usage.used / (1024 ** 3)
        free_gb = disk_usage.free / (1024 ** 3)
        percent_used = disk_usage.percent

        self._log(f"Primary disk: {used_gb:.2f} GB / {total_gb:.2f} GB ({percent_used:.1f}%)")

        # Collect I/O statistics
        read_bytes, write_bytes, read_time, write_time, iops = self._collect_io_stats()

        # Collect partition details
        partitions = self._get_partitions()

        # Analyze risk level
        risk_level, exit_code = self._assess_risk(
            percent_used, free_gb, iops
        )

        # Generate recommendations
        recommendations, warnings = self._generate_recommendations(
            percent_used, free_gb, total_gb, iops, partitions
        )

        return DiskMetrics(
            total_space=round(total_gb, 2),
            used_space=round(used_gb, 2),
            free_space=round(free_gb, 2),
            percent_used=round(percent_used, 2),
            read_bytes=read_bytes,
            write_bytes=write_bytes,
            read_time=read_time,
            write_time=write_time,
            iops=round(iops, 2),
            partitions=partitions,
            risk_level=risk_level,
            exit_code=exit_code,
            recommendations=recommendations,
            warnings=warnings
        )

    def _collect_io_stats(self) -> Tuple[int, int, int, int, float]:
        """
        Collect disk I/O statistics with sampling

        Returns:
            (read_bytes, write_bytes, read_time, write_time, iops)
        """
        self._log(f"Sampling disk I/O ({IO_SAMPLE_COUNT} samples, {IO_SAMPLE_INTERVAL}s interval)...")

        try:
            # Initial snapshot
            io_start = psutil.disk_io_counters()
            if not io_start:
                self._log("I/O counters not available")
                return (0, 0, 0, 0, 0.0)

            start_time = time.time()
            start_read = io_start.read_bytes
            start_write = io_start.write_bytes
            start_read_count = io_start.read_count
            start_write_count = io_start.write_count

            # Collect samples
            samples = []
            for i in range(IO_SAMPLE_COUNT):
                time.sleep(IO_SAMPLE_INTERVAL)

                io_sample = psutil.disk_io_counters()
                if not io_sample:
                    continue

                elapsed = time.time() - start_time

                # Calculate deltas
                read_delta = io_sample.read_bytes - start_read
                write_delta = io_sample.write_bytes - start_write
                read_count_delta = io_sample.read_count - start_read_count
                write_count_delta = io_sample.write_count - start_write_count

                # Calculate IOPS for this sample
                sample_iops = (read_count_delta + write_count_delta) / elapsed if elapsed > 0 else 0

                samples.append({
                    'read_bytes': read_delta,
                    'write_bytes': write_delta,
                    'iops': sample_iops
                })

                self._log(f"  Sample {i+1}: IOPS={sample_iops:.1f}, Read={read_delta/1024:.1f}KB, Write={write_delta/1024:.1f}KB")

            # Final snapshot
            io_end = psutil.disk_io_counters()
            if not io_end:
                return (0, 0, 0, 0, 0.0)

            # Calculate total deltas
            total_read = io_end.read_bytes - start_read
            total_write = io_end.write_bytes - start_write
            total_read_time = io_end.read_time - io_start.read_time
            total_write_time = io_end.write_time - io_start.write_time

            # Calculate average IOPS
            avg_iops = sum(s['iops'] for s in samples) / len(samples) if samples else 0.0

            self._log(f"Average IOPS: {avg_iops:.1f}")

            return (
                int(total_read),
                int(total_write),
                int(total_read_time),
                int(total_write_time),
                avg_iops
            )

        except Exception as e:
            self._log(f"I/O statistics collection failed: {e}")
            return (0, 0, 0, 0, 0.0)

    def _calculate_iops(self, read_count: int, write_count: int, elapsed: float) -> float:
        """
        Calculate I/O operations per second

        Args:
            read_count: Number of read operations
            write_count: Number of write operations
            elapsed: Elapsed time in seconds

        Returns:
            IOPS value
        """
        if elapsed <= 0:
            return 0.0

        total_ops = read_count + write_count
        iops = total_ops / elapsed

        return iops

    def _get_partitions(self) -> List[Dict[str, Any]]:
        """
        Get details for all mounted partitions

        Returns:
            List of partition dicts with usage info
        """
        partitions = []

        try:
            for part in psutil.disk_partitions(all=False):
                # Skip non-physical partitions
                if 'cdrom' in part.opts or part.fstype == '':
                    continue

                try:
                    usage = psutil.disk_usage(part.mountpoint)

                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total_gb': round(usage.total / (1024 ** 3), 2),
                        'used_gb': round(usage.used / (1024 ** 3), 2),
                        'free_gb': round(usage.free / (1024 ** 3), 2),
                        'percent_used': round(usage.percent, 2)
                    })

                except (PermissionError, OSError):
                    # Skip partitions we can't access
                    continue

        except Exception as e:
            self._log(f"Partition enumeration failed: {e}")

        self._log(f"Found {len(partitions)} accessible partitions")
        return partitions

    def _assess_risk(
        self,
        percent_used: float,
        free_gb: float,
        iops: float
    ) -> Tuple[str, int]:
        """
        Assess disk risk level

        Args:
            percent_used: Disk usage percentage
            free_gb: Free space in GB
            iops: I/O operations per second

        Returns:
            (risk_level, exit_code)
        """
        # High risk conditions
        high_risk_conditions = []

        if percent_used >= USAGE_CRITICAL:
            high_risk_conditions.append(f"Disk usage critical: {percent_used:.1f}%")

        if free_gb < FREE_SPACE_CRITICAL:
            high_risk_conditions.append(f"Critical low free space: {free_gb:.2f} GB")

        if high_risk_conditions:
            self._log(f"Risk assessment: HIGH ({', '.join(high_risk_conditions)})")
            return ("high", 2)

        # Medium risk conditions
        medium_risk_conditions = []

        if percent_used >= self.threshold:
            medium_risk_conditions.append(f"Disk usage high: {percent_used:.1f}%")

        if free_gb < FREE_SPACE_WARNING:
            medium_risk_conditions.append(f"Low free space: {free_gb:.2f} GB")

        if medium_risk_conditions:
            self._log(f"Risk assessment: MEDIUM ({', '.join(medium_risk_conditions)})")
            return ("medium", 1)

        # Low risk
        self._log("Risk assessment: LOW (all metrics healthy)")
        return ("low", 0)

    def _generate_recommendations(
        self,
        percent_used: float,
        free_gb: float,
        total_gb: float,
        iops: float,
        partitions: List[Dict]
    ) -> Tuple[List[str], List[str]]:
        """
        Generate actionable recommendations and warnings

        Returns:
            (recommendations, warnings)
        """
        recommendations = []
        warnings = []

        # Critical disk usage
        if percent_used >= USAGE_CRITICAL:
            warnings.append(f"Disk usage critical at {percent_used:.1f}%")
            recommendations.append("URGENT: Free up disk space immediately")
            recommendations.append("Delete unnecessary files and empty trash")
            recommendations.append("Remove old Time Machine backups")
            recommendations.append("Clear application caches and temporary files")

        # High disk usage
        elif percent_used >= self.threshold:
            warnings.append(f"Disk usage high at {percent_used:.1f}%")
            recommendations.append("Review and delete unnecessary files")
            recommendations.append("Empty trash and clear browser cache")
            recommendations.append("Consider moving large files to external storage")

        # Low free space
        if free_gb < FREE_SPACE_CRITICAL:
            warnings.append(f"Critical low free space: {free_gb:.2f} GB remaining")
            recommendations.append("System may become unstable with <5 GB free space")
            recommendations.append("Free up space immediately to prevent system issues")

        elif free_gb < FREE_SPACE_WARNING:
            warnings.append(f"Low free space: {free_gb:.2f} GB remaining")
            recommendations.append("Maintain at least 10 GB free space for system stability")

        # I/O performance analysis
        if iops > 0:
            # Low IOPS might indicate slow disk or heavy usage
            if iops < 50:
                recommendations.append(f"Low I/O performance detected (IOPS: {iops:.1f})")
                recommendations.append("Consider checking for background processes")

            # Very high IOPS might indicate excessive disk activity
            elif iops > 1000:
                recommendations.append(f"High disk activity detected (IOPS: {iops:.1f})")
                recommendations.append("Review applications performing heavy disk I/O")

        # Partition-specific warnings
        for part in partitions:
            if part['percent_used'] >= USAGE_CRITICAL:
                warnings.append(f"Partition '{part['mountpoint']}' critically full ({part['percent_used']:.1f}%)")

        # Fragmentation warning (for HDDs, less relevant for SSDs)
        if percent_used > 80:
            recommendations.append("Consider defragmentation if using HDD (not needed for SSD)")

        # Storage optimization recommendations
        if percent_used < 50:
            recommendations.append("Disk usage is healthy")
            recommendations.append("Consider regular cleanup to maintain performance")

        self._log(f"Generated {len(recommendations)} recommendations, {len(warnings)} warnings")
        return recommendations, warnings

    def analyze(self) -> DiskMetrics:
        """
        Perform complete disk analysis

        Returns:
            DiskMetrics with all analysis results
        """
        return self.collect_metrics()


# ============================================================================
# Output Formatting
# ============================================================================

def format_human_readable(metrics: DiskMetrics) -> str:
    """
    Format metrics for human-readable output

    Args:
        metrics: DiskMetrics to format

    Returns:
        Formatted string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("Disk Analysis Report")
    lines.append("=" * 60)
    lines.append("")

    # Overall status
    risk_symbols = {"low": "✓", "medium": "⚠", "high": "✗"}

    risk_symbol = risk_symbols[metrics.risk_level]
    lines.append(f"Status: {risk_symbol} {metrics.risk_level.upper()} RISK")
    lines.append("")

    # Storage Usage
    lines.append("Storage Usage:")
    lines.append(f"  Total:        {metrics.total_space:.2f} GB")
    lines.append(f"  Used:         {metrics.used_space:.2f} GB ({metrics.percent_used:.1f}%)")
    lines.append(f"  Free:         {metrics.free_space:.2f} GB")
    lines.append("")

    # I/O Performance
    lines.append("I/O Performance:")
    lines.append(f"  IOPS:         {metrics.iops:.2f}")

    read_mb = metrics.read_bytes / (1024 ** 2)
    write_mb = metrics.write_bytes / (1024 ** 2)

    lines.append(f"  Read:         {read_mb:.2f} MB ({metrics.read_time} ms)")
    lines.append(f"  Write:        {write_mb:.2f} MB ({metrics.write_time} ms)")
    lines.append("")

    # Partitions
    if metrics.partitions:
        lines.append("Mounted Partitions:")
        for part in metrics.partitions:
            lines.append(f"  {part['mountpoint']}")
            lines.append(f"    Device:     {part['device']}")
            lines.append(f"    Type:       {part['fstype']}")
            lines.append(f"    Size:       {part['total_gb']:.2f} GB")
            lines.append(f"    Used:       {part['used_gb']:.2f} GB ({part['percent_used']:.1f}%)")
            lines.append(f"    Free:       {part['free_gb']:.2f} GB")
        lines.append("")

    # Warnings
    if metrics.warnings:
        lines.append("Warnings:")
        for warning in metrics.warnings:
            lines.append(f"  ⚠ {warning}")
        lines.append("")

    # Recommendations
    if metrics.recommendations:
        lines.append("Recommendations:")
        for i, rec in enumerate(metrics.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(str(line) for line in lines)


# ============================================================================
# CLI Interface
# ============================================================================

@click.command()
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format"
)
@click.option(
    "--threshold",
    type=float,
    default=DEFAULT_THRESHOLD,
    help=f"Disk usage threshold for warnings (default: {DEFAULT_THRESHOLD}%)"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Analyze disk I/O performance and storage usage.

    Exit codes:
      0 - Disk healthy (low risk)
      1 - Disk under stress (medium risk)
      2 - Disk critical (high risk)
      3 - Analysis error
    """
    try:
        # Create analyzer
        analyzer = DiskAnalyzer(threshold=threshold, verbose=verbose)

        # Perform analysis
        metrics = analyzer.analyze()

        # Output results
        if output_json:
            # JSON output
            output = asdict(metrics)
            click.echo(json.dumps(output, indent=2))
        else:
            # Human-readable output
            output = format_human_readable(metrics)
            click.echo(output)

        # Exit with appropriate code
        sys.exit(metrics.exit_code)

    except KeyboardInterrupt:
        click.echo("\nAnalysis interrupted", err=True)
        sys.exit(3)

    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
