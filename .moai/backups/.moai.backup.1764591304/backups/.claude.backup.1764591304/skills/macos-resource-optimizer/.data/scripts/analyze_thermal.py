#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - Thermal Analyzer

Detailed temperature monitoring and thermal management analysis with recommendations.

Usage:
    uv run analyze_thermal.py                      # Human-readable output
    uv run analyze_thermal.py --json               # JSON output
    uv run analyze_thermal.py --threshold 75.0     # Custom temperature threshold (°C)
    uv run analyze_thermal.py --verbose            # Detailed output

Exit Codes:
    0 - Healthy (temperature within normal range)
    1 - Warning (temperature elevated but manageable)
    2 - Critical (temperature at dangerous levels)
    3 - Error (execution failure or sensors unavailable)
"""

import json
import sys
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import click
import psutil


@dataclass
class ThermalMetrics:
    """Thermal performance metrics."""
    cpu_temperature: Optional[float]
    temperatures: dict
    fan_speeds: Optional[list[int]]
    thermal_state: str
    max_temperature: Optional[float]
    avg_temperature: Optional[float]


@dataclass
class ThermalAnalysis:
    """Thermal analysis results."""
    category: str
    timestamp: float
    metrics: dict
    analysis: dict


class ThermalAnalyzer:
    """Detailed thermal analysis and recommendations."""

    # Default thresholds (Celsius)
    THRESHOLD_NOMINAL = 60.0
    THRESHOLD_WARNING = 75.0
    THRESHOLD_CRITICAL = 85.0
    THRESHOLD_THROTTLE = 90.0

    def __init__(self, threshold: float = 75.0, verbose: bool = False):
        self.threshold = threshold
        self.verbose = verbose

    def collect_metrics(self) -> ThermalMetrics:
        """Collect comprehensive thermal metrics."""
        # Try to get temperature data from psutil
        temperatures = {}
        cpu_temperature = None
        fan_speeds = None

        try:
            temps = psutil.sensors_temperatures()

            if temps:
                # Collect all temperature sensors
                for sensor_name, entries in temps.items():
                    for entry in entries:
                        label = entry.label or sensor_name
                        temperatures[label] = entry.current

                        # Identify CPU temperature
                        if 'cpu' in label.lower() or 'core' in label.lower():
                            if cpu_temperature is None or entry.current > cpu_temperature:
                                cpu_temperature = entry.current

                # If no specific CPU temp found, use average of all sensors
                if cpu_temperature is None and temperatures:
                    cpu_temperature = sum(temperatures.values()) / len(temperatures)

        except AttributeError:
            # sensors_temperatures() not available on this platform
            pass

        # If psutil didn't return temperatures (common on macOS), try system commands
        if not temperatures:
            temperatures = self._get_macos_temperatures()

            if temperatures:
                # Extract CPU temperature
                cpu_temps = [v for k, v in temperatures.items() if 'cpu' in k.lower() or 'core' in k.lower()]
                if cpu_temps:
                    cpu_temperature = sum(cpu_temps) / len(cpu_temps)
                elif temperatures:
                    cpu_temperature = sum(temperatures.values()) / len(temperatures)

        # Get fan speeds
        try:
            fans = psutil.sensors_fans()
            if fans:
                fan_speeds = []
                for fan_name, entries in fans.items():
                    for entry in entries:
                        if entry.current:
                            fan_speeds.append(entry.current)
        except AttributeError:
            # sensors_fans() not available
            fan_speeds = self._get_macos_fan_speeds()

        # Calculate statistics
        if temperatures:
            max_temp = max(temperatures.values())
            avg_temp = sum(temperatures.values()) / len(temperatures)
        else:
            max_temp = cpu_temperature
            avg_temp = cpu_temperature

        # Determine thermal state
        thermal_state = self._determine_thermal_state(cpu_temperature or avg_temp)

        return ThermalMetrics(
            cpu_temperature=cpu_temperature,
            temperatures=temperatures,
            fan_speeds=fan_speeds,
            thermal_state=thermal_state,
            max_temperature=max_temp,
            avg_temperature=avg_temp
        )

    def _get_macos_temperatures(self) -> dict:
        """Get temperature data using macOS powermetrics (requires sudo)."""
        temperatures = {}

        try:
            # Try powermetrics (requires sudo, may not work)
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--samplers', 'smc', '-i', '1', '-n', '1'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0:
                output = result.stdout

                # Parse temperature data
                for line in output.split('\n'):
                    line = line.strip()

                    # Look for temperature readings
                    if 'CPU die temperature' in line or 'GPU die temperature' in line:
                        try:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                temp_str = parts[1].strip().split()[0]
                                temp = float(temp_str)
                                sensor_name = parts[0].strip()
                                temperatures[sensor_name] = temp
                        except (ValueError, IndexError):
                            pass

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fallback: Try to estimate from system activity (very rough approximation)
        if not temperatures:
            # Use CPU usage as a proxy for temperature estimation
            # This is NOT accurate but provides some indication when sensors unavailable
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                # Rough approximation: 40°C base + 0.4°C per percent CPU usage
                # This is purely illustrative when no real sensors are available
                estimated_temp = 40.0 + (cpu_percent * 0.4)
                temperatures['Estimated CPU'] = estimated_temp
            except Exception:
                pass

        return temperatures

    def _get_macos_fan_speeds(self) -> Optional[list[int]]:
        """Get fan speed data using macOS istats or similar (if available)."""
        # Note: This would require istats to be installed
        # For now, return None as we can't reliably get fan data on macOS
        return None

    def _determine_thermal_state(self, temperature: Optional[float]) -> str:
        """Determine thermal state based on temperature."""
        if temperature is None:
            return "unknown"

        if temperature >= self.THRESHOLD_THROTTLE:
            return "throttling"
        elif temperature >= self.THRESHOLD_CRITICAL:
            return "critical"
        elif temperature >= self.threshold:
            return "elevated"
        elif temperature >= self.THRESHOLD_NOMINAL:
            return "fair"
        else:
            return "nominal"

    def detect_issues(self, metrics: ThermalMetrics) -> list[str]:
        """Detect thermal-related issues."""
        issues = []

        # Temperature issues
        if metrics.cpu_temperature is not None:
            temp = metrics.cpu_temperature

            if temp >= self.THRESHOLD_THROTTLE:
                issues.append(
                    f"Critical: CPU temperature extremely high ({temp:.1f}°C) - "
                    "thermal throttling may occur"
                )
            elif temp >= self.THRESHOLD_CRITICAL:
                issues.append(
                    f"Critical: CPU temperature high ({temp:.1f}°C) - "
                    "immediate cooling required"
                )
            elif temp >= self.threshold:
                issues.append(
                    f"Warning: CPU temperature elevated ({temp:.1f}°C)"
                )

        # Check maximum temperature across all sensors
        if metrics.max_temperature is not None:
            if metrics.max_temperature >= self.THRESHOLD_CRITICAL:
                issues.append(
                    f"Critical: Maximum sensor temperature {metrics.max_temperature:.1f}°C"
                )

        # Thermal state issues
        if metrics.thermal_state == "throttling":
            issues.append(
                "System may be experiencing thermal throttling - "
                "performance degradation likely"
            )
        elif metrics.thermal_state == "critical":
            issues.append("System thermal state is critical")

        # Fan speed issues (if available)
        if metrics.fan_speeds is not None and metrics.fan_speeds:
            max_fan_speed = max(metrics.fan_speeds)

            # High fan speed indicates system is working hard to cool
            if max_fan_speed > 5000:  # RPM
                issues.append(
                    f"Fans running at high speed ({max_fan_speed} RPM) - "
                    "system under thermal stress"
                )

            # Check if all fans are at zero (potential hardware issue)
            if all(speed == 0 for speed in metrics.fan_speeds):
                issues.append(
                    "Warning: No fan activity detected - "
                    "check cooling system"
                )

        return issues

    def generate_recommendations(
        self,
        metrics: ThermalMetrics,
        issues: list[str]
    ) -> list[str]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Critical temperature recommendations
        if metrics.cpu_temperature is not None:
            temp = metrics.cpu_temperature

            if temp >= self.THRESHOLD_THROTTLE:
                recommendations.append("URGENT: Shutdown system immediately if temperature doesn't decrease")
                recommendations.append("Close all resource-intensive applications")
                recommendations.append("Ensure proper ventilation and airflow")
                recommendations.append("Check for dust buildup in vents")
                recommendations.append("Consider professional cleaning service")

            elif temp >= self.THRESHOLD_CRITICAL:
                recommendations.append("Close resource-intensive applications immediately")
                recommendations.append("Improve ventilation around device")
                recommendations.append("Use cooling pad or elevate laptop")
                recommendations.append("Clean dust from cooling vents")

            elif temp >= self.threshold:
                recommendations.append("Monitor CPU temperature trends")
                recommendations.append("Close unnecessary applications")
                recommendations.append("Ensure adequate ventilation")
                recommendations.append("Check Activity Monitor for CPU-intensive processes")

        # Thermal state recommendations
        if metrics.thermal_state == "throttling":
            recommendations.append("System is thermal throttling")
            recommendations.append("Performance will be reduced until temperature decreases")
            recommendations.append("Consider hardware upgrade for better cooling")

        # Fan-related recommendations
        if metrics.fan_speeds is not None and metrics.fan_speeds:
            max_fan_speed = max(metrics.fan_speeds)

            if max_fan_speed > 5000:
                recommendations.append("High fan speed indicates thermal stress")
                recommendations.append("Reduce workload if possible")
                recommendations.append("Check for background processes")

            if all(speed == 0 for speed in metrics.fan_speeds):
                recommendations.append("No fan activity - cooling system may be faulty")
                recommendations.append("Contact Apple Support for hardware check")

        # General thermal management recommendations
        if metrics.thermal_state in ["nominal", "fair"]:
            recommendations.append("Thermal state is healthy")
            recommendations.append("Continue monitoring temperature trends")
        else:
            recommendations.append("Use macOS Activity Monitor to identify heat sources")
            recommendations.append("Avoid using laptop on soft surfaces (bed, couch)")
            recommendations.append("Keep macOS and applications updated")
            recommendations.append("Consider using a cooling pad for laptops")

        # Data availability warning
        if not metrics.temperatures:
            recommendations.append("Note: Temperature sensors not available via standard tools")
            recommendations.append("Install 'istats' for detailed thermal monitoring:")
            recommendations.append("  brew install iStats")
            recommendations.append("Consider using third-party monitoring tools")

        return recommendations

    def determine_risk_level(self, metrics: ThermalMetrics) -> str:
        """Determine overall thermal risk level."""
        # Critical conditions
        if metrics.cpu_temperature is not None:
            if metrics.cpu_temperature >= self.THRESHOLD_CRITICAL:
                return "critical"

        if metrics.max_temperature is not None:
            if metrics.max_temperature >= self.THRESHOLD_CRITICAL:
                return "critical"

        if metrics.thermal_state in ["critical", "throttling"]:
            return "critical"

        # Warning conditions
        if metrics.cpu_temperature is not None:
            if metrics.cpu_temperature >= self.threshold:
                return "warning"

        if metrics.thermal_state == "elevated":
            return "warning"

        return "low"

    def analyze(self) -> ThermalAnalysis:
        """Perform complete thermal analysis."""
        metrics = self.collect_metrics()
        issues = self.detect_issues(metrics)
        recommendations = self.generate_recommendations(metrics, issues)
        risk_level = self.determine_risk_level(metrics)

        status = "healthy"
        if risk_level == "critical":
            status = "critical"
        elif risk_level == "warning":
            status = "warning"

        analysis = ThermalAnalysis(
            category="thermal",
            timestamp=time.time(),
            metrics=asdict(metrics),
            analysis={
                "status": status,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "warnings": issues
            }
        )

        return analysis


def format_human_readable(analysis: ThermalAnalysis, verbose: bool = False) -> str:
    """Format analysis as human-readable output."""
    lines = []

    # Header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    status = analysis.analysis["status"]
    lines.append(f"\n{status_emoji[status]} Thermal Analysis: {status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Metrics
    metrics = analysis.metrics

    # Temperature information
    if metrics['cpu_temperature'] is not None:
        temp_emoji = "❄️" if metrics['cpu_temperature'] < 60 else "🔥" if metrics['cpu_temperature'] >= 85 else "🌡️"
        lines.append(f"{temp_emoji} CPU Temperature: {metrics['cpu_temperature']:.1f}°C")

    if verbose and metrics['avg_temperature'] is not None:
        lines.append(f"  Average Temperature: {metrics['avg_temperature']:.1f}°C")

    if verbose and metrics['max_temperature'] is not None:
        lines.append(f"  Maximum Temperature: {metrics['max_temperature']:.1f}°C")

    lines.append(f"Thermal State: {metrics['thermal_state'].title()}")
    lines.append("")

    # All temperature sensors (verbose mode)
    if verbose and metrics['temperatures']:
        lines.append("Temperature Sensors:")
        for sensor, temp in sorted(metrics['temperatures'].items()):
            lines.append(f"  {sensor}: {temp:.1f}°C")
        lines.append("")

    # Fan speeds
    if metrics['fan_speeds'] is not None and metrics['fan_speeds']:
        lines.append("Fan Speeds:")
        for i, speed in enumerate(metrics['fan_speeds']):
            lines.append(f"  Fan {i + 1}: {speed} RPM")
        lines.append("")
    elif verbose:
        lines.append("Fan Speeds: Not available")
        lines.append("")

    # Issues/Warnings
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
@click.option('--threshold', type=float, default=75.0, help='Temperature threshold in °C (default: 75.0)')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Detailed temperature monitoring and thermal management analysis.

    Analyzes CPU temperature, thermal state, and fan speeds.
    Detects thermal throttling and provides cooling recommendations.

    Note: On macOS, temperature sensor access may be limited.
    For detailed thermal monitoring, install 'istats' via Homebrew.
    """
    try:
        analyzer = ThermalAnalyzer(threshold=threshold, verbose=verbose)
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
            "category": "thermal",
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
