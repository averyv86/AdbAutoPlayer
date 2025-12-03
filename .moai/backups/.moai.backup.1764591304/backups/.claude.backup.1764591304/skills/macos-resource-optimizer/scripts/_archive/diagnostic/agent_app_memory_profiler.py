#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=6.1.0", "click>=8.1.0", "rich>=13.0.0"]
# ///
"""
Agent 15: App Memory Profiler
Profiles all running applications and identifies memory-intensive apps
Part of macOS Resource Optimizer v2.0 - RAM Optimization
"""

import json
import sys
import time
import click
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from ram_utils import RAMUtils

class AppMemoryProfiler:
    """
    Profiles application memory usage and identifies optimization targets
    """

    def __init__(self, config_path: Path = None):
        """Initialize profiler with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)
        self.ram_utils = RAMUtils()
        self.protected_apps = self.config.get('protected_apps', [])

    def _load_config(self, config_path: Path) -> dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('ram_optimization', {})
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'protected_apps': [
                    'Claude Code',
                    'Notion',
                    'Slack',
                    'Discord',
                    'Mail',
                    'Messages',
                    'Ghostty'
                ]
            }

    def profile_all_apps(self) -> dict:
        """
        Profile all running applications
        Returns comprehensive profiling report
        """
        # Get all processes
        all_processes = self.ram_utils.get_all_processes_memory()

        # Group processes by application
        apps = self._group_by_application(all_processes)

        # Analyze each app
        app_profiles = []
        for app_name, processes in apps.items():
            profile = self._profile_application(app_name, processes)
            app_profiles.append(profile)

        # Sort by total memory (descending)
        app_profiles.sort(key=lambda x: x['total_memory_gb'], reverse=True)

        # Categorize apps
        categorized = self._categorize_apps(app_profiles)

        # Generate optimization targets
        targets = self._identify_optimization_targets(app_profiles)

        # Build comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_apps': len(app_profiles),
                'total_processes': len(all_processes),
                'total_memory_gb': round(sum(p['rss_gb'] for p in all_processes), 2),
                'high_memory_apps': len(categorized['high_memory']),
                'optimization_targets': len(targets)
            },
            'top_10_apps': app_profiles[:10],
            'categorized': categorized,
            'optimization_targets': targets,
            'protected_apps': self.protected_apps
        }

        return report

    def _group_by_application(self, processes: list) -> dict:
        """
        Group processes by application name
        Returns dict: {app_name: [process_list]}
        """
        apps = defaultdict(list)

        for proc in processes:
            command = proc['command']

            # Extract application name (simplified)
            app_name = self._extract_app_name(command)
            apps[app_name].append(proc)

        return dict(apps)

    def _extract_app_name(self, command: str) -> str:
        """
        Extract application name from command string
        Handles common patterns like /Applications/App.app/Contents/MacOS/App
        """
        # Extract from .app path if present
        if '.app/' in command:
            parts = command.split('.app/')[0]
            app_name = parts.split('/')[-1]
            return app_name

        # Extract from binary name
        parts = command.split()
        if not parts:
            return 'Unknown'

        binary = parts[0]
        app_name = binary.split('/')[-1]

        # Clean up common suffixes
        for suffix in [' Helper', ' (Renderer)', ' (GPU)', ' (Network)']:
            if app_name.endswith(suffix):
                app_name = app_name[:-len(suffix)]

        return app_name if app_name else 'Unknown'

    def _profile_application(self, app_name: str, processes: list) -> dict:
        """
        Create detailed profile for a single application
        """
        total_memory_gb = sum(p['rss_gb'] for p in processes)
        total_cpu = sum(p['cpu_percent'] for p in processes)

        # Identify process types (main app, helpers, etc.)
        process_types = defaultdict(list)
        for proc in processes:
            if 'Helper' in proc['command']:
                if 'Renderer' in proc['command']:
                    process_types['renderer_helpers'].append(proc)
                elif 'GPU' in proc['command']:
                    process_types['gpu_helpers'].append(proc)
                elif 'Network' in proc['command']:
                    process_types['network_helpers'].append(proc)
                else:
                    process_types['other_helpers'].append(proc)
            else:
                process_types['main'].append(proc)

        # Check if protected
        is_protected = any(protected.lower() in app_name.lower()
                          for protected in self.protected_apps)

        profile = {
            'app_name': app_name,
            'total_memory_gb': round(total_memory_gb, 2),
            'total_memory_mb': round(total_memory_gb * 1024, 2),
            'total_cpu_percent': round(total_cpu, 1),
            'process_count': len(processes),
            'is_protected': is_protected,
            'process_breakdown': {
                'main_processes': len(process_types['main']),
                'renderer_helpers': len(process_types['renderer_helpers']),
                'gpu_helpers': len(process_types['gpu_helpers']),
                'network_helpers': len(process_types['network_helpers']),
                'other_helpers': len(process_types['other_helpers'])
            },
            'memory_breakdown': {
                'main_gb': round(sum(p['rss_gb'] for p in process_types['main']), 2),
                'helpers_gb': round(sum(p['rss_gb'] for p in processes
                                       if 'Helper' in p['command']), 2)
            },
            'largest_process': max(processes, key=lambda p: p['rss_gb']) if processes else None
        }

        return profile

    def _categorize_apps(self, app_profiles: list) -> dict:
        """
        Categorize apps by memory usage and characteristics
        """
        categorized = {
            'high_memory': [],      # >2 GB
            'medium_memory': [],    # 1-2 GB
            'low_memory': [],       # <1 GB
            'browsers': [],
            'electron_apps': [],
            'protected': [],
            'optimization_candidates': []
        }

        browser_keywords = ['arc', 'chrome', 'safari', 'firefox', 'edge', 'brave']
        electron_keywords = ['electron', 'notion', 'slack', 'discord', 'vscode', 'vs code']

        for profile in app_profiles:
            app_name = profile['app_name'].lower()
            memory_gb = profile['total_memory_gb']

            # Memory categories
            if memory_gb >= 2:
                categorized['high_memory'].append(profile)
            elif memory_gb >= 1:
                categorized['medium_memory'].append(profile)
            else:
                categorized['low_memory'].append(profile)

            # App type categories
            if any(keyword in app_name for keyword in browser_keywords):
                categorized['browsers'].append(profile)

            if any(keyword in app_name for keyword in electron_keywords):
                categorized['electron_apps'].append(profile)

            if profile['is_protected']:
                categorized['protected'].append(profile)

            # Optimization candidates: high memory, many helpers, not protected
            if (memory_gb >= 1.5 and
                profile['process_count'] > 10 and
                not profile['is_protected']):
                categorized['optimization_candidates'].append(profile)

        return categorized

    def _identify_optimization_targets(self, app_profiles: list) -> list:
        """
        Identify specific optimization targets with recommendations
        """
        targets = []

        for profile in app_profiles:
            if profile['is_protected']:
                continue

            optimizations = []
            potential_savings_gb = 0

            # Browser helper consolidation
            if profile['process_breakdown']['renderer_helpers'] > 20:
                optimizations.append({
                    'type': 'consolidate_browser_helpers',
                    'description': f"Consolidate {profile['process_breakdown']['renderer_helpers']} renderer helpers",
                    'estimated_savings_gb': round(profile['memory_breakdown']['helpers_gb'] * 0.4, 2)
                })
                potential_savings_gb += profile['memory_breakdown']['helpers_gb'] * 0.4

            # Electron app optimization
            if profile['process_breakdown']['other_helpers'] > 5:
                optimizations.append({
                    'type': 'optimize_electron_helpers',
                    'description': f"Optimize {profile['process_breakdown']['other_helpers']} Electron helpers",
                    'estimated_savings_gb': round(profile['memory_breakdown']['helpers_gb'] * 0.3, 2)
                })
                potential_savings_gb += profile['memory_breakdown']['helpers_gb'] * 0.3

            # High memory single process
            if profile['largest_process'] and profile['largest_process']['rss_gb'] > 2:
                optimizations.append({
                    'type': 'investigate_high_memory_process',
                    'description': f"Investigate process using {profile['largest_process']['rss_gb']:.2f} GB",
                    'estimated_savings_gb': round(profile['largest_process']['rss_gb'] * 0.5, 2)
                })
                potential_savings_gb += profile['largest_process']['rss_gb'] * 0.5

            # Only add if we found optimizations
            if optimizations:
                targets.append({
                    'app_name': profile['app_name'],
                    'current_memory_gb': profile['total_memory_gb'],
                    'potential_savings_gb': round(potential_savings_gb, 2),
                    'optimizations': optimizations,
                    'priority': 'high' if potential_savings_gb > 1 else 'medium'
                })

        # Sort by potential savings
        targets.sort(key=lambda x: x['potential_savings_gb'], reverse=True)

        return targets

    def generate_report(self, output_path: Path = None) -> str:
        """
        Generate and save comprehensive profiling report
        """
        report = self.profile_all_apps()
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
@click.option('--format', type=click.Choice(['json', 'table', 'summary']), default='json',
              help='Output format (default: json)')
@click.option('--verbose', is_flag=True, help='Include full app profiles')
def main(format: str, verbose: bool):
    """Main execution"""
    start_time = time.time()

    # Initialize profiler
    profiler = AppMemoryProfiler()

    # Profile all apps
    report = profiler.profile_all_apps()

    # Extract PIDs from optimization targets (apps that could be optimized)
    target_pids = []
    for target in report['optimization_targets']:
        # Get PIDs from top_10_apps matching this app name
        for app in report['top_10_apps']:
            if app['app_name'] == target['app_name'] and app.get('largest_process'):
                target_pids.append(app['largest_process']['pid'])
                break

    # Build coordinator-compatible result
    result = {
        "agent": "agent_app_memory_profiler",
        "zombies_found": len(report['optimization_targets']),  # Apps needing optimization
        "total_memory_bytes": int(report['summary']['total_memory_gb'] * 1024 * 1024 * 1024),
        "execution_time_ms": round((time.time() - start_time) * 1000, 2),
        "pids": target_pids,
        "summary": report['summary'],
        "top_apps": report['top_10_apps'] if verbose else report['top_10_apps'][:5],
        "optimization_targets": report['optimization_targets'] if verbose else report['optimization_targets'][:5],
        "protected_apps": report['protected_apps']
    }

    if format == 'json':
        print(json.dumps(result, indent=2))
    elif format == 'table':
        # Display summary (existing rich output)
        print("=== App Memory Profiler (Agent 15) ===\n")
        print(f"Timestamp: {report['timestamp']}\n")

        summary = report['summary']
        print("Summary:")
        print(f"  Total Apps: {summary['total_apps']}")
        print(f"  Total Processes: {summary['total_processes']}")
        print(f"  Total Memory: {summary['total_memory_gb']} GB")
        print(f"  High Memory Apps: {summary['high_memory_apps']} (>2 GB)")
        print(f"  Optimization Targets: {summary['optimization_targets']}")

        print("\nTop 10 Memory Consumers:")
        for i, app in enumerate(report['top_10_apps'], 1):
            protected = " [PROTECTED]" if app['is_protected'] else ""
            print(f"  {i}. {app['app_name']:30s} {app['total_memory_gb']:6.2f} GB  "
                  f"({app['process_count']} processes){protected}")

        print("\nOptimization Targets:")
        for target in report['optimization_targets'][:5]:
            print(f"\n  {target['app_name']}")
            print(f"    Current: {target['current_memory_gb']} GB")
            print(f"    Potential Savings: {target['potential_savings_gb']} GB")
            print(f"    Priority: {target['priority'].upper()}")
            print("    Optimizations:")
            for opt in target['optimizations']:
                print(f"      - {opt['description']} (~{opt['estimated_savings_gb']} GB)")

        # Save report
        output_path = Path(__file__).parent.parent / 'data' / 'app-memory-profile.json'
        profiler.generate_report(output_path)
    elif format == 'summary':
        # Brief console output
        summary = report['summary']
        print(f"Apps: {summary['total_apps']}, Processes: {summary['total_processes']}")
        print(f"Total Memory: {summary['total_memory_gb']:.1f} GB")
        print(f"Optimization targets: {summary['optimization_targets']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
