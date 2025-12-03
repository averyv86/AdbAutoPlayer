#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
macOS System Health Status

Quick system health check across all categories.
Provides summary metrics for CPU, memory, disk, network, battery, thermal.

Usage:
    uv run status.py
    uv run status.py --json
    uv run status.py --verbose

Exit codes:
    0 - Healthy
    1 - Warning (performance degradation)
    2 - Critical (immediate attention needed)
    3 - Error (script execution failed)
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import click
import psutil


# Configuration Constants
THRESHOLDS = {
    "cpu": {"warning": 70.0, "critical": 90.0},
    "memory": {"warning": 80.0, "critical": 95.0},
    "disk": {"warning": 85.0, "critical": 95.0},
    "battery": {"warning": 20.0, "critical": 10.0},
    "thermal": {"warning": 80.0, "critical": 95.0},
}


def collect_quick_metrics() -> Dict[str, Any]:
    """Collect quick metrics from all categories"""
    return {
        "cpu": _get_cpu_metrics(),
        "memory": _get_memory_metrics(),
        "disk": _get_disk_metrics(),
        "network": _get_network_metrics(),
        "battery": _get_battery_status(),
        "thermal": _get_thermal_status()
    }


def _get_cpu_metrics() -> Dict[str, Any]:
    """Get CPU usage metrics"""
    return {
        "usage": round(psutil.cpu_percent(interval=0.1), 1),
        "cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else None
    }


def _get_memory_metrics() -> Dict[str, Any]:
    """Get memory usage metrics"""
    mem = psutil.virtual_memory()
    return {
        "percent": round(mem.percent, 1),
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2)
    }


def _get_disk_metrics() -> Dict[str, Any]:
    """Get disk usage metrics"""
    disk = psutil.disk_usage('/')
    return {
        "percent": round(disk.percent, 1),
        "total_gb": round(disk.total / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2)
    }


def _get_network_metrics() -> Dict[str, Any]:
    """Get network I/O metrics"""
    net_io = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv
    }


def _get_battery_status() -> Dict[str, Any]:
    """Get battery status"""
    battery = psutil.sensors_battery()
    if battery:
        return {
            "available": True,
            "percent": round(battery.percent, 1),
            "plugged": battery.power_plugged,
            "time_left_mins": round(battery.secsleft / 60, 0) if battery.secsleft > 0 else None
        }
    return {"available": False}


def _get_thermal_status() -> Dict[str, Any]:
    """Get thermal status"""
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            all_temps = [t.current for sensor in temps.values() for t in sensor]
            if all_temps:
                avg_temp = round(sum(all_temps) / len(all_temps), 1)
                max_temp = round(max(all_temps), 1)
                return {
                    "available": True,
                    "avg_temp_celsius": avg_temp,
                    "max_temp_celsius": max_temp
                }
    except (AttributeError, OSError):
        pass
    return {"available": False}


