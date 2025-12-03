#!/usr/bin/env python3
"""
Memory Growth Detector - Agent
Detects runaway memory growth in processes on macOS.

Detection:
- Samples top 20 processes by memory twice (1s apart)
- Compares memory growth rate
- Flags processes growing >100MB/s
- Reports potential memory leaks

Output: JSON with memory growth analysis and leak suspects
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


def get_top_processes_by_memory(count: int = 20) -> list:
    """Get top N processes by memory usage."""
    # Use ps sorted by RSS (resident set size)
    stdout, stderr, rc = run_command([
        "ps", "-arcwwwxo", "pid,rss,%mem,%cpu,etime,command"
    ])

    if rc != 0 or not stdout.strip():
        return []

    processes = []
    lines = stdout.strip().split('\n')

    # Skip header
    for line in lines[1:count+1]:
        parts = line.split(None, 5)
        if len(parts) >= 6:
            try:
                processes.append({
                    "pid": int(parts[0]),
                    "rss_kb": int(parts[1]),
                    "rss_mb": int(parts[1]) / 1024,
                    "mem_percent": float(parts[2]),
                    "cpu_percent": float(parts[3]),
                    "elapsed_time": parts[4],
                    "command": parts[5][:100]
                })
            except (ValueError, IndexError):
                continue

    return processes


def sample_memory_twice(interval_seconds: float = 1.0, top_count: int = 20) -> tuple:
    """Sample memory usage twice with interval."""
    sample1 = get_top_processes_by_memory(top_count)
    sample1_time = time.time()

    # Create lookup by PID
    sample1_by_pid = {p["pid"]: p for p in sample1}

    # Wait for interval
    time.sleep(interval_seconds)

    sample2 = get_top_processes_by_memory(top_count)
    sample2_time = time.time()

    actual_interval = sample2_time - sample1_time

    return sample1_by_pid, sample2, actual_interval


def calculate_growth_rates(sample1_by_pid: dict, sample2: list, interval: float) -> list:
    """Calculate memory growth rates for processes."""
    growth_data = []

    for proc in sample2:
        pid = proc["pid"]

        if pid in sample1_by_pid:
            prev = sample1_by_pid[pid]
            current_kb = proc["rss_kb"]
            prev_kb = prev["rss_kb"]

            growth_kb = current_kb - prev_kb
            growth_mb = growth_kb / 1024
            growth_rate_mb_per_sec = growth_mb / interval if interval > 0 else 0

            growth_data.append({
                "pid": pid,
                "command": proc["command"],
                "current_mb": proc["rss_mb"],
                "previous_mb": prev["rss_mb"],
                "growth_mb": growth_mb,
                "growth_rate_mb_per_sec": growth_rate_mb_per_sec,
                "elapsed_time": proc["elapsed_time"],
                "cpu_percent": proc["cpu_percent"]
            })
        else:
            # New process in top 20
            growth_data.append({
                "pid": pid,
                "command": proc["command"],
                "current_mb": proc["rss_mb"],
                "previous_mb": 0,
                "growth_mb": proc["rss_mb"],
                "growth_rate_mb_per_sec": proc["rss_mb"] / interval if interval > 0 else 0,
                "elapsed_time": proc["elapsed_time"],
                "cpu_percent": proc["cpu_percent"],
                "new_process": True
            })

    return growth_data


def analyze_memory_growth(growth_data: list, interval: float) -> dict:
    """Analyze memory growth patterns and detect leaks."""
    analysis = {
        "sample_interval_seconds": round(interval, 2),
        "processes_analyzed": len(growth_data),
        "leak_suspects": [],
        "fast_growers": [],
        "stable_processes": [],
        "issues": [],
        "recommendations": [],
        "thresholds": {
            "leak_suspect_mb_per_sec": 100,
            "fast_growth_mb_per_sec": 50,
            "concerning_growth_mb_per_sec": 20
        }
    }

    for proc in growth_data:
        rate = proc.get("growth_rate_mb_per_sec", 0)

        if rate > analysis["thresholds"]["leak_suspect_mb_per_sec"]:
            proc["severity"] = "critical"
            analysis["leak_suspects"].append(proc)
        elif rate > analysis["thresholds"]["fast_growth_mb_per_sec"]:
            proc["severity"] = "warning"
            analysis["fast_growers"].append(proc)
        elif rate > analysis["thresholds"]["concerning_growth_mb_per_sec"]:
            proc["severity"] = "concerning"
            analysis["fast_growers"].append(proc)
        elif rate < 1:  # Less than 1 MB/s growth
            analysis["stable_processes"].append({
                "pid": proc["pid"],
                "command": proc["command"][:50],
                "current_mb": proc["current_mb"]
            })

    # Generate issues and recommendations
    if analysis["leak_suspects"]:
        for suspect in analysis["leak_suspects"]:
            analysis["issues"].append(
                f"Memory leak suspected in PID {suspect['pid']} ({suspect['command'][:30]}): "
                f"growing at {suspect['growth_rate_mb_per_sec']:.1f} MB/s"
            )
        analysis["recommendations"].append("Consider restarting processes with suspected memory leaks")
        analysis["recommendations"].append("Check application logs for errors")
        analysis["recommendations"].append("Monitor with: top -o mem")

    if analysis["fast_growers"]:
        for grower in analysis["fast_growers"]:
            if grower.get("severity") == "warning":
                analysis["issues"].append(
                    f"Fast memory growth in PID {grower['pid']} ({grower['command'][:30]}): "
                    f"{grower['growth_rate_mb_per_sec']:.1f} MB/s"
                )

    # Summary stats
    analysis["summary"] = {
        "leak_suspect_count": len(analysis["leak_suspects"]),
        "fast_grower_count": len(analysis["fast_growers"]),
        "total_growth_mb_per_sec": sum(p.get("growth_rate_mb_per_sec", 0) for p in growth_data if p.get("growth_rate_mb_per_sec", 0) > 0),
        "stable_count": len(analysis["stable_processes"])
    }

    return analysis


def main() -> dict:
    """Main function - detect memory growth patterns."""
    start_time = time.time()

    result = {
        "agent": "memory_growth_detector",
        "zombies_found": 0,
        "memory_freed_mb": 0,
        "actions_taken": 0,
        "status": "success",
        "time_ms": 0,
        "growth_data": [],
        "analysis": {}
    }

    try:
        # Sample memory twice
        sample1_by_pid, sample2, interval = sample_memory_twice(
            interval_seconds=1.0,
            top_count=20
        )

        # Calculate growth rates
        growth_data = calculate_growth_rates(sample1_by_pid, sample2, interval)
        result["growth_data"] = growth_data

        # Analyze
        result["analysis"] = analyze_memory_growth(growth_data, interval)

        # Count leak suspects as "zombies"
        result["zombies_found"] = len(result["analysis"]["leak_suspects"])

        # Memory that could be freed by restarting leak suspects
        result["memory_freed_mb"] = sum(
            p.get("current_mb", 0) for p in result["analysis"]["leak_suspects"]
        )

        # Actions = recommendations
        result["actions_taken"] = len(result["analysis"].get("recommendations", []))

        # PIDs of suspects
        result["pids"] = [p["pid"] for p in result["analysis"]["leak_suspects"]]

        # Status based on findings
        if result["analysis"]["leak_suspects"]:
            result["status"] = "critical"
        elif result["analysis"]["fast_growers"]:
            result["status"] = "warning"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["time_ms"] = round((time.time() - start_time) * 1000, 2)

    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps(output, indent=2))
