#!/usr/bin/env python3
"""
Scheduler - Automated Cleanup Scheduling
Generates and manages launchd plists for automated macOS cleanup tasks.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List
import sys
from datetime import datetime

class CleanupScheduler:
    """Manage automated cleanup schedules"""

    def __init__(self):
        self.launch_agents_dir = Path.home() / "Library/LaunchAgents"
        self.launch_agents_dir.mkdir(parents=True, exist_ok=True)

        self.schedules = {
            "daily": {
                "label": "com.macos-optimizer.daily-cleanup",
                "hour": 3,
                "minute": 0,
                "weekday": None,  # Every day
                "description": "Daily light cleanup (caches, temp files)"
            },
            "weekly": {
                "label": "com.macos-optimizer.weekly-cleanup",
                "hour": 3,
                "minute": 0,
                "weekday": 0,  # Sunday
                "description": "Weekly medium cleanup (Docker, build artifacts)"
            },
            "monthly": {
                "label": "com.macos-optimizer.monthly-cleanup",
                "hour": 3,
                "minute": 0,
                "day": 1,  # 1st of month
                "description": "Monthly deep cleanup (full analysis)"
            }
        }

    def generate_plist(self, schedule_type: str, script_path: str) -> str:
        """Generate launchd plist XML"""
        if schedule_type not in self.schedules:
            raise ValueError(f"Invalid schedule type: {schedule_type}")

        config = self.schedules[schedule_type]

        # Build calendar interval
        calendar_dict = {
            "Hour": config["hour"],
            "Minute": config["minute"]
        }

        if "weekday" in config and config["weekday"] is not None:
            calendar_dict["Weekday"] = config["weekday"]

        if "day" in config:
            calendar_dict["Day"] = config["day"]

        # Generate plist XML
        plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{config["label"]}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>uv</string>
        <string>run</string>
        <string>python3</string>
        <string>{script_path}</string>
        <string>--{schedule_type}</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{calendar_dict["Hour"]}</integer>
        <key>Minute</key>
        <integer>{calendar_dict["Minute"]}</integer>
'''

        if "Weekday" in calendar_dict:
            plist += f'''        <key>Weekday</key>
        <integer>{calendar_dict["Weekday"]}</integer>
'''

        if "Day" in calendar_dict:
            plist += f'''        <key>Day</key>
        <integer>{calendar_dict["Day"]}</integer>
'''

        plist += '''    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/macos-optimizer-{}.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/macos-optimizer-{}-error.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>'''.format(schedule_type, schedule_type)

        return plist

    def install_schedule(self, schedule_type: str, script_path: str) -> bool:
        """Install launchd schedule"""
        try:
            config = self.schedules[schedule_type]
            plist_content = self.generate_plist(schedule_type, script_path)

            # Write plist file
            plist_path = self.launch_agents_dir / f"{config['label']}.plist"
            with open(plist_path, 'w') as f:
                f.write(plist_content)

            print(f"✓ Created plist: {plist_path}")

            # Validate plist
            validation = subprocess.run(
                ['plutil', '-lint', str(plist_path)],
                capture_output=True,
                text=True
            )

            if validation.returncode != 0:
                print(f"✗ Plist validation failed: {validation.stderr}", file=sys.stderr)
                return False

            print(f"✓ Plist validated")

            # Load with launchctl
            load_result = subprocess.run(
                ['launchctl', 'load', str(plist_path)],
                capture_output=True,
                text=True
            )

            if load_result.returncode != 0:
                print(f"✗ Failed to load: {load_result.stderr}", file=sys.stderr)
                return False

            print(f"✓ Schedule installed: {config['description']}")
            return True

        except Exception as e:
            print(f"Error installing schedule: {e}", file=sys.stderr)
            return False

    def uninstall_schedule(self, schedule_type: str) -> bool:
        """Uninstall launchd schedule"""
        try:
            config = self.schedules[schedule_type]
            plist_path = self.launch_agents_dir / f"{config['label']}.plist"

            if not plist_path.exists():
                print(f"Schedule not installed: {schedule_type}")
                return True

            # Unload with launchctl
            unload_result = subprocess.run(
                ['launchctl', 'unload', str(plist_path)],
                capture_output=True,
                text=True
            )

            if unload_result.returncode != 0:
                print(f"Warning: Failed to unload: {unload_result.stderr}", file=sys.stderr)

            # Remove plist file
            plist_path.unlink()
            print(f"✓ Schedule uninstalled: {schedule_type}")
            return True

        except Exception as e:
            print(f"Error uninstalling schedule: {e}", file=sys.stderr)
            return False

    def list_schedules(self) -> List[Dict]:
        """List installed schedules"""
        installed = []

        for schedule_type, config in self.schedules.items():
            plist_path = self.launch_agents_dir / f"{config['label']}.plist"

            status = {
                "type": schedule_type,
                "description": config["description"],
                "installed": plist_path.exists(),
                "plist_path": str(plist_path)
            }

            if status["installed"]:
                # Check if loaded
                list_result = subprocess.run(
                    ['launchctl', 'list'],
                    capture_output=True,
                    text=True
                )
                status["loaded"] = config["label"] in list_result.stdout
            else:
                status["loaded"] = False

            installed.append(status)

        return installed

    def detect_safe_window(self) -> bool:
        """Detect if it's a safe time for cleanup (low load, no active user)"""
        try:
            # Check system load
            uptime_output = subprocess.run(
                ['uptime'],
                capture_output=True,
                text=True,
                check=True
            )

            # Extract load average
            load_match = uptime_output.stdout.split('load averages:')
            if len(load_match) > 1:
                loads = load_match[1].strip().split()
                one_min_load = float(loads[0])

                # Safe if load < 2.0
                if one_min_load >= 2.0:
                    return False

            # Check for active user sessions
            who_output = subprocess.run(
                ['who'],
                capture_output=True,
                text=True,
                check=True
            )

            active_sessions = len(who_output.stdout.strip().split('\n'))

            # Safe if no active console sessions (only launchd)
            if active_sessions > 1:
                return False

            # Check time (prefer 3-5 AM)
            current_hour = datetime.now().hour
            if not (3 <= current_hour < 5):
                return False

            return True

        except Exception as e:
            print(f"Error detecting safe window: {e}", file=sys.stderr)
            return False

    def generate_cleanup_script(self, schedule_type: str) -> str:
        """Generate cleanup script for schedule type"""
        script_dir = Path(__file__).parent

        scripts = {
            "daily": f'''#!/bin/bash
# Daily light cleanup (3 AM)

echo "Running daily cleanup at $(date)"

# Clear system caches
rm -rf ~/Library/Caches/*
rm -rf /tmp/*

# Clear Python caches
find ~ -type d -name "__pycache__" -exec rm -rf {{}} + 2>/dev/null

# Clear npm cache (safe operation)
npm cache clean --force 2>/dev/null

# Log result
echo "Daily cleanup completed at $(date)"
''',
            "weekly": f'''#!/bin/bash
# Weekly medium cleanup (Sunday 3 AM)

echo "Running weekly cleanup at $(date)"

# Run daily cleanup first
{script_dir}/scheduler.py --daily

# Docker cleanup
docker system prune -f 2>/dev/null

# Clear build artifacts
find ~ -type d -name "node_modules" -mtime +30 -exec rm -rf {{}} + 2>/dev/null
find ~ -type d -name "dist" -mtime +30 -exec rm -rf {{}} + 2>/dev/null
find ~ -type d -name "build" -mtime +30 -exec rm -rf {{}} + 2>/dev/null

# Clear old logs
find ~/Library/Logs -type f -mtime +30 -delete 2>/dev/null

echo "Weekly cleanup completed at $(date)"
''',
            "monthly": f'''#!/bin/bash
# Monthly deep cleanup (1st Sunday 3 AM)

echo "Running monthly cleanup at $(date)"

# Run weekly cleanup first
{script_dir}/scheduler.py --weekly

# Full Docker cleanup
docker system prune -a -f --volumes 2>/dev/null

# Analyze and report
python3 {script_dir}/trend-analyzer.py --analyze --days 90
python3 {script_dir}/duplicate-finder.py --report

# Archive old logs
tar -czf ~/cleanup-logs-$(date +%Y%m).tar.gz ~/Library/Logs/*.log 2>/dev/null
rm ~/Library/Logs/*.log 2>/dev/null

echo "Monthly cleanup completed at $(date)"
'''
        }

        return scripts.get(schedule_type, "")

    def generate_report(self, output_format: str = "text") -> str:
        """Generate scheduler status report"""
        schedules = self.list_schedules()
        safe_window = self.detect_safe_window()

        if output_format == "json":
            return json.dumps({
                "schedules": schedules,
                "safe_window": safe_window
            }, indent=2)

        # Text format
        report = []
        report.append("=" * 80)
        report.append("CLEANUP SCHEDULER STATUS")
        report.append("=" * 80)
        report.append("")

        report.append("SCHEDULED TASKS")
        report.append("-" * 80)
        for schedule in schedules:
            status_icon = "✓" if schedule["loaded"] else "✗"
            report.append(f"{status_icon} {schedule['type'].upper()}")
            report.append(f"    {schedule['description']}")
            report.append(f"    Installed: {schedule['installed']}")
            report.append(f"    Loaded: {schedule['loaded']}")
            report.append(f"    Path: {schedule['plist_path']}")
            report.append("")

        report.append("SAFE CLEANUP WINDOW")
        report.append("-" * 80)
        if safe_window:
            report.append("  ✓ Safe to run cleanup (low load, no active users)")
        else:
            report.append("  ✗ Not safe to run cleanup (system active)")
        report.append(f"  Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(report)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage automated cleanup schedules")
    parser.add_argument("--install", choices=["daily", "weekly", "monthly", "all"],
                       help="Install schedule")
    parser.add_argument("--uninstall", choices=["daily", "weekly", "monthly", "all"],
                       help="Uninstall schedule")
    parser.add_argument("--list", action="store_true", help="List schedules")
    parser.add_argument("--status", action="store_true", help="Show status report")
    parser.add_argument("--generate-script", choices=["daily", "weekly", "monthly"],
                       help="Generate cleanup script")
    parser.add_argument("--check-safe-window", action="store_true",
                       help="Check if safe to run cleanup")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")

    args = parser.parse_args()

    scheduler = CleanupScheduler()
    script_dir = Path(__file__).parent

    if args.install:
        if args.install == "all":
            types = ["daily", "weekly", "monthly"]
        else:
            types = [args.install]

        for schedule_type in types:
            script_path = script_dir / f"cleanup-{schedule_type}.sh"
            scheduler.install_schedule(schedule_type, str(script_path))

    if args.uninstall:
        if args.uninstall == "all":
            types = ["daily", "weekly", "monthly"]
        else:
            types = [args.uninstall]

        for schedule_type in types:
            scheduler.uninstall_schedule(schedule_type)

    if args.list:
        schedules = scheduler.list_schedules()
        if args.format == "json":
            print(json.dumps(schedules, indent=2))
        else:
            print("Installed Schedules:")
            for schedule in schedules:
                status = "✓" if schedule["loaded"] else "✗"
                print(f"  {status} {schedule['type']}: {schedule['description']}")

    if args.generate_script:
        script = scheduler.generate_cleanup_script(args.generate_script)
        print(script)

    if args.check_safe_window:
        safe = scheduler.detect_safe_window()
        if args.format == "json":
            print(json.dumps({"safe_window": safe}))
        else:
            print(f"Safe cleanup window: {'Yes' if safe else 'No'}")

    if args.status or not any([args.install, args.uninstall, args.list,
                                args.generate_script, args.check_safe_window]):
        report = scheduler.generate_report(args.format)
        print(report)


if __name__ == "__main__":
    main()