def analyze_status(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze health status and generate warnings"""
    status = "healthy"
    warnings = []
    critical_issues = []

    # CPU Analysis
    cpu_usage = metrics["cpu"]["usage"]
    if cpu_usage >= THRESHOLDS["cpu"]["critical"]:
        critical_issues.append(f"CRITICAL: CPU usage at {cpu_usage}%")
        status = "critical"
    elif cpu_usage >= THRESHOLDS["cpu"]["warning"]:
        warnings.append(f"High CPU usage: {cpu_usage}%")
        if status == "healthy":
            status = "warning"

    # Memory Analysis
    mem_percent = metrics["memory"]["percent"]
    if mem_percent >= THRESHOLDS["memory"]["critical"]:
        critical_issues.append(f"CRITICAL: Memory usage at {mem_percent}%")
        status = "critical"
    elif mem_percent >= THRESHOLDS["memory"]["warning"]:
        warnings.append(f"High memory usage: {mem_percent}%")
        if status == "healthy":
            status = "warning"

    # Disk Analysis
    disk_percent = metrics["disk"]["percent"]
    if disk_percent >= THRESHOLDS["disk"]["critical"]:
        critical_issues.append(f"CRITICAL: Disk usage at {disk_percent}%")
        status = "critical"
    elif disk_percent >= THRESHOLDS["disk"]["warning"]:
        warnings.append(f"High disk usage: {disk_percent}%")
        if status == "healthy":
            status = "warning"

    # Battery Analysis
    battery = metrics["battery"]
    if battery.get("available") and not battery.get("plugged"):
        battery_percent = battery.get("percent", 100)
        if battery_percent <= THRESHOLDS["battery"]["critical"]:
            critical_issues.append(f"CRITICAL: Battery at {battery_percent}%")
            status = "critical"
        elif battery_percent <= THRESHOLDS["battery"]["warning"]:
            warnings.append(f"Low battery: {battery_percent}%")
            if status == "healthy":
                status = "warning"

    # Thermal Analysis
    thermal = metrics["thermal"]
    if thermal.get("available"):
        avg_temp = thermal.get("avg_temp_celsius", 0)
        if avg_temp >= THRESHOLDS["thermal"]["critical"]:
            critical_issues.append(f"CRITICAL: Temperature at {avg_temp}°C")
            status = "critical"
        elif avg_temp >= THRESHOLDS["thermal"]["warning"]:
            warnings.append(f"High temperature: {avg_temp}°C")
            if status == "healthy":
                status = "warning"

    return {
        "timestamp": datetime.now().isoformat(),
        "timestamp_unix": time.time(),
        "status": status,
        "metrics": metrics,
        "warnings": warnings,
        "critical_issues": critical_issues
    }


def format_human_readable(result: Dict[str, Any], verbose: bool = False) -> str:
    """Format results for human consumption"""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("macOS System Health Status")
    lines.append("=" * 60)
    lines.append(f"Timestamp: {result['timestamp']}")

    metrics = result["metrics"]

    # CPU Section
    lines.append(f"\n📊 CPU:")
    lines.append(f"  Usage: {metrics['cpu']['usage']}% ({metrics['cpu']['cores']} cores)")
    if verbose and metrics['cpu'].get('frequency_mhz'):
        lines.append(f"  Frequency: {metrics['cpu']['frequency_mhz']} MHz")

    # Memory Section
    lines.append(f"\n💾 Memory:")
    lines.append(f"  Usage: {metrics['memory']['percent']}% ({metrics['memory']['used_gb']} GB / {metrics['memory']['total_gb']} GB)")
    if verbose:
        lines.append(f"  Available: {metrics['memory']['available_gb']} GB")

    # Disk Section
    lines.append(f"\n💿 Disk:")
    lines.append(f"  Usage: {metrics['disk']['percent']}% ({metrics['disk']['used_gb']} GB / {metrics['disk']['total_gb']} GB)")
    if verbose:
        lines.append(f"  Free: {metrics['disk']['free_gb']} GB")

    # Network Section
    if verbose:
        lines.append(f"\n🌐 Network:")
        lines.append(f"  Sent: {metrics['network']['bytes_sent_mb']} MB")
        lines.append(f"  Received: {metrics['network']['bytes_recv_mb']} MB")

    # Battery Section
    if metrics['battery'].get('available'):
        lines.append(f"\n🔋 Battery:")
        battery_status = "Charging" if metrics['battery']['plugged'] else "Discharging"
        lines.append(f"  Level: {metrics['battery']['percent']}% ({battery_status})")
        if verbose and metrics['battery'].get('time_left_mins'):
            lines.append(f"  Time remaining: {metrics['battery']['time_left_mins']} minutes")

    # Thermal Section
    if metrics['thermal'].get('available'):
        lines.append(f"\n🌡️  Thermal:")
        lines.append(f"  Average: {metrics['thermal']['avg_temp_celsius']}°C")
        if verbose:
            lines.append(f"  Maximum: {metrics['thermal']['max_temp_celsius']}°C")

    # Overall Status
    lines.append(f"\n📈 Overall Status: {result['status'].upper()}")

    # Critical Issues
    if result['critical_issues']:
        lines.append(f"\n🚨 CRITICAL ISSUES:")
        for issue in result['critical_issues']:
            lines.append(f"  - {issue}")

    # Warnings
    if result['warnings']:
        lines.append(f"\n⚠️  Warnings:")
        for warning in result['warnings']:
            lines.append(f"  - {warning}")

    # All Good
    if not result['warnings'] and not result['critical_issues']:
        lines.append("\n✅ System running optimally")

    lines.append("\n" + "=" * 60 + "\n")
    return "\n".join(lines)


@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Include detailed metrics')
def main(output_json: bool, verbose: bool):
    """
    Check macOS system health status

    Performs a quick health check across CPU, memory, disk,
    network, battery, and thermal metrics.
    """
    try:
        # Collect metrics
        metrics = collect_quick_metrics()

        # Analyze status
        result = analyze_status(metrics)

        # Output results
        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(format_human_readable(result, verbose))

        # Exit code based on status
        exit_code = {
            "healthy": 0,
            "warning": 1,
            "critical": 2
        }.get(result["status"], 3)

        sys.exit(exit_code)

    except Exception as e:
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
        if output_json:
            click.echo(json.dumps(error_data, indent=2), err=True)
        else:
            click.echo(f"❌ Error: {e}", err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
