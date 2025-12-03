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
Orphaned Process Groups Hunter - Agent 12
Detects orphaned process groups with dead leaders consuming memory.

Detects:
- Process groups where leader (PGID==PID) is dead
- Orphaned child processes still running
- Zombie process groups consuming resources
- Memory leaks from abandoned process trees

Expected Recovery: 1-5 GB
CAUTION: High system impact - extensive validation required
"""

import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
import click
from rich.console import Console
from rich.table import Table

console = Console()

# Memory threshold: 200MB in bytes (process groups can be large)
MEMORY_THRESHOLD = 209_715_200
MIN_ORPHANED_CHILDREN = 2  # Minimum orphaned children to consider

# System process groups that should never be touched
SYSTEM_PGIDS = {0, 1}  # kernel and launchd

# Critical system processes that should never be killed
CRITICAL_SYSTEM_PROCESSES = {
    'kernel_task', 'launchd', 'WindowServer', 'loginwindow', 'Finder',
    'Dock', 'SystemUIServer', 'UserEventAgent', 'coreservicesd', 'coreaudiod',
    'cfprefsd', 'distnoted', 'hidd', 'notifyd', 'syslogd', 'securityd',
    'accountsd', 'apsd', 'bird', 'cloudd', 'com.apple.WebKit.WebContent'
}

# Protected process patterns
PROTECTED_PATTERNS = {
    'claude-code', 'cursor', 'code', 'vscode', 'postgres', 'redis',
    'meilisearch', 'ollama', 'docker', 'railway', 'ghostty'
}


def load_exclusions() -> Dict[str, Any]:
    """Load protection rules from config/exclusions.json."""
    config_path = Path(__file__).parent.parent / 'config' / 'exclusions.json'

    if not config_path.exists():
        console.print(f"[yellow]Warning: {config_path} not found, using strict defaults[/yellow]")
        return {
            'protected_processes': list(PROTECTED_PATTERNS),
            'protected_patterns': ['vscode', 'cursor', 'docker', 'postgresql', 'chrome', 'firefox']
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

    # Check critical system processes
    if proc_name in CRITICAL_SYSTEM_PROCESSES:
        return True

    # Check exact matches
    for protected in exclusions.get('protected_processes', []):
        if protected.lower() in proc_lower:
            return True

    # Check patterns
    for pattern in exclusions.get('protected_patterns', []):
        if pattern.lower() in proc_lower:
            return True

    # Check protected patterns
    for pattern in PROTECTED_PATTERNS:
        if pattern.lower() in proc_lower:
            return True

    return False


def get_process_groups() -> Dict[int, List[Dict[str, Any]]]:
    """
    Parse process information and group by PGID.
    Returns {pgid: [process_info_dicts]}.
    """
    process_groups = {}

    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'memory_info', 'create_time', 'status']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            ppid = proc.info['ppid']
            mem_info = proc.info.get('memory_info')

            if mem_info is None:
                continue

            # Get process group ID
            try:
                # On macOS, use psutil's gids() to get process group
                p = psutil.Process(pid)
                # psutil doesn't have direct PGID access on macOS, use subprocess
                result = subprocess.run(
                    ['ps', '-o', 'pgid=', '-p', str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                pgid = int(result.stdout.strip()) if result.stdout.strip() else pid
            except:
                # Fallback: assume PID is PGID for group leaders
                pgid = pid

            process_info = {
                'pid': pid,
                'pgid': pgid,
                'ppid': ppid,
                'name': name,
                'memory_bytes': mem_info.rss,
                'memory_mb': round(mem_info.rss / (1024 * 1024), 2),
                'create_time': proc.info['create_time'],
                'status': proc.info.get('status', 'unknown'),
                'is_group_leader': (pid == pgid)
            }

            if pgid not in process_groups:
                process_groups[pgid] = []
            process_groups[pgid].append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            # Silently skip problematic processes
            continue

    return process_groups


def is_group_leader_dead(pgid: int, process_groups: Dict[int, List[Dict[str, Any]]]) -> bool:
    """
    Check if process group leader is dead.
    Leader is dead if PGID exists but no process has PID==PGID.
    """
    if pgid not in process_groups:
        return True

    # Check if any process in the group is the leader (PID == PGID)
    for proc_info in process_groups[pgid]:
        if proc_info['pid'] == pgid:
            # Leader exists, check if it's a zombie
            if proc_info['status'] == 'zombie':
                return True
            return False

    # No leader found in group
    return True


def find_orphaned_children(pgid: int, process_groups: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Find orphaned child processes in a process group.
    Returns list of process info dicts for orphaned children.
    """
    if pgid not in process_groups:
        return []

    orphaned = []
    for proc_info in process_groups[pgid]:
        # Skip the leader itself
        if proc_info['is_group_leader']:
            continue

        # Check if parent is dead
        ppid = proc_info['ppid']
        try:
            parent = psutil.Process(ppid)
            # Parent exists, not orphaned
            continue
        except psutil.NoSuchProcess:
            # Parent is dead, this is orphaned
            orphaned.append(proc_info)

    return orphaned


