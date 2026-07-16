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
System Analyzer - Agent 5

Comprehensive system analysis: memory, ports, protection verification.
Self-contained with all dependencies inline (PEP 723).

Analyzes:
- Memory consumption (all processes)
- Port occupancy (listening processes)
- Protected process verification
- System health metrics
"""

import psutil
import click
import json
import time
import subprocess
from rich.console import Console

console = Console()

# ============================================================================
# ALL FUNCTIONS INLINE (100% self-contained)
# ============================================================================

def format_memory(bytes_value: float) -> str:
    """Format memory in MB/GB"""
    gb = bytes_value / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    return f"{bytes_value / (1024 ** 2):.1f} MB"

def analyze_memory() -> dict:
    """Analyze system memory usage"""
    mem = psutil.virtual_memory()

    # Get top 20 memory consumers
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            mem_info = proc.info.get('memory_info')
            if mem_info is None:
                continue

            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "memory_bytes": mem_info.rss,
                "memory": format_memory(mem_info.rss),
                "cpu_percent": round(proc.info.get('cpu_percent', 0.0), 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            continue

    # Sort by memory and get top 20
    top_processes = sorted(processes, key=lambda x: x['memory_bytes'], reverse=True)[:20]

    return {
        "total_ram_gb": round(mem.total / (1024 ** 3), 1),
        "used_ram_gb": round(mem.used / (1024 ** 3), 1),
        "free_ram_gb": round(mem.available / (1024 ** 3), 1),
        "percent_used": round(mem.percent, 1),
        "top_consumers": top_processes
    }

def analyze_ports() -> dict:
    """Analyze port occupancy using lsof (macOS compatible)"""
    try:
        # Use lsof for macOS compatibility
        result = subprocess.run(
            ['lsof', '-iTCP', '-sTCP:LISTEN', '-n', '-P'],
            capture_output=True,
            text=True
        )

        listening_ports = []
        seen_ports = set()

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 9:
                    port_info = parts[8]
                    if ':' in port_info:
                        port = int(port_info.split(':')[-1])
                        if port not in seen_ports:
                            seen_ports.add(port)
                            listening_ports.append({
                                "port": port,
                                "pid": int(parts[1]),
                                "process": parts[0]
                            })

        return {
            "listening_count": len(listening_ports),
            "ports": sorted(listening_ports, key=lambda x: x['port'])
        }
    except Exception as e:
        return {
            "listening_count": 0,
            "ports": [],
            "error": str(e)
        }

def verify_protected_processes() -> dict:
    """Verify critical protected processes are running"""

    protected = {
        "claude-code": 0,
        "claude-flow": 0,
        "ghostty": 0,
        "postgres": 0,
        "redis": 0,
        "meilisearch": 0,
        "ollama": 0
    }

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            cmdline = " ".join(proc.info['cmdline'] or []).lower()

            if "claude-code" in cmdline or "claude" in cmdline:
                protected["claude-code"] += 1
            elif "claude-flow" in cmdline:
                protected["claude-flow"] += 1
            elif "ghostty" in name or "ghostty" in cmdline:
                protected["ghostty"] += 1
            elif "postgres" in name:
                protected["postgres"] += 1
            elif "redis" in name:
                protected["redis"] += 1
            elif "meilisearch" in name:
                protected["meilisearch"] += 1
            elif "ollama" in name:
                protected["ollama"] += 1

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return protected

@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def main(format: str, verbose: bool) -> None:
    """System Analyzer - Parallel Agent 5"""

    start_time = time.time()

    if verbose:
        console.print("[cyan]🔍 Agent 5: System Analyzer[/cyan]")
        console.print("Performing comprehensive system analysis...\n")

    # Perform analyses
    memory = analyze_memory()
    ports = analyze_ports()
    protection = verify_protected_processes()

    execution_time = (time.time() - start_time) * 1000  # milliseconds

    # Prepare output
    result = {
        "agent": "system_analyzer",
        "memory": memory,
        "ports": ports,
        "protected_processes": protection,
        "execution_time_ms": round(execution_time, 2)
    }

    # Output based on format
    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        from rich.table import Table

        # Memory table
        console.print("[bold]Memory Analysis[/bold]")
        console.print(f"Total RAM: {memory['total_ram_gb']} GB")
        console.print(f"Used: {memory['used_ram_gb']} GB ({memory['percent_used']}%)")
        console.print(f"Free: {memory['free_ram_gb']} GB\n")

        # Protection verification
        console.print("[bold]Protected Processes[/bold]")
        prot_table = Table()
        prot_table.add_column("Process")
        prot_table.add_column("Count", justify="right")
        prot_table.add_column("Status")

        for proc, count in protection.items():
            status = "✅" if count > 0 else "❌"
            prot_table.add_row(proc, str(count), status)

        console.print(prot_table)
        console.print(f"\n✓ Completed in {execution_time:.0f}ms")
    else:  # summary
        console.print(f"[bold]System Analyzer[/bold]")
        console.print(f"  RAM Usage: {memory['percent_used']}%")
        console.print(f"  Ports: {ports['listening_count']}")
        console.print(f"  Protected: {sum(1 for c in protection.values() if c > 0)}/7")
        console.print(f"  Time: {execution_time:.0f}ms")

if __name__ == "__main__":
    main()
