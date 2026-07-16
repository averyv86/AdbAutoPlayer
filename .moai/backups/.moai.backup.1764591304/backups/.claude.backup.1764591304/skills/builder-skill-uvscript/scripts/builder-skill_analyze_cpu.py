#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "psutil>=5.9.0",
#   "click>=8.1.0",
# ]
# ///
"""
CPU Analysis Script for macOS Resource Optimizer

Analyzes CPU usage, core utilization, temperature, and provides actionable recommendations.
Exit codes: 0 (healthy), 1 (medium risk), 2 (high risk), 3 (error)
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import subprocess
import psutil
import click


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_THRESHOLD = 80.0  # Default CPU usage threshold (%)
TEMP_WARNING = 80.0       # Temperature warning threshold (°C)
TEMP_CRITICAL = 95.0      # Temperature critical threshold (°C)
SAMPLE_INTERVAL = 2.0     # CPU usage sampling interval (seconds)
SAMPLE_COUNT = 3          # Number of samples to average


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CPUMetrics:
    """Complete CPU metrics data structure"""
    # Overall metrics
    total_usage: float
    per_core_usage: List[float]
    core_count: int

    # Temperature metrics
    temperature: Optional[float]
    temp_sensors: Dict[str, float]

    # Frequency metrics
    current_freq: Optional[float]
    max_freq: Optional[float]
    min_freq: Optional[float]

    # Load metrics
    load_1min: float
    load_5min: float
    load_15min: float

    # Process metrics
    top_processes: List[Dict[str, any]]

    # Risk assessment
    risk_level: str  # "low", "medium", "high"
    exit_code: int   # 0, 1, 2

    # Recommendations
    recommendations: List[str]
    warnings: List[str]


# ============================================================================
# CPU Analyzer
# ============================================================================

class CPUAnalyzer:
    """Main CPU analysis engine"""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, verbose: bool = False):
        """
        Initialize CPU analyzer

        Args:
            threshold: CPU usage threshold for warnings (%)
            verbose: Enable verbose output
        """
        self.threshold = threshold
        self.verbose = verbose
        self._log(f"Initialized CPU analyzer (threshold={threshold}%)")

    def _log(self, message: str):
        """Print verbose log message"""
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)

    def collect_metrics(self) -> CPUMetrics:
        """
        Collect all CPU metrics

        Returns:
            CPUMetrics object with complete CPU state
        """
        self._log("Collecting CPU metrics...")

        # Collect CPU usage (average over interval)
        self._log(f"Sampling CPU usage ({SAMPLE_COUNT} samples, {SAMPLE_INTERVAL}s interval)...")
        cpu_usage_samples = []
        per_core_samples = []

        for i in range(SAMPLE_COUNT):
            if i > 0:
                time.sleep(SAMPLE_INTERVAL)

            total = psutil.cpu_percent(interval=0.1)
            per_core = psutil.cpu_percent(interval=0.1, percpu=True)

            cpu_usage_samples.append(total)
            per_core_samples.append(per_core)

            self._log(f"  Sample {i+1}: {total:.1f}% (cores: {[f'{c:.1f}' for c in per_core]})")

        # Average the samples
        total_usage = sum(cpu_usage_samples) / len(cpu_usage_samples)
        core_count = len(per_core_samples[0])
        per_core_usage = [
            sum(sample[i] for sample in per_core_samples) / len(per_core_samples)
            for i in range(core_count)
        ]

        self._log(f"Average CPU usage: {total_usage:.1f}%")

        # Collect temperature
        temperature, temp_sensors = self._get_temperature()

        # Collect frequency
        freq_info = self._get_cpu_frequency()

        # Collect load average
        load_avg = psutil.getloadavg()

        # Collect top processes
        top_processes = self._get_top_processes()

        # Analyze risk level
        risk_level, exit_code = self._assess_risk(
            total_usage, temperature, per_core_usage
        )

        # Generate recommendations
        recommendations, warnings = self._generate_recommendations(
            total_usage, temperature, per_core_usage, top_processes, load_avg
        )

        return CPUMetrics(
            total_usage=round(total_usage, 2),
            per_core_usage=[round(c, 2) for c in per_core_usage],
            core_count=core_count,
            temperature=round(temperature, 2) if temperature else None,
            temp_sensors=temp_sensors,
            current_freq=freq_info[0],
            max_freq=freq_info[1],
            min_freq=freq_info[2],
            load_1min=round(load_avg[0], 2),
            load_5min=round(load_avg[1], 2),
            load_15min=round(load_avg[2], 2),
            top_processes=top_processes,
            risk_level=risk_level,
            exit_code=exit_code,
            recommendations=recommendations,
            warnings=warnings
        )

    def _get_temperature(self) -> Tuple[Optional[float], Dict[str, float]]:
        """
        Get CPU temperature using macOS sensors

        Returns:
            (average_temp, sensor_dict)
        """
        try:
            # Try using powermetrics (requires sudo, may not work)
            result = subprocess.run(
                ["sudo", "-n", "powermetrics", "--samplers", "smc", "-i1", "-n1"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse powermetrics output
                temps = {}
                for line in result.stdout.split('\n'):
                    if 'CPU die temperature' in line:
                        temp_str = line.split(':')[1].strip().split()[0]
                        temps['cpu_die'] = float(temp_str)

                if temps:
                    avg_temp = sum(temps.values()) / len(temps)
                    self._log(f"Temperature: {avg_temp:.1f}°C (sensors: {temps})")
                    return avg_temp, temps

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError):
            pass

        # Fallback: Try psutil sensors (limited on macOS)
        try:
            sensors = psutil.sensors_temperatures()
            if sensors:
                temps = {}
                for name, entries in sensors.items():
                    for entry in entries:
                        temps[f"{name}_{entry.label}"] = entry.current

                if temps:
                    avg_temp = sum(temps.values()) / len(temps)
                    self._log(f"Temperature: {avg_temp:.1f}°C (sensors: {temps})")
                    return avg_temp, temps
        except AttributeError:
            pass

        self._log("Temperature: Not available (requires sudo)")
        return None, {}

    def _get_cpu_frequency(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Get CPU frequency information

        Returns:
            (current_freq, max_freq, min_freq) in MHz
        """
        try:
            freq = psutil.cpu_freq()
            if freq:
                self._log(f"Frequency: {freq.current:.0f} MHz (max: {freq.max:.0f}, min: {freq.min:.0f})")
                return (
                    round(freq.current, 2),
                    round(freq.max, 2),
                    round(freq.min, 2)
                )
        except AttributeError:
            pass

        # Fallback: Try sysctl on macOS
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.cpufrequency"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                freq_hz = int(result.stdout.strip())
                freq_mhz = freq_hz / 1_000_000
                self._log(f"Frequency: {freq_mhz:.0f} MHz")
                return (round(freq_mhz, 2), None, None)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass

        self._log("Frequency: Not available")
        return (None, None, None)

    def _get_top_processes(self, count: int = 5) -> List[Dict[str, any]]:
        """
        Get top CPU-consuming processes

        Args:
            count: Number of top processes to return

        Returns:
            List of process dicts sorted by CPU usage
        """
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                cpu_pct = pinfo['cpu_percent']
                mem_pct = pinfo['memory_percent']

                if cpu_pct is not None and cpu_pct > 0:
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': round(cpu_pct, 2),
                        'memory_percent': round(mem_pct, 2) if mem_pct is not None else 0.0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top = processes[:count]

        top_summary = ", ".join([f"{p['name']}({p['cpu_percent']}%)" for p in top])
        self._log(f"Top {count} processes: {top_summary}")
        return top

    def _assess_risk(
        self,
        total_usage: float,
        temperature: Optional[float],
        per_core_usage: List[float]
    ) -> Tuple[str, int]:
        """
        Assess CPU risk level

        Args:
            total_usage: Overall CPU usage (%)
            temperature: CPU temperature (°C)
            per_core_usage: Per-core CPU usage (%)

        Returns:
            (risk_level, exit_code)
        """
        # High risk conditions
        high_risk_conditions = []

        if total_usage >= 95:
            high_risk_conditions.append(f"CPU usage critical: {total_usage:.1f}%")

        if temperature and temperature >= TEMP_CRITICAL:
            high_risk_conditions.append(f"Temperature critical: {temperature:.1f}°C")

        max_core = max(per_core_usage) if per_core_usage else 0
        if max_core >= 98:
            high_risk_conditions.append(f"Core maxed out: {max_core:.1f}%")

        if high_risk_conditions:
            self._log(f"Risk assessment: HIGH ({', '.join(high_risk_conditions)})")
            return ("high", 2)

        # Medium risk conditions
        medium_risk_conditions = []

        if total_usage >= self.threshold:
            medium_risk_conditions.append(f"CPU usage high: {total_usage:.1f}%")

        if temperature and temperature >= TEMP_WARNING:
            medium_risk_conditions.append(f"Temperature high: {temperature:.1f}°C")

        if medium_risk_conditions:
            self._log(f"Risk assessment: MEDIUM ({', '.join(medium_risk_conditions)})")
            return ("medium", 1)

        # Low risk
        self._log("Risk assessment: LOW (all metrics healthy)")
        return ("low", 0)

    def _generate_recommendations(
        self,
        total_usage: float,
        temperature: Optional[float],
        per_core_usage: List[float],
        top_processes: List[Dict],
        load_avg: Tuple[float, float, float]
    ) -> Tuple[List[str], List[str]]:
        """
        Generate actionable recommendations and warnings

        Returns:
            (recommendations, warnings)
        """
        recommendations = []
        warnings = []

        # CPU usage recommendations
        if total_usage >= 95:
            warnings.append(f"CPU usage critical at {total_usage:.1f}%")
            recommendations.append("Immediately close unnecessary applications")
            recommendations.append("Consider system restart if usage persists")
        elif total_usage >= self.threshold:
            warnings.append(f"CPU usage high at {total_usage:.1f}%")
            recommendations.append("Review and close unnecessary applications")

        # Temperature recommendations
        if temperature:
            if temperature >= TEMP_CRITICAL:
                warnings.append(f"CPU temperature critical at {temperature:.1f}°C")
                recommendations.append("Reduce workload immediately to prevent thermal throttling")
                recommendations.append("Check for dust buildup in vents")
            elif temperature >= TEMP_WARNING:
                warnings.append(f"CPU temperature high at {temperature:.1f}°C")
                recommendations.append("Ensure proper ventilation and cooling")

        # Core imbalance
        if per_core_usage:
            max_core = max(per_core_usage)
            avg_core = sum(per_core_usage) / len(per_core_usage)

            if max_core >= 98:
                warnings.append(f"Core maxed out at {max_core:.1f}%")
                recommendations.append("Single-threaded bottleneck detected")
            elif max_core - avg_core > 40:
                recommendations.append("Unbalanced core usage detected")
                recommendations.append("Consider multi-threaded workload optimization")

        # Process-specific recommendations
        if top_processes and top_processes[0]['cpu_percent'] > 50:
            top_proc = top_processes[0]
            recommendations.append(
                f"Process '{top_proc['name']}' using {top_proc['cpu_percent']}% CPU"
            )

        # Load average recommendations
        if load_avg[0] > len(per_core_usage) * 2:
            warnings.append(f"System overloaded (load: {load_avg[0]:.2f})")
            recommendations.append("System load exceeds CPU capacity")

        self._log(f"Generated {len(recommendations)} recommendations, {len(warnings)} warnings")
        return recommendations, warnings

    def analyze(self) -> CPUMetrics:
        """
        Perform complete CPU analysis

        Returns:
            CPUMetrics with all analysis results
        """
        return self.collect_metrics()


