#!/usr/bin/env python3
"""
Browser Utilities - Core browser management functions
Part of macOS Resource Optimizer v2.0 - RAM Optimization
"""

import subprocess
import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

class BrowserUtils:
    """Core utilities for browser memory management"""

    # Browser process patterns
    BROWSER_PATTERNS = {
        'arc': {
            'app_name': 'Arc',
            'process_names': ['Arc', 'Dia'],
            'helper_pattern': r'(Arc Helper|Dia)',
            'renderer_pattern': r'Helper.*Renderer',
            'gpu_pattern': r'Helper.*GPU',
            'network_pattern': r'Helper.*Network'
        },
        'chrome': {
            'app_name': 'Google Chrome',
            'process_names': ['Google Chrome'],
            'helper_pattern': r'Chrome Helper',
            'renderer_pattern': r'Helper.*Renderer',
            'gpu_pattern': r'Helper.*GPU',
            'network_pattern': r'Helper.*Network'
        },
        'safari': {
            'app_name': 'Safari',
            'process_names': ['Safari'],
            'helper_pattern': r'com\.apple\.WebKit',
            'renderer_pattern': r'WebKit\.WebContent',
            'gpu_pattern': r'WebKit\.GPU',
            'network_pattern': r'WebKit\.Networking'
        },
        'firefox': {
            'app_name': 'Firefox',
            'process_names': ['Firefox', 'firefox-bin'],
            'helper_pattern': r'(firefox|plugin-container)',
            'renderer_pattern': r'RDD Process|Web Content',
            'gpu_pattern': r'GPU Process',
            'network_pattern': r'Socket Process'
        }
    }

    @staticmethod
    def detect_running_browsers() -> List[str]:
        """
        Detect which browsers are currently running
        Returns list of browser keys (arc, chrome, safari, firefox)
        """
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            running = []
            processes = result.stdout.lower()

            for browser_key, config in BrowserUtils.BROWSER_PATTERNS.items():
                for process_name in config['process_names']:
                    if process_name.lower() in processes:
                        running.append(browser_key)
                        break

            return running
        except Exception as e:
            print(f"Error detecting browsers: {e}")
            return []

    @staticmethod
    def get_browser_processes(browser: str) -> List[Dict[str, any]]:
        """
        Get all processes for a specific browser with memory info
        Returns list of process dicts with classification
        """
        if browser not in BrowserUtils.BROWSER_PATTERNS:
            return []

        config = BrowserUtils.BROWSER_PATTERNS[browser]

        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            processes = []
            lines = result.stdout.strip().split('\n')

            for line in lines[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue

                command = parts[10]

                # Check if this is a browser process
                is_browser = False
                for process_name in config['process_names']:
                    if process_name in command:
                        is_browser = True
                        break

                if not is_browser and not re.search(config['helper_pattern'], command):
                    continue

                try:
                    rss_kb = int(parts[5])

                    # Classify process type
                    process_type = 'main'
                    if re.search(config['renderer_pattern'], command):
                        process_type = 'renderer'
                    elif re.search(config['gpu_pattern'], command):
                        process_type = 'gpu'
                    elif re.search(config['network_pattern'], command):
                        process_type = 'network'
                    elif 'Helper' in command or 'helper' in command.lower():
                        process_type = 'other_helper'

                    processes.append({
                        'browser': browser,
                        'pid': int(parts[1]),
                        'cpu_percent': float(parts[2]),
                        'mem_percent': float(parts[3]),
                        'rss_kb': rss_kb,
                        'rss_mb': round(rss_kb / 1024, 2),
                        'rss_gb': round(rss_kb / (1024 * 1024), 2),
                        'process_type': process_type,
                        'command': command
                    })
                except (ValueError, IndexError):
                    continue

            # Sort by RSS (descending)
            processes.sort(key=lambda x: x['rss_kb'], reverse=True)
            return processes

        except Exception as e:
            print(f"Error getting browser processes: {e}")
            return []

    @staticmethod
    def group_browser_helpers(browser: str) -> Dict[str, List[Dict]]:
        """
        Group browser helper processes by type
        Returns: {
            'main': [...],
            'renderer': [...],
            'gpu': [...],
            'network': [...],
            'other_helper': [...]
        }
        """
        processes = BrowserUtils.get_browser_processes(browser)

        grouped = defaultdict(list)
        for proc in processes:
            grouped[proc['process_type']].append(proc)

        return dict(grouped)

    @staticmethod
    def calculate_browser_memory(browser: str) -> Dict[str, any]:
        """
        Calculate total memory usage for a browser
        Returns detailed breakdown by process type
        """
        processes = BrowserUtils.get_browser_processes(browser)

        if not processes:
            return {
                'browser': browser,
                'total_gb': 0,
                'total_mb': 0,
                'process_count': 0
            }

        grouped = defaultdict(lambda: {'count': 0, 'memory_gb': 0})

        for proc in processes:
            ptype = proc['process_type']
            grouped[ptype]['count'] += 1
            grouped[ptype]['memory_gb'] += proc['rss_gb']

        total_gb = sum(proc['rss_gb'] for proc in processes)

        return {
            'browser': browser,
            'total_gb': round(total_gb, 2),
            'total_mb': round(total_gb * 1024, 2),
            'process_count': len(processes),
            'breakdown': {
                ptype: {
                    'count': data['count'],
                    'memory_gb': round(data['memory_gb'], 2)
                }
                for ptype, data in grouped.items()
            },
            'processes': processes
        }

    @staticmethod
    def find_high_memory_helpers(browser: str, threshold_mb: int = 500) -> List[Dict]:
        """
        Find helper processes exceeding memory threshold
        Returns list of high-memory helpers sorted by memory
        """
        processes = BrowserUtils.get_browser_processes(browser)

        high_memory = [
            proc for proc in processes
            if proc['process_type'] in ['renderer', 'gpu', 'network', 'other_helper']
            and proc['rss_mb'] > threshold_mb
        ]

        return high_memory

    @staticmethod
    def count_helpers_by_type(browser: str) -> Dict[str, int]:
        """
        Count helper processes by type
        Returns: {'renderer': N, 'gpu': N, 'network': N, 'other': N}
        """
        grouped = BrowserUtils.group_browser_helpers(browser)

        return {
            'renderer': len(grouped.get('renderer', [])),
            'gpu': len(grouped.get('gpu', [])),
            'network': len(grouped.get('network', [])),
            'other': len(grouped.get('other_helper', [])),
            'total_helpers': sum([
                len(grouped.get('renderer', [])),
                len(grouped.get('gpu', [])),
                len(grouped.get('network', [])),
                len(grouped.get('other_helper', []))
            ])
        }

    @staticmethod
    def get_browser_cache_size(browser: str) -> Dict[str, any]:
        """
        Estimate browser cache size
        Returns cache location and estimated size in GB
        """
        cache_paths = {
            'arc': '~/Library/Caches/company.thebrowser.Browser',
            'chrome': '~/Library/Caches/Google/Chrome',
            'safari': '~/Library/Caches/com.apple.Safari',
            'firefox': '~/Library/Caches/Firefox'
        }

        if browser not in cache_paths:
            return {'browser': browser, 'cache_gb': 0, 'path': None}

        cache_path = Path(cache_paths[browser]).expanduser()

        if not cache_path.exists():
            return {'browser': browser, 'cache_gb': 0, 'path': str(cache_path)}

        try:
            result = subprocess.run(
                ['du', '-sh', str(cache_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                size_str = result.stdout.split()[0]

                # Parse size (handles G, M, K suffixes)
                match = re.match(r'([\d.]+)([GMK])?', size_str)
                if match:
                    size = float(match.group(1))
                    unit = match.group(2) or 'K'

                    # Convert to GB
                    if unit == 'G':
                        size_gb = size
                    elif unit == 'M':
                        size_gb = size / 1024
                    else:  # K
                        size_gb = size / (1024 * 1024)

                    return {
                        'browser': browser,
                        'cache_gb': round(size_gb, 2),
                        'cache_mb': round(size_gb * 1024, 2),
                        'path': str(cache_path)
                    }
        except Exception as e:
            print(f"Error calculating cache size: {e}")

        return {'browser': browser, 'cache_gb': 0, 'path': str(cache_path)}

    @staticmethod
    def analyze_all_browsers() -> Dict[str, Dict]:
        """
        Comprehensive analysis of all running browsers
        Returns dict: {browser_key: analysis_data}
        """
        running_browsers = BrowserUtils.detect_running_browsers()

        analysis = {}
        for browser in running_browsers:
            memory_data = BrowserUtils.calculate_browser_memory(browser)
            cache_data = BrowserUtils.get_browser_cache_size(browser)
            helper_counts = BrowserUtils.count_helpers_by_type(browser)
            high_memory = BrowserUtils.find_high_memory_helpers(browser)

            analysis[browser] = {
                'memory': memory_data,
                'cache': cache_data,
                'helpers': helper_counts,
                'high_memory_helpers': len(high_memory),
                'optimization_potential_gb': round(
                    (memory_data['total_gb'] * 0.4) +  # 40% memory reduction potential
                    (cache_data['cache_gb'] * 0.8),    # 80% cache can be cleared
                    2
                )
            }

        return analysis


if __name__ == '__main__':
    # Test the utilities
    print("=== Browser Utilities Test ===\n")

    # Detect running browsers
    running = BrowserUtils.detect_running_browsers()
    print(f"Running Browsers: {', '.join(running) if running else 'None'}\n")

    # Analyze all browsers
    analysis = BrowserUtils.analyze_all_browsers()

    for browser, data in analysis.items():
        print(f"\n{browser.upper()} Analysis:")
        print(f"  Total Memory: {data['memory']['total_gb']} GB")
        print(f"  Process Count: {data['memory']['process_count']}")
        print(f"  Helpers: {data['helpers']['total_helpers']} " +
              f"(R:{data['helpers']['renderer']}, " +
              f"G:{data['helpers']['gpu']}, " +
              f"N:{data['helpers']['network']}, " +
              f"O:{data['helpers']['other']})")
        print(f"  Cache Size: {data['cache']['cache_gb']} GB")
        print(f"  High Memory Helpers: {data['high_memory_helpers']}")
        print(f"  Optimization Potential: {data['optimization_potential_gb']} GB")
