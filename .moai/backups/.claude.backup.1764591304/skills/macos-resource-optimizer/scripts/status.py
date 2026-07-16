#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""Quick Status Check - macOS Resource Optimizer

Fast health check across all resource categories.

Exit Codes:
    0: All systems healthy
    1: Warning detected
    2: Critical issue detected

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

async def quick_status():
    """Quick status check (no subprocess calls, direct psutil)."""
    status = {
        'timestamp': time.time(),
        'categories': {},
        'overall_status': 'healthy',
        'overall_exit_code': 0
    }

    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_status = 'critical' if cpu_percent > 90 else ('warning' if cpu_percent > 75 else 'healthy')
    status['categories']['cpu'] = {'percent': round(cpu_percent, 1), 'status': cpu_status}
    if cpu_status == 'critical':
        status['overall_exit_code'] = max(status['overall_exit_code'], 2)
        status['overall_status'] = 'critical'
    elif cpu_status == 'warning' and status['overall_exit_code'] < 2:
        status['overall_exit_code'] = 1
        status['overall_status'] = 'warning'

    # Memory
    mem = psutil.virtual_memory()
    mem_status = 'critical' if mem.percent > 90 else ('warning' if mem.percent > 75 else 'healthy')
    status['categories']['memory'] = {'percent': round(mem.percent, 1), 'status': mem_status}
    if mem_status == 'critical':
        status['overall_exit_code'] = max(status['overall_exit_code'], 2)
        status['overall_status'] = 'critical'
    elif mem_status == 'warning' and status['overall_exit_code'] < 2:
        status['overall_exit_code'] = 1
        status['overall_status'] = 'warning'

    # Disk
    disk = psutil.disk_usage('/')
    disk_status = 'critical' if disk.percent > 90 else ('warning' if disk.percent > 80 else 'healthy')
    status['categories']['disk'] = {'percent': round(disk.percent, 1), 'status': disk_status}
    if disk_status == 'critical':
        status['overall_exit_code'] = max(status['overall_exit_code'], 2)
        status['overall_status'] = 'critical'
    elif disk_status == 'warning' and status['overall_exit_code'] < 2:
        status['overall_exit_code'] = 1
        status['overall_status'] = 'warning'

    # Network (connection count)
    try:
        connections = len(psutil.net_connections())
        net_status = 'warning' if connections > 1000 else 'healthy'
        status['categories']['network'] = {'connections': connections, 'status': net_status}
        if net_status == 'warning' and status['overall_exit_code'] < 2:
            status['overall_exit_code'] = 1
            status['overall_status'] = 'warning'
    except:
        status['categories']['network'] = {'status': 'unavailable'}

    # Battery
    try:
        battery = psutil.sensors_battery()
        if battery:
            batt_percent = battery.percent
            plugged = battery.power_plugged
            batt_status = 'critical' if (not plugged and batt_percent < 10) else ('warning' if (not plugged and batt_percent < 20) else 'healthy')
            status['categories']['battery'] = {'percent': batt_percent, 'plugged': plugged, 'status': batt_status}
            if batt_status == 'critical':
                status['overall_exit_code'] = max(status['overall_exit_code'], 2)
                status['overall_status'] = 'critical'
            elif batt_status == 'warning' and status['overall_exit_code'] < 2:
                status['overall_exit_code'] = 1
                status['overall_status'] = 'warning'
        else:
            status['categories']['battery'] = {'status': 'not_available'}
    except:
        status['categories']['battery'] = {'status': 'unavailable'}

    # Thermal
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # Get first available temp
            cpu_temp = None
            for name, entries in temps.items():
                if entries:
                    cpu_temp = entries[0].current
                    break

            if cpu_temp:
                thermal_status = 'critical' if cpu_temp > 90 else ('warning' if cpu_temp > 75 else 'healthy')
                status['categories']['thermal'] = {'cpu_temp': round(cpu_temp, 1), 'status': thermal_status}
                if thermal_status == 'critical':
                    status['overall_exit_code'] = max(status['overall_exit_code'], 2)
                    status['overall_status'] = 'critical'
                elif thermal_status == 'warning' and status['overall_exit_code'] < 2:
                    status['overall_exit_code'] = 1
                    status['overall_status'] = 'warning'
            else:
                status['categories']['thermal'] = {'status': 'not_available'}
        else:
            status['categories']['thermal'] = {'status': 'not_available'}
    except:
        status['categories']['thermal'] = {'status': 'unavailable'}

    return status

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Quick system health check')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    output_format = 'json' if args.json else args.format
    result = await quick_status()

    if output_format == 'json':
        print(json.dumps(result, indent=2))
        return result['overall_exit_code']

    # TOON format
    print("# System Status")
    print(f"overall:{result['overall_status']}")
    print(f"timestamp:{result['timestamp']}")
    print()
    for cat, data in result['categories'].items():
        print(f"{cat}:{data.get('status', 'unknown')}")
        if 'percent' in data:
            print(f"{cat}_pct:{data['percent']}")
    print()

    return result['overall_exit_code']

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
