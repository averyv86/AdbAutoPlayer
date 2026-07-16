#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Developer Cache Hunter - Agent 15

Finds developer cache directories consuming significant disk space.
Self-contained with all dependencies inline (PEP 723).

Scans:
- ~/.npm/_cacache (npm cache)
- ~/Library/Caches/Homebrew (Homebrew downloads)
- ~/.cache/pip (pip cache)
- ~/Library/Caches/CocoaPods (CocoaPods cache)
- ~/.cargo/registry (Rust crates)
- ~/.cache/yarn (Yarn cache)
- ~/.bun/install/cache (Bun cache)

Recovery: 5-50 GB disk space
Note: Informational only, does NOT delete caches
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import click
from rich.console import Console
from rich.table import Table

console = Console()


# Developer cache locations to scan
DEVELOPER_CACHES = {
    'npm': {
        'paths': ['~/.npm/_cacache', '~/.npm'],
        'description': 'NPM package cache',
        'cleanup_cmd': 'npm cache clean --force'
    },
    'homebrew': {
        'paths': ['~/Library/Caches/Homebrew'],
        'description': 'Homebrew downloads cache',
        'cleanup_cmd': 'brew cleanup -s'
    },
    'pip': {
        'paths': ['~/.cache/pip', '~/Library/Caches/pip'],
        'description': 'Python pip cache',
        'cleanup_cmd': 'pip cache purge'
    },
    'cocoapods': {
        'paths': ['~/Library/Caches/CocoaPods'],
        'description': 'CocoaPods cache',
        'cleanup_cmd': 'pod cache clean --all'
    },
    'cargo': {
        'paths': ['~/.cargo/registry', '~/.cargo/git'],
        'description': 'Rust cargo crates cache',
        'cleanup_cmd': 'cargo cache --autoclean'
    },
    'yarn': {
        'paths': ['~/.cache/yarn', '~/Library/Caches/Yarn'],
        'description': 'Yarn package cache',
        'cleanup_cmd': 'yarn cache clean'
    },
    'bun': {
        'paths': ['~/.bun/install/cache'],
        'description': 'Bun package cache',
        'cleanup_cmd': 'bun pm cache rm'
    },
    'pnpm': {
        'paths': ['~/Library/pnpm/store', '~/.local/share/pnpm/store'],
        'description': 'PNPM package store',
        'cleanup_cmd': 'pnpm store prune'
    },
    'gradle': {
        'paths': ['~/.gradle/caches'],
        'description': 'Gradle build cache',
        'cleanup_cmd': 'rm -rf ~/.gradle/caches/*'
    },
    'maven': {
        'paths': ['~/.m2/repository'],
        'description': 'Maven repository cache',
        'cleanup_cmd': 'mvn dependency:purge-local-repository'
    },
    'go': {
        'paths': ['~/go/pkg/mod/cache'],
        'description': 'Go module cache',
        'cleanup_cmd': 'go clean -modcache'
    },
    'composer': {
        'paths': ['~/.composer/cache', '~/Library/Caches/composer'],
        'description': 'PHP Composer cache',
        'cleanup_cmd': 'composer clear-cache'
    }
}


def get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes using du command."""
    if not path.exists():
        return 0

    try:
        result = subprocess.run(
            ['du', '-sk', str(path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            # du -sk returns size in KB
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        return 0
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return 0


def scan_developer_caches() -> List[Dict[str, Any]]:
    """Scan all developer cache directories."""
    caches = []

    for cache_name, cache_info in DEVELOPER_CACHES.items():
        total_size = 0
        found_paths = []

        for path_str in cache_info['paths']:
            path = Path(path_str).expanduser()

            if path.exists():
                size = get_directory_size(path)
                if size > 0:
                    total_size += size
                    found_paths.append({
                        'path': str(path),
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'size_gb': round(size / (1024 * 1024 * 1024), 2)
                    })

        if total_size > 0:
            caches.append({
                'name': cache_name,
                'description': cache_info['description'],
                'cleanup_cmd': cache_info['cleanup_cmd'],
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'paths': found_paths
            })

    return sorted(caches, key=lambda x: x['total_size_bytes'], reverse=True)


def calculate_totals(caches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total recoverable space."""
    total_bytes = sum(c['total_size_bytes'] for c in caches)

    return {
        'total_bytes': total_bytes,
        'total_mb': round(total_bytes / (1024 * 1024), 2),
        'total_gb': round(total_bytes / (1024 * 1024 * 1024), 2),
        'cache_count': len(caches)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed path listings')
def main(format: str, verbose: bool):
    """
    Developer Cache Hunter - Agent 15

    Finds developer cache directories for disk space recovery.
    Informational only - does NOT delete caches.
    """
    start_time = time.time()

    # Scan developer caches
    caches = scan_developer_caches()
    totals = calculate_totals(caches)

    execution_time = round((time.time() - start_time) * 1000, 2)

    if format == 'json':
        result = {
            'agent': 'developer_cache_hunter',
            'agent_number': 15,
            'category': 'disk_cleanup',
            'zombies_found': totals['cache_count'],
            'memory_freed_mb': 0,  # This agent analyzes disk, not RAM
            'disk_freed_gb': totals['total_gb'],
            'status': 'success',
            'time_ms': execution_time,
            'pids': [],  # No PIDs to kill
            'disk_recovery': {
                'total_gb': totals['total_gb'],
                'total_mb': totals['total_mb'],
                'cache_count': totals['cache_count']
            },
            'caches': [{
                'name': c['name'],
                'description': c['description'],
                'size_gb': c['total_size_gb'],
                'size_mb': c['total_size_mb'],
                'cleanup_cmd': c['cleanup_cmd'],
                'paths': c['paths'] if verbose else []
            } for c in caches],
            'note': 'Use cleanup_cmd for each cache to reclaim space'
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 15: Developer Cache Hunter[/bold cyan]\n")

        if caches:
            cache_table = Table(title=f"Developer Caches Found ({totals['cache_count']} caches)")
            cache_table.add_column("Cache", style="yellow")
            cache_table.add_column("Description", style="cyan")
            cache_table.add_column("Size", justify="right", style="red")
            cache_table.add_column("Cleanup Command", style="green")

            for cache in caches:
                size_str = f"{cache['total_size_gb']:.1f} GB" if cache['total_size_gb'] >= 1 else f"{cache['total_size_mb']:.0f} MB"
                cache_table.add_row(
                    cache['name'],
                    cache['description'][:30],
                    size_str,
                    cache['cleanup_cmd'][:35] + "..." if len(cache['cleanup_cmd']) > 35 else cache['cleanup_cmd']
                )

            cache_table.add_row(
                "[bold]TOTAL[/bold]",
                "",
                f"[bold]{totals['total_gb']:.1f} GB[/bold]",
                ""
            )

            console.print(cache_table)

            if verbose:
                console.print("\n[bold]Detailed Paths:[/bold]")
                for cache in caches[:5]:  # Top 5 only
                    console.print(f"\n[yellow]{cache['name']}:[/yellow]")
                    for path_info in cache['paths']:
                        console.print(f"  {path_info['path']}: {path_info['size_mb']:.0f} MB")
        else:
            console.print("[green]No significant developer caches found![/green]")

        console.print(f"\n[dim]Note: This is informational only. No files were deleted.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
