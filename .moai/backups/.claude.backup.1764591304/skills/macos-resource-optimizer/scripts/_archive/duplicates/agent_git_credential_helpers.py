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
Git Credential Helper Hunter - Agent 7
Detects idle git-credential-cache--daemon and orphaned GitHub CLI helper processes.

Detection Rules:
- Pattern: `git-credential-cache--daemon` or `git-credential-osxkeychain`
- Criteria: Idle credential helpers with expired sockets (>15min inactive)
- Pattern: `gh auth` helper processes orphaned from parent
- Memory: Usually 10-15 MB per daemon, but many stale = 500 MB total

Protection:
- Check socket activity timestamp (~/.git-credential-cache/socket)
- Never kill if Git operations in last 5 minutes
- Check if parent process (git/gh) still running
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

# Configuration
IDLE_THRESHOLD_MINUTES = 15  # Flag if idle >15 minutes
GIT_ACTIVITY_GRACE_MINUTES = 5  # Don't kill if git used recently
MEMORY_PER_DAEMON_MB = 12  # Typical memory per credential daemon

# Protected processes
PROTECTED_PROCESSES = {
    "claude-flow",
    "claude",
    "ghostty",
    "Terminal",
    "iTerm",
    "Warp",
    "git"
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


def check_git_recent_activity() -> bool:
    """Check if any git operations happened recently."""
    try:
        threshold = time.time() - (GIT_ACTIVITY_GRACE_MINUTES * 60)

        # Check for running git processes
        for proc in psutil.process_iter(['name', 'create_time']):
            if proc.info['name'] == 'git':
                return True

        # Check common git directories for recent activity
        git_dirs = [
            Path.home() / ".git-credential-cache",
            Path.home() / ".gitconfig",
            Path("/tmp").glob("git-*")
        ]

        for location in git_dirs:
            if isinstance(location, Path):
                if location.exists() and location.stat().st_mtime > threshold:
                    return True
            else:
                # Handle glob
                for path in location:
                    if path.stat().st_mtime > threshold:
                        return True

    except (OSError, PermissionError):
        pass
    return False


def check_credential_socket_activity() -> float:
    """Check last activity time of git credential cache socket."""
    try:
        socket_path = Path.home() / ".git-credential-cache" / "socket"
        if socket_path.exists():
            return socket_path.stat().st_mtime
    except (OSError, PermissionError):
        pass
    return 0


def find_git_credential_daemons() -> List[psutil.Process]:
    """Find git-credential-cache--daemon processes."""
    daemons = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info.get('cmdline') or [])
            if ('git-credential-cache--daemon' in cmdline or
                'git-credential-osxkeychain' in cmdline or
                proc.info['name'] == 'git-credential-cache--daemon'):
                daemons.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return daemons


def find_gh_auth_helpers() -> List[psutil.Process]:
    """Find orphaned GitHub CLI authentication helpers."""
    helpers = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
        try:
            cmdline = ' '.join(proc.info.get('cmdline') or [])
            if 'gh auth' in cmdline or 'gh-auth-helper' in cmdline:
                # Check if parent is still running
                ppid = proc.info.get('ppid')
                if ppid:
                    try:
                        parent = psutil.Process(ppid)
                        if not parent.is_running():
                            helpers.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        helpers.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return helpers


