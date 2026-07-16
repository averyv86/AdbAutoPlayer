#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Gradle/Maven Cache Hunter - Agent 17

Finds Gradle and Maven cache directories consuming disk space.
Self-contained with all dependencies inline (PEP 723).

Scans:
- ~/.gradle/caches (Gradle dependency cache)
- ~/.gradle/wrapper (Gradle wrapper distributions)
- ~/.gradle/daemon (Gradle daemon logs)
- ~/.m2/repository (Maven local repository)
- ~/Library/Android/sdk/build-cache (Android SDK build cache)
- ~/Library/Android/sdk/ndk (Android NDK installations)

Recovery: 15-50 GB disk space
Note: Informational only, does NOT delete caches
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table

console = Console()


# Gradle/Maven cache locations
JVM_BUILD_CACHES = {
    'gradle_caches': {
        'path': '~/.gradle/caches',
        'description': 'Gradle dependency cache',
        'cleanup_cmd': 'rm -rf ~/.gradle/caches/*',
        'priority': 'high'
    },
    'gradle_wrapper': {
        'path': '~/.gradle/wrapper/dists',
        'description': 'Gradle wrapper distributions',
        'cleanup_cmd': 'rm -rf ~/.gradle/wrapper/dists/*',
        'priority': 'medium'
    },
    'gradle_daemon': {
        'path': '~/.gradle/daemon',
        'description': 'Gradle daemon logs',
        'cleanup_cmd': 'rm -rf ~/.gradle/daemon/*',
        'priority': 'high'
    },
    'gradle_native': {
        'path': '~/.gradle/native',
        'description': 'Gradle native libraries',
        'cleanup_cmd': 'rm -rf ~/.gradle/native/*',
        'priority': 'low'
    },
    'maven_repository': {
        'path': '~/.m2/repository',
        'description': 'Maven local repository',
        'cleanup_cmd': 'mvn dependency:purge-local-repository',
        'priority': 'medium'
    },
    'android_build_cache': {
        'path': '~/Library/Android/sdk/build-cache',
        'description': 'Android SDK build cache',
        'cleanup_cmd': 'rm -rf ~/Library/Android/sdk/build-cache/*',
        'priority': 'high'
    },
    'android_ndk': {
        'path': '~/Library/Android/sdk/ndk',
        'description': 'Android NDK installations',
        'cleanup_cmd': 'SDK Manager > Remove old NDK versions',
        'priority': 'low'
    },
    'android_emulator': {
        'path': '~/.android/avd',
        'description': 'Android emulator AVD images',
        'cleanup_cmd': 'AVD Manager > Delete unused emulators',
        'priority': 'low'
    },
    'android_cache': {
        'path': '~/.android/cache',
        'description': 'Android debug cache',
        'cleanup_cmd': 'rm -rf ~/.android/cache/*',
        'priority': 'high'
    },
    'kotlin_daemon': {
        'path': '~/.kotlin/daemon',
        'description': 'Kotlin compiler daemon',
        'cleanup_cmd': 'rm -rf ~/.kotlin/daemon/*',
        'priority': 'high'
    },
    'sbt_cache': {
        'path': '~/.sbt',
        'description': 'Scala SBT cache',
        'cleanup_cmd': 'rm -rf ~/.sbt/*',
        'priority': 'medium'
    },
    'ivy_cache': {
        'path': '~/.ivy2/cache',
        'description': 'Apache Ivy cache',
        'cleanup_cmd': 'rm -rf ~/.ivy2/cache/*',
        'priority': 'medium'
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
            timeout=120
        )
        if result.returncode == 0:
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        return 0
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return 0


def get_directory_age(path: Path) -> int:
    """Get age of directory in days based on oldest modification."""
    if not path.exists():
        return -1

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days
    except OSError:
        return -1


def count_items_in_directory(path: Path, depth: int = 1) -> int:
    """Count items in directory at specified depth."""
    if not path.exists():
        return 0

    try:
        if depth == 1:
            return len(list(path.iterdir()))
        else:
            count = 0
            for item in path.iterdir():
                if item.is_dir():
                    count += len(list(item.iterdir()))
                else:
                    count += 1
            return count
    except (OSError, PermissionError):
        return 0


def get_gradle_version_info(path: Path) -> List[Dict[str, Any]]:
    """Get list of Gradle versions in wrapper/dists."""
    versions = []

    if not path.exists():
        return versions

    try:
        for version_dir in path.iterdir():
            if version_dir.is_dir():
                size = get_directory_size(version_dir)
                if size > 0:
                    versions.append({
                        'version': version_dir.name,
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2)
                    })
    except (OSError, PermissionError):
        pass

    return sorted(versions, key=lambda x: x['size_bytes'], reverse=True)


