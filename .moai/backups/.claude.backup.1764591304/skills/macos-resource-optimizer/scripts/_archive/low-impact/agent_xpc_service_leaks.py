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
XPC Service Leak Hunter - Agent 8
Detects orphaned and leaked XPC agent processes from macOS system services.

Detection Rules:
- Pattern: `com.apple.*XPCAgent` or `*.xpc` service processes
- Criteria: Long-running (>24h), idle (<1% CPU), orphaned (parent terminated)
- Memory: 50-100 MB per leaked service, accumulates to 1-2 GB over time

Protection:
- WHITELIST-ONLY: Never touch critical system services
- Protected: Dock, WindowServer, Security, Audio, Kernel extensions
- Only target: User-space app XPC agents that lost parent process
"""

import json
import time
from typing import Dict, List, Any, Set

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

# Configuration
RUNTIME_THRESHOLD_HOURS = 24  # Flag if running >24 hours
CPU_THRESHOLD_PERCENT = 1.0   # Flag if CPU <1%
MEMORY_THRESHOLD_MB = 50      # Typical leaked XPC service memory

# CRITICAL WHITELIST: Never touch these system services
SYSTEM_XPC_WHITELIST = {
    # Core system services
    "com.apple.WindowServer",
    "com.apple.dock",
    "com.apple.systemuiserver",
    "com.apple.Dock",

    # Security & authentication
    "com.apple.security",
    "com.apple.SecurityAgent",
    "com.apple.authd",
    "com.apple.securityd",
    "com.apple.loginwindow",

    # Audio & media
    "com.apple.audio",
    "com.apple.coreaudio",
    "com.apple.CoreAudio",

    # Display & graphics
    "com.apple.windowserver",
    "com.apple.ColorSync",

    # Kernel & system
    "com.apple.kernel",
    "com.apple.kextd",
    "com.apple.launchd",

    # Networking
    "com.apple.networkd",
    "com.apple.configd",

    # Input devices
    "com.apple.HIServices",
    "com.apple.inputmethod",

    # Notifications
    "com.apple.notificationcenterui",
    "com.apple.usernotificationsd",

    # Spotlight & search
    "com.apple.spotlight",
    "com.apple.metadata",

    # Time Machine
    "com.apple.TimeMachine",
    "com.apple.backupd",
}

# User-space app XPC patterns (safe to check for orphans)
USER_XPC_PATTERNS = [
    "XPCAgent",
    ".xpc/Contents",
    "Helper.xpc",
    "Service.xpc",
]

# Protected parent processes
PROTECTED_PROCESSES = {
    "claude-flow",
    "claude",
    "ghostty",
    "Terminal",
    "iTerm",
    "Warp",
    "Finder",
    "Dock"
}


def format_memory(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def get_xpc_whitelist() -> Set[str]:
    """Get complete whitelist of protected XPC services."""
    return SYSTEM_XPC_WHITELIST.copy()


def is_system_critical_xpc(cmdline: str, name: str) -> bool:
    """Check if XPC service is system-critical (never kill)."""
    whitelist = get_xpc_whitelist()

    # Check exact matches
    for protected in whitelist:
        if protected.lower() in cmdline.lower() or protected.lower() in name.lower():
            return True

    return False


def is_user_space_xpc(cmdline: str) -> bool:
    """Check if XPC service is user-space app helper (safe to check)."""
    for pattern in USER_XPC_PATTERNS:
        if pattern in cmdline:
            # Make sure it's not a system service
            if not is_system_critical_xpc(cmdline, ""):
                return True
    return False


def is_xpc_service_active(proc: psutil.Process) -> bool:
    """Verify if XPC service is legitimately active."""
    try:
        # Check if parent process exists and is running
        parent = proc.parent()
        if parent and parent.is_running():
            parent_name = parent.name()

            # If parent is system process, it's legitimate
            if parent_name in PROTECTED_PROCESSES:
                return True

            # If parent is a user app, verify it's actually running
            if parent.status() == psutil.STATUS_RUNNING:
                return True

        # Check if process has open connections (network activity)
        connections = proc.net_connections()
        if connections:
            return True

        # Check if process has open files (active I/O)
        open_files = proc.open_files()
        if len(open_files) > 2:  # More than stdin/stdout
            return True

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    return False


def find_xpc_agent_processes() -> List[psutil.Process]:
    """Find all XPC agent processes."""
    xpc_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info.get('cmdline') or [])
            name = proc.info.get('name', '')

            # Look for XPC patterns
            if ('XPCAgent' in name or
                'XPCAgent' in cmdline or
                '.xpc' in cmdline):
                xpc_processes.append(proc)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return xpc_processes


def detect_xpc_service_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Detect orphaned and leaked XPC service processes."""
    start_time = time.time()
    zombies = []

    if verbose:
        console.print("[cyan]Scanning for XPC service zombie processes...[/cyan]")
        console.print(f"[yellow]Protected services: {len(SYSTEM_XPC_WHITELIST)}[/yellow]")

    current_time = time.time()
    xpc_processes = find_xpc_agent_processes()

    if verbose:
        console.print(f"Found {len(xpc_processes)} XPC processes total")

    for proc in xpc_processes:
        try:
            info = proc.as_dict(['pid', 'name', 'cmdline', 'cpu_percent',
                                'memory_info', 'create_time', 'ppid', 'status'])

            cmdline_str = ' '.join(info.get('cmdline') or [])
            name = info.get('name', '')

            # CRITICAL: Skip system services
            if is_system_critical_xpc(cmdline_str, name):
                if verbose:
                    console.print(f"  PID {info['pid']}: [green]PROTECTED[/green] - System service")
                continue

            # Only check user-space XPC services
            if not is_user_space_xpc(cmdline_str):
                if verbose:
                    console.print(f"  PID {info['pid']}: [blue]SKIP[/blue] - Not user-space XPC")
                continue

            runtime_hours = (current_time - info['create_time']) / 3600
            cpu_percent = info.get('cpu_percent') or 0
            memory_mb = info['memory_info'].rss / (1024 * 1024)

            # Check if it's a zombie
            is_long_running = runtime_hours > RUNTIME_THRESHOLD_HOURS
            is_idle = cpu_percent < CPU_THRESHOLD_PERCENT
            is_active = is_xpc_service_active(proc)

            if verbose:
                console.print(f"\n  PID {info['pid']} ({name[:30]})")
                console.print(f"    Runtime: {runtime_hours:.1f}h, "
                            f"CPU: {cpu_percent:.1f}%, "
                            f"MEM: {memory_mb:.1f}MB")
                console.print(f"    Active: {is_active}, "
                            f"Status: {info.get('status', 'unknown')}")

            # Flag as zombie if:
            # 1. Running for >24h AND
            # 2. Idle (<1% CPU) AND
            # 3. Not legitimately active (orphaned or no activity)
            if is_long_running and is_idle and not is_active:
                # Double-check parent status
                parent_exists = False
                try:
                    if info.get('ppid'):
                        parent = psutil.Process(info['ppid'])
                        parent_exists = parent.is_running()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                reason_parts = []
                if not parent_exists:
                    reason_parts.append("orphaned (parent terminated)")
                if is_idle:
                    reason_parts.append(f"idle {cpu_percent:.1f}% CPU")
                if is_long_running:
                    reason_parts.append(f"running {runtime_hours:.1f}h")

                zombies.append({
                    'pid': info['pid'],
                    'name': name,
                    'cmdline': cmdline_str[:200],
                    'cpu_percent': cpu_percent,
                    'memory_bytes': info['memory_info'].rss,
                    'runtime_hours': runtime_hours,
                    'reason': ', '.join(reason_parts),
                    'type': 'xpc-service-leak',
                    'parent_exists': parent_exists
                })

                if verbose:
                    console.print(f"    [red]ZOMBIE DETECTED[/red]: {', '.join(reason_parts)}")
            elif verbose and is_active:
                console.print(f"    [green]ACTIVE[/green]: Legitimate service")

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError) as e:
            if verbose:
                console.print(f"  [yellow]Error processing PID: {e}[/yellow]")
            continue

    execution_time = (time.time() - start_time) * 1000
    total_memory = sum(z['memory_bytes'] for z in zombies)

    return {
        'zombies_found': len(zombies),
        'total_memory_bytes': total_memory,
        'pids': [z['pid'] for z in zombies],
        'processes': zombies,
        'execution_time_ms': round(execution_time, 2),
        'total_xpc_scanned': len(xpc_processes),
        'protected_services': len(SYSTEM_XPC_WHITELIST)
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="XPC Service Zombie Processes")
    table.add_column("PID", style="cyan")
    table.add_column("Name", style="yellow", max_width=30)
    table.add_column("CPU %", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Runtime", justify="right")
    table.add_column("Reason", style="red", max_width=50)

    for proc in result['processes']:
        table.add_row(
            str(proc['pid']),
            proc['name'][:30],
            f"{proc['cpu_percent']:.1f}%",
            format_memory(proc['memory_bytes']),
            f"{proc['runtime_hours']:.1f}h",
            proc['reason']
        )

    console.print(table)


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]XPC Service Zombie Analysis[/bold]")
    console.print(f"Total XPC processes scanned: {result['total_xpc_scanned']}")
    console.print(f"Protected system services: {result['protected_services']}")
    console.print(f"Zombies found: {result['zombies_found']}")
    console.print(f"Total memory: {format_memory(result['total_memory_bytes'])}")
    console.print(f"Execution time: {result['execution_time_ms']:.2f}ms")

    if result['zombies_found'] > 0:
        console.print(f"\n[yellow]WARNING: Review carefully before killing![/yellow]")
        console.print(f"PIDs to kill: {', '.join(map(str, result['pids']))}")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Detect orphaned and leaked XPC service processes."""
    result = detect_xpc_service_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
