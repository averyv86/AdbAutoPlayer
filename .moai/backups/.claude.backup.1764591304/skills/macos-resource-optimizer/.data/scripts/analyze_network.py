#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Network Analyzer

Detailed network performance and connection analysis with recommendations.

Usage:
    uv run analyze_network.py                      # Human-readable output
    uv run analyze_network.py --json               # JSON output
    uv run analyze_network.py --threshold 0.5      # Custom error rate threshold (%)
    uv run analyze_network.py --verbose            # Detailed output

Exit Codes:
    0 - Healthy (no network issues)
    1 - Warning (minor network issues detected)
    2 - Critical (serious network problems)
    3 - Error (execution failure)
"""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from collections import Counter

import click
import psutil


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int
    connections_count: int
    connection_states: dict


@dataclass
class NetworkAnalysis:
    """Network analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class NetworkAnalyzer:
    """Detailed network analysis and recommendations."""

    # Default thresholds
    ERROR_RATE_WARNING = 0.1  # 0.1% error rate
    ERROR_RATE_CRITICAL = 0.5  # 0.5% error rate
    DROP_RATE_WARNING = 0.1
    DROP_RATE_CRITICAL = 0.5
    TIME_WAIT_WARNING = 50  # Number of TIME_WAIT connections
    TIME_WAIT_CRITICAL = 100
    CLOSE_WAIT_WARNING = 20  # Potential connection leak
    CLOSE_WAIT_CRITICAL = 50

    def __init__(self, threshold: float = 0.5, verbose: bool = False):
        self.threshold = threshold  # Error rate threshold in percentage
        self.verbose = verbose

    def collect_metrics(self) -> NetworkMetrics:
        """Collect comprehensive network metrics."""
        # Network I/O statistics
        net_io = psutil.net_io_counters()

        bytes_sent = net_io.bytes_sent
        bytes_received = net_io.bytes_recv
        packets_sent = net_io.packets_sent
        packets_received = net_io.packets_recv
        errors_in = net_io.errin
        errors_out = net_io.errout
        drops_in = net_io.dropin
        drops_out = net_io.dropout

        # Connection statistics (may require elevated privileges)
        connections = []
        connections_count = 0
        connection_states = {}

        try:
            connections = psutil.net_connections(kind='inet')
            connections_count = len(connections)
            # Count connection states
            connection_states = Counter(conn.status for conn in connections)
            connection_states = dict(connection_states)
        except (psutil.AccessDenied, PermissionError):
            # Cannot access connection information without sudo
            # Provide empty data but continue with other metrics
            pass

        return NetworkMetrics(
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            packets_sent=packets_sent,
            packets_received=packets_received,
            errors_in=errors_in,
            errors_out=errors_out,
            drops_in=drops_in,
            drops_out=drops_out,
            connections_count=connections_count,
            connection_states=dict(connection_states)
        )

    def calculate_error_rates(self, metrics: NetworkMetrics) -> dict:
        """Calculate error and drop rates as percentages."""
        total_packets = metrics.packets_sent + metrics.packets_received
        total_errors = metrics.errors_in + metrics.errors_out
        total_drops = metrics.drops_in + metrics.drops_out

        if total_packets == 0:
            return {
                "error_rate": 0.0,
                "drop_rate": 0.0,
                "error_rate_in": 0.0,
                "error_rate_out": 0.0,
                "drop_rate_in": 0.0,
                "drop_rate_out": 0.0
            }

        # Overall rates
        error_rate = (total_errors / total_packets) * 100
        drop_rate = (total_drops / total_packets) * 100

        # Directional rates
        error_rate_in = (metrics.errors_in / max(metrics.packets_received, 1)) * 100
        error_rate_out = (metrics.errors_out / max(metrics.packets_sent, 1)) * 100
        drop_rate_in = (metrics.drops_in / max(metrics.packets_received, 1)) * 100
        drop_rate_out = (metrics.drops_out / max(metrics.packets_sent, 1)) * 100

        return {
            "error_rate": error_rate,
            "drop_rate": drop_rate,
            "error_rate_in": error_rate_in,
            "error_rate_out": error_rate_out,
            "drop_rate_in": drop_rate_in,
            "drop_rate_out": drop_rate_out
        }

    def detect_issues(self, metrics: NetworkMetrics, error_rates: dict) -> list[str]:
        """Detect network-related issues."""
        issues = []

        # Error rate issues
        error_rate = error_rates["error_rate"]
        if error_rate >= self.ERROR_RATE_CRITICAL:
            issues.append(
                f"Critical: High network error rate ({error_rate:.3f}%) - "
                f"{metrics.errors_in + metrics.errors_out:,} errors detected"
            )
        elif error_rate >= self.threshold:
            issues.append(
                f"Warning: Elevated network error rate ({error_rate:.3f}%)"
            )

        # Packet drop issues
        drop_rate = error_rates["drop_rate"]
        if drop_rate >= self.DROP_RATE_CRITICAL:
            issues.append(
                f"Critical: High packet drop rate ({drop_rate:.3f}%) - "
                f"{metrics.drops_in + metrics.drops_out:,} packets dropped"
            )
        elif drop_rate >= self.DROP_RATE_WARNING:
            issues.append(
                f"Warning: Packets being dropped ({drop_rate:.3f}%)"
            )

        # Connection state issues
        time_wait_count = metrics.connection_states.get('TIME_WAIT', 0)
        if time_wait_count >= self.TIME_WAIT_CRITICAL:
            issues.append(
                f"Critical: Excessive TIME_WAIT connections ({time_wait_count}) - "
                "possible connection exhaustion"
            )
        elif time_wait_count >= self.TIME_WAIT_WARNING:
            issues.append(
                f"Warning: Many TIME_WAIT connections ({time_wait_count})"
            )

        # Connection leak detection
        close_wait_count = metrics.connection_states.get('CLOSE_WAIT', 0)
        if close_wait_count >= self.CLOSE_WAIT_CRITICAL:
            issues.append(
                f"Critical: Excessive CLOSE_WAIT connections ({close_wait_count}) - "
                "possible connection leak"
            )
        elif close_wait_count >= self.CLOSE_WAIT_WARNING:
            issues.append(
                f"Warning: Multiple CLOSE_WAIT connections ({close_wait_count}) - "
                "check for connection leaks"
            )

        # Directional error analysis
        if error_rates["error_rate_in"] > error_rates["error_rate_out"] * 2:
            issues.append(
                "Inbound errors significantly higher than outbound - "
                "check network/WiFi signal quality"
            )
        elif error_rates["error_rate_out"] > error_rates["error_rate_in"] * 2:
            issues.append(
                "Outbound errors significantly higher than inbound - "
                "check local network interface"
            )

        return issues

    def generate_recommendations(
        self,
        metrics: NetworkMetrics,
        error_rates: dict,
        issues: list[str]
    ) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Error rate recommendations
        if error_rates["error_rate"] >= self.ERROR_RATE_CRITICAL:
            recommendations.append("URGENT: Investigate network errors immediately")
            recommendations.append("Check network cable connections or WiFi signal strength")
            recommendations.append("Verify network interface settings")
            recommendations.append("Check for hardware issues with network adapter")
        elif error_rates["error_rate"] >= self.threshold:
            recommendations.append("Monitor network error trends")
            recommendations.append("Check WiFi signal strength and interference")
            recommendations.append("Consider switching to wired connection")

        # Packet drop recommendations
        if error_rates["drop_rate"] >= self.DROP_RATE_WARNING:
            recommendations.append("Investigate packet drops")
            recommendations.append("Check for network congestion")
            recommendations.append("Verify router/switch configuration")
            recommendations.append("Monitor bandwidth usage")

        # TIME_WAIT connection recommendations
        time_wait_count = metrics.connection_states.get('TIME_WAIT', 0)
        if time_wait_count >= self.TIME_WAIT_WARNING:
            recommendations.append("Review application connection pooling")
            recommendations.append("Consider adjusting TCP keepalive settings")
            recommendations.append("Monitor for rapid connection cycling")

            if time_wait_count >= self.TIME_WAIT_CRITICAL:
                recommendations.append("URGENT: Connection exhaustion risk")
                recommendations.append("Implement connection reuse in applications")
                recommendations.append("Check for connection leaks in code")

        # CLOSE_WAIT connection leak recommendations
        close_wait_count = metrics.connection_states.get('CLOSE_WAIT', 0)
        if close_wait_count >= self.CLOSE_WAIT_WARNING:
            recommendations.append("Possible connection leak detected")
            recommendations.append("Review application shutdown logic")
            recommendations.append("Ensure proper connection cleanup in error handlers")
            recommendations.append("Check for unclosed sockets in application code")

            if close_wait_count >= self.CLOSE_WAIT_CRITICAL:
                recommendations.append("URGENT: Fix connection leak immediately")
                recommendations.append("Restart affected applications")
                recommendations.append("Implement proper resource cleanup")

        # Directional error recommendations
        if error_rates["error_rate_in"] > error_rates["error_rate_out"] * 2:
            recommendations.append("Check WiFi/network signal quality")
            recommendations.append("Move closer to WiFi router or use wired connection")
            recommendations.append("Check for electromagnetic interference")
        elif error_rates["error_rate_out"] > error_rates["error_rate_in"] * 2:
            recommendations.append("Check local network adapter settings")
            recommendations.append("Update network driver software")
            recommendations.append("Verify network adapter hardware")

        # General optimization recommendations
        if not recommendations:
            recommendations.append("Network performance is healthy")
            recommendations.append("Continue monitoring connection patterns")
            recommendations.append("Maintain current network configuration")

        return recommendations

    def determine_risk_level(self, metrics: NetworkMetrics, error_rates: dict) -> str:
        """Determine overall network risk level."""
        # Critical conditions
        time_wait_count = metrics.connection_states.get('TIME_WAIT', 0)
        close_wait_count = metrics.connection_states.get('CLOSE_WAIT', 0)

        if (error_rates["error_rate"] >= self.ERROR_RATE_CRITICAL or
            error_rates["drop_rate"] >= self.DROP_RATE_CRITICAL or
            time_wait_count >= self.TIME_WAIT_CRITICAL or
            close_wait_count >= self.CLOSE_WAIT_CRITICAL):
            return "high"

        # Warning conditions
        if (error_rates["error_rate"] >= self.threshold or
            error_rates["drop_rate"] >= self.DROP_RATE_WARNING or
            time_wait_count >= self.TIME_WAIT_WARNING or
            close_wait_count >= self.CLOSE_WAIT_WARNING):
            return "medium"

        return "low"

    def analyze(self) -> NetworkAnalysis:
        """Perform complete network analysis."""
        metrics = self.collect_metrics()
        error_rates = self.calculate_error_rates(metrics)
        issues = self.detect_issues(metrics, error_rates)
        recommendations = self.generate_recommendations(metrics, error_rates, issues)
        risk_level = self.determine_risk_level(metrics, error_rates)

        status = "healthy"
        if risk_level == "high":
            status = "critical"
        elif risk_level == "medium":
            status = "warning"

        analysis = NetworkAnalysis(
            category="network",
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


def format_bytes(bytes_value: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_human_readable(analysis: NetworkAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} Network Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Metrics
    metrics = analysis.metrics

    lines.append("Network Traffic:")
    lines.append(f"  Sent: {format_bytes(metrics['bytes_sent'])} ({metrics['packets_sent']:,} packets)")
    lines.append(f"  Received: {format_bytes(metrics['bytes_received'])} ({metrics['packets_received']:,} packets)")
    lines.append("")

    # Error statistics
    error_rates = analysis.analysis["error_rates"]
    lines.append("Error Statistics:")
    lines.append(f"  Overall Error Rate: {error_rates['error_rate']:.4f}%")
    lines.append(f"  Errors In: {metrics['errors_in']:,} ({error_rates['error_rate_in']:.4f}%)")
    lines.append(f"  Errors Out: {metrics['errors_out']:,} ({error_rates['error_rate_out']:.4f}%)")
    lines.append("")

    lines.append("Packet Drops:")
    lines.append(f"  Overall Drop Rate: {error_rates['drop_rate']:.4f}%")
    lines.append(f"  Drops In: {metrics['drops_in']:,} ({error_rates['drop_rate_in']:.4f}%)")
    lines.append(f"  Drops Out: {metrics['drops_out']:,} ({error_rates['drop_rate_out']:.4f}%)")
    lines.append("")

    # Connection information
    lines.append(f"Active Connections: {metrics['connections_count']}")

    if metrics['connection_states']:
        lines.append("Connection States:")
        for state, count in sorted(metrics['connection_states'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {state}: {count}")

    lines.append("")

    # Warnings
    warnings = analysis.analysis["warnings"]
    if warnings:
        lines.append("🔍 Detected Warnings:")
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
@click.option('--threshold', type=float, default=0.5, help='Error rate threshold in % (default: 0.5)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed network performance and connection analysis with recommendations.

    Analyzes network traffic, error rates, packet drops, and connection states.
    Detects connection leaks and provides specific optimization recommendations.
    """
    try:
        analyzer = NetworkAnalyzer(threshold=threshold, verbose=verbose)
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
            "medium": 1,
            "high": 2
        }
        risk_level = analysis.analysis["risk_level"]
        sys.exit(exit_codes[risk_level])

    except Exception as e:
        error_output = {
            "category": "network",
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
