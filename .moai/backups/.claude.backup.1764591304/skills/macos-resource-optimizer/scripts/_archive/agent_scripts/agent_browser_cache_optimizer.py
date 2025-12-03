#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
#   "psutil>=5.9.8",
# ]
# ///
"""
Agent 13: Browser Cache Optimizer
Analyzes and optimizes browser cache sizes
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 2
"""

import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import click
from browser_utils import BrowserUtils


class BrowserCacheOptimizer:
    """
    Analyzes browser cache sizes and recommends cleanup
    """

    def __init__(self, config_path: Path = None):
        """Initialize optimizer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.browser_utils = BrowserUtils()

        # Get threshold from config
        self.clear_cache_threshold_mb = self.config.get('clear_cache_threshold_mb', 2000)

    def _load_config(self, config_path: Path) -> dict:
        """Load browser optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('browser_optimization', {})
        except Exception as e:
            if not hasattr(self, '_config_warning_shown'):
                click.echo(f"Warning: Could not load config: {e}", err=True)
                self._config_warning_shown = True
            return {
                'clear_cache_threshold_mb': 2000
            }

    def analyze_browser_caches(self) -> dict:
        """
        Analyze cache sizes for all running browsers
        Returns comprehensive cache analysis
        """
        running_browsers = BrowserUtils.detect_running_browsers()

        if not running_browsers:
            return {
                'timestamp': datetime.now().isoformat(),
                'browsers_analyzed': 0,
                'cache_data': [],
                'total_cache_gb': 0,
                'cleanup_targets': [],
                'total_potential_savings_gb': 0
            }

        cache_data = []
        cleanup_targets = []
        total_cache_gb = 0
        total_potential_savings = 0

        for browser in running_browsers:
            cache_info = BrowserUtils.get_browser_cache_size(browser)
            cache_gb = cache_info['cache_gb']
            cache_mb = cache_info.get('cache_mb', cache_gb * 1024)

            cache_data.append({
                'browser': browser,
                'cache_gb': cache_gb,
                'cache_mb': round(cache_mb, 2),
                'path': cache_info['path'],
                'exceeds_threshold': cache_mb > self.clear_cache_threshold_mb
            })

            total_cache_gb += cache_gb

            # Check if exceeds threshold
            if cache_mb > self.clear_cache_threshold_mb:
                # Estimate 80% can be safely cleared
                potential_savings = cache_gb * 0.8

                cleanup_targets.append({
                    'browser': browser,
                    'cache_gb': cache_gb,
                    'cache_mb': round(cache_mb, 2),
                    'threshold_mb': self.clear_cache_threshold_mb,
                    'excess_mb': round(cache_mb - self.clear_cache_threshold_mb, 2),
                    'potential_savings_gb': round(potential_savings, 2),
                    'priority': 'high' if cache_gb > 5 else 'medium',
                    'path': cache_info['path']
                })

                total_potential_savings += potential_savings

        # Sort cleanup targets by cache size (descending)
        cleanup_targets.sort(key=lambda x: x['cache_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'browsers_analyzed': len(running_browsers),
            'cache_threshold_mb': self.clear_cache_threshold_mb,
            'cache_data': cache_data,
            'total_cache_gb': round(total_cache_gb, 2),
            'cleanup_targets': cleanup_targets,
            'browsers_exceeding_threshold': len(cleanup_targets),
            'total_potential_savings_gb': round(total_potential_savings, 2),
            'recommendations': self._generate_recommendations(cleanup_targets)
        }

    def _generate_recommendations(self, cleanup_targets: list) -> list:
        """Generate actionable cache cleanup recommendations"""
        if not cleanup_targets:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'All browser caches within threshold',
                'expected_savings_gb': 0
            }]

        recommendations = []

        for target in cleanup_targets:
            browser = target['browser']

            # Determine cleanup strategy
            if target['cache_gb'] > 10:
                # Very large cache - aggressive cleanup
                recommendations.append({
                    'priority': 'critical',
                    'action': 'full_cache_clear',
                    'browser': browser,
                    'description': f"Clear {target['cache_gb']:.1f} GB cache (critical size)",
                    'method': 'system_cache_clear',
                    'expected_savings_gb': target['potential_savings_gb'],
                    'risk': 'low',
                    'impact': 'Temporary slowdown on next browser start'
                })
            elif target['cache_gb'] > 5:
                # Large cache - full clear recommended
                recommendations.append({
                    'priority': 'high',
                    'action': 'full_cache_clear',
                    'browser': browser,
                    'description': f"Clear {target['cache_gb']:.1f} GB cache",
                    'method': 'system_cache_clear',
                    'expected_savings_gb': target['potential_savings_gb'],
                    'risk': 'low'
                })
            else:
                # Moderate cache - partial clear
                recommendations.append({
                    'priority': 'medium',
                    'action': 'partial_cache_clear',
                    'browser': browser,
                    'description': f"Clear old cache data ({target['cache_gb']:.1f} GB)",
                    'method': 'age_based_cleanup',
                    'expected_savings_gb': target['potential_savings_gb'],
                    'risk': 'minimal'
                })

        return recommendations

    def get_cache_breakdown(self, browser: str) -> dict:
        """
        Get detailed breakdown of cache contents for a browser
        """
        cache_info = BrowserUtils.get_browser_cache_size(browser)
        cache_path = Path(cache_info['path']).expanduser()

        if not cache_path.exists():
            return {
                'browser': browser,
                'cache_exists': False,
                'path': str(cache_path)
            }

        breakdown = {
            'browser': browser,
            'cache_exists': True,
            'path': str(cache_path),
            'total_size_gb': cache_info['cache_gb'],
            'subdirectories': []
        }

        try:
            # Get subdirectories and their sizes
            for subdir in cache_path.iterdir():
                if subdir.is_dir():
                    try:
                        result = subprocess.run(
                            ['du', '-sh', str(subdir)],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if result.returncode == 0:
                            size_str = result.stdout.split()[0]
                            breakdown['subdirectories'].append({
                                'name': subdir.name,
                                'size': size_str
                            })
                    except:
                        continue

            # Sort by name
            breakdown['subdirectories'].sort(key=lambda x: x['name'])

        except Exception as e:
            click.echo(f"Warning: Could not analyze cache breakdown: {e}", err=True)

        return breakdown

    def estimate_cache_impact(self) -> dict:
        """
        Estimate overall impact of cache cleanup
        """
        analysis = self.analyze_browser_caches()

        # Calculate memory pressure reduction
        # Cache cleanup doesn't directly free RAM, but reduces disk I/O
        # which can indirectly reduce memory pressure

        impact = {
            'timestamp': datetime.now().isoformat(),
            'disk_space_savings_gb': analysis['total_potential_savings_gb'],
            'estimated_ram_pressure_reduction': 'low',  # Cache cleanup has indirect RAM benefit
            'performance_impact': {
                'short_term': 'negative',  # Slower first loads
                'long_term': 'positive',   # Better overall performance
                'rebuild_time_estimate': '5-15 minutes per browser'
            },
            'recommendations': {
                'best_time': 'Before system restart or overnight',
                'user_impact': 'Minimal if done when browser closed',
                'frequency': 'Monthly for caches >5 GB'
            }
        }

        # Adjust impact based on total cache size
        if analysis['total_cache_gb'] > 20:
            impact['estimated_ram_pressure_reduction'] = 'medium'
        elif analysis['total_cache_gb'] > 50:
            impact['estimated_ram_pressure_reduction'] = 'high'

        return impact

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save cache optimization report"""
        report = self.analyze_browser_caches()
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
    Browser Cache Optimizer (Agent 13)

    Analyzes browser cache sizes and recommends cleanup actions
    for memory optimization.
    """
    start_time = time.time()

    # Initialize optimizer
    optimizer = BrowserCacheOptimizer()

    # Analyze caches
    report = optimizer.analyze_browser_caches()

    # Calculate execution time
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 3)

    if format == 'json':
        click.echo(json.dumps(report, indent=2))
        return 0

    # Human-readable format
    click.echo("=== Browser Cache Optimizer (Agent 13) ===\n")
    click.echo(f"Timestamp: {report['timestamp']}")
    click.echo(f"Browsers Analyzed: {report['browsers_analyzed']}")
    click.echo(f"Cache Threshold: {report['cache_threshold_mb']} MB\n")

    click.echo(f"Total Cache Size: {report['total_cache_gb']} GB")
    click.echo(f"Browsers Exceeding Threshold: {report['browsers_exceeding_threshold']}")
    click.echo(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

    if report['cache_data']:
        click.echo("Browser Caches:")
        for cache in report['cache_data']:
            status = "EXCEEDS" if cache['exceeds_threshold'] else "OK"
            click.echo(f"  {cache['browser']:10s}  {cache['cache_gb']:6.2f} GB  [{status}]")

    if report['cleanup_targets']:
        click.echo("\nCleanup Targets:")
        for i, target in enumerate(report['cleanup_targets'], 1):
            click.echo(f"\n  {i}. {target['browser'].upper()} [{target['priority'].upper()}]")
            click.echo(f"     Cache: {target['cache_gb']} GB ({target['cache_mb']:.0f} MB)")
            click.echo(f"     Excess: {target['excess_mb']:.0f} MB over threshold")
            click.echo(f"     Potential Savings: {target['potential_savings_gb']} GB")
            click.echo(f"     Path: {target['path']}")

        click.echo("\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            click.echo(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            click.echo(f"     Action: {rec['action']}")
            click.echo(f"     Method: {rec.get('method', 'N/A')}")
            click.echo(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
            if 'risk' in rec:
                click.echo(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                click.echo(f"     Impact: {rec['impact']}")
    else:
        click.echo("All browser caches within threshold. No cleanup needed.")

    # Get impact estimate
    click.echo("\n=== Cache Cleanup Impact ===")
    impact = optimizer.estimate_cache_impact()

    click.echo(f"Disk Space Savings: {impact['disk_space_savings_gb']} GB")
    click.echo(f"RAM Pressure Reduction: {impact['estimated_ram_pressure_reduction']}")
    click.echo(f"\nPerformance Impact:")
    click.echo(f"  Short-term: {impact['performance_impact']['short_term']}")
    click.echo(f"  Long-term: {impact['performance_impact']['long_term']}")
    click.echo(f"  Rebuild Time: {impact['performance_impact']['rebuild_time_estimate']}")
    click.echo(f"\nBest Practices:")
    click.echo(f"  Best Time: {impact['recommendations']['best_time']}")
    click.echo(f"  User Impact: {impact['recommendations']['user_impact']}")
    click.echo(f"  Frequency: {impact['recommendations']['frequency']}")

    click.echo(f"\nExecution time: {execution_time:.3f}s")

    # Save report if requested
    if output:
        optimizer.generate_report(Path(output))

    return 0


if __name__ == '__main__':
    sys.exit(main())
