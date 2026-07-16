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
Log Rotation Optimizer - Agent 14
Analyzes system and application logs for disk space recovery.

Detects:
- Large log files (>100MB) in /var/log and ~/Library/Logs
- Unrotated logs consuming excessive disk space
- Log files that should be compressed
- System log analysis and rotation recommendations

Recovery: 20-50 GB disk space
Note: Informational only, suggests compression/rotation but does NOT delete
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.table import Table

console = Console()

# Thresholds
LARGE_LOG_THRESHOLD_MB = 100  # 100MB
VERY_LARGE_LOG_THRESHOLD_MB = 500  # 500MB
LOG_AGE_DAYS = 30  # Suggest compression for logs older than 30 days


def get_file_size(path: Path) -> int:
    """Get file size in bytes, handling errors."""
    try:
        return path.stat().st_size
    except (OSError, PermissionError):
        return 0


def get_file_age_days(path: Path) -> int:
    """Get file age in days."""
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days
    except (OSError, PermissionError):
        return 0


def find_large_logs(base_path: Path, threshold_mb: int = LARGE_LOG_THRESHOLD_MB) -> List[Dict[str, Any]]:
    """
    Find large log files in a directory.
    Returns list of log files exceeding threshold.
    """
    large_logs = []

    if not base_path.exists():
        return large_logs

    # Common log extensions
    log_extensions = {'.log', '.txt', '.out', '.err', '.1', '.2', '.3'}

    try:
        # Use find command for performance (handles permissions better)
        result = subprocess.run(
            ['find', str(base_path), '-type', 'f', '-size', f'+{threshold_mb}M'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            for log_path_str in result.stdout.strip().split('\n'):
                if not log_path_str:
                    continue

                log_path = Path(log_path_str)

                # Check if it's a log file
                is_log = (
                    log_path.suffix in log_extensions or
                    'log' in log_path.name.lower() or
                    any(pattern in str(log_path).lower() for pattern in ['.log', 'syslog', 'messages'])
                )

                if is_log:
                    file_size = get_file_size(log_path)
                    file_age = get_file_age_days(log_path)

                    large_logs.append({
                        'path': str(log_path),
                        'name': log_path.name,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'size_bytes': file_size,
                        'age_days': file_age,
                        'compressed': log_path.suffix in {'.gz', '.bz2', '.zip', '.xz'},
                        'suggestion': 'compress' if file_age > LOG_AGE_DAYS and file_size > VERY_LARGE_LOG_THRESHOLD_MB * 1024 * 1024 else 'rotate'
                    })

    except (subprocess.TimeoutExpired, OSError, PermissionError):
        pass

    return sorted(large_logs, key=lambda x: x['size_bytes'], reverse=True)


def analyze_system_logs() -> Dict[str, Any]:
    """
    Analyze system logs in /var/log.
    Returns breakdown of system log usage.
    """
    system_log_path = Path('/var/log')
    large_logs = find_large_logs(system_log_path)

    total_bytes = sum(log['size_bytes'] for log in large_logs)
    uncompressed_logs = [log for log in large_logs if not log['compressed']]
    compressible_bytes = sum(log['size_bytes'] for log in uncompressed_logs if log['age_days'] > LOG_AGE_DAYS)

    return {
        'total_logs': len(large_logs),
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 ** 3), 2),
        'uncompressed_logs': len(uncompressed_logs),
        'compressible_bytes': compressible_bytes,
        'compressible_gb': round(compressible_bytes / (1024 ** 3), 2),
        'logs': large_logs[:20]  # Top 20
    }


