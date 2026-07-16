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
Cleanup Verifier - Confirms cleanup succeeded and active work preserved

Checks:
✅ Zombie PIDs terminated
✅ Ports freed (5001, etc.)
✅ Active Claude Code sessions running
✅ claude-flow MCP servers running
✅ Ghostty terminal running
✅ Essential services running (PostgreSQL, Redis, MeiliSearch, Ollama)
"""

import psutil
import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Set

console = Console()

# Load configuration
SKILL_DIR = Path(__file__).parent.parent
CONFIG_DIR = SKILL_DIR / "config"

with open(CONFIG_DIR / "exclusions.json") as f:
    EXCLUSIONS = json.load(f)


def check_pids_terminated(pids: List[int]) -> Dict[str, any]:
    """Check if specific PIDs are terminated"""
    still_running = []

    for pid in pids:
        if psutil.pid_exists(pid):
            try:
                proc = psutil.Process(pid)
                still_running.append({
                    "pid": pid,
                    "name": proc.name(),
                    "status": proc.status()
                })
            except psutil.NoSuchProcess:
                pass  # Race condition - process terminated

    return {
        "total": len(pids),
        "still_running": len(still_running),
        "terminated": len(pids) - len(still_running),
        "processes": still_running,
        "success": len(still_running) == 0
    }


def check_ports_freed(ports: List[int]) -> Dict[str, any]:
    """Check if specific ports are freed"""
    occupied = []

    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port in ports:
                occupied.append({
                    "port": conn.laddr.port,
                    "status": conn.status,
                    "pid": conn.pid
                })
    except (psutil.AccessDenied, PermissionError) as e:
        # macOS requires elevated permissions for net_connections
        # Fall back to lsof command
        import subprocess
        seen_ports = set()
        for port in ports:
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{port}', '-sTCP:LISTEN'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            port_pid = (port, int(parts[1]))
                            if port_pid not in seen_ports:
                                seen_ports.add(port_pid)
                                occupied.append({
                                    "port": port,
                                    "status": "LISTEN",
                                    "pid": int(parts[1])
                                })
            except (subprocess.SubprocessError, ValueError):
                continue

    return {
        "total": len(ports),
        "occupied": len(occupied),
        "freed": len(ports) - len(occupied),
        "ports": occupied,
        "success": len(occupied) == 0
    }


def check_protected_processes() -> Dict[str, any]:
    """Verify protected processes still running"""
    found_processes = {}

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])
            name = proc.info['name']

            for protected in EXCLUSIONS["protected_processes"]:
                if protected.lower() in cmdline.lower() or protected.lower() in name.lower():
                    if protected not in found_processes:
                        found_processes[protected] = []
                    found_processes[protected].append({
                        "pid": proc.info['pid'],
                        "command": cmdline[:60] + "..." if len(cmdline) > 60 else cmdline
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Expected processes
    expected = {
        "claude-code": 5,      # 5 Claude Code sessions
        "claude-flow": 12,     # 12 MCP server processes
        "Ghostty": 1,          # Terminal
        "postgres": 1,         # Database
        "redis-server": 1,     # Cache
        "meilisearch": 1,      # Search
        "ollama": 1           # AI models
    }

    results = []
    all_found = True

    for process, expected_count in expected.items():
        found = found_processes.get(process, [])
        found_count = len(found)

        status = "✅" if found_count >= expected_count else "❌"
        if found_count < expected_count:
            all_found = False

        results.append({
            "process": process,
            "expected": expected_count,
            "found": found_count,
            "status": status,
            "pids": [p["pid"] for p in found]
        })

    return {
        "results": results,
        "success": all_found
    }


def check_essential_services() -> Dict[str, any]:
    """Check essential services on expected ports"""
    services = {
        5432: "PostgreSQL",
        6379: "Redis",
        7700: "MeiliSearch",
        11434: "Ollama"
    }

    results = []
    all_running = True

    try:
        for port, service_name in services.items():
            found = False
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    found = True
                    results.append({
                        "service": service_name,
                        "port": port,
                        "status": "✅ Running",
                        "pid": conn.pid
                    })
                    break

            if not found:
                all_running = False
                results.append({
                    "service": service_name,
                    "port": port,
                    "status": "❌ Not found",
                    "pid": None
                })
    except (psutil.AccessDenied, PermissionError):
        # macOS requires elevated permissions for net_connections
        # Fall back to lsof command
        import subprocess
        for port, service_name in services.items():
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{port}', '-sTCP:LISTEN'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    if lines:
                        parts = lines[0].split()
                        pid = int(parts[1]) if len(parts) >= 2 else None
                        results.append({
                            "service": service_name,
                            "port": port,
                            "status": "✅ Running",
                            "pid": pid
                        })
                    else:
                        all_running = False
                        results.append({
                            "service": service_name,
                            "port": port,
                            "status": "❌ Not found",
                            "pid": None
                        })
                else:
                    all_running = False
                    results.append({
                        "service": service_name,
                        "port": port,
                        "status": "❌ Not found",
                        "pid": None
                    })
            except (subprocess.SubprocessError, ValueError):
                all_running = False
                results.append({
                    "service": service_name,
                    "port": port,
                    "status": "❌ Error checking",
                    "pid": None
                })

    return {
        "results": results,
        "success": all_running
    }


@click.command()
@click.option('--pids', help='Comma-separated list of PIDs to check (e.g., "45087,44664,76501")')
@click.option('--ports', help='Comma-separated list of ports to check (e.g., "5001,3000")')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def verify(pids: str, ports: str, verbose: bool) -> None:
    """Verify cleanup succeeded and active work preserved"""

    console.print(Panel.fit(
        "[bold cyan]macOS Resource Optimizer - Cleanup Verification[/bold cyan]\n"
        "Checking: PIDs terminated | Ports freed | Active work preserved",
        border_style="cyan"
    ))

    all_checks_passed = True

    # Check PIDs if provided
    if pids:
        pid_list = [int(p.strip()) for p in pids.split(',')]
        console.print(f"\n[bold]1. Checking PIDs terminated ({len(pid_list)} total)[/bold]")

        result = check_pids_terminated(pid_list)

        if result["success"]:
            console.print(f"[green]✅ All {result['total']} PIDs terminated[/green]")
        else:
            console.print(f"[red]❌ {result['still_running']} PIDs still running:[/red]")
            for proc in result["processes"]:
                console.print(f"  PID {proc['pid']}: {proc['name']} ({proc['status']})")
            all_checks_passed = False

    # Check ports if provided
    if ports:
        port_list = [int(p.strip()) for p in ports.split(',')]
        console.print(f"\n[bold]2. Checking ports freed ({len(port_list)} total)[/bold]")

        result = check_ports_freed(port_list)

        if result["success"]:
            console.print(f"[green]✅ All {result['total']} ports freed[/green]")
        else:
            console.print(f"[yellow]⚠️  {result['occupied']} ports still occupied:[/yellow]")
            for port_info in result["ports"]:
                console.print(f"  Port {port_info['port']}: {port_info['status']} (PID {port_info['pid']})")
            all_checks_passed = False

    # Check protected processes
    console.print("\n[bold]3. Checking active work preserved[/bold]")
    result = check_protected_processes()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Process", style="yellow")
    table.add_column("Expected", justify="right")
    table.add_column("Found", justify="right")
    table.add_column("Status")

    if verbose:
        table.add_column("PIDs")

    for proc in result["results"]:
        row = [
            proc["process"],
            str(proc["expected"]),
            str(proc["found"]),
            proc["status"]
        ]

        if verbose:
            row.append(", ".join(map(str, proc["pids"][:3])) + ("..." if len(proc["pids"]) > 3 else ""))

        table.add_row(*row)

    console.print(table)

    if not result["success"]:
        all_checks_passed = False

    # Check essential services
    console.print("\n[bold]4. Checking essential services[/bold]")
    result = check_essential_services()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Service", style="yellow")
    table.add_column("Port", justify="right")
    table.add_column("Status")

    if verbose:
        table.add_column("PID", justify="right")

    for svc in result["results"]:
        row = [
            svc["service"],
            str(svc["port"]),
            svc["status"]
        ]

        if verbose and svc["pid"]:
            row.append(str(svc["pid"]))

        table.add_row(*row)

    console.print(table)

    if not result["success"]:
        all_checks_passed = False

    # Final summary
    console.print("\n" + "="*60)

    if all_checks_passed:
        console.print("[bold green]✅ All verification checks passed![/bold green]")
        console.print("\n[cyan]Cleanup successful - system healthy[/cyan]")
    else:
        console.print("[bold red]❌ Some verification checks failed[/bold red]")
        console.print("\n[yellow]Review the issues above and take corrective action[/yellow]")


if __name__ == "__main__":
    verify()
