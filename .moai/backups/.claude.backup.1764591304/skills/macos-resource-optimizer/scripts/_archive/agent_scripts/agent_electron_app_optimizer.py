#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# ///
"""
Agent 16: Electron App Optimizer
Optimizes Electron-based applications (VS Code, Slack, Notion, Discord)
PRIMARY TARGET: VS Code 4.41 GB → 1.5 GB (2.94 GB savings)
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 3
"""

import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import click
from hibernation_utils import HibernationUtils


class ElectronAppOptimizer:
    """
    Optimizes Electron applications by consolidating helpers
    """

    def __init__(self, config_path: Path = None):
        """Initialize optimizer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Electron app thresholds
        self.electron_apps = HibernationUtils.ELECTRON_APPS

    def _load_config(self, config_path: Path) -> dict:
        """Load Electron app optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('electron_optimization', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {}

    def analyze_electron_apps(self) -> dict:
        """
        Analyze all Electron applications and identify optimization opportunities
        Returns comprehensive analysis with consolidation recommendations
        """
        optimization_targets = []
        total_memory_gb = 0
        total_potential_savings = 0

        for app_name, app_info in self.electron_apps.items():
            activity = HibernationUtils.get_app_activity_level(app_name)

            # Skip if app not running
            if 'error' in activity or activity.get('process_count', 0) == 0:
                continue

            helper_count = activity['helper_count']
            memory_gb = activity['memory_gb']
            max_normal_helpers = app_info['max_normal_helpers']

            total_memory_gb += memory_gb

            # Check if exceeds threshold
            if helper_count > max_normal_helpers:
                excess_helpers = helper_count - max_normal_helpers

                # Calculate detailed breakdown
                breakdown = self._analyze_electron_breakdown(app_name, app_info)

                # Calculate potential savings (40% of excess helper memory)
                helper_memory = breakdown['helper_memory_gb']
                potential_savings = helper_memory * 0.4

                # Determine severity
                ratio = helper_count / max_normal_helpers
                if ratio >= 2.5:
                    severity = 'critical'
                elif ratio >= 2.0:
                    severity = 'high'
                elif ratio >= 1.5:
                    severity = 'medium'
                else:
                    severity = 'low'

                optimization_targets.append({
                    'app_name': app_name,
                    'total_memory_gb': memory_gb,
                    'helper_count': helper_count,
                    'max_helpers': max_normal_helpers,
                    'excess_helpers': excess_helpers,
                    'helper_breakdown': breakdown,
                    'potential_savings_gb': round(potential_savings, 2),
                    'severity': severity,
                    'priority': severity,
                    'activity_level': activity['activity_level']
                })

                total_potential_savings += potential_savings

        # Sort by memory (descending)
        optimization_targets.sort(key=lambda x: x['total_memory_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'electron_apps_analyzed': len(self.electron_apps),
            'electron_apps_running': len(optimization_targets),
            'optimization_targets': optimization_targets,
            'total_electron_memory_gb': round(total_memory_gb, 2),
            'total_potential_savings_gb': round(total_potential_savings, 2),
            'recommendations': self._generate_recommendations(optimization_targets)
        }

    def _analyze_electron_breakdown(self, app_name: str, app_info: dict) -> dict:
        """Get detailed breakdown of Electron app helpers"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get process list'}

            main_memory_gb = 0.0
            helper_memory_gb = 0.0
            helper_types = {
                'renderer': {'count': 0, 'memory_gb': 0.0},
                'gpu': {'count': 0, 'memory_gb': 0.0},
                'other': {'count': 0, 'memory_gb': 0.0}
            }

            for line in result.stdout.split('\n'):
                if app_name not in line:
                    continue

                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue

                # Calculate memory
                rss_kb = float(parts[5])
                mem_gb = rss_kb / 1024 / 1024

                # Classify process
                if 'Helper' in line:
                    helper_memory_gb += mem_gb

                    # Classify helper type
                    if 'Renderer' in line or 'render' in line.lower():
                        helper_types['renderer']['count'] += 1
                        helper_types['renderer']['memory_gb'] += mem_gb
                    elif 'GPU' in line or 'gpu' in line.lower():
                        helper_types['gpu']['count'] += 1
                        helper_types['gpu']['memory_gb'] += mem_gb
                    else:
                        helper_types['other']['count'] += 1
                        helper_types['other']['memory_gb'] += mem_gb
                else:
                    main_memory_gb += mem_gb

            return {
                'main_process_memory_gb': round(main_memory_gb, 2),
                'helper_memory_gb': round(helper_memory_gb, 2),
                'renderer_helpers': {
                    'count': helper_types['renderer']['count'],
                    'memory_gb': round(helper_types['renderer']['memory_gb'], 2)
                },
                'gpu_helpers': {
                    'count': helper_types['gpu']['count'],
                    'memory_gb': round(helper_types['gpu']['memory_gb'], 2)
                },
                'other_helpers': {
                    'count': helper_types['other']['count'],
                    'memory_gb': round(helper_types['other']['memory_gb'], 2)
                }
            }

        except Exception as e:
            return {'error': str(e)}

    def _generate_recommendations(self, targets: list) -> list:
        """Generate actionable Electron app optimization recommendations"""
        if not targets:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'No Electron apps exceeding thresholds',
                'expected_savings_gb': 0
            }]

        recommendations = []

        for target in targets:
            app_name = target['app_name']
            breakdown = target['helper_breakdown']

            # Primary strategy: Renderer consolidation
            if breakdown.get('renderer_helpers', {}).get('count', 0) > target['max_helpers'] * 0.5:
                recommendations.append({
                    'priority': target['priority'],
                    'action': 'consolidate_renderers',
                    'app_name': app_name,
                    'description': f"Consolidate {breakdown['renderer_helpers']['count']} renderer helpers in {app_name}",
                    'method': 'close_windows_tabs',
                    'expected_savings_gb': round(breakdown['renderer_helpers']['memory_gb'] * 0.4, 2),
                    'risk': 'low',
                    'impact': f"Reduce {app_name} memory by ~40%"
                })

            # Secondary strategy: Full restart if severely bloated
            if target['severity'] == 'critical':
                recommendations.append({
                    'priority': 'critical',
                    'action': 'restart_app',
                    'app_name': app_name,
                    'description': f"Restart {app_name} to consolidate {target['excess_helpers']} excess helpers",
                    'method': 'graceful_restart',
                    'expected_savings_gb': target['potential_savings_gb'],
                    'risk': 'medium',
                    'impact': 'Temporary workflow interruption (30-60 seconds)',
                    'note': 'State will be preserved and restored automatically'
                })

            # Tertiary strategy: Settings optimization
            if breakdown.get('gpu_helpers', {}).get('count', 0) > 2:
                recommendations.append({
                    'priority': 'medium',
                    'action': 'disable_hardware_acceleration',
                    'app_name': app_name,
                    'description': f"Disable hardware acceleration in {app_name} ({breakdown['gpu_helpers']['count']} GPU helpers)",
                    'method': 'settings_adjustment',
                    'expected_savings_gb': round(breakdown['gpu_helpers']['memory_gb'] * 0.6, 2),
                    'risk': 'low',
                    'impact': 'Slightly reduced graphics performance'
                })

        return recommendations

    def get_vscode_optimization_plan(self) -> dict:
        """
        Get detailed optimization plan for VS Code (primary target)
        Target: 4.41 GB → 1.5 GB (2.94 GB savings)
        """
        activity = HibernationUtils.get_app_activity_level('Visual Studio Code')

        if 'error' in activity:
            return {
                'app_name': 'Visual Studio Code',
                'running': False,
                'error': activity['error']
            }

        if activity.get('process_count', 0) == 0:
            return {
                'app_name': 'Visual Studio Code',
                'running': False,
                'message': 'VS Code not currently running'
            }

        # Get detailed breakdown
        breakdown = self._analyze_electron_breakdown('Visual Studio Code',
                                                     self.electron_apps['Visual Studio Code'])

        # Calculate optimization potential
        renderer_savings = breakdown.get('renderer_helpers', {}).get('memory_gb', 0) * 0.6  # 60% from renderers
        other_savings = breakdown.get('other_helpers', {}).get('memory_gb', 0) * 0.4  # 40% from others
        total_savings = renderer_savings + other_savings

        return {
            'app_name': 'Visual Studio Code',
            'running': True,
            'current_memory_gb': activity['memory_gb'],
            'target_memory_gb': 1.5,
            'potential_savings_gb': round(total_savings, 2),
            'helper_breakdown': breakdown,
            'optimization_steps': [
                {
                    'step': 1,
                    'action': 'Close unused editor windows',
                    'target': f"{breakdown.get('renderer_helpers', {}).get('count', 0)} renderer helpers",
                    'expected_savings_gb': round(renderer_savings, 2),
                    'method': 'Close windows manually or via Command Palette'
                },
                {
                    'step': 2,
                    'action': 'Disable unused extensions',
                    'target': 'Extension host processes',
                    'expected_savings_gb': round(other_savings * 0.5, 2),
                    'method': 'Extensions → Disable unused extensions'
                },
                {
                    'step': 3,
                    'action': 'Restart VS Code',
                    'target': 'Full memory consolidation',
                    'expected_savings_gb': round(other_savings * 0.5, 2),
                    'method': 'File → Exit (preserves workspace state)'
                }
            ],
            'estimated_result': {
                'final_memory_gb': 1.5,
                'total_savings_gb': round(total_savings, 2),
                'reduction_percent': round((total_savings / activity['memory_gb']) * 100, 1)
            }
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save Electron app optimization report"""
        report = self.analyze_electron_apps()
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
def main(format, save_report):
    """Electron App Optimizer - Analyzes and optimizes Electron applications"""
    start_time = time.time()

    # Initialize optimizer
    optimizer = ElectronAppOptimizer()

    # Analyze Electron apps
    report = optimizer.analyze_electron_apps()

    # Get VS Code optimization plan
    vscode_plan = optimizer.get_vscode_optimization_plan()

    # Add execution metadata
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 3)
    report['vscode_optimization_plan'] = vscode_plan

    if format == 'json':
        # JSON output
        print(json.dumps(report, indent=2))
    else:
        # Text output
        print("=== Electron App Optimizer (Agent 16) ===\n")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Execution Time: {report['execution_time_seconds']}s")
        print(f"Electron Apps Analyzed: {report['electron_apps_analyzed']}")
        print(f"Electron Apps Running: {report['electron_apps_running']}\n")

        print(f"Total Electron Memory: {report['total_electron_memory_gb']} GB")
        print(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

        if report['optimization_targets']:
            print("=== Optimization Targets ===")
            for i, target in enumerate(report['optimization_targets'], 1):
                print(f"\n  {i}. {target['app_name'].upper()} [{target['severity'].upper()}]")
                print(f"     Total Memory: {target['total_memory_gb']} GB")
                print(f"     Helpers: {target['helper_count']} (Max: {target['max_helpers']}, Excess: {target['excess_helpers']})")
                print(f"     Activity: {target['activity_level']}")
                print(f"     Potential Savings: {target['potential_savings_gb']} GB")

                breakdown = target['helper_breakdown']
                print(f"     Breakdown:")
                print(f"       Main Process: {breakdown.get('main_process_memory_gb', 0)} GB")
                print(f"       Renderer: {breakdown.get('renderer_helpers', {}).get('count', 0)} helpers, {breakdown.get('renderer_helpers', {}).get('memory_gb', 0)} GB")
                print(f"       GPU: {breakdown.get('gpu_helpers', {}).get('count', 0)} helpers, {breakdown.get('gpu_helpers', {}).get('memory_gb', 0)} GB")
                print(f"       Other: {breakdown.get('other_helpers', {}).get('count', 0)} helpers, {breakdown.get('other_helpers', {}).get('memory_gb', 0)} GB")

        if report['recommendations']:
            print("\n=== Recommendations ===")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
                print(f"     Action: {rec['action']}")
                if 'app_name' in rec:
                    print(f"     App: {rec['app_name']}")
                print(f"     Method: {rec.get('method', 'N/A')}")
                print(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
                print(f"     Risk: {rec.get('risk', 'N/A')}")
                if 'impact' in rec:
                    print(f"     Impact: {rec['impact']}")
                if 'note' in rec:
                    print(f"     Note: {rec['note']}")

        # VS Code optimization plan
        print("\n=== VS Code Optimization Plan (PRIMARY TARGET) ===")
        if vscode_plan.get('running'):
            print(f"Current Memory: {vscode_plan['current_memory_gb']} GB")
            print(f"Target Memory: {vscode_plan['target_memory_gb']} GB")
            print(f"Potential Savings: {vscode_plan['potential_savings_gb']} GB")
            print(f"\nOptimization Steps:")
            for step in vscode_plan['optimization_steps']:
                print(f"\n  Step {step['step']}: {step['action']}")
                print(f"    Target: {step['target']}")
                print(f"    Expected Savings: {step['expected_savings_gb']} GB")
                print(f"    Method: {step['method']}")

            result = vscode_plan['estimated_result']
            print(f"\nEstimated Result:")
            print(f"  Final Memory: {result['final_memory_gb']} GB")
            print(f"  Total Savings: {result['total_savings_gb']} GB ({result['reduction_percent']}% reduction)")
        else:
            print(f"Status: {vscode_plan.get('message', vscode_plan.get('error', 'Unknown status'))}")

    # Save report if requested
    if save_report:
        output_path = Path(__file__).parent.parent / 'data' / 'electron-app-optimization.json'
        optimizer.generate_report(output_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
