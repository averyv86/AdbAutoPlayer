#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
#   "psutil>=5.9.8",
# ]
# ///
"""
Agent 14: Inactive App Detector
Identifies applications idle for extended periods with high memory usage
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 3
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
import click
from hibernation_utils import HibernationUtils


class InactiveAppDetector:
    """
    Detects inactive applications and recommends hibernation
    """

    def __init__(self, config_path: Path = None):
        """Initialize detector with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Get thresholds from config
        self.inactive_timeout_hours = self.config.get('inactive_timeout_hours', 2)
        self.min_memory_mb = self.config.get('min_memory_mb', 1000)

    def _load_config(self, config_path: Path) -> dict:
        """Load app hibernation configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('app_hibernation', {})
        except Exception as e:
            if not hasattr(self, '_config_warning_shown'):
                click.echo(f"Warning: Could not load config: {e}", err=True)
                self._config_warning_shown = True
            return {
                'inactive_timeout_hours': 2,
                'min_memory_mb': 1000
            }

    def analyze_inactive_apps(self) -> dict:
        """
        Analyze system for inactive applications
        Returns comprehensive analysis with hibernation recommendations
        """
        # Detect inactive apps
        inactive_apps = HibernationUtils.detect_inactive_apps(
            timeout_hours=self.inactive_timeout_hours,
            min_memory_mb=self.min_memory_mb
        )

        if not inactive_apps:
            return {
                'timestamp': datetime.now().isoformat(),
                'inactive_timeout_hours': self.inactive_timeout_hours,
                'min_memory_mb': self.min_memory_mb,
                'inactive_apps': [],
                'total_inactive_count': 0,
                'total_potential_savings_gb': 0,
                'recommendations': [{
                    'priority': 'low',
                    'action': 'no_action_needed',
                    'description': 'No inactive apps detected',
                    'expected_savings_gb': 0
                }]
            }

        # Calculate totals
        total_memory_gb = sum(app['memory_gb'] for app in inactive_apps)

        # Group by priority
        high_priority = [app for app in inactive_apps if app['priority'] == 'high']
        medium_priority = [app for app in inactive_apps if app['priority'] == 'medium']

        return {
            'timestamp': datetime.now().isoformat(),
            'inactive_timeout_hours': self.inactive_timeout_hours,
            'min_memory_mb': self.min_memory_mb,
            'inactive_apps': inactive_apps,
            'high_priority_apps': high_priority,
            'medium_priority_apps': medium_priority,
            'total_inactive_count': len(inactive_apps),
            'total_potential_savings_gb': round(total_memory_gb * 0.8, 2),  # 80% recoverable
            'recommendations': self._generate_recommendations(inactive_apps)
        }

    def _generate_recommendations(self, inactive_apps: list) -> list:
        """Generate actionable hibernation recommendations"""
        if not inactive_apps:
            return []

        recommendations = []

        # Group apps by priority and suspension safety
        suspendable_high = [app for app in inactive_apps
                           if app['priority'] == 'high' and app['can_suspend']]
        suspendable_medium = [app for app in inactive_apps
                             if app['priority'] == 'medium' and app['can_suspend']]

        # High priority hibernation targets
        if suspendable_high:
            total_savings = sum(app['memory_gb'] for app in suspendable_high)
            recommendations.append({
                'priority': 'critical',
                'action': 'hibernate_high_priority_apps',
                'description': f"Hibernate {len(suspendable_high)} high-priority inactive apps",
                'apps': [app['app_name'] for app in suspendable_high[:5]],
                'app_count': len(suspendable_high),
                'expected_savings_gb': round(total_savings * 0.8, 2),
                'method': 'graceful_quit',
                'risk': 'low',
                'impact': 'App state preserved, can be restored'
            })

        # Medium priority hibernation targets
        if suspendable_medium:
            total_savings = sum(app['memory_gb'] for app in suspendable_medium)
            recommendations.append({
                'priority': 'high',
                'action': 'hibernate_medium_priority_apps',
                'description': f"Hibernate {len(suspendable_medium)} medium-priority inactive apps",
                'apps': [app['app_name'] for app in suspendable_medium[:5]],
                'app_count': len(suspendable_medium),
                'expected_savings_gb': round(total_savings * 0.8, 2),
                'method': 'graceful_quit',
                'risk': 'low'
            })

        # Bulk hibernation if many apps inactive
        if len(inactive_apps) >= 5:
            total_savings = sum(app['memory_gb'] for app in inactive_apps if app['can_suspend'])
            recommendations.append({
                'priority': 'high',
                'action': 'bulk_hibernate',
                'description': f"Hibernate all {len(inactive_apps)} inactive apps",
                'expected_savings_gb': round(total_savings * 0.8, 2),
                'method': 'automated_hibernation',
                'risk': 'low',
                'estimated_time': f"{len(inactive_apps) * 3} seconds"
            })

        return recommendations

    def get_app_hibernation_impact(self, app_name: str) -> dict:
        """
        Estimate impact of hibernating a specific app
        """
        activity = HibernationUtils.get_app_activity_level(app_name)

        if 'error' in activity:
            return {
                'app_name': app_name,
                'can_analyze': False,
                'error': activity['error']
            }

        # Estimate recovery (80% of memory, 20% remains in swap)
        memory_recovery = activity['memory_gb'] * 0.8

        return {
            'app_name': app_name,
            'current_memory_gb': activity['memory_gb'],
            'expected_savings_gb': round(memory_recovery, 2),
            'helper_count': activity['helper_count'],
            'activity_level': activity['activity_level'],
            'can_suspend': activity['can_suspend'],
            'recommendation': 'hibernate' if activity['activity_level'] == 'idle' else 'monitor',
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save inactive app detection report"""
        report = self.analyze_inactive_apps()
        report_json = json.dumps(report, indent=2)

        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report_json)
                click.echo(f"Report saved to: {output_path}")
            except Exception as e:
                click.echo(f"Warning: Could not save report: {e}", err=True)

        return report_json


