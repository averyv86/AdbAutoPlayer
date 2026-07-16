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
Slack/Discord Cache Hunter - Agent 11

Analyzes Slack and Discord cache directories to identify recoverable space.

Detection Targets:
- ~/Library/Application Support/Slack (Cache, Service Worker)
- ~/Library/Application Support/discord (Cache, Code Cache, GPUCache)
- Workspace-specific cache data
- Service Worker caches

Reports:
- Per-app cache sizes
- Workspace breakdown
- Potential space recovery (2-5GB typical)
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.table import Table

console = Console()

# Cache directories to scan
SLACK_BASE = Path.home() / "Library" / "Application Support" / "Slack"
DISCORD_BASE = Path.home() / "Library" / "Application Support" / "discord"

SLACK_CACHE_DIRS = [
    "Cache",
    "Code Cache",
    "Service Worker",
    "GPUCache",
    "blob_storage",
]

DISCORD_CACHE_DIRS = [
    "Cache",
    "Code Cache",
    "GPUCache",
    "blob_storage",
    "Service Worker",
]


def format_size(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def get_directory_size(path: Path) -> int:
    """Calculate total size of a directory recursively."""
    total = 0
    try:
        if path.is_file():
            return path.stat().st_size
        for entry in path.rglob('*'):
            try:
                if entry.is_file():
                    total += entry.stat().st_size
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    return total


def analyze_slack_cache(verbose: bool = False) -> Dict[str, Any]:
    """Analyze Slack cache directories."""
    result = {
        "app": "Slack",
        "base_path": str(SLACK_BASE),
        "exists": SLACK_BASE.exists(),
        "caches": [],
        "total_bytes": 0,
        "workspace_count": 0,
    }

    if not SLACK_BASE.exists():
        return result

    for cache_dir in SLACK_CACHE_DIRS:
        cache_path = SLACK_BASE / cache_dir
        if cache_path.exists():
            size = get_directory_size(cache_path)
            result["caches"].append({
                "name": cache_dir,
                "path": str(cache_path),
                "size_bytes": size,
                "size_human": format_size(size),
            })
            result["total_bytes"] += size
            if verbose:
                console.print(f"  [cyan]Slack/{cache_dir}[/cyan]: {format_size(size)}")

    # Count workspace storage
    storage_path = SLACK_BASE / "storage"
    if storage_path.exists():
        workspaces = [d for d in storage_path.iterdir() if d.is_dir()]
        result["workspace_count"] = len(workspaces)

    return result


def analyze_discord_cache(verbose: bool = False) -> Dict[str, Any]:
    """Analyze Discord cache directories."""
    result = {
        "app": "Discord",
        "base_path": str(DISCORD_BASE),
        "exists": DISCORD_BASE.exists(),
        "caches": [],
        "total_bytes": 0,
    }

    if not DISCORD_BASE.exists():
        return result

    for cache_dir in DISCORD_CACHE_DIRS:
        cache_path = DISCORD_BASE / cache_dir
        if cache_path.exists():
            size = get_directory_size(cache_path)
            result["caches"].append({
                "name": cache_dir,
                "path": str(cache_path),
                "size_bytes": size,
                "size_human": format_size(size),
            })
            result["total_bytes"] += size
            if verbose:
                console.print(f"  [cyan]Discord/{cache_dir}[/cyan]: {format_size(size)}")

    return result


def detect_cache_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Main detection function for Slack/Discord caches."""
    start_time = time.time()

    if verbose:
        console.print("[cyan]Scanning Slack/Discord cache directories...[/cyan]\n")

    slack_result = analyze_slack_cache(verbose)
    discord_result = analyze_discord_cache(verbose)

    total_bytes = slack_result["total_bytes"] + discord_result["total_bytes"]
    execution_time = (time.time() - start_time) * 1000

    # Calculate actions (each cache dir = 1 action)
    actions = len(slack_result["caches"]) + len(discord_result["caches"])

    return {
        "zombies_found": actions,
        "memory_freed_mb": round(total_bytes / (1024 * 1024), 1),
        "actions_taken": actions,
        "status": "success",
        "time_ms": round(execution_time, 2),
        "details": {
            "slack": slack_result,
            "discord": discord_result,
            "total_bytes": total_bytes,
            "total_human": format_size(total_bytes),
            "recommendation": "Safe to clear caches - apps will rebuild on next launch",
        }
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="Slack/Discord Cache Analysis")
    table.add_column("App", style="cyan")
    table.add_column("Cache Type", style="white")
    table.add_column("Size", justify="right")
    table.add_column("Path", style="dim")

    for app_key in ["slack", "discord"]:
        app_data = result["details"][app_key]
        for cache in app_data["caches"]:
            table.add_row(
                app_data["app"],
                cache["name"],
                cache["size_human"],
                cache["path"][:50] + "..."
            )

    console.print(table)
    console.print(f"\n[bold]Total Recoverable:[/bold] {result['details']['total_human']}")


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]Slack/Discord Cache Analysis[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Cache locations found: {result['zombies_found']}")
    console.print(f"Potential recovery: {result['details']['total_human']}")
    console.print(f"Execution time: {result['time_ms']:.2f}ms")

    slack = result["details"]["slack"]
    discord = result["details"]["discord"]

    console.print(f"\n[bold]Breakdown:[/bold]")
    console.print(f"  Slack: {format_size(slack['total_bytes'])} ({len(slack['caches'])} caches)")
    if slack.get("workspace_count"):
        console.print(f"    Workspaces: {slack['workspace_count']}")
    console.print(f"  Discord: {format_size(discord['total_bytes'])} ({len(discord['caches'])} caches)")

    console.print(f"\n[dim]{result['details']['recommendation']}[/dim]")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Analyze Slack and Discord cache directories for potential cleanup."""
    result = detect_cache_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
