#!/usr/bin/env python3
"""
Agent 24: Process Restart Coordinator
Gracefully restarts applications to consolidate memory
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 3
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from hibernation_utils import HibernationUtils


class ProcessRestartCoordinator:
    """
    Coordinates graceful application restarts for memory consolidation
    """

    def __init__(self, config_path: Path = None):
        """Initialize coordinator with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> dict:
        """Load process restart configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('process_restart', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {}

    def identify_restart_candidates(self) -> dict:
        """
        Identify applications that would benefit from restart

        Criteria:
        - High helper count relative to normal
        - High memory fragmentation (many small helpers)
        - Long uptime with accumulated memory bloat
        """
        restart_candidates = []

        # Check Electron apps
        for app_name in HibernationUtils.ELECTRON_APPS.keys():
            activity = HibernationUtils.get_app_activity_level(app_name)

            if 'error' in activity or activity.get('process_count', 0) == 0:
                continue

            app_info = HibernationUtils.ELECTRON_APPS[app_name]
            max_normal = app_info['max_normal_helpers']

            # Check if exceeds threshold
            if activity['helper_count'] > max_normal * 1.5:  # 50% over normal
                restart_benefit = activity['memory_gb'] * 0.3  # 30% memory recovery expected

                restart_candidates.append({
                    'app_name': app_name,
                    'app_type': 'electron',
                    'current_memory_gb': activity['memory_gb'],
                    'helper_count': activity['helper_count'],
                    'max_normal_helpers': max_normal,
                    'restart_benefit_gb': round(restart_benefit, 2),
                    'priority': 'high' if activity['helper_count'] > max_normal * 2 else 'medium',
                    'reason': 'Helper count exceeds threshold'
                })

        # Check browsers (already analyzed by Week 2 agents, but add for completeness)
        # This provides a unified view of all restart candidates

        return {
            'timestamp': datetime.now().isoformat(),
            'restart_candidates': restart_candidates,
            'total_candidates': len(restart_candidates),
            'total_potential_savings_gb': round(sum(c['restart_benefit_gb'] for c in restart_candidates), 2),
            'recommendations': self._generate_recommendations(restart_candidates)
        }

    def _generate_recommendations(self, candidates: list) -> list:
        """Generate actionable restart recommendations"""
        if not candidates:
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'No applications requiring restart',
                'expected_savings_gb': 0
            }]

        recommendations = []

        # High priority restarts
        high_priority = [c for c in candidates if c['priority'] == 'high']
        if high_priority:
            total_savings = sum(c['restart_benefit_gb'] for c in high_priority)
            recommendations.append({
                'priority': 'critical',
                'action': 'restart_high_priority_apps',
                'description': f"Restart {len(high_priority)} high-priority applications",
                'apps': [c['app_name'] for c in high_priority],
                'expected_savings_gb': round(total_savings, 2),
                'method': 'graceful_restart_with_state',
                'risk': 'medium',
                'impact': 'Temporary workflow interruption (30-90 seconds per app)',
                'note': 'All app state will be preserved and restored'
            })

        # Medium priority restarts
        medium_priority = [c for c in candidates if c['priority'] == 'medium']
        if medium_priority:
            total_savings = sum(c['restart_benefit_gb'] for c in medium_priority)
            recommendations.append({
                'priority': 'high',
                'action': 'restart_medium_priority_apps',
                'description': f"Restart {len(medium_priority)} medium-priority applications",
                'apps': [c['app_name'] for c in medium_priority],
                'expected_savings_gb': round(total_savings, 2),
                'method': 'graceful_restart_with_state',
                'risk': 'low'
            })

        # Scheduled restart strategy
        if len(candidates) >= 3:
            recommendations.append({
                'priority': 'medium',
                'action': 'schedule_sequential_restarts',
                'description': f"Schedule sequential restarts for {len(candidates)} apps",
                'method': 'automated_sequential_restart',
                'expected_savings_gb': round(sum(c['restart_benefit_gb'] for c in candidates), 2),
                'estimated_time': f"{len(candidates) * 60} seconds (1 min per app)",
                'risk': 'low',
                'note': 'Restarts apps one at a time to minimize disruption'
            })

        return recommendations

    def restart_app_gracefully(self, app_name: str, preserve_state: bool = True) -> dict:
        """
        Perform graceful restart of an application

        Steps:
        1. Get before state
        2. Quit app gracefully
        3. Wait for full termination
        4. Reopen app
        5. Wait for stabilization
        6. Get after state
        7. Calculate memory recovery
        """
        print(f"\nRestarting {app_name}...")

        # Step 1: Get before state
        before_state = HibernationUtils.get_app_activity_level(app_name)

        if 'error' in before_state or before_state.get('process_count', 0) == 0:
            return {
                'success': False,
                'error': 'App not running',
                'app_name': app_name
            }

        print(f"  Before: {before_state['memory_gb']} GB, {before_state['helper_count']} helpers")

        # Step 2: Suspend (quit) app
        suspend_result = HibernationUtils.suspend_app(app_name, preserve_state=preserve_state)

        if not suspend_result['success']:
            return {
                'success': False,
                'error': 'Could not quit app',
                'app_name': app_name,
                'suspend_result': suspend_result
            }

        print(f"  Suspended: {suspend_result['memory_freed_gb']} GB freed")

        # Step 3: Wait for full termination
        time.sleep(3)

        # Step 4: Reopen app
        print(f"  Reopening {app_name}...")
        resume_result = HibernationUtils.resume_app(app_name)

        if not resume_result['success']:
            return {
                'success': False,
                'error': 'Could not reopen app',
                'app_name': app_name,
                'resume_result': resume_result
            }

        # Step 5: Wait for stabilization
        print(f"  Waiting for stabilization...")
        time.sleep(5)

        # Step 6: Get after state
        after_state = HibernationUtils.get_app_activity_level(app_name)
        print(f"  After: {after_state['memory_gb']} GB, {after_state['helper_count']} helpers")

        # Step 7: Calculate recovery
        memory_recovered = before_state['memory_gb'] - after_state['memory_gb']
        helper_reduction = before_state['helper_count'] - after_state['helper_count']

        return {
            'success': True,
            'app_name': app_name,
            'before_memory_gb': before_state['memory_gb'],
            'after_memory_gb': after_state['memory_gb'],
            'memory_recovered_gb': round(memory_recovered, 2),
            'before_helpers': before_state['helper_count'],
            'after_helpers': after_state['helper_count'],
            'helpers_reduced': helper_reduction,
            'reduction_percent': round((memory_recovered / before_state['memory_gb']) * 100, 1) if before_state['memory_gb'] > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }

    def restart_multiple_apps(self, app_names: list, delay_seconds: int = 30) -> dict:
        """
        Restart multiple apps sequentially with delay between each
        """
        results = []
        total_recovered = 0.0

        for app_name in app_names:
            result = self.restart_app_gracefully(app_name)
            results.append(result)

            if result['success']:
                total_recovered += result['memory_recovered_gb']

            # Delay before next restart (except for last app)
            if app_name != app_names[-1]:
                print(f"\nWaiting {delay_seconds} seconds before next restart...")
                time.sleep(delay_seconds)

        return {
            'apps_restarted': len(app_names),
            'successful_restarts': sum(1 for r in results if r['success']),
            'failed_restarts': sum(1 for r in results if not r['success']),
            'total_memory_recovered_gb': round(total_recovered, 2),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save process restart report"""
        report = self.identify_restart_candidates()
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