@click.command()
@click.option('--format', type=click.Choice(['human', 'json']), default='human',
              help='Output format (human-readable or JSON)')
@click.option('--output', type=click.Path(), default=None,
              help='Save JSON report to file')
def main(format: str, output: str):
    """
    Inactive App Detector (Agent 14)

    Identifies applications that are idle for extended periods with
    high memory usage and recommends hibernation actions.
    """
    start_time = time.time()

    # Initialize detector
    detector = InactiveAppDetector()

    # Analyze inactive apps
    report = detector.analyze_inactive_apps()

    # Calculate execution time
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 3)

    if format == 'json':
        click.echo(json.dumps(report, indent=2))
        return 0

    # Human-readable format
    click.echo("=== Inactive App Detector (Agent 14) ===\n")
    click.echo(f"Timestamp: {report['timestamp']}")
    click.echo(f"Inactive Timeout: {report['inactive_timeout_hours']} hours")
    click.echo(f"Memory Threshold: {report['min_memory_mb']} MB\n")

    click.echo(f"Total Inactive Apps: {report['total_inactive_count']}")
    click.echo(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

    if report['inactive_apps']:
        click.echo("=== Inactive Apps ===")
        click.echo(f"{'App Name':30s}  {'Memory':>8s}  {'CPU':>7s}  {'Priority':>10s}  {'Can Suspend':>12s}")
        click.echo("-" * 80)
        for app in report['inactive_apps'][:15]:
            suspend_status = "YES" if app['can_suspend'] else "NO"
            click.echo(f"{app['app_name']:30s}  {app['memory_gb']:6.2f} GB  {app['cpu_percent']:5.2f}%  {app['priority']:>10s}  {suspend_status:>12s}")

        if len(report['inactive_apps']) > 15:
            click.echo(f"\n... and {len(report['inactive_apps']) - 15} more apps")

    if report.get('high_priority_apps'):
        click.echo(f"\n=== High Priority Targets ({len(report['high_priority_apps'])} apps) ===")
        high_memory = sum(app['memory_gb'] for app in report['high_priority_apps'])
        click.echo(f"Total Memory: {high_memory:.2f} GB")
        for app in report['high_priority_apps'][:5]:
            click.echo(f"  {app['app_name']:30s}  {app['memory_gb']:6.2f} GB")

    if report['recommendations']:
        click.echo("\n=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            click.echo(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            click.echo(f"     Action: {rec['action']}")
            if 'apps' in rec:
                click.echo(f"     Apps: {', '.join(rec['apps'][:3])}")
                if rec['app_count'] > 3:
                    click.echo(f"           ... and {rec['app_count'] - 3} more")
            if 'app_count' in rec:
                click.echo(f"     Count: {rec['app_count']} apps")
            click.echo(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
            click.echo(f"     Method: {rec.get('method', 'N/A')}")
            click.echo(f"     Risk: {rec.get('risk', 'N/A')}")
            if 'impact' in rec:
                click.echo(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                click.echo(f"     Est. Time: {rec['estimated_time']}")

    click.echo(f"\nExecution time: {execution_time:.3f}s")

    # Save report if requested
    if output:
        detector.generate_report(Path(output))

    return 0


if __name__ == '__main__':
    sys.exit(main())
