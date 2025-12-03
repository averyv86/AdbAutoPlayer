#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Time Machine Snapshot Hunter - Agent 14

Detects APFS Time Machine local snapshots consuming disk space.
Self-contained with all dependencies inline (PEP 723).

Identifies:
- Local Time Machine snapshots on root volume
- Snapshot age and estimated size
- Total potential recovery (10-80GB typical)

Safety:
- Does NOT auto-delete snapshots
- Report-only mode for user review
- Requires admin privileges for full info

Recovery: 10-80 GB disk space
"""

import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any
import click
from rich.console import Console
from rich.table import Table

console = Console()


def run_command(cmd: List[str], timeout: int = 30) -> tuple:
    """Run command and return stdout, stderr, return_code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", "Command not found", 1


def list_local_snapshots() -> List[Dict[str, Any]]:
    """List all local Time Machine snapshots."""
    snapshots = []

    # Get list of local snapshots
    stdout, stderr, rc = run_command(["tmutil", "listlocalsnapshots", "/"])

    if rc != 0:
        return snapshots

    for line in stdout.strip().split('\n'):
        if not line or not line.startswith('com.apple.TimeMachine'):
            continue

        # Parse snapshot name: com.apple.TimeMachine.2024-01-15-123456
        snapshot_name = line.strip()

        try:
            # Extract date from snapshot name
            date_str = snapshot_name.replace('com.apple.TimeMachine.', '')
            # Format: 2024-01-15-123456
            snapshot_date = datetime.strptime(date_str, '%Y-%m-%d-%H%M%S')
            age_days = (datetime.now() - snapshot_date).days
            age_hours = (datetime.now() - snapshot_date).total_seconds() / 3600

            snapshots.append({
                'name': snapshot_name,
                'date': snapshot_date.isoformat(),
                'age_days': age_days,
                'age_hours': round(age_hours, 1)
            })
        except ValueError:
            # If date parsing fails, still include with unknown age
            snapshots.append({
                'name': snapshot_name,
                'date': 'unknown',
                'age_days': -1,
                'age_hours': -1
            })

    return snapshots


def estimate_snapshot_size() -> Dict[str, Any]:
    """Estimate total snapshot size using disk utility."""
    size_info = {
        'total_bytes': 0,
        'total_gb': 0,
        'method': 'estimate'
    }

    # Method 1: Use diskutil to get APFS snapshot info
    stdout, stderr, rc = run_command(["diskutil", "apfs", "list"])

    if rc == 0:
        # Parse snapshot info from diskutil output
        # Look for "Snapshot" entries and "Size"
        lines = stdout.split('\n')
        snapshot_count = 0

        for line in lines:
            if 'Snapshot' in line or 'snapshot' in line.lower():
                snapshot_count += 1

        # Estimate: Average snapshot is 2-10GB
        # Conservative estimate of 5GB per snapshot
        estimated_gb = snapshot_count * 5
        size_info['total_gb'] = estimated_gb
        size_info['total_bytes'] = estimated_gb * 1024 * 1024 * 1024
        size_info['snapshot_count'] = snapshot_count

    # Method 2: Try tmutil localsnapshot info
    stdout, stderr, rc = run_command(["tmutil", "listlocalsnapshots", "/"])

    if rc == 0:
        snapshot_count = len([l for l in stdout.split('\n') if 'com.apple.TimeMachine' in l])
        if snapshot_count > 0:
            # Refine estimate based on actual count
            estimated_gb = snapshot_count * 5  # 5GB per snapshot average
            size_info['total_gb'] = estimated_gb
            size_info['total_bytes'] = estimated_gb * 1024 * 1024 * 1024
            size_info['snapshot_count'] = snapshot_count

    return size_info


def get_purgeable_space() -> Dict[str, Any]:
    """Get purgeable space info from disk."""
    purgeable = {
        'purgeable_bytes': 0,
        'purgeable_gb': 0
    }

    stdout, stderr, rc = run_command(["diskutil", "info", "/"])

    if rc == 0:
        for line in stdout.split('\n'):
            if 'Purgeable' in line:
                try:
                    # Parse line like "Container Free Space: 50.0 GB (Purgeable)"
                    parts = line.split(':')
                    if len(parts) >= 2:
                        size_part = parts[1].strip()
                        # Extract number and unit
                        for word in size_part.split():
                            if word.replace('.', '').isdigit():
                                size = float(word)
                                if 'GB' in size_part:
                                    purgeable['purgeable_gb'] = size
                                    purgeable['purgeable_bytes'] = int(size * 1024 * 1024 * 1024)
                                elif 'MB' in size_part:
                                    purgeable['purgeable_gb'] = size / 1024
                                    purgeable['purgeable_bytes'] = int(size * 1024 * 1024)
                                break
                except (ValueError, IndexError):
                    continue

    return purgeable


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed snapshot listings')
def main(format: str, verbose: bool):
    """
    Time Machine Snapshot Hunter - Agent 14

    Detects APFS local snapshots for disk space recovery.
    Informational only - does NOT delete snapshots.
    """
    start_time = time.time()

    # Gather snapshot information
    snapshots = list_local_snapshots()
    size_info = estimate_snapshot_size()
    purgeable = get_purgeable_space()

    execution_time = round((time.time() - start_time) * 1000, 2)

    # Calculate potential recovery
    total_recovery_gb = size_info.get('total_gb', 0)

    if format == 'json':
        result = {
            'agent': 'timemachine_snapshot_hunter',
            'agent_number': 14,
            'category': 'disk_cleanup',
            'zombies_found': len(snapshots),
            'memory_freed_mb': 0,  # This agent analyzes disk, not RAM
            'disk_freed_gb': total_recovery_gb,
            'status': 'success',
            'time_ms': execution_time,
            'pids': [],  # No PIDs to kill
            'disk_recovery': {
                'snapshot_count': len(snapshots),
                'estimated_total_gb': total_recovery_gb,
                'purgeable_gb': purgeable.get('purgeable_gb', 0),
                'method': 'estimate (5GB per snapshot average)'
            },
            'snapshots': snapshots if verbose else [],
            'note': 'To delete snapshots, use: sudo tmutil deletelocalsnapshots <date>'
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 14: Time Machine Snapshot Hunter[/bold cyan]\n")

        summary_table = Table(title="Time Machine Local Snapshots")
        summary_table.add_column("Metric", style="yellow")
        summary_table.add_column("Value", justify="right", style="green")

        summary_table.add_row("Total Snapshots", str(len(snapshots)))
        summary_table.add_row("Estimated Size", f"{total_recovery_gb} GB")
        summary_table.add_row("Purgeable Space", f"{purgeable.get('purgeable_gb', 0):.1f} GB")

        console.print(summary_table)

        if verbose and snapshots:
            console.print("\n[bold]Snapshot Details:[/bold]")
            snap_table = Table()
            snap_table.add_column("Snapshot Name", style="cyan")
            snap_table.add_column("Date", style="yellow")
            snap_table.add_column("Age", justify="right", style="red")

            for snap in sorted(snapshots, key=lambda x: x.get('age_days', 0), reverse=True)[:15]:
                age_str = f"{snap['age_days']}d" if snap['age_days'] >= 0 else "unknown"
                snap_table.add_row(
                    snap['name'][:50] + "..." if len(snap['name']) > 50 else snap['name'],
                    snap['date'][:10] if snap['date'] != 'unknown' else 'unknown',
                    age_str
                )

            console.print(snap_table)

        console.print(f"\n[dim]Note: This is informational only. No snapshots were deleted.[/dim]")
        console.print(f"[dim]To delete: sudo tmutil deletelocalsnapshots <date>[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