def analyze_application_logs() -> Dict[str, Any]:
    """
    Analyze application logs in ~/Library/Logs.
    Returns breakdown of application log usage.
    """
    home = Path.home()
    app_log_path = home / 'Library' / 'Logs'

    large_logs = find_large_logs(app_log_path)

    # Group by application
    app_breakdown = {}
    for log in large_logs:
        # Extract app name from path (usually first directory under Logs/)
        path_parts = Path(log['path']).relative_to(app_log_path).parts
        app_name = path_parts[0] if path_parts else 'Unknown'

        if app_name not in app_breakdown:
            app_breakdown[app_name] = {
                'log_count': 0,
                'total_bytes': 0,
                'logs': []
            }

        app_breakdown[app_name]['log_count'] += 1
        app_breakdown[app_name]['total_bytes'] += log['size_bytes']
        app_breakdown[app_name]['logs'].append(log)

    # Sort by total size
    sorted_apps = sorted(
        [
            {
                'app': app_name,
                'log_count': data['log_count'],
                'total_bytes': data['total_bytes'],
                'total_mb': round(data['total_bytes'] / (1024 * 1024), 2),
                'total_gb': round(data['total_bytes'] / (1024 ** 3), 2),
                'logs': data['logs']
            }
            for app_name, data in app_breakdown.items()
        ],
        key=lambda x: x['total_bytes'],
        reverse=True
    )

    total_bytes = sum(log['size_bytes'] for log in large_logs)

    return {
        'total_logs': len(large_logs),
        'total_bytes': total_bytes,
        'total_gb': round(total_bytes / (1024 ** 3), 2),
        'applications': sorted_apps[:15],  # Top 15 apps
        'all_logs': large_logs[:20]  # Top 20 logs
    }


def suggest_compression_strategy() -> Dict[str, Any]:
    """
    Generate log rotation and compression recommendations.
    """
    recommendations = {
        'compress_old_logs': {
            'description': 'Compress logs older than 30 days',
            'command': 'find /var/log ~/Library/Logs -type f -name "*.log" -mtime +30 -exec gzip {} \\;',
            'estimated_savings': '60-80% file size reduction'
        },
        'rotate_large_logs': {
            'description': 'Set up automatic log rotation for files >100MB',
            'command': 'Configure /etc/newsyslog.conf or use logrotate',
            'estimated_savings': 'Prevent future disk growth'
        },
        'cleanup_old_rotated': {
            'description': 'Remove rotated logs older than 90 days',
            'command': 'find /var/log ~/Library/Logs -type f \\( -name "*.log.*" -o -name "*.log.*.gz" \\) -mtime +90 -delete',
            'estimated_savings': '5-10 GB'
        }
    }

    return recommendations


