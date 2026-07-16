#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS Resource Optimizer - System Status Checker

Quick system health check across all resource categories.

Usage:
    uv run status.py                    # Human-readable output
    uv run status.py --json             # JSON output
    uv run status.py --verbose          # Detailed output

Exit Codes:
    0 - Healthy (all systems normal)
    1 - Warning (some resources elevated)
    2 - Critical (resources at dangerous levels)
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
class SystemStatus:
    """System health status across all categories."""
    timestamp: float
    status: str  # "healthy", "warning", "critical"
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: Optional[int]
    battery_charging: Optional[bool]
    network_active: bool
    temperature: Optional[float]
    warnings: list[str]
    critical_issues: list[str]


class StatusChecker:
    """Quick system health checker."""

    # Thresholds for status determination
    CPU_WARNING = 70.0
    CPU_CRITICAL = 85.0
    MEMORY_WARNING = 75.0
    MEMORY_CRITICAL = 85.0
    DISK_WARNING = 80.0
    DISK_CRITICAL = 90.0
    BATTERY_WARNING = 20
    TEMP_WARNING = 75.0
    TEMP_CRITICAL = 85.0

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.warnings = []
        self.critical_issues = []

    def check_cpu(self) -> float:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=1)

        if cpu_percent >= self.CPU_CRITICAL:
            self.critical_issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
        elif cpu_percent >= self.CPU_WARNING:
            self.warnings.append(f"CPU usage elevated: {cpu_percent:.1f}%")

        return cpu_percent

    def check_memory(self) -> float:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        if memory_percent >= self.MEMORY_CRITICAL:
            self.critical_issues.append(f"Memory usage critical: {memory_percent:.1f}%")
        elif memory_percent >= self.MEMORY_WARNING:
            self.warnings.append(f"Memory usage elevated: {memory_percent:.1f}%")

        return memory_percent

    def check_disk(self) -> float:
        """Check disk usage."""
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        if disk_percent >= self.DISK_CRITICAL:
            self.critical_issues.append(f"Disk usage critical: {disk_percent:.1f}%")
        elif disk_percent >= self.DISK_WARNING:
            self.warnings.append(f"Disk usage elevated: {disk_percent:.1f}%")

        return disk_percent

    def check_battery(self) -> tuple[Optional[int], Optional[bool]]:
        """Check battery status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return None, None

            percent = battery.percent
            charging = battery.power_plugged

            if not charging and percent <= self.BATTERY_WARNING:
                self.warnings.append(f"Battery low: {percent}%")

            return int(percent), charging
        except Exception:
            return None, None

    def check_network(self) -> bool:
        """Check network activity."""
        try:
            net_io = psutil.net_io_counters()
            # Network is considered active if any bytes sent/received
            return net_io.bytes_sent > 0 or net_io.bytes_recv > 0
        except Exception:
            return False

    def check_temperature(self) -> Optional[float]:
        """Check system temperature if available."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Get average temperature across all sensors
            all_temps = []
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current:
                        all_temps.append(entry.current)

            if not all_temps:
                return None

            avg_temp = sum(all_temps) / len(all_temps)

            if avg_temp >= self.TEMP_CRITICAL:
                self.critical_issues.append(f"Temperature critical: {avg_temp:.1f}°C")
            elif avg_temp >= self.TEMP_WARNING:
                self.warnings.append(f"Temperature elevated: {avg_temp:.1f}°C")

            return avg_temp
        except Exception:
            return None

    def determine_status(self) -> str:
        """Determine overall system status."""
        if self.critical_issues:
            return "critical"
        elif self.warnings:
            return "warning"
        else:
            return "healthy"

    def check_system(self) -> SystemStatus:
        """Perform complete system health check."""
        cpu_percent = self.check_cpu()
        memory_percent = self.check_memory()
        disk_percent = self.check_disk()
        battery_percent, battery_charging = self.check_battery()
        network_active = self.check_network()
        temperature = self.check_temperature()

        status = self.determine_status()

        return SystemStatus(
            timestamp=datetime.now().timestamp(),
            status=status,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            battery_percent=battery_percent,
            battery_charging=battery_charging,
            network_active=network_active,
            temperature=temperature,
            warnings=self.warnings,
            critical_issues=self.critical_issues
        )


def format_human_readable(status: SystemStatus) -> str:
    """Format status as human-readable output."""
    lines = []

    # Status header
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🔴"
    }

    lines.append(f"\n{status_emoji[status.status]} System Status: {status.status.upper()}")
    lines.append(f"Timestamp: {datetime.fromtimestamp(status.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Resource metrics
    lines.append("Resource Usage:")
    lines.append(f"  CPU: {status.cpu_percent:.1f}%")
    lines.append(f"  Memory: {status.memory_percent:.1f}%")
    lines.append(f"  Disk: {status.disk_percent:.1f}%")

    if status.battery_percent is not None:
        charging_status = "charging" if status.battery_charging else "discharging"
        lines.append(f"  Battery: {status.battery_percent}% ({charging_status})")

    if status.temperature is not None:
        lines.append(f"  Temperature: {status.temperature:.1f}°C")

    lines.append(f"  Network: {'Active' if status.network_active else 'Inactive'}")
    lines.append("")

    # Critical issues
    if status.critical_issues:
        lines.append("🔴 Critical Issues:")
        for issue in status.critical_issues:
            lines.append(f"  - {issue}")
        lines.append("")

    # Warnings
    if status.warnings:
        lines.append("⚠️  Warnings:")
        for warning in status.warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    return "\n".join(lines)


@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(output_json: bool, verbose: bool):
    """
    Quick system health check.

    Checks CPU, memory, disk, battery, network, and temperature status.
    Reports overall system health with warnings and critical issues.
    """
    try:
        checker = StatusChecker(verbose=verbose)
        status = checker.check_system()

        if output_json:
            # JSON output
            output = asdict(status)
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            output = format_human_readable(status)
            print(output)

        # Exit code based on status
        exit_codes = {
            "healthy": 0,
            "warning": 1,
            "critical": 2
        }
        sys.exit(exit_codes[status.status])

    except Exception as e:
        error_output = {
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
