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
Process Analyzer - Detects zombie processes and classifies active vs idle

Identifies:
- Railway MCP servers (can be safely killed)
- Localhost zombie processes (idle 20+ hours)
- Stuck test processes (hung 10+ hours)

Preserves:
- Claude Code sessions
- claude-flow MCP servers
- Ghostty terminal
- Essential services (PostgreSQL, Redis, MeiliSearch, Ollama)
"""

import psutil
import click
import json
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Dict, List, Tuple
from datetime import timedelta

console = Console()

# Load configuration
SKILL_DIR = Path(__file__).parent.parent
CONFIG_DIR = SKILL_DIR / "config"

with open(CONFIG_DIR / "patterns.json") as f:
    PATTERNS = json.load(f)

with open(CONFIG_DIR / "exclusions.json") as f:
    EXCLUSIONS = json.load(f)


def format_time(seconds: float) -> str:
    """Format elapsed time as HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))


def format_memory(bytes_value: float) -> str:
    """Format memory in MB"""
    return f"{bytes_value / 1024 / 1024:.1f} MB"


def is_protected(proc: psutil.Process) -> bool:
    """Check if process is protected from termination"""
    try:
        cmdline = " ".join(proc.cmdline())
        name = proc.name()

        for protected in EXCLUSIONS["protected_processes"]:
            if protected.lower() in cmdline.lower() or protected.lower() in name.lower():
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True  # Protect if we can't access it


