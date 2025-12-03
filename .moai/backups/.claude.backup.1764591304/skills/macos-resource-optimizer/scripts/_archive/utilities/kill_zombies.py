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
Zombie Killer - Safely terminates zombie processes

Safety features:
- Dry-run mode (default)
- Interactive confirmation prompts
- Graceful termination (SIGTERM → SIGKILL)
- Protected process whitelist
- Detailed logging
"""

import psutil
import click
import signal
import time
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from typing import List, Dict, Tuple
import sys

console = Console()

# Import process detection from analyze script
sys.path.insert(0, str(Path(__file__).parent))
from analyze_processes import (
    detect_railway_mcp,
    detect_localhost_zombies,
    detect_stuck_tests,
    format_memory,
    is_protected,
    EXCLUSIONS
)


def kill_process(pid: int, timeout: int = 5, force: bool = False) -> bool:
    """
    Kill a process gracefully (SIGTERM) with fallback to SIGKILL

    Returns True if successfully killed, False otherwise
    """
    try:
        proc = psutil.Process(pid)

        # Double-check it's not protected
        if is_protected(proc):
            console.print(f"[yellow]⚠️  PID {pid} is protected - skipping[/yellow]")
            return False

        # Send SIGTERM (graceful)
        console.print(f"[cyan]Sending SIGTERM to PID {pid}...[/cyan]")
        proc.terminate()

        # Wait for graceful shutdown
        try:
            proc.wait(timeout=timeout)
            console.print(f"[green]✅ PID {pid} terminated gracefully[/green]")
            return True
        except psutil.TimeoutExpired:
            # Process didn't terminate - escalate to SIGKILL if forced
            if force or Confirm.ask(f"Process {pid} didn't terminate. Force kill (SIGKILL)?"):
                console.print(f"[red]Sending SIGKILL to PID {pid}...[/red]")
                proc.kill()
                proc.wait(timeout=2)
                console.print(f"[green]✅ PID {pid} force-killed[/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Skipped force-kill of PID {pid}[/yellow]")
                return False

    except psutil.NoSuchProcess:
        console.print(f"[green]✅ PID {pid} already terminated[/green]")
        return True
    except psutil.AccessDenied:
        console.print(f"[red]❌ Permission denied for PID {pid}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error killing PID {pid}: {e}[/red]")
        return False


def kill_category(processes: List[Dict], category_name: str, dry_run: bool,
                  timeout: int, force: bool) -> Tuple[int, int]:
    """
    Kill all processes in a category

    Returns: (successful_kills, failed_kills)
    """
    if not processes:
        console.print(f"\n[green]✅ No {category_name} to kill[/green]")
        return (0, 0)

    console.print(f"\n[bold yellow]{category_name}[/bold yellow]")
    console.print(f"Found {len(processes)} processes:")

    for proc in processes:
        console.print(f"  PID {proc['pid']}: {proc['command'][:60]} ({proc['memory']})")

    total_memory = sum(p["memory_bytes"] for p in processes)
    console.print(f"\n[cyan]Total memory to reclaim: {format_memory(total_memory)}[/cyan]")

    if dry_run:
        console.print(f"[yellow]DRY RUN: Would kill {len(processes)} processes[/yellow]")
        return (0, 0)

    if not force:
        if not Confirm.ask(f"\n[bold red]Kill {len(processes)} {category_name}?[/bold red]"):
            console.print("[yellow]Skipped[/yellow]")
            return (0, 0)

    successful = 0
    failed = 0

    for proc in processes:
        if kill_process(proc["pid"], timeout=timeout, force=force):
            successful += 1
        else:
            failed += 1

        # Small delay between kills
        time.sleep(0.5)

    console.print(f"\n[bold]Results:[/bold] {successful} killed, {failed} failed")
    return (successful, failed)


@click.command()
@click.option('--dry-run', is_flag=True, default=True,
              help='Show what would be killed without actually killing (default: True)')
@click.option('--execute', is_flag=True,
              help='Actually kill processes (overrides --dry-run)')
@click.option('--category', type=click.Choice(['railway', 'localhost', 'tests', 'all']), default='all',
              help='Kill specific category')
@click.option('--force', is_flag=True,
              help='Skip confirmation prompts (use with caution)')
@click.option('--timeout', default=5, type=int,
              help='Seconds to wait before SIGKILL (default: 5)')
def kill_zombies(dry_run: bool, execute: bool, category: str, force: bool, timeout: int) -> None:
    """Safely terminate zombie processes"""

    # Override dry_run if --execute is specified
    if execute:
        dry_run = False

    mode = "[yellow]DRY RUN MODE[/yellow]" if dry_run else "[red]EXECUTION MODE[/red]"

    console.print(Panel.fit(
        f"[bold cyan]macOS Resource Optimizer - Zombie Killer[/bold cyan]\n{mode}\n"
        f"Category: {category} | Timeout: {timeout}s | Force: {force}",
        border_style="red" if not dry_run else "yellow"
    ))

    if not dry_run:
        console.print("\n[bold red]⚠️  WARNING: This will terminate processes![/bold red]")
        console.print("[yellow]Protected processes (never killed):[/yellow]")
        for proc in EXCLUSIONS["protected_processes"]:
            console.print(f"  • {proc}")
        console.print()

        if not force:
            if not Confirm.ask("[bold]Continue with process termination?[/bold]"):
                console.print("[yellow]Cancelled by user[/yellow]")
                return

    # Get all processes
    all_processes = list(psutil.process_iter())

    # Detect zombies by category
    railway = detect_railway_mcp(all_processes) if category in ['railway', 'all'] else []
    localhost = detect_localhost_zombies(all_processes) if category in ['localhost', 'all'] else []
    tests = detect_stuck_tests(all_processes) if category in ['tests', 'all'] else []

    # Kill by category
    total_successful = 0
    total_failed = 0

    if railway:
        success, failed = kill_category(railway, "Railway MCP Servers", dry_run, timeout, force)
        total_successful += success
        total_failed += failed

    if localhost:
        success, failed = kill_category(localhost, "Localhost Zombies", dry_run, timeout, force)
        total_successful += success
        total_failed += failed

    if tests:
        success, failed = kill_category(tests, "Stuck Tests", dry_run, timeout, force)
        total_successful += success
        total_failed += failed

    # Summary
    console.print("\n" + "="*60)

    if dry_run:
        total_procs = len(railway) + len(localhost) + len(tests)
        total_mem = sum(p["memory_bytes"] for p in railway + localhost + tests)
        console.print(f"[yellow]DRY RUN: Would kill {total_procs} processes ({format_memory(total_mem)})[/yellow]")
        console.print(f"\n[dim]To actually kill, run: uv run scripts/kill_zombies.py --execute --category {category}[/dim]")
    else:
        console.print(f"[bold]Total: {total_successful} killed, {total_failed} failed[/bold]")

        if total_successful > 0:
            console.print(f"\n[green]✅ Cleanup complete![/green]")
            console.print(f"[dim]Run verification: uv run scripts/verify_cleanup.py[/dim]")


if __name__ == "__main__":
    kill_zombies()
