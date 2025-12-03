#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Memory Analysis Script - macOS Resource Optimizer

Analyzes memory usage, swap usage, and identifies memory-intensive processes.

Author: MoAI-ADK
Version: 3.0.0 (TOON-enabled)
Date: 2025-12-01
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from agent_result_formatter import format_memory_result


async def analyze_memory():
    """Analyze memory usage and swap."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Convert to GB
    total_gb = mem.total / (1024**3)
    used_gb = mem.used / (1024**3)
    available_gb = mem.available / (1024**3)
    swap_used_gb = swap.used / (1024**3)

    # Top memory consumers
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            info = proc.info
            if info['memory_percent'] and info['memory_percent'] > 0.5:
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory_percent': info['memory_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top_processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]

    # Issues and recommendations
    issues = []
    recommendations = []

    if mem.percent > 90:
        issues.append({
            'type': 'critical_memory',
            'severity': 'critical',
            'value': mem.percent,
            'description': f'Memory at {mem.percent:.1f}% (critical)'
        })
        recommendations.append({
            'action': 'close_memory_hogs',
            'target': f'{top_processes[0]["name"]} ({top_processes[0]["memory_percent"]:.1f}%)',
            'reason': 'Critical memory usage',
            'priority_score': 95
        })
    elif mem.percent > 75:
        issues.append({
            'type': 'high_memory',
            'severity': 'warning',
            'value': mem.percent,
            'description': f'Memory at {mem.percent:.1f}% (warning)'
        })
        recommendations.append({
            'action': 'monitor_memory',
            'target': 'System memory',
            'reason': 'High memory usage',
            'priority_score': 70
        })

    if swap.percent > 50:
        issues.append({
            'type': 'high_swap',
            'severity': 'warning',
            'value': swap.percent,
            'description': f'Swap at {swap.percent:.1f}%'
        })
        recommendations.append({
            'action': 'reduce_swap_usage',
            'target': 'Swap memory',
            'reason': f'High swap usage: {swap.percent:.1f}%',
            'priority_score': 65
        })

    result = {
        'category': 'memory',
        'metrics': {
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'available_gb': round(available_gb, 2),
            'percent': round(mem.percent, 1),
            'swap_used_gb': round(swap_used_gb, 2),
            'swap_percent': round(swap.percent, 1),
            'top_processes': [
                {'name': p['name'], 'memory_percent': round(p['memory_percent'], 1)}
                for p in top_processes[:5]
            ]
        },
        'issues': issues,
        'recommendations': recommendations,
        'timestamp': time.time()
    }

    return result


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze memory usage')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    output_format = 'json' if args.json else args.format
    result = await analyze_memory()

    if output_format == 'json':
        print(json.dumps(result, indent=2))
        return 0

    # TOON output
    toon_output = format_memory_result(
        total_gb=result['metrics']['total_gb'],
        used_gb=result['metrics']['used_gb'],
        available_gb=result['metrics']['available_gb'],
        percent=result['metrics']['percent'],
        swap_used_gb=result['metrics']['swap_used_gb'],
        issues=result.get('issues'),
        recommendations=result.get('recommendations')
    )
    print(toon_output)

    if result['issues']:
        critical = any(i['severity'] == 'critical' for i in result['issues'])
        return 2 if critical else 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
