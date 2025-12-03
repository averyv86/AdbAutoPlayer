#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# ///
"""
Agent 17: Background App Suspender
Identifies and suspends background applications with low activity
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 3
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
import click
from hibernation_utils import HibernationUtils


class BackgroundAppSuspender:
    """
    Manages suspension of background applications
    """

    def __init__(self, config_path: Path = None):
        """Initialize suspender with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.background_apps = HibernationUtils.BACKGROUND_APPS

    def _load_config(self, config_path: Path) -> dict:
        """Load background app suspension configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('background_app_suspension', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {}

    def analyze_background_apps(self) -> dict:
        """
        Analyze background applications and identify suspension candidates
        Returns comprehensive analysis with suspension recommendations
        """
        suspension_candidates = []
        total_memory_gb = 0
        total_potential_savings = 0

        for app_name, app_info in self.background_apps.items():
            activity = HibernationUtils.get_app_activity_level(app_name)

            # Skip if app not running
            if 'error' in activity or activity.get('process_count', 0) == 0:
                continue

            memory_gb = activity['memory_gb']
            can_suspend = app_info['safe_suspend']

            total_memory_gb += memory_gb

            # Add to candidates if suspendable and using memory
            if can_suspend and memory_gb >= 0.1:  # At least 100 MB
                # Estimate savings (70% of memory recoverable)
                potential_savings = memory_gb * 0.7

                # Determine priority based on activity
                if activity['activity_level'] == 'idle':
                    priority = 'high'
                elif activity['activity_level'] == 'low':
                    priority = 'medium'
                else:
                    priority = 'low'

                suspension_candidates.append({
                    'app_name': app_name,
                    'memory_gb': memory_gb,
                    'activity_level': activity['activity_level'],
                    'cpu_percent': activity['cpu_percent'],
                    'process_count': activity['process_count'],
                    'can_suspend': can_suspend,
                    'potential_savings_gb': round(potential_savings, 2),
                    'priority': priority
                })

                total_potential_savings += potential_savings

        # Sort by memory (descending)
        suspension_candidates.sort(key=lambda x: x['memory_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'background_apps_total': len(self.background_apps),
            'background_apps_running': len(suspension_candidates),
            'suspension_candidates': suspension_candidates,
            'total_background_memory_gb': round(total_memory_gb, 2),
            'total_potential_savings_gb': round(total_potential_savings, 2),
            'recommendations': self._generate_recommendations(suspension_candidates)
        }

    def _generate_recommendations(self, candidates: list) -> list:
        """Generate actionable background app suspension recommendations"""
        if not candidates:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'No background apps requiring suspension',
                'expected_savings_gb': 0
            }]

        recommendations = []

        # Group by priority
        high_priority = [c for c in candidates if c['priority'] == 'high']
        medium_priority = [c for c in candidates if c['priority'] == 'medium']

        # High priority suspensions (idle apps)
        if high_priority:
            total_savings = sum(c['potential_savings_gb'] for c in high_priority)
            recommendations.append({
                'priority': 'high',
                'action': 'suspend_idle_background_apps',
                'description': f"Suspend {len(high_priority)} idle background apps",
                'apps': [c['app_name'] for c in high_priority],
                'app_count': len(high_priority),
                'expected_savings_gb': round(total_savings, 2),
                'method': 'graceful_quit',
                'risk': 'low',
                'impact': 'Apps will restart when needed',
                'restoration': 'Automatic on next use'
            })

        # Medium priority suspensions (low activity apps)
        if medium_priority:
            total_savings = sum(c['potential_savings_gb'] for c in medium_priority)
            recommendations.append({
                'priority': 'medium',
                'action': 'suspend_low_activity_apps',
                'description': f"Suspend {len(medium_priority)} low-activity background apps",
                'apps': [c['app_name'] for c in medium_priority],
                'app_count': len(medium_priority),
                'expected_savings_gb': round(total_savings, 2),
                'method': 'graceful_quit',
                'risk': 'low'
            })

        # Bulk suspension if many candidates
        if len(candidates) >= 3:
            total_savings = sum(c['potential_savings_gb'] for c in candidates)
            recommendations.append({
                'priority': 'high',
                'action': 'bulk_suspend_background_apps',
                'description': f"Suspend all {len(candidates)} background apps",
                'expected_savings_gb': round(total_savings, 2),
                'method': 'automated_suspension',
                'risk': 'low',
                'estimated_time': f"{len(candidates) * 2} seconds",
                'note': 'Apps will auto-restart when needed by system'
            })

        return recommendations

    def get_suspension_impact(self, app_name: str) -> dict:
        """
        Estimate impact of suspending a specific background app
        """
        if app_name not in self.background_apps:
            return {
                'app_name': app_name,
                'error': 'Not a known background app'
            }

        activity = HibernationUtils.get_app_activity_level(app_name)

        if 'error' in activity:
            return {
                'app_name': app_name,
                'error': activity['error']
            }

        if activity.get('process_count', 0) == 0:
            return {
                'app_name': app_name,
                'running': False,
                'message': 'App not currently running'
            }

        app_info = self.background_apps[app_name]

        # Calculate impact
        memory_recovery = activity['memory_gb'] * 0.7  # 70% recoverable

        return {
            'app_name': app_name,
            'current_memory_gb': activity['memory_gb'],
            'expected_savings_gb': round(memory_recovery, 2),
            'activity_level': activity['activity_level'],
            'cpu_percent': activity['cpu_percent'],
            'can_suspend': app_info['safe_suspend'],
            'suspension_impact': {
                'data_loss_risk': 'none',
                'restart_time': '1-2 seconds',
                'auto_restart': 'yes',
                'state_preservation': 'full'
            },
            'recommendation': 'suspend' if activity['activity_level'] in ['idle', 'low'] else 'keep_running',
            'timestamp': datetime.now().isoformat()
        }

    def suspend_app(self, app_name: str) -> dict:
        """
        Suspend a specific background app
        """
        if app_name not in self.background_apps:
            return {
                'success': False,
                'error': 'Not a known background app',
                'app_name': app_name
            }

        if not self.background_apps[app_name]['safe_suspend']:
            return {
                'success': False,
                'error': 'App marked as unsafe to suspend',
                'app_name': app_name
            }

        # Use hibernation utilities to suspend
        result = HibernationUtils.suspend_app(app_name, preserve_state=True)

        return result

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save background app suspension report"""
        report = self.analyze_background_apps()
        report_json = json.dumps(report, indent=2)

        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report_json)
                print(f"Report saved to: {output_path}")
            except Exception as e:
                print(f"Warning: Could not save report: {e}")

        return report_json


