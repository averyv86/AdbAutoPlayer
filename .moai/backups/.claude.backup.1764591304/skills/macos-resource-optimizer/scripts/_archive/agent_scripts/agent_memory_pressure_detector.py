#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=6.1.0", "click>=8.1.0", "rich>=13.0.0"]
# ///
"""
Agent 18: Memory Pressure Detector
Analyzes system-wide memory pressure and recommends cleanup level
Part of macOS Resource Optimizer v2.0 - RAM Optimization
"""

import json
import sys
import time
import click
from pathlib import Path
from datetime import datetime
from ram_utils import RAMUtils

class MemoryPressureDetector:
    """
    Detects system memory pressure and determines appropriate cleanup level
    """

    def __init__(self, config_path: Path = None):
        """Initialize with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.ram_utils = RAMUtils()

    def _load_config(self, config_path: Path) -> dict:
        """Load cleanup rules configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('ram_optimization', {})
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            # Return defaults
            return {
                'enabled': True,
                'memory_pressure_threshold': 'warning',
                'swap_threshold_gb': 4
            }

    def analyze_memory_pressure(self) -> dict:
        """
        Comprehensive memory pressure analysis
        Returns detailed report with recommendations
        """
        # Get memory pressure level
        pressure_level, vm_details = self.ram_utils.get_memory_pressure()

        # Get total RAM usage
        totals = self.ram_utils.calculate_total_ram_usage()

        # Determine cleanup urgency
        urgency = self._determine_urgency(pressure_level, vm_details, totals)

        # Generate recommendations
        recommendations = self._generate_recommendations(pressure_level, vm_details, totals, urgency)

        # Build comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'pressure_level': pressure_level,
            'urgency': urgency,
            'memory_stats': {
                'total_rss_gb': totals['total_rss_gb'],
                'free_gb': totals['free_gb'],
                'compressed_gb': totals['compressed_gb'],
                'swap_used_gb': vm_details['swap_used_gb'],
                'pageouts': vm_details['pageouts'],
                'process_count': totals['process_count']
            },
            'vm_details': vm_details,
            'recommendations': recommendations,
            'cleanup_phases': self._determine_cleanup_phases(urgency)
        }

        return report

    def _determine_urgency(self, pressure_level: str, vm_details: dict, totals: dict) -> str:
        """
        Determine cleanup urgency level
        Returns: 'low' | 'medium' | 'high' | 'critical'
        """
        swap_gb = vm_details.get('swap_used_gb', 0)
        free_gb = totals.get('free_gb', 0)
        pageouts = vm_details.get('pageouts', 0)

        # Critical: System is thrashing or nearly out of memory
        if pressure_level == 'critical' or free_gb < 0.5 or swap_gb > 8:
            return 'critical'

        # High: Memory pressure detected, should act soon
        if pressure_level == 'warning' or free_gb < 2 or swap_gb > 4:
            return 'high'

        # Medium: Some pressure signs, preventive cleanup recommended
        if pageouts > 1000 or swap_gb > 1 or free_gb < 5:
            return 'medium'

        # Low: System is healthy, routine maintenance only
        return 'low'

    def _generate_recommendations(self, pressure_level: str, vm_details: dict,
                                  totals: dict, urgency: str) -> list:
        """Generate actionable recommendations based on memory state"""
        recommendations = []

        # Always check for memory leaks
        recommendations.append({
            'priority': 'high' if urgency in ['high', 'critical'] else 'medium',
            'action': 'scan_memory_leaks',
            'description': 'Scan for processes with memory leaks',
            'expected_impact_gb': '1-3'
        })

        # Browser optimization (usually high-impact)
        if urgency in ['medium', 'high', 'critical']:
            recommendations.append({
                'priority': 'high',
                'action': 'optimize_browsers',
                'description': 'Optimize browser memory (tabs, helpers, cache)',
                'expected_impact_gb': '3-5'
            })

        # App hibernation for high/critical
        if urgency in ['high', 'critical']:
            recommendations.append({
                'priority': 'high',
                'action': 'hibernate_inactive_apps',
                'description': 'Suspend inactive applications',
                'expected_impact_gb': '2-4'
            })

        # Swap optimization if swap is being used heavily
        if vm_details.get('swap_used_gb', 0) > 2:
            recommendations.append({
                'priority': 'high' if urgency == 'critical' else 'medium',
                'action': 'optimize_swap',
                'description': 'Clear swap and optimize memory pressure',
                'expected_impact_gb': '1-2'
            })

        # System optimization for critical situations
        if urgency == 'critical':
            recommendations.append({
                'priority': 'critical',
                'action': 'emergency_cleanup',
                'description': 'Emergency system-wide memory cleanup',
                'expected_impact_gb': '5-10'
            })

        # Preventive maintenance for low urgency
        if urgency == 'low':
            recommendations.append({
                'priority': 'low',
                'action': 'routine_maintenance',
                'description': 'Routine cache and zombie process cleanup',
                'expected_impact_gb': '0.5-1'
            })

        return recommendations

    def _determine_cleanup_phases(self, urgency: str) -> list:
        """
        Determine which cleanup phases should be executed
        Returns list of phase names in priority order
        """
        if urgency == 'critical':
            return [
                'browser_optimization',
                'app_hibernation',
                'memory_leak_fixes',
                'swap_optimization',
                'system_optimization',
                'zombie_cleanup'
            ]
        elif urgency == 'high':
            return [
                'browser_optimization',
                'app_hibernation',
                'memory_leak_fixes',
                'zombie_cleanup'
            ]
        elif urgency == 'medium':
            return [
                'browser_optimization',
                'memory_leak_fixes',
                'zombie_cleanup'
            ]
        else:  # low
            return [
                'zombie_cleanup',
                'routine_cache_cleanup'
            ]

    def should_trigger_cleanup(self) -> bool:
        """
        Determine if automatic cleanup should be triggered
        Based on configured threshold
        """
        pressure_level, _ = self.ram_utils.get_memory_pressure()
        threshold = self.config.get('memory_pressure_threshold', 'warning')

        threshold_order = ['normal', 'warning', 'critical']
        current_index = threshold_order.index(pressure_level) if pressure_level in threshold_order else 0
        threshold_index = threshold_order.index(threshold) if threshold in threshold_order else 1

        return current_index >= threshold_index

    def generate_report(self, output_path: Path = None) -> str:
        """
        Generate and save comprehensive memory pressure report
        Returns report as JSON string
        """
        report = self.analyze_memory_pressure()
        report_json = json.dumps(report, indent=2)

        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report_json)
                print(f"Report saved to: {output_path}")
            except Exception as e:
                print(f"Warning: Could not save report to {output_path}: {e}")

        return report_json


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format (default: json)')
@click.option('--verbose', is_flag=True, help='Include detailed information')
def main(format: str, verbose: bool):
    """Main execution"""
    start_time = time.time()

    # Initialize detector
    detector = MemoryPressureDetector()

    # Analyze memory pressure
    report = detector.analyze_memory_pressure()

    # Build coordinator-compatible result
    result = {
        "agent": "agent_memory_pressure_detector",
        "zombies_found": 0,  # Informational agent, no zombies
        "total_memory_bytes": int(report['memory_stats']['total_rss_gb'] * 1024 * 1024 * 1024),
        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
        "pids": [],
        "pressure_level": report['pressure_level'],
        "urgency": report['urgency'],
        "memory_stats": report['memory_stats'],
        "recommendations": report['recommendations'] if verbose else report['recommendations'][:3],
        "cleanup_phases": report['cleanup_phases'],
        "should_trigger_cleanup": detector.should_trigger_cleanup()
    }

    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        # Display summary (existing rich output)
        print("=== Memory Pressure Detector (Agent 18) ===\n")
        print(f"Timestamp: {report['timestamp']}")
        print(f"\nMemory Pressure Level: {report['pressure_level'].upper()}")
        print(f"Cleanup Urgency: {report['urgency'].upper()}\n")

        print("Memory Statistics:")
        stats = report['memory_stats']
        print(f"  Total RSS: {stats['total_rss_gb']} GB")
        print(f"  Free: {stats['free_gb']} GB")
        print(f"  Compressed: {stats['compressed_gb']} GB")
        print(f"  Swap Used: {stats['swap_used_gb']} GB")
        print(f"  Pageouts: {stats['pageouts']:,}")
        print(f"  Processes: {stats['process_count']}")

        print("\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"     Action: {rec['action']}")
            print(f"     Expected Impact: {rec['expected_impact_gb']} GB")

        print("\nRecommended Cleanup Phases:")
        for phase in report['cleanup_phases']:
            print(f"  - {phase}")

        print(f"\nAuto-trigger cleanup: {'YES' if detector.should_trigger_cleanup() else 'NO'}")

        # Save report
        output_path = Path(__file__).parent.parent / 'data' / 'memory-pressure-report.json'
        detector.generate_report(output_path)
    elif format == 'summary':
        # Brief console output
        print(f"Pressure: {report['pressure_level'].upper()}, Urgency: {report['urgency'].upper()}")
        print(f"Memory: {report['memory_stats']['total_rss_gb']:.1f} GB used, "
              f"{report['memory_stats']['free_gb']:.1f} GB free")
        print(f"Cleanup phases: {len(report['cleanup_phases'])}")

    # Return exit code based on urgency
    urgency_codes = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    return urgency_codes.get(report['urgency'], 0)


if __name__ == '__main__':
    sys.exit(main())
