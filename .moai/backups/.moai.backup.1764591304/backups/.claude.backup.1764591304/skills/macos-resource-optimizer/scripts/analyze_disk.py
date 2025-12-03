#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Disk Analysis Script - macOS Resource Optimizer

Analyzes disk usage, I/O performance, and storage optimization opportunities.

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
from agent_result_formatter import format_disk_result


async def analyze_disk():
    """Analyze disk usage and I/O."""
    # Disk usage
    disk = psutil.disk_usage('/')
    total_gb = disk.total / (1024**3)
    used_gb = disk.used / (1024**3)
    free_gb = disk.free / (1024**3)

    # Disk I/O
    try:
        io_start = psutil.disk_io_counters()
        await asyncio.sleep(1)  # Sample for 1 second
        io_end = psutil.disk_io_counters()

        read_bytes = io_end.read_bytes - io_start.read_bytes
        write_bytes = io_end.write_bytes - io_start.write_bytes
        read_mbps = (read_bytes / (1024**2))  # MB/s
        write_mbps = (write_bytes / (1024**2))  # MB/s
    except:
        read_mbps = None
        write_mbps = None

    # Issues and recommendations
    issues = []
    recommendations = []

    if disk.percent > 90:
        issues.append({
            'type': 'critical_disk_space',
            'severity': 'critical',
            'value': disk.percent,
            'description': f'Disk at {disk.percent:.1f}% (critical)'
        })
        recommendations.append({
            'action': 'cleanup_disk_space',
            'target': 'System disk',
            'reason': f'Critical disk space: {disk.percent:.1f}%',
            'priority_score': 95
        })
    elif disk.percent > 80:
        issues.append({
            'type': 'high_disk_usage',
            'severity': 'warning',
            'value': disk.percent,
            'description': f'Disk at {disk.percent:.1f}% (warning)'
        })
        recommendations.append({
            'action': 'free_disk_space',
            'target': 'Caches and logs',
            'reason': f'High disk usage: {disk.percent:.1f}%',
            'priority_score': 75
        })

    result = {
        'category': 'disk',
        'metrics': {
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'percent': round(disk.percent, 1),
            'read_mbps': round(read_mbps, 2) if read_mbps else None,
            'write_mbps': round(write_mbps, 2) if write_mbps else None
        },
        'issues': issues,
        'recommendations': recommendations,
        'timestamp': time.time()
    }

    return result


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze disk usage')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    output_format = 'json' if args.json else args.format
    result = await analyze_disk()

    if output_format == 'json':
        print(json.dumps(result, indent=2))
        return 0

    # TOON output
    toon_output = format_disk_result(
        total_gb=result['metrics']['total_gb'],
        used_gb=result['metrics']['used_gb'],
        free_gb=result['metrics']['free_gb'],
        percent=result['metrics']['percent'],
        read_mbps=result['metrics'].get('read_mbps'),
        write_mbps=result['metrics'].get('write_mbps'),
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
