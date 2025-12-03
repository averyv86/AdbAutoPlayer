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
Generic Idle Hunter - Agent 10
Catch-all for any idle process >500MB not detected by specialized agents.

Detects processes that:
- Use >500MB memory
- Have <1% CPU for 24+ hours
- Are not protected by exclusions
- Are not system critical processes
- Were not caught by specialized agents 1-9
"""

import json
import time
import psutil
from pathlib import Path
from typing import Dict, List, Any
import click
from rich.console import Console
from rich.table import Table

console = Console()

# Memory threshold: 500MB in bytes
MEMORY_THRESHOLD = 524_288_000
CPU_THRESHOLD = 1.0  # 1% CPU
IDLE_TIME_THRESHOLD = 86400  # 24 hours in seconds

# System processes that should never be killed
SYSTEM_PROCESSES = {
    'kernel_task', 'launchd', 'WindowServer', 'loginwindow', 'Finder',
    'Dock', 'SystemUIServer', 'UserEventAgent', 'coreservicesd', 'coreaudiod',
    'cfprefsd', 'distnoted', 'hidd', 'notifyd', 'syslogd', 'blued',
    'bluetoothd', 'airportd', 'mDNSResponder', 'networkserviceproxy',
    'com.apple.WebKit.WebContent', 'accountsd', 'apsd', 'bird', 'cloudd'
}

# Processes caught by specialized agents (1-9)
SPECIALIZED_AGENT_PATTERNS = {
    'workerd', 'wrangler',  # Agent 1: Cloudflare Workers
    'ChromeDriver', 'geckodriver', 'msedgedriver',  # Agent 2: Browser drivers
    'node', 'npm', 'yarn', 'pnpm', 'bun',  # Agent 3: Node.js
    'python', 'python3', 'pip', 'pipenv', 'poetry',  # Agent 4: Python
    'ruby', 'gem', 'bundle', 'rails',  # Agent 5: Ruby
    'java', 'mvn', 'gradle',  # Agent 6: Java
    'rust-analyzer', 'cargo', 'rustc',  # Agent 7: Rust
    'go', 'gopls',  # Agent 8: Go
    'Railway CLI', 'railway',  # Agent 9: Railway MCP
}


def load_exclusions() -> Dict[str, Any]:
    """Load protection rules from config/exclusions.json."""
    config_path = Path(__file__).parent.parent / 'config' / 'exclusions.json'

    if not config_path.exists():
        console.print(f"[yellow]Warning: {config_path} not found, using minimal defaults[/yellow]")
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

    # System processes
    if proc_name in SYSTEM_PROCESSES:
        return True

    return False


def is_specialized_agent_target(proc_name: str) -> bool:
    """Check if process should be caught by specialized agents 1-9."""
    proc_lower = proc_name.lower()

    for pattern in SPECIALIZED_AGENT_PATTERNS:
        if pattern.lower() in proc_lower:
            return True

    return False


def get_process_idle_time(proc: psutil.Process) -> float:
    """
    Estimate process idle time based on CPU usage.
    Returns seconds since process has been truly idle (<1% CPU).

    Note: This is an approximation since we can't track historical CPU usage.
    We use process creation time as a proxy if CPU is currently low.
    """
    try:
        cpu_percent = proc.cpu_percent(interval=0.1)

        # If CPU is high now, not idle
        if cpu_percent >= CPU_THRESHOLD:
            return 0.0

        # If CPU is low, assume it's been idle since creation
        # (This is conservative - real idle time might be shorter)
        create_time = proc.create_time()
        current_time = time.time()
        uptime = current_time - create_time

        return uptime
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0


def detect_generic_idle_zombies(exclusions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect idle zombie processes not caught by specialized agents."""
    zombies = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time']):
        try:
            # Get process info
            pid = proc.info['pid']
            name = proc.info['name']
            mem_info = proc.info.get('memory_info')
            if mem_info is None:
                continue
            memory_bytes = mem_info.rss

            # Check memory threshold
            if memory_bytes < MEMORY_THRESHOLD:
                continue

            # Check if protected
            if is_protected(name, exclusions):
                continue

            # Check if should be caught by specialized agent
            if is_specialized_agent_target(name):
                continue

            # Check CPU and idle time
            cpu_percent = proc.cpu_percent(interval=0.1)
            idle_time = get_process_idle_time(proc)

            if cpu_percent < CPU_THRESHOLD and idle_time >= IDLE_TIME_THRESHOLD:
                zombies.append({
                    'pid': pid,
                    'name': name,
                    'memory_mb': round(memory_bytes / (1024 * 1024), 2),
                    'memory_bytes': memory_bytes,
                    'cpu_percent': round(cpu_percent, 2),
                    'idle_hours': round(idle_time / 3600, 1),
                    'create_time': proc.info['create_time']
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return zombies


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--min-memory-mb', type=int, default=500, help='Minimum memory in MB')
@click.option('--min-idle-hours', type=float, default=24.0, help='Minimum idle hours')
def main(format: str, min_memory_mb: int, min_idle_hours: float):
    """
    Generic Idle Hunter - Agent 10

    Detects idle processes >500MB not caught by specialized agents.
    """
    start_time = time.time()

    # Load exclusions
    exclusions = load_exclusions()

    # Override thresholds if specified
    global MEMORY_THRESHOLD, IDLE_TIME_THRESHOLD
    MEMORY_THRESHOLD = min_memory_mb * 1024 * 1024
    IDLE_TIME_THRESHOLD = min_idle_hours * 3600

    # Detect zombies
    zombies = detect_generic_idle_zombies(exclusions)

    # Calculate totals
    total_memory = sum(z['memory_bytes'] for z in zombies)
    execution_time = round((time.time() - start_time) * 1000, 2)

    # Output results
    if format == 'json':
        result = {
            'agent': 'generic_idle_hunter',
            'agent_number': 10,
            'zombies_found': len(zombies),
            'total_memory_bytes': total_memory,
            'total_memory_mb': round(total_memory / (1024 * 1024), 2),
            'execution_time_ms': execution_time,
            'pids': [z['pid'] for z in zombies],
            'processes': zombies,
            'thresholds': {
                'memory_mb': min_memory_mb,
                'idle_hours': min_idle_hours,
                'cpu_percent': CPU_THRESHOLD
            }
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        table = Table(title=f"Agent 10: Generic Idle Zombies ({len(zombies)} found)")
        table.add_column("PID", style="cyan")
        table.add_column("Process", style="yellow")
        table.add_column("Memory (MB)", justify="right", style="red")
        table.add_column("CPU %", justify="right", style="green")
        table.add_column("Idle (hours)", justify="right", style="blue")

        for z in zombies:
            table.add_row(
                str(z['pid']),
                z['name'],
                str(z['memory_mb']),
                str(z['cpu_percent']),
                str(z['idle_hours'])
            )

        console.print(table)
        console.print(f"\n[bold]Total Memory:[/bold] {round(total_memory / (1024 * 1024), 2)} MB")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
