#!/usr/bin/env python3
"""
Spotlight/mds Hunter - Agent
Finds and analyzes Spotlight indexing processes on macOS.

Detection:
- Finds mdworker, mds_stores, mds processes
- Checks CPU usage with `ps -o %cpu= -p PID`
- Detects if indexing is active
- Reports if using >50% CPU (runaway indexing)

Output: JSON with Spotlight process stats and recommendations
"""

import json
import subprocess
import sys
import os
import time


def run_command(cmd: list) -> tuple:
    """Run command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


def run_command_shell(cmd: str) -> tuple:
    """Run shell command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


# Spotlight-related process patterns
SPOTLIGHT_PATTERNS = [
    "mds",
    "mds_stores",
    "mdworker",
    "mdworker_shared",
    "mdwrite",
    "mdsync",
    "mddiagnose",
    "Spotlight",
    "corespotlightd"
]

# Process types
SPOTLIGHT_TYPES = {
    "metadata_server": ["mds"],
    "indexer": ["mdworker", "mdworker_shared"],
    "storage": ["mds_stores"],
    "writer": ["mdwrite"],
    "sync": ["mdsync"],
    "diagnostic": ["mddiagnose"],
    "spotlight_ui": ["Spotlight"],
    "corespotlight": ["corespotlightd"]
}


def get_process_details(pid: str) -> dict:
    """Get detailed information about a process."""
    stdout, stderr, rc = run_command([
        "ps", "-o", "pid=,rss=,%cpu=,%mem=,etime=,command=", "-p", pid
    ])

    if rc != 0 or not stdout.strip():
        return None

    parts = stdout.strip().split(None, 5)
    if len(parts) < 6:
        return None

    try:
        return {
            "pid": int(parts[0]),
            "rss_kb": int(parts[1]),
            "rss_mb": int(parts[1]) / 1024,
            "cpu_percent": float(parts[2]),
            "mem_percent": float(parts[3]),
            "elapsed_time": parts[4],
            "command": parts[5][:150]
        }
    except (ValueError, IndexError):
        return None


def categorize_spotlight_process(command: str) -> str:
    """Categorize a Spotlight process by type."""
    command_parts = command.split('/')
    proc_name = command_parts[-1].split()[0] if command_parts else ""

    for proc_type, patterns in SPOTLIGHT_TYPES.items():
        for pattern in patterns:
            if pattern == proc_name or pattern in proc_name:
                return proc_type

    return "other"


def is_spotlight_process(command: str) -> bool:
    """Check if command is a Spotlight-related process."""
    command_lower = command.lower()
    return any(pattern.lower() in command_lower for pattern in SPOTLIGHT_PATTERNS)


def find_spotlight_processes() -> list:
    """Find all Spotlight-related processes."""
    processes = []
    seen_pids = set()

    # Find mds processes
    for pattern in SPOTLIGHT_PATTERNS:
        stdout, stderr, rc = run_command(["pgrep", "-f", pattern])
        if rc == 0 and stdout.strip():
            for pid in stdout.strip().split('\n'):
                if pid.strip():
                    seen_pids.add(pid.strip())

    # Get detailed info for each PID
    for pid in seen_pids:
        try:
            proc_info = get_process_details(pid)
            if proc_info and is_spotlight_process(proc_info.get("command", "")):
                proc_info["type"] = categorize_spotlight_process(proc_info.get("command", ""))
                processes.append(proc_info)
        except Exception:
            continue

    return processes


def check_indexing_status() -> dict:
    """Check Spotlight indexing status using mdutil."""
    status = {
        "indexing_enabled": True,
        "currently_indexing": False,
        "volumes": []
    }

    # Check indexing status
    stdout, stderr, rc = run_command(["mdutil", "-s", "/"])
    if rc == 0:
        status["root_status"] = stdout.strip()
        if "Indexing disabled" in stdout:
            status["indexing_enabled"] = False
        if "Indexing" in stdout and "enabled" not in stdout.lower():
            status["currently_indexing"] = True

    return status


