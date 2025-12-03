#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""Battery Analysis - macOS Resource Optimizer"""

import asyncio
import json
import sys
import time
from pathlib import Path
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from agent_result_formatter import format_battery_result

async def analyze_battery():
    """Analyze battery status."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return {'category': 'battery', 'status': 'not_available', 'timestamp': time.time()}

        percent = battery.percent
        plugged = battery.power_plugged
        seconds_left = battery.secsleft
        hours_remaining = seconds_left / 3600 if seconds_left > 0 else None

        issues = []
        recommendations = []

        if not plugged and percent < 10:
            issues.append({'type': 'critical_battery', 'severity': 'critical', 'value': percent, 'description': f'Battery at {percent}%'})
            recommendations.append({'action': 'plug_in_charger', 'target': 'Battery', 'reason': 'Critical battery', 'priority_score': 95})
        elif not plugged and percent < 20:
            issues.append({'type': 'low_battery', 'severity': 'warning', 'value': percent, 'description': f'Battery at {percent}%'})
            recommendations.append({'action': 'consider_charging', 'target': 'Battery', 'reason': 'Low battery', 'priority_score': 75})

        return {
            'category': 'battery',
            'metrics': {'percent': percent, 'hours_remaining': round(hours_remaining, 1) if hours_remaining else None, 'plugged': plugged},
            'issues': issues,
            'recommendations': recommendations,
            'timestamp': time.time()
        }
    except:
        return {'category': 'battery', 'status': 'error', 'timestamp': time.time()}

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['json', 'toon'], default='toon')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    result = await analyze_battery()

    if args.json or args.format == 'json':
        print(json.dumps(result))
        return 0

    if result.get('status') in ['not_available', 'error']:
        print(f"cat:battery\ns:{result['status']}\nt:{result['timestamp']}")
        return 0

    toon_output = format_battery_result(
        percent=result['metrics']['percent'],
        hours_remaining=result['metrics'].get('hours_remaining'),
        power_plugged=result['metrics']['plugged'],
        issues=result.get('issues'),
        recommendations=result.get('recommendations')
    )
    print(toon_output)
    return 2 if any(i['severity'] == 'critical' for i in result['issues']) else (1 if result['issues'] else 0)

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
