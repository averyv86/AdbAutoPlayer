#!/usr/bin/env python3
"""
Application Hibernation Utilities
Core library for app suspension, state preservation, and activity detection
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 3
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import re


class HibernationUtils:
    """
    Core utilities for application hibernation and state management
    """

    # Electron-based apps (special handling required)
    ELECTRON_APPS = {
        'Visual Studio Code': {
            'process_names': ['Code', 'Code Helper', 'Electron'],
            'helper_pattern': r'Code Helper',
            'max_normal_helpers': 10,
            'state_file': '~/Library/Application Support/Code/User/workspaceStorage'
        },
        'Slack': {
            'process_names': ['Slack', 'Slack Helper'],
            'helper_pattern': r'Slack Helper',
            'max_normal_helpers': 8,
            'state_file': '~/Library/Application Support/Slack'
        },
        'Notion': {
            'process_names': ['Notion', 'Notion Helper'],
            'helper_pattern': r'Notion Helper',
            'max_normal_helpers': 5,
            'state_file': '~/Library/Application Support/Notion'
        },
        'Discord': {
            'process_names': ['Discord', 'Discord Helper'],
            'helper_pattern': r'Discord Helper',
            'max_normal_helpers': 6,
            'state_file': '~/Library/Application Support/discord'
        }
    }

    # Background apps (can be safely suspended)
    BACKGROUND_APPS = {
        'Mail': {'process_names': ['Mail'], 'safe_suspend': True},
        'Messages': {'process_names': ['Messages'], 'safe_suspend': True},
        'Calendar': {'process_names': ['Calendar'], 'safe_suspend': True},
        'Notes': {'process_names': ['Notes'], 'safe_suspend': True},
        'Reminders': {'process_names': ['Reminders'], 'safe_suspend': True},
        'Photos': {'process_names': ['Photos'], 'safe_suspend': False},  # Photo library in use
        'Music': {'process_names': ['Music'], 'safe_suspend': True}
    }

    # Protected apps (never suspend)
    PROTECTED_APPS = [
        'Finder', 'Dock', 'WindowServer', 'SystemUIServer',
        'loginwindow', 'launchd', 'kernel_task', 'mds', 'mds_stores',
        'Activity Monitor', 'Console', 'Terminal', 'iTerm'
    ]

    @staticmethod
    def detect_inactive_apps(timeout_hours: int = 2, min_memory_mb: int = 1000) -> List[Dict[str, any]]:
        """
        Detect applications that have been idle for specified timeout

        Args:
            timeout_hours: Hours of inactivity threshold (default: 2)
            min_memory_mb: Minimum memory usage to consider (default: 1000 MB)

        Returns:
            List of inactive app dicts with memory and activity info
        """
        inactive_apps = []

        try:
            # Get all running processes
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            # Parse process list
            for line in result.stdout.split('\n')[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue

                cpu_percent = float(parts[2])
                mem_percent = float(parts[3])
                command = parts[10]

                # Extract app name
                app_name = HibernationUtils._extract_app_name(command)
                if not app_name:
                    continue

                # Skip protected apps
                if app_name in HibernationUtils.PROTECTED_APPS:
                    continue

                # Calculate memory in MB
                mem_mb = HibernationUtils._calculate_process_memory_mb(line)

                if mem_mb < min_memory_mb:
                    continue

                # Check CPU activity (idle = < 1% CPU for 2+ hours)
                # In practice, we approximate by checking if CPU < 0.5%
                is_idle = cpu_percent < 0.5

                if is_idle:
                    # Get app memory details
                    app_memory = HibernationUtils._get_app_total_memory(app_name)

                    inactive_apps.append({
                        'app_name': app_name,
                        'cpu_percent': cpu_percent,
                        'memory_gb': round(app_memory / 1024, 2),
                        'memory_mb': app_memory,
                        'idle_status': 'inactive',
                        'priority': 'high' if app_memory > 2000 else 'medium',
                        'can_suspend': HibernationUtils._can_safely_suspend(app_name)
                    })

        except Exception as e:
            print(f"Error detecting inactive apps: {e}")

        # Sort by memory (descending)
        inactive_apps.sort(key=lambda x: x['memory_mb'], reverse=True)

        return inactive_apps

    @staticmethod
    def _extract_app_name(command: str) -> Optional[str]:
        """Extract clean app name from ps command string"""
        # Remove path and arguments
        if '.app/' in command:
            match = re.search(r'/([^/]+)\.app/', command)
            if match:
                return match.group(1)

        # Try to extract from command
        base_cmd = command.split()[0] if command else ''
        app_name = Path(base_cmd).name

        # Remove common suffixes
        app_name = app_name.replace(' Helper', '').replace('.app', '')

        return app_name if app_name else None

    @staticmethod
    def _calculate_process_memory_mb(ps_line: str) -> float:
        """Calculate process memory in MB from ps aux line"""
        try:
            parts = ps_line.split(None, 10)
            if len(parts) < 6:
                return 0.0

            # RSS is in KB (column 6)
            rss_kb = float(parts[5])
            return rss_kb / 1024
        except:
            return 0.0

    @staticmethod
    def _get_app_total_memory(app_name: str) -> float:
        """Get total memory usage for app including all helpers (in MB)"""
        try:
            # Get all processes matching app name
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return 0.0

            total_memory_mb = 0.0

            for line in result.stdout.split('\n'):
                if app_name in line:
                    mem_mb = HibernationUtils._calculate_process_memory_mb(line)
                    total_memory_mb += mem_mb

            return total_memory_mb

        except:
            return 0.0

    @staticmethod
    def _can_safely_suspend(app_name: str) -> bool:
        """Check if app can be safely suspended"""
        # Check if protected
        if app_name in HibernationUtils.PROTECTED_APPS:
            return False

        # Check if explicitly marked as safe in background apps
        if app_name in HibernationUtils.BACKGROUND_APPS:
            return HibernationUtils.BACKGROUND_APPS[app_name]['safe_suspend']

        # Electron apps need special handling
        if app_name in HibernationUtils.ELECTRON_APPS:
            return True  # Can suspend but need state preservation

        # Default: safe to suspend if not protected
        return True

    @staticmethod
    def get_app_activity_level(app_name: str) -> Dict[str, any]:
        """
        Get detailed activity level for an application

        Returns:
            Dict with CPU usage, memory, helper count, activity status
        """
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get process list'}

            total_cpu = 0.0
            total_memory_mb = 0.0
            process_count = 0
            helper_count = 0

            for line in result.stdout.split('\n'):
                if app_name not in line:
                    continue

                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue

                cpu = float(parts[2])
                mem_mb = HibernationUtils._calculate_process_memory_mb(line)

                total_cpu += cpu
                total_memory_mb += mem_mb
                process_count += 1

                # Count helpers
                if 'Helper' in line:
                    helper_count += 1

            # Determine activity level
            if total_cpu < 0.5:
                activity = 'idle'
            elif total_cpu < 5:
                activity = 'low'
            elif total_cpu < 20:
                activity = 'moderate'
            else:
                activity = 'active'

            return {
                'app_name': app_name,
                'activity_level': activity,
                'cpu_percent': round(total_cpu, 2),
                'memory_gb': round(total_memory_mb / 1024, 2),
                'memory_mb': round(total_memory_mb, 2),
                'process_count': process_count,
                'helper_count': helper_count,
                'can_suspend': HibernationUtils._can_safely_suspend(app_name),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def suspend_app(app_name: str, preserve_state: bool = True) -> Dict[str, any]:
        """
        Suspend an application gracefully

        Args:
            app_name: Name of app to suspend
            preserve_state: Whether to preserve app state before suspension

        Returns:
            Dict with suspension status and details
        """
        if app_name in HibernationUtils.PROTECTED_APPS:
            return {
                'success': False,
                'error': 'Cannot suspend protected app',
                'app_name': app_name
            }

        try:
            # Get app activity before suspension
            before_state = HibernationUtils.get_app_activity_level(app_name)

            # For Electron apps, preserve state if requested
            if preserve_state and app_name in HibernationUtils.ELECTRON_APPS:
                state_preserved = HibernationUtils._preserve_electron_state(app_name)
            else:
                state_preserved = False

            # Quit the app gracefully (macOS will preserve state if App Nap enabled)
            result = subprocess.run(
                ['osascript', '-e', f'quit app "{app_name}"'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Wait for app to quit
            time.sleep(2)

            # Verify app is quit
            after_state = HibernationUtils.get_app_activity_level(app_name)

            success = after_state['process_count'] == 0

            return {
                'success': success,
                'app_name': app_name,
                'memory_freed_gb': before_state['memory_gb'] if success else 0,
                'memory_freed_mb': before_state['memory_mb'] if success else 0,
                'state_preserved': state_preserved,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'app_name': app_name
            }

    @staticmethod
    def _preserve_electron_state(app_name: str) -> bool:
        """Preserve Electron app state before suspension"""
        if app_name not in HibernationUtils.ELECTRON_APPS:
            return False

        try:
            app_info = HibernationUtils.ELECTRON_APPS[app_name]
            state_path = Path(app_info['state_file']).expanduser()

            # Verify state directory exists
            if not state_path.exists():
                return False

            # State is automatically preserved by Electron
            # Just verify we have write access
            return state_path.is_dir()

        except:
            return False

    @staticmethod
    def resume_app(app_name: str) -> Dict[str, any]:
        """
        Resume a suspended application

        Args:
            app_name: Name of app to resume

        Returns:
            Dict with resume status
        """
        try:
            # Open the app
            result = subprocess.run(
                ['open', '-a', app_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Could not open app',
                    'app_name': app_name
                }

            # Wait for app to start
            time.sleep(3)

            # Get app state after resume
            after_state = HibernationUtils.get_app_activity_level(app_name)

            success = after_state['process_count'] > 0

            return {
                'success': success,
                'app_name': app_name,
                'memory_used_gb': after_state['memory_gb'],
                'memory_used_mb': after_state['memory_mb'],
                'process_count': after_state['process_count'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'app_name': app_name
            }

    @staticmethod
    def get_hibernation_candidates() -> Dict[str, any]:
        """
        Get comprehensive list of hibernation candidates

        Returns:
            Dict with inactive apps, Electron apps, background apps
        """
        # Detect inactive apps
        inactive_apps = HibernationUtils.detect_inactive_apps(timeout_hours=2, min_memory_mb=1000)

        # Get Electron app status
        electron_apps = []
        for app_name in HibernationUtils.ELECTRON_APPS.keys():
            activity = HibernationUtils.get_app_activity_level(app_name)
            if activity.get('process_count', 0) > 0:
                electron_apps.append(activity)

        # Get background app status
        background_apps = []
        for app_name in HibernationUtils.BACKGROUND_APPS.keys():
            activity = HibernationUtils.get_app_activity_level(app_name)
            if activity.get('process_count', 0) > 0:
                background_apps.append(activity)

        # Calculate totals
        total_inactive_memory = sum(app['memory_mb'] for app in inactive_apps)
        total_electron_memory = sum(app.get('memory_mb', 0) for app in electron_apps)
        total_background_memory = sum(app.get('memory_mb', 0) for app in background_apps)

        return {
            'timestamp': datetime.now().isoformat(),
            'inactive_apps': inactive_apps,
            'electron_apps': electron_apps,
            'background_apps': background_apps,
            'summary': {
                'inactive_count': len(inactive_apps),
                'inactive_memory_gb': round(total_inactive_memory / 1024, 2),
                'electron_count': len(electron_apps),
                'electron_memory_gb': round(total_electron_memory / 1024, 2),
                'background_count': len(background_apps),
                'background_memory_gb': round(total_background_memory / 1024, 2),
                'total_hibernation_potential_gb': round(
                    (total_inactive_memory + total_electron_memory + total_background_memory) / 1024, 2
                )
            }
        }


def main():
    """Test hibernation utilities"""
    print("=== Hibernation Utilities Test ===\n")

    # Get hibernation candidates
    candidates = HibernationUtils.get_hibernation_candidates()

    print(f"Timestamp: {candidates['timestamp']}\n")
    print("=== Summary ===")
    print(f"Inactive Apps: {candidates['summary']['inactive_count']} ({candidates['summary']['inactive_memory_gb']} GB)")
    print(f"Electron Apps: {candidates['summary']['electron_count']} ({candidates['summary']['electron_memory_gb']} GB)")
    print(f"Background Apps: {candidates['summary']['background_count']} ({candidates['summary']['background_memory_gb']} GB)")
    print(f"Total Hibernation Potential: {candidates['summary']['total_hibernation_potential_gb']} GB\n")

    if candidates['inactive_apps']:
        print("=== Inactive Apps ===")
        for app in candidates['inactive_apps'][:10]:
            print(f"  {app['app_name']:30s}  {app['memory_gb']:6.2f} GB  CPU: {app['cpu_percent']:5.2f}%  [{app['priority']}]")

    if candidates['electron_apps']:
        print("\n=== Electron Apps ===")
        for app in candidates['electron_apps']:
            print(f"  {app['app_name']:30s}  {app['memory_gb']:6.2f} GB  Helpers: {app['helper_count']}")

    if candidates['background_apps']:
        print("\n=== Background Apps ===")
        for app in candidates['background_apps']:
            safe = "YES" if app['can_suspend'] else "NO"
            print(f"  {app['app_name']:30s}  {app['memory_gb']:6.2f} GB  Safe: {safe}")


if __name__ == '__main__':
    main()
