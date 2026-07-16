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
VS Code Deep Cleanup Agent - Agent 12

Analyzes VS Code cache directories for potential space recovery.

Detection Targets:
- ~/Library/Application Support/Code/CachedData
- ~/Library/Application Support/Code/CachedExtensionVSIXs
- ~/Library/Application Support/Code/User/workspaceStorage
- ~/Library/Application Support/Code/logs
- ~/Library/Application Support/Code/CachedExtensions

Typical Recovery: 2-10GB depending on usage
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.table import Table

console = Console()

# VS Code base paths
VSCODE_BASE = Path.home() / "Library" / "Application Support" / "Code"
VSCODE_INSIDERS = Path.home() / "Library" / "Application Support" / "Code - Insiders"

# Cache directories with cleanup safety ratings
VSCODE_CACHE_DIRS = {
    "CachedData": {"safe": True, "desc": "Compiled bytecode cache"},
    "CachedExtensionVSIXs": {"safe": True, "desc": "Downloaded extension packages"},
    "CachedExtensions": {"safe": True, "desc": "Cached extension metadata"},
    "User/workspaceStorage": {"safe": False, "desc": "Workspace-specific data"},
    "logs": {"safe": True, "desc": "Application logs"},
    "Cache": {"safe": True, "desc": "General cache"},
    "GPUCache": {"safe": True, "desc": "GPU shader cache"},
    "Service Worker": {"safe": True, "desc": "Service worker cache"},
}


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


def count_items(path: Path) -> int:
    """Count items in a directory."""
    try:
        return sum(1 for _ in path.iterdir()) if path.exists() else 0
    except (OSError, PermissionError):
        return 0


def get_oldest_file_age(path: Path) -> int:
    """Get age of oldest file in days."""
    oldest = time.time()
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                mtime = entry.stat().st_mtime
                if mtime < oldest:
                    oldest = mtime
    except (OSError, PermissionError):
        pass
    return int((time.time() - oldest) / 86400)


def analyze_vscode_installation(base_path: Path, name: str, verbose: bool = False) -> Dict[str, Any]:
    """Analyze a VS Code installation's cache directories."""
    result = {
        "installation": name,
        "base_path": str(base_path),
        "exists": base_path.exists(),
        "caches": [],
        "total_bytes": 0,
        "safe_cleanup_bytes": 0,
        "workspace_count": 0,
    }

    if not base_path.exists():
        return result

    for cache_dir, info in VSCODE_CACHE_DIRS.items():
        cache_path = base_path / cache_dir
        if cache_path.exists():
            size = get_directory_size(cache_path)
            item_count = count_items(cache_path)
            age_days = get_oldest_file_age(cache_path)

            cache_info = {
                "name": cache_dir,
                "path": str(cache_path),
                "size_bytes": size,
                "size_human": format_size(size),
                "item_count": item_count,
                "oldest_days": age_days,
                "safe_to_clean": info["safe"],
                "description": info["desc"],
            }
            result["caches"].append(cache_info)
            result["total_bytes"] += size

            if info["safe"]:
                result["safe_cleanup_bytes"] += size

            if verbose:
                safety = "[green]SAFE[/green]" if info["safe"] else "[yellow]CAUTION[/yellow]"
                console.print(f"  {safety} {cache_dir}: {format_size(size)} ({item_count} items)")

    # Count workspaces
    workspace_path = base_path / "User" / "workspaceStorage"
    if workspace_path.exists():
        result["workspace_count"] = count_items(workspace_path)

    return result


def detect_vscode_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Main detection function for VS Code caches."""
    start_time = time.time()

    if verbose:
        console.print("[cyan]Scanning VS Code cache directories...[/cyan]\n")

    installations = []

    # Check standard VS Code
    if VSCODE_BASE.exists():
        if verbose:
            console.print("[bold]VS Code (Standard):[/bold]")
        installations.append(analyze_vscode_installation(VSCODE_BASE, "VS Code", verbose))

    # Check VS Code Insiders
    if VSCODE_INSIDERS.exists():
        if verbose:
            console.print("\n[bold]VS Code Insiders:[/bold]")
        installations.append(analyze_vscode_installation(VSCODE_INSIDERS, "VS Code Insiders", verbose))

    total_bytes = sum(i["total_bytes"] for i in installations)
    safe_bytes = sum(i["safe_cleanup_bytes"] for i in installations)
    total_caches = sum(len(i["caches"]) for i in installations)

    execution_time = (time.time() - start_time) * 1000

    return {
        "zombies_found": total_caches,
        "memory_freed_mb": round(safe_bytes / (1024 * 1024), 1),
        "actions_taken": total_caches,
        "status": "success",
        "time_ms": round(execution_time, 2),
        "details": {
            "installations": installations,
            "total_bytes": total_bytes,
            "total_human": format_size(total_bytes),
            "safe_cleanup_bytes": safe_bytes,
            "safe_cleanup_human": format_size(safe_bytes),
            "recommendation": "CachedData and CachedExtensionVSIXs are safe to delete",
        }
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    table = Table(title="VS Code Cache Analysis")
    table.add_column("Installation", style="cyan")
    table.add_column("Cache Type", style="white")
    table.add_column("Size", justify="right")
    table.add_column("Items", justify="right")
    table.add_column("Age (days)", justify="right")
    table.add_column("Safe", justify="center")

    for inst in result["details"]["installations"]:
        for cache in inst["caches"]:
            safe_str = "[green]Yes[/green]" if cache["safe_to_clean"] else "[yellow]No[/yellow]"
            table.add_row(
                inst["installation"],
                cache["name"],
                cache["size_human"],
                str(cache["item_count"]),
                str(cache["oldest_days"]),
                safe_str
            )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {result['details']['total_human']}")
    console.print(f"[bold]Safe to Clean:[/bold] {result['details']['safe_cleanup_human']}")


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]VS Code Deep Cleanup Analysis[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Cache locations found: {result['zombies_found']}")
    console.print(f"Total cache size: {result['details']['total_human']}")
    console.print(f"Safe to clean: {result['details']['safe_cleanup_human']}")
    console.print(f"Execution time: {result['time_ms']:.2f}ms")

    console.print(f"\n[bold]By Installation:[/bold]")
    for inst in result["details"]["installations"]:
        console.print(f"  {inst['installation']}: {format_size(inst['total_bytes'])}")
        console.print(f"    Workspaces: {inst['workspace_count']}")
        console.print(f"    Safe cleanup: {format_size(inst['safe_cleanup_bytes'])}")

    console.print(f"\n[dim]{result['details']['recommendation']}[/dim]")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Analyze VS Code cache directories for potential cleanup."""
    result = detect_vscode_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
