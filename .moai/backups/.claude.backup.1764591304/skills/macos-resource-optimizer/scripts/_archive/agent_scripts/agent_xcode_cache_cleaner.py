#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Xcode Artifact Hunter - Agent 16

Finds Xcode build artifacts and old simulators consuming disk space.
Self-contained with all dependencies inline (PEP 723).

Scans:
- ~/Library/Developer/Xcode/DerivedData (build artifacts)
- ~/Library/Developer/Xcode/Archives (app archives)
- ~/Library/Developer/CoreSimulator/Devices (iOS simulators)
- ~/Library/Developer/Xcode/iOS DeviceSupport (device support files)
- ~/Library/Developer/Xcode/watchOS DeviceSupport
- ~/Library/Developer/Xcode/tvOS DeviceSupport

Recovery: 20-100 GB disk space (especially DerivedData and simulators)
Note: Informational only, does NOT delete artifacts
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


# Xcode artifact locations
XCODE_ARTIFACTS = {
    'derived_data': {
        'path': '~/Library/Developer/Xcode/DerivedData',
        'description': 'Xcode build artifacts (safe to delete)',
        'cleanup_cmd': 'rm -rf ~/Library/Developer/Xcode/DerivedData/*',
        'safe_to_delete': True
    },
    'archives': {
        'path': '~/Library/Developer/Xcode/Archives',
        'description': 'App archives (keep for App Store submissions)',
        'cleanup_cmd': 'Xcode > Window > Organizer > Archives',
        'safe_to_delete': False
    },
    'ios_simulators': {
        'path': '~/Library/Developer/CoreSimulator/Devices',
        'description': 'iOS Simulator devices',
        'cleanup_cmd': 'xcrun simctl delete unavailable',
        'safe_to_delete': False
    },
    'ios_device_support': {
        'path': '~/Library/Developer/Xcode/iOS DeviceSupport',
        'description': 'iOS device support files',
        'cleanup_cmd': 'rm -rf "~/Library/Developer/Xcode/iOS DeviceSupport"',
        'safe_to_delete': True
    },
    'watchos_device_support': {
        'path': '~/Library/Developer/Xcode/watchOS DeviceSupport',
        'description': 'watchOS device support files',
        'cleanup_cmd': 'rm -rf "~/Library/Developer/Xcode/watchOS DeviceSupport"',
        'safe_to_delete': True
    },
    'tvos_device_support': {
        'path': '~/Library/Developer/Xcode/tvOS DeviceSupport',
        'description': 'tvOS device support files',
        'cleanup_cmd': 'rm -rf "~/Library/Developer/Xcode/tvOS DeviceSupport"',
        'safe_to_delete': True
    },
    'xcode_caches': {
        'path': '~/Library/Caches/com.apple.dt.Xcode',
        'description': 'Xcode application cache',
        'cleanup_cmd': 'rm -rf ~/Library/Caches/com.apple.dt.Xcode',
        'safe_to_delete': True
    },
    'previews': {
        'path': '~/Library/Developer/Xcode/UserData/Previews',
        'description': 'SwiftUI preview cache',
        'cleanup_cmd': 'rm -rf ~/Library/Developer/Xcode/UserData/Previews',
        'safe_to_delete': True
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
            timeout=120  # Longer timeout for large directories
        )
        if result.returncode == 0:
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        return 0
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return 0


def count_items_in_directory(path: Path) -> int:
    """Count number of items in a directory."""
    if not path.exists():
        return 0

    try:
        return len(list(path.iterdir()))
    except (OSError, PermissionError):
        return 0


def get_derived_data_projects(path: Path) -> List[Dict[str, Any]]:
    """Get list of projects in DerivedData with sizes."""
    projects = []

    if not path.exists():
        return projects

    try:
        for project_dir in path.iterdir():
            if project_dir.is_dir():
                size = get_directory_size(project_dir)
                if size > 0:
                    # Get modification time
                    try:
                        mtime = datetime.fromtimestamp(project_dir.stat().st_mtime)
                        age_days = (datetime.now() - mtime).days
                    except OSError:
                        age_days = -1

                    projects.append({
                        'name': project_dir.name.split('-')[0],  # Remove UUID suffix
                        'path': str(project_dir),
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'size_gb': round(size / (1024 * 1024 * 1024), 2),
                        'age_days': age_days
                    })
    except (OSError, PermissionError):
        pass

    return sorted(projects, key=lambda x: x['size_bytes'], reverse=True)


def get_simulator_info() -> Dict[str, Any]:
    """Get iOS simulator information."""
    info = {
        'total_count': 0,
        'unavailable_count': 0,
        'simulators': []
    }

    # Try to get simulator list
    try:
        result = subprocess.run(
            ['xcrun', 'simctl', 'list', 'devices', '-j'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            import json as json_module
            data = json_module.loads(result.stdout)

            for runtime, devices in data.get('devices', {}).items():
                for device in devices:
                    info['total_count'] += 1
                    if device.get('isAvailable') == False:
                        info['unavailable_count'] += 1
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    return info


def scan_xcode_artifacts() -> List[Dict[str, Any]]:
    """Scan all Xcode artifact directories."""
    artifacts = []

    for artifact_name, artifact_info in XCODE_ARTIFACTS.items():
        path = Path(artifact_info['path']).expanduser()

        if path.exists():
            size = get_directory_size(path)
            item_count = count_items_in_directory(path)

            if size > 0:
                artifact_data = {
                    'name': artifact_name,
                    'path': str(path),
                    'description': artifact_info['description'],
                    'cleanup_cmd': artifact_info['cleanup_cmd'],
                    'safe_to_delete': artifact_info['safe_to_delete'],
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'size_gb': round(size / (1024 * 1024 * 1024), 2),
                    'item_count': item_count
                }

                # Add extra info for DerivedData
                if artifact_name == 'derived_data':
                    artifact_data['projects'] = get_derived_data_projects(path)[:10]  # Top 10

                artifacts.append(artifact_data)

    return sorted(artifacts, key=lambda x: x['size_bytes'], reverse=True)


def calculate_totals(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total recoverable space."""
    total_bytes = sum(a['size_bytes'] for a in artifacts)
    safe_bytes = sum(a['size_bytes'] for a in artifacts if a.get('safe_to_delete', False))

    return {
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 * 1024 * 1024), 2),
        'safe_to_delete_bytes': safe_bytes,
        'safe_to_delete_gb': round(safe_bytes / (1024 * 1024 * 1024), 2),
        'artifact_count': len(artifacts)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed project listings')
def main(format: str, verbose: bool):
    """
    Xcode Artifact Hunter - Agent 16

    Finds Xcode build artifacts for disk space recovery.
    Informational only - does NOT delete artifacts.
    """
    start_time = time.time()

    # Scan Xcode artifacts
    artifacts = scan_xcode_artifacts()
    totals = calculate_totals(artifacts)
    simulator_info = get_simulator_info()

    execution_time = round((time.time() - start_time) * 1000, 2)

    if format == 'json':
        result = {
            'agent': 'xcode_artifact_hunter',
            'agent_number': 16,
            'category': 'disk_cleanup',
            'zombies_found': totals['artifact_count'],
            'memory_freed_mb': 0,
            'disk_freed_gb': totals['total_gb'],
            'status': 'success',
            'time_ms': execution_time,
            'pids': [],
            'disk_recovery': {
                'total_gb': totals['total_gb'],
                'safe_to_delete_gb': totals['safe_to_delete_gb'],
                'artifact_count': totals['artifact_count']
            },
            'simulator_info': simulator_info,
            'artifacts': [{
                'name': a['name'],
                'description': a['description'],
                'size_gb': a['size_gb'],
                'size_mb': a['size_mb'],
                'item_count': a['item_count'],
                'safe_to_delete': a['safe_to_delete'],
                'cleanup_cmd': a['cleanup_cmd'],
                'projects': a.get('projects', []) if verbose else []
            } for a in artifacts],
            'note': 'Items marked safe_to_delete can be removed without data loss'
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 16: Xcode Artifact Hunter[/bold cyan]\n")

        if artifacts:
            artifact_table = Table(title=f"Xcode Artifacts Found ({totals['artifact_count']} locations)")
            artifact_table.add_column("Artifact", style="yellow")
            artifact_table.add_column("Items", justify="right", style="cyan")
            artifact_table.add_column("Size", justify="right", style="red")
            artifact_table.add_column("Safe?", justify="center", style="green")

            for artifact in artifacts:
                size_str = f"{artifact['size_gb']:.1f} GB" if artifact['size_gb'] >= 1 else f"{artifact['size_mb']:.0f} MB"
                safe_str = "Yes" if artifact['safe_to_delete'] else "Caution"
                artifact_table.add_row(
                    artifact['name'],
                    str(artifact['item_count']),
                    size_str,
                    safe_str
                )

            artifact_table.add_row(
                "[bold]TOTAL[/bold]",
                "",
                f"[bold]{totals['total_gb']:.1f} GB[/bold]",
                ""
            )

            console.print(artifact_table)

            # Simulator info
            if simulator_info['total_count'] > 0:
                console.print(f"\n[bold]iOS Simulators:[/bold] {simulator_info['total_count']} total, {simulator_info['unavailable_count']} unavailable")

            if verbose:
                # Show DerivedData projects
                derived = next((a for a in artifacts if a['name'] == 'derived_data'), None)
                if derived and derived.get('projects'):
                    console.print("\n[bold]Top DerivedData Projects:[/bold]")
                    for proj in derived['projects'][:5]:
                        size_str = f"{proj['size_gb']:.1f} GB" if proj['size_gb'] >= 1 else f"{proj['size_mb']:.0f} MB"
                        console.print(f"  {proj['name']}: {size_str} (age: {proj['age_days']}d)")
        else:
            console.print("[green]No Xcode artifacts found! (Is Xcode installed?)[/green]")

        console.print(f"\n[dim]Note: This is informational only. No files were deleted.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