def detect_railway_mcp(processes: List[psutil.Process]) -> List[Dict]:
    """Detect Railway MCP server processes"""
    railway_procs = []

    for proc in processes:
        try:
            if is_protected(proc):
                continue

            cmdline = " ".join(proc.cmdline())

            # Match Railway MCP patterns
            if any(pattern in cmdline for pattern in PATTERNS["railway_mcp"]):
                create_time = proc.create_time()
                elapsed = time.time() - create_time if create_time else 0

                railway_procs.append({
                    "pid": proc.pid,
                    "command": cmdline[:60] + "..." if len(cmdline) > 60 else cmdline,
                    "elapsed": format_time(elapsed),
                    "cpu_percent": proc.cpu_percent(interval=0),
                    "memory": format_memory(proc.memory_info().rss),
                    "memory_bytes": proc.memory_info().rss
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return railway_procs


def detect_localhost_zombies(processes: List[psutil.Process]) -> List[Dict]:
    """Detect idle localhost processes (Python apps, bun servers)"""
    zombies = []
    cpu_threshold = PATTERNS["localhost_zombies"]["cpu_threshold"]
    runtime_threshold = PATTERNS["localhost_zombies"]["runtime_hours"] * 3600

    for proc in processes:
        try:
            if is_protected(proc):
                continue

            cmdline = " ".join(proc.cmdline())
            create_time = proc.create_time()
            elapsed = time.time() - create_time if create_time else 0
            cpu = proc.cpu_percent(interval=0)

            # Check for Python apps or bun servers
            is_python_app = "python" in cmdline.lower() and ("app.py" in cmdline or "multiprocessing" in cmdline)
            is_bun_server = "bun" in cmdline.lower() and ("run dev" in cmdline or proc.parent())

            if (is_python_app or is_bun_server) and cpu < cpu_threshold and elapsed > runtime_threshold:
                zombies.append({
                    "pid": proc.pid,
                    "command": cmdline[:60] + "..." if len(cmdline) > 60 else cmdline,
                    "elapsed": format_time(elapsed),
                    "cpu_percent": cpu,
                    "memory": format_memory(proc.memory_info().rss),
                    "memory_bytes": proc.memory_info().rss,
                    "type": "Python app" if is_python_app else "Bun server"
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return zombies


def detect_stuck_tests(processes: List[psutil.Process]) -> List[Dict]:
    """Detect stuck test processes"""
    stuck_tests = []
    runtime_threshold = PATTERNS["stuck_tests"]["runtime_hours"] * 3600
    cpu_threshold = PATTERNS["stuck_tests"]["cpu_threshold"]

    for proc in processes:
        try:
            if is_protected(proc):
                continue

            cmdline = " ".join(proc.cmdline())
            create_time = proc.create_time()
            elapsed = time.time() - create_time if create_time else 0
            cpu = proc.cpu_percent(interval=0)

            # Check for test frameworks
            is_test = any(framework in cmdline.lower() for framework in PATTERNS["stuck_tests"]["frameworks"])

            if is_test and cpu < cpu_threshold and elapsed > runtime_threshold:
                stuck_tests.append({
                    "pid": proc.pid,
                    "command": cmdline[:60] + "..." if len(cmdline) > 60 else cmdline,
                    "elapsed": format_time(elapsed),
                    "cpu_percent": cpu,
                    "memory": format_memory(proc.memory_info().rss),
                    "memory_bytes": proc.memory_info().rss
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return stuck_tests


def create_summary_table(railway: List[Dict], localhost: List[Dict], tests: List[Dict]) -> None:
    """Create summary table with all categories"""
    table = Table(title="Zombie Process Summary", show_header=True, header_style="bold cyan")

    table.add_column("Category", style="yellow")
    table.add_column("Count", justify="right")
    table.add_column("Total Memory", justify="right")
    table.add_column("Action", style="red")

    railway_mem = sum(p["memory_bytes"] for p in railway)
    localhost_mem = sum(p["memory_bytes"] for p in localhost)
    tests_mem = sum(p["memory_bytes"] for p in tests)

    table.add_row("Railway MCP Servers", str(len(railway)), format_memory(railway_mem), "KILL")
    table.add_row("Localhost Zombies", str(len(localhost)), format_memory(localhost_mem), "KILL")
    table.add_row("Stuck Tests", str(len(tests)), format_memory(tests_mem), "KILL")
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{len(railway) + len(localhost) + len(tests)}[/bold]",
        f"[bold]{format_memory(railway_mem + localhost_mem + tests_mem)}[/bold]",
        "[bold red]RECLAIM[/bold red]"
    )

    console.print(table)


def create_detail_table(category: str, processes: List[Dict]) -> None:
    """Create detailed table for a category"""
    if not processes:
        console.print(f"\n[green]✅ No {category} found[/green]")
        return

    table = Table(title=f"{category} ({len(processes)} processes)", show_header=True, header_style="bold cyan")

    table.add_column("PID", justify="right", style="yellow")
    table.add_column("Command", style="white")
    table.add_column("Elapsed", justify="right")
    table.add_column("CPU", justify="right")
    table.add_column("Memory", justify="right")

    if "type" in processes[0]:  # Localhost zombies have type
        table.add_column("Type", style="cyan")

    for proc in processes:
        row = [
            str(proc["pid"]),
            proc["command"],
            proc["elapsed"],
            f"{proc['cpu_percent']:.1f}%",
            proc["memory"]
        ]

        if "type" in proc:
            row.append(proc["type"])

        table.add_row(*row)

    console.print(table)


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='table',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed process information')
@click.option('--category', type=click.Choice(['railway', 'localhost', 'tests', 'all']), default='all',
              help='Filter by category')
def analyze(format: str, verbose: bool, category: str) -> None:
    """Analyze system processes and detect zombies"""

    console.print(Panel.fit(
        "[bold cyan]macOS Resource Optimizer - Process Analysis[/bold cyan]\n"
        "Detecting: Railway MCP | Localhost Zombies | Stuck Tests\n"
        "Preserving: Claude Code | claude-flow | Ghostty | Services",
        border_style="cyan"
    ))

    # Get all processes
    all_processes = list(psutil.process_iter())

    # Detect zombies by category
    railway = detect_railway_mcp(all_processes) if category in ['railway', 'all'] else []
    localhost = detect_localhost_zombies(all_processes) if category in ['localhost', 'all'] else []
    tests = detect_stuck_tests(all_processes) if category in ['tests', 'all'] else []

    # Output based on format
    if format == 'json':
        output = {
            "railway_mcp": railway,
            "localhost_zombies": localhost,
            "stuck_tests": tests,
            "total_processes": len(railway) + len(localhost) + len(tests),
            "total_memory_bytes": sum(p["memory_bytes"] for p in railway + localhost + tests)
        }
        console.print_json(data=output)

    elif format == 'summary':
        create_summary_table(railway, localhost, tests)

    else:  # table format
        create_summary_table(railway, localhost, tests)

        if verbose:
            console.print("\n")
            create_detail_table("Railway MCP Servers", railway)
            console.print("\n")
            create_detail_table("Localhost Zombies", localhost)
            console.print("\n")
            create_detail_table("Stuck Tests", tests)

    # Show PIDs for easy killing
    if railway or localhost or tests:
        all_pids = [p["pid"] for p in railway + localhost + tests]
        console.print(f"\n[bold yellow]PIDs to kill:[/bold yellow] {' '.join(map(str, all_pids))}")
        console.print(f"\n[dim]Run: uv run scripts/kill_zombies.py --category {category}[/dim]")


if __name__ == "__main__":
    analyze()
