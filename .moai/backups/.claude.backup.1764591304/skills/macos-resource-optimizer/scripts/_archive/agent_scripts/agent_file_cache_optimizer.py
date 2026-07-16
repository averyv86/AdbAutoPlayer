#!/usr/bin/env python3
"""
Agent 23: File Cache Optimizer
Analyzes and optimizes system file caches (excluding browser caches)
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from ram_utils import RAMUtils


class FileCacheOptimizer:
    """
    Optimizes system file caches for disk space and indirect RAM benefits
    """

    def __init__(self, config_path: Path = None):
        """Initialize optimizer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Cache directories (excluding browser caches - handled by Agent 13)
        self.cache_dirs = self.config.get('cache_directories', [
            '~/Library/Caches',
            '~/Library/Logs',
            '/Library/Caches',
            '/System/Library/Caches',
            '/var/folders',
            '/private/var/folders'
        ])

        # Exclusions (browser caches handled separately)
        self.exclude_patterns = [
            'Google',
            'Chrome',
            'Firefox',
            'Safari',
            'company.thebrowser.Browser',  # Arc
            'Brave',
            'Edge'
        ]

        # Thresholds
        self.large_cache_mb = self.config.get('large_cache_threshold_mb', 500)
        self.stale_days = self.config.get('stale_cache_days', 30)

    def _load_config(self, config_path: Path) -> dict:
        """Load file cache optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('file_cache_optimization', {
                    'cache_directories': [
                        '~/Library/Caches',
                        '~/Library/Logs',
                        '/Library/Caches'
                    ],
                    'large_cache_threshold_mb': 500,
                    'stale_cache_days': 30
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'cache_directories': [
                    '~/Library/Caches',
                    '~/Library/Logs'
                ],
                'large_cache_threshold_mb': 500,
                'stale_cache_days': 30
            }

    def analyze_system_caches(self) -> dict:
        """
        Analyze system file caches and identify cleanup opportunities
        Returns comprehensive cache analysis with cleanup recommendations
        """
        cache_analysis = []
        total_cache_size_mb = 0
        total_cleanup_potential_mb = 0

        for cache_dir in self.cache_dirs:
            # Expand home directory
            expanded_path = Path(os.path.expanduser(cache_dir))

            if not expanded_path.exists():
                continue

            # Analyze this cache directory
            analysis = self._analyze_cache_directory(expanded_path)

            if analysis and analysis.get('size_mb', 0) > 0:
                cache_analysis.append(analysis)
                total_cache_size_mb += analysis['size_mb']
                total_cleanup_potential_mb += analysis.get('cleanup_potential_mb', 0)

        # Sort by size (descending)
        cache_analysis.sort(key=lambda x: x['size_mb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'cache_directories_analyzed': len(self.cache_dirs),
            'caches_found': len(cache_analysis),
            'cache_analysis': cache_analysis,
            'total_cache_size_mb': round(total_cache_size_mb, 2),
            'total_cache_size_gb': round(total_cache_size_mb / 1024, 2),
            'total_cleanup_potential_mb': round(total_cleanup_potential_mb, 2),
            'total_cleanup_potential_gb': round(total_cleanup_potential_mb / 1024, 2),
            'recommendations': self._generate_recommendations(cache_analysis, total_cleanup_potential_mb)
        }

    def _analyze_cache_directory(self, cache_path: Path) -> dict:
        """Analyze single cache directory"""
        try:
            # Get directory size using du
            result = subprocess.run(
                ['du', '-sm', str(cache_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return None

            # Parse size
            size_mb = 0
            try:
                size_str = result.stdout.strip().split()[0]
                size_mb = float(size_str)
            except (IndexError, ValueError):
                return None

            if size_mb < 1:  # Skip tiny caches
                return None

            # Check if this is a browser cache (should be excluded)
            is_browser_cache = any(pattern in str(cache_path) for pattern in self.exclude_patterns)

            if is_browser_cache:
                return {
                    'path': str(cache_path),
                    'size_mb': round(size_mb, 2),
                    'excluded': True,
                    'reason': 'Browser cache (handled by Agent 13)'
                }

            # Analyze subdirectories for large caches
            large_items = self._find_large_cache_items(cache_path)

            # Analyze stale items
            stale_items = self._find_stale_cache_items(cache_path)

            # Calculate cleanup potential
            cleanup_potential_mb = 0
            if large_items:
                cleanup_potential_mb += sum(item['size_mb'] for item in large_items)
            if stale_items:
                cleanup_potential_mb += sum(item['size_mb'] for item in stale_items)

            # Avoid double counting
            cleanup_potential_mb = min(cleanup_potential_mb, size_mb * 0.7)  # Max 70% cleanup

            return {
                'path': str(cache_path),
                'size_mb': round(size_mb, 2),
                'size_gb': round(size_mb / 1024, 2),
                'large_items': large_items[:10],  # Top 10
                'large_items_count': len(large_items),
                'stale_items': stale_items[:10],  # Top 10
                'stale_items_count': len(stale_items),
                'cleanup_potential_mb': round(cleanup_potential_mb, 2),
                'cleanup_potential_gb': round(cleanup_potential_mb / 1024, 2),
                'excluded': False
            }

        except Exception as e:
            return None

    def _find_large_cache_items(self, cache_path: Path) -> List[Dict]:
        """Find large cache items within directory"""
        try:
            # Use du to find large subdirectories
            result = subprocess.run(
                ['du', '-sm', str(cache_path) + '/*'],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            if result.returncode != 0:
                return []

            large_items = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue

                try:
                    size_mb = float(parts[0])
                    path = parts[1]

                    if size_mb >= self.large_cache_mb:
                        # Check if browser cache
                        is_browser = any(pattern in path for pattern in self.exclude_patterns)
                        if not is_browser:
                            large_items.append({
                                'path': path,
                                'size_mb': round(size_mb, 2),
                                'size_gb': round(size_mb / 1024, 2)
                            })
                except (ValueError, IndexError):
                    continue

            # Sort by size (descending)
            large_items.sort(key=lambda x: x['size_mb'], reverse=True)
            return large_items

        except Exception:
            return []

    def _find_stale_cache_items(self, cache_path: Path) -> List[Dict]:
        """Find stale cache items (not modified in X days)"""
        try:
            # Find files/dirs not accessed in X days
            cutoff_date = datetime.now() - timedelta(days=self.stale_days)

            result = subprocess.run(
                ['find', str(cache_path), '-type', 'f', '-atime', f'+{self.stale_days}', '-exec', 'du', '-sm', '{}', '+'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            stale_items = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue

                try:
                    size_mb = float(parts[0])
                    path = parts[1]

                    # Check if browser cache
                    is_browser = any(pattern in path for pattern in self.exclude_patterns)
                    if not is_browser and size_mb >= 10:  # At least 10 MB
                        stale_items.append({
                            'path': path,
                            'size_mb': round(size_mb, 2),
                            'age_days': self.stale_days
                        })
                except (ValueError, IndexError):
                    continue

            # Sort by size (descending)
            stale_items.sort(key=lambda x: x['size_mb'], reverse=True)
            return stale_items

        except Exception:
            return []

    def _generate_recommendations(self, cache_analysis: list, total_potential_mb: float) -> list:
        """Generate cache cleanup recommendations"""
        if total_potential_mb < 100:  # Less than 100 MB
            return [{
                'priority': 'low',
                'action': 'no_cleanup_needed',
                'description': 'System caches are minimal',
                'total_potential_mb': round(total_potential_mb, 2)
            }]

        recommendations = []

        # Large cache cleanup
        large_caches = [c for c in cache_analysis
                       if not c.get('excluded', False) and c.get('size_mb', 0) >= 1000]  # ≥1 GB

        if large_caches:
            total_large = sum(c['cleanup_potential_mb'] for c in large_caches)
            recommendations.append({
                'priority': 'high',
                'action': 'cleanup_large_caches',
                'description': f"Clean up {len(large_caches)} large cache directories",
                'caches': [c['path'] for c in large_caches[:5]],
                'expected_savings_mb': round(total_large, 2),
                'expected_savings_gb': round(total_large / 1024, 2),
                'method': 'selective_deletion',
                'risk': 'low',
                'impact': 'Apps may re-download cached data'
            })

        # Stale cache cleanup
        stale_caches = [c for c in cache_analysis
                       if not c.get('excluded', False) and c.get('stale_items_count', 0) > 0]

        if stale_caches:
            total_stale = sum(sum(item['size_mb'] for item in c.get('stale_items', [])[:10]) for c in stale_caches)
            recommendations.append({
                'priority': 'medium',
                'action': 'cleanup_stale_caches',
                'description': f"Clean up stale cache files (>{self.stale_days} days old)",
                'caches': [c['path'] for c in stale_caches[:5]],
                'expected_savings_mb': round(total_stale, 2),
                'expected_savings_gb': round(total_stale / 1024, 2),
                'method': 'age_based_deletion',
                'risk': 'very_low',
                'impact': 'Minimal - stale data unlikely to be needed'
            })

        # System log cleanup
        log_caches = [c for c in cache_analysis if 'Logs' in c['path'] and c.get('size_mb', 0) > 200]

        if log_caches:
            total_logs = sum(c['size_mb'] for c in log_caches)
            recommendations.append({
                'priority': 'medium',
                'action': 'cleanup_old_logs',
                'description': f"Clean up old system logs",
                'paths': [c['path'] for c in log_caches],
                'expected_savings_mb': round(total_logs * 0.8, 2),
                'expected_savings_gb': round(total_logs * 0.8 / 1024, 2),
                'method': 'log_rotation',
                'risk': 'very_low',
                'note': 'Keep recent logs, remove old diagnostic data'
            })

        # Bulk cleanup for significant savings
        if total_potential_mb >= 2000:  # ≥2 GB
            recommendations.append({
                'priority': 'high',
                'action': 'bulk_cache_cleanup',
                'description': f"Perform bulk system cache cleanup",
                'expected_savings_mb': round(total_potential_mb, 2),
                'expected_savings_gb': round(total_potential_mb / 1024, 2),
                'method': 'automated_cleanup',
                'estimated_time': '5-10 minutes',
                'risk': 'low',
                'impact': 'Temporary performance impact as caches rebuild',
                'note': 'Caches will be rebuilt automatically as needed'
            })

        return recommendations

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save file cache optimization report"""
        report = self.analyze_system_caches()
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
    print("=== File Cache Optimizer (Agent 23) ===\n")

    # Initialize optimizer
    optimizer = FileCacheOptimizer()

    # Analyze system caches
    print("Analyzing system caches (this may take 30-60 seconds)...\n")
    report = optimizer.analyze_system_caches()

    # Display summary
    print(f"Timestamp: {report['timestamp']}")
    print(f"Directories Analyzed: {report['cache_directories_analyzed']}")
    print(f"Caches Found: {report['caches_found']}\n")

    print(f"Total Cache Size: {report['total_cache_size_gb']} GB ({report['total_cache_size_mb']} MB)")
    print(f"Cleanup Potential: {report['total_cleanup_potential_gb']} GB ({report['total_cleanup_potential_mb']} MB)\n")

    # Display cache analysis
    if report['cache_analysis']:
        print(f"=== Cache Analysis ===")
        for i, cache in enumerate(report['cache_analysis'][:10], 1):
            if cache.get('excluded'):
                print(f"\n  {i}. {cache['path']} [EXCLUDED]")
                print(f"     Size: {cache['size_mb']} MB")
                print(f"     Reason: {cache['reason']}")
            else:
                print(f"\n  {i}. {cache['path']}")
                print(f"     Size: {cache['size_gb']} GB ({cache['size_mb']} MB)")
                print(f"     Cleanup Potential: {cache['cleanup_potential_gb']} GB ({cache['cleanup_potential_mb']} MB)")

                if cache.get('large_items_count', 0) > 0:
                    print(f"     Large Items: {cache['large_items_count']}")
                    for item in cache.get('large_items', [])[:3]:
                        item_name = Path(item['path']).name
                        print(f"       - {item_name}: {item['size_mb']} MB")

                if cache.get('stale_items_count', 0) > 0:
                    print(f"     Stale Items: {cache['stale_items_count']} (>{optimizer.stale_days} days old)")

        if len(report['cache_analysis']) > 10:
            print(f"\n... and {len(report['cache_analysis']) - 10} more caches")

    # Display recommendations
    if report['recommendations']:
        print(f"\n=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"     Action: {rec['action']}")

            if 'caches' in rec:
                print(f"     Target Caches:")
                for cache_path in rec['caches'][:3]:
                    print(f"       - {cache_path}")
            if 'paths' in rec:
                print(f"     Target Paths:")
                for path in rec['paths'][:3]:
                    print(f"       - {path}")
            if 'expected_savings_gb' in rec:
                print(f"     Expected Savings: {rec['expected_savings_gb']} GB")
            if 'method' in rec:
                print(f"     Method: {rec['method']}")
            if 'risk' in rec:
                print(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                print(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                print(f"     Est. Time: {rec['estimated_time']}")
            if 'note' in rec:
                print(f"     Note: {rec['note']}")

    # Save report
    output_path = Path(__file__).parent.parent / 'data' / 'file-cache-optimization.json'
    optimizer.generate_report(output_path)

    print(f"\n💡 NOTE: Browser caches are analyzed separately by Agent 13")

    return 0


if __name__ == '__main__':
    sys.exit(main())
