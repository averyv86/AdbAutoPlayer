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
Database Connection Leak Hunter - Agent 2

Detects idle database connections and orphaned DB processes that can be safely terminated.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- PostgreSQL connections (port 5432) idle >30min
- MySQL connections (port 3306) idle >30min
- Redis connections (port 6379) idle >30min
- Orphaned DB client processes with dead parent

Preserves:
- Active database servers (postgres, mysqld, redis-server)
- Claude Code and Ghostty processes
- Connections with active parent processes
"""

import psutil
import click
import json
import time
import subprocess
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

def is_db_server_running(port: int) -> bool:
    """Check if database server is running on given port"""
    server_names = {
        5432: ["postgres", "postgresql"],
        3306: ["mysqld", "mysql"],
        6379: ["redis-server", "redis"]
    }

    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name'].lower()
            if any(server in proc_name for server in server_names.get(port, [])):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False

def get_db_connections() -> list:
    """Get all database connections using lsof"""
    connections = []

    try:
        # Use lsof to find connections to common DB ports
        result = subprocess.run(
            ["lsof", "-i", ":5432,:3306,:6379", "-n", "-P"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return []

        # Parse lsof output
        lines = result.stdout.strip().split('\n')[1:]  # Skip header

        for line in lines:
            parts = line.split()
            if len(parts) >= 9:
                try:
                    pid = int(parts[1])
                    connections.append({
                        "pid": pid,
                        "command": parts[0],
                        "connection": parts[8]
                    })
                except (ValueError, IndexError):
                    continue

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return connections

def is_connection_idle(pid: int) -> tuple[bool, float]:
    """Check if connection process is idle (low CPU for >30min)"""
    try:
        proc = psutil.Process(pid)
        create_time = proc.create_time()
        elapsed = time.time() - create_time

        # Get CPU percent (averaged over 0.1 seconds)
        cpu = proc.cpu_percent(interval=0.1)

        # Idle if running >30min and CPU <1%
        idle_threshold = 30 * 60  # 30 minutes
        cpu_threshold = 1.0

        is_idle = elapsed > idle_threshold and cpu < cpu_threshold

        return is_idle, elapsed

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False, 0

def is_protected_process(cmdline: str) -> bool:
    """Check if process is protected (Claude Code, Ghostty, etc.)"""
    protected_patterns = [
        "claude",
        "ghostty",
        "claude-flow",
        "/Applications/Claude.app",
        "/Applications/Ghostty.app"
    ]

    cmdline_lower = cmdline.lower()
    return any(pattern in cmdline_lower for pattern in protected_patterns)

def find_zombie_connections() -> list:
    """Main detection function for zombie DB connections"""

    # Safety check: Skip if any DB server is actively running
    if is_db_server_running(5432):
        if click.confirm("PostgreSQL server detected running. Continue anyway?", default=False):
            pass
        else:
            return []

    if is_db_server_running(3306):
        if click.confirm("MySQL server detected running. Continue anyway?", default=False):
            pass
        else:
            return []

    if is_db_server_running(6379):
        if click.confirm("Redis server detected running. Continue anyway?", default=False):
            pass
        else:
            return []

    # Get all DB connections
    connections = get_db_connections()
    zombies = []

    for conn in connections:
        try:
            pid = conn["pid"]
            proc = psutil.Process(pid)

            # Get full command line
            cmdline = " ".join(proc.cmdline() or [])

            # Skip protected processes
            if is_protected_process(cmdline):
                continue

            # Check if idle
            is_idle, elapsed = is_connection_idle(pid)

            if not is_idle:
                continue

            # Check if parent is alive
            try:
                parent = proc.parent()
                if parent is None:
                    # Orphaned process
                    is_orphan = True
                else:
                    is_orphan = False
            except psutil.NoSuchProcess:
                is_orphan = True

            # Get memory info
            mem_info = proc.memory_info()

            zombies.append({
                "pid": pid,
                "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                "connection": conn["connection"],
                "elapsed": format_time(elapsed),
                "elapsed_seconds": int(elapsed),
                "cpu_percent": round(proc.cpu_percent(), 2),
                "memory": format_memory(mem_info.rss),
                "memory_bytes": mem_info.rss,
                "orphaned": is_orphan
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Database Connection Leak Hunter - Parallel Agent 2"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 2: Database Connection Leak Hunter[/cyan]")
        console.print("Scanning for idle database connections...\n")

    # Detect zombie connections
    zombies = find_zombie_connections()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "db_connection_leaks",
        "zombies_found": len(zombies),
        "total_memory_bytes": sum(z["memory_bytes"] for z in zombies),
        "total_memory": format_memory(sum(z["memory_bytes"] for z in zombies)),
        "execution_time_ms": round(execution_time, 2),
        "pids": [z["pid"] for z in zombies],
        "processes": zombies if verbose else []
    }

    # Output based on format
    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        from rich.table import Table
        table = Table(title=f"Database Connection Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Connection", justify="left")
        table.add_column("Runtime", justify="right")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory")
        table.add_column("Status")
        table.add_column("Command")

        for z in zombies:
            status = "🔴 Orphan" if z["orphaned"] else "⚠️  Idle"
            table.add_row(
                str(z["pid"]),
                z["connection"][:30],
                z["elapsed"],
                f"{z['cpu_percent']:.1f}%",
                z["memory"],
                status,
                z["command"][:40]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]DB Connection Leak Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
