#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

import psutil
from collections import defaultdict

# CRITICAL: NEVER TOUCH THESE APPS (User's active work environment)
BLACKLIST = {
    # Terminal (NEVER CLOSE)
    'Ghostty',
    'ghostty',

    # Editor (NEVER CLOSE)
    'Visual Studio Code',
    'Code',
    'code',

    # Browsers (NEVER CLOSE without permission)
    'Chrome',
    'Google Chrome',
    'chrome',
    'Firefox',
    'firefox',
    'Safari',
    'safari',
    'Dia',  # Dia Browser
    'dia',
    'Arc',
    'arc',
    'Brave',
    'brave',
    'Edge',
    'edge',
    'Opera',
    'opera',
    'Vivaldi',
    'vivaldi',
    'Browser',  # Any process with "Browser" in name
    'browser',
}

def is_blacklisted(name: str) -> bool:
    """Check if process name matches any blacklisted app."""
    name_lower = name.lower()
    for blacklisted in BLACKLIST:
        if blacklisted.lower() in name_lower or name_lower in blacklisted.lower():
            return True
    return False

groups = defaultdict(lambda: {'count': 0, 'memory_mb': 0, 'pids': []})

for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'exe']):
    try:
        info = proc.info
        pid = info['pid']
        name = info['name'] or 'unknown'
        exe = info.get('exe') or ''
        mem_mb = info['memory_info'].rss / 1024 / 1024 if info.get('memory_info') else 0

        # Group by pattern
        if 'Helper' in name:
            if 'Dia' in exe or 'Arc' in exe:
                key = 'Dia Helpers'
            elif 'Chrome' in exe or 'Google' in exe:
                key = 'Chrome Helpers'
            elif 'Notion' in exe:
                key = 'Notion Helpers'
            elif 'Slack' in exe:
                key = 'Slack Helpers'
            elif 'Visual Studio Code' in exe:
                key = 'VS Code Helpers'
            else:
                key = name
        elif 'Visual Studio Code' in exe or 'Code Helper' in name:
            key = 'VS Code'
        elif 'claude' in name.lower():
            key = 'Claude'
        elif 'Notion' in exe:
            key = 'Notion'
        elif 'Slack' in exe:
            key = 'Slack'
        elif 'Dia' in exe or 'Arc' in exe:
            key = 'Dia Browser'
        elif 'tailspind' in name:
            key = 'Tailspind'
        elif 'next-server' in name:
            key = 'Next.js Server'
        else:
            key = name

        groups[key]['count'] += 1
        groups[key]['memory_mb'] += mem_mb
        groups[key]['pids'].append(pid)

    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
        pass

# Sort and print
sorted_groups = sorted(groups.items(), key=lambda x: x[1]['memory_mb'], reverse=True)

print("=" * 80)
print("🔍 Process Memory Analysis - Top Consumers")
print("=" * 80)
print()

total_killable = 0
kill_recommendations = []

for name, data in sorted_groups[:30]:
    if data['memory_mb'] > 10:  # Only show processes using >10MB
        memory_gb = data['memory_mb'] / 1024
        print(f"{name}:")
        print(f"  Processes: {data['count']}")
        print(f"  Memory: {data['memory_mb']:.0f} MB ({memory_gb:.2f} GB)")

        # CRITICAL: Check blacklist first
        if is_blacklisted(name):
            print(f"  🚫 PROTECTED - User's active work environment (NEVER TOUCH)")
            print()
            continue

        # Determine if killable
        killable = False
        action = None
        if 'Helper' in name or name in ['Tailspind', 'Next.js Server']:
            killable = True
            recovery = data['memory_mb'] * 0.7
            total_killable += recovery
            print(f"  ✅ KILLABLE - Estimated recovery: {recovery:.0f} MB")

            if 'Helper' in name:
                app = name.replace(' Helpers', '')
                action = f"Restart {app} app"
                print(f"  📋 Action: Restart {app} app")
            elif name == 'Tailspind':
                action = "killall tailspind"
                print(f"  📋 Action: killall tailspind")

            kill_recommendations.append((name, recovery, action))
        else:
            print(f"  ⚠️  In use - manual review needed")

        print()

print("=" * 80)
print(f"Total Killable Memory: {total_killable:.0f} MB ({total_killable/1024:.2f} GB)")
print("=" * 80)
print()
print("🎯 KILL RECOMMENDATIONS (sorted by impact):")
print("=" * 80)
kill_recommendations.sort(key=lambda x: x[1], reverse=True)
for i, (name, recovery, action) in enumerate(kill_recommendations, 1):
    print(f"{i}. {name} - Recovery: {recovery:.0f} MB")
    print(f"   Action: {action}")
    print()
