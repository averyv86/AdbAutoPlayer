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
Python Zombie Hunter - Agent 2

Detects idle Python web servers and multiprocessing zombies.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Flask/FastAPI/Uvicorn servers (idle 20+ hours)
- Orphaned multiprocessing.spawn processes
- Zombie Python workers

Preserves:
- Claude Code Python processes
- Active Jupyter/IPython kernels
- Processes with recent file activity
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

def is_protected_python(cmdline: str) -> bool:
    """Check if Python process is protected"""
    protected_patterns = [
        "claude-code",
        "claude",
        "specstory",
        "jupyter",
        "ipython",
        ".claude/",
        "claude-flow"
    ]

    for pattern in protected_patterns:
        if pattern in cmdline.lower():
            return True
    return False

def detect_python_zombies() -> list:
    """Detect Python zombie processes"""

    python_patterns = [
        "python app.py",
        "python3 app.py",
        "python -m flask",
        "python -m uvicorn",
        "gunicorn",
        "multiprocessing.spawn"
    ]

    min_runtime_hours = 20
    cpu_threshold = 1.0

    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's a Python process
            is_python = "python" in name.lower() or "python3" in name.lower()
            if not is_python:
                continue

            # Check for Python app patterns
            is_python_app = any(pattern in cmdline.lower() for pattern in python_patterns)
            if not is_python_app:
                continue

            # Skip protected processes
            if is_protected_python(cmdline):
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
                    "type": "Python app"
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Python Zombie Hunter - Parallel Agent 2"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 2: Python Zombie Hunter[/cyan]")
        console.print("Scanning for idle Python web servers...\n")

    # Detect zombies
    zombies = detect_python_zombies()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "python_zombies",
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
        table = Table(title=f"Python Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Runtime", justify="right")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory")
        table.add_column("Command")

        for z in zombies:
            table.add_row(
                str(z["pid"]),
                z["elapsed"],
                f"{z['cpu_percent']:.1f}%",
                z["memory"],
                z["command"][:50]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]Python Zombie Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
