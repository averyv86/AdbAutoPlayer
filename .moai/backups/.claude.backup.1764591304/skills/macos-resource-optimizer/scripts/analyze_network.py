#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""Network Analysis - macOS Resource Optimizer"""

import asyncio
import json
import sys
import time
from pathlib import Path
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from agent_result_formatter import format_network_result

async def analyze_network():
    """Analyze network usage."""
    # Network I/O
    io_start = psutil.net_io_counters()
    await asyncio.sleep(1)
    io_end = psutil.net_io_counters()

    sent_bytes = io_end.bytes_sent - io_start.bytes_sent
    recv_bytes = io_end.bytes_recv - io_start.bytes_recv
    sent_mbps = (sent_bytes / (1024**2))
    recv_mbps = (recv_bytes / (1024**2))

    # Network connections
    connections = len(psutil.net_connections())

    issues = []
    recommendations = []

    if connections > 1000:
        issues.append({'type': 'high_connections', 'severity': 'warning', 'value': connections, 'description': f'{connections} open connections'})
        recommendations.append({'action': 'reduce_connections', 'target': 'Network connections', 'reason': f'{connections} connections', 'priority_score': 70})

    return {
        'category': 'network',
        'metrics': {'sent_mbps': round(sent_mbps, 2), 'recv_mbps': round(recv_mbps, 2), 'connections': connections},
        'issues': issues,
        'recommendations': recommendations,
        'timestamp': time.time()
    }

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    result = await analyze_network()

    if args.json or args.format == 'json':
        print(json.dumps(result))
        return 0

    toon_output = format_network_result(
        sent_mbps=result['metrics']['sent_mbps'],
        recv_mbps=result['metrics']['recv_mbps'],
        connections=result['metrics']['connections'],
        issues=result.get('issues'),
        recommendations=result.get('recommendations')
    )
    print(toon_output)
    return 2 if any(i['severity'] == 'critical' for i in result['issues']) else (1 if result['issues'] else 0)

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
