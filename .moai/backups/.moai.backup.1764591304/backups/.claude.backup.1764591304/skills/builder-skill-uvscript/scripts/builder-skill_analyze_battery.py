#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Battery Analyzer

Detailed battery health and power management analysis with recommendations.

Usage:
    uv run analyze_battery.py                      # Human-readable output
    uv run analyze_battery.py --json               # JSON output
    uv run analyze_battery.py --threshold 20.0     # Custom low battery threshold
    uv run analyze_battery.py --verbose            # Detailed output

Exit Codes:
    0 - Healthy (battery level above threshold or plugged in)
    1 - Warning (battery level low but manageable)
    2 - Critical (battery critically low)
    3 - Error (execution failure or no battery detected)
"""

import json
import sys
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import click
import psutil


@dataclass
class BatteryMetrics:
    """Battery performance metrics."""
    percent: float
    is_plugged: bool
    time_remaining_seconds: Optional[int]
    power_status: str
    cycle_count: Optional[int]
    max_capacity: Optional[int]
    design_capacity: Optional[int]
    health_percent: Optional[float]


@dataclass
class BatteryAnalysis:
    """Battery analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class BatteryAnalyzer:
    """Detailed battery analysis and recommendations."""

    # Default thresholds
    THRESHOLD_CRITICAL = 10.0
    THRESHOLD_WARNING = 20.0
    HEALTH_WARNING = 80.0
    HEALTH_CRITICAL = 60.0
    CYCLE_WARNING = 500
    CYCLE_CRITICAL = 1000

    def __init__(self, threshold: float = 20.0, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose

    def collect_metrics(self) -> BatteryMetrics:
        """Collect comprehensive battery metrics."""
        # Basic battery information from psutil
        battery = psutil.sensors_battery()

        if battery is None:
            raise RuntimeError("No battery detected - this may be a desktop system")

        percent = battery.percent
        is_plugged = battery.power_plugged

        # Calculate time remaining
        time_remaining_seconds = None
        if not is_plugged and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
            time_remaining_seconds = battery.secsleft if battery.secsleft > 0 else None

        # Determine power status
        if is_plugged:
            if percent >= 99:
                power_status = "full"
            else:
                power_status = "charging"
        else:
            power_status = "discharging"

        # Get extended battery information (macOS specific)
        extended_info = self._get_extended_battery_info()

        return BatteryMetrics(
            percent=percent,
            is_plugged=is_plugged,
            time_remaining_seconds=time_remaining_seconds,
            power_status=power_status,
            cycle_count=extended_info.get('cycle_count'),
            max_capacity=extended_info.get('max_capacity'),
            design_capacity=extended_info.get('design_capacity'),
            health_percent=extended_info.get('health_percent')
        )

    def _get_extended_battery_info(self) -> dict:
        """Get extended battery information using macOS system_profiler."""
        extended_info = {
            'cycle_count': None,
            'max_capacity': None,
            'design_capacity': None,
            'health_percent': None
        }

        try:
            # Use system_profiler to get detailed battery info
            result = subprocess.run(
                ['system_profiler', 'SPPowerDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout

                # Parse cycle count
                for line in output.split('\n'):
                    line = line.strip()

                    if 'Cycle Count:' in line:
                        try:
                            extended_info['cycle_count'] = int(line.split(':')[1].strip())
                        except (ValueError, IndexError):
                            pass

                    elif 'Maximum Capacity:' in line or 'Max Capacity:' in line:
                        try:
                            # Extract percentage value
                            capacity_str = line.split(':')[1].strip()
                            if '%' in capacity_str:
                                extended_info['max_capacity'] = int(capacity_str.replace('%', '').strip())
                        except (ValueError, IndexError):
                            pass

                    elif 'Condition:' in line or 'Health Information:' in line:
                        # Try to extract health condition
                        if 'Normal' in line or 'Good' in line:
                            extended_info['health_percent'] = 100.0
                        elif 'Fair' in line:
                            extended_info['health_percent'] = 75.0
                        elif 'Poor' in line or 'Replace' in line:
                            extended_info['health_percent'] = 50.0

                # Calculate health percentage from max capacity if available
                if extended_info['max_capacity'] is not None and extended_info['health_percent'] is None:
                    extended_info['health_percent'] = float(extended_info['max_capacity'])

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Fallback: Try ioreg command for cycle count
            try:
                result = subprocess.run(
                    ['ioreg', '-l', '-w0'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '"CycleCount"' in line:
                            try:
                                extended_info['cycle_count'] = int(line.split('=')[1].strip())
                                break
                            except (ValueError, IndexError):
                                pass

                        elif '"MaxCapacity"' in line:
                            try:
                                extended_info['max_capacity'] = int(line.split('=')[1].strip())
                            except (ValueError, IndexError):
                                pass

                        elif '"DesignCapacity"' in line:
                            try:
                                extended_info['design_capacity'] = int(line.split('=')[1].strip())
                            except (ValueError, IndexError):
                                pass

                    # Calculate health percentage
                    if (extended_info['max_capacity'] is not None and
                        extended_info['design_capacity'] is not None and
                        extended_info['design_capacity'] > 0):
                        health = (extended_info['max_capacity'] / extended_info['design_capacity']) * 100
                        extended_info['health_percent'] = health

            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pass

        return extended_info

    def detect_issues(self, metrics: BatteryMetrics) -> list[str]:
        """Detect battery-related issues."""
        issues = []

        # Battery level issues (only if not plugged in)
        if not metrics.is_plugged:
            if metrics.percent <= self.THRESHOLD_CRITICAL:
                issues.append(
                    f"Critical: Battery critically low ({metrics.percent:.1f}%) - "
                    "plug in immediately"
                )
            elif metrics.percent <= self.threshold:
                issues.append(
                    f"Warning: Battery low ({metrics.percent:.1f}%)"
                )

            # Time remaining warnings
            if metrics.time_remaining_seconds is not None:
                minutes_remaining = metrics.time_remaining_seconds / 60
                if minutes_remaining < 15:
                    issues.append(
                        f"Critical: Only {minutes_remaining:.0f} minutes remaining"
                    )
                elif minutes_remaining < 30:
                    issues.append(
                        f"Warning: {minutes_remaining:.0f} minutes remaining"
                    )

        # Health issues
        if metrics.health_percent is not None:
            if metrics.health_percent <= self.HEALTH_CRITICAL:
                issues.append(
                    f"Critical: Battery health poor ({metrics.health_percent:.1f}%) - "
                    "consider battery replacement"
                )
            elif metrics.health_percent <= self.HEALTH_WARNING:
                issues.append(
                    f"Warning: Battery health degraded ({metrics.health_percent:.1f}%)"
                )

        # Cycle count issues
        if metrics.cycle_count is not None:
            if metrics.cycle_count >= self.CYCLE_CRITICAL:
                issues.append(
                    f"Warning: High cycle count ({metrics.cycle_count}) - "
                    "battery may need replacement soon"
                )
            elif metrics.cycle_count >= self.CYCLE_WARNING:
                issues.append(
                    f"Battery cycle count: {metrics.cycle_count} (monitor health)"
                )

        return issues

    def generate_recommendations(
        self,
        metrics: BatteryMetrics,
        issues: list[str]
    ) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Critical battery level recommendations
        if not metrics.is_plugged:
            if metrics.percent <= self.THRESHOLD_CRITICAL:
                recommendations.append("URGENT: Plug in charger immediately")
                recommendations.append("Save all work and prepare for shutdown")
                recommendations.append("Close non-essential applications")
            elif metrics.percent <= self.threshold:
                recommendations.append("Connect to power source soon")
                recommendations.append("Enable Low Power Mode to extend battery life")
                recommendations.append("Close power-hungry applications")
                recommendations.append("Reduce screen brightness")

        # Time remaining recommendations
        if metrics.time_remaining_seconds is not None:
            minutes_remaining = metrics.time_remaining_seconds / 60
            if minutes_remaining < 30:
                recommendations.append("Limited battery time remaining")
                recommendations.append("Disable Bluetooth and WiFi if not needed")
                recommendations.append("Close background applications")

        # Health recommendations
        if metrics.health_percent is not None:
            if metrics.health_percent <= self.HEALTH_CRITICAL:
                recommendations.append("Battery health is critical")
                recommendations.append("Schedule battery replacement with Apple")
                recommendations.append("Keep device plugged in when possible")
            elif metrics.health_percent <= self.HEALTH_WARNING:
                recommendations.append("Monitor battery health trends")
                recommendations.append("Consider battery calibration")
                recommendations.append("Avoid deep discharge cycles")

        # Cycle count recommendations
        if metrics.cycle_count is not None:
            if metrics.cycle_count >= self.CYCLE_WARNING:
                recommendations.append("High battery cycle count detected")
                recommendations.append("Check battery health regularly")
                recommendations.append("Plan for eventual battery replacement")

                if metrics.cycle_count >= self.CYCLE_CRITICAL:
                    recommendations.append("Battery approaching end of life")
                    recommendations.append("Contact Apple Support for battery service")

        # Charging recommendations
        if metrics.is_plugged and metrics.percent < 100:
            recommendations.append("Battery is charging")
            if metrics.percent >= 80:
                recommendations.append("Consider unplugging at 80% for optimal battery longevity")

        # General optimization recommendations
        if not issues or (metrics.is_plugged and metrics.percent > self.threshold):
            if not metrics.is_plugged:
                recommendations.append("Battery level is adequate")
            recommendations.append("Enable Battery Health Management in System Settings")
            recommendations.append("Avoid extreme temperatures")
            recommendations.append("Use Optimized Battery Charging feature")

        return recommendations

    def determine_risk_level(self, metrics: BatteryMetrics) -> str:
        """Determine overall battery risk level."""
        # Critical conditions
        if not metrics.is_plugged:
            if metrics.percent <= self.THRESHOLD_CRITICAL:
                return "critical"

            if metrics.time_remaining_seconds is not None:
                minutes_remaining = metrics.time_remaining_seconds / 60
                if minutes_remaining < 15:
                    return "critical"

        if metrics.health_percent is not None and metrics.health_percent <= self.HEALTH_CRITICAL:
            return "critical"

        # Warning conditions
        if not metrics.is_plugged and metrics.percent <= self.threshold:
            return "warning"

        if metrics.health_percent is not None and metrics.health_percent <= self.HEALTH_WARNING:
            return "warning"

        if metrics.cycle_count is not None and metrics.cycle_count >= self.CYCLE_WARNING:
            return "warning"

        return "low"

    def analyze(self) -> BatteryAnalysis:
        """Perform complete battery analysis."""
        metrics = self.collect_metrics()
        issues = self.detect_issues(metrics)
        recommendations = self.generate_recommendations(metrics, issues)
        risk_level = self.determine_risk_level(metrics)

        status = "healthy"
        if risk_level == "critical":
            status = "critical"
        elif risk_level == "warning":
            status = "warning"

        analysis = BatteryAnalysis(
            category="battery",
            timestamp=datetime.now().timestamp(),
            metrics=asdict(metrics),
            analysis={
                "status": status,
                "risk_level": risk_level,
                "issues": issues,
                "recommendations": recommendations
            }
        )

        return analysis


def format_time(seconds: Optional[int]) -> str:
    """Format seconds as human-readable time."""
    if seconds is None:
        return "Unknown"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_human_readable(analysis: BatteryAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} Battery Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Metrics
    metrics = analysis.metrics

    lines.append("Battery Status:")
    lines.append(f"  Level: {metrics['percent']:.1f}%")
    lines.append(f"  Power: {metrics['power_status'].title()}")
    lines.append(f"  Plugged In: {'Yes' if metrics['is_plugged'] else 'No'}")

    if not metrics['is_plugged'] and metrics['time_remaining_seconds'] is not None:
        time_str = format_time(metrics['time_remaining_seconds'])
        lines.append(f"  Time Remaining: {time_str}")

    lines.append("")

    # Extended information
    if verbose or metrics['cycle_count'] is not None or metrics['health_percent'] is not None:
        lines.append("Battery Health:")

        if metrics['health_percent'] is not None:
            health_emoji = "✅" if metrics['health_percent'] >= 80 else "⚠️" if metrics['health_percent'] >= 60 else "🔴"
            lines.append(f"  {health_emoji} Health: {metrics['health_percent']:.1f}%")

        if metrics['cycle_count'] is not None:
            lines.append(f"  Cycle Count: {metrics['cycle_count']}")

        if verbose and metrics['max_capacity'] is not None:
            lines.append(f"  Max Capacity: {metrics['max_capacity']}%")

        if verbose and metrics['design_capacity'] is not None:
            lines.append(f"  Design Capacity: {metrics['design_capacity']} mAh")

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
@click.option('--threshold', type=float, default=20.0, help='Low battery threshold (default: 20.0)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed battery health and power management analysis with recommendations.

    Analyzes battery level, charging status, health, and cycle count.
    Provides specific recommendations for battery optimization and longevity.
    """
    try:
        analyzer = BatteryAnalyzer(threshold=threshold, verbose=verbose)
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
            "category": "battery",
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
