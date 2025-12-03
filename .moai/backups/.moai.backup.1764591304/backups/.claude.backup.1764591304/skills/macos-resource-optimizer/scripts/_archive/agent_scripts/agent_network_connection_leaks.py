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
Network Connection Leaks Hunter - Agent 11
Detects zombie network connections and leaked sockets.

Detects:
- CLOSE_WAIT connections (server didn't close properly)
- Orphaned WebSocket processes (disconnected but still running)
- TIME_WAIT accumulation (warns when >1000 sockets)
- Zombie network connections consuming memory

Expected Recovery: 1-2 GB
"""

import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
import click
from rich.console import Console
from rich.table import Table

console = Console()

# Memory threshold: 100MB in bytes (network processes are usually smaller)
MEMORY_THRESHOLD = 104_857_600
TIME_WAIT_WARNING_THRESHOLD = 1000
CLOSE_WAIT_THRESHOLD = 10  # More than 10 CLOSE_WAIT is suspicious

# System processes that should never be killed
SYSTEM_PROCESSES = {
    'kernel_task', 'launchd', 'WindowServer', 'loginwindow', 'Finder',
    'Dock', 'SystemUIServer', 'mDNSResponder', 'networkserviceproxy',
    'nsurlsessiond', 'netbiosd', 'rapportd', 'sharingd'
}

# Processes that legitimately hold network connections
LEGITIMATE_NETWORK_PROCESSES = {
    'claude-code', 'cursor', 'code', 'firefox', 'chrome', 'safari',
    'slack', 'discord', 'zoom', 'teams', 'postgres', 'redis',
    'meilisearch', 'ollama', 'docker', 'Railway'
}


def load_exclusions() -> Dict[str, Any]:
    """Load protection rules from config/exclusions.json."""
    config_path = Path(__file__).parent.parent / 'config' / 'exclusions.json'

    if not config_path.exists():
        console.print(f"[yellow]Warning: {config_path} not found, using minimal defaults[/yellow]")
        return {
            'protected_processes': list(LEGITIMATE_NETWORK_PROCESSES),
            'protected_patterns': ['vscode', 'cursor', 'docker', 'postgresql']
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

    # System processes
    if proc_name in SYSTEM_PROCESSES:
        return True

    # Legitimate network processes
    if proc_name in LEGITIMATE_NETWORK_PROCESSES:
        return True

    return False


def get_close_wait_connections() -> List[Tuple[str, int, str, str]]:
    """
    Parse netstat to find CLOSE_WAIT connections.
    Returns list of (local_addr, pid, foreign_addr, state).
    """
    close_wait = []

    try:
        result = subprocess.run(
            ['netstat', '-an', '-p', 'tcp'],
            capture_output=True,
            text=True,
            timeout=5
        )

        for line in result.stdout.split('\n'):
            if 'CLOSE_WAIT' in line:
                parts = line.split()
                if len(parts) >= 6:
                    local_addr = parts[3]
                    foreign_addr = parts[4]
                    state = parts[5]
                    # Try to extract PID (format varies)
                    pid = 0
                    for part in parts:
                        if part.isdigit():
                            pid = int(part)
                            break

                    close_wait.append((local_addr, pid, foreign_addr, state))

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        console.print(f"[yellow]Warning: netstat failed: {e}[/yellow]")

    return close_wait


def count_time_wait_sockets() -> int:
    """
    Count TIME_WAIT sockets.
    Returns count of TIME_WAIT connections.
    """
    time_wait_count = 0

    try:
        result = subprocess.run(
            ['netstat', '-an', '-p', 'tcp'],
            capture_output=True,
            text=True,
            timeout=5
        )

        for line in result.stdout.split('\n'):
            if 'TIME_WAIT' in line:
                time_wait_count += 1

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        console.print(f"[yellow]Warning: netstat failed: {e}[/yellow]")

    return time_wait_count


def find_websocket_zombies(exclusions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find orphaned WebSocket processes (disconnected but still running).
    Looks for processes with 'websocket', 'ws://', 'wss://' in command line.
    """
    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            cmdline = proc.info.get('cmdline', [])
            mem_info = proc.info.get('memory_info')

            if mem_info is None or cmdline is None:
                continue

            # Check if protected
            if is_protected(name, exclusions):
                continue

            # Check for WebSocket indicators in command line
            cmdline_str = ' '.join(cmdline).lower()
            if any(ws in cmdline_str for ws in ['websocket', 'ws://', 'wss://']):
                # Check if has no active connections (get separately)
                try:
                    p = psutil.Process(pid)
                    connections = p.connections()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    connections = []

                if not connections or len(connections) == 0:
                    memory_bytes = mem_info.rss

                    zombies.append({
                        'pid': pid,
                        'name': name,
                        'type': 'websocket_zombie',
                        'memory_mb': round(memory_bytes / (1024 * 1024), 2),
                        'memory_bytes': memory_bytes,
                        'cmdline': cmdline_str[:100],  # Truncate for readability
                        'connection_count': 0
                    })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return zombies


def get_process_connections_by_pid(pid: int) -> int:
    """Count active connections for a PID."""
    try:
        proc = psutil.Process(pid)
        return len(proc.connections())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def has_active_connections_to_endpoint(endpoint: str) -> bool:
    """
    Check if any process has active connections to this endpoint.
    Safety check: don't kill if other processes still using same endpoint.
    """
    try:
        for proc in psutil.process_iter(['pid']):
            try:
                p = psutil.Process(proc.info['pid'])
                connections = p.connections()
                for conn in connections:
                    if hasattr(conn, 'raddr') and conn.raddr:
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}"
                        if endpoint in remote_addr:
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except:
        pass

    return False


