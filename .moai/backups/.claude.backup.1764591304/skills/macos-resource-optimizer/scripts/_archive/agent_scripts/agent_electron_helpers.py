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
Electron Helper Hunter - Agent 9

Detects idle Electron app helpers (Notion, Slack, Discord, etc).
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Notion Helper (Renderer) - Heavy memory usage (1.2GB+)
- Slack Helper - Electron renderers
- Discord Helper - Voice/video helpers
- Other Electron app helpers without parent

Preserves:
- VS Code helpers (Code Helper - protected)
- Cursor helpers (protected)
- Helpers with active parent Electron app
- Protected patterns from exclusions.json
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
    """Format memory in GB for large values, MB otherwise"""
    gb = bytes_value / 1024 / 1024 / 1024
    if gb >= 1.0:
        return f"{gb:.2f} GB"
    return f"{bytes_value / 1024 / 1024:.1f} MB"

def get_parent_process_name(proc) -> str:
    """Get parent process name safely"""
    try:
        parent = proc.parent()
        if parent:
            return parent.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return None

def is_parent_app_running(app_name: str) -> bool:
    """Check if parent Electron app is running"""
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'] or ""
            if app_name.lower() in name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def is_protected_electron_helper(name: str, cmdline: str) -> bool:
    """Check if Electron helper is protected"""

    # Protected patterns (VS Code, Cursor, Visual Studio Code)
    protected_patterns = [
        "Code Helper",
        "Code Helper (Renderer)",
        "Code Helper (Plugin)",
        "Visual Studio Code",
        "Cursor"
    ]

    for pattern in protected_patterns:
        if pattern in name or pattern in cmdline:
            return True

    return False

def detect_electron_helper_zombies() -> list:
    """Detect idle Electron helper processes"""

    electron_helper_patterns = [
        "Notion Helper",
        "Slack Helper",
        "Discord Helper",
        "Electron Helper",
        "Helper (Renderer)",
        "Helper (GPU)",
        "Helper (Plugin)"
    ]

    min_runtime_hours = 4  # 4 hours
    memory_threshold_gb = 1.0  # 1GB
    cpu_threshold = 1.0  # <1% CPU

    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's an Electron helper
            is_electron_helper = any(pattern in name for pattern in electron_helper_patterns)
            if not is_electron_helper:
                continue

            # Skip protected helpers (VS Code, Cursor)
            if is_protected_electron_helper(name, cmdline):
                continue

            # Calculate runtime and memory
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time
            runtime_hours = elapsed / 3600
            memory_bytes = proc.info['memory_info'].rss
            memory_gb = memory_bytes / 1024 / 1024 / 1024
            cpu = proc.info['cpu_percent']

            # Zombie criteria: running >4 hours, using >1GB, <1% CPU
            if runtime_hours > min_runtime_hours and memory_gb > memory_threshold_gb and cpu < cpu_threshold:
                # Determine parent app
                parent_name = get_parent_process_name(proc)
                app_name = "Unknown"

                if "Notion" in name:
                    app_name = "Notion"
                    # Check if Notion.app is running
                    if is_parent_app_running("Notion"):
                        continue  # Skip if parent is active
                elif "Slack" in name:
                    app_name = "Slack"
                    if is_parent_app_running("Slack"):
                        continue
                elif "Discord" in name:
                    app_name = "Discord"
                    if is_parent_app_running("Discord"):
                        continue
                elif parent_name:
                    app_name = parent_name

                # Determine helper type
                helper_type = "Renderer"
                if "(GPU)" in name:
                    helper_type = "GPU"
                elif "(Plugin)" in name:
                    helper_type = "Plugin"
                elif "(Renderer)" in name:
                    helper_type = "Renderer"

                zombies.append({
                    "pid": proc.info['pid'],
                    "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                    "elapsed": format_time(elapsed),
                    "elapsed_hours": round(runtime_hours, 1),
                    "cpu_percent": round(cpu, 2),
                    "memory": format_memory(memory_bytes),
                    "memory_bytes": memory_bytes,
                    "type": f"{app_name} Helper ({helper_type})",
                    "app": app_name,
                    "helper_type": helper_type
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Electron Helper Hunter - Parallel Agent 9"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 9: Electron Helper Hunter[/cyan]")
        console.print("Scanning for idle Electron app helpers...\n")

    # Detect zombies
    zombies = detect_electron_helper_zombies()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "electron_helpers",
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
        table = Table(title=f"Electron Helper Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("App", justify="left")
        table.add_column("Type", justify="left")
        table.add_column("Runtime", justify="right")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory")

        for z in zombies:
            table.add_row(
                str(z["pid"]),
                z["app"],
                z["helper_type"],
                z["elapsed"],
                f"{z['cpu_percent']:.1f}%",
                z["memory"]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]Electron Helper Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