def scan_jvm_caches() -> List[Dict[str, Any]]:
    """Scan all JVM build cache directories."""
    caches = []

    for cache_name, cache_info in JVM_BUILD_CACHES.items():
        path = Path(cache_info['path']).expanduser()

        if path.exists():
            size = get_directory_size(path)

            if size > 0:
                item_count = count_items_in_directory(path)
                age_days = get_directory_age(path)

                cache_data = {
                    'name': cache_name,
                    'path': str(path),
                    'description': cache_info['description'],
                    'cleanup_cmd': cache_info['cleanup_cmd'],
                    'priority': cache_info['priority'],
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'size_gb': round(size / (1024 * 1024 * 1024), 2),
                    'item_count': item_count,
                    'age_days': age_days
                }

                # Add version info for Gradle wrapper
                if cache_name == 'gradle_wrapper':
                    cache_data['versions'] = get_gradle_version_info(path)

                caches.append(cache_data)

    return sorted(caches, key=lambda x: x['size_bytes'], reverse=True)


def calculate_totals(caches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total recoverable space."""
    total_bytes = sum(c['size_bytes'] for c in caches)
    high_priority_bytes = sum(c['size_bytes'] for c in caches if c.get('priority') == 'high')

    return {
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 * 1024 * 1024), 2),
        'high_priority_bytes': high_priority_bytes,
        'high_priority_gb': round(high_priority_bytes / (1024 * 1024 * 1024), 2),
        'cache_count': len(caches)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed version listings')
def main(format: str, verbose: bool):
    """
    Gradle/Maven Cache Hunter - Agent 17

    Finds JVM build caches for disk space recovery.
    Informational only - does NOT delete caches.
    """
    start_time = time.time()

    # Scan JVM caches
    caches = scan_jvm_caches()
    totals = calculate_totals(caches)

    execution_time = round((time.time() - start_time) * 1000, 2)

    if format == 'json':
        result = {
            'agent': 'gradle_maven_hunter',
            'agent_number': 17,
            'category': 'disk_cleanup',
            'zombies_found': totals['cache_count'],
            'memory_freed_mb': 0,
            'disk_freed_gb': totals['total_gb'],
            'status': 'success',
            'time_ms': execution_time,
            'pids': [],
            'disk_recovery': {
                'total_gb': totals['total_gb'],
                'high_priority_gb': totals['high_priority_gb'],
                'cache_count': totals['cache_count']
            },
            'caches': [{
                'name': c['name'],
                'description': c['description'],
                'size_gb': c['size_gb'],
                'size_mb': c['size_mb'],
                'item_count': c['item_count'],
                'priority': c['priority'],
                'cleanup_cmd': c['cleanup_cmd'],
                'versions': c.get('versions', []) if verbose else []
            } for c in caches],
            'note': 'High priority caches are safe to delete and regenerate on next build'
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 17: Gradle/Maven Cache Hunter[/bold cyan]\n")

        if caches:
            cache_table = Table(title=f"JVM Build Caches Found ({totals['cache_count']} locations)")
            cache_table.add_column("Cache", style="yellow")
            cache_table.add_column("Items", justify="right", style="cyan")
            cache_table.add_column("Size", justify="right", style="red")
            cache_table.add_column("Priority", justify="center", style="green")

            for cache in caches:
                size_str = f"{cache['size_gb']:.1f} GB" if cache['size_gb'] >= 1 else f"{cache['size_mb']:.0f} MB"
                priority_color = {
                    'high': 'green',
                    'medium': 'yellow',
                    'low': 'red'
                }.get(cache['priority'], 'white')

                cache_table.add_row(
                    cache['name'],
                    str(cache['item_count']),
                    size_str,
                    f"[{priority_color}]{cache['priority']}[/{priority_color}]"
                )

            cache_table.add_row(
                "[bold]TOTAL[/bold]",
                "",
                f"[bold]{totals['total_gb']:.1f} GB[/bold]",
                ""
            )

            console.print(cache_table)

            # Summary
            console.print(f"\n[bold]High Priority (safe to delete):[/bold] {totals['high_priority_gb']:.1f} GB")

            if verbose:
                # Show Gradle versions
                gradle_wrapper = next((c for c in caches if c['name'] == 'gradle_wrapper'), None)
                if gradle_wrapper and gradle_wrapper.get('versions'):
                    console.print("\n[bold]Gradle Wrapper Versions:[/bold]")
                    for ver in gradle_wrapper['versions'][:5]:
                        console.print(f"  {ver['version']}: {ver['size_mb']:.0f} MB")
        else:
            console.print("[green]No JVM build caches found! (Gradle/Maven not used?)[/green]")

        console.print(f"\n[dim]Note: This is informational only. No files were deleted.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
