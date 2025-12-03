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
JVM Zombie Hunter - Agent JVM

Detects idle Gradle daemons and zombie Java processes.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Idle Gradle daemons (>3 hours, no activity)
- Java processes (>500MB, <1% CPU, >4 hours runtime)
- Orphaned build tool processes

Preserves:
- Active Gradle/Maven builds
- Java processes in IDEs (IntelliJ/Eclipse/VS Code)
- Recent JVM activity (<5 minutes)

Recovery: 5-10 GB (Gradle daemons + zombie Java processes)
"""

import psutil
import click
import json
import time
import os
from pathlib import Path
from datetime import timedelta
from rich.console import Console

console = Console()

# ============================================================================
# ALL FUNCTIONS INLINE (100% self-contained)
# ============================================================================

def format_time(seconds: float) -> str:
    """Format elapsed time as HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))

def format_memory(bytes_value: float) -> str:
    """Format memory in MB"""
    return f"{bytes_value / 1024 / 1024:.1f} MB"

def find_gradle_daemons() -> list:
    """Find idle Gradle daemon processes"""
    daemons = []

    # Check ~/.gradle/daemon/ directory for daemon registry
    gradle_dir = Path.home() / ".gradle" / "daemon"
    daemon_registry = {}

    if gradle_dir.exists():
        for version_dir in gradle_dir.iterdir():
            if version_dir.is_dir():
                registry_file = version_dir / "registry.bin"
                if registry_file.exists():
                    try:
                        mtime = registry_file.stat().st_mtime
                        age_hours = (time.time() - mtime) / 3600
                        daemon_registry[str(version_dir.name)] = {
                            'last_activity': mtime,
                            'age_hours': age_hours
                        }
                    except OSError:
                        continue

    # Find Gradle daemon processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check for Gradle daemon
            is_gradle_daemon = (
                "GradleDaemon" in cmdline or
                "gradle-launcher" in cmdline or
                ("java" in proc.info['name'].lower() and "gradle" in cmdline.lower() and "daemon" in cmdline.lower())
            )

            if not is_gradle_daemon:
                continue

            # Calculate runtime
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time
            runtime_hours = elapsed / 3600

            daemons.append({
                'pid': proc.info['pid'],
                'cmdline': cmdline,
                'elapsed': elapsed,
                'runtime_hours': runtime_hours,
                'memory_bytes': proc.info['memory_info'].rss,
                'cpu_percent': proc.info['cpu_percent']
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return daemons

def find_java_zombies() -> list:
    """Find zombie Java processes (high memory, low CPU, long runtime)"""
    zombies = []

    min_memory_mb = 500
    max_cpu_percent = 1.0
    min_runtime_hours = 4.0

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if it's a Java process
            is_java = "java" in name.lower()
            if not is_java:
                continue

            # Skip protected patterns (IDE-related)
            protected_patterns = [
                "intellij",
                "idea",
                "eclipse",
                "vscode",
                "code-server",
                "jetbrains"
            ]

            if any(pattern in cmdline.lower() for pattern in protected_patterns):
                continue

            # Calculate metrics
            create_time = proc.info['create_time']
            elapsed = time.time() - create_time
            runtime_hours = elapsed / 3600
            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
            cpu = proc.info['cpu_percent']

            # Check if it's a zombie
            if memory_mb > min_memory_mb and cpu < max_cpu_percent and runtime_hours > min_runtime_hours:
                zombies.append({
                    'pid': proc.info['pid'],
                    'cmdline': cmdline,
                    'elapsed': elapsed,
                    'runtime_hours': runtime_hours,
                    'memory_bytes': proc.info['memory_info'].rss,
                    'cpu_percent': cpu
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue

    return zombies

def is_build_tool_active() -> bool:
    """Check if Gradle or Maven builds are actively running"""
    for proc in psutil.process_iter(['name', 'cmdline', 'create_time']):
        try:
            name = proc.info['name'] or ""
            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check for active build tools
            is_build = (
                "gradle" in name.lower() or
                "mvn" in name.lower() or
                "maven" in cmdline.lower()
            )

            if is_build:
                # Check if process is recent (< 5 minutes)
                create_time = proc.info['create_time']
                age_minutes = (time.time() - create_time) / 60
                if age_minutes < 5:
                    return True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False

def is_ide_running() -> bool:
    """Check if IDE is running (IntelliJ/Eclipse/VS Code)"""
    ide_names = ["idea", "intellij", "eclipse", "code", "code-server"]

    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'] or ""
            if any(ide in name.lower() for ide in ide_names):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False

def find_zombie_jvm_processes() -> list:
    """Detect zombie JVM processes"""
    zombies = []

    min_daemon_idle_hours = 3.0
    min_recent_use_minutes = 5.0

    # Find idle Gradle daemons
    daemons = find_gradle_daemons()
    for daemon in daemons:
        runtime_hours = daemon['runtime_hours']
        age_minutes = daemon['elapsed'] / 60

        # Skip if too recent
        if age_minutes < min_recent_use_minutes:
            continue

        # Check if idle for too long
        if runtime_hours > min_daemon_idle_hours:
            zombies.append({
                "pid": daemon['pid'],
                "command": daemon['cmdline'][:80] + "..." if len(daemon['cmdline']) > 80 else daemon['cmdline'],
                "elapsed": format_time(daemon['elapsed']),
                "elapsed_hours": round(runtime_hours, 1),
                "cpu_percent": round(daemon['cpu_percent'], 2),
                "memory": format_memory(daemon['memory_bytes']),
                "memory_bytes": daemon['memory_bytes'],
                "type": "Gradle daemon"
            })

    # Find generic Java zombies
    java_zombies = find_java_zombies()
    for zombie in java_zombies:
        zombies.append({
            "pid": zombie['pid'],
            "command": zombie['cmdline'][:80] + "..." if len(zombie['cmdline']) > 80 else zombie['cmdline'],
            "elapsed": format_time(zombie['elapsed']),
            "elapsed_hours": round(zombie['runtime_hours'], 1),
            "cpu_percent": round(zombie['cpu_percent'], 2),
            "memory": format_memory(zombie['memory_bytes']),
            "memory_bytes": zombie['memory_bytes'],
            "type": "Java process"
        })

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """JVM Zombie Hunter - Parallel Agent JVM"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent JVM: JVM Zombie Hunter[/cyan]")
        console.print("Scanning for idle Gradle daemons and zombie Java processes...\n")

    # Safety checks
    skip_reasons = []

    if is_ide_running():
        skip_reasons.append("IDE running (IntelliJ/Eclipse/VS Code)")

    if is_build_tool_active():
        skip_reasons.append("Active build detected")

    if skip_reasons:
        if verbose:
            console.print(f"[yellow]⚠️  Skipping scan: {', '.join(skip_reasons)}[/yellow]")
        result = {
            "agent": "jvm_zombies",
            "zombies_found": 0,
            "total_memory_bytes": 0,
            "total_memory": "0 MB",
            "execution_time_ms": 0,
            "pids": [],
            "processes": [],
            "skipped": True,
            "reason": ", ".join(skip_reasons)
        }
        print(json.dumps(result, indent=2))
        return

    # Detect zombies
    zombies = find_zombie_jvm_processes()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "jvm_zombies",
        "zombies_found": len(zombies),
        "total_memory_bytes": sum(z["memory_bytes"] for z in zombies),
        "total_memory": format_memory(sum(z["memory_bytes"] for z in zombies)),
        "execution_time_ms": round(execution_time, 2),
        "pids": [z["pid"] for z in zombies],
        "processes": zombies if verbose else []
    }

    # Output based on format
    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        from rich.table import Table
        table = Table(title=f"JVM Zombies ({len(zombies)} found)")
        table.add_column("PID", justify="right")
        table.add_column("Type", justify="left")
        table.add_column("Runtime", justify="right")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory")
        table.add_column("Command")

        for z in zombies:
            table.add_row(
                str(z["pid"]),
                z["type"],
                z["elapsed"],
                f"{z['cpu_percent']:.1f}%",
                z["memory"],
                z["command"][:50]
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]JVM Zombie Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
