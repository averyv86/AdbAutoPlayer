#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# ///
"""
Agent 10: Memory Leak Hunter
Detects processes with abnormal memory growth patterns
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
"""

import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from ram_utils import RAMUtils
import click


class MemoryLeakHunter:
    """
    Detects memory leaks by tracking process memory growth over time
    """

    def __init__(self, config_path: Path = None):
        """Initialize leak hunter with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Leak detection thresholds
        self.growth_rate_threshold_mb_per_min = self.config.get('growth_rate_threshold_mb_per_min', 50)
        self.abnormal_memory_threshold_gb = self.config.get('abnormal_memory_threshold_gb', 10)
        self.monitoring_interval_seconds = self.config.get('monitoring_interval_seconds', 30)

    def _load_config(self, config_path: Path) -> dict:
        """Load memory leak detection configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('memory_leak_detection', {
                    'growth_rate_threshold_mb_per_min': 50,
                    'abnormal_memory_threshold_gb': 10,
                    'monitoring_interval_seconds': 30
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'growth_rate_threshold_mb_per_min': 50,
                'abnormal_memory_threshold_gb': 10,
                'monitoring_interval_seconds': 30
            }

    def analyze_memory_patterns(self, quick_scan: bool = True) -> dict:
        """
        Analyze processes for memory leak patterns

        Args:
            quick_scan: If True, analyze current snapshot. If False, monitor over time.
        Returns:
            Comprehensive leak analysis with detection results
        """
        if quick_scan:
            return self._quick_leak_scan()
        else:
            return self._monitor_memory_growth()

    def _quick_leak_scan(self) -> dict:
        """Quick scan for obvious leak indicators (single snapshot)"""
        # Get all processes
        processes = RAMUtils.get_all_processes_memory()

        leak_candidates = []
        total_abnormal_memory_gb = 0

        for proc in processes:
            memory_gb = proc['rss_gb']  # Fixed: use 'rss_gb' not 'memory_gb'

            # Flag processes exceeding normal thresholds
            if memory_gb >= self.abnormal_memory_threshold_gb:
                leak_severity = self._determine_leak_severity(memory_gb)

                leak_candidates.append({
                    'pid': proc['pid'],
                    'name': proc['command'],  # Fixed: use 'command' not 'name'
                    'memory_gb': memory_gb,
                    'memory_percent': proc['mem_percent'],  # Fixed: use 'mem_percent'
                    'leak_indicator': 'abnormal_memory_usage',
                    'severity': leak_severity,
                    'recommended_action': 'restart' if leak_severity in ['critical', 'high'] else 'monitor'
                })

                total_abnormal_memory_gb += memory_gb

        # Sort by memory (descending)
        leak_candidates.sort(key=lambda x: x['memory_gb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'quick_scan',
            'leak_candidates': leak_candidates,
            'total_candidates': len(leak_candidates),
            'total_abnormal_memory_gb': round(total_abnormal_memory_gb, 2),
            'potential_recovery_gb': round(total_abnormal_memory_gb * 0.4, 2),  # 40% recoverable
            'recommendations': self._generate_recommendations(leak_candidates)
        }

    def _monitor_memory_growth(self) -> dict:
        """Monitor processes over time to detect growth patterns"""
        print(f"Monitoring memory growth for {self.monitoring_interval_seconds} seconds...\n")

        # Take initial snapshot
        initial_processes = RAMUtils.get_all_processes_memory()
        initial_by_pid = {p['pid']: p for p in initial_processes}

        print(f"Initial snapshot: {len(initial_processes)} processes")
        print(f"Waiting {self.monitoring_interval_seconds} seconds...")

        # Wait for monitoring interval
        time.sleep(self.monitoring_interval_seconds)

        # Take final snapshot
        final_processes = RAMUtils.get_all_processes_memory()
        final_by_pid = {p['pid']: p for p in final_processes}

        print(f"Final snapshot: {len(final_processes)} processes\n")

        # Analyze growth
        leak_candidates = []
        elapsed_minutes = self.monitoring_interval_seconds / 60.0

        for pid, final_proc in final_by_pid.items():
            if pid not in initial_by_pid:
                continue  # New process, skip

            initial_proc = initial_by_pid[pid]
            initial_memory_mb = initial_proc['rss_gb'] * 1024  # Fixed: use 'rss_gb'
            final_memory_mb = final_proc['rss_gb'] * 1024  # Fixed: use 'rss_gb'

            # Calculate growth
            growth_mb = final_memory_mb - initial_memory_mb
            growth_rate_mb_per_min = growth_mb / elapsed_minutes if elapsed_minutes > 0 else 0

            # Flag if exceeds threshold
            if growth_rate_mb_per_min >= self.growth_rate_threshold_mb_per_min:
                leak_severity = self._determine_leak_severity_by_growth(growth_rate_mb_per_min)

                leak_candidates.append({
                    'pid': pid,
                    'name': final_proc['command'],  # Fixed: use 'command'
                    'initial_memory_gb': initial_proc['rss_gb'],  # Fixed: use 'rss_gb'
                    'final_memory_gb': final_proc['rss_gb'],  # Fixed: use 'rss_gb'
                    'growth_mb': round(growth_mb, 2),
                    'growth_rate_mb_per_min': round(growth_rate_mb_per_min, 2),
                    'elapsed_minutes': round(elapsed_minutes, 2),
                    'leak_indicator': 'abnormal_growth_rate',
                    'severity': leak_severity,
                    'recommended_action': 'restart' if leak_severity in ['critical', 'high'] else 'monitor',
                    'projected_1h_growth_gb': round((growth_rate_mb_per_min * 60) / 1024, 2)
                })

        # Sort by growth rate (descending)
        leak_candidates.sort(key=lambda x: x['growth_rate_mb_per_min'], reverse=True)

        total_growth_mb = sum(c['growth_mb'] for c in leak_candidates)

        return {
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'monitored_growth',
            'monitoring_interval_seconds': self.monitoring_interval_seconds,
            'leak_candidates': leak_candidates,
            'total_candidates': len(leak_candidates),
            'total_growth_mb': round(total_growth_mb, 2),
            'total_growth_gb': round(total_growth_mb / 1024, 2),
            'recommendations': self._generate_recommendations(leak_candidates)
        }

    def _determine_leak_severity(self, memory_gb: float) -> str:
        """Determine leak severity based on absolute memory"""
        if memory_gb >= 20:
            return 'critical'
        elif memory_gb >= 15:
            return 'high'
        elif memory_gb >= 10:
            return 'medium'
        else:
            return 'low'

    def _determine_leak_severity_by_growth(self, growth_rate_mb_per_min: float) -> str:
        """Determine leak severity based on growth rate"""
        if growth_rate_mb_per_min >= 200:  # 200 MB/min = 12 GB/hour
            return 'critical'
        elif growth_rate_mb_per_min >= 100:  # 100 MB/min = 6 GB/hour
            return 'high'
        elif growth_rate_mb_per_min >= 50:   # 50 MB/min = 3 GB/hour
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(self, leak_candidates: list) -> list:
        """Generate leak remediation recommendations"""
        if not leak_candidates:
            return [{
                'priority': 'low',
                'action': 'no_leaks_detected',
                'description': 'No memory leaks detected',
                'expected_recovery_gb': 0
            }]

        recommendations = []

        # Group by severity
        critical_leaks = [c for c in leak_candidates if c['severity'] == 'critical']
        high_leaks = [c for c in leak_candidates if c['severity'] == 'high']
        medium_leaks = [c for c in leak_candidates if c['severity'] == 'medium']

        # Critical leaks: Immediate restart
        if critical_leaks:
            total_memory = sum(c.get('memory_gb', c.get('final_memory_gb', 0)) for c in critical_leaks)
            recommendations.append({
                'priority': 'critical',
                'action': 'restart_critical_processes',
                'description': f"CRITICAL: Restart {len(critical_leaks)} processes with severe memory leaks",
                'processes': [f"{c['name']} (PID {c['pid']})" for c in critical_leaks[:5]],
                'expected_recovery_gb': round(total_memory * 0.6, 2),  # 60% recoverable after restart
                'risk': 'high',
                'impact': 'Immediate memory recovery, possible data loss',
                'note': 'Save work in these applications before restarting'
            })

        # High priority leaks: Scheduled restart
        if high_leaks:
            total_memory = sum(c.get('memory_gb', c.get('final_memory_gb', 0)) for c in high_leaks)
            recommendations.append({
                'priority': 'high',
                'action': 'schedule_process_restarts',
                'description': f"Schedule restart for {len(high_leaks)} processes with high memory leaks",
                'processes': [f"{c['name']} (PID {c['pid']})" for c in high_leaks[:5]],
                'expected_recovery_gb': round(total_memory * 0.5, 2),
                'risk': 'medium',
                'impact': 'Scheduled downtime, state preservation possible'
            })

        # Medium priority: Monitor and report
        if medium_leaks:
            recommendations.append({
                'priority': 'medium',
                'action': 'monitor_and_log',
                'description': f"Monitor {len(medium_leaks)} processes with moderate memory growth",
                'processes': [f"{c['name']} (PID {c['pid']})" for c in medium_leaks[:5]],
                'method': 'continued_monitoring',
                'note': 'Re-run Agent 20 with monitoring mode to track growth'
            })

        # Growth-based projections (if monitored growth data available)
        if leak_candidates and 'growth_rate_mb_per_min' in leak_candidates[0]:
            fast_growers = [c for c in leak_candidates if c.get('projected_1h_growth_gb', 0) > 5]
            if fast_growers:
                recommendations.append({
                    'priority': 'high',
                    'action': 'prevent_memory_exhaustion',
                    'description': f"{len(fast_growers)} processes projected to consume >5 GB in 1 hour",
                    'processes': [f"{c['name']} ({c['projected_1h_growth_gb']} GB/hr)" for c in fast_growers[:5]],
                    'method': 'proactive_restart',
                    'estimated_time': '10-20 minutes'
                })

        return recommendations

    def get_leak_details(self, pid: int) -> dict:
        """Get detailed leak analysis for specific process"""
        try:
            # Get process info
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'pid,comm,rss,%mem'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    'pid': pid,
                    'error': 'Process not found'
                }

            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {
                    'pid': pid,
                    'error': 'Could not parse process info'
                }

            # Parse process data
            parts = lines[1].split(None, 3)
            if len(parts) < 4:
                return {
                    'pid': pid,
                    'error': 'Invalid process data'
                }

            rss_kb = float(parts[2])
            memory_gb = round(rss_kb / 1024 / 1024, 2)
            memory_percent = float(parts[3])

            return {
                'pid': pid,
                'name': parts[1],
                'memory_gb': memory_gb,
                'memory_percent': memory_percent,
                'leak_severity': self._determine_leak_severity(memory_gb),
                'recommended_action': 'restart' if memory_gb > 10 else 'monitor',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'pid': pid,
                'error': str(e)
            }

    def generate_report(self, output_path: Path = None, quick_scan: bool = True) -> str:
        """Generate and save memory leak detection report"""
        report = self.analyze_memory_patterns(quick_scan=quick_scan)
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
@click.option('--monitor/--quick', default=False,
              help='Monitor mode (track growth over time) vs quick scan (single snapshot)')
@click.option('--output', type=click.Path(), default=None,
              help='Save report to file')
def main(format: str, monitor: bool, output: str):
    """
    Agent 10: Memory Leak Hunter

    Detects processes with abnormal memory growth patterns
    Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
    """
    start_time = time.time()
    quick_scan = not monitor

    # Initialize hunter
    hunter = MemoryLeakHunter()

    # Analyze memory patterns
    report = hunter.analyze_memory_patterns(quick_scan=quick_scan)

    # Add execution metrics
    execution_time = time.time() - start_time
    report['execution_time_seconds'] = round(execution_time, 2)

    # Output results
    if format == 'json':
        click.echo(json.dumps(report, indent=2))
    else:
        _print_human_readable(report)

    # Save to file if requested
    if output:
        output_path = Path(output)
        hunter.generate_report(output_path, quick_scan=quick_scan)
        if format == 'human':
            click.echo(f"\nReport saved to: {output_path}")

    return 0


def _print_human_readable(report: dict):
    """Print human-readable output"""
    click.echo("=== Memory Leak Hunter (Agent 10) ===\n")

    # Display summary
    click.echo(f"Timestamp: {report['timestamp']}")
    click.echo(f"Scan Type: {report['scan_type']}\n")

    if report['scan_type'] == 'quick_scan':
        click.echo(f"Total Candidates: {report['total_candidates']}")
        click.echo(f"Total Abnormal Memory: {report['total_abnormal_memory_gb']} GB")
        click.echo(f"Potential Recovery: {report['potential_recovery_gb']} GB\n")

        if report['leak_candidates']:
            click.echo("=== Leak Candidates (Quick Scan) ===")
            click.echo(f"{'PID':>7s}  {'Process Name':30s}  {'Memory':>8s}  {'Severity':>10s}  {'Action':>10s}")
            click.echo("-" * 80)
            for candidate in report['leak_candidates'][:15]:
                click.echo(f"{candidate['pid']:7d}  {candidate['name']:30s}  {candidate['memory_gb']:6.2f} GB  {candidate['severity']:>10s}  {candidate['recommended_action']:>10s}")

            if len(report['leak_candidates']) > 15:
                click.echo(f"\n... and {len(report['leak_candidates']) - 15} more processes")

    else:  # monitored_growth
        click.echo(f"Monitoring Interval: {report['monitoring_interval_seconds']} seconds")
        click.echo(f"Total Candidates: {report['total_candidates']}")
        click.echo(f"Total Growth: {report['total_growth_gb']} GB\n")

        if report['leak_candidates']:
            click.echo("=== Leak Candidates (Growth Monitoring) ===")
            click.echo(f"{'PID':>7s}  {'Process Name':30s}  {'Growth':>10s}  {'Rate/min':>10s}  {'1h Proj':>10s}  {'Severity':>10s}")
            click.echo("-" * 95)
            for candidate in report['leak_candidates'][:15]:
                click.echo(f"{candidate['pid']:7d}  {candidate['name']:30s}  {candidate['growth_mb']:8.1f} MB  {candidate['growth_rate_mb_per_min']:8.1f} MB  {candidate['projected_1h_growth_gb']:8.2f} GB  {candidate['severity']:>10s}")

    # Display recommendations
    if report['recommendations']:
        click.echo("\n=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            click.echo(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            click.echo(f"     Action: {rec['action']}")

            if 'processes' in rec:
                click.echo("     Target Processes:")
                for proc in rec['processes'][:5]:
                    click.echo(f"       - {proc}")
            if 'expected_recovery_gb' in rec:
                click.echo(f"     Expected Recovery: {rec['expected_recovery_gb']} GB")
            if 'method' in rec:
                click.echo(f"     Method: {rec['method']}")
            if 'risk' in rec:
                click.echo(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                click.echo(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                click.echo(f"     Est. Time: {rec['estimated_time']}")
            if 'note' in rec:
                click.echo(f"     Note: {rec['note']}")

    # Show execution time
    click.echo(f"\n⏱️  Execution time: {report['execution_time_seconds']}s")

    # Show tip for monitor mode
    if report['scan_type'] == 'quick_scan':
        click.echo("\n💡 TIP: Run with --monitor flag for time-based leak detection:")
        click.echo("   uv run agent_memory_leak_hunter.py --monitor")


if __name__ == '__main__':
    main()
