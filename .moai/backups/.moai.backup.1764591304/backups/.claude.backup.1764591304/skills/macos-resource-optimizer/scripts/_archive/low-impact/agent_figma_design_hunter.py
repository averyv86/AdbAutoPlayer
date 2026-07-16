#!/usr/bin/env python3
"""
Figma Design Tool Hunter - Agent
Finds Figma helper processes on macOS.

Detection:
- Finds: "Figma Helper", "Figma Agent", "Figma" main process
- Uses `pgrep -f Figma`
- Calculates memory per Figma helper
- Reports total consumption (often 2-8GB for heavy users)

Output: JSON with Figma process list and memory stats
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


# Figma process patterns
FIGMA_PATTERNS = [
    "Figma",
    "Figma Helper",
    "Figma Agent",
    "Figma Helper (Renderer)",
    "Figma Helper (GPU)",
    "Figma Helper (Plugin)"
]

# Process types for categorization
FIGMA_PROCESS_TYPES = {
    "main": ["Figma"],
    "renderer": ["Figma Helper (Renderer)", "Helper (Renderer)"],
    "gpu": ["Figma Helper (GPU)", "Helper (GPU)"],
    "plugin": ["Figma Helper (Plugin)", "Helper (Plugin)"],
    "agent": ["Figma Agent"],
    "helper": ["Figma Helper"]
}


def get_process_details(pid: str) -> dict:
    """Get detailed information about a process."""
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
            "command": parts[6][:200]
        }
    except (ValueError, IndexError):
        return None


def categorize_figma_process(command: str) -> str:
    """Categorize a Figma process by type."""
    command_lower = command.lower()

    for process_type, patterns in FIGMA_PROCESS_TYPES.items():
        for pattern in patterns:
            if pattern.lower() in command_lower:
                return process_type

    return "other"


def find_figma_processes() -> list:
    """Find all Figma-related processes."""
    processes = []
    seen_pids = set()

    # Method 1: pgrep -f Figma
    stdout, stderr, rc = run_command(["pgrep", "-f", "Figma"])
    if rc == 0 and stdout.strip():
        for pid in stdout.strip().split('\n'):
            if pid.strip():
                seen_pids.add(pid.strip())

    # Method 2: ps aux for more details
    stdout, stderr, rc = run_command_shell("ps aux | grep -i figma | grep -v grep")
    if rc == 0 and stdout.strip():
        for line in stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2:
                seen_pids.add(parts[1])

    # Get detailed info for each PID
    for pid in seen_pids:
        try:
            proc_info = get_process_details(pid)
            if proc_info:
                proc_info["type"] = categorize_figma_process(proc_info.get("command", ""))
                processes.append(proc_info)
        except Exception:
            continue

    return processes


def analyze_figma_usage(processes: list) -> dict:
    """Analyze Figma memory usage and make recommendations."""
    analysis = {
        "figma_running": len(processes) > 0,
        "total_memory_mb": 0,
        "total_cpu_percent": 0,
        "process_count": len(processes),
        "by_type": {},
        "issues": [],
        "recommendations": [],
        "memory_per_helper_mb": 0
    }

    if not processes:
        return analysis

    helper_count = 0
    helper_memory = 0

    for proc in processes:
        analysis["total_memory_mb"] += proc.get("rss_mb", 0)
        analysis["total_cpu_percent"] += proc.get("cpu_percent", 0)

        proc_type = proc.get("type", "other")
        if proc_type not in analysis["by_type"]:
            analysis["by_type"][proc_type] = {
                "count": 0,
                "memory_mb": 0,
                "pids": []
            }

        analysis["by_type"][proc_type]["count"] += 1
        analysis["by_type"][proc_type]["memory_mb"] += proc.get("rss_mb", 0)
        analysis["by_type"][proc_type]["pids"].append(proc["pid"])

        # Track helper processes
        if proc_type in ["renderer", "gpu", "plugin", "helper"]:
            helper_count += 1
            helper_memory += proc.get("rss_mb", 0)

    # Calculate average memory per helper
    if helper_count > 0:
        analysis["memory_per_helper_mb"] = helper_memory / helper_count

    # Analyze and recommend
    if analysis["total_memory_mb"] > 4000:
        analysis["issues"].append(f"Figma using {analysis['total_memory_mb']:.0f} MB (very high)")
        analysis["recommendations"].append("Close unused Figma tabs/files")
        analysis["recommendations"].append("Consider using Figma in browser instead")
    elif analysis["total_memory_mb"] > 2000:
        analysis["issues"].append(f"Figma using {analysis['total_memory_mb']:.0f} MB (high)")
        analysis["recommendations"].append("Close some Figma files to free memory")

    if helper_count > 10:
        analysis["issues"].append(f"Many Figma helpers running ({helper_count})")
        analysis["recommendations"].append("Reduce number of open Figma files")

    if analysis["memory_per_helper_mb"] > 500:
        analysis["issues"].append(f"Average helper using {analysis['memory_per_helper_mb']:.0f} MB each")

    # Check for GPU process
    if "gpu" in analysis["by_type"]:
        gpu_mem = analysis["by_type"]["gpu"]["memory_mb"]
        if gpu_mem > 1000:
            analysis["issues"].append(f"Figma GPU process using {gpu_mem:.0f} MB")
            analysis["recommendations"].append("Reduce canvas size or complexity in Figma files")

    return analysis


def main() -> dict:
    """Main function - find and analyze Figma processes."""
    start_time = time.time()

    result = {
        "agent": "figma_design_hunter",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "processes": [],
        "analysis": {}
    }

    try:
        # Find Figma processes
        processes = find_figma_processes()
        result["processes"] = processes

        # Analyze
        result["analysis"] = analyze_figma_usage(processes)

        # Count helper processes as "zombies" (potential optimization targets)
        helper_types = ["renderer", "gpu", "plugin", "helper"]
        result["zombies_found"] = sum(
            1 for p in processes if p.get("type") in helper_types
        )

        # Memory that could potentially be freed
        result["memory_freed_mb"] = result["analysis"]["total_memory_mb"]

        # Actions = recommendations
        result["actions_taken"] = len(result["analysis"].get("recommendations", []))

        # PIDs
        result["pids"] = [p["pid"] for p in processes]

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
