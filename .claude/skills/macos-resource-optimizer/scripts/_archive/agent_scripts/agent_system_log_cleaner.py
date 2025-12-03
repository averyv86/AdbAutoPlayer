#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
System Log Hunter - Agent 18

Finds large system logs consuming disk space.
Self-contained with all dependencies inline (PEP 723).

Scans:
- /var/log (system logs - requires sudo for full access)
- ~/Library/Logs (user application logs)
- /Library/Logs (system-wide application logs)
- ~/Library/Logs/DiagnosticReports (crash reports)
- /private/var/log (macOS system logs)

Recovery: 1-10 GB disk space
Note: Informational only, does NOT delete logs
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


# Minimum size threshold for reporting (100 MB)
MIN_LOG_SIZE_MB = 100
# Large file threshold (100 MB)
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024


# Log locations to scan
LOG_LOCATIONS = {
    'user_logs': {
        'path': '~/Library/Logs',
        'description': 'User application logs',
        'cleanup_cmd': 'rm -rf ~/Library/Logs/*',
        'requires_sudo': False
    },
    'diagnostic_reports': {
        'path': '~/Library/Logs/DiagnosticReports',
        'description': 'Crash and diagnostic reports',
        'cleanup_cmd': 'rm -rf ~/Library/Logs/DiagnosticReports/*',
        'requires_sudo': False
    },
    'system_logs': {
        'path': '/Library/Logs',
        'description': 'System-wide application logs',
        'cleanup_cmd': 'sudo rm -rf /Library/Logs/*',
        'requires_sudo': True
    },
    'var_log': {
        'path': '/var/log',
        'description': 'Unix system logs',
        'cleanup_cmd': 'sudo rm /var/log/*.log',
        'requires_sudo': True
    },
    'private_var_log': {
        'path': '/private/var/log',
        'description': 'macOS private logs',
        'cleanup_cmd': 'sudo rm /private/var/log/*.log',
        'requires_sudo': True
    },
    'asl_logs': {
        'path': '/private/var/log/asl',
        'description': 'Apple System Logger archives',
        'cleanup_cmd': 'sudo rm /private/var/log/asl/*.asl',
        'requires_sudo': True
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
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        return 0
    except (subprocess.TimeoutExpired, ValueError, IndexError, PermissionError):
        return 0


def find_large_log_files(path: Path, threshold: int = LARGE_FILE_THRESHOLD) -> List[Dict[str, Any]]:
    """Find log files larger than threshold."""
    large_files = []

    if not path.exists():
        return large_files

    try:
        # Use find command for efficiency
        result = subprocess.run(
            ['find', str(path), '-type', 'f', '-size', f'+{threshold // (1024 * 1024)}M'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            for file_path in result.stdout.strip().split('\n'):
                if not file_path:
                    continue

                try:
                    file_path = Path(file_path)
                    if file_path.exists():
                        size = file_path.stat().st_size
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        age_days = (datetime.now() - mtime).days

                        large_files.append({
                            'path': str(file_path),
                            'name': file_path.name,
                            'size_bytes': size,
                            'size_mb': round(size / (1024 * 1024), 2),
                            'age_days': age_days
                        })
                except (OSError, PermissionError):
                    continue
    except (subprocess.TimeoutExpired, PermissionError):
        pass

    return sorted(large_files, key=lambda x: x['size_bytes'], reverse=True)


def count_log_files(path: Path) -> int:
    """Count number of log files in directory."""
    if not path.exists():
        return 0

    try:
        result = subprocess.run(
            ['find', str(path), '-type', 'f', '-name', '*.log'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return len([l for l in result.stdout.strip().split('\n') if l])
        return 0
    except (subprocess.TimeoutExpired, PermissionError):
        return 0


def scan_log_locations() -> List[Dict[str, Any]]:
    """Scan all log locations."""
    logs = []

    for log_name, log_info in LOG_LOCATIONS.items():
        path = Path(log_info['path']).expanduser()

        if path.exists():
            size = get_directory_size(path)
            size_mb = size / (1024 * 1024)

            # Only report if significant size or explicitly checking all
            if size_mb >= MIN_LOG_SIZE_MB or size > 0:
                file_count = count_log_files(path)
                large_files = find_large_log_files(path)

                logs.append({
                    'name': log_name,
                    'path': str(path),
                    'description': log_info['description'],
                    'cleanup_cmd': log_info['cleanup_cmd'],
                    'requires_sudo': log_info['requires_sudo'],
                    'size_bytes': size,
                    'size_mb': round(size_mb, 2),
                    'size_gb': round(size / (1024 * 1024 * 1024), 2),
                    'file_count': file_count,
                    'large_files': large_files[:5]  # Top 5 large files
                })

    return sorted(logs, key=lambda x: x['size_bytes'], reverse=True)


def calculate_totals(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total recoverable space."""
    total_bytes = sum(l['size_bytes'] for l in logs)
    user_bytes = sum(l['size_bytes'] for l in logs if not l.get('requires_sudo', False))

    return {
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 * 1024 * 1024), 2),
        'user_accessible_bytes': user_bytes,
        'user_accessible_gb': round(user_bytes / (1024 * 1024 * 1024), 2),
        'location_count': len(logs)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed file listings')
def main(format: str, verbose: bool):
    """
    System Log Hunter - Agent 18

    Finds large system logs for disk space recovery.
    Informational only - does NOT delete logs.
    """
    start_time = time.time()

    # Scan log locations
    logs = scan_log_locations()
    totals = calculate_totals(logs)

    execution_time = round((time.time() - start_time) * 1000, 2)

    if format == 'json':
        result = {
            'agent': 'system_log_hunter',
            'agent_number': 18,
            'category': 'disk_cleanup',
            'zombies_found': totals['location_count'],
            'memory_freed_mb': 0,
            'disk_freed_gb': totals['total_gb'],
            'status': 'success',
            'time_ms': execution_time,
            'pids': [],
            'disk_recovery': {
                'total_gb': totals['total_gb'],
                'user_accessible_gb': totals['user_accessible_gb'],
                'location_count': totals['location_count']
            },
            'logs': [{
                'name': l['name'],
                'description': l['description'],
                'size_gb': l['size_gb'],
                'size_mb': l['size_mb'],
                'file_count': l['file_count'],
                'requires_sudo': l['requires_sudo'],
                'cleanup_cmd': l['cleanup_cmd'],
                'large_files': l['large_files'] if verbose else []
            } for l in logs],
            'note': 'Some locations require sudo access for full cleanup'
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 18: System Log Hunter[/bold cyan]\n")

        if logs:
            log_table = Table(title=f"Log Locations Found ({totals['location_count']} locations)")
            log_table.add_column("Location", style="yellow")
            log_table.add_column("Files", justify="right", style="cyan")
            log_table.add_column("Size", justify="right", style="red")
            log_table.add_column("Sudo?", justify="center", style="green")

            for log in logs:
                size_str = f"{log['size_gb']:.1f} GB" if log['size_gb'] >= 1 else f"{log['size_mb']:.0f} MB"
                sudo_str = "Yes" if log['requires_sudo'] else "No"

                log_table.add_row(
                    log['name'],
                    str(log['file_count']),
                    size_str,
                    sudo_str
                )

            log_table.add_row(
                "[bold]TOTAL[/bold]",
                "",
                f"[bold]{totals['total_gb']:.1f} GB[/bold]",
                ""
            )

            console.print(log_table)

            # Summary
            console.print(f"\n[bold]User-accessible (no sudo):[/bold] {totals['user_accessible_gb']:.1f} GB")

            if verbose:
                # Show large files
                for log in logs:
                    if log['large_files']:
                        console.print(f"\n[bold]Large files in {log['name']}:[/bold]")
                        for lf in log['large_files'][:3]:
                            console.print(f"  {lf['name']}: {lf['size_mb']:.0f} MB (age: {lf['age_days']}d)")
        else:
            console.print("[green]No significant log files found![/green]")

        console.print(f"\n[dim]Note: This is informational only. No files were deleted.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
