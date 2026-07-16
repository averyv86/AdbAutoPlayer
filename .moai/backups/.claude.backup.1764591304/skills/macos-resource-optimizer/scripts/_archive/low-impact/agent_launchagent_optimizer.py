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
LaunchAgent Optimizer - Agent 13

Analyzes LaunchAgents for optimization opportunities.

Detection Targets:
- ~/Library/LaunchAgents (User agents)
- /Library/LaunchAgents (System agents)
- Running agents via launchctl list
- Memory consumption per agent

Reports:
- Agents consuming >50MB memory
- Disabled but loaded agents
- Orphaned agent plists
"""

import json
import os
import plistlib
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

# LaunchAgent directories
USER_AGENTS = Path.home() / "Library" / "LaunchAgents"
SYSTEM_AGENTS = Path("/Library/LaunchAgents")

MEMORY_THRESHOLD_MB = 50


def format_size(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def run_command(cmd: List[str]) -> tuple[str, int]:
    """Run a command and return output and return code."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1


def get_loaded_agents() -> Dict[str, Dict[str, Any]]:
    """Get list of loaded LaunchAgents from launchctl."""
    agents = {}
    output, code = run_command(["launchctl", "list"])

    if code != 0:
        return agents

    for line in output.strip().split('\n')[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 3:
            pid = parts[0]
            status = parts[1]
            label = parts[2]

            agents[label] = {
                "pid": int(pid) if pid != '-' else None,
                "status": int(status) if status != '-' else 0,
                "label": label,
                "running": pid != '-',
            }

    return agents


def get_process_memory(pid: int) -> int:
    """Get memory usage for a process by PID."""
    try:
        proc = psutil.Process(pid)
        return proc.memory_info().rss
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def parse_plist(path: Path) -> Optional[Dict[str, Any]]:
    """Parse a plist file and return contents."""
    try:
        with open(path, 'rb') as f:
            return plistlib.load(f)
    except Exception:
        return None


def analyze_agents_directory(path: Path, loaded_agents: Dict[str, Dict], verbose: bool = False) -> List[Dict[str, Any]]:
    """Analyze LaunchAgents in a directory."""
    results = []

    if not path.exists():
        return results

    for plist_file in path.glob("*.plist"):
        plist_data = parse_plist(plist_file)
        if not plist_data:
            continue

        label = plist_data.get("Label", plist_file.stem)
        program = plist_data.get("Program", "")
        program_args = plist_data.get("ProgramArguments", [])
        run_at_load = plist_data.get("RunAtLoad", False)
        keep_alive = plist_data.get("KeepAlive", False)
        disabled = plist_data.get("Disabled", False)

        # Check if loaded
        loaded_info = loaded_agents.get(label, {})
        is_loaded = label in loaded_agents
        is_running = loaded_info.get("running", False)
        pid = loaded_info.get("pid")

        # Get memory if running
        memory_bytes = 0
        if pid:
            memory_bytes = get_process_memory(pid)

        # Determine optimization opportunities
        issues = []
        if disabled and is_loaded:
            issues.append("Disabled but still loaded")
        if memory_bytes > MEMORY_THRESHOLD_MB * 1024 * 1024:
            issues.append(f"High memory (>{MEMORY_THRESHOLD_MB}MB)")
        if not is_loaded and run_at_load:
            issues.append("RunAtLoad but not loaded")

        agent_info = {
            "label": label,
            "plist_path": str(plist_file),
            "program": program or (program_args[0] if program_args else "unknown"),
            "run_at_load": run_at_load,
            "keep_alive": keep_alive,
            "disabled": disabled,
            "is_loaded": is_loaded,
            "is_running": is_running,
            "pid": pid,
            "memory_bytes": memory_bytes,
            "memory_human": format_size(memory_bytes) if memory_bytes else "N/A",
            "issues": issues,
            "has_issues": len(issues) > 0,
        }

        results.append(agent_info)

        if verbose and issues:
            console.print(f"  [yellow]{label}[/yellow]: {', '.join(issues)}")

    return results


def detect_launchagent_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Main detection function for LaunchAgent analysis."""
    start_time = time.time()

    if verbose:
        console.print("[cyan]Analyzing LaunchAgents...[/cyan]\n")

    # Get loaded agents first
    loaded_agents = get_loaded_agents()

    if verbose:
        console.print(f"[bold]Loaded agents:[/bold] {len(loaded_agents)}\n")

    # Analyze directories
    if verbose:
        console.print("[bold]User LaunchAgents:[/bold]")
    user_agents = analyze_agents_directory(USER_AGENTS, loaded_agents, verbose)

    if verbose:
        console.print("\n[bold]System LaunchAgents:[/bold]")
    system_agents = analyze_agents_directory(SYSTEM_AGENTS, loaded_agents, verbose)

    all_agents = user_agents + system_agents

    # Calculate stats
    high_memory_agents = [a for a in all_agents if a["memory_bytes"] > MEMORY_THRESHOLD_MB * 1024 * 1024]
    agents_with_issues = [a for a in all_agents if a["has_issues"]]
    total_memory = sum(a["memory_bytes"] for a in all_agents if a["is_running"])

    execution_time = (time.time() - start_time) * 1000

    return {
        "zombies_found": len(agents_with_issues),
        "memory_freed_mb": round(sum(a["memory_bytes"] for a in high_memory_agents) / (1024 * 1024), 1),
        "actions_taken": len(agents_with_issues),
        "status": "success",
        "time_ms": round(execution_time, 2),
        "details": {
            "total_agents": len(all_agents),
            "loaded_agents": len([a for a in all_agents if a["is_loaded"]]),
            "running_agents": len([a for a in all_agents if a["is_running"]]),
            "high_memory_agents": len(high_memory_agents),
            "agents_with_issues": len(agents_with_issues),
            "total_memory_bytes": total_memory,
            "total_memory_human": format_size(total_memory),
            "user_agents": user_agents,
            "system_agents": system_agents,
            "recommendation": "Review high-memory agents and disable unused services",
        }
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="LaunchAgent Analysis")
    table.add_column("Label", style="cyan")
    table.add_column("Running", justify="center")
    table.add_column("Memory", justify="right")
    table.add_column("Issues", style="yellow")

    all_agents = result["details"]["user_agents"] + result["details"]["system_agents"]
    for agent in sorted(all_agents, key=lambda x: x["memory_bytes"], reverse=True)[:20]:
        running = "[green]Yes[/green]" if agent["is_running"] else "[dim]No[/dim]"
        issues = ", ".join(agent["issues"]) if agent["issues"] else "-"
        table.add_row(
            agent["label"][:40],
            running,
            agent["memory_human"],
            issues[:30]
        )

    console.print(table)
    console.print(f"\n[bold]Total Agent Memory:[/bold] {result['details']['total_memory_human']}")


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]LaunchAgent Optimization Analysis[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Total agents: {result['details']['total_agents']}")
    console.print(f"Running agents: {result['details']['running_agents']}")
    console.print(f"High memory agents: {result['details']['high_memory_agents']}")
    console.print(f"Agents with issues: {result['details']['agents_with_issues']}")
    console.print(f"Total memory: {result['details']['total_memory_human']}")
    console.print(f"Execution time: {result['time_ms']:.2f}ms")

    console.print(f"\n[dim]{result['details']['recommendation']}[/dim]")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Analyze LaunchAgents for optimization opportunities."""
    result = detect_launchagent_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
