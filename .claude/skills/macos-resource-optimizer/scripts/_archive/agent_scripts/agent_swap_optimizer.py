#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# ///
"""
Agent 9: Swap Optimizer
Analyzes and reduces swap usage (target: 22.27 GB detected)
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
"""

import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from ram_utils import RAMUtils
import click


class SwapOptimizer:
    """
    Optimizes swap usage by identifying memory pressure sources
    """

    def __init__(self, config_path: Path = None):
        """Initialize optimizer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Swap thresholds
        self.critical_swap_gb = self.config.get('critical_swap_gb', 20)
        self.warning_swap_gb = self.config.get('warning_swap_gb', 10)
        self.target_swap_gb = self.config.get('target_swap_gb', 5)

    def _load_config(self, config_path: Path) -> dict:
        """Load swap optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('swap_optimization', {
                    'critical_swap_gb': 20,
                    'warning_swap_gb': 10,
                    'target_swap_gb': 5
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'critical_swap_gb': 20,
                'warning_swap_gb': 10,
                'target_swap_gb': 5
            }

    def analyze_swap_usage(self) -> dict:
        """
        Analyze current swap usage and identify optimization opportunities
        Returns comprehensive swap analysis with reduction recommendations
        """
        # Get current swap stats
        swap_stats = self._get_swap_statistics()

        if 'error' in swap_stats:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': swap_stats['error']
            }

        swap_used_gb = swap_stats['swap_used_gb']
        swap_free_gb = swap_stats['swap_free_gb']
        swap_total_gb = swap_used_gb + swap_free_gb

        # Determine severity
        if swap_used_gb >= self.critical_swap_gb:
            severity = 'critical'
        elif swap_used_gb >= self.warning_swap_gb:
            severity = 'warning'
        else:
            severity = 'normal'

        # Get memory pressure
        pressure_level, pressure_stats = RAMUtils.get_memory_pressure()

        # Identify swap contributors
        swap_contributors = self._identify_swap_contributors()

        # Calculate optimization potential
        potential_reduction = max(0, swap_used_gb - self.target_swap_gb)
        target_reduction_percent = (potential_reduction / swap_used_gb * 100) if swap_used_gb > 0 else 0

        return {
            'timestamp': datetime.now().isoformat(),
            'swap_statistics': {
                'swap_used_gb': swap_used_gb,
                'swap_free_gb': swap_free_gb,
                'swap_total_gb': swap_total_gb,
                'swap_utilization_percent': round((swap_used_gb / swap_total_gb * 100), 1) if swap_total_gb > 0 else 0
            },
            'severity': severity,
            'memory_pressure': pressure_level,
            'pageouts': pressure_stats.get('pageouts', 0),
            'swap_contributors': swap_contributors,
            'optimization_analysis': {
                'current_swap_gb': swap_used_gb,
                'target_swap_gb': self.target_swap_gb,
                'potential_reduction_gb': round(potential_reduction, 2),
                'target_reduction_percent': round(target_reduction_percent, 1)
            },
            'recommendations': self._generate_recommendations(
                swap_used_gb, severity, swap_contributors, potential_reduction
            )
        }

    def _get_swap_statistics(self) -> dict:
        """Get detailed swap statistics from vm_stat"""
        try:
            result = subprocess.run(
                ['vm_stat'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get vm_stat'}

            # Parse vm_stat output
            stats = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip().rstrip('.')

                    # Convert pages to GB (assuming 4KB page size)
                    if value.isdigit():
                        pages = int(value)
                        stats[key] = pages
                        stats[f"{key}_gb"] = round(pages * 4096 / (1024**3), 2)

            # Get swapusage for more accurate swap data
            swap_result = subprocess.run(
                ['sysctl', 'vm.swapusage'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if swap_result.returncode == 0:
                # Parse: vm.swapusage: total = 22528.00M  used = 22272.38M  free = 255.62M  (encrypted)
                swap_line = swap_result.stdout.strip()

                # Extract used swap
                if 'used = ' in swap_line:
                    used_part = swap_line.split('used = ')[1].split()[0]
                    used_value = float(used_part.rstrip('M'))
                    swap_used_gb = round(used_value / 1024, 2)
                else:
                    swap_used_gb = 0

                # Extract free swap
                if 'free = ' in swap_line:
                    free_part = swap_line.split('free = ')[1].split()[0]
                    free_value = float(free_part.rstrip('M'))
                    swap_free_gb = round(free_value / 1024, 2)
                else:
                    swap_free_gb = 0

                return {
                    'swap_used_gb': swap_used_gb,
                    'swap_free_gb': swap_free_gb,
                    'vm_stats': stats
                }

            return {'error': 'Could not get swapusage'}

        except Exception as e:
            return {'error': str(e)}

    def _identify_swap_contributors(self) -> list:
        """Identify processes contributing to swap pressure"""
        try:
            # Get all processes sorted by memory
            processes = RAMUtils.get_all_processes_memory()

            # Top 10 memory consumers (likely contributing to swap)
            contributors = []
            for proc in processes[:10]:
                contributors.append({
                    'pid': proc['pid'],
                    'name': proc['name'],
                    'memory_gb': proc['memory_gb'],
                    'memory_percent': proc['memory_percent'],
                    'contribution': 'high' if proc['memory_gb'] > 5 else 'medium' if proc['memory_gb'] > 2 else 'low'
                })

            return contributors

        except Exception as e:
            return []

    def _generate_recommendations(self, swap_gb: float, severity: str,
                                  contributors: list, potential_reduction: float) -> list:
        """Generate swap reduction recommendations"""
        if severity == 'normal':
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'Swap usage is within normal range',
                'current_swap_gb': swap_gb,
                'target_swap_gb': self.target_swap_gb
            }]

        recommendations = []

        # Critical: Immediate action needed
        if severity == 'critical':
            recommendations.append({
                'priority': 'critical',
                'action': 'immediate_memory_reduction',
                'description': f"CRITICAL: Reduce swap from {swap_gb} GB to {self.target_swap_gb} GB",
                'expected_reduction_gb': round(potential_reduction, 2),
                'steps': [
                    'Run browser optimization (Week 2 agents)',
                    'Run app hibernation (Week 3 agents)',
                    'Restart high-memory processes',
                    'Close unnecessary applications'
                ],
                'risk': 'medium',
                'impact': 'Significant performance improvement, reduced disk I/O',
                'estimated_time': '15-30 minutes'
            })

            # Target specific high-memory processes
            if contributors:
                high_memory_procs = [c for c in contributors if c['contribution'] == 'high']
                if high_memory_procs:
                    recommendations.append({
                        'priority': 'critical',
                        'action': 'terminate_high_memory_processes',
                        'description': f"Terminate {len(high_memory_procs)} high-memory processes",
                        'processes': [f"{c['name']} ({c['memory_gb']} GB)" for c in high_memory_procs[:5]],
                        'expected_reduction_gb': round(sum(c['memory_gb'] for c in high_memory_procs) * 0.5, 2),
                        'risk': 'high',
                        'impact': 'Immediate swap reduction, possible data loss',
                        'note': 'Save work before terminating'
                    })

        # Warning: Preventive action
        elif severity == 'warning':
            recommendations.append({
                'priority': 'high',
                'action': 'preventive_memory_optimization',
                'description': f"Reduce swap from {swap_gb} GB to prevent critical state",
                'expected_reduction_gb': round(potential_reduction, 2),
                'steps': [
                    'Run browser helper consolidation (Agent 12)',
                    'Run Electron app optimization (Agent 16)',
                    'Hibernate inactive apps (Agent 14)',
                    'Clear unnecessary caches (Agent 23)'
                ],
                'risk': 'low',
                'estimated_time': '10-20 minutes'
            })

        # Memory compaction strategy
        if swap_gb > 10:
            recommendations.append({
                'priority': 'high',
                'action': 'memory_compaction',
                'description': 'Compact memory to reduce swap pressure',
                'method': 'purge_inactive_memory',
                'command': 'sudo purge',
                'expected_reduction_gb': round(swap_gb * 0.15, 2),  # 15% from purge
                'risk': 'low',
                'impact': 'Temporary system slowdown (10-30 seconds)',
                'note': 'Requires sudo password'
            })

        # Restart strategy for severe cases
        if swap_gb > 15:
            recommendations.append({
                'priority': 'medium',
                'action': 'system_restart',
                'description': 'Restart system to clear swap completely',
                'expected_reduction_gb': swap_gb,
                'risk': 'low',
                'impact': 'Full swap clear, requires reopening applications',
                'note': 'Last resort option - save all work first'
            })

        return recommendations

    def get_swap_reduction_plan(self) -> dict:
        """
        Get comprehensive swap reduction plan
        Target: 22.27 GB → 5 GB (17.27 GB reduction)
        """
        analysis = self.analyze_swap_usage()

        if 'error' in analysis:
            return analysis

        swap_gb = analysis['swap_statistics']['swap_used_gb']

        # Calculate multi-phase reduction strategy
        phases = []

        # Phase 1: Browser optimization (Week 2)
        phases.append({
            'phase': 1,
            'name': 'Browser Memory Optimization',
            'agents': ['Agent 11', 'Agent 12', 'Agent 13'],
            'expected_reduction_gb': 3.5,  # Conservative estimate from Week 2
            'estimated_time': '5-10 minutes',
            'risk': 'low'
        })

        # Phase 2: App hibernation (Week 3)
        phases.append({
            'phase': 2,
            'name': 'Application Hibernation',
            'agents': ['Agent 14', 'Agent 16', 'Agent 17', 'Agent 24'],
            'expected_reduction_gb': 5.0,  # Conservative estimate from Week 3
            'estimated_time': '10-15 minutes',
            'risk': 'low'
        })

        # Phase 3: System optimization (Week 4)
        phases.append({
            'phase': 3,
            'name': 'System-Level Optimization',
            'agents': ['Agent 20', 'Agent 23', 'Agent 22'],
            'expected_reduction_gb': 3.0,
            'estimated_time': '5-10 minutes',
            'risk': 'low'
        })

        # Phase 4: Emergency measures (if still critical)
        if swap_gb > 15:
            phases.append({
                'phase': 4,
                'name': 'Emergency Memory Reduction',
                'actions': ['Purge inactive memory', 'Restart high-memory processes'],
                'expected_reduction_gb': 2.0,
                'estimated_time': '5 minutes',
                'risk': 'medium'
            })

        total_expected = sum(p.get('expected_reduction_gb', 0) for p in phases)

        return {
            'current_swap_gb': swap_gb,
            'target_swap_gb': self.target_swap_gb,
            'total_reduction_needed_gb': round(swap_gb - self.target_swap_gb, 2),
            'total_expected_reduction_gb': total_expected,
            'reduction_phases': phases,
            'estimated_result': {
                'final_swap_gb': max(0, swap_gb - total_expected),
                'reduction_percent': round((total_expected / swap_gb * 100), 1) if swap_gb > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save swap optimization report"""
        report = self.analyze_swap_usage()
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
@click.option('--format', type=click.Choice(['human', 'json']), default='human',
              help='Output format (human-readable or JSON)')
@click.option('--output', type=click.Path(), default=None,
              help='Save report to file')
def main(format: str, output: str):
    """
    Agent 9: Swap Optimizer

    Analyzes and reduces swap usage (target: 22.27 GB detected)
    Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
    """
    start_time = time.time()

    # Initialize optimizer
    optimizer = SwapOptimizer()

    # Analyze swap usage
    report = optimizer.analyze_swap_usage()

    # Add execution metrics
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 2)

    if 'error' in report:
        if format == 'json':
            click.echo(json.dumps(report, indent=2))
        else:
            click.echo(f"Error: {report['error']}", err=True)
        return 1

    # Get comprehensive reduction plan
    plan = optimizer.get_swap_reduction_plan()
    if 'error' not in plan:
        report['reduction_plan'] = plan

    # Output results
    if format == 'json':
        click.echo(json.dumps(report, indent=2))
    else:
        _print_human_readable(report)

    # Save to file if requested
    if output:
        output_path = Path(output)
        optimizer.generate_report(output_path)
        if format == 'human':
            click.echo(f"\nReport saved to: {output_path}")

    return 0


def _print_human_readable(report: dict):
    """Print human-readable output"""
    click.echo("=== Swap Optimizer (Agent 9) ===\n")

    # Display swap statistics
    stats = report['swap_statistics']
    click.echo(f"Timestamp: {report['timestamp']}")
    click.echo(f"Swap Used: {stats['swap_used_gb']} GB")
    click.echo(f"Swap Free: {stats['swap_free_gb']} GB")
    click.echo(f"Swap Total: {stats['swap_total_gb']} GB")
    click.echo(f"Utilization: {stats['swap_utilization_percent']}%\n")

    click.echo(f"Severity: {report['severity'].upper()}")
    click.echo(f"Memory Pressure: {report['memory_pressure'].upper()}")
    click.echo(f"Pageouts: {report['pageouts']:,}\n")

    # Display optimization analysis
    opt = report['optimization_analysis']
    click.echo("=== Optimization Analysis ===")
    click.echo(f"Current Swap: {opt['current_swap_gb']} GB")
    click.echo(f"Target Swap: {opt['target_swap_gb']} GB")
    click.echo(f"Potential Reduction: {opt['potential_reduction_gb']} GB ({opt['target_reduction_percent']}%)\n")

    # Display swap contributors
    if report['swap_contributors']:
        click.echo("=== Top Swap Contributors ===")
        click.echo(f"{'PID':>7s}  {'Process Name':30s}  {'Memory':>8s}  {'Contribution':>12s}")
        click.echo("-" * 70)
        for contrib in report['swap_contributors'][:10]:
            click.echo(f"{contrib['pid']:7d}  {contrib['name']:30s}  {contrib['memory_gb']:6.2f} GB  {contrib['contribution']:>12s}")

    # Display recommendations
    if report['recommendations']:
        click.echo("\n=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            click.echo(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            click.echo(f"     Action: {rec['action']}")

            if 'expected_reduction_gb' in rec:
                click.echo(f"     Expected Reduction: {rec['expected_reduction_gb']} GB")
            if 'steps' in rec:
                click.echo("     Steps:")
                for step in rec['steps']:
                    click.echo(f"       - {step}")
            if 'processes' in rec:
                click.echo("     Target Processes:")
                for proc in rec['processes'][:5]:
                    click.echo(f"       - {proc}")
            if 'method' in rec:
                click.echo(f"     Method: {rec['method']}")
            if 'command' in rec:
                click.echo(f"     Command: {rec['command']}")
            if 'risk' in rec:
                click.echo(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                click.echo(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                click.echo(f"     Est. Time: {rec['estimated_time']}")
            if 'note' in rec:
                click.echo(f"     Note: {rec['note']}")

    # Display reduction plan
    if 'reduction_plan' in report:
        plan = report['reduction_plan']
        click.echo("\n=== Swap Reduction Plan ===")
        click.echo(f"Current Swap: {plan['current_swap_gb']} GB")
        click.echo(f"Target Swap: {plan['target_swap_gb']} GB")
        click.echo(f"Reduction Needed: {plan['total_reduction_needed_gb']} GB")
        click.echo(f"Expected Reduction: {plan['total_expected_reduction_gb']} GB\n")

        click.echo("=== Reduction Phases ===")
        for phase in plan['reduction_phases']:
            click.echo(f"\n  Phase {phase['phase']}: {phase['name']}")
            if 'agents' in phase:
                click.echo(f"    Agents: {', '.join(phase['agents'])}")
            if 'actions' in phase:
                click.echo(f"    Actions: {', '.join(phase['actions'])}")
            click.echo(f"    Expected Reduction: {phase['expected_reduction_gb']} GB")
            click.echo(f"    Est. Time: {phase['estimated_time']}")
            click.echo(f"    Risk: {phase['risk']}")

        result = plan['estimated_result']
        click.echo("\n  Estimated Result:")
        click.echo(f"    Final Swap: {result['final_swap_gb']} GB")
        click.echo(f"    Total Reduction: {plan['total_expected_reduction_gb']} GB ({result['reduction_percent']}%)")

    # Show execution time
    click.echo(f"\n⏱️  Execution time: {report['execution_time_seconds']}s")


if __name__ == '__main__':
    main()
