#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Agent Result Formatter - TOON format output for all optimization agents.

This module provides standardized TOON formatting for agent analysis results,
achieving 60-75% token reduction compared to JSON.

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add utils to path for toon_codec import
sys.path.insert(0, str(Path(__file__).parent))
from toon_codec import encode_toon


def format_analysis_result(
    category: str,
    metrics: Dict[str, Any],
    status: str = "healthy",
    issues: List[Dict] = None,
    recommendations: List[Dict] = None,
    timestamp: float = None
) -> str:
    """
    Format analysis result in TOON format.

    Args:
        category: Analysis category (cpu, memory, disk, network, battery, thermal)
        metrics: Dict of metric key-value pairs
        status: Status (healthy, warning, critical)
        issues: List of detected issues (optional)
        recommendations: List of optimization recommendations (optional)
        timestamp: Unix timestamp (optional, defaults to current time)

    Returns:
        TOON-formatted result string

    Example:
        >>> result = format_analysis_result(
        ...     category="cpu",
        ...     metrics={"usage": 45.2, "cores": 8},
        ...     status="healthy"
        ... )
        >>> print(result)
        cat:cpu
        m:usage|45.2,cores|8
        s:healthy
        t:1764505149.05
    """
    if timestamp is None:
        import time
        timestamp = time.time()

    # Build base result
    result_data = {
        "cat": category,
        "m": metrics,
        "s": status,
        "t": timestamp
    }

    # Add issues if present
    if issues:
        # Compact issues: i:type|severity|value|desc
        issue_lines = []
        for issue in issues:
            issue_compact = f"{issue.get('type', '')}|{issue.get('severity', '')}|{issue.get('value', '')}|{issue.get('description', '')}"
            issue_lines.append(issue_compact)
        result_data["i"] = issue_lines

    # Add recommendations if present
    if recommendations:
        # Compact recommendations: r:action|target|reason|priority
        rec_lines = []
        for rec in recommendations:
            rec_compact = f"{rec.get('action', '')}|{rec.get('target', '')}|{rec.get('reason', '')}|{rec.get('priority_score', 0)}"
            rec_lines.append(rec_compact)
        result_data["r"] = rec_lines

    return encode_toon(result_data)


