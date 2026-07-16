#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "psutil>=5.9.0",
#   "click>=8.1.0",
# ]
# ///
"""
Thermal Analysis Script for macOS Resource Optimizer

Analyzes thermal management, cooling performance, and temperature sensors.
Exit codes: 0 (healthy), 1 (medium risk), 2 (high risk), 3 (error)
"""

import json
import sys
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import psutil
import click


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_TEMP_WARNING = 75.0    # Default temperature warning (°C)
DEFAULT_TEMP_CRITICAL = 85.0   # Default temperature critical (°C)
GPU_TEMP_WARNING = 80.0        # GPU temperature warning (°C)
GPU_TEMP_CRITICAL = 90.0       # GPU temperature critical (°C)
THERMAL_PRESSURE_LOW = 60.0    # Low thermal pressure threshold (°C)
THERMAL_PRESSURE_HIGH = 80.0   # High thermal pressure threshold (°C)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ThermalMetrics:
    """Complete thermal metrics data structure"""
    # Temperature metrics
    cpu_temp: Optional[float]          # CPU temperature (°C)
    gpu_temp: Optional[float]          # GPU temperature (°C)
    avg_temp: Optional[float]          # Average system temperature (°C)
    max_temp: Optional[float]          # Maximum sensor temperature (°C)

    # Fan metrics
    fan_speeds: List[int]              # Fan speeds (RPM)

    # Thermal pressure
    thermal_pressure: str              # "low", "medium", "high"

    # Sensor availability
    sensors_available: bool
    sensor_count: int
    sensor_details: Dict[str, float]   # All sensor readings

    # CPU load context
    cpu_usage: float                   # Current CPU usage (%)
    cpu_count: int                     # Number of CPU cores

    # Risk assessment
    risk_level: str                    # "low", "medium", "high"
    exit_code: int                     # 0, 1, 2

    # Recommendations
    recommendations: List[str]
    warnings: List[str]


# ============================================================================
# Thermal Analyzer
# ============================================================================

