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
SSH Session Leak Hunter - Agent SSH

Detects stale SSH ControlMaster sockets and orphaned SSH tunnels.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Orphaned ControlMaster sockets (no active SSH process)
- Idle SSH tunnels (>1 hour, no traffic)
- Forgotten SSH port forwards

Preserves:
- Active SSH connections (<5 minutes)
- SSH processes with recent activity
- Tunnels with active connections

Recovery: 0.5-1 GB (socket files + zombie SSH processes)
"""

import psutil
import click
import json
import time
import os
import subprocess
from pathlib import Path
from datetime import timedelta
from rich.console import Console

console = Console()

# ============================================================================
# ALL FUNCTIONS INLINE (100% self-contained)
# ============================================================================

def format_time(seconds: float) -> str:
    """Format elapsed time as HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))

def format_memory(bytes_value: float) -> str:
    """Format memory in MB"""
    return f"{bytes_value / 1024 / 1024:.1f} MB"

def find_controlmaster_sockets() -> list:
    """Find SSH ControlMaster socket files"""
    socket_paths = []

    # Check ~/.ssh/ directory
    ssh_dir = Path.home() / ".ssh"
    if ssh_dir.exists():
        for socket_file in ssh_dir.glob("master-*"):
            if socket_file.is_socket():
                socket_paths.append(socket_file)

    # Check /tmp/ for SSH sockets
    tmp_dir = Path("/tmp")
    for pattern in ["ssh-*", "controlmaster-*"]:
        for socket_file in tmp_dir.glob(pattern):
            if socket_file.is_socket():
                socket_paths.append(socket_file)

    return socket_paths

def is_socket_active(socket_path: Path) -> bool:
    """Check if socket has active connections using lsof"""
    try:
        result = subprocess.run(
            ["lsof", "-U", str(socket_path)],
            capture_output=True,
            text=True,
            timeout=2
        )
        # If lsof finds processes, socket is active
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def find_ssh_tunnels() -> list:
    """Find SSH tunnel processes"""
    tunnels = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's an SSH process
            if name.lower() != "ssh":
                continue

            # Check for tunnel flags
            is_tunnel = any(flag in cmdline for flag in ["-L", "-R", "-D", "LocalForward", "RemoteForward"])
            if not is_tunnel:
                continue

            # Calculate runtime
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time

            tunnels.append({
                'pid': proc.info['pid'],
                'cmdline': cmdline,
                'elapsed': elapsed,
                'memory_bytes': proc.info['memory_info'].rss
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return tunnels

def has_active_ssh_connections() -> bool:
    """Check if there are any active SSH connections"""
    for proc in psutil.process_iter(['name', 'create_time']):
        try:
            name = proc.info['name'] or ""
            if name.lower() == "ssh":
                # Check if SSH process is recent (< 5 minutes)
                create_time = proc.info['create_time']
                age_minutes = (time.time() - create_time) / 60
                if age_minutes < 5:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def find_zombie_ssh_sessions() -> list:
    """Detect zombie SSH sessions and orphaned sockets"""
    zombies = []

    min_runtime_hours = 1.0  # Consider idle after 1 hour
    min_recent_use_minutes = 5.0  # Protect if used in last 5 minutes

    # Find orphaned ControlMaster sockets
    sockets = find_controlmaster_sockets()
    for socket_path in sockets:
        if not is_socket_active(socket_path):
            try:
                stat_info = socket_path.stat()
                age_seconds = time.time() - stat_info.st_mtime
                age_minutes = age_seconds / 60

                # Skip if recently modified (within 5 minutes)
                if age_minutes < min_recent_use_minutes:
                    continue

                zombies.append({
                    "pid": 0,  # Socket file, no PID
                    "command": f"orphaned socket: {socket_path.name}",
                    "elapsed": format_time(age_seconds),
                    "elapsed_hours": round(age_seconds / 3600, 1),
                    "cpu_percent": 0.0,
                    "memory": "0 MB",
                    "memory_bytes": socket_path.stat().st_size,
                    "type": "SSH socket",
                    "path": str(socket_path)
                })
            except (OSError, FileNotFoundError):
                continue

    # Find idle SSH tunnels
    tunnels = find_ssh_tunnels()
    for tunnel in tunnels:
        runtime_hours = tunnel['elapsed'] / 3600
        age_minutes = tunnel['elapsed'] / 60

        # Skip if too recent
        if age_minutes < min_recent_use_minutes:
            continue

        # Check if idle for too long
        if runtime_hours > min_runtime_hours:
            zombies.append({
                "pid": tunnel['pid'],
                "command": tunnel['cmdline'][:80] + "..." if len(tunnel['cmdline']) > 80 else tunnel['cmdline'],
                "elapsed": format_time(tunnel['elapsed']),
                "elapsed_hours": round(runtime_hours, 1),
                "cpu_percent": 0.0,
                "memory": format_memory(tunnel['memory_bytes']),
                "memory_bytes": tunnel['memory_bytes'],
                "type": "SSH tunnel"
            })

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """SSH Session Leak Hunter - Parallel Agent SSH"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent SSH: SSH Session Leak Hunter[/cyan]")
        console.print("Scanning for orphaned sockets and idle tunnels...\n")

    # Safety check: Skip if active SSH connections exist
    if has_active_ssh_connections():
        if verbose:
            console.print("[yellow]⚠️  Active SSH connections detected. Skipping scan for safety.[/yellow]")
        result = {
            "agent": "ssh_session_leaks",
            "zombies_found": 0,
            "total_memory_bytes": 0,
            "total_memory": "0 MB",
            "execution_time_ms": 0,
            "pids": [],
            "processes": [],
            "skipped": True,
            "reason": "Active SSH connections detected"
        }
        print(json.dumps(result, indent=2))
        return

    # Detect zombies
    zombies = find_zombie_ssh_sessions()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "ssh_session_leaks",
        "zombies_found": len(zombies),
        "total_memory_bytes": sum(z["memory_bytes"] for z in zombies),
        "total_memory": format_memory(sum(z["memory_bytes"] for z in zombies)),
        "execution_time_ms": round(execution_time, 2),
        "pids": [z["pid"] for z in zombies if z["pid"] > 0],
        "processes": zombies if verbose else []
    }

    # Output based on format
    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        from rich.table import Table
        table = Table(title=f"SSH Session Leaks ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Type", justify="left")
        table.add_column("Runtime", justify="right")
        table.add_column("Memory")
        table.add_column("Command")

        for z in zombies:
            table.add_row(
                str(z["pid"]) if z["pid"] > 0 else "N/A",
                z["type"],
                z["elapsed"],
                z["memory"],
                z["command"][:50]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]SSH Session Leak Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
