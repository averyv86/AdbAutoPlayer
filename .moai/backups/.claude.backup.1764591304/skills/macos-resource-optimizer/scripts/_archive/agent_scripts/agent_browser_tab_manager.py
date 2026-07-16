#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1.0",
#   "psutil>=5.9.0",
# ]
# ///
"""
Agent 11: Browser Tab Manager
Identifies and manages high-memory browser tabs
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 2
"""

import json
import sys
import time
import click
from pathlib import Path
from datetime import datetime
from browser_utils import BrowserUtils
from ram_utils import RAMUtils

class BrowserTabManager:
    """
    Manages browser tabs with high memory usage
    Identifies tabs exceeding threshold for optimization
    """

    def __init__(self, config_path: Path = None):
        """Initialize tab manager with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.browser_utils = BrowserUtils()
        self.ram_utils = RAMUtils()

        # Get thresholds from config
        self.tab_memory_limit_mb = self.config.get('tab_memory_limit_mb', 500)
        self.inactive_timeout_minutes = self.config.get('inactive_tab_timeout_minutes', 30)
        self.suspend_inactive = self.config.get('suspend_inactive_tabs', True)

    def _load_config(self, config_path: Path) -> dict:
        """Load browser optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('browser_optimization', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'tab_memory_limit_mb': 500,
                'suspend_inactive_tabs': True,
                'inactive_tab_timeout_minutes': 30
            }

    def analyze_browser_tabs(self, browser: str = None) -> dict:
        """
        Analyze browser tabs and identify high-memory consumers
        If browser is None, analyzes all running browsers
        """
        browsers_to_check = [browser] if browser else BrowserUtils.detect_running_browsers()

        if not browsers_to_check:
            return {
                'timestamp': datetime.now().isoformat(),
                'browsers_analyzed': 0,
                'high_memory_tabs': [],
                'total_potential_savings_gb': 0
            }

        high_memory_tabs = []
        total_potential_savings = 0

        for browser_key in browsers_to_check:
            # Get high-memory helpers (proxies for tabs in most browsers)
            high_memory = BrowserUtils.find_high_memory_helpers(
                browser_key,
                self.tab_memory_limit_mb
            )

            for helper in high_memory:
                # For renderer helpers, each typically represents a tab or group of tabs
                if helper['process_type'] == 'renderer':
                    potential_savings = helper['rss_gb'] * 0.7  # Estimate 70% can be freed by suspending

                    high_memory_tabs.append({
                        'browser': browser_key,
                        'pid': helper['pid'],
                        'memory_gb': helper['rss_gb'],
                        'memory_mb': helper['rss_mb'],
                        'process_type': helper['process_type'],
                        'potential_savings_gb': round(potential_savings, 2),
                        'recommended_action': 'suspend' if self.suspend_inactive else 'close',
                        'priority': 'high' if helper['rss_mb'] > 1000 else 'medium'
                    })

                    total_potential_savings += potential_savings

        # Sort by memory (descending)
        high_memory_tabs.sort(key=lambda x: x['memory_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'browsers_analyzed': len(browsers_to_check),
            'tab_memory_limit_mb': self.tab_memory_limit_mb,
            'high_memory_tabs': high_memory_tabs,
            'total_tabs_over_limit': len(high_memory_tabs),
            'total_memory_gb': round(sum(t['memory_gb'] for t in high_memory_tabs), 2),
            'total_potential_savings_gb': round(total_potential_savings, 2),
            'recommendations': self._generate_recommendations(high_memory_tabs)
        }

    def _generate_recommendations(self, high_memory_tabs: list) -> list:
        """Generate actionable recommendations for tab management"""
        if not high_memory_tabs:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'No tabs exceeding memory threshold',
                'expected_savings_gb': 0
            }]

        recommendations = []

        # Group by browser
        by_browser = {}
        for tab in high_memory_tabs:
            browser = tab['browser']
            if browser not in by_browser:
                by_browser[browser] = []
            by_browser[browser].append(tab)

        # Generate per-browser recommendations
        for browser, tabs in by_browser.items():
            total_savings = sum(t['potential_savings_gb'] for t in tabs)

            if len(tabs) >= 5:
                recommendations.append({
                    'priority': 'high',
                    'action': 'bulk_suspend_tabs',
                    'browser': browser,
                    'description': f"Suspend {len(tabs)} high-memory tabs in {browser}",
                    'tab_count': len(tabs),
                    'expected_savings_gb': round(total_savings, 2)
                })
            else:
                for tab in tabs:
                    recommendations.append({
                        'priority': tab['priority'],
                        'action': 'suspend_tab',
                        'browser': browser,
                        'description': f"Suspend tab using {tab['memory_mb']:.0f} MB",
                        'pid': tab['pid'],
                        'expected_savings_gb': tab['potential_savings_gb']
                    })

        # Sort by expected savings
        recommendations.sort(key=lambda x: x.get('expected_savings_gb', 0), reverse=True)

        return recommendations

    def get_browser_tab_summary(self) -> dict:
        """
        Get summary of all browser tabs across all browsers
        """
        analysis = BrowserUtils.analyze_all_browsers()

        summary = {
            'timestamp': datetime.now().isoformat(),
            'browsers': {},
            'totals': {
                'browsers_running': len(analysis),
                'total_memory_gb': 0,
                'total_helpers': 0,
                'optimization_potential_gb': 0
            }
        }

        for browser, data in analysis.items():
            summary['browsers'][browser] = {
                'memory_gb': data['memory']['total_gb'],
                'process_count': data['memory']['process_count'],
                'helper_count': data['helpers']['total_helpers'],
                'high_memory_helpers': data['high_memory_helpers'],
                'optimization_potential_gb': data['optimization_potential_gb']
            }

            # Update totals
            summary['totals']['total_memory_gb'] += data['memory']['total_gb']
            summary['totals']['total_helpers'] += data['helpers']['total_helpers']
            summary['totals']['optimization_potential_gb'] += data['optimization_potential_gb']

        # Round totals
        summary['totals']['total_memory_gb'] = round(summary['totals']['total_memory_gb'], 2)
        summary['totals']['optimization_potential_gb'] = round(summary['totals']['optimization_potential_gb'], 2)

        return summary

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save tab management report"""
        report = self.analyze_browser_tabs()
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
@click.option('--format', type=click.Choice(['json', 'text']), default='text',
              help='Output format (json for coordinator, text for human)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def main(format, verbose):
    """
    Agent 11: Browser Tab Manager
    Identifies and manages high-memory browser tabs
    """
    start_time = time.time()

    # Initialize manager
    manager = BrowserTabManager()

    # Get tab analysis
    report = manager.analyze_browser_tabs()

    # Get browser summary
    summary = manager.get_browser_tab_summary()

    # Calculate execution time
    execution_time = time.time() - start_time

    if format == 'json':
        # JSON output for coordinator
        output = {
            "agent": "browser_tab_manager",
            "status": "success",
            "execution_time_seconds": round(execution_time, 3),
            "timestamp": report['timestamp'],
            "summary": {
                "browsers_analyzed": report['browsers_analyzed'],
                "tab_memory_limit_mb": report['tab_memory_limit_mb'],
                "high_memory_tabs_count": report['total_tabs_over_limit'],
                "total_memory_gb": report['total_memory_gb'],
                "potential_savings_gb": report['total_potential_savings_gb']
            },
            "high_memory_tabs": report['high_memory_tabs'][:10],  # Top 10
            "recommendations": report['recommendations'][:5],  # Top 5
            "browser_summary": summary,
            "metrics": {
                "total_browsers": summary['totals']['browsers_running'],
                "total_browser_memory_gb": summary['totals']['total_memory_gb'],
                "total_helpers": summary['totals']['total_helpers'],
                "total_optimization_potential_gb": summary['totals']['optimization_potential_gb']
            }
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Text output for humans
        click.echo("=== Browser Tab Manager (Agent 11) ===\n")
        click.echo(f"Timestamp: {report['timestamp']}")
        click.echo(f"Browsers Analyzed: {report['browsers_analyzed']}")
        click.echo(f"Tab Memory Limit: {report['tab_memory_limit_mb']} MB\n")

        click.echo(f"High Memory Tabs: {report['total_tabs_over_limit']}")
        click.echo(f"Total Memory: {report['total_memory_gb']} GB")
        click.echo(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

        if report['high_memory_tabs']:
            click.echo("Top 10 High-Memory Tabs:")
            for i, tab in enumerate(report['high_memory_tabs'][:10], 1):
                click.echo(f"  {i}. [{tab['browser'].upper()}] PID {tab['pid']:6d}  "
                          f"{tab['memory_gb']:6.2f} GB  "
                          f"(~{tab['potential_savings_gb']:.2f} GB savings)")

            click.echo("\nRecommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                click.echo(f"  {i}. [{rec['priority'].upper()}] {rec['description']}")
                click.echo(f"     Action: {rec['action']}")
                click.echo(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
        else:
            click.echo("No tabs exceeding memory threshold.")

        # Browser summary
        click.echo("\n=== Browser Summary ===")
        for browser, data in summary['browsers'].items():
            click.echo(f"\n{browser.upper()}:")
            click.echo(f"  Memory: {data['memory_gb']} GB")
            click.echo(f"  Helpers: {data['helper_count']} (High: {data['high_memory_helpers']})")
            click.echo(f"  Optimization Potential: {data['optimization_potential_gb']} GB")

        click.echo(f"\nTotals:")
        click.echo(f"  Browsers: {summary['totals']['browsers_running']}")
        click.echo(f"  Total Memory: {summary['totals']['total_memory_gb']} GB")
        click.echo(f"  Total Helpers: {summary['totals']['total_helpers']}")
        click.echo(f"  Total Optimization Potential: {summary['totals']['optimization_potential_gb']} GB")

        click.echo(f"\nExecution time: {execution_time:.3f}s")

        # Save report
        output_path = Path(__file__).parent.parent / 'data' / 'browser-tab-analysis.json'
        manager.generate_report(output_path)


if __name__ == '__main__':
    main()