def find_zombie_network_connections(exclusions: Dict[str, Any]) -> Dict[str, Any]:
    """Main detection function - find all types of network zombies."""
    zombies = []
    warnings = []

    # 1. Find CLOSE_WAIT connections
    close_wait_conns = get_close_wait_connections()
    if len(close_wait_conns) > CLOSE_WAIT_THRESHOLD:
        warnings.append({
            'type': 'close_wait_excessive',
            'count': len(close_wait_conns),
            'threshold': CLOSE_WAIT_THRESHOLD,
            'message': f"Found {len(close_wait_conns)} CLOSE_WAIT connections (threshold: {CLOSE_WAIT_THRESHOLD})"
        })

        # Group by PID and find processes with most CLOSE_WAIT
        pid_counts = {}
        for local, pid, foreign, state in close_wait_conns:
            if pid > 0:
                pid_counts[pid] = pid_counts.get(pid, 0) + 1

        for pid, count in pid_counts.items():
            try:
                proc = psutil.Process(pid)
                if not is_protected(proc.name(), exclusions):
                    mem_info = proc.memory_info()
                    zombies.append({
                        'pid': pid,
                        'name': proc.name(),
                        'type': 'close_wait_leak',
                        'memory_mb': round(mem_info.rss / (1024 * 1024), 2),
                        'memory_bytes': mem_info.rss,
                        'close_wait_count': count,
                        'total_connections': len(proc.connections())
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    # 2. Find WebSocket zombies
    ws_zombies = find_websocket_zombies(exclusions)
    zombies.extend(ws_zombies)

    # 3. Check TIME_WAIT accumulation
    time_wait_count = count_time_wait_sockets()
    if time_wait_count > TIME_WAIT_WARNING_THRESHOLD:
        warnings.append({
            'type': 'time_wait_excessive',
            'count': time_wait_count,
            'threshold': TIME_WAIT_WARNING_THRESHOLD,
            'message': f"Found {time_wait_count} TIME_WAIT sockets (threshold: {TIME_WAIT_WARNING_THRESHOLD})"
        })

    # 4. Find processes with excessive connections but low activity
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            mem_info = proc.info.get('memory_info')

            if mem_info is None:
                continue

            # Check if protected
            if is_protected(name, exclusions):
                continue

            # Get connections separately
            try:
                p = psutil.Process(pid)
                connections = p.connections()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                connections = []

            # Look for processes with >50 connections but <1% CPU
            cpu_percent = proc.cpu_percent(interval=0.1)
            if len(connections) > 50 and cpu_percent < 1.0:
                memory_bytes = mem_info.rss

                # Check if memory exceeds threshold
                if memory_bytes >= MEMORY_THRESHOLD:
                    zombies.append({
                        'pid': pid,
                        'name': name,
                        'type': 'excessive_connections_idle',
                        'memory_mb': round(memory_bytes / (1024 * 1024), 2),
                        'memory_bytes': memory_bytes,
                        'connection_count': len(connections),
                        'cpu_percent': round(cpu_percent, 2)
                    })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return {
        'zombies': zombies,
        'warnings': warnings,
        'close_wait_connections': close_wait_conns,
        'time_wait_count': time_wait_count
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed connection information')
def main(format: str, verbose: bool):
    """
    Network Connection Leaks Hunter - Agent 11

    Detects zombie network connections and leaked sockets.
    Expected recovery: 1-2 GB
    """
    start_time = time.time()

    # Load exclusions
    exclusions = load_exclusions()

    # Detect zombies
    result = find_zombie_network_connections(exclusions)
    zombies = result['zombies']
    warnings = result['warnings']
    close_wait_conns = result['close_wait_connections']
    time_wait_count = result['time_wait_count']

    # Calculate totals
    total_memory = sum(z['memory_bytes'] for z in zombies)
    execution_time = round((time.time() - start_time) * 1000, 2)

    # Output results
    if format == 'json':
        output = {
            'agent': 'network_connection_leaks',
            'agent_number': 11,
            'zombies_found': len(zombies),
            'total_memory_bytes': total_memory,
            'total_memory_mb': round(total_memory / (1024 * 1024), 2),
            'execution_time_ms': execution_time,
            'pids': [z['pid'] for z in zombies],
            'processes': zombies,
            'warnings': warnings,
            'metrics': {
                'close_wait_count': len(close_wait_conns),
                'time_wait_count': time_wait_count,
                'close_wait_threshold': CLOSE_WAIT_THRESHOLD,
                'time_wait_threshold': TIME_WAIT_WARNING_THRESHOLD
            }
        }

        if verbose:
            output['close_wait_connections'] = [
                {'local': local, 'pid': pid, 'foreign': foreign, 'state': state}
                for local, pid, foreign, state in close_wait_conns
            ]

        print(json.dumps(output, indent=2))

    elif format == 'summary':
        console.print(f"\n[bold cyan]Agent 11: Network Connection Leaks[/bold cyan]")
        console.print(f"Zombies found: [bold red]{len(zombies)}[/bold red]")
        console.print(f"Total memory: [bold red]{round(total_memory / (1024 * 1024), 2)} MB[/bold red]")
        console.print(f"CLOSE_WAIT connections: [yellow]{len(close_wait_conns)}[/yellow]")
        console.print(f"TIME_WAIT sockets: [yellow]{time_wait_count}[/yellow]")

        if warnings:
            console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  - {warning['message']}")

    else:  # table format
        table = Table(title=f"Agent 11: Network Connection Leaks ({len(zombies)} found)")
        table.add_column("PID", style="cyan")
        table.add_column("Process", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Memory (MB)", justify="right", style="red")
        table.add_column("Connections", justify="right", style="blue")
        table.add_column("Details", style="dim")

        for z in zombies:
            details = ""
            if z['type'] == 'close_wait_leak':
                details = f"CLOSE_WAIT: {z.get('close_wait_count', 0)}"
            elif z['type'] == 'websocket_zombie':
                details = "No active connections"
            elif z['type'] == 'excessive_connections_idle':
                details = f"CPU: {z.get('cpu_percent', 0)}%"

            table.add_row(
                str(z['pid']),
                z['name'],
                z['type'].replace('_', ' ').title(),
                str(z['memory_mb']),
                str(z.get('connection_count', z.get('total_connections', 0))),
                details
            )

        console.print(table)
        console.print(f"\n[bold]Total Memory:[/bold] {round(total_memory / (1024 * 1024), 2)} MB")
        console.print(f"[bold]CLOSE_WAIT:[/bold] {len(close_wait_conns)} connections")
        console.print(f"[bold]TIME_WAIT:[/bold] {time_wait_count} sockets")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")

        if warnings:
            console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  ⚠️  {warning['message']}")


if __name__ == '__main__':
    main()
