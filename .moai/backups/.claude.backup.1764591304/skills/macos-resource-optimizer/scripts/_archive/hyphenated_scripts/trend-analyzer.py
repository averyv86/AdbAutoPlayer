#!/usr/bin/env python3
"""
Trend Analyzer - Historical Process Usage Tracking
Analyzes process usage patterns over 30/90 days to identify truly idle processes.
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import sys

# History log location
HISTORY_LOG = Path.home() / ".process_history.log"
HISTORY_DATA = Path.home() / ".process_history.json"

class TrendAnalyzer:
    """Analyze process usage trends over time"""

    def __init__(self):
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """Load historical process data"""
        if HISTORY_DATA.exists():
            try:
                with open(HISTORY_DATA, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load history: {e}", file=sys.stderr)
        return {"processes": {}, "last_scan": None}

    def _save_history(self):
        """Save historical process data"""
        try:
            with open(HISTORY_DATA, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}", file=sys.stderr)

    def log_current_processes(self):
        """Log currently running processes to history"""
        timestamp = datetime.now().isoformat()

        try:
            # Get current processes
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            current_processes = set()
            for line in ps_output.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    pid = parts[1]
                    command = parts[10]
                    process_name = command.split()[0] if command else "unknown"
                    current_processes.add(process_name)

                    # Initialize process entry if not exists
                    if process_name not in self.history["processes"]:
                        self.history["processes"][process_name] = {
                            "first_seen": timestamp,
                            "last_seen": timestamp,
                            "access_count": 1,
                            "access_dates": [timestamp]
                        }
                    else:
                        # Update existing entry
                        self.history["processes"][process_name]["last_seen"] = timestamp
                        self.history["processes"][process_name]["access_count"] += 1
                        self.history["processes"][process_name]["access_dates"].append(timestamp)

                        # Keep only last 1000 access dates to limit file size
                        if len(self.history["processes"][process_name]["access_dates"]) > 1000:
                            self.history["processes"][process_name]["access_dates"] = \
                                self.history["processes"][process_name]["access_dates"][-1000:]

            self.history["last_scan"] = timestamp
            self._save_history()

            # Also append to simple log file
            with open(HISTORY_LOG, 'a') as f:
                for proc in current_processes:
                    f.write(f"{timestamp} {proc} active\n")

        except Exception as e:
            print(f"Error logging processes: {e}", file=sys.stderr)

    def analyze_trends(self, days: int = 30) -> Dict:
        """Analyze usage trends over specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        results = {
            "daily": [],      # Used almost daily
            "weekly": [],     # Used weekly
            "monthly": [],    # Used monthly
            "one_off": [],    # Used very rarely
            "idle": []        # Not used in analysis period
        }

        for process_name, data in self.history["processes"].items():
            # Parse last seen date
            try:
                last_seen = datetime.fromisoformat(data["last_seen"])
            except:
                continue

            # Check if process was active in the period
            if last_seen < cutoff_date:
                results["idle"].append({
                    "name": process_name,
                    "last_seen": data["last_seen"],
                    "access_count": data["access_count"]
                })
                continue

            # Count accesses in the period
            recent_accesses = [
                d for d in data["access_dates"]
                if datetime.fromisoformat(d) >= cutoff_date
            ]

            access_count = len(recent_accesses)

            # Classify usage pattern
            if access_count >= days * 0.7:  # Used 70%+ of days
                results["daily"].append({
                    "name": process_name,
                    "access_count": access_count,
                    "frequency": f"{access_count}/{days} days"
                })
            elif access_count >= days / 7:  # Used weekly or more
                results["weekly"].append({
                    "name": process_name,
                    "access_count": access_count,
                    "frequency": f"{access_count}/{days} days"
                })
            elif access_count >= 3:  # Used at least 3 times
                results["monthly"].append({
                    "name": process_name,
                    "access_count": access_count,
                    "frequency": f"{access_count}/{days} days"
                })
            else:  # Rarely used
                results["one_off"].append({
                    "name": process_name,
                    "access_count": access_count,
                    "frequency": f"{access_count}/{days} days"
                })

        return results

    def find_truly_idle(self, days: int = 90) -> List[Dict]:
        """Find processes with <3 accesses in specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        idle_processes = []

        for process_name, data in self.history["processes"].items():
            recent_accesses = [
                d for d in data["access_dates"]
                if datetime.fromisoformat(d) >= cutoff_date
            ]

            if len(recent_accesses) < 3:
                idle_processes.append({
                    "name": process_name,
                    "access_count": len(recent_accesses),
                    "last_seen": data["last_seen"],
                    "days_since": (datetime.now() - datetime.fromisoformat(data["last_seen"])).days
                })

        return sorted(idle_processes, key=lambda x: x["days_since"], reverse=True)

    def generate_report(self, output_format: str = "text") -> str:
        """Generate trend analysis report"""
        # Analyze 30 and 90 day trends
        trends_30 = self.analyze_trends(30)
        trends_90 = self.analyze_trends(90)
        idle_90 = self.find_truly_idle(90)

        if output_format == "json":
            return json.dumps({
                "30_day_trends": trends_30,
                "90_day_trends": trends_90,
                "idle_processes_90_days": idle_90
            }, indent=2)

        # Text format
        report = []
        report.append("=" * 80)
        report.append("PROCESS USAGE TREND ANALYSIS")
        report.append("=" * 80)
        report.append("")

        report.append("30-DAY ANALYSIS")
        report.append("-" * 80)
        report.append(f"Daily users: {len(trends_30['daily'])} processes")
        report.append(f"Weekly users: {len(trends_30['weekly'])} processes")
        report.append(f"Monthly users: {len(trends_30['monthly'])} processes")
        report.append(f"One-off users: {len(trends_30['one_off'])} processes")
        report.append(f"Idle: {len(trends_30['idle'])} processes")
        report.append("")

        report.append("90-DAY ANALYSIS")
        report.append("-" * 80)
        report.append(f"Daily users: {len(trends_90['daily'])} processes")
        report.append(f"Weekly users: {len(trends_90['weekly'])} processes")
        report.append(f"Monthly users: {len(trends_90['monthly'])} processes")
        report.append(f"One-off users: {len(trends_90['one_off'])} processes")
        report.append(f"Idle: {len(trends_90['idle'])} processes")
        report.append("")

        report.append("TRULY IDLE PROCESSES (<3 accesses in 90 days)")
        report.append("-" * 80)
        for proc in idle_90[:20]:  # Show top 20
            report.append(f"  {proc['name']:<40} | "
                         f"Accesses: {proc['access_count']} | "
                         f"Last seen: {proc['days_since']} days ago")

        if len(idle_90) > 20:
            report.append(f"  ... and {len(idle_90) - 20} more")

        return "\n".join(report)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze process usage trends")
    parser.add_argument("--log", action="store_true", help="Log current processes")
    parser.add_argument("--analyze", action="store_true", help="Analyze trends")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--idle", action="store_true", help="Show truly idle processes")

    args = parser.parse_args()

    analyzer = TrendAnalyzer()

    if args.log:
        print("Logging current processes...")
        analyzer.log_current_processes()
        print("✓ Process snapshot logged")

    if args.analyze:
        report = analyzer.generate_report(args.format)
        print(report)

    if args.idle:
        idle = analyzer.find_truly_idle(args.days)
        if args.format == "json":
            print(json.dumps(idle, indent=2))
        else:
            print(f"\nTruly idle processes (<3 accesses in {args.days} days):")
            print("-" * 80)
            for proc in idle:
                print(f"  {proc['name']:<40} | "
                      f"Accesses: {proc['access_count']} | "
                      f"Last: {proc['days_since']} days ago")

    if not (args.log or args.analyze or args.idle):
        parser.print_help()


if __name__ == "__main__":
    main()
