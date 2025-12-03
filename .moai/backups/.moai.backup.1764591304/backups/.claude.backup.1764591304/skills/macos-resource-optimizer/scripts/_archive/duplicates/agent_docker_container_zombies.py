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
Docker Container Zombie Hunter - Agent 3

Detects stopped Docker containers and orphaned containerd-shim processes.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Docker containers stopped >24 hours
- Orphaned containerd-shim processes
- Docker processes with dead parent processes
- Unused docker-compose processes

Preserves:
- Active Docker daemon (dockerd)
- Recently stopped containers (<24h)
- Active container processes
"""

import psutil
import click
import json
import time
import subprocess
from datetime import timedelta, datetime
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

def is_dockerd_running() -> bool:
    """Check if Docker daemon is running"""
    for proc in psutil.process_iter(['name']):
        try:
            if 'dockerd' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def get_stopped_containers() -> list:
    """Get all stopped Docker containers using docker ps"""
    containers = []

    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "status=exited", "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return []

        lines = result.stdout.strip().split('\n')

        for line in lines:
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 4:
                container_id = parts[0]
                name = parts[1]
                status = parts[2]
                image = parts[3]

                # Parse "Exited (0) X hours/days ago" to get elapsed time
                elapsed_hours = parse_docker_status_time(status)

                if elapsed_hours >= 24:  # Only containers stopped >24 hours
                    containers.append({
                        "container_id": container_id,
                        "name": name,
                        "status": status,
                        "image": image,
                        "elapsed_hours": elapsed_hours
                    })

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return containers

def parse_docker_status_time(status: str) -> float:
    """Parse Docker status string to get hours elapsed"""
    try:
        # Format: "Exited (0) 2 days ago" or "Exited (0) 3 hours ago"
        parts = status.split()

        if 'day' in status.lower():
            days_idx = next(i for i, part in enumerate(parts) if part.isdigit())
            days = int(parts[days_idx])
            return days * 24
        elif 'hour' in status.lower():
            hours_idx = next(i for i, part in enumerate(parts) if part.isdigit())
            hours = int(parts[hours_idx])
            return hours
        elif 'minute' in status.lower():
            return 0.5  # Less than an hour
        else:
            return 0

    except (ValueError, StopIteration):
        return 0

def find_containerd_shim_orphans() -> list:
    """Find orphaned containerd-shim processes"""
    orphans = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
        try:
            name = proc.info['name'].lower()

            # Look for containerd-shim processes
            if 'containerd-shim' not in name:
                continue

            cmdline = " ".join(proc.info['cmdline'] or [])

            # Check if parent is alive
            try:
                parent = proc.parent()
                if parent is None:
                    is_orphan = True
                else:
                    # Check if parent is also containerd-related or dockerd
                    parent_name = parent.name().lower()
                    if 'docker' not in parent_name and 'containerd' not in parent_name:
                        is_orphan = True
                    else:
                        is_orphan = False
            except psutil.NoSuchProcess:
                is_orphan = True

            if is_orphan:
                create_time = proc.info['create_time']
                elapsed = time.time() - create_time
                mem_info = proc.info['memory_info']

                orphans.append({
                    "pid": proc.info['pid'],
                    "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                    "elapsed": format_time(elapsed),
                    "elapsed_seconds": int(elapsed),
                    "memory": format_memory(mem_info.rss),
                    "memory_bytes": mem_info.rss,
                    "type": "containerd-shim-orphan"
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return orphans

def find_zombie_docker_processes() -> list:
    """Main detection function for zombie Docker processes"""

    # Safety check: Skip if Docker daemon is running
    if is_dockerd_running():
        if not click.confirm("Docker daemon detected running. Stopping containers may affect running services. Continue?", default=False):
            return []

    zombies = []

    # 1. Find stopped containers (>24h)
    stopped_containers = get_stopped_containers()

    for container in stopped_containers:
        # Estimate memory (containers don't consume much when stopped, but we'll check processes)
        zombies.append({
            "pid": None,
            "type": "stopped-container",
            "container_id": container["container_id"],
            "name": container["name"],
            "command": f"Docker container: {container['name']} ({container['image']})",
            "status": container["status"],
            "elapsed": f"{container['elapsed_hours']:.1f} hours",
            "elapsed_seconds": int(container["elapsed_hours"] * 3600),
            "memory": "N/A",
            "memory_bytes": 0  # Stopped containers don't use memory
        })

    # 2. Find orphaned containerd-shim processes
    shim_orphans = find_containerd_shim_orphans()
    zombies.extend(shim_orphans)

    # 3. Find docker-compose processes that are idle
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])

            if 'docker-compose' not in cmdline.lower():
                continue

            create_time = proc.info['create_time']
            elapsed = time.time() - create_time

            # Only flag if idle >1 hour
            if elapsed < 3600:
                continue

            cpu = proc.info['cpu_percent']

            if cpu < 1.0:  # Idle
                mem_info = proc.info['memory_info']

                zombies.append({
                    "pid": proc.info['pid'],
                    "type": "idle-docker-compose",
                    "command": cmdline[:80] + "..." if len(cmdline) > 80 else cmdline,
                    "elapsed": format_time(elapsed),
                    "elapsed_seconds": int(elapsed),
                    "cpu_percent": round(cpu, 2),
                    "memory": format_memory(mem_info.rss),
                    "memory_bytes": mem_info.rss
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return zombies

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """Docker Container Zombie Hunter - Parallel Agent 3"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 3: Docker Container Zombie Hunter[/cyan]")
        console.print("Scanning for stopped containers and orphaned Docker processes...\n")

    # Detect zombie Docker processes
    zombies = find_zombie_docker_processes()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "docker_container_zombies",
        "zombies_found": len(zombies),
        "total_memory_bytes": sum(z.get("memory_bytes", 0) for z in zombies),
        "total_memory": format_memory(sum(z.get("memory_bytes", 0) for z in zombies)),
        "execution_time_ms": round(execution_time, 2),
        "pids": [z["pid"] for z in zombies if z["pid"] is not None],
        "container_ids": [z.get("container_id") for z in zombies if z.get("container_id")],
        "processes": zombies if verbose else []
    }

    # Output based on format
    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        from rich.table import Table
        table = Table(title=f"Docker Zombies ({len(zombies)} found)")
        table.add_column("Type", justify="left")
        table.add_column("PID/ID", justify="right")
        table.add_column("Runtime", justify="right")
        table.add_column("Memory")
        table.add_column("Details")

        for z in zombies:
            ztype = z.get("type", "unknown")
            pid_or_id = z.get("container_id", str(z.get("pid", "N/A")))[:12]

            table.add_row(
                ztype,
                pid_or_id,
                z.get("elapsed", "N/A"),
                z.get("memory", "N/A"),
                z["command"][:50] if "command" in z else z.get("name", "N/A")
            )

        console.print(table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]Docker Zombie Agent[/bold]")
        console.print(f"  Zombies: {len(zombies)}")
        console.print(f"  Memory: {result['total_memory']}")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
