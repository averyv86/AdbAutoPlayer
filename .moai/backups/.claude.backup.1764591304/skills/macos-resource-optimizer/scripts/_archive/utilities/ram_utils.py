#!/usr/bin/env python3
"""
RAM Utilities - Core memory detection and management functions
Part of macOS Resource Optimizer v2.0
"""

import subprocess
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class RAMUtils:
    """Core utilities for RAM analysis and management"""

    # Memory pressure thresholds (in pages)
    PRESSURE_THRESHOLDS = {
        'normal': {'pageouts': 1000, 'swap_used_gb': 0.5},
        'warning': {'pageouts': 5000, 'swap_used_gb': 2.0},
        'critical': {'pageouts': 10000, 'swap_used_gb': 4.0}
    }

    # Memory leak detection thresholds
    LEAK_THRESHOLD_MB_PER_HOUR = 100
    MONITORING_WINDOW_HOURS = 4

    @staticmethod
    def get_vm_stat() -> Dict[str, int]:
        """
        Parse vm_stat output to get memory statistics
        Returns dict with page counts and compressed memory stats
        """
        try:
            result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {}

            stats = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    # Extract numeric value (remove periods and convert to int)
                    value = value.strip().rstrip('.')
                    try:
                        stats[key] = int(value)
                    except ValueError:
                        continue

            return stats
        except Exception as e:
            print(f"Error getting vm_stat: {e}")
            return {}

    @staticmethod
    def get_memory_pressure() -> Tuple[str, Dict[str, any]]:
        """
        Determine system memory pressure level
        Returns: (pressure_level, detailed_stats)
        pressure_level: 'normal' | 'warning' | 'critical'
        """
        vm_stats = RAMUtils.get_vm_stat()
        if not vm_stats:
            return 'unknown', {}

        pageouts = vm_stats.get('pageouts', 0)
        swap_used_mb = vm_stats.get('swapouts', 0) * 4096 / (1024 * 1024)  # Convert pages to MB
        swap_used_gb = swap_used_mb / 1024

        # Calculate memory pressure level
        if pageouts > RAMUtils.PRESSURE_THRESHOLDS['critical']['pageouts'] or \
           swap_used_gb > RAMUtils.PRESSURE_THRESHOLDS['critical']['swap_used_gb']:
            level = 'critical'
        elif pageouts > RAMUtils.PRESSURE_THRESHOLDS['warning']['pageouts'] or \
             swap_used_gb > RAMUtils.PRESSURE_THRESHOLDS['warning']['swap_used_gb']:
            level = 'warning'
        else:
            level = 'normal'

        # Detailed stats
        details = {
            'pageouts': pageouts,
            'swap_used_gb': round(swap_used_gb, 2),
            'compressed_pages': vm_stats.get('pages_stored_in_compressor', 0),
            'compressed_occupied': vm_stats.get('pages_occupied_by_compressor', 0),
            'free_pages': vm_stats.get('pages_free', 0),
            'active_pages': vm_stats.get('pages_active', 0),
            'inactive_pages': vm_stats.get('pages_inactive', 0),
            'wired_pages': vm_stats.get('pages_wired_down', 0)
        }

        return level, details

    @staticmethod
    def get_process_memory(pid: int) -> Optional[Dict[str, any]]:
        """
        Get detailed memory stats for a specific process
        Returns dict with RSS, VSZ, compressed memory, etc.
        """
        try:
            # Use ps to get basic memory info
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'pid,rss,vsz,%mem,command'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 or len(result.stdout.split('\n')) < 2:
                return None

            # Parse ps output (skip header)
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None

            data = lines[1].split(None, 4)  # Split on whitespace, max 5 parts
            if len(data) < 5:
                return None

            return {
                'pid': int(data[0]),
                'rss_kb': int(data[1]),
                'rss_mb': round(int(data[1]) / 1024, 2),
                'rss_gb': round(int(data[1]) / (1024 * 1024), 2),
                'vsz_kb': int(data[2]),
                'mem_percent': float(data[3]),
                'command': data[4]
            }
        except Exception as e:
            print(f"Error getting memory for PID {pid}: {e}")
            return None

    @staticmethod
    def get_all_processes_memory() -> List[Dict[str, any]]:
        """
        Get memory stats for all processes, sorted by RSS
        Returns list of process dicts
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

            processes = []
            lines = result.stdout.strip().split('\n')

            # Skip header
            for line in lines[1:]:
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue

                try:
                    rss_kb = int(parts[5])
                    processes.append({
                        'user': parts[0],
                        'pid': int(parts[1]),
                        'cpu_percent': float(parts[2]),
                        'mem_percent': float(parts[3]),
                        'rss_kb': rss_kb,
                        'rss_mb': round(rss_kb / 1024, 2),
                        'rss_gb': round(rss_kb / (1024 * 1024), 2),
                        'command': parts[10]
                    })
                except (ValueError, IndexError):
                    continue

            # Sort by RSS (descending)
            processes.sort(key=lambda x: x['rss_kb'], reverse=True)
            return processes

        except Exception as e:
            print(f"Error getting all processes: {e}")
            return []

    @staticmethod
    def detect_memory_leak(pid: int, history_file: Optional[Path] = None,
                          window_hours: int = MONITORING_WINDOW_HOURS) -> Dict[str, any]:
        """
        Detect memory leak by tracking process RAM growth over time
        Returns: {'is_leak': bool, 'growth_mb_per_hour': float, 'data_points': int}
        """
        if history_file is None:
            history_file = Path('/tmp/macos-optimizer-memory-history.json')

        # Load historical data
        history = {}
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = {}

        # Get current memory usage
        current_mem = RAMUtils.get_process_memory(pid)
        if not current_mem:
            return {'is_leak': False, 'growth_mb_per_hour': 0, 'data_points': 0}

        # Add current data point
        pid_str = str(pid)
        current_time = time.time()

        if pid_str not in history:
            history[pid_str] = []

        history[pid_str].append({
            'timestamp': current_time,
            'rss_mb': current_mem['rss_mb'],
            'command': current_mem['command']
        })

        # Keep only data within monitoring window
        cutoff_time = current_time - (window_hours * 3600)
        history[pid_str] = [
            dp for dp in history[pid_str]
            if dp['timestamp'] > cutoff_time
        ]

        # Save updated history
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except:
            pass

        # Analyze for leak (need at least 3 data points)
        data_points = history[pid_str]
        if len(data_points) < 3:
            return {'is_leak': False, 'growth_mb_per_hour': 0, 'data_points': len(data_points)}

        # Calculate growth rate (MB per hour)
        first = data_points[0]
        last = data_points[-1]
        time_diff_hours = (last['timestamp'] - first['timestamp']) / 3600

        if time_diff_hours < 0.5:  # Need at least 30 minutes of data
            return {'is_leak': False, 'growth_mb_per_hour': 0, 'data_points': len(data_points)}

        growth_mb = last['rss_mb'] - first['rss_mb']
        growth_rate = growth_mb / time_diff_hours

        is_leak = growth_rate > RAMUtils.LEAK_THRESHOLD_MB_PER_HOUR

        return {
            'is_leak': is_leak,
            'growth_mb_per_hour': round(growth_rate, 2),
            'data_points': len(data_points),
            'current_mb': last['rss_mb'],
            'initial_mb': first['rss_mb'],
            'total_growth_mb': round(growth_mb, 2),
            'monitoring_hours': round(time_diff_hours, 2)
        }

    @staticmethod
    def safe_terminate(pid: int, preserve_state: bool = False,
                      signal: str = 'TERM') -> Dict[str, any]:
        """
        Safely terminate a process with optional state preservation
        Args:
            pid: Process ID to terminate
            preserve_state: If True, attempt graceful shutdown
            signal: Signal to send ('TERM' for graceful, 'KILL' for force)
        Returns: {'success': bool, 'message': str}
        """
        try:
            # Check if process exists
            result = subprocess.run(
                ['ps', '-p', str(pid)],
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                return {'success': False, 'message': f'Process {pid} not found'}

            # Get process info before termination
            proc_info = RAMUtils.get_process_memory(pid)
            if not proc_info:
                return {'success': False, 'message': f'Cannot get info for PID {pid}'}

            # Terminate process
            if preserve_state and signal == 'TERM':
                # Send SIGTERM for graceful shutdown
                subprocess.run(['kill', '-TERM', str(pid)], timeout=5)

                # Wait up to 5 seconds for graceful termination
                for _ in range(10):
                    time.sleep(0.5)
                    check = subprocess.run(
                        ['ps', '-p', str(pid)],
                        capture_output=True,
                        timeout=2
                    )
                    if check.returncode != 0:
                        # Process terminated gracefully
                        return {
                            'success': True,
                            'message': f'Process {pid} terminated gracefully',
                            'freed_mb': proc_info['rss_mb']
                        }

                # If still running, force kill
                subprocess.run(['kill', '-KILL', str(pid)], timeout=5)
                return {
                    'success': True,
                    'message': f'Process {pid} force killed after timeout',
                    'freed_mb': proc_info['rss_mb']
                }
            else:
                # Direct kill
                signal_flag = '-KILL' if signal == 'KILL' else '-TERM'
                subprocess.run(['kill', signal_flag, str(pid)], timeout=5)
                return {
                    'success': True,
                    'message': f'Process {pid} terminated with {signal}',
                    'freed_mb': proc_info['rss_mb']
                }

        except Exception as e:
            return {'success': False, 'message': f'Error terminating PID {pid}: {str(e)}'}

    @staticmethod
    def calculate_total_ram_usage() -> Dict[str, float]:
        """
        Calculate total RAM usage across all processes
        Returns dict with totals in GB
        """
        processes = RAMUtils.get_all_processes_memory()
        total_rss_gb = sum(p['rss_gb'] for p in processes)

        # Get system memory info
        pressure_level, vm_details = RAMUtils.get_memory_pressure()

        return {
            'total_rss_gb': round(total_rss_gb, 2),
            'process_count': len(processes),
            'pressure_level': pressure_level,
            'compressed_gb': round(vm_details.get('compressed_pages', 0) * 4096 / (1024**3), 2),
            'free_gb': round(vm_details.get('free_pages', 0) * 4096 / (1024**3), 2)
        }


if __name__ == '__main__':
    # Test the utilities
    print("=== RAM Utilities Test ===\n")

    # Test 1: Memory pressure
    pressure, details = RAMUtils.get_memory_pressure()
    print(f"Memory Pressure: {pressure.upper()}")
    print(f"  Pageouts: {details['pageouts']:,}")
    print(f"  Swap Used: {details['swap_used_gb']} GB")
    print(f"  Compressed: {details['compressed_pages']:,} pages\n")

    # Test 2: Top 5 processes by memory
    print("Top 5 Memory Consumers:")
    processes = RAMUtils.get_all_processes_memory()[:5]
    for i, proc in enumerate(processes, 1):
        print(f"  {i}. {proc['command'][:50]:50s} {proc['rss_gb']:.2f} GB")

    # Test 3: Total RAM usage
    print("\nTotal RAM Usage:")
    totals = RAMUtils.calculate_total_ram_usage()
    print(f"  Total RSS: {totals['total_rss_gb']} GB")
    print(f"  Processes: {totals['process_count']}")
    print(f"  Free: {totals['free_gb']} GB")