def analyze_log_rotation() -> Dict[str, Any]:
    """
    Main analysis function for log rotation optimization.
    Returns categorized log analysis and recommendations.
    """
    # Analyze different log categories
    system_logs = analyze_system_logs()
    app_logs = analyze_application_logs()
    compression_strategy = suggest_compression_strategy()

    # Calculate total recoverable space
    total_recovery = system_logs['total_bytes'] + app_logs['total_bytes']

    # Estimate compression savings (assume 70% compression ratio)
    compression_savings = (
        system_logs['compressible_bytes'] +
        sum(log['size_bytes'] for log in app_logs['all_logs'] if not log['compressed'] and log['age_days'] > LOG_AGE_DAYS)
    ) * 0.7

    return {
        'system_logs': system_logs,
        'application_logs': app_logs,
        'compression_strategy': compression_strategy,
        'total_recovery_bytes': total_recovery,
        'total_recovery_gb': round(total_recovery / (1024 ** 3), 2),
        'compression_savings_bytes': int(compression_savings),
        'compression_savings_gb': round(compression_savings / (1024 ** 3), 2)
    }


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='json', help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed log listings')
def main(format: str, verbose: bool):
    """
    Log Rotation Optimizer - Agent 14

    Analyzes system and application logs for disk space recovery.
    Informational only - suggests compression but does NOT delete.
    """
    start_time = time.time()

    # Analyze logs
    results = analyze_log_rotation()

    execution_time = round((time.time() - start_time) * 1000, 2)

    # Output results
    if format == 'json':
        result = {
            'agent': 'log_rotation_optimizer',
            'agent_number': 14,
            'category': 'disk_cleanup',
            'zombies_found': 0,  # This agent doesn't find zombies (PIDs)
            'total_memory_bytes': 0,  # This agent analyzes disk, not RAM
            'execution_time_ms': execution_time,
            'pids': [],  # No PIDs to kill
            'disk_recovery': {
                'total_gb': results['total_recovery_gb'],
                'total_bytes': results['total_recovery_bytes'],
                'compression_savings_gb': results['compression_savings_gb'],
                'breakdown': {
                    'system_logs_gb': results['system_logs']['total_gb'],
                    'application_logs_gb': results['application_logs']['total_gb'],
                    'compressible_system_logs_gb': results['system_logs']['compressible_gb']
                }
            },
            'details': {
                'system_logs': {
                    'count': results['system_logs']['total_logs'],
                    'logs': results['system_logs']['logs'] if verbose else []
                },
                'application_logs': {
                    'count': results['application_logs']['total_logs'],
                    'top_applications': results['application_logs']['applications'] if verbose else [],
                    'logs': results['application_logs']['all_logs'] if verbose else []
                },
                'recommendations': results['compression_strategy']
            }
        }
        print(json.dumps(result, indent=2))

    else:  # table format
        console.print("\n[bold cyan]Agent 14: Log Rotation Optimizer[/bold cyan]\n")

        # Summary table
        summary_table = Table(title="Log Disk Space Analysis")
        summary_table.add_column("Category", style="yellow")
        summary_table.add_column("Log Files", justify="right", style="cyan")
        summary_table.add_column("Current Size", justify="right", style="red")
        summary_table.add_column("Potential Savings", justify="right", style="green")

        summary_table.add_row(
            "System Logs (/var/log)",
            str(results['system_logs']['total_logs']),
            f"{results['system_logs']['total_gb']} GB",
            f"{results['system_logs']['compressible_gb']} GB (compress)"
        )
        summary_table.add_row(
            "Application Logs (~/Library/Logs)",
            str(results['application_logs']['total_logs']),
            f"{results['application_logs']['total_gb']} GB",
            f"{round(results['compression_savings_gb'] - results['system_logs']['compressible_gb'], 2)} GB (compress)"
        )
        summary_table.add_row(
            "[bold]TOTAL RECOVERY[/bold]",
            "",
            f"[bold]{results['total_recovery_gb']} GB[/bold]",
            f"[bold]{results['compression_savings_gb']} GB[/bold]"
        )

        console.print(summary_table)

        if verbose:
            # Top applications table
            if results['application_logs']['applications']:
                console.print("\n[bold]Top Applications by Log Size:[/bold]")
                app_table = Table()
                app_table.add_column("Application", style="yellow")
                app_table.add_column("Log Files", justify="right", style="cyan")
                app_table.add_column("Total Size", justify="right", style="red")

                for app in results['application_logs']['applications'][:10]:
                    app_table.add_row(
                        app['app'],
                        str(app['log_count']),
                        f"{app['total_gb']} GB" if app['total_gb'] >= 1 else f"{app['total_mb']} MB"
                    )

                console.print(app_table)

            # Recommendations
            console.print("\n[bold]Recommended Actions:[/bold]")
            rec_table = Table()
            rec_table.add_column("Action", style="yellow")
            rec_table.add_column("Description", style="cyan")
            rec_table.add_column("Estimated Savings", style="green")

            for action_name, action_data in results['compression_strategy'].items():
                rec_table.add_row(
                    action_name.replace('_', ' ').title(),
                    action_data['description'],
                    action_data['estimated_savings']
                )

            console.print(rec_table)

        console.print(f"\n[dim]Note: This is informational only. Review logs before deletion.[/dim]")
        console.print(f"[bold]Execution Time:[/bold] {execution_time} ms")


if __name__ == '__main__':
    main()
