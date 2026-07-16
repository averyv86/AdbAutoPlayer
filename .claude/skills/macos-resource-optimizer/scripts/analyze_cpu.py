#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
CPU Analysis Script - Part of macOS Resource Optimizer

Analyzes CPU usage, identifies high-usage processes, and generates TOON-formatted
recommendations for optimization.

Usage:
    uv run scripts/analyze_cpu.py [--format json|toon] [--json]

Author: MoAI-ADK
Version: 3.0.0 (TOON-enabled)
Date: 2025-12-01
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import psutil

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from agent_result_formatter import format_cpu_result


async def analyze_cpu() -> Dict:
    """
    Analyze CPU usage and identify optimization opportunities.

    Returns:
        Dict with CPU metrics, issues, and recommendations
    """
    # Get CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)

    try:
        cpu_freq = psutil.cpu_freq()
        freq_mhz = int(cpu_freq.current) if cpu_freq else None
    except:
        freq_mhz = None

    # Get per-process CPU usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] and info['cpu_percent'] > 1.0:
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'cpu_percent': info['cpu_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Sort by CPU usage and get top 10
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]

    # User vs System time breakdown
    cpu_times = psutil.cpu_times_percent(interval=1)
    user_percent = cpu_times.user
    system_percent = cpu_times.system

    # Identify issues
    issues = []
    recommendations = []

    # Critical CPU usage
    if cpu_percent > 90:
        issues.append({
            'type': 'critical_cpu_usage',
            'severity': 'critical',
            'value': cpu_percent,
            'description': f'CPU usage at {cpu_percent:.1f}% (critical threshold: 90%)'
        })
        recommendations.append({
            'action': 'identify_cpu_hogs',
            'target': f'Top process: {top_processes[0]["name"] if top_processes else "unknown"}',
            'reason': f'Critical CPU usage: {cpu_percent:.1f}%',
            'priority_score': 95
        })

    # High CPU usage
    elif cpu_percent > 75:
        issues.append({
            'type': 'high_cpu_usage',
            'severity': 'warning',
            'value': cpu_percent,
            'description': f'CPU usage at {cpu_percent:.1f}% (warning threshold: 75%)'
        })
        recommendations.append({
            'action': 'monitor_cpu_usage',
            'target': 'System CPU',
            'reason': f'High CPU usage: {cpu_percent:.1f}%',
            'priority_score': 70
        })

    # High process count
    if len(processes) > 300:
        issues.append({
            'type': 'high_process_count',
            'severity': 'warning',
            'value': len(processes),
            'description': f'{len(processes)} processes running (threshold: 300)'
        })
        recommendations.append({
            'action': 'reduce_process_count',
            'target': 'Background processes',
            'reason': f'High process count: {len(processes)}',
            'priority_score': 60
        })

    # Top CPU consumers
    if top_processes and top_processes[0]['cpu_percent'] > 50:
        process = top_processes[0]
        issues.append({
            'type': 'cpu_hog_detected',
            'severity': 'high',
            'value': process['cpu_percent'],
            'description': f'{process["name"]} using {process["cpu_percent"]:.1f}% CPU'
        })
        recommendations.append({
            'action': 'terminate_or_optimize',
            'target': f'{process["name"]} (PID {process["pid"]})',
            'reason': f'High CPU usage: {process["cpu_percent"]:.1f}%',
            'priority_score': 85
        })

    # Build result
    result = {
        'category': 'cpu',
        'metrics': {
            'usage_percent': round(cpu_percent, 1),
            'user_percent': round(user_percent, 1),
            'system_percent': round(system_percent, 1),
            'cores_logical': cpu_count_logical,
            'cores_physical': cpu_count_physical,
            'freq_mhz': freq_mhz,
            'process_count': len(processes),
            'top_processes': [
                {
                    'name': p['name'],
                    'cpu_percent': round(p['cpu_percent'], 1)
                }
                for p in top_processes[:5]
            ]
        },
        'issues': issues,
        'recommendations': recommendations,
        'timestamp': time.time()
    }

    return result


async def main():
    """Main execution with format selection."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze CPU usage')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon',
                        help='Output format (default: toon)')
    parser.add_argument('--json', action='store_true',
                        help='Shorthand for --format json')
    args = parser.parse_args()

    # Override format if --json flag is used
    output_format = 'json' if args.json else args.format

    # Run analysis
    result = await analyze_cpu()

    # Output in requested format
    if output_format == 'json':
        print(json.dumps(result, indent=2))
        return 0

    # TOON format (default)
    toon_output = format_cpu_result(
        usage_percent=result['metrics']['usage_percent'],
        user_percent=result['metrics']['user_percent'],
        system_percent=result['metrics']['system_percent'],
        cores=result['metrics']['cores_logical'],
        freq_mhz=result['metrics'].get('freq_mhz'),
        issues=result.get('issues'),
        recommendations=result.get('recommendations')
    )
    print(toon_output)

    # Exit code based on status
    if result['issues']:
        critical = any(i['severity'] == 'critical' for i in result['issues'])
        return 2 if critical else 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