# ============================================================================
# Output Formatting
# ============================================================================

def format_human_readable(metrics: CPUMetrics) -> str:
    """
    Format metrics for human-readable output

    Args:
        metrics: CPUMetrics to format

    Returns:
        Formatted string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("CPU Analysis Report")
    lines.append("=" * 60)
    lines.append("")

    # Overall status
    risk_symbols = {"low": "✓", "medium": "⚠", "high": "✗"}
    risk_colors = {"low": "green", "medium": "yellow", "high": "red"}

    risk_symbol = risk_symbols[metrics.risk_level]
    lines.append(f"Status: {risk_symbol} {metrics.risk_level.upper()} RISK")
    lines.append("")

    # CPU Usage
    lines.append("CPU Usage:")
    lines.append(f"  Total:        {metrics.total_usage}%")
    lines.append(f"  Cores:        {metrics.core_count}")

    # Per-core usage (group in rows of 4)
    core_lines = []
    for i, usage in enumerate(metrics.per_core_usage):
        if i > 0 and i % 4 == 0:
            lines.append(f"  Per-core:     {''.join(core_lines)}")
            core_lines = []
        core_lines.append(f"Core{i}: {usage:5.1f}%  ")

    if core_lines:  # Add remaining cores
        if len(metrics.per_core_usage) > 4:
            lines.append(f"                {''.join(core_lines)}")
        else:
            lines.append(f"  Per-core:     {''.join(core_lines)}")

    lines.append("")

    # Temperature
    if metrics.temperature:
        lines.append(f"Temperature:    {metrics.temperature}°C")
        if metrics.temp_sensors:
            for sensor, temp in metrics.temp_sensors.items():
                lines.append(f"  {sensor}: {temp}°C")
        lines.append("")

    # Frequency
    if metrics.current_freq:
        lines.append(f"Frequency:      {metrics.current_freq} MHz")
        if metrics.max_freq:
            lines.append(f"  Max:          {metrics.max_freq} MHz")
        if metrics.min_freq:
            lines.append(f"  Min:          {metrics.min_freq} MHz")
        lines.append("")

    # Load Average
    lines.append(f"Load Average:   {metrics.load_1min} (1m), {metrics.load_5min} (5m), {metrics.load_15min} (15m)")
    lines.append("")

    # Top Processes
    if metrics.top_processes:
        lines.append("Top CPU Processes:")
        for proc in metrics.top_processes:
            lines.append(f"  {proc['name']:<30} {proc['cpu_percent']:6.1f}% CPU, {proc['memory_percent']:6.1f}% RAM")
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
    help=f"CPU usage threshold for warnings (default: {DEFAULT_THRESHOLD}%)"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
def main(output_json: bool, threshold: float, verbose: bool):
    """
    Analyze CPU usage, temperature, and performance.

    Exit codes:
      0 - CPU healthy (low risk)
      1 - CPU under stress (medium risk)
      2 - CPU critical (high risk)
      3 - Analysis error
    """
    try:
        # Create analyzer
        analyzer = CPUAnalyzer(threshold=threshold, verbose=verbose)

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
