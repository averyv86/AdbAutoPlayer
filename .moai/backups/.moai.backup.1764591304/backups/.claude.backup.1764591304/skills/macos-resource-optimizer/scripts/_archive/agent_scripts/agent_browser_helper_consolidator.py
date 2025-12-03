#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1.0",
#   "psutil>=5.9.0",
# ]
# ///
"""
Agent 12: Browser Helper Consolidator
Identifies and consolidates excessive browser helper processes
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 2
Primary Target: Arc/Dia 79 helpers → ~30 target (5.41 GB potential savings)
"""

import json
import sys
import time
import click
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from browser_utils import BrowserUtils
from ram_utils import RAMUtils

class BrowserHelperConsolidator:
    """
    Identifies browsers with excessive helpers and recommends consolidation
    """

    def __init__(self, config_path: Path = None):
        """Initialize consolidator with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.patterns = self._load_patterns()
        self.browser_utils = BrowserUtils()
        self.ram_utils = RAMUtils()

    def _load_config(self, config_path: Path) -> dict:
        """Load browser optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('browser_optimization', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'max_helpers_per_browser': 30,
                'browsers': {
                    'arc': {'max_helpers': 30},
                    'chrome': {'max_helpers': 25},
                    'safari': {'max_helpers': 15},
                    'firefox': {'max_helpers': 20}
                }
            }

    def _load_patterns(self) -> dict:
        """Load RAM patterns configuration"""
        patterns_path = Path(__file__).parent.parent / 'config' / 'ram-patterns.json'
        try:
            with open(patterns_path, 'r') as f:
                patterns = json.load(f)
                return patterns.get('browser_helpers', {})
        except Exception as e:
            print(f"Warning: Could not load patterns: {e}")
            return {}

    def analyze_browser_helpers(self, browser: str = None) -> dict:
        """
        Analyze browser helper processes and identify consolidation opportunities
        If browser is None, analyzes all running browsers
        """
        browsers_to_check = [browser] if browser else BrowserUtils.detect_running_browsers()

        if not browsers_to_check:
            return {
                'timestamp': datetime.now().isoformat(),
                'browsers_analyzed': 0,
                'consolidation_targets': [],
                'total_potential_savings_gb': 0
            }

        consolidation_targets = []
        total_potential_savings = 0

        for browser_key in browsers_to_check:
            target = self._analyze_single_browser(browser_key)
            if target:
                consolidation_targets.append(target)
                total_potential_savings += target['potential_savings_gb']

        # Sort by potential savings (descending)
        consolidation_targets.sort(key=lambda x: x['potential_savings_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'browsers_analyzed': len(browsers_to_check),
            'consolidation_targets': consolidation_targets,
            'total_browsers_exceeding_limit': len(consolidation_targets),
            'total_potential_savings_gb': round(total_potential_savings, 2),
            'recommendations': self._generate_recommendations(consolidation_targets)
        }

    def _analyze_single_browser(self, browser_key: str) -> dict:
        """Analyze a single browser for helper consolidation"""
        # Get helper counts
        helper_counts = BrowserUtils.count_helpers_by_type(browser_key)
        total_helpers = helper_counts['total_helpers']

        # Get configured max helpers
        browser_config = self.config.get('browsers', {}).get(browser_key, {})
        max_helpers = browser_config.get('max_helpers', self.config.get('max_helpers_per_browser', 30))

        # Check if exceeds limit
        if total_helpers <= max_helpers:
            return None

        # Get memory breakdown
        memory_data = BrowserUtils.calculate_browser_memory(browser_key)

        # Calculate excess helpers
        excess_helpers = total_helpers - max_helpers

        # Estimate potential savings
        # Assume we can consolidate excess helpers and free 40% of their memory
        helpers_memory_gb = memory_data['breakdown'].get('renderer', {}).get('memory_gb', 0) + \
                           memory_data['breakdown'].get('other_helper', {}).get('memory_gb', 0)

        if total_helpers > 0:
            avg_helper_memory = helpers_memory_gb / total_helpers
            potential_savings = excess_helpers * avg_helper_memory * 0.4
        else:
            potential_savings = 0

        return {
            'browser': browser_key,
            'total_helpers': total_helpers,
            'max_helpers': max_helpers,
            'excess_helpers': excess_helpers,
            'helper_breakdown': helper_counts,
            'total_memory_gb': memory_data['total_gb'],
            'helpers_memory_gb': round(helpers_memory_gb, 2),
            'potential_savings_gb': round(potential_savings, 2),
            'severity': self._determine_severity(excess_helpers, max_helpers),
            'priority': 'critical' if potential_savings > 3 else 'high' if potential_savings > 1 else 'medium'
        }

    def _determine_severity(self, excess: int, max_allowed: int) -> str:
        """Determine severity based on excess helpers"""
        ratio = excess / max_allowed if max_allowed > 0 else 0

        if ratio >= 1.5:  # 150%+ over limit
            return 'critical'
        elif ratio >= 0.5:  # 50-150% over limit
            return 'high'
        elif ratio >= 0.2:  # 20-50% over limit
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(self, targets: list) -> list:
        """Generate actionable recommendations for helper consolidation"""
        if not targets:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'All browsers within helper limits',
                'expected_savings_gb': 0
            }]

        recommendations = []

        for target in targets:
            browser = target['browser']
            excess = target['excess_helpers']

            # Strategy based on helper types
            renderer_count = target['helper_breakdown']['renderer']
            other_count = target['helper_breakdown']['other']

            if renderer_count > target['max_helpers'] * 0.7:
                # Mostly renderer helpers (tabs)
                recommendations.append({
                    'priority': target['priority'],
                    'action': 'consolidate_tab_renderers',
                    'browser': browser,
                    'description': f"Consolidate {renderer_count} renderer helpers by closing/suspending tabs",
                    'target_reduction': excess,
                    'expected_savings_gb': target['potential_savings_gb'],
                    'strategy': 'tab_management'
                })
            else:
                # Mixed helpers
                recommendations.append({
                    'priority': target['priority'],
                    'action': 'restart_browser',
                    'browser': browser,
                    'description': f"Restart {browser} to consolidate {excess} excess helpers",
                    'target_reduction': excess,
                    'expected_savings_gb': target['potential_savings_gb'],
                    'strategy': 'browser_restart'
                })

            # Additional GPU helper recommendation
            if target['helper_breakdown']['gpu'] > 3:
                recommendations.append({
                    'priority': 'medium',
                    'action': 'optimize_gpu_helpers',
                    'browser': browser,
                    'description': f"Reduce {target['helper_breakdown']['gpu']} GPU helpers via settings",
                    'strategy': 'settings_optimization'
                })

        return recommendations

    def get_detailed_helper_analysis(self, browser: str) -> dict:
        """
        Get detailed analysis of a specific browser's helper processes
        """
        grouped = BrowserUtils.group_browser_helpers(browser)
        memory_data = BrowserUtils.calculate_browser_memory(browser)

        # Analyze each helper type
        analysis = {
            'browser': browser,
            'timestamp': datetime.now().isoformat(),
            'total_memory_gb': memory_data['total_gb'],
            'process_count': memory_data['process_count'],
            'helper_types': {}
        }

        for helper_type, processes in grouped.items():
            if helper_type == 'main':
                continue

            type_memory = sum(p['rss_gb'] for p in processes)

            analysis['helper_types'][helper_type] = {
                'count': len(processes),
                'memory_gb': round(type_memory, 2),
                'avg_memory_mb': round(type_memory * 1024 / len(processes), 2) if processes else 0,
                'largest_process': max(processes, key=lambda p: p['rss_gb']) if processes else None
            }

        return analysis

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save helper consolidation report"""
        report = self.analyze_browser_helpers()
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
    Agent 12: Browser Helper Consolidator
    Identifies and consolidates excessive browser helper processes
    """
    start_time = time.time()

    # Initialize consolidator
    consolidator = BrowserHelperConsolidator()

    # Analyze helpers
    report = consolidator.analyze_browser_helpers()

    # Get detailed analysis if targets exist
    detailed_analysis = None
    if report['consolidation_targets']:
        top_target = report['consolidation_targets'][0]
        detailed_analysis = consolidator.get_detailed_helper_analysis(top_target['browser'])

    # Calculate execution time
    execution_time = time.time() - start_time

    if format == 'json':
        # JSON output for coordinator
        output = {
            "agent": "browser_helper_consolidator",
            "status": "success",
            "execution_time_seconds": round(execution_time, 3),
            "timestamp": report['timestamp'],
            "summary": {
                "browsers_analyzed": report['browsers_analyzed'],
                "browsers_exceeding_limits": report['total_browsers_exceeding_limit'],
                "total_potential_savings_gb": report['total_potential_savings_gb']
            },
            "consolidation_targets": report['consolidation_targets'],
            "recommendations": report['recommendations'][:5],  # Top 5
            "detailed_analysis": detailed_analysis
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Text output for humans
        click.echo("=== Browser Helper Consolidator (Agent 12) ===\n")
        click.echo(f"Timestamp: {report['timestamp']}")
        click.echo(f"Browsers Analyzed: {report['browsers_analyzed']}")
        click.echo(f"Browsers Exceeding Limits: {report['total_browsers_exceeding_limit']}")
        click.echo(f"Total Potential Savings: {report['total_potential_savings_gb']} GB\n")

        if report['consolidation_targets']:
            click.echo("Consolidation Targets:")
            for i, target in enumerate(report['consolidation_targets'], 1):
                click.echo(f"\n  {i}. {target['browser'].upper()} [{target['severity'].upper()}]")
                click.echo(f"     Total Helpers: {target['total_helpers']} (Max: {target['max_helpers']})")
                click.echo(f"     Excess: {target['excess_helpers']} helpers")
                click.echo(f"     Memory: {target['total_memory_gb']} GB (Helpers: {target['helpers_memory_gb']} GB)")
                click.echo(f"     Potential Savings: {target['potential_savings_gb']} GB")
                click.echo(f"     Breakdown: R:{target['helper_breakdown']['renderer']} " +
                          f"G:{target['helper_breakdown']['gpu']} " +
                          f"N:{target['helper_breakdown']['network']} " +
                          f"O:{target['helper_breakdown']['other']}")

            click.echo("\nRecommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                click.echo(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
                click.echo(f"     Action: {rec['action']}")
                click.echo(f"     Strategy: {rec.get('strategy', 'N/A')}")
                if 'expected_savings_gb' in rec:
                    click.echo(f"     Expected Savings: {rec['expected_savings_gb']} GB")
        else:
            click.echo("All browsers within helper limits. No consolidation needed.")

        # Detailed analysis for top target
        if detailed_analysis:
            click.echo(f"\n=== Detailed Analysis: {detailed_analysis['browser'].upper()} ===")
            for helper_type, data in detailed_analysis['helper_types'].items():
                click.echo(f"\n{helper_type.upper()} Helpers:")
                click.echo(f"  Count: {data['count']}")
                click.echo(f"  Memory: {data['memory_gb']} GB")
                click.echo(f"  Avg per Helper: {data['avg_memory_mb']} MB")
                if data['largest_process']:
                    click.echo(f"  Largest: {data['largest_process']['rss_mb']:.0f} MB (PID {data['largest_process']['pid']})")

        click.echo(f"\nExecution time: {execution_time:.3f}s")

        # Save report
        output_path = Path(__file__).parent.parent / 'data' / 'browser-helper-consolidation.json'
        consolidator.generate_report(output_path)


if __name__ == '__main__':
    main()