def main():
    """Main execution"""
    print("=== Process Restart Coordinator (Agent 24) ===\n")

    # Initialize coordinator
    coordinator = ProcessRestartCoordinator()

    # Identify restart candidates
    report = coordinator.identify_restart_candidates()

    # Display summary
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Candidates: {report['total_candidates']}")
    print(f"Potential Savings: {report['total_potential_savings_gb']} GB\n")

    if report['restart_candidates']:
        print("=== Restart Candidates ===")
        for i, candidate in enumerate(report['restart_candidates'], 1):
            print(f"\n  {i}. {candidate['app_name'].upper()} [{candidate['priority'].upper()}]")
            print(f"     Type: {candidate['app_type']}")
            print(f"     Current Memory: {candidate['current_memory_gb']} GB")
            print(f"     Helpers: {candidate['helper_count']} (Max Normal: {candidate['max_normal_helpers']})")
            print(f"     Restart Benefit: {candidate['restart_benefit_gb']} GB")
            print(f"     Reason: {candidate['reason']}")

    if report['recommendations']:
        print("\n=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"     Action: {rec['action']}")
            if 'apps' in rec:
                print(f"     Apps: {', '.join(rec['apps'])}")
            print(f"     Expected Savings: {rec.get('expected_savings_gb', 0)} GB")
            print(f"     Method: {rec.get('method', 'N/A')}")
            print(f"     Risk: {rec.get('risk', 'N/A')}")
            if 'impact' in rec:
                print(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                print(f"     Est. Time: {rec['estimated_time']}")
            if 'note' in rec:
                print(f"     Note: {rec['note']}")

    # Save report
    output_path = Path(__file__).parent.parent / 'data' / 'process-restart-candidates.json'
    coordinator.generate_report(output_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
