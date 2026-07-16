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
Parallel Zombie Killer
Safely terminates zombie processes identified by the 10-agent system.

Features:
- Graceful termination (SIGTERM → SIGKILL)
- Interactive confirmation by category
- Dry-run mode
- Comprehensive safety checks
- Progress tracking
- Memory freed reporting
"""

import json
import sys
import time
import signal
import psutil
from pathlib import Path
from typing import List, Dict, Any, Set
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm

console = Console()

# Categories for grouping processes
PROCESS_CATEGORIES = {
    'workerd': ['workerd', 'wrangler'],
    'browser_helpers': ['ChromeDriver', 'geckodriver', 'msedgedriver', 'Chrome Helper'],
    'language_servers': ['rust-analyzer', 'gopls', 'typescript-language-server', 'pylsp'],
    'node_tools': ['node', 'npm', 'yarn', 'pnpm', 'bun'],
    'python_tools': ['python', 'python3', 'pip', 'pipenv', 'poetry'],
    'build_tools': ['cargo', 'mvn', 'gradle', 'webpack', 'rollup'],
    'dev_servers': ['webpack-dev-server', 'vite', 'next', 'astro'],
    'other': []  # Catch-all
}


def load_exclusions() -> Dict[str, Any]:
    """Load protection rules from config/exclusions.json."""
    config_path = Path(__file__).parent.parent / 'config' / 'exclusions.json'

    if not config_path.exists():
        return {
            'protected_processes': [
                'claude-code', 'claude-flow', 'Ghostty', 'postgres',
                'redis', 'meilisearch', 'ollama', 'code', 'cursor'
            ],
            'protected_patterns': [
                'vscode', 'cursor', 'docker', 'postgresql', 'nginx'
            ]
        }

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading exclusions: {e}[/red]")
        return {'protected_processes': [], 'protected_patterns': []}


def is_protected(proc_name: str, exclusions: Dict[str, Any]) -> bool:
    """Check if process is protected from termination."""
    proc_lower = proc_name.lower()

    # Check exact matches
    for protected in exclusions.get('protected_processes', []):
        if protected.lower() in proc_lower:
            return True

    # Check patterns
    for pattern in exclusions.get('protected_patterns', []):
        if pattern.lower() in proc_lower:
            return True

    return False


def categorize_process(proc_name: str) -> str:
    """Categorize process by name."""
    proc_lower = proc_name.lower()

    for category, patterns in PROCESS_CATEGORIES.items():
        if category == 'other':
            continue
        for pattern in patterns:
            if pattern.lower() in proc_lower:
                return category

    return 'other'


def get_process_info(pid: int) -> Dict[str, Any] | None:
    """Get detailed process information."""
    try:
        proc = psutil.Process(pid)
        return {
            'pid': pid,
            'name': proc.name(),
            'memory_bytes': proc.memory_info().rss,
            'memory_mb': round(proc.memory_info().rss / (1024 * 1024), 2),
            'cpu_percent': round(proc.cpu_percent(interval=0.1), 2),
            'category': categorize_process(proc.name())
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def verify_safe_to_kill(pid: int, exclusions: Dict[str, Any], cpu_threshold: float = 5.0) -> tuple[bool, str]:
    """
    Verify process is safe to kill.

    Returns (is_safe, reason) tuple.
    """
    try:
        proc = psutil.Process(pid)
        name = proc.name()

        # Check if protected
        if is_protected(name, exclusions):
            return False, f"Protected process: {name}"

        # Check if process became active
        cpu_percent = proc.cpu_percent(interval=0.1)
        if cpu_percent >= cpu_threshold:
            return False, f"Process became active (CPU: {cpu_percent}%)"

        # Check if system critical
        if proc.ppid() == 1 and name in ['launchd', 'kernel_task']:
            return False, f"System critical process: {name}"

        return True, "Safe to kill"

    except psutil.NoSuchProcess:
        return False, "Process no longer exists"
    except psutil.AccessDenied:
        return False, "Access denied (may require sudo)"


def kill_process(pid: int, timeout: int = 5) -> tuple[bool, str, int]:
    """
    Kill process gracefully (SIGTERM → SIGKILL).

    Returns (success, message, memory_freed) tuple.
    """
    try:
        proc = psutil.Process(pid)
        memory_freed = proc.memory_info().rss
        name = proc.name()

        # Try SIGTERM first
        proc.terminate()

        # Wait for process to exit
        try:
            proc.wait(timeout=timeout)
            return True, f"Killed {name} (PID {pid}) with SIGTERM", memory_freed
        except psutil.TimeoutExpired:
            # Force kill with SIGKILL
            proc.kill()
            proc.wait(timeout=2)
            return True, f"Force killed {name} (PID {pid}) with SIGKILL", memory_freed

    except psutil.NoSuchProcess:
        return False, f"Process {pid} already terminated", 0
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid} (try sudo)", 0
    except Exception as e:
        return False, f"Error killing PID {pid}: {str(e)}", 0


def group_pids_by_category(pids: List[int]) -> Dict[str, List[Dict[str, Any]]]:
    """Group PIDs by process category."""
    grouped = {cat: [] for cat in PROCESS_CATEGORIES.keys()}

    for pid in pids:
        info = get_process_info(pid)
        if info:
            grouped[info['category']].append(info)

    # Remove empty categories
    return {k: v for k, v in grouped.items() if v}


@click.command()
@click.option('--pids', help='Comma-separated PIDs to kill')
@click.option('--stdin', is_flag=True, help='Read PIDs from stdin')
@click.option('--dry-run', is_flag=True, help='Show what would be killed (no actual termination)')
@click.option('--force', is_flag=True, help='Skip confirmation prompts')
@click.option('--timeout', default=5, help='Wait time before SIGKILL (seconds)')
@click.option('--format', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.option('--cpu-threshold', default=5.0, help='Skip if CPU > threshold (default: 5%)')
def main(pids: str, stdin: bool, dry_run: bool, force: bool, timeout: int, format: str, cpu_threshold: float):
    """
    Parallel Zombie Killer

    Safely terminates zombie processes identified by the 10-agent system.

    Examples:

        # Kill specific PIDs with confirmation
        uv run kill_zombies_parallel.py --pids "1234,5678,9101"

        # Dry run to see what would be killed
        uv run kill_zombies_parallel.py --pids "1234,5678" --dry-run

        # Read PIDs from stdin
        cat pids.txt | uv run kill_zombies_parallel.py --stdin

        # Force kill without confirmation
        uv run kill_zombies_parallel.py --pids "1234" --force
    """
    start_time = time.time()

    # Parse PIDs
    pid_list = []
    if pids:
        pid_list = [int(p.strip()) for p in pids.split(',') if p.strip()]
    elif stdin:
        pid_list = [int(line.strip()) for line in sys.stdin if line.strip().isdigit()]
    else:
        console.print("[red]Error: Must provide --pids or --stdin[/red]")
        sys.exit(1)

    if not pid_list:
        console.print("[yellow]No PIDs provided[/yellow]")
        sys.exit(0)

    # Load exclusions
    exclusions = load_exclusions()

    # Group PIDs by category
    grouped = group_pids_by_category(pid_list)

    # Verify all processes are safe to kill
    safe_pids = []
    unsafe_pids = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Verifying processes...", total=len(pid_list))

        for pid in pid_list:
            is_safe, reason = verify_safe_to_kill(pid, exclusions, cpu_threshold)

            if is_safe:
                safe_pids.append(pid)
            else:
                unsafe_pids.append({'pid': pid, 'reason': reason})

            progress.advance(task)

    # Show verification results
    if unsafe_pids:
        console.print("\n[yellow]Skipping unsafe processes:[/yellow]")
        unsafe_table = Table()
        unsafe_table.add_column("PID", style="cyan")
        unsafe_table.add_column("Reason", style="yellow")

        for item in unsafe_pids:
            unsafe_table.add_row(str(item['pid']), item['reason'])

        console.print(unsafe_table)

    if not safe_pids:
        console.print("\n[yellow]No safe processes to kill[/yellow]")
        sys.exit(0)

    # Show what will be killed
    console.print(f"\n[bold]Found {len(safe_pids)} processes to kill:[/bold]")

    for category, processes in grouped.items():
        if not processes:
            continue

        cat_pids = [p['pid'] for p in processes if p['pid'] in safe_pids]
        if not cat_pids:
            continue

        total_mem = sum(p['memory_mb'] for p in processes if p['pid'] in safe_pids)

        cat_table = Table(title=f"{category.replace('_', ' ').title()} ({len(cat_pids)} processes, {total_mem:.2f} MB)")
        cat_table.add_column("PID", style="cyan")
        cat_table.add_column("Process", style="yellow")
        cat_table.add_column("Memory (MB)", justify="right", style="red")
        cat_table.add_column("CPU %", justify="right", style="green")

        for proc in processes:
            if proc['pid'] in safe_pids:
                cat_table.add_row(
                    str(proc['pid']),
                    proc['name'],
                    str(proc['memory_mb']),
                    str(proc['cpu_percent'])
                )

        console.print(cat_table)

    # Confirmation
    if not force and not dry_run:
        if not Confirm.ask(f"\n[bold red]Kill {len(safe_pids)} processes?[/bold red]"):
            console.print("[yellow]Aborted[/yellow]")
            sys.exit(0)

    # Dry run exit
    if dry_run:
        console.print(f"\n[bold green]Dry run complete. Would kill {len(safe_pids)} processes.[/bold green]")
        sys.exit(0)

    # Kill processes
    killed_count = 0
    memory_freed = 0
    failed_pids = []
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("Killing processes...", total=len(safe_pids))

        for pid in safe_pids:
            success, message, mem_freed = kill_process(pid, timeout)

            if success:
                killed_count += 1
                memory_freed += mem_freed
                console.print(f"[green]✓[/green] {message}")
            else:
                failed_pids.append(pid)
                errors.append(message)
                console.print(f"[red]✗[/red] {message}")

            progress.advance(task)

    # Results
    execution_time = round((time.time() - start_time) * 1000, 2)

    if format == 'json':
        result = {
            'killed_count': killed_count,
            'failed_count': len(failed_pids),
            'memory_freed_bytes': memory_freed,
            'memory_freed_mb': round(memory_freed / (1024 * 1024), 2),
            'execution_time_ms': execution_time,
            'failed_pids': failed_pids,
            'errors': errors,
            'skipped_unsafe': len(unsafe_pids)
        }
        print(json.dumps(result, indent=2))
    else:
        console.print(f"\n[bold green]Successfully killed {killed_count} processes[/bold green]")
        console.print(f"[bold]Memory freed:[/bold] {round(memory_freed / (1024 * 1024), 2)} MB")
        console.print(f"[bold]Failed:[/bold] {len(failed_pids)}")
        console.print(f"[bold]Execution time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
