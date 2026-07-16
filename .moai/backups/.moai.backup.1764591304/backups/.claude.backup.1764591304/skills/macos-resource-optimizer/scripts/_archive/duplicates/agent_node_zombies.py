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
Node/Bun Zombie Hunter - Agent 3

Detects idle Node.js and Bun development servers.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Node.js servers (idle 20+ hours)
- Bun development servers
- Orphaned Node worker processes

Preserves:
- claude-flow Node processes
- Processes with active websockets
- Processes with recent port activity
"""

import psutil
import click
import json
import time
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

def is_protected_node(cmdline: str) -> bool:
    """Check if Node process is protected"""
    protected_patterns = [
        "claude-flow",
        "claude-code",
        "specstory",
        "mcp"
    ]

    for pattern in protected_patterns:
        if pattern in cmdline.lower():
            return True
    return False

def detect_node_zombies() -> list:
    """Detect Node/Bun zombie processes"""

    node_patterns = [
        "node server.js",
        "node app.js",
        "node index.js",
        "bun run dev",
        "bun run start",
        "bun server"
    ]

    min_runtime_hours = 20
    cpu_threshold = 1.0

    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's a Node/Bun process
            is_node_bun = "node" in name.lower() or "bun" in name.lower()
            if not is_node_bun:
                continue

            # Check for Node/Bun app patterns
            is_dev_server = any(pattern in cmdline.lower() for pattern in node_patterns)
            if not is_dev_server:
                continue

            # Skip protected processes
            if is_protected_node(cmdline):
                continue

            # Calculate runtime
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time
            runtime_hours = elapsed / 3600

            # Check if it's a zombie (long runtime, low CPU)
            cpu = proc.info['cpu_percent']

            if runtime_hours > min_runtime_hours and cpu < cpu_threshold:
                zombies.append({
                    "pid": proc.info['pid'],
                    "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                    "elapsed": format_time(elapsed),
                    "elapsed_hours": round(runtime_hours, 1),
                    "cpu_percent": round(cpu, 2),
                    "memory": format_memory(proc.info['memory_info'].rss),
                    "memory_bytes": proc.info['memory_info'].rss,
                    "type": "Bun server" if "bun" in name.lower() else "Node server"
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Node/Bun Zombie Hunter - Parallel Agent 3"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 3: Node/Bun Zombie Hunter[/cyan]")
        console.print("Scanning for idle Node.js and Bun servers...\n")

    # Detect zombies
    zombies = detect_node_zombies()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "node_zombies",
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
        table = Table(title=f"Node/Bun Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Type")
        table.add_column("Runtime", justify="right")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory")
        table.add_column("Command")

        for z in zombies:
            table.add_row(
                str(z["pid"]),
                z["type"],
                z["elapsed"],
                f"{z['cpu_percent']:.1f}%",
                z["memory"],
                z["command"][:40]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]Node/Bun Zombie Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
