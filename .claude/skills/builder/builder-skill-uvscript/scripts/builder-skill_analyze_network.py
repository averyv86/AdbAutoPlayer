#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "psutil>=5.9.0",
#   "click>=8.1.0",
# ]
# ///
"""
Network Analysis Script for macOS Resource Optimizer

Analyzes network I/O, connection count, bandwidth utilization, and provides actionable recommendations.
Exit codes: 0 (healthy), 1 (medium risk), 2 (high risk), 3 (error)
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import psutil
import click


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_BANDWIDTH_THRESHOLD = 80.0  # Default bandwidth usage threshold (%)
DEFAULT_CONNECTION_THRESHOLD = 500  # Default connection count threshold
SAMPLE_INTERVAL = 2.0              # Network I/O sampling interval (seconds)
SAMPLE_COUNT = 3                   # Number of samples to average
ERROR_RATE_THRESHOLD = 1.0         # Error rate threshold (%)
DROP_RATE_THRESHOLD = 1.0          # Drop rate threshold (%)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class NetworkMetrics:
    """Complete network metrics data structure"""
    # I/O metrics
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int

    # Connection metrics
    connection_count: int
    established_count: int
    listening_count: int
    time_wait_count: int
    close_wait_count: int

    # Bandwidth metrics
    bandwidth_usage_mb: float
    bytes_sent_per_sec: float
    bytes_received_per_sec: float

    # Quality metrics
    error_rate_pct: float
    drop_rate_pct: float

    # Top connections
    top_connections: List[Dict[str, any]]

    # Risk assessment
    risk_level: str  # "low", "medium", "high"
    exit_code: int   # 0, 1, 2

    # Recommendations
    recommendations: List[str]
    warnings: List[str]


# ============================================================================
# Network Analyzer
# ============================================================================

class NetworkAnalyzer:
    """Main network analysis engine"""

    def __init__(
        self,
        bandwidth_threshold: float = DEFAULT_BANDWIDTH_THRESHOLD,
        connection_threshold: int = DEFAULT_CONNECTION_THRESHOLD,
        verbose: bool = False
    ):
        """
        Initialize network analyzer

        Args:
            bandwidth_threshold: Bandwidth usage threshold for warnings (%)
            connection_threshold: Connection count threshold for warnings
            verbose: Enable verbose output
        """
        self.bandwidth_threshold = bandwidth_threshold
        self.connection_threshold = connection_threshold
        self.verbose = verbose
        self._log(f"Initialized network analyzer (bandwidth_threshold={bandwidth_threshold}%, connection_threshold={connection_threshold})")

    def _log(self, message: str):
        """Print verbose log message"""
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)

    def collect_metrics(self) -> NetworkMetrics:
        """
        Collect all network metrics

        Returns:
            NetworkMetrics object with complete network state
        """
        self._log("Collecting network metrics...")

        # Collect initial network I/O stats
        net_io_start = psutil.net_io_counters()
        time.sleep(SAMPLE_INTERVAL)
        net_io_end = psutil.net_io_counters()

        # Calculate per-second rates
        bytes_sent_per_sec = (net_io_end.bytes_sent - net_io_start.bytes_sent) / SAMPLE_INTERVAL
        bytes_received_per_sec = (net_io_end.bytes_recv - net_io_start.bytes_recv) / SAMPLE_INTERVAL

        self._log(f"Network I/O rate: {bytes_sent_per_sec / 1024 / 1024:.2f} MB/s sent, {bytes_received_per_sec / 1024 / 1024:.2f} MB/s received")

        # Collect connection statistics (may require elevated permissions)
        try:
            connections = psutil.net_connections(kind='inet')
            connection_stats = self._analyze_connections(connections)
            top_connections = self._get_top_connections(connections)
        except (psutil.AccessDenied, PermissionError, OSError) as e:
            # Cannot access connection information without elevated privileges
            self._log(f"Warning: Cannot access connection info (requires sudo): {e}")
            connections = []
            connection_stats = {
                'total': 0,
                'established': 0,
                'listening': 0,
                'time_wait': 0,
                'close_wait': 0,
                'other': 0
            }
            top_connections = []

        # Calculate bandwidth usage
        bandwidth_usage_mb = self._calculate_bandwidth(bytes_sent_per_sec, bytes_received_per_sec)

        # Calculate error and drop rates
        total_packets_in = net_io_end.packets_recv if net_io_end.packets_recv > 0 else 1
        total_packets_out = net_io_end.packets_sent if net_io_end.packets_sent > 0 else 1

        error_rate_pct = ((net_io_end.errin + net_io_end.errout) / (total_packets_in + total_packets_out)) * 100
        drop_rate_pct = ((net_io_end.dropin + net_io_end.dropout) / (total_packets_in + total_packets_out)) * 100

        # Analyze risk level
        risk_level, exit_code = self._assess_risk(
            bandwidth_usage_mb,
            connection_stats['total'],
            error_rate_pct,
            drop_rate_pct
        )

        # Generate recommendations
        recommendations, warnings = self._generate_recommendations(
            bandwidth_usage_mb,
            connection_stats,
            error_rate_pct,
            drop_rate_pct,
            bytes_sent_per_sec,
            bytes_received_per_sec
        )

        return NetworkMetrics(
            bytes_sent=net_io_end.bytes_sent,
            bytes_received=net_io_end.bytes_recv,
            packets_sent=net_io_end.packets_sent,
            packets_received=net_io_end.packets_recv,
            errors_in=net_io_end.errin,
            errors_out=net_io_end.errout,
            drops_in=net_io_end.dropin,
            drops_out=net_io_end.dropout,
            connection_count=connection_stats['total'],
            established_count=connection_stats['established'],
            listening_count=connection_stats['listening'],
            time_wait_count=connection_stats['time_wait'],
            close_wait_count=connection_stats['close_wait'],
            bandwidth_usage_mb=round(bandwidth_usage_mb, 2),
            bytes_sent_per_sec=round(bytes_sent_per_sec, 2),
            bytes_received_per_sec=round(bytes_received_per_sec, 2),
            error_rate_pct=round(error_rate_pct, 4),
            drop_rate_pct=round(drop_rate_pct, 4),
            top_connections=top_connections,
            risk_level=risk_level,
            exit_code=exit_code,
            recommendations=recommendations,
            warnings=warnings
        )

    def _analyze_connections(self, connections: List) -> Dict[str, int]:
        """
        Analyze network connections by status

        Args:
            connections: List of connection objects from psutil

        Returns:
            Dict with connection counts by status
        """
        stats = {
            'total': 0,
            'established': 0,
            'listening': 0,
            'time_wait': 0,
            'close_wait': 0,
            'other': 0
        }

        for conn in connections:
            stats['total'] += 1

            status = conn.status.lower() if hasattr(conn, 'status') else 'none'

            if status == 'established':
                stats['established'] += 1
            elif status == 'listen':
                stats['listening'] += 1
            elif status == 'time_wait':
                stats['time_wait'] += 1
            elif status == 'close_wait':
                stats['close_wait'] += 1
            else:
                stats['other'] += 1

        self._log(f"Connections: {stats['total']} total, {stats['established']} established, {stats['listening']} listening")
        return stats

    def _calculate_bandwidth(self, bytes_sent_per_sec: float, bytes_received_per_sec: float) -> float:
        """
        Calculate current bandwidth usage in MB/s

        Args:
            bytes_sent_per_sec: Bytes sent per second
            bytes_received_per_sec: Bytes received per second

        Returns:
            Total bandwidth usage in MB/s
        """
        total_bytes_per_sec = bytes_sent_per_sec + bytes_received_per_sec
        bandwidth_mb = total_bytes_per_sec / 1024 / 1024

        self._log(f"Bandwidth: {bandwidth_mb:.2f} MB/s")
        return bandwidth_mb

    def _get_top_connections(self, connections: List, count: int = 5) -> List[Dict[str, any]]:
        """
        Get top network connections by process

        Args:
            connections: List of connection objects
            count: Number of top connections to return

        Returns:
            List of connection dicts with process information
        """
        connection_map = {}

        for conn in connections:
            try:
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()

                        if proc_name not in connection_map:
                            connection_map[proc_name] = {
                                'name': proc_name,
                                'pid': conn.pid,
                                'connections': 0,
                                'established': 0
                            }

                        connection_map[proc_name]['connections'] += 1
                        if hasattr(conn, 'status') and conn.status.lower() == 'established':
                            connection_map[proc_name]['established'] += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                pass

        # Sort by connection count
        top = sorted(connection_map.values(), key=lambda x: x['connections'], reverse=True)[:count]

        top_summary = ", ".join([f"{p['name']}({p['connections']})" for p in top])
        self._log(f"Top {count} processes: {top_summary}")
        return top

    def _assess_risk(
        self,
        bandwidth_usage_mb: float,
        connection_count: int,
        error_rate_pct: float,
        drop_rate_pct: float
    ) -> Tuple[str, int]:
        """
        Assess network risk level

        Args:
            bandwidth_usage_mb: Bandwidth usage in MB/s
            connection_count: Total connection count
            error_rate_pct: Error rate percentage
            drop_rate_pct: Drop rate percentage

        Returns:
            (risk_level, exit_code)
        """
        # High risk conditions
        high_risk_conditions = []

        if bandwidth_usage_mb >= 100:  # 100 MB/s = 800 Mbps
            high_risk_conditions.append(f"Bandwidth critical: {bandwidth_usage_mb:.1f} MB/s")

        if connection_count >= 1000:
            high_risk_conditions.append(f"Connection count critical: {connection_count}")

        if error_rate_pct >= 5.0:
            high_risk_conditions.append(f"Error rate critical: {error_rate_pct:.2f}%")

        if drop_rate_pct >= 5.0:
            high_risk_conditions.append(f"Drop rate critical: {drop_rate_pct:.2f}%")

        if high_risk_conditions:
            self._log(f"Risk assessment: HIGH ({', '.join(high_risk_conditions)})")
            return ("high", 2)

        # Medium risk conditions
        medium_risk_conditions = []

        if bandwidth_usage_mb >= 50:  # 50 MB/s = 400 Mbps
            medium_risk_conditions.append(f"Bandwidth high: {bandwidth_usage_mb:.1f} MB/s")

        if connection_count >= self.connection_threshold:
            medium_risk_conditions.append(f"Connection count high: {connection_count}")

        if error_rate_pct >= ERROR_RATE_THRESHOLD:
            medium_risk_conditions.append(f"Error rate high: {error_rate_pct:.2f}%")

        if drop_rate_pct >= DROP_RATE_THRESHOLD:
            medium_risk_conditions.append(f"Drop rate high: {drop_rate_pct:.2f}%")

        if medium_risk_conditions:
            self._log(f"Risk assessment: MEDIUM ({', '.join(medium_risk_conditions)})")
            return ("medium", 1)

        # Low risk
        self._log("Risk assessment: LOW (all metrics healthy)")
        return ("low", 0)

    def _generate_recommendations(
        self,
        bandwidth_usage_mb: float,
        connection_stats: Dict[str, int],
        error_rate_pct: float,
        drop_rate_pct: float,
        bytes_sent_per_sec: float,
        bytes_received_per_sec: float
    ) -> Tuple[List[str], List[str]]:
        """
        Generate actionable recommendations and warnings

        Returns:
            (recommendations, warnings)
        """
        recommendations = []
        warnings = []

        # Bandwidth recommendations
        if bandwidth_usage_mb >= 100:
            warnings.append(f"Bandwidth usage critical at {bandwidth_usage_mb:.1f} MB/s")
            recommendations.append("Check for large file transfers or streaming")
            recommendations.append("Consider upgrading network connection")
        elif bandwidth_usage_mb >= 50:
            warnings.append(f"Bandwidth usage high at {bandwidth_usage_mb:.1f} MB/s")
            recommendations.append("Monitor network-intensive applications")

        # Connection count recommendations
        if connection_stats['total'] >= 1000:
            warnings.append(f"Connection count critical: {connection_stats['total']}")
            recommendations.append("Review applications with many connections")
            recommendations.append("Check for connection leaks or misconfigurations")
        elif connection_stats['total'] >= self.connection_threshold:
            warnings.append(f"Connection count high: {connection_stats['total']}")
            recommendations.append("Monitor connection-intensive applications")

        # TIME_WAIT connections
        if connection_stats['time_wait'] > 100:
            recommendations.append(f"High TIME_WAIT connections: {connection_stats['time_wait']}")
            recommendations.append("Consider tuning TCP time-wait settings")

        # CLOSE_WAIT connections
        if connection_stats['close_wait'] > 50:
            warnings.append(f"High CLOSE_WAIT connections: {connection_stats['close_wait']}")
            recommendations.append("Application may not be closing connections properly")

        # Error rate recommendations
        if error_rate_pct >= 5.0:
            warnings.append(f"Packet error rate critical: {error_rate_pct:.2f}%")
            recommendations.append("Check network cable and hardware")
            recommendations.append("Investigate network driver issues")
        elif error_rate_pct >= ERROR_RATE_THRESHOLD:
            warnings.append(f"Packet error rate high: {error_rate_pct:.2f}%")
            recommendations.append("Monitor network reliability")

        # Drop rate recommendations
        if drop_rate_pct >= 5.0:
            warnings.append(f"Packet drop rate critical: {drop_rate_pct:.2f}%")
            recommendations.append("Network congestion or buffer overflow detected")
            recommendations.append("Consider upgrading network infrastructure")
        elif drop_rate_pct >= DROP_RATE_THRESHOLD:
            warnings.append(f"Packet drop rate high: {drop_rate_pct:.2f}%")
            recommendations.append("Monitor for network congestion")

        # Asymmetric traffic pattern
        if bytes_sent_per_sec > 0 and bytes_received_per_sec > 0:
            ratio = max(bytes_sent_per_sec, bytes_received_per_sec) / min(bytes_sent_per_sec, bytes_received_per_sec)
            if ratio > 10:
                recommendations.append("Asymmetric traffic pattern detected")
                if bytes_sent_per_sec > bytes_received_per_sec:
                    recommendations.append("Heavy upload activity detected")
                else:
                    recommendations.append("Heavy download activity detected")

        self._log(f"Generated {len(recommendations)} recommendations, {len(warnings)} warnings")
        return recommendations, warnings

    def analyze(self) -> NetworkMetrics:
        """
        Perform complete network analysis

        Returns:
            NetworkMetrics with all analysis results
        """
        return self.collect_metrics()


# ============================================================================
# Output Formatting
# ============================================================================

def format_human_readable(metrics: NetworkMetrics) -> str:
    """
    Format metrics for human-readable output

    Args:
        metrics: NetworkMetrics to format

    Returns:
        Formatted string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("Network Analysis Report")
    lines.append("=" * 60)
    lines.append("")

    # Overall status
    risk_symbols = {"low": "✓", "medium": "⚠", "high": "✗"}
    risk_symbol = risk_symbols[metrics.risk_level]
    lines.append(f"Status: {risk_symbol} {metrics.risk_level.upper()} RISK")
    lines.append("")

    # Network I/O
    lines.append("Network I/O:")
    lines.append(f"  Bytes sent:       {metrics.bytes_sent / 1024 / 1024 / 1024:.2f} GB")
    lines.append(f"  Bytes received:   {metrics.bytes_received / 1024 / 1024 / 1024:.2f} GB")
    lines.append(f"  Packets sent:     {metrics.packets_sent:,}")
    lines.append(f"  Packets received: {metrics.packets_received:,}")
    lines.append("")

    # Bandwidth
    lines.append("Bandwidth Usage:")
    lines.append(f"  Current:          {metrics.bandwidth_usage_mb:.2f} MB/s")
    lines.append(f"  Upload rate:      {metrics.bytes_sent_per_sec / 1024 / 1024:.2f} MB/s")
    lines.append(f"  Download rate:    {metrics.bytes_received_per_sec / 1024 / 1024:.2f} MB/s")
    lines.append("")

    # Connections
    lines.append("Connections:")
    lines.append(f"  Total:            {metrics.connection_count}")
    lines.append(f"  Established:      {metrics.established_count}")
    lines.append(f"  Listening:        {metrics.listening_count}")
    lines.append(f"  TIME_WAIT:        {metrics.time_wait_count}")
    lines.append(f"  CLOSE_WAIT:       {metrics.close_wait_count}")
    lines.append("")

    # Quality metrics
    lines.append("Quality Metrics:")
    lines.append(f"  Errors (in):      {metrics.errors_in}")
    lines.append(f"  Errors (out):     {metrics.errors_out}")
    lines.append(f"  Drops (in):       {metrics.drops_in}")
    lines.append(f"  Drops (out):      {metrics.drops_out}")
    lines.append(f"  Error rate:       {metrics.error_rate_pct:.4f}%")
    lines.append(f"  Drop rate:        {metrics.drop_rate_pct:.4f}%")
    lines.append("")

    # Top connections
    if metrics.top_connections:
        lines.append("Top Network Processes:")
        for proc in metrics.top_connections:
            lines.append(f"  {proc['name']:<30} {proc['connections']:4} connections ({proc['established']} established)")
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
    "--bandwidth-threshold",
    type=float,
    default=DEFAULT_BANDWIDTH_THRESHOLD,
    help=f"Bandwidth usage threshold for warnings in MB/s (default: {DEFAULT_BANDWIDTH_THRESHOLD})"
)
@click.option(
    "--connection-threshold",
    type=int,
    default=DEFAULT_CONNECTION_THRESHOLD,
    help=f"Connection count threshold for warnings (default: {DEFAULT_CONNECTION_THRESHOLD})"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
def main(output_json: bool, bandwidth_threshold: float, connection_threshold: int, verbose: bool):
    """
    Analyze network performance, connections, and bandwidth utilization.

    Exit codes:
      0 - Network healthy (low risk)
      1 - Network under stress (medium risk)
      2 - Network critical (high risk)
      3 - Analysis error
    """
    try:
        # Create analyzer
        analyzer = NetworkAnalyzer(
            bandwidth_threshold=bandwidth_threshold,
            connection_threshold=connection_threshold,
            verbose=verbose
        )

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
