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
Cloudflare Workers Hunter - Agent 6
Detects idle workerd processes from Cloudflare Workers development.

Detection Rules:
- Pattern: `/workerd serve` from node_modules/@cloudflare/workerd-darwin-arm64
- Criteria: Multiple instances (5+) from same project path
- Runtime threshold: 2+ hours idle
- CPU threshold: <1%
- Memory: Usually 20-25 MB per instance, but 30+ instances = 500-600 MB total

Protection:
- Check if parent node process is running
- Check if project directory still has active development
- Never kill if parent process is active
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

# Configuration
MIN_INSTANCES_THRESHOLD = 5  # Flag as zombie if 5+ instances from same project
RUNTIME_THRESHOLD_HOURS = 2
CPU_THRESHOLD_PERCENT = 1.0
MEMORY_PER_INSTANCE_MB = 20  # Typical memory per workerd instance

# Protected processes
PROTECTED_PROCESSES = {
    "claude-flow",
    "claude",
    "ghostty",
    "Terminal",
    "iTerm",
    "Warp"
}


def format_memory(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def is_protected_parent(proc: psutil.Process) -> bool:
    """Check if process has a protected parent."""
    try:
        parent = proc.parent()
        if parent and parent.name() in PROTECTED_PROCESSES:
            return True
        # Check grandparent
        if parent:
            grandparent = parent.parent()
            if grandparent and grandparent.name() in PROTECTED_PROCESSES:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


def is_project_active(project_path: str) -> bool:
    """Check if project directory has recent activity."""
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            return False

        # Check for recent file modifications (last 10 minutes)
        threshold = time.time() - 600  # 10 minutes
        for file in project_dir.rglob('*'):
            if file.is_file() and file.stat().st_mtime > threshold:
                return True
    except (OSError, PermissionError):
        pass
    return False


def get_project_path(cmdline: List[str]) -> str:
    """Extract project path from workerd command line."""
    try:
        # Look for the path before node_modules
        for i, arg in enumerate(cmdline):
            if 'node_modules/@cloudflare/workerd' in arg:
                # Project path is usually in earlier arguments or cwd
                for prev_arg in reversed(cmdline[:i]):
                    if '/' in prev_arg and not prev_arg.startswith('-'):
                        return str(Path(prev_arg).parent)
        return ""
    except Exception:
        return ""


def detect_workerd_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Detect idle workerd processes from Cloudflare Workers development."""
    start_time = time.time()
    zombies = []
    workerd_by_project = {}  # Group by project path

    if verbose:
        console.print("[cyan]Scanning for workerd zombie processes...[/cyan]")

    current_time = time.time()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent',
                                     'memory_info', 'create_time', 'ppid']):
        try:
            info = proc.info
            cmdline = info.get('cmdline') or []
            cmdline_str = ' '.join(cmdline)

            # Match workerd processes
            if (info['name'] == 'workerd' or
                'workerd serve' in cmdline_str or
                '@cloudflare/workerd' in cmdline_str):

                # Get runtime
                runtime_hours = (current_time - info['create_time']) / 3600

                # Get CPU usage
                cpu_percent = info['cpu_percent'] or 0

                # Get memory
                mem_info = info.get('memory_info')
                memory_mb = mem_info.rss / (1024 * 1024) if mem_info else 0

                # Extract project path
                project_path = get_project_path(cmdline)

                # Group by project
                if project_path not in workerd_by_project:
                    workerd_by_project[project_path] = []

                workerd_by_project[project_path].append({
                    'pid': info['pid'],
                    'ppid': info.get('ppid'),
                    'cmdline': cmdline_str[:200],
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'runtime_hours': runtime_hours,
                    'project_path': project_path
                })

                if verbose:
                    console.print(f"  Found workerd: PID {info['pid']}, "
                                f"CPU: {cpu_percent:.1f}%, "
                                f"MEM: {memory_mb:.1f}MB, "
                                f"Runtime: {runtime_hours:.1f}h")

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    # Analyze grouped processes
    for project_path, processes in workerd_by_project.items():
        num_instances = len(processes)

        if verbose:
            console.print(f"\n[yellow]Project: {project_path or 'unknown'}[/yellow]")
            console.print(f"  Instances: {num_instances}")

        # Check if this is a zombie cluster
        if num_instances >= MIN_INSTANCES_THRESHOLD:
            # Check if all instances are idle
            all_idle = all(
                p['cpu_percent'] < CPU_THRESHOLD_PERCENT and
                p['runtime_hours'] > RUNTIME_THRESHOLD_HOURS
                for p in processes
            )

            if all_idle:
                # Check if project is still active
                project_active = is_project_active(project_path) if project_path else False

                # Check if parent processes are running
                parent_running = False
                for p in processes:
                    try:
                        if p['ppid']:
                            parent = psutil.Process(p['ppid'])
                            if parent.is_running():
                                parent_running = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if not project_active and not parent_running:
                    # Mark entire cluster as zombies
                    for p in processes:
                        zombies.append({
                            'pid': p['pid'],
                            'name': 'workerd',
                            'cmdline': p['cmdline'],
                            'cpu_percent': p['cpu_percent'],
                            'memory_bytes': int(p['memory_mb'] * 1024 * 1024),
                            'runtime_hours': p['runtime_hours'],
                            'reason': f'Idle cluster ({num_instances} instances) from inactive project',
                            'project_path': project_path or 'unknown'
                        })

                    if verbose:
                        console.print(f"  [red]ZOMBIE CLUSTER DETECTED[/red]: "
                                    f"{num_instances} idle instances")
                elif verbose:
                    if project_active:
                        console.print(f"  [green]PROTECTED[/green]: Project still active")
                    if parent_running:
                        console.print(f"  [green]PROTECTED[/green]: Parent process running")

    execution_time = (time.time() - start_time) * 1000
    total_memory = sum(z['memory_bytes'] for z in zombies)

    return {
        'zombies_found': len(zombies),
        'total_memory_bytes': total_memory,
        'pids': [z['pid'] for z in zombies],
        'processes': zombies,
        'execution_time_ms': round(execution_time, 2)
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="Workerd Zombie Processes")
    table.add_column("PID", style="cyan")
    table.add_column("Project Path", style="yellow")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Runtime", justify="right")
    table.add_column("Reason", style="red")

    for proc in result['processes']:
        table.add_row(
            str(proc['pid']),
            proc.get('project_path', 'unknown')[:50],
            f"{proc['cpu_percent']:.1f}%",
            format_memory(proc['memory_bytes']),
            f"{proc['runtime_hours']:.1f}h",
            proc['reason']
        )

    console.print(table)


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]Workerd Zombie Analysis[/bold]")
    console.print(f"Zombies found: {result['zombies_found']}")
    console.print(f"Total memory: {format_memory(result['total_memory_bytes'])}")
    console.print(f"Execution time: {result['execution_time_ms']:.2f}ms")

    if result['zombies_found'] > 0:
        console.print(f"\nPIDs to kill: {', '.join(map(str, result['pids']))}")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Detect idle workerd processes from Cloudflare Workers development."""
    result = detect_workerd_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
