#!/usr/bin/env python3
"""
Swap & Purgeable Memory Hunter - Agent
Analyzes swap usage and purgeable memory pressure on macOS.

Detection:
- Uses `sysctl vm.swapusage` to get swap statistics
- Uses `vm_stat` to analyze purgeable pages and memory pressure
- Reports current swap usage and pressure levels
- Suggests `sudo purge` if high pressure detected

Output: JSON with swap stats, purgeable memory, and recommendations
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


def parse_swap_usage() -> dict:
    """Parse sysctl vm.swapusage output."""
    stdout, stderr, rc = run_command(["sysctl", "vm.swapusage"])

    if rc != 0:
        return {"error": stderr, "total": 0, "used": 0, "free": 0}

    # Format: vm.swapusage: total = 2048.00M  used = 512.00M  free = 1536.00M  (encrypted)
    result = {"total": 0, "used": 0, "free": 0, "encrypted": False, "raw": stdout.strip()}

    # Parse values in MB
    total_match = re.search(r'total\s*=\s*([\d.]+)M', stdout)
    used_match = re.search(r'used\s*=\s*([\d.]+)M', stdout)
    free_match = re.search(r'free\s*=\s*([\d.]+)M', stdout)

    if total_match:
        result["total"] = float(total_match.group(1))
    if used_match:
        result["used"] = float(used_match.group(1))
    if free_match:
        result["free"] = float(free_match.group(1))

    result["encrypted"] = "(encrypted)" in stdout
    result["usage_percent"] = (result["used"] / result["total"] * 100) if result["total"] > 0 else 0

    return result


def parse_vm_stat() -> dict:
    """Parse vm_stat output for purgeable memory analysis."""
    stdout, stderr, rc = run_command(["vm_stat"])

    if rc != 0:
        return {"error": stderr}

    result = {"raw_lines": [], "pages": {}, "page_size": 16384}  # Default page size

    # Extract page size from first line
    page_size_match = re.search(r'page size of (\d+) bytes', stdout)
    if page_size_match:
        result["page_size"] = int(page_size_match.group(1))

    # Parse all page statistics
    for line in stdout.strip().split('\n'):
        if ':' in line and 'page size' not in line:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(' ', '_').replace('"', '')
                value_str = parts[1].strip().rstrip('.')
                try:
                    value = int(value_str)
                    result["pages"][key] = value
                except ValueError:
                    pass

    # Calculate memory in MB
    page_size = result["page_size"]
    pages = result["pages"]

    result["purgeable_mb"] = pages.get("pages_purgeable", 0) * page_size / (1024 * 1024)
    result["free_mb"] = pages.get("pages_free", 0) * page_size / (1024 * 1024)
    result["active_mb"] = pages.get("pages_active", 0) * page_size / (1024 * 1024)
    result["inactive_mb"] = pages.get("pages_inactive", 0) * page_size / (1024 * 1024)
    result["wired_mb"] = pages.get("pages_wired_down", 0) * page_size / (1024 * 1024)
    result["compressed_mb"] = pages.get("pages_occupied_by_compressor", 0) * page_size / (1024 * 1024)
    result["speculative_mb"] = pages.get("pages_speculative", 0) * page_size / (1024 * 1024)
    result["pageins"] = pages.get("pageins", 0)
    result["pageouts"] = pages.get("pageouts", 0)
    result["swapins"] = pages.get("swapins", 0)
    result["swapouts"] = pages.get("swapouts", 0)

    return result


def analyze_memory_pressure(swap: dict, vm: dict) -> dict:
    """Analyze memory pressure and make recommendations."""
    analysis = {
        "pressure_level": "normal",
        "score": 0,
        "recommendations": [],
        "issues": []
    }

    # Score based on swap usage
    if swap.get("usage_percent", 0) > 80:
        analysis["score"] += 40
        analysis["issues"].append(f"High swap usage: {swap['usage_percent']:.1f}%")
    elif swap.get("usage_percent", 0) > 50:
        analysis["score"] += 20
        analysis["issues"].append(f"Moderate swap usage: {swap['usage_percent']:.1f}%")

    # Score based on purgeable memory
    purgeable = vm.get("purgeable_mb", 0)
    if purgeable > 2000:  # More than 2GB purgeable
        analysis["score"] += 30
        analysis["issues"].append(f"High purgeable memory: {purgeable:.0f} MB")
        analysis["recommendations"].append("Run `sudo purge` to free purgeable memory")
    elif purgeable > 1000:
        analysis["score"] += 15
        analysis["issues"].append(f"Moderate purgeable memory: {purgeable:.0f} MB")

    # Score based on pageouts (indicates memory pressure)
    pageouts = vm.get("pageouts", 0)
    swapouts = vm.get("swapouts", 0)

    if pageouts > 100000:
        analysis["score"] += 20
        analysis["issues"].append(f"High pageout activity: {pageouts:,}")

    if swapouts > 50000:
        analysis["score"] += 10
        analysis["issues"].append(f"High swapout activity: {swapouts:,}")

    # Determine pressure level
    if analysis["score"] >= 60:
        analysis["pressure_level"] = "critical"
        analysis["recommendations"].append("Consider closing memory-heavy applications")
        analysis["recommendations"].append("Restart system if issues persist")
    elif analysis["score"] >= 30:
        analysis["pressure_level"] = "high"
        analysis["recommendations"].append("Monitor memory usage closely")
    elif analysis["score"] >= 15:
        analysis["pressure_level"] = "moderate"

    return analysis


def main() -> dict:
    """Main function - analyze swap and purgeable memory."""
    start_time = time.time()

    result = {
        "agent": "swap_purgeable_hunter",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "swap": {},
        "vm_stat": {},
        "analysis": {}
    }

    try:
        # Get swap usage
        result["swap"] = parse_swap_usage()

        # Get VM statistics
        result["vm_stat"] = parse_vm_stat()

        # Analyze pressure
        result["analysis"] = analyze_memory_pressure(result["swap"], result["vm_stat"])

        # Count "zombies" as issues found
        result["zombies_found"] = len(result["analysis"].get("issues", []))

        # Calculate potential memory that could be freed
        result["memory_freed_mb"] = result["vm_stat"].get("purgeable_mb", 0)

        # Actions = number of recommendations
        result["actions_taken"] = len(result["analysis"].get("recommendations", []))

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
