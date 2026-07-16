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
Browser Helper Hunter - Agent 7
Detects idle browser renderer processes from Arc, Chrome, Safari.

Detection Rules:
- Pattern: `Browser Helper (Renderer)`, `Electron Helper (Renderer)`
- Criteria: >500MB memory, <1% CPU, running >2 hours
- Types: Arc (Dia.app), Chrome, Safari

Protection:
- Check if main browser process (Arc, Chrome) is running
- Don't kill helpers for active tabs (check parent process connections)
- Protected: Any helper with active network connections or file descriptors >50
"""

import json
import time
from typing import Dict, List, Any

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

# Configuration
MEMORY_THRESHOLD_MB = 500
CPU_THRESHOLD_PERCENT = 1.0
RUNTIME_THRESHOLD_HOURS = 2
ACTIVE_FD_THRESHOLD = 50  # File descriptors indicating active tab

# Browser process mappings
BROWSER_HELPERS = {
    'Google Chrome Helper (Renderer)': 'Google Chrome',
    'Chromium Helper (Renderer)': 'Chromium',
    'Dia Helper (Renderer)': 'Dia',  # Arc browser
    'Arc Helper (Renderer)': 'Arc',
    'Electron Helper (Renderer)': 'Electron',
    'Safari Web Content': 'Safari',
    'WebKit Web Content': 'Safari'
}

# Protected browser processes
ACTIVE_BROWSERS = {
    'Google Chrome',
    'Chromium',
    'Arc',
    'Dia',
    'Safari',
    'Firefox'
}


def format_memory(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def is_browser_running(browser_name: str) -> bool:
    """Check if the main browser process is running."""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == browser_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def has_active_network_connections(proc: psutil.Process) -> bool:
    """Check if process has active network connections."""
    try:
        connections = proc.connections(kind='inet')
        # Consider ESTABLISHED connections as active
        active_connections = [
            conn for conn in connections
            if conn.status == 'ESTABLISHED'
        ]
        return len(active_connections) > 0
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def count_file_descriptors(proc: psutil.Process) -> int:
    """Count open file descriptors for a process."""
    try:
        return proc.num_fds() if hasattr(proc, 'num_fds') else 0
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def is_protected_helper(proc: psutil.Process, proc_name: str) -> bool:
    """Check if browser helper should be protected."""
    try:
        # Check if main browser is running
        browser_name = None
        for helper_pattern, browser in BROWSER_HELPERS.items():
            if helper_pattern in proc_name:
                browser_name = browser
                break

        if browser_name and not is_browser_running(browser_name):
            # Main browser not running, helper can be killed
            return False

        # Check for active network connections
        if has_active_network_connections(proc):
            return True

        # Check for high file descriptor count (active tab indicator)
        fd_count = count_file_descriptors(proc)
        if fd_count > ACTIVE_FD_THRESHOLD:
            return True

        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True  # Protect if we can't determine


def is_browser_helper(proc_name: str) -> bool:
    """Check if process is a browser helper."""
    return any(pattern in proc_name for pattern in BROWSER_HELPERS.keys())


def detect_browser_helper_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Detect idle browser renderer processes."""
    start_time = time.time()
    zombies = []

    if verbose:
        console.print("[cyan]Scanning for browser helper zombie processes...[/cyan]")

    current_time = time.time()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent',
                                     'memory_info', 'create_time']):
        try:
            info = proc.info
            proc_name = info['name'] or ''

            # Check if this is a browser helper
            if not is_browser_helper(proc_name):
                continue

            # Get metrics
            mem_info = info.get('memory_info')
            memory_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
            cpu_percent = info['cpu_percent'] or 0
            runtime_hours = (current_time - info['create_time']) / 3600

            if verbose:
                console.print(f"  Found {proc_name}: PID {info['pid']}, "
                            f"CPU: {cpu_percent:.1f}%, "
                            f"MEM: {memory_mb:.1f}MB, "
                            f"Runtime: {runtime_hours:.1f}h")

            # Check zombie criteria
            is_zombie = (
                memory_mb > MEMORY_THRESHOLD_MB and
                cpu_percent < CPU_THRESHOLD_PERCENT and
                runtime_hours > RUNTIME_THRESHOLD_HOURS
            )

            if is_zombie:
                # Check if protected
                if is_protected_helper(proc, proc_name):
                    if verbose:
                        console.print(f"    [green]PROTECTED[/green]: Active connections or high FD count")
                    continue

                # Determine browser type
                browser_type = 'Unknown'
                for helper_pattern, browser in BROWSER_HELPERS.items():
                    if helper_pattern in proc_name:
                        browser_type = browser
                        break

                cmdline = info.get('cmdline') or []
                cmdline_str = ' '.join(cmdline)[:200]

                zombies.append({
                    'pid': info['pid'],
                    'name': proc_name,
                    'browser_type': browser_type,
                    'cmdline': cmdline_str,
                    'cpu_percent': cpu_percent,
                    'memory_bytes': int(memory_mb * 1024 * 1024),
                    'runtime_hours': runtime_hours,
                    'reason': f'Idle {browser_type} renderer (>{MEMORY_THRESHOLD_MB}MB, <{CPU_THRESHOLD_PERCENT}% CPU, >{RUNTIME_THRESHOLD_HOURS}h)',
                    'fd_count': count_file_descriptors(proc)
                })

                if verbose:
                    console.print(f"    [red]ZOMBIE DETECTED[/red]: {zombies[-1]['reason']}")

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

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
    table = Table(title="Browser Helper Zombie Processes")
    table.add_column("PID", style="cyan")
    table.add_column("Browser", style="yellow")
    table.add_column("Helper Name", style="white")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Runtime", justify="right")
    table.add_column("FDs", justify="right")
    table.add_column("Reason", style="red")

    for proc in result['processes']:
        table.add_row(
            str(proc['pid']),
            proc['browser_type'],
            proc['name'][:30],
            f"{proc['cpu_percent']:.1f}%",
            format_memory(proc['memory_bytes']),
            f"{proc['runtime_hours']:.1f}h",
            str(proc.get('fd_count', 0)),
            proc['reason'][:50]
        )

    console.print(table)


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]Browser Helper Zombie Analysis[/bold]")
    console.print(f"Zombies found: {result['zombies_found']}")
    console.print(f"Total memory: {format_memory(result['total_memory_bytes'])}")
    console.print(f"Execution time: {result['execution_time_ms']:.2f}ms")

    if result['zombies_found'] > 0:
        # Group by browser type
        by_browser = {}
        for proc in result['processes']:
            browser = proc['browser_type']
            if browser not in by_browser:
                by_browser[browser] = []
            by_browser[browser].append(proc)

        console.print("\n[bold]By Browser:[/bold]")
        for browser, procs in sorted(by_browser.items()):
            total_mem = sum(p['memory_bytes'] for p in procs)
            console.print(f"  {browser}: {len(procs)} helpers, {format_memory(total_mem)}")

        console.print(f"\nPIDs to kill: {', '.join(map(str, result['pids']))}")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Detect idle browser renderer processes from Arc, Chrome, Safari."""
    result = detect_browser_helper_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