@click.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text',
              help='Output format (text or json)')
@click.option('--save-report', is_flag=True, default=False,
              help='Save report to data directory')
@click.option('--app', type=str, default=None,
              help='Analyze specific app impact')
def main(format, save_report, app):
    """Background App Suspender - Identifies and manages background app suspension"""
    start_time = time.time()

    # Initialize suspender
    suspender = BackgroundAppSuspender()

    # Get specific app impact if requested
    if app:
        impact = suspender.get_suspension_impact(app)
        execution_time = time.time() - start_time
        impact['execution_time_seconds'] = round(execution_time, 3)

        if format == 'json':
            print(json.dumps(impact, indent=2))
        else:
            print(f"=== Background App Impact: {app} ===\n")
            print(f"Execution Time: {impact['execution_time_seconds']}s")
            if 'error' in impact:
                print(f"Error: {impact['error']}")
            elif not impact.get('running'):
                print(f"Status: {impact.get('message', 'Not running')}")
            else:
                print(f"Current Memory: {impact['current_memory_gb']} GB")
                print(f"Expected Savings: {impact['expected_savings_gb']} GB")
                print(f"Activity Level: {impact['activity_level']}")
                print(f"CPU: {impact['cpu_percent']}%")
                print(f"Can Suspend: {'YES' if impact['can_suspend'] else 'NO'}")
                print(f"Recommendation: {impact['recommendation'].upper()}")
        return 0

    # Analyze background apps
    report = suspender.analyze_background_apps()

    # Add execution metadata
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 3)

    if format == 'json':
        # JSON output
        print(json.dumps(report, indent=2))
    else:
        # Text output
        print("=== Background App Suspender (Agent 17) ===\n")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Execution Time: {report['execution_time_seconds']}s")
        print(f"Background Apps Total: {report['background_apps_total']}")
        print(f"Background Apps Running: {report['background_apps_running']}\n")

        print(f"Total Background Memory: {report['total_background_memory_gb']} GB")
        print(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

        if report['suspension_candidates']:
            print("=== Suspension Candidates ===")
            print(f"{'App Name':20s}  {'Memory':>8s}  {'Activity':>10s}  {'CPU':>7s}  {'Priority':>10s}")
            print("-" * 70)
            for candidate in report['suspension_candidates']:
                print(f"{candidate['app_name']:20s}  {candidate['memory_gb']:6.2f} GB  {candidate['activity_level']:>10s}  {candidate['cpu_percent']:5.2f}%  {candidate['priority']:>10s}")

            print(f"\n=== Detailed Candidates ===")
            for i, candidate in enumerate(report['suspension_candidates'], 1):
                print(f"\n  {i}. {candidate['app_name']}")
                print(f"     Memory: {candidate['memory_gb']} GB")
                print(f"     Activity: {candidate['activity_level']} (CPU: {candidate['cpu_percent']}%)")
                print(f"     Processes: {candidate['process_count']}")
                print(f"     Potential Savings: {candidate['potential_savings_gb']} GB")
                print(f"     Priority: {candidate['priority']}")
                print(f"     Can Suspend: {'YES' if candidate['can_suspend'] else 'NO'}")

        if report['recommendations']:
            print("\n=== Recommendations ===")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
                print(f"     Action: {rec['action']}")
                if 'apps' in rec:
                    print(f"     Apps: {', '.join(rec['apps'])}")
                if 'app_count' in rec:
                    print(f"     Count: {rec['app_count']} apps")
                print(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
                print(f"     Method: {rec.get('method', 'N/A')}")
                print(f"     Risk: {rec.get('risk', 'N/A')}")
                if 'impact' in rec:
                    print(f"     Impact: {rec['impact']}")
                if 'restoration' in rec:
                    print(f"     Restoration: {rec['restoration']}")
                if 'estimated_time' in rec:
                    print(f"     Est. Time: {rec['estimated_time']}")
                if 'note' in rec:
                    print(f"     Note: {rec['note']}")

    # Save report if requested
    if save_report:
        output_path = Path(__file__).parent.parent / 'data' / 'background-app-suspension.json'
        suspender.generate_report(output_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
