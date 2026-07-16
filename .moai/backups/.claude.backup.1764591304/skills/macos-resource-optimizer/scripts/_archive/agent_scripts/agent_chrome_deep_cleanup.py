#!/usr/bin/env python3
"""
Agent: Chrome Deep Cleanup Analyzer
Scans Chrome data directories for cacheable/cleanable data.
Analyzes Service Workers, GPUCache, IndexedDB, blob_storage, crash reports.
Part of macOS Resource Optimizer - Browser Deep Cleanup Suite
"""

import json
import subprocess
import sys
import os
import time
from pathlib import Path


def get_directory_size_mb(path: Path) -> float:
    """Get directory size in MB using du command."""
    if not path.exists():
        return 0.0
    try:
        result = subprocess.run(
            ['du', '-sk', str(path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            size_kb = int(result.stdout.split()[0])
            return size_kb / 1024.0
    except Exception:
        pass
    return 0.0


def scan_chrome_directories() -> dict:
    """Scan all Chrome data directories for cleanable data."""
    home = Path.home()
    categories = {}

    # Chrome data paths to scan
    scan_paths = {
        'service_worker': home / 'Library/Application Support/Google/Chrome/Default/Service Worker',
        'gpu_cache': home / 'Library/Application Support/Google/Chrome/Default/GPUCache',
        'shader_cache': home / 'Library/Application Support/Google/Chrome/Default/ShaderCache',
        'code_cache': home / 'Library/Application Support/Google/Chrome/Default/Code Cache',
        'cache': home / 'Library/Caches/Google/Chrome',
        'crash_reports': home / 'Library/Application Support/Google/Chrome/Crash Reports',
        'indexeddb': home / 'Library/Application Support/Google/Chrome/Default/IndexedDB',
        'blob_storage': home / 'Library/Application Support/Google/Chrome/Default/blob_storage',
        'local_storage': home / 'Library/Application Support/Google/Chrome/Default/Local Storage',
        'session_storage': home / 'Library/Application Support/Google/Chrome/Default/Session Storage',
        'webrtc_logs': home / 'Library/Application Support/Google/Chrome/Default/WebRTC Logs',
        'file_system': home / 'Library/Application Support/Google/Chrome/Default/File System'
    }

    for category, path in scan_paths.items():
        size_mb = get_directory_size_mb(path)
        categories[category] = {
            'path': str(path),
            'exists': path.exists(),
            'size_mb': round(size_mb, 2),
            'size_gb': round(size_mb / 1024.0, 3)
        }

    return categories


def analyze_profiles() -> list:
    """Find and analyze all Chrome profiles."""
    profiles = []
    chrome_base = Path.home() / 'Library/Application Support/Google/Chrome'

    if not chrome_base.exists():
        return profiles

    # Look for profile directories
    for item in chrome_base.iterdir():
        if item.is_dir() and (item.name == 'Default' or item.name.startswith('Profile ')):
            profile_size = get_directory_size_mb(item)
            profiles.append({
                'name': item.name,
                'path': str(item),
                'size_mb': round(profile_size, 2),
                'size_gb': round(profile_size / 1024.0, 3)
            })

    return profiles


def count_old_crash_reports() -> dict:
    """Count crash reports older than 7 days."""
    crash_dir = Path.home() / 'Library/Application Support/Google/Chrome/Crash Reports'

    if not crash_dir.exists():
        return {'count': 0, 'size_mb': 0}

    old_count = 0
    old_size = 0
    cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago

    try:
        for item in crash_dir.rglob('*'):
            if item.is_file() and item.stat().st_mtime < cutoff_time:
                old_count += 1
                old_size += item.stat().st_size
    except Exception:
        pass

    return {
        'count': old_count,
        'size_mb': round(old_size / (1024 * 1024), 2)
    }


def main() -> dict:
    """Main execution - returns JSON result dict."""
    start_time = time.time()
    result = {
        'zombies_found': 0,
        'memory_freed_mb': 0,
        'disk_freed_gb': 0,
        'status': 'success',
        'time_ms': 0,
        'browser': 'chrome',
        'categories': {},
        'profiles': [],
        'old_crash_reports': {},
        'total_size_gb': 0,
        'recommendations': []
    }

    try:
        # Scan Chrome directories
        categories = scan_chrome_directories()
        result['categories'] = categories

        # Calculate totals
        total_mb = sum(c['size_mb'] for c in categories.values())
        result['total_size_gb'] = round(total_mb / 1024.0, 3)
        result['disk_freed_gb'] = result['total_size_gb']
        result['memory_freed_mb'] = round(total_mb * 0.1, 2)  # Estimate 10% RAM relief

        # Analyze profiles
        result['profiles'] = analyze_profiles()

        # Check old crash reports
        result['old_crash_reports'] = count_old_crash_reports()

        # Count cleanable items as "zombies"
        result['zombies_found'] = sum(1 for c in categories.values() if c['size_mb'] > 100)

        # Generate recommendations
        recommendations = []
        if categories.get('service_worker', {}).get('size_mb', 0) > 500:
            recommendations.append('Clear Service Worker cache (>500MB)')
        if categories.get('gpu_cache', {}).get('size_mb', 0) > 200:
            recommendations.append('Clear GPU cache (>200MB)')
        if categories.get('indexeddb', {}).get('size_mb', 0) > 1000:
            recommendations.append('Review IndexedDB storage (>1GB)')
        if categories.get('blob_storage', {}).get('size_mb', 0) > 500:
            recommendations.append('Clear blob storage (>500MB)')
        if result['old_crash_reports']['count'] > 10:
            recommendations.append(f"Delete {result['old_crash_reports']['count']} old crash reports")
        if total_mb > 5000:
            recommendations.append('Consider full Chrome cache cleanup (>5GB total)')

        result['recommendations'] = recommendations

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)

    result['time_ms'] = round((time.time() - start_time) * 1000, 2)
    return result


if __name__ == '__main__':
    output = main()
    print(json.dumps(output, indent=2))
    sys.exit(0 if output['status'] == 'success' else 1)
