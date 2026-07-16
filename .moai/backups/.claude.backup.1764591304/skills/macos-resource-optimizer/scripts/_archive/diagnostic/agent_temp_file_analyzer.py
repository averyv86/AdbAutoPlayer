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
Temp File Analyzer - Agent 13
Analyzes temporary files and caches for disk space recovery.

Detects:
- /tmp files older than 7 days
- ~/Library/Caches size analysis
- Orphaned node_modules, target/, .next/, dist/
- Build artifacts in non-project directories

Recovery: 10-30 GB disk space
Note: Informational only, does NOT delete files or kill PIDs
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.table import Table

console = Console()

# Thresholds
TEMP_FILE_AGE_DAYS = 7
LARGE_CACHE_THRESHOLD_MB = 1000  # 1GB
ORPHANED_BUILD_ARTIFACTS_MB = 100  # 100MB minimum


def get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    try:
        result = subprocess.run(
            ['du', '-sk', str(path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # du -sk returns size in KB
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        return 0
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return 0


def analyze_tmp_directory() -> Dict[str, Any]:
    """
    Analyze /tmp for old files (7+ days).
    Returns summary of recoverable space.
    """
    tmp_path = Path('/tmp')
    if not tmp_path.exists():
        return {'total_files': 0, 'total_bytes': 0, 'files': []}

    cutoff_date = datetime.now() - timedelta(days=TEMP_FILE_AGE_DAYS)
    old_files = []
    total_bytes = 0

    try:
        for item in tmp_path.iterdir():
            try:
                # Get file stats
                stat = item.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)

                if mtime < cutoff_date:
                    file_size = stat.st_size
                    if item.is_dir():
                        # For directories, get total size
                        file_size = get_directory_size(item)

                    total_bytes += file_size
                    old_files.append({
                        'path': str(item),
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'age_days': (datetime.now() - mtime).days,
                        'type': 'directory' if item.is_dir() else 'file'
                    })

            except (OSError, PermissionError):
                continue

    except (OSError, PermissionError):
        pass

    return {
        'total_files': len(old_files),
        'total_bytes': total_bytes,
        'total_mb': round(total_bytes / (1024 * 1024), 2),
        'files': sorted(old_files, key=lambda x: x['size_mb'], reverse=True)[:20]  # Top 20
    }


def analyze_library_caches() -> Dict[str, Any]:
    """
    Analyze ~/Library/Caches for large caches.
    Returns breakdown by application.
    """
    home = Path.home()
    caches_path = home / 'Library' / 'Caches'

    if not caches_path.exists():
        return {'total_bytes': 0, 'caches': []}

    large_caches = []
    total_bytes = 0

    try:
        for cache_dir in caches_path.iterdir():
            if not cache_dir.is_dir():
                continue

            try:
                cache_size = get_directory_size(cache_dir)
                cache_mb = cache_size / (1024 * 1024)

                if cache_mb > LARGE_CACHE_THRESHOLD_MB:
                    total_bytes += cache_size
                    large_caches.append({
                        'name': cache_dir.name,
                        'path': str(cache_dir),
                        'size_mb': round(cache_mb, 2),
                        'size_gb': round(cache_mb / 1024, 2)
                    })

            except (OSError, PermissionError):
                continue

    except (OSError, PermissionError):
        pass

    return {
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 ** 3), 2),
        'caches': sorted(large_caches, key=lambda x: x['size_mb'], reverse=True)[:15]  # Top 15
    }


def find_orphaned_build_artifacts() -> Dict[str, Any]:
    """
    Find orphaned build artifacts (node_modules, target/, dist/, .next/).
    Checks common development directories.
    """
    home = Path.home()
    search_paths = [
        home / 'Documents',
        home / 'Desktop',
        home / 'Downloads',
    ]

    build_patterns = {
        'node_modules': 'Node.js dependencies',
        'target': 'Rust/Java build output',
        '.next': 'Next.js build cache',
        'dist': 'Build distribution',
        'build': 'Generic build output',
        '__pycache__': 'Python bytecode cache',
        '.turbo': 'Turborepo cache',
        '.cache': 'Generic cache'
    }

    orphaned_artifacts = []
    total_bytes = 0

    for base_path in search_paths:
        if not base_path.exists():
            continue

        try:
            # Limit depth to avoid scanning entire filesystem
            for pattern_name, description in build_patterns.items():
                try:
                    # Use find command for performance
                    result = subprocess.run(
                        ['find', str(base_path), '-maxdepth', '4', '-type', 'd', '-name', pattern_name],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode != 0:
                        continue

                    for artifact_path in result.stdout.strip().split('\n'):
                        if not artifact_path:
                            continue

                        artifact_path = Path(artifact_path)
                        if not artifact_path.exists():
                            continue

                        # Check if it's in an active project (has package.json, Cargo.toml, etc.)
                        parent = artifact_path.parent
                        is_active_project = any([
                            (parent / 'package.json').exists(),
                            (parent / 'Cargo.toml').exists(),
                            (parent / 'pyproject.toml').exists(),
                            (parent / '.git').exists(),
                        ])

                        # Only flag orphaned artifacts (no project markers)
                        if not is_active_project:
                            artifact_size = get_directory_size(artifact_path)
                            artifact_mb = artifact_size / (1024 * 1024)

                            if artifact_mb > ORPHANED_BUILD_ARTIFACTS_MB:
                                total_bytes += artifact_size
                                orphaned_artifacts.append({
                                    'path': str(artifact_path),
                                    'type': pattern_name,
                                    'description': description,
                                    'size_mb': round(artifact_mb, 2),
                                    'size_gb': round(artifact_mb / 1024, 2)
                                })

                except (subprocess.TimeoutExpired, OSError, PermissionError):
                    continue

        except (OSError, PermissionError):
            continue

    return {
        'total_artifacts': len(orphaned_artifacts),
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 ** 3), 2),
        'artifacts': sorted(orphaned_artifacts, key=lambda x: x['size_mb'], reverse=True)[:20]  # Top 20
    }


