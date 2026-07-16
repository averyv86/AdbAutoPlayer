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
Memory Reporter - Show memory usage before/after cleanup

Reports:
- Top memory consumers
- Total system memory usage
- Memory freed by cleanup
- Process categories breakdown
"""

import psutil
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict

console = Console()


def format_bytes(bytes_value: float) -> str:
    """Format bytes in human-readable form"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def get_top_processes(limit: int = 20) -> List[Dict]:
    """Get top memory consuming processes"""
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'cmdline']):
        try:
            mem_info = proc.info['memory_info']

            # Skip if memory_info is None (process terminated or inaccessible)
            if mem_info is None:
                continue

            cmdline = " ".join(proc.info['cmdline'] or [])

            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "memory_rss": mem_info.rss,
                "memory_percent": proc.memory_percent(),
                "cpu_percent": proc.info['cpu_percent'],
                "command": cmdline[:60] + "..." if len(cmdline) > 60 else cmdline
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            continue

    # Sort by memory usage
    processes.sort(key=lambda p: p["memory_rss"], reverse=True)

    return processes[:limit]


def get_system_memory() -> Dict:
    """Get system-wide memory statistics"""
    mem = psutil.virtual_memory()

    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "free": mem.free
    }


def categorize_processes() -> Dict[str, Dict]:
    """Categorize processes by type and calculate memory usage"""
    categories = {
        "Claude Code": {"keywords": ["claude-code", "claude code"], "memory": 0, "count": 0},
        "claude-flow": {"keywords": ["claude-flow"], "memory": 0, "count": 0},
        "MCP Servers": {"keywords": ["mcp", "@railway"], "memory": 0, "count": 0},
        "Node.js": {"keywords": ["node"], "memory": 0, "count": 0},
        "Python": {"keywords": ["python"], "memory": 0, "count": 0},
        "Bun": {"keywords": ["bun"], "memory": 0, "count": 0},
        "Browsers": {"keywords": ["chrome", "firefox", "safari"], "memory": 0, "count": 0},
        "Terminals": {"keywords": ["ghostty", "terminal", "iterm"], "memory": 0, "count": 0},
        "Services": {"keywords": ["postgres", "redis", "meilisearch", "ollama"], "memory": 0, "count": 0},
        "System": {"keywords": ["kernel", "launchd", "windowserver"], "memory": 0, "count": 0},
        "Other": {"keywords": [], "memory": 0, "count": 0}
    }

    for proc in psutil.process_iter(['name', 'memory_info', 'cmdline']):
        try:
            mem_info = proc.info['memory_info']

            # Skip if memory_info is None (process terminated or inaccessible)
            if mem_info is None:
                continue

            mem = mem_info.rss
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            name = proc.info['name'].lower()

            categorized = False

            for category, data in categories.items():
                if category == "Other":
                    continue

                for keyword in data["keywords"]:
                    if keyword in cmdline or keyword in name:
                        data["memory"] += mem
                        data["count"] += 1
                        categorized = True
                        break

                if categorized:
                    break

            if not categorized:
                categories["Other"]["memory"] += mem
                categories["Other"]["count"] += 1

        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            continue

    return categories


@click.command()
@click.option('--top', default=20, type=int, help='Number of top processes to show (default: 20)')
@click.option('--format', type=click.Choice(['table', 'summary']), default='table',
              help='Output format')
@click.option('--categories', is_flag=True, help='Show memory usage by process category')
def report(top: int, format: str, categories: bool) -> None:
    """Report memory usage and top consumers"""

    console.print(Panel.fit(
        "[bold cyan]macOS Resource Optimizer - Memory Report[/bold cyan]\n"
        "System memory usage and top consumers",
        border_style="cyan"
    ))

    # System memory
    sys_mem = get_system_memory()

    console.print("\n[bold]System Memory[/bold]")
    console.print(f"Total:     {format_bytes(sys_mem['total'])}")
    console.print(f"Used:      {format_bytes(sys_mem['used'])} ({sys_mem['percent']:.1f}%)")
    console.print(f"Available: {format_bytes(sys_mem['available'])}")
    console.print(f"Free:      {format_bytes(sys_mem['free'])}")

    # Categories if requested
    if categories:
        console.print("\n[bold]Memory by Category[/bold]")

        cats = categorize_processes()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Processes", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("% of Total", justify="right")

        # Sort by memory usage
        sorted_cats = sorted(cats.items(), key=lambda x: x[1]["memory"], reverse=True)

        for cat_name, cat_data in sorted_cats:
            if cat_data["count"] > 0:
                percent = (cat_data["memory"] / sys_mem["total"]) * 100
                table.add_row(
                    cat_name,
                    str(cat_data["count"]),
                    format_bytes(cat_data["memory"]),
                    f"{percent:.1f}%"
                )

        console.print(table)

    # Top processes
    console.print(f"\n[bold]Top {top} Memory Consumers[/bold]")

    processes = get_top_processes(limit=top)

    if format == 'summary':
        for i, proc in enumerate(processes[:10], 1):
            console.print(
                f"{i:2d}. PID {proc['pid']:5d} | "
                f"{format_bytes(proc['memory_rss']):>10s} | "
                f"{proc['name'][:30]}"
            )
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Rank", justify="right", style="dim")
        table.add_column("PID", justify="right", style="yellow")
        table.add_column("Process", style="white")
        table.add_column("Memory", justify="right")
        table.add_column("% RAM", justify="right")
        table.add_column("CPU %", justify="right")

        for i, proc in enumerate(processes, 1):
            table.add_row(
                str(i),
                str(proc["pid"]),
                proc["command"][:50],
                format_bytes(proc["memory_rss"]),
                f"{proc['memory_percent']:.1f}%",
                f"{proc['cpu_percent']:.1f}%" if proc['cpu_percent'] else "0.0%"
            )

        console.print(table)

    # Recommendations
    console.print("\n[bold cyan]Recommendations[/bold cyan]")

    high_mem_procs = [p for p in processes if p["memory_percent"] > 5.0]

    if high_mem_procs:
        console.print(f"[yellow]• {len(high_mem_procs)} processes using >5% RAM each[/yellow]")
        console.print("[dim]  Run: uv run scripts/analyze_processes.py to identify zombies[/dim]")

    if sys_mem["percent"] > 80:
        console.print("[red]• Memory usage >80% - cleanup recommended[/red]")
        console.print("[dim]  Run: uv run scripts/kill_zombies.py --dry-run[/dim]")
    elif sys_mem["percent"] > 60:
        console.print("[yellow]• Memory usage >60% - monitor closely[/yellow]")
    else:
        console.print("[green]• Memory usage healthy (<60%)[/green]")


if __name__ == "__main__":
    report()
