#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "psutil>=6.1.0",
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Socket Leak Hunter - Agent 15

Detects socket leaks and processes with excessive open connections.

Detection Targets:
- CLOSE_WAIT connections (stuck sockets)
- Processes with >100 open sockets
- FIN_WAIT states indicating potential issues
- Total open connection analysis

Reports:
- Per-process socket counts
- Stuck socket states
- Potential leak indicators
"""

import json
import subprocess
import time
from collections import defaultdict
from typing import Any, Dict, List

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

SOCKET_THRESHOLD = 100  # Alert if process has more than this many sockets
CLOSE_WAIT_THRESHOLD = 5  # Alert if process has more than this many CLOSE_WAIT


def get_process_name(pid: int) -> str:
    """Get process name by PID."""
    try:
        proc = psutil.Process(pid)
        return proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"


def get_process_cmdline(pid: int) -> str:
    """Get process command line by PID."""
    try:
        proc = psutil.Process(pid)
        cmdline = proc.cmdline()
        return " ".join(cmdline)[:100] if cmdline else proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"


def run_command(cmd: List[str], timeout: int = 30) -> tuple[str, int]:
    """Run a command and return output and return code."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1


def analyze_connections() -> Dict[str, Any]:
    """Analyze all network connections using lsof (more reliable on macOS)."""
    # Group by PID
    by_pid = defaultdict(lambda: {
        "total": 0,
        "established": 0,
        "close_wait": 0,
        "time_wait": 0,
        "fin_wait_1": 0,
        "fin_wait_2": 0,
        "listen": 0,
        "other": 0,
        "states": defaultdict(int),
    })

    # Track overall stats
    overall = {
        "total": 0,
        "by_status": defaultdict(int),
        "close_wait_total": 0,
        "error": None,
    }

    # Use netstat for overall stats (no permission issues)
    output, code = run_command(["netstat", "-an"])

    if code == 0:
        for line in output.strip().split('\n'):
            if 'tcp' in line.lower():
                overall["total"] += 1
                parts = line.split()
                status = parts[-1] if len(parts) >= 6 and parts[-1].isupper() else "UNKNOWN"

                overall["by_status"][status] = overall["by_status"].get(status, 0) + 1
                if status == 'CLOSE_WAIT':
                    overall["close_wait_total"] += 1

    # Use lsof to get per-process network info (handles permissions better)
    lsof_output, lsof_code = run_command(["lsof", "-i", "-n", "-P"])

    if lsof_code == 0:
        for line in lsof_output.strip().split('\n')[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 10:
                try:
                    pid = int(parts[1])
                    # Get connection state from the line
                    state = "UNKNOWN"
                    if "(ESTABLISHED)" in line:
                        state = "ESTABLISHED"
                    elif "(CLOSE_WAIT)" in line:
                        state = "CLOSE_WAIT"
                    elif "(TIME_WAIT)" in line:
                        state = "TIME_WAIT"
                    elif "(LISTEN)" in line:
                        state = "LISTEN"
                    elif "(FIN_WAIT1)" in line or "(FIN_WAIT_1)" in line:
                        state = "FIN_WAIT1"
                    elif "(FIN_WAIT2)" in line or "(FIN_WAIT_2)" in line:
                        state = "FIN_WAIT2"

                    by_pid[pid]["total"] += 1
                    by_pid[pid]["states"][state] += 1

                    if state == 'ESTABLISHED':
                        by_pid[pid]["established"] += 1
                    elif state == 'CLOSE_WAIT':
                        by_pid[pid]["close_wait"] += 1
                    elif state == 'TIME_WAIT':
                        by_pid[pid]["time_wait"] += 1
                    elif state == 'FIN_WAIT1':
                        by_pid[pid]["fin_wait_1"] += 1
                    elif state == 'FIN_WAIT2':
                        by_pid[pid]["fin_wait_2"] += 1
                    elif state == 'LISTEN':
                        by_pid[pid]["listen"] += 1
                    else:
                        by_pid[pid]["other"] += 1
                except (ValueError, IndexError):
                    continue
    else:
        overall["error"] = "Could not retrieve per-process connection info"

    return {
        "by_pid": dict(by_pid),
        "overall": overall,
    }


def find_socket_leaks(conn_analysis: Dict[str, Any], verbose: bool = False) -> List[Dict[str, Any]]:
    """Find processes with potential socket leaks."""
    leaks = []

    for pid, stats in conn_analysis["by_pid"].items():
        issues = []
        severity = "low"

        # Check for high socket count
        if stats["total"] > SOCKET_THRESHOLD:
            issues.append(f"High socket count: {stats['total']}")
            severity = "medium"

        # Check for CLOSE_WAIT accumulation
        if stats["close_wait"] > CLOSE_WAIT_THRESHOLD:
            issues.append(f"CLOSE_WAIT accumulation: {stats['close_wait']}")
            severity = "high"

        # Check for FIN_WAIT states
        fin_waits = stats["fin_wait_1"] + stats["fin_wait_2"]
        if fin_waits > 10:
            issues.append(f"FIN_WAIT accumulation: {fin_waits}")
            if severity != "high":
                severity = "medium"

        if issues:
            process_name = get_process_name(pid)
            cmdline = get_process_cmdline(pid)

            leak_info = {
                "pid": pid,
                "process_name": process_name,
                "cmdline": cmdline,
                "total_sockets": stats["total"],
                "established": stats["established"],
                "close_wait": stats["close_wait"],
                "time_wait": stats["time_wait"],
                "fin_wait": fin_waits,
                "issues": issues,
                "severity": severity,
            }
            leaks.append(leak_info)

            if verbose:
                sev_color = {"low": "yellow", "medium": "orange", "high": "red"}[severity]
                console.print(f"  [{sev_color}]{process_name}[/{sev_color}] (PID {pid}): {', '.join(issues)}")

    return sorted(leaks, key=lambda x: x["close_wait"], reverse=True)


def get_lsof_count() -> int:
    """Get total open file/socket count using lsof."""
    try:
        result = subprocess.run(
            ["lsof", "-i"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Count lines (minus header)
        lines = result.stdout.strip().split('\n')
        return max(0, len(lines) - 1)
    except Exception:
        return -1


def detect_socket_leaks(verbose: bool = False) -> Dict[str, Any]:
    """Main detection function for socket leaks."""
    start_time = time.time()

    if verbose:
        console.print("[cyan]Analyzing socket connections for leaks...[/cyan]\n")

    # Analyze connections
    conn_analysis = analyze_connections()

    if verbose:
        console.print(f"[bold]Total connections:[/bold] {conn_analysis['overall']['total']}\n")

    # Find leaks
    if verbose:
        console.print("[bold]Processes with potential socket issues:[/bold]")
    leaks = find_socket_leaks(conn_analysis, verbose)

    # Get lsof count
    lsof_count = get_lsof_count()

    execution_time = (time.time() - start_time) * 1000

    # Calculate stats
    total_close_wait = conn_analysis["overall"]["close_wait_total"]
    high_severity = len([l for l in leaks if l["severity"] == "high"])
    medium_severity = len([l for l in leaks if l["severity"] == "medium"])

    return {
        "zombies_found": len(leaks),
        "memory_freed_mb": 0,  # Socket cleanup doesn't directly free memory
        "actions_taken": len(leaks),
        "status": "success",
        "time_ms": round(execution_time, 2),
        "details": {
            "total_connections": conn_analysis["overall"]["total"],
            "close_wait_total": total_close_wait,
            "connection_states": dict(conn_analysis["overall"]["by_status"]),
            "lsof_count": lsof_count,
            "processes_with_issues": len(leaks),
            "high_severity_count": high_severity,
            "medium_severity_count": medium_severity,
            "leaks": leaks,
            "recommendation": (
                "Review CLOSE_WAIT connections - they indicate the remote end closed but local process hasn't. "
                "May require process restart to clear stuck sockets."
            ),
        }
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    # Connection states table
    states_table = Table(title="Connection States")
    states_table.add_column("State", style="cyan")
    states_table.add_column("Count", justify="right")

    for state, count in sorted(result["details"]["connection_states"].items()):
        style = "red" if state == 'CLOSE_WAIT' and count > 5 else "white"
        states_table.add_row(state, str(count), style=style)

    console.print(states_table)

    # Leaks table
    if result["details"]["leaks"]:
        console.print("")
        leaks_table = Table(title="Processes with Socket Issues")
        leaks_table.add_column("PID", style="cyan", justify="right")
        leaks_table.add_column("Process", style="white")
        leaks_table.add_column("Total", justify="right")
        leaks_table.add_column("CLOSE_WAIT", justify="right")
        leaks_table.add_column("Severity")
        leaks_table.add_column("Issues")

        for leak in result["details"]["leaks"][:15]:
            sev_style = {"low": "yellow", "medium": "orange3", "high": "red"}[leak["severity"]]
            leaks_table.add_row(
                str(leak["pid"]),
                leak["process_name"][:20],
                str(leak["total_sockets"]),
                str(leak["close_wait"]),
                f"[{sev_style}]{leak['severity'].upper()}[/{sev_style}]",
                leak["issues"][0][:30] if leak["issues"] else ""
            )

        console.print(leaks_table)


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]Socket Leak Analysis[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Processes with issues: {result['zombies_found']}")
    console.print(f"Execution time: {result['time_ms']:.2f}ms")

    console.print(f"\n[bold]Connection Overview:[/bold]")
    console.print(f"  Total connections: {result['details']['total_connections']}")
    console.print(f"  CLOSE_WAIT (stuck): {result['details']['close_wait_total']}")
    console.print(f"  Open network files (lsof): {result['details']['lsof_count']}")

    console.print(f"\n[bold]Issue Severity:[/bold]")
    console.print(f"  High: {result['details']['high_severity_count']}")
    console.print(f"  Medium: {result['details']['medium_severity_count']}")

    if result["details"]["leaks"]:
        console.print(f"\n[bold]Top Offenders:[/bold]")
        for leak in result["details"]["leaks"][:5]:
            sev = leak["severity"].upper()
            console.print(f"  [{sev}] {leak['process_name']} (PID {leak['pid']}): "
                        f"{leak['total_sockets']} sockets, {leak['close_wait']} CLOSE_WAIT")

    console.print(f"\n[dim]{result['details']['recommendation']}[/dim]")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Detect socket leaks and processes with excessive connections."""
    result = detect_socket_leaks(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