def detect_git_credential_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Detect idle git credential helpers and orphaned auth processes."""
    start_time = time.time()
    zombies = []

    if verbose:
        console.print("[cyan]Scanning for git credential zombie processes...[/cyan]")

    # Check for recent git activity
    git_active = check_git_recent_activity()
    if git_active and verbose:
        console.print("[yellow]Recent git activity detected - applying protection[/yellow]")

    # Check socket activity
    socket_last_activity = check_credential_socket_activity()
    current_time = time.time()

    if socket_last_activity > 0:
        socket_idle_minutes = (current_time - socket_last_activity) / 60
        if verbose:
            console.print(f"Credential socket idle: {socket_idle_minutes:.1f} minutes")
    else:
        socket_idle_minutes = float('inf')

    # Find git-credential daemons
    credential_daemons = find_git_credential_daemons()
    if verbose:
        console.print(f"\nFound {len(credential_daemons)} credential daemon(s)")

    for proc in credential_daemons:
        try:
            info = proc.as_dict(['pid', 'name', 'cmdline', 'cpu_percent',
                                'memory_info', 'create_time'])

            runtime_hours = (current_time - info['create_time']) / 3600
            memory_mb = info['memory_info'].rss / (1024 * 1024)
            cmdline_str = ' '.join(info.get('cmdline') or [])

            # Don't kill if git recently active
            if git_active:
                if verbose:
                    console.print(f"  PID {info['pid']}: [green]PROTECTED[/green] - Recent git activity")
                continue

            # Check if socket is stale
            if socket_idle_minutes > IDLE_THRESHOLD_MINUTES:
                zombies.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'cmdline': cmdline_str[:200],
                    'cpu_percent': info['cpu_percent'] or 0,
                    'memory_bytes': info['memory_info'].rss,
                    'runtime_hours': runtime_hours,
                    'reason': f'Credential socket idle {socket_idle_minutes:.1f}min (>{IDLE_THRESHOLD_MINUTES}min)',
                    'type': 'git-credential-daemon'
                })

                if verbose:
                    console.print(f"  PID {info['pid']}: [red]ZOMBIE[/red] - "
                                f"Socket idle {socket_idle_minutes:.1f}min, "
                                f"MEM: {memory_mb:.1f}MB")

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    # Find orphaned gh auth helpers
    gh_helpers = find_gh_auth_helpers()
    if verbose:
        console.print(f"\nFound {len(gh_helpers)} orphaned gh auth helper(s)")

    for proc in gh_helpers:
        try:
            info = proc.as_dict(['pid', 'name', 'cmdline', 'cpu_percent',
                                'memory_info', 'create_time'])

            runtime_hours = (current_time - info['create_time']) / 3600
            memory_mb = info['memory_info'].rss / (1024 * 1024)
            cmdline_str = ' '.join(info.get('cmdline') or [])

            zombies.append({
                'pid': info['pid'],
                'name': info['name'],
                'cmdline': cmdline_str[:200],
                'cpu_percent': info['cpu_percent'] or 0,
                'memory_bytes': info['memory_info'].rss,
                'runtime_hours': runtime_hours,
                'reason': 'Orphaned gh auth helper (parent terminated)',
                'type': 'gh-auth-helper'
            })

            if verbose:
                console.print(f"  PID {info['pid']}: [red]ZOMBIE[/red] - "
                            f"Orphaned, MEM: {memory_mb:.1f}MB, "
                            f"Runtime: {runtime_hours:.1f}h")

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    execution_time = (time.time() - start_time) * 1000
    total_memory = sum(z['memory_bytes'] for z in zombies)

    return {
        'zombies_found': len(zombies),
        'total_memory_bytes': total_memory,
        'pids': [z['pid'] for z in zombies],
        'processes': zombies,
        'execution_time_ms': round(execution_time, 2),
        'git_recently_active': git_active,
        'socket_idle_minutes': socket_idle_minutes if socket_idle_minutes != float('inf') else None
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="Git Credential Zombie Processes")
    table.add_column("PID", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Runtime", justify="right")
    table.add_column("Reason", style="red")

    for proc in result['processes']:
        table.add_row(
            str(proc['pid']),
            proc.get('type', 'unknown'),
            f"{proc['cpu_percent']:.1f}%",
            format_memory(proc['memory_bytes']),
            f"{proc['runtime_hours']:.1f}h",
            proc['reason']
        )

    console.print(table)


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]Git Credential Zombie Analysis[/bold]")
    console.print(f"Zombies found: {result['zombies_found']}")
    console.print(f"Total memory: {format_memory(result['total_memory_bytes'])}")
    console.print(f"Execution time: {result['execution_time_ms']:.2f}ms")

    if result.get('git_recently_active'):
        console.print(f"[yellow]Git recently active: Protected processes[/yellow]")

    if result.get('socket_idle_minutes') is not None:
        console.print(f"Socket idle: {result['socket_idle_minutes']:.1f} minutes")

    if result['zombies_found'] > 0:
        console.print(f"\nPIDs to kill: {', '.join(map(str, result['pids']))}")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Detect idle git credential helpers and orphaned auth processes."""
    result = detect_git_credential_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