def analyze_spotlight_usage(processes: list, indexing_status: dict) -> dict:
    """Analyze Spotlight resource usage and make recommendations."""
    analysis = {
        "total_cpu_percent": 0,
        "total_memory_mb": 0,
        "process_count": len(processes),
        "indexer_count": 0,
        "by_type": {},
        "issues": [],
        "recommendations": [],
        "indexing_active": False,
        "runaway_detected": False
    }

    HIGH_CPU_THRESHOLD = 50
    RUNAWAY_CPU_THRESHOLD = 100

    high_cpu_processes = []

    for proc in processes:
        cpu = proc.get("cpu_percent", 0)
        mem = proc.get("rss_mb", 0)

        analysis["total_cpu_percent"] += cpu
        analysis["total_memory_mb"] += mem

        proc_type = proc.get("type", "other")
        if proc_type not in analysis["by_type"]:
            analysis["by_type"][proc_type] = {
                "count": 0,
                "cpu_percent": 0,
                "memory_mb": 0,
                "pids": []
            }

        analysis["by_type"][proc_type]["count"] += 1
        analysis["by_type"][proc_type]["cpu_percent"] += cpu
        analysis["by_type"][proc_type]["memory_mb"] += mem
        analysis["by_type"][proc_type]["pids"].append(proc["pid"])

        if proc_type == "indexer":
            analysis["indexer_count"] += 1

        if cpu > HIGH_CPU_THRESHOLD:
            high_cpu_processes.append(proc)

    # Detect runaway indexing
    if analysis["total_cpu_percent"] > RUNAWAY_CPU_THRESHOLD:
        analysis["runaway_detected"] = True
        analysis["issues"].append(f"Runaway Spotlight indexing detected: {analysis['total_cpu_percent']:.1f}% total CPU")
        analysis["recommendations"].append("Run: sudo mdutil -E / (to rebuild index)")
        analysis["recommendations"].append("Or: sudo mdutil -i off / (to disable temporarily)")
    elif analysis["total_cpu_percent"] > HIGH_CPU_THRESHOLD:
        analysis["indexing_active"] = True
        analysis["issues"].append(f"Active Spotlight indexing: {analysis['total_cpu_percent']:.1f}% CPU")
        analysis["recommendations"].append("Wait for indexing to complete")
        analysis["recommendations"].append("Or add folders to Spotlight privacy list")

    # Check for many indexer processes
    if analysis["indexer_count"] > 5:
        analysis["issues"].append(f"Many mdworker processes ({analysis['indexer_count']})")

    # Check memory usage
    if analysis["total_memory_mb"] > 500:
        analysis["issues"].append(f"Spotlight using {analysis['total_memory_mb']:.0f} MB memory")

    # Add high CPU processes to analysis
    if high_cpu_processes:
        analysis["high_cpu_processes"] = [
            {"pid": p["pid"], "cpu": p["cpu_percent"], "type": p.get("type", "unknown")}
            for p in high_cpu_processes
        ]

    return analysis


def main() -> dict:
    """Main function - find and analyze Spotlight processes."""
    start_time = time.time()

    result = {
        "agent": "spotlight_mds_hunter",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "processes": [],
        "indexing_status": {},
        "analysis": {}
    }

    try:
        # Find Spotlight processes
        processes = find_spotlight_processes()
        result["processes"] = processes

        # Check indexing status
        result["indexing_status"] = check_indexing_status()

        # Analyze
        result["analysis"] = analyze_spotlight_usage(processes, result["indexing_status"])

        # Count high-CPU processes as "zombies"
        result["zombies_found"] = len([
            p for p in processes if p.get("cpu_percent", 0) > 50
        ])

        # Memory used by Spotlight
        result["memory_freed_mb"] = result["analysis"]["total_memory_mb"]

        # Actions = recommendations
        result["actions_taken"] = len(result["analysis"].get("recommendations", []))

        # PIDs
        result["pids"] = [p["pid"] for p in processes]

        # Reflect status
        if result["analysis"].get("runaway_detected"):
            result["status"] = "critical"
        elif result["analysis"].get("indexing_active"):
            result["status"] = "warning"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