class ThermalAnalyzer:
    """Main thermal analysis engine"""

    def __init__(
        self,
        temp_warning: float = DEFAULT_TEMP_WARNING,
        temp_critical: float = DEFAULT_TEMP_CRITICAL,
        verbose: bool = False
    ):
        """
        Initialize thermal analyzer

        Args:
            temp_warning: Temperature warning threshold (°C)
            temp_critical: Temperature critical threshold (°C)
            verbose: Enable verbose output
        """
        self.temp_warning = temp_warning
        self.temp_critical = temp_critical
        self.verbose = verbose
        self._log(f"Initialized thermal analyzer (warning={temp_warning}°C, critical={temp_critical}°C)")

    def _log(self, message: str):
        """Print verbose log message"""
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)

    def collect_metrics(self) -> ThermalMetrics:
        """
        Collect all thermal metrics

        Returns:
            ThermalMetrics object with complete thermal state
        """
        self._log("Collecting thermal metrics...")

        # Collect temperature sensors
        cpu_temp, gpu_temp, avg_temp, max_temp, sensor_details = self._get_temperatures()

        # Collect fan speeds
        fan_speeds = self._get_fan_speeds()

        # Get CPU context
        cpu_usage = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()

        # Calculate thermal pressure
        thermal_pressure = self._calculate_thermal_pressure(avg_temp, max_temp, cpu_usage)

        # Determine sensor availability
        sensors_available = len(sensor_details) > 0
        sensor_count = len(sensor_details)

        # Assess risk level
        risk_level, exit_code = self._assess_risk(cpu_temp, gpu_temp, max_temp, thermal_pressure)

        # Generate recommendations
        recommendations, warnings = self._generate_recommendations(
            cpu_temp, gpu_temp, max_temp, fan_speeds, thermal_pressure, cpu_usage
        )

        return ThermalMetrics(
            cpu_temp=round(cpu_temp, 2) if cpu_temp else None,
            gpu_temp=round(gpu_temp, 2) if gpu_temp else None,
            avg_temp=round(avg_temp, 2) if avg_temp else None,
            max_temp=round(max_temp, 2) if max_temp else None,
            fan_speeds=fan_speeds,
            thermal_pressure=thermal_pressure,
            sensors_available=sensors_available,
            sensor_count=sensor_count,
            sensor_details=sensor_details,
            cpu_usage=round(cpu_usage, 2),
            cpu_count=cpu_count,
            risk_level=risk_level,
            exit_code=exit_code,
            recommendations=recommendations,
            warnings=warnings
        )

    def _get_temperatures(self) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Dict[str, float]]:
        """
        Get temperature readings from all available sensors

        Returns:
            (cpu_temp, gpu_temp, avg_temp, max_temp, sensor_dict)
        """
        sensor_details = {}
        cpu_temps = []
        gpu_temps = []

        # Try powermetrics (macOS, requires sudo)
        self._log("Attempting to read temperatures via powermetrics...")
        try:
            result = subprocess.run(
                ["sudo", "-n", "powermetrics", "--samplers", "smc", "-i1", "-n1"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'CPU die temperature' in line:
                        try:
                            temp_str = line.split(':')[1].strip().split()[0]
                            temp = float(temp_str)
                            sensor_details['cpu_die'] = temp
                            cpu_temps.append(temp)
                            self._log(f"  CPU die temperature: {temp}°C")
                        except (IndexError, ValueError):
                            pass
                    elif 'GPU die temperature' in line:
                        try:
                            temp_str = line.split(':')[1].strip().split()[0]
                            temp = float(temp_str)
                            sensor_details['gpu_die'] = temp
                            gpu_temps.append(temp)
                            self._log(f"  GPU die temperature: {temp}°C")
                        except (IndexError, ValueError):
                            pass

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError, FileNotFoundError):
            self._log("  powermetrics not available (requires sudo)")

        # Try psutil sensors (limited on macOS)
        self._log("Attempting to read temperatures via psutil...")
        try:
            sensors = psutil.sensors_temperatures()
            if sensors:
                for sensor_name, entries in sensors.items():
                    for entry in entries:
                        sensor_key = f"{sensor_name}_{entry.label}" if entry.label else sensor_name
                        sensor_details[sensor_key] = entry.current

                        # Categorize as CPU or GPU
                        if 'cpu' in sensor_name.lower() or 'core' in sensor_name.lower():
                            cpu_temps.append(entry.current)
                        elif 'gpu' in sensor_name.lower():
                            gpu_temps.append(entry.current)

                        self._log(f"  {sensor_key}: {entry.current}°C")

        except (AttributeError, RuntimeError):
            self._log("  psutil sensors not available on this platform")

        # Calculate aggregate temperatures
        cpu_temp = sum(cpu_temps) / len(cpu_temps) if cpu_temps else None
        gpu_temp = sum(gpu_temps) / len(gpu_temps) if gpu_temps else None

        all_temps = list(sensor_details.values())
        avg_temp = sum(all_temps) / len(all_temps) if all_temps else None
        max_temp = max(all_temps) if all_temps else None

        if not sensor_details:
            self._log("Temperature sensors: Not available (requires sudo on macOS)")
        else:
            self._log(f"Temperature summary: CPU={cpu_temp}°C, GPU={gpu_temp}°C, Avg={avg_temp}°C, Max={max_temp}°C")

        return cpu_temp, gpu_temp, avg_temp, max_temp, sensor_details

    def _get_fan_speeds(self) -> List[int]:
        """
        Get fan speeds from available sensors

        Returns:
            List of fan speeds in RPM
        """
        fan_speeds = []

        self._log("Attempting to read fan speeds...")

        # Try psutil fans (limited on macOS)
        try:
            fans = psutil.sensors_fans()
            if fans:
                for fan_name, entries in fans.items():
                    for entry in entries:
                        fan_speeds.append(entry.current)
                        self._log(f"  {fan_name}: {entry.current} RPM")

        except (AttributeError, RuntimeError):
            self._log("  Fan sensors not available on this platform")

        if not fan_speeds:
            self._log("Fan speeds: Not available (macOS limitation)")

        return fan_speeds

    def _calculate_thermal_pressure(
        self,
        avg_temp: Optional[float],
        max_temp: Optional[float],
        cpu_usage: float
    ) -> str:
        """
        Calculate thermal pressure indicator

        Args:
            avg_temp: Average system temperature (°C)
            max_temp: Maximum sensor temperature (°C)
            cpu_usage: Current CPU usage (%)

        Returns:
            "low", "medium", or "high"
        """
        if not max_temp and not avg_temp:
            # No temperature data, use CPU usage as proxy
            if cpu_usage >= 80:
                return "high"
            elif cpu_usage >= 50:
                return "medium"
            else:
                return "low"

        # Use max temperature if available, otherwise average
        reference_temp = max_temp if max_temp else avg_temp

        if reference_temp >= THERMAL_PRESSURE_HIGH:
            pressure = "high"
        elif reference_temp >= THERMAL_PRESSURE_LOW:
            pressure = "medium"
        else:
            pressure = "low"

        self._log(f"Thermal pressure: {pressure} (temp={reference_temp}°C, cpu={cpu_usage}%)")
        return pressure

    def _assess_risk(
        self,
        cpu_temp: Optional[float],
        gpu_temp: Optional[float],
        max_temp: Optional[float],
        thermal_pressure: str
    ) -> Tuple[str, int]:
        """
        Assess thermal risk level

        Args:
            cpu_temp: CPU temperature (°C)
            gpu_temp: GPU temperature (°C)
            max_temp: Maximum sensor temperature (°C)
            thermal_pressure: Thermal pressure indicator

        Returns:
            (risk_level, exit_code)
        """
        high_risk_conditions = []

        # Check CPU temperature
        if cpu_temp and cpu_temp >= self.temp_critical:
            high_risk_conditions.append(f"CPU temperature critical: {cpu_temp:.1f}°C")

        # Check GPU temperature
        if gpu_temp and gpu_temp >= GPU_TEMP_CRITICAL:
            high_risk_conditions.append(f"GPU temperature critical: {gpu_temp:.1f}°C")

        # Check maximum sensor temperature
        if max_temp and max_temp >= self.temp_critical:
            high_risk_conditions.append(f"Maximum temperature critical: {max_temp:.1f}°C")

        if high_risk_conditions:
            self._log(f"Risk assessment: HIGH ({', '.join(high_risk_conditions)})")
            return ("high", 2)

        # Medium risk conditions
        medium_risk_conditions = []

        if cpu_temp and cpu_temp >= self.temp_warning:
            medium_risk_conditions.append(f"CPU temperature elevated: {cpu_temp:.1f}°C")

        if gpu_temp and gpu_temp >= GPU_TEMP_WARNING:
            medium_risk_conditions.append(f"GPU temperature elevated: {gpu_temp:.1f}°C")

        if thermal_pressure == "high":
            medium_risk_conditions.append("High thermal pressure detected")

        if medium_risk_conditions:
            self._log(f"Risk assessment: MEDIUM ({', '.join(medium_risk_conditions)})")
            return ("medium", 1)

        # Low risk
        self._log("Risk assessment: LOW (thermal conditions healthy)")
        return ("low", 0)

    def _generate_recommendations(
        self,
        cpu_temp: Optional[float],
        gpu_temp: Optional[float],
        max_temp: Optional[float],
        fan_speeds: List[int],
        thermal_pressure: str,
        cpu_usage: float
    ) -> Tuple[List[str], List[str]]:
        """
        Generate actionable recommendations and warnings

        Returns:
            (recommendations, warnings)
        """
        recommendations = []
        warnings = []

        # CPU temperature warnings
        if cpu_temp:
            if cpu_temp >= self.temp_critical:
                warnings.append(f"CPU temperature critical at {cpu_temp:.1f}°C")
                recommendations.append("Reduce workload immediately to prevent thermal throttling")
                recommendations.append("Check for dust buildup in cooling system")
                recommendations.append("Verify adequate ventilation around device")
            elif cpu_temp >= self.temp_warning:
                warnings.append(f"CPU temperature elevated at {cpu_temp:.1f}°C")
                recommendations.append("Monitor workload and reduce if temperature continues rising")
                recommendations.append("Ensure proper airflow and cooling")

        # GPU temperature warnings
        if gpu_temp:
            if gpu_temp >= GPU_TEMP_CRITICAL:
                warnings.append(f"GPU temperature critical at {gpu_temp:.1f}°C")
                recommendations.append("Reduce graphics-intensive tasks immediately")
                recommendations.append("Check GPU cooling system")
            elif gpu_temp >= GPU_TEMP_WARNING:
                warnings.append(f"GPU temperature elevated at {gpu_temp:.1f}°C")
                recommendations.append("Monitor GPU-intensive applications")

        # Thermal throttling detection
        if max_temp and max_temp >= 95:
            warnings.append(f"Thermal throttling likely at {max_temp:.1f}°C")
            recommendations.append("System performance may be reduced to prevent damage")
            recommendations.append("Consider upgrading cooling solution")

        # High thermal pressure
        if thermal_pressure == "high":
            if not cpu_temp and not gpu_temp:
                warnings.append("High thermal pressure detected (sensors unavailable)")
                recommendations.append("High CPU usage may indicate thermal stress")

        # Fan speed analysis
        if fan_speeds:
            avg_fan = sum(fan_speeds) / len(fan_speeds)
            if avg_fan > 4000:  # High RPM
                recommendations.append(f"Fan running at high speed ({avg_fan:.0f} RPM)")
                recommendations.append("System is working hard to maintain cooling")
        else:
            if thermal_pressure == "high":
                recommendations.append("Fan speed monitoring unavailable")
                recommendations.append("Consider third-party monitoring tools for macOS")

        # No sensor data available
        if not cpu_temp and not gpu_temp and not max_temp:
            warnings.append("Temperature sensors not accessible")
            recommendations.append("Run with sudo for full thermal monitoring on macOS")
            recommendations.append("Use Activity Monitor to check for CPU-intensive processes")

        # Poor cooling indicators
        if cpu_temp and gpu_temp and abs(cpu_temp - gpu_temp) > 20:
            recommendations.append("Significant temperature variance between components")
            recommendations.append("Check for uneven cooling or thermal paste issues")

        self._log(f"Generated {len(recommendations)} recommendations, {len(warnings)} warnings")
        return recommendations, warnings

    def analyze(self) -> ThermalMetrics:
        """
        Perform complete thermal analysis

        Returns:
            ThermalMetrics with all analysis results
        """
        return self.collect_metrics()


# ============================================================================
# Output Formatting
# ============================================================================

def format_human_readable(metrics: ThermalMetrics) -> str:
    """
    Format metrics for human-readable output

    Args:
        metrics: ThermalMetrics to format

    Returns:
        Formatted string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("Thermal Analysis Report")
    lines.append("=" * 60)
    lines.append("")

    # Overall status
    risk_symbols = {"low": "✓", "medium": "⚠", "high": "✗"}
    risk_symbol = risk_symbols[metrics.risk_level]
    lines.append(f"Status: {risk_symbol} {metrics.risk_level.upper()} RISK")
    lines.append("")

    # Sensor availability
    if metrics.sensors_available:
        lines.append(f"Sensors:        {metrics.sensor_count} temperature sensors detected")
    else:
        lines.append("Sensors:        ⚠ No sensors available (requires sudo on macOS)")
    lines.append("")

    # Temperature summary
    lines.append("Temperature Summary:")
    if metrics.cpu_temp:
        lines.append(f"  CPU:          {metrics.cpu_temp}°C")
    else:
        lines.append("  CPU:          Not available")

    if metrics.gpu_temp:
        lines.append(f"  GPU:          {metrics.gpu_temp}°C")
    else:
        lines.append("  GPU:          Not available")

    if metrics.avg_temp:
        lines.append(f"  Average:      {metrics.avg_temp}°C")

    if metrics.max_temp:
        lines.append(f"  Maximum:      {metrics.max_temp}°C")

    lines.append("")

    # Detailed sensor readings
    if metrics.sensor_details:
        lines.append("Sensor Details:")
        for sensor, temp in sorted(metrics.sensor_details.items()):
            lines.append(f"  {sensor:<25} {temp}°C")
        lines.append("")

    # Fan speeds
    if metrics.fan_speeds:
        lines.append("Fan Speeds:")
        for i, rpm in enumerate(metrics.fan_speeds, 1):
            lines.append(f"  Fan {i}:       {rpm} RPM")
        avg_rpm = sum(metrics.fan_speeds) / len(metrics.fan_speeds)
        lines.append(f"  Average:      {avg_rpm:.0f} RPM")
        lines.append("")

    # Thermal pressure
    pressure_symbols = {"low": "✓", "medium": "⚠", "high": "✗"}
    pressure_symbol = pressure_symbols[metrics.thermal_pressure]
    lines.append(f"Thermal Pressure: {pressure_symbol} {metrics.thermal_pressure.upper()}")
    lines.append("")

    # CPU context
    lines.append(f"CPU Context:    {metrics.cpu_usage}% usage ({metrics.cpu_count} cores)")
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
    "--temp-warning",
    type=float,
    default=DEFAULT_TEMP_WARNING,
    help=f"Temperature warning threshold (default: {DEFAULT_TEMP_WARNING}°C)"
)
@click.option(
    "--temp-critical",
    type=float,
    default=DEFAULT_TEMP_CRITICAL,
    help=f"Temperature critical threshold (default: {DEFAULT_TEMP_CRITICAL}°C)"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
def main(output_json: bool, temp_warning: float, temp_critical: float, verbose: bool):
    """
    Analyze thermal management and cooling performance.

    Exit codes:
      0 - Thermal conditions healthy (low risk)
      1 - Thermal conditions elevated (medium risk)
      2 - Thermal conditions critical (high risk)
      3 - Analysis error
    """
    try:
        # Create analyzer
        analyzer = ThermalAnalyzer(
            temp_warning=temp_warning,
            temp_critical=temp_critical,
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