def format_cpu_result(
    usage_percent: float,
    user_percent: float,
    system_percent: float,
    cores: int,
    freq_mhz: int = None,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format CPU analysis result in TOON format."""
    metrics = {
        "u": usage_percent,
        "usr": user_percent,
        "sys": system_percent,
        "cores": cores
    }
    if freq_mhz:
        metrics["freq"] = freq_mhz

    # Determine status
    if usage_percent > 90:
        status = "critical"
    elif usage_percent > 75:
        status = "warning"
    else:
        status = "healthy"

    return format_analysis_result("cpu", metrics, status, issues, recommendations)


def format_memory_result(
    total_gb: float,
    used_gb: float,
    available_gb: float,
    percent: float,
    swap_used_gb: float = None,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format memory analysis result in TOON format."""
    metrics = {
        "total": total_gb,
        "used": used_gb,
        "avail": available_gb,
        "pct": percent
    }
    if swap_used_gb is not None:
        metrics["swap"] = swap_used_gb

    # Determine status
    if percent > 90:
        status = "critical"
    elif percent > 75:
        status = "warning"
    else:
        status = "healthy"

    return format_analysis_result("memory", metrics, status, issues, recommendations)


def format_disk_result(
    total_gb: float,
    used_gb: float,
    free_gb: float,
    percent: float,
    read_mbps: float = None,
    write_mbps: float = None,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format disk analysis result in TOON format."""
    metrics = {
        "total": total_gb,
        "used": used_gb,
        "free": free_gb,
        "pct": percent
    }
    if read_mbps is not None:
        metrics["rd"] = read_mbps
    if write_mbps is not None:
        metrics["wr"] = write_mbps

    # Determine status
    if percent > 90:
        status = "critical"
    elif percent > 80:
        status = "warning"
    else:
        status = "healthy"

    return format_analysis_result("disk", metrics, status, issues, recommendations)


def format_network_result(
    sent_mbps: float,
    recv_mbps: float,
    connections: int,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format network analysis result in TOON format."""
    metrics = {
        "tx": sent_mbps,
        "rx": recv_mbps,
        "conn": connections
    }

    # Determine status based on connection count
    if connections > 1000:
        status = "warning"
    else:
        status = "healthy"

    return format_analysis_result("network", metrics, status, issues, recommendations)


def format_battery_result(
    percent: float,
    hours_remaining: float = None,
    power_plugged: bool = False,
    health_percent: float = None,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format battery analysis result in TOON format."""
    metrics = {
        "pct": percent,
        "plugged": 1 if power_plugged else 0
    }
    if hours_remaining is not None:
        metrics["hrs"] = hours_remaining
    if health_percent is not None:
        metrics["health"] = health_percent

    # Determine status
    if not power_plugged:
        if percent < 10:
            status = "critical"
        elif percent < 20:
            status = "warning"
        else:
            status = "healthy"
    else:
        status = "healthy"

    return format_analysis_result("battery", metrics, status, issues, recommendations)


def format_thermal_result(
    cpu_temp: float,
    gpu_temp: float = None,
    fan_speed_rpm: int = None,
    issues: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """Format thermal analysis result in TOON format."""
    metrics = {
        "cpu_temp": cpu_temp
    }
    if gpu_temp is not None:
        metrics["gpu_temp"] = gpu_temp
    if fan_speed_rpm is not None:
        metrics["fan"] = fan_speed_rpm

    # Determine status
    if cpu_temp > 90:
        status = "critical"
    elif cpu_temp > 75:
        status = "warning"
    else:
        status = "healthy"

    return format_analysis_result("thermal", metrics, status, issues, recommendations)


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    import time

    print("🎨 Agent Result Formatter - TOON Format Examples")
    print("=" * 60)

    # Example 1: CPU Result
    print("\n📋 Example 1: CPU Analysis")
    cpu_result = format_cpu_result(
        usage_percent=45.2,
        user_percent=23.1,
        system_percent=22.1,
        cores=8,
        freq_mhz=2400
    )
    print(cpu_result)
    print(f"Tokens: ~{len(cpu_result) / 4:.1f}")

    # Example 2: Memory Result with Issues
    print("\n📋 Example 2: Memory Analysis (with issues)")
    memory_result = format_memory_result(
        total_gb=16.0,
        used_gb=14.2,
        available_gb=1.8,
        percent=88.8,
        swap_used_gb=2.5,
        issues=[
            {"type": "high_memory", "severity": "warning", "value": 88.8, "description": "Memory usage high"}
        ],
        recommendations=[
            {"action": "close_apps", "target": "Chrome", "reason": "High memory usage", "priority_score": 80}
        ]
    )
    print(memory_result)
    print(f"Tokens: ~{len(memory_result) / 4:.1f}")

    # Example 3: Disk Result
    print("\n📋 Example 3: Disk Analysis")
    disk_result = format_disk_result(
        total_gb=500.0,
        used_gb=450.0,
        free_gb=50.0,
        percent=90.0,
        read_mbps=125.5,
        write_mbps=87.2,
        issues=[
            {"type": "low_disk_space", "severity": "critical", "value": 90.0, "description": "Disk almost full"}
        ],
        recommendations=[
            {"action": "cleanup_cache", "target": "Developer caches", "reason": "Low disk space", "priority_score": 95}
        ]
    )
    print(disk_result)
    print(f"Tokens: ~{len(disk_result) / 4:.1f}")

    # Example 4: Network Result
    print("\n📋 Example 4: Network Analysis")
    network_result = format_network_result(
        sent_mbps=25.5,
        recv_mbps=125.3,
        connections=342
    )
    print(network_result)
    print(f"Tokens: ~{len(network_result) / 4:.1f}")

    # Example 5: Battery Result
    print("\n📋 Example 5: Battery Analysis")
    battery_result = format_battery_result(
        percent=35.0,
        hours_remaining=2.5,
        power_plugged=False,
        health_percent=92.0,
        issues=[
            {"type": "low_battery", "severity": "warning", "value": 35.0, "description": "Battery draining"}
        ],
        recommendations=[
            {"action": "enable_low_power_mode", "target": "System", "reason": "Battery low", "priority_score": 85}
        ]
    )
    print(battery_result)
    print(f"Tokens: ~{len(battery_result) / 4:.1f}")

    # Example 6: Thermal Result
    print("\n📋 Example 6: Thermal Analysis")
    thermal_result = format_thermal_result(
        cpu_temp=78.5,
        gpu_temp=72.3,
        fan_speed_rpm=4500
    )
    print(thermal_result)
    print(f"Tokens: ~{len(thermal_result) / 4:.1f}")

    print("\n✅ All examples generated successfully!")