def is_process_group_safe_to_kill(
    pgid: int,
    process_groups: Dict[int, List[Dict[str, Any]]],
    exclusions: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Extensive safety validation before killing process group.
    Returns (is_safe, reason).
    """
    # Never kill system PGIDs
    if pgid in SYSTEM_PGIDS:
        return False, "System PGID (kernel/launchd)"

    # Check if group exists
    if pgid not in process_groups:
        return False, "Process group does not exist"

    # Get all processes in group
    group_processes = process_groups[pgid]

    # Check each process for protection
    for proc_info in group_processes:
        if is_protected(proc_info['name'], exclusions):
            return False, f"Contains protected process: {proc_info['name']}"

    # Check if any process is a parent of other processes outside the group
    group_pids = {p['pid'] for p in group_processes}
    for proc in psutil.process_iter(['pid', 'ppid']):
        try:
            if proc.info['ppid'] in group_pids and proc.info['pid'] not in group_pids:
                return False, "Process group has children outside group"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return True, "Safe to kill"


def find_zombie_process_groups(exclusions: Dict[str, Any]) -> Dict[str, Any]:
    """Main detection function - find orphaned process groups."""
    zombies = []
    validation_failures = []

    # Get all process groups
    process_groups = get_process_groups()

    # Analyze each process group
    for pgid, processes in process_groups.items():
        # Skip system PGIDs
        if pgid in SYSTEM_PGIDS:
            continue

        # Check if leader is dead
        if not is_group_leader_dead(pgid, process_groups):
            continue

        # Find orphaned children
        orphaned_children = find_orphaned_children(pgid, process_groups)

        # Skip if not enough orphaned children
        if len(orphaned_children) < MIN_ORPHANED_CHILDREN:
            continue

        # Calculate total memory for group
        total_memory = sum(p['memory_bytes'] for p in orphaned_children)

        # Skip if below memory threshold
        if total_memory < MEMORY_THRESHOLD:
            continue

        # Safety validation
        is_safe, reason = is_process_group_safe_to_kill(pgid, process_groups, exclusions)

        if is_safe:
            zombies.append({
                'pgid': pgid,
                'type': 'orphaned_process_group',
                'orphaned_children_count': len(orphaned_children),
                'total_memory_bytes': total_memory,
                'total_memory_mb': round(total_memory / (1024 * 1024), 2),
                'processes': [
                    {
                        'pid': p['pid'],
                        'name': p['name'],
                        'ppid': p['ppid'],
                        'memory_mb': p['memory_mb'],
                        'status': p['status']
                    }
                    for p in orphaned_children
                ],
                'pids': [p['pid'] for p in orphaned_children]
            })
        else:
            validation_failures.append({
                'pgid': pgid,
                'reason': reason,
                'orphaned_count': len(orphaned_children),
                'memory_mb': round(total_memory / (1024 * 1024), 2)
            })

    return {
        'zombies': zombies,
        'validation_failures': validation_failures,
        'total_groups_analyzed': len(process_groups)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show validation failures and detailed info')
@click.option('--min-children', type=int, default=MIN_ORPHANED_CHILDREN, help='Minimum orphaned children')
def main(format: str, verbose: bool, min_children: int):
    """
    Orphaned Process Groups Hunter - Agent 12

    ⚠️  CAUTION: High system impact - extensive validation required

    Detects orphaned process groups with dead leaders.
    Expected recovery: 1-5 GB
    """
    start_time = time.time()

    # Override minimum children if specified
    global MIN_ORPHANED_CHILDREN
    MIN_ORPHANED_CHILDREN = min_children

    # Load exclusions
    exclusions = load_exclusions()

    # Detect zombies
    result = find_zombie_process_groups(exclusions)
    zombies = result['zombies']
    validation_failures = result['validation_failures']
    total_groups = result['total_groups_analyzed']

    # Calculate totals
    total_memory = sum(z['total_memory_bytes'] for z in zombies)
    total_orphaned_processes = sum(z['orphaned_children_count'] for z in zombies)
    execution_time = round((time.time() - start_time) * 1000, 2)

    # Output results
    if format == 'json':
        output = {
            'agent': 'orphaned_process_groups',
            'agent_number': 12,
            'zombie_groups_found': len(zombies),
            'total_orphaned_processes': total_orphaned_processes,
            'total_memory_bytes': total_memory,
            'total_memory_mb': round(total_memory / (1024 * 1024), 2),
            'execution_time_ms': execution_time,
            'process_groups': zombies,
            'all_pids': [pid for z in zombies for pid in z['pids']],
            'metrics': {
                'total_groups_analyzed': total_groups,
                'validation_failures': len(validation_failures),
                'min_children_threshold': min_children
            }
        }

        if verbose:
            output['validation_failures'] = validation_failures

        print(json.dumps(output, indent=2))

    elif format == 'summary':
        console.print(f"\n[bold cyan]Agent 12: Orphaned Process Groups[/bold cyan]")
        console.print(f"⚠️  [bold yellow]High system impact - use with caution[/bold yellow]")
        console.print(f"Zombie groups found: [bold red]{len(zombies)}[/bold red]")
        console.print(f"Orphaned processes: [bold red]{total_orphaned_processes}[/bold red]")
        console.print(f"Total memory: [bold red]{round(total_memory / (1024 * 1024), 2)} MB[/bold red]")
        console.print(f"Groups analyzed: [dim]{total_groups}[/dim]")
        console.print(f"Validation failures: [yellow]{len(validation_failures)}[/yellow]")

        if verbose and validation_failures:
            console.print(f"\n[bold yellow]Validation Failures:[/bold yellow]")
            for failure in validation_failures[:5]:  # Show first 5
                console.print(f"  - PGID {failure['pgid']}: {failure['reason']} ({failure['memory_mb']} MB)")

    else:  # table format
        table = Table(title=f"Agent 12: Orphaned Process Groups ({len(zombies)} found)")
        table.add_column("PGID", style="cyan")
        table.add_column("Orphaned", justify="right", style="yellow")
        table.add_column("Memory (MB)", justify="right", style="red")
        table.add_column("Process Names", style="dim")

        for z in zombies:
            # Get unique process names
            proc_names = list(set(p['name'] for p in z['processes']))
            names_str = ', '.join(proc_names[:3])
            if len(proc_names) > 3:
                names_str += f" +{len(proc_names) - 3} more"

            table.add_row(
                str(z['pgid']),
                str(z['orphaned_children_count']),
                str(z['total_memory_mb']),
                names_str
            )

        console.print(table)
        console.print(f"\n[bold]Total Memory:[/bold] {round(total_memory / (1024 * 1024), 2)} MB")
        console.print(f"[bold]Orphaned Processes:[/bold] {total_orphaned_processes}")
        console.print(f"[bold]Groups Analyzed:[/bold] {total_groups}")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")

        if verbose and validation_failures:
            console.print(f"\n[bold yellow]Validation Failures ({len(validation_failures)}):[/bold yellow]")
            for failure in validation_failures[:5]:
                console.print(f"  ⚠️  PGID {failure['pgid']}: {failure['reason']}")


if __name__ == '__main__':
    main()
