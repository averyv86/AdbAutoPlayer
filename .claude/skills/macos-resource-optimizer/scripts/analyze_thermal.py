#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""Thermal Analysis - macOS Resource Optimizer"""

import asyncio
import json
import sys
import time
from pathlib import Path
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from agent_result_formatter import format_thermal_result

async def analyze_thermal():
    """Analyze thermal status."""
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return {'category': 'thermal', 'status': 'not_available', 'timestamp': time.time()}

        # Get CPU temp (varies by platform)
        cpu_temp = None
        for name, entries in temps.items():
            if 'cpu' in name.lower() or 'core' in name.lower():
                cpu_temp = entries[0].current if entries else None
                break

        if cpu_temp is None and temps:
            first_sensor = list(temps.values())[0]
            cpu_temp = first_sensor[0].current if first_sensor else None

        if cpu_temp is None:
            return {'category': 'thermal', 'status': 'not_available', 'timestamp': time.time()}

        issues = []
        recommendations = []

        if cpu_temp > 90:
            issues.append({'type': 'critical_temp', 'severity': 'critical', 'value': cpu_temp, 'description': f'CPU temp {cpu_temp}°C'})
            recommendations.append({'action': 'reduce_cpu_load', 'target': 'CPU', 'reason': 'Critical temperature', 'priority_score': 95})
        elif cpu_temp > 75:
            issues.append({'type': 'high_temp', 'severity': 'warning', 'value': cpu_temp, 'description': f'CPU temp {cpu_temp}°C'})
            recommendations.append({'action': 'monitor_temperature', 'target': 'CPU', 'reason': 'High temperature', 'priority_score': 70})

        return {
            'category': 'thermal',
            'metrics': {'cpu_temp': round(cpu_temp, 1)},
            'issues': issues,
            'recommendations': recommendations,
            'timestamp': time.time()
        }
    except:
        return {'category': 'thermal', 'status': 'error', 'timestamp': time.time()}

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    result = await analyze_thermal()

    if args.json or args.format == 'json':
        print(json.dumps(result))
        return 0

    if result.get('status') in ['not_available', 'error']:
        print(f"cat:thermal\ns:{result['status']}\nt:{result['timestamp']}")
        return 0

    toon_output = format_thermal_result(
        cpu_temp=result['metrics']['cpu_temp'],
        issues=result.get('issues'),
        recommendations=result.get('recommendations')
    )
    print(toon_output)
    return 2 if any(i['severity'] == 'critical' for i in result['issues']) else (1 if result['issues'] else 0)

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
