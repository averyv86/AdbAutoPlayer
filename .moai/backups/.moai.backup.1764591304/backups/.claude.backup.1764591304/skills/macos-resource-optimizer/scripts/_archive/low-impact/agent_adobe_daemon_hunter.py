#!/usr/bin/env python3
"""
Adobe Daemon Hunter - Agent
Finds Adobe background processes and daemons on macOS.

Detection:
- Finds: AdobeIPCBroker, Creative Cloud, CCXProcess, AdobeUpdateService
- Uses `pgrep -f Adobe` and `ps aux | grep -i adobe`
- Calculates total Adobe memory consumption
- Reports which daemons are running

Output: JSON with Adobe process list and memory stats
"""

import json
import subprocess
import sys
import os
import time
import re


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


# Adobe daemon patterns to look for
ADOBE_PATTERNS = [
    "AdobeIPCBroker",
    "Creative Cloud",
    "CCXProcess",
    "AdobeUpdateService",
    "Adobe Desktop Service",
    "AdobeGCClient",
    "Adobe CEF Helper",
    "AdobeCRDaemon",
    "AGSService",
    "AdobeResourceSynchronizer",
    "Core Sync",
    "CCLibrary",
    "node.* Adobe",
    "Adobe Crash Reporter",
    "LogTransport",
    "Adobe Genuine",
    "ACC Helper",
    "AdobeExtensionsService"
]

# Categorize daemons by type
DAEMON_CATEGORIES = {
    "creative_cloud": ["Creative Cloud", "CCXProcess", "CCLibrary", "ACC Helper", "Core Sync"],
    "ipc_sync": ["AdobeIPCBroker", "AdobeResourceSynchronizer"],
    "update_services": ["AdobeUpdateService", "AdobeGCClient", "Adobe Genuine"],
    "crash_logging": ["Adobe Crash Reporter", "LogTransport"],
    "background_helpers": ["Adobe CEF Helper", "AdobeCRDaemon", "AGSService", "Adobe Desktop Service", "AdobeExtensionsService"]
}


def find_adobe_processes() -> list:
    """Find all Adobe-related processes."""
    processes = []
    seen_pids = set()

    # Method 1: pgrep -f Adobe
    stdout, stderr, rc = run_command(["pgrep", "-f", "Adobe"])
    if rc == 0 and stdout.strip():
        pids = stdout.strip().split('\n')
        for pid in pids:
            if pid.strip():
                seen_pids.add(pid.strip())

    # Method 2: ps aux | grep -i adobe
    stdout, stderr, rc = run_command_shell("ps aux | grep -i adobe | grep -v grep")

    if rc == 0 and stdout.strip():
        for line in stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 11:
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                # RSS is in KB (column 5 with headers, but we need to parse differently)
                command = ' '.join(parts[10:])

                seen_pids.add(pid)

    # Get detailed info for each PID
    for pid in seen_pids:
        try:
            proc_info = get_process_details(pid)
            if proc_info and is_adobe_process(proc_info.get("command", "")):
                processes.append(proc_info)
        except Exception:
            continue

    return processes


def get_process_details(pid: str) -> dict:
    """Get detailed information about a process."""
    # Get full process info
    stdout, stderr, rc = run_command([
        "ps", "-o", "pid=,rss=,vsz=,%cpu=,%mem=,etime=,command=", "-p", pid
    ])

    if rc != 0 or not stdout.strip():
        return None

    parts = stdout.strip().split(None, 6)
    if len(parts) < 7:
        return None

    try:
        return {
            "pid": int(parts[0]),
            "rss_kb": int(parts[1]),
            "rss_mb": int(parts[1]) / 1024,
            "vsz_kb": int(parts[2]),
            "cpu_percent": float(parts[3]),
            "mem_percent": float(parts[4]),
            "elapsed_time": parts[5],
            "command": parts[6][:200]  # Truncate long commands
        }
    except (ValueError, IndexError):
        return None


def is_adobe_process(command: str) -> bool:
    """Check if command is an Adobe process."""
    command_lower = command.lower()
    return any(pattern.lower() in command_lower for pattern in ADOBE_PATTERNS)


def categorize_daemon(command: str) -> str:
    """Categorize an Adobe daemon by type."""
    for category, patterns in DAEMON_CATEGORIES.items():
        for pattern in patterns:
            if pattern.lower() in command.lower():
                return category
    return "other"


def analyze_adobe_daemons(processes: list) -> dict:
    """Analyze Adobe daemon impact and make recommendations."""
    analysis = {
        "total_memory_mb": 0,
        "total_cpu_percent": 0,
        "daemon_count": len(processes),
        "by_category": {},
        "issues": [],
        "recommendations": [],
        "can_disable": []
    }

    # Categorize and sum resources
    for proc in processes:
        analysis["total_memory_mb"] += proc.get("rss_mb", 0)
        analysis["total_cpu_percent"] += proc.get("cpu_percent", 0)

        category = categorize_daemon(proc.get("command", ""))
        if category not in analysis["by_category"]:
            analysis["by_category"][category] = {
                "count": 0,
                "memory_mb": 0,
                "processes": []
            }

        analysis["by_category"][category]["count"] += 1
        analysis["by_category"][category]["memory_mb"] += proc.get("rss_mb", 0)
        analysis["by_category"][category]["processes"].append(proc["pid"])

    # Analyze and recommend
    if analysis["total_memory_mb"] > 1000:
        analysis["issues"].append(f"Adobe daemons using {analysis['total_memory_mb']:.0f} MB total")
        analysis["recommendations"].append("Consider disabling Adobe Creative Cloud auto-start")

    if analysis["daemon_count"] > 5:
        analysis["issues"].append(f"Many Adobe background processes running ({analysis['daemon_count']})")

    # Check for update services
    if "update_services" in analysis["by_category"]:
        update_mem = analysis["by_category"]["update_services"]["memory_mb"]
        if update_mem > 200:
            analysis["can_disable"].append("Adobe Update Services (can be disabled in Creative Cloud preferences)")

    # Check for crash/logging
    if "crash_logging" in analysis["by_category"]:
        analysis["can_disable"].append("Adobe Crash Reporter and LogTransport (safe to disable)")

    return analysis


def main() -> dict:
    """Main function - find and analyze Adobe daemons."""
    start_time = time.time()

    result = {
        "agent": "adobe_daemon_hunter",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "processes": [],
        "analysis": {}
    }

    try:
        # Find Adobe processes
        processes = find_adobe_processes()
        result["processes"] = processes

        # Analyze
        result["analysis"] = analyze_adobe_daemons(processes)

        # Count as zombies (background daemons that could be disabled)
        result["zombies_found"] = len(processes)

        # Memory that could be freed
        result["memory_freed_mb"] = result["analysis"]["total_memory_mb"]

        # Actions = recommendations + can_disable items
        result["actions_taken"] = (
            len(result["analysis"].get("recommendations", [])) +
            len(result["analysis"].get("can_disable", []))
        )

        # PIDs for potential termination
        result["pids"] = [p["pid"] for p in processes]

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