def calculate_disk_recovery() -> Dict[str, Any]:
    """
    Main analysis function for temporary file cleanup.
    Returns categorized disk space recovery data.
    """
    # Analyze different categories
    tmp_analysis = analyze_tmp_directory()
    cache_analysis = analyze_library_caches()
    build_artifacts = find_orphaned_build_artifacts()

    # Calculate total recoverable space
    total_recovery = (
        tmp_analysis['total_bytes'] +
        cache_analysis['total_bytes'] +
        build_artifacts['total_bytes']
    )

    return {
        'tmp_files': tmp_analysis,
        'library_caches': cache_analysis,
        'build_artifacts': build_artifacts,
        'total_recovery_bytes': total_recovery,
        'total_recovery_gb': round(total_recovery / (1024 ** 3), 2)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed file listings')
def main(format: str, verbose: bool):
    """
    Temp File Analyzer - Agent 13

    Analyzes temporary files and caches for disk space recovery.
    Informational only - does NOT delete files.
    """
    start_time = time.time()

    # Analyze disk usage
    results = calculate_disk_recovery()

    execution_time = round((time.time() - start_time) * 1000, 2)

    # Output results
    if format == 'json':
        result = {
            'agent': 'temp_file_analyzer',
            'agent_number': 13,
            'category': 'disk_cleanup',
            'zombies_found': 0,  # This agent doesn't find zombies (PIDs)
            'total_memory_bytes': 0,  # This agent analyzes disk, not RAM
            'execution_time_ms': execution_time,
            'pids': [],  # No PIDs to kill
            'disk_recovery': {
                'total_gb': results['total_recovery_gb'],
                'total_bytes': results['total_recovery_bytes'],
                'breakdown': {
                    'tmp_files_gb': round(results['tmp_files']['total_bytes'] / (1024 ** 3), 2),
                    'library_caches_gb': results['library_caches']['total_gb'],
                    'build_artifacts_gb': results['build_artifacts']['total_gb']
                }
            },
            'details': {
                'tmp_files': {
                    'count': results['tmp_files']['total_files'],
                    'files': results['tmp_files']['files'] if verbose else []
                },
                'library_caches': {
                    'count': len(results['library_caches']['caches']),
                    'caches': results['library_caches']['caches'] if verbose else []
                },
                'build_artifacts': {
                    'count': results['build_artifacts']['total_artifacts'],
                    'artifacts': results['build_artifacts']['artifacts'] if verbose else []
                }
            }
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 13: Temp File Analyzer[/bold cyan]\n")

        # Summary table
        summary_table = Table(title="Disk Space Recovery Summary")
        summary_table.add_column("Category", style="yellow")
        summary_table.add_column("Items", justify="right", style="cyan")
        summary_table.add_column("Recoverable Space", justify="right", style="green")

        summary_table.add_row(
            "/tmp (>7 days)",
            str(results['tmp_files']['total_files']),
            f"{round(results['tmp_files']['total_bytes'] / (1024 ** 3), 2)} GB"
        )
        summary_table.add_row(
            "~/Library/Caches",
            str(len(results['library_caches']['caches'])),
            f"{results['library_caches']['total_gb']} GB"
        )
        summary_table.add_row(
            "Orphaned Build Artifacts",
            str(results['build_artifacts']['total_artifacts']),
            f"{results['build_artifacts']['total_gb']} GB"
        )
        summary_table.add_row(
            "[bold]TOTAL RECOVERY[/bold]",
            "",
            f"[bold]{results['total_recovery_gb']} GB[/bold]"
        )

        console.print(summary_table)

        if verbose:
            # Detailed tables
            if results['library_caches']['caches']:
                console.print("\n[bold]Top Library Caches:[/bold]")
                cache_table = Table()
                cache_table.add_column("Application", style="yellow")
                cache_table.add_column("Size", justify="right", style="red")

                for cache in results['library_caches']['caches'][:10]:
                    cache_table.add_row(cache['name'], f"{cache['size_gb']} GB")

                console.print(cache_table)

            if results['build_artifacts']['artifacts']:
                console.print("\n[bold]Top Orphaned Build Artifacts:[/bold]")
                artifact_table = Table()
                artifact_table.add_column("Path", style="yellow")
                artifact_table.add_column("Type", style="cyan")
                artifact_table.add_column("Size", justify="right", style="red")

                for artifact in results['build_artifacts']['artifacts'][:10]:
                    artifact_table.add_row(
                        artifact['path'][:60] + "..." if len(artifact['path']) > 60 else artifact['path'],
                        artifact['type'],
                        f"{artifact['size_gb']} GB" if artifact['size_gb'] >= 1 else f"{artifact['size_mb']} MB"
                    )

                console.print(artifact_table)

        console.print(f"\n[dim]Note: This is informational only. No files were deleted.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
