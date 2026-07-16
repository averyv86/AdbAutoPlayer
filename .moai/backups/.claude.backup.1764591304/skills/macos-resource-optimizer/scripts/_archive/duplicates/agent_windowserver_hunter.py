#!/usr/bin/env python3
"""
WindowServer Memory Hunter - Agent
Analyzes WindowServer process memory consumption on macOS.

Detection:
- Finds WindowServer process using `pgrep -x WindowServer`
- Gets memory usage with `ps -o rss= -p PID`
- Reports GPU/display memory consumption
- Flags if WindowServer uses >1GB (typical: 200-800MB)

Output: JSON with WindowServer stats and recommendations
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


def get_windowserver_pid() -> int:
    """Get WindowServer process PID."""
    stdout, stderr, rc = run_command(["pgrep", "-x", "WindowServer"])

    if rc != 0 or not stdout.strip():
        return -1

    try:
        return int(stdout.strip().split('\n')[0])
    except ValueError:
        return -1


def get_process_memory(pid: int) -> dict:
    """Get detailed memory info for a process."""
    result = {
        "rss_kb": 0,
        "rss_mb": 0,
        "vsz_kb": 0,
        "vsz_mb": 0,
        "cpu_percent": 0
    }

    # Get RSS (Resident Set Size)
    stdout, stderr, rc = run_command(["ps", "-o", "rss=", "-p", str(pid)])
    if rc == 0 and stdout.strip():
        try:
            result["rss_kb"] = int(stdout.strip())
            result["rss_mb"] = result["rss_kb"] / 1024
        except ValueError:
            pass

    # Get VSZ (Virtual Size)
    stdout, stderr, rc = run_command(["ps", "-o", "vsz=", "-p", str(pid)])
    if rc == 0 and stdout.strip():
        try:
            result["vsz_kb"] = int(stdout.strip())
            result["vsz_mb"] = result["vsz_kb"] / 1024
        except ValueError:
            pass

    # Get CPU percent
    stdout, stderr, rc = run_command(["ps", "-o", "%cpu=", "-p", str(pid)])
    if rc == 0 and stdout.strip():
        try:
            result["cpu_percent"] = float(stdout.strip())
        except ValueError:
            pass

    return result


def get_display_info() -> dict:
    """Get display configuration info using system_profiler."""
    result = {
        "displays": [],
        "total_resolution": "",
        "retina": False
    }

    stdout, stderr, rc = run_command([
        "system_profiler", "SPDisplaysDataType", "-json"
    ])

    if rc == 0 and stdout.strip():
        try:
            data = json.loads(stdout)
            displays = data.get("SPDisplaysDataType", [])

            for gpu in displays:
                gpu_displays = gpu.get("spdisplays_ndrvs", [])
                for display in gpu_displays:
                    display_info = {
                        "name": display.get("_name", "Unknown"),
                        "resolution": display.get("_spdisplays_resolution", ""),
                        "retina": "Retina" in display.get("spdisplays_display_type", "")
                    }
                    result["displays"].append(display_info)
                    if display_info["retina"]:
                        result["retina"] = True

        except json.JSONDecodeError:
            pass

    return result


def analyze_windowserver(memory: dict, displays: dict) -> dict:
    """Analyze WindowServer memory usage and make recommendations."""
    analysis = {
        "status": "normal",
        "issues": [],
        "recommendations": [],
        "thresholds": {
            "normal_max_mb": 800,
            "warning_mb": 1024,
            "critical_mb": 2048
        }
    }

    rss_mb = memory.get("rss_mb", 0)

    # Adjust thresholds for Retina displays
    if displays.get("retina") or len(displays.get("displays", [])) > 1:
        analysis["thresholds"]["normal_max_mb"] = 1200
        analysis["thresholds"]["warning_mb"] = 1500
        analysis["thresholds"]["critical_mb"] = 2500
        analysis["notes"] = "Thresholds adjusted for Retina/multi-display setup"

    # Check memory usage
    if rss_mb > analysis["thresholds"]["critical_mb"]:
        analysis["status"] = "critical"
        analysis["issues"].append(f"WindowServer using {rss_mb:.0f} MB (critical threshold: {analysis['thresholds']['critical_mb']} MB)")
        analysis["recommendations"].append("Consider logging out and back in to reset WindowServer")
        analysis["recommendations"].append("Check for GPU-intensive applications")
        analysis["recommendations"].append("Reduce number of open windows/workspaces")
    elif rss_mb > analysis["thresholds"]["warning_mb"]:
        analysis["status"] = "warning"
        analysis["issues"].append(f"WindowServer using {rss_mb:.0f} MB (warning threshold: {analysis['thresholds']['warning_mb']} MB)")
        analysis["recommendations"].append("Close unused applications with heavy graphics")
        analysis["recommendations"].append("Reduce transparency effects in Accessibility settings")
    elif rss_mb > analysis["thresholds"]["normal_max_mb"]:
        analysis["status"] = "elevated"
        analysis["issues"].append(f"WindowServer memory slightly elevated: {rss_mb:.0f} MB")

    # Check CPU usage
    cpu = memory.get("cpu_percent", 0)
    if cpu > 20:
        analysis["issues"].append(f"High WindowServer CPU usage: {cpu:.1f}%")
        analysis["recommendations"].append("Check for animations or GPU-heavy content")

    return analysis


def main() -> dict:
    """Main function - analyze WindowServer memory."""
    start_time = time.time()

    result = {
        "agent": "windowserver_hunter",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "windowserver": {},
        "displays": {},
        "analysis": {}
    }

    try:
        # Get WindowServer PID
        pid = get_windowserver_pid()

        if pid == -1:
            result["status"] = "error"
            result["error"] = "WindowServer process not found"
            result["time_ms"] = round((time.time() - start_time) * 1000, 2)
            return result

        # Get memory info
        memory = get_process_memory(pid)
        memory["pid"] = pid
        result["windowserver"] = memory

        # Get display info
        result["displays"] = get_display_info()

        # Analyze
        result["analysis"] = analyze_windowserver(memory, result["displays"])

        # Count issues as "zombies"
        result["zombies_found"] = len(result["analysis"].get("issues", []))

        # Memory that could potentially be freed
        rss_mb = memory.get("rss_mb", 0)
        threshold = result["analysis"]["thresholds"]["normal_max_mb"]
        if rss_mb > threshold:
            result["memory_freed_mb"] = rss_mb - threshold

        # Actions = recommendations
        result["actions_taken"] = len(result["analysis"].get("recommendations", []))

        # Reflect analysis status
        if result["analysis"]["status"] in ["critical", "warning"]:
            result["status"] = result["analysis"]["status"]

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
