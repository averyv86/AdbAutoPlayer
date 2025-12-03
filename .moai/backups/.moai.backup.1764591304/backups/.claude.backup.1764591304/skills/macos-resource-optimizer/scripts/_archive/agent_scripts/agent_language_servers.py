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
IDE Language Server Hunter - Agent 8

Detects orphaned TypeScript, JSON, Markdown language servers from VS Code.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- tsserver.js processes (TypeScript language server)
- Code Helper (Plugin) - language server helpers
- jsonServerMain - JSON language server
- serverWorkerMain - Markdown/other language servers

Preserves:
- Language servers with active VS Code window
- Servers with recent file activity (<30 min)
- Servers with active file watchers
"""

import psutil
import click
import json
import time
import os
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

def is_vscode_running() -> bool:
    """Check if VS Code main process is running"""
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'] or ""
            if name in ["Code", "Visual Studio Code", "Cursor"]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def has_active_vscode_workspace() -> bool:
    """Check if VS Code has active renderer processes (open windows)"""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check for VS Code renderer processes (means window is open)
            if "Code Helper (Renderer)" in name or "Code Helper (Renderer)" in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def has_recent_file_activity(workspace_path: str, minutes: int = 30) -> bool:
    """Check if workspace has recent file modifications"""
    try:
        if not workspace_path or not os.path.exists(workspace_path):
            return False

        now = time.time()
        cutoff = now - (minutes * 60)

        # Check .vscode folder for recent activity
        vscode_dir = Path(workspace_path) / ".vscode"
        if vscode_dir.exists():
            for file in vscode_dir.glob("*"):
                if file.stat().st_mtime > cutoff:
                    return True

        # Check recent files in workspace
        workspace = Path(workspace_path)
        if workspace.exists():
            for file in workspace.rglob("*"):
                if file.is_file() and file.stat().st_mtime > cutoff:
                    return True

    except (OSError, PermissionError):
        pass

    return False

def is_protected_language_server(proc, cmdline: str) -> bool:
    """Check if language server should be protected"""

    # Protected if VS Code is running with active windows
    if is_vscode_running() and has_active_vscode_workspace():
        return True

    # Check for active file watchers (connections indicate activity)
    try:
        connections = proc.net_connections()
        if len(connections) > 0:
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    # Try to extract workspace path from command line
    try:
        if "--socket" in cmdline:
            # Extract workspace path from socket path if possible
            parts = cmdline.split()
            for i, part in enumerate(parts):
                if part == "--socket" and i + 1 < len(parts):
                    socket_path = parts[i + 1]
                    # Socket paths often contain workspace identifiers
                    workspace_path = None
                    if "/workspace/" in socket_path:
                        workspace_path = socket_path.split("/workspace/")[1].split("/")[0]

                    if workspace_path and has_recent_file_activity(workspace_path):
                        return True
    except (IndexError, ValueError):
        pass

    return False

def detect_language_server_zombies() -> list:
    """Detect orphaned language server processes"""

    language_server_patterns = [
        "tsserver.js",
        "Code Helper (Plugin)",
        "jsonServerMain",
        "serverWorkerMain",
        "typescript-language-server",
        "vscode-json-language-server",
        "vscode-markdown-language-server"
    ]

    min_runtime_hours = 24  # 1 day
    memory_threshold_mb = 100  # Language servers typically use 100-200 MB

    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's a language server process
            is_language_server = any(pattern in name or pattern in cmdline for pattern in language_server_patterns)
            if not is_language_server:
                continue

            # Skip protected language servers
            if is_protected_language_server(proc, cmdline):
                continue

            # Calculate runtime
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time
            runtime_hours = elapsed / 3600

            # Check memory usage
            memory_mb = proc.info['memory_info'].rss / 1024 / 1024

            # Zombie criteria: running >24 hours, using >100MB, no active VS Code
            if runtime_hours > min_runtime_hours and memory_mb > memory_threshold_mb:
                # Determine server type
                server_type = "Unknown"
                if "tsserver" in cmdline:
                    server_type = "TypeScript"
                elif "json" in cmdline.lower():
                    server_type = "JSON"
                elif "markdown" in cmdline.lower():
                    server_type = "Markdown"
                elif "Code Helper (Plugin)" in name:
                    server_type = "VS Code Plugin"

                zombies.append({
                    "pid": proc.info['pid'],
                    "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                    "elapsed": format_time(elapsed),
                    "elapsed_hours": round(runtime_hours, 1),
                    "cpu_percent": round(proc.info['cpu_percent'], 2),
                    "memory": format_memory(proc.info['memory_info'].rss),
                    "memory_bytes": proc.info['memory_info'].rss,
                    "type": f"{server_type} Language Server"
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Language Server Hunter - Parallel Agent 8"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 8: Language Server Hunter[/cyan]")
        console.print("Scanning for orphaned IDE language servers...\n")

    # Detect zombies
    zombies = detect_language_server_zombies()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "language_servers",
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
        table = Table(title=f"Language Server Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Type", justify="left")
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
        console.print(f"[bold]Language Server Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
