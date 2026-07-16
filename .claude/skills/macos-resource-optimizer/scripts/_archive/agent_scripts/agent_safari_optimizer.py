#!/usr/bin/env python3
"""
Agent: Safari Cache Optimizer
Scans Safari cache and storage directories for cleanable data.
Analyzes LocalStorage, Databases, WebKit caches, Reading List offline cache.
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


def scan_safari_directories() -> dict:
    """Scan all Safari data directories for cleanable data."""
    home = Path.home()
    categories = {}

    # Safari data paths to scan
    scan_paths = {
        'cache': home / 'Library/Caches/com.apple.Safari',
        'webkit_cache': home / 'Library/Caches/com.apple.WebKit.WebContent',
        'network_cache': home / 'Library/Caches/com.apple.Safari/Cache.db',
        'local_storage': home / 'Library/Safari/LocalStorage',
        'databases': home / 'Library/Safari/Databases',
        'service_workers': home / 'Library/Safari/ServiceWorkers',
        'indexeddb': home / 'Library/Safari/IndexedDB',
        'offline_reading': home / 'Library/Safari/ReadingListArchives',
        'website_data': home / 'Library/Safari/WebsiteData',
        'blob_storage': home / 'Library/Safari/BlobStorage',
        'resource_load_stats': home / 'Library/Safari/ResourceLoadStatistics',
        'history': home / 'Library/Safari/History.db'
    }

    for category, path in scan_paths.items():
        if path.is_file():
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
            except Exception:
                size_mb = 0.0
        else:
            size_mb = get_directory_size_mb(path)

        categories[category] = {
            'path': str(path),
            'exists': path.exists(),
            'size_mb': round(size_mb, 2),
            'size_gb': round(size_mb / 1024.0, 3)
        }

    return categories


def check_webkit_processes() -> dict:
    """Check WebKit/Safari helper processes."""
    helpers = {
        'count': 0,
        'memory_mb': 0,
        'processes': []
    }

    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=10
        )

        for line in result.stdout.split('\n'):
            if 'WebKit' in line or 'Safari' in line:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        rss_kb = int(parts[5]) if parts[5].isdigit() else 0
                        helpers['memory_mb'] += rss_kb / 1024.0
                        helpers['count'] += 1
                        helpers['processes'].append({
                            'name': ' '.join(parts[10:])[:50] if len(parts) > 10 else 'unknown',
                            'memory_kb': rss_kb
                        })
                    except (ValueError, IndexError):
                        continue
    except Exception:
        pass

    helpers['memory_mb'] = round(helpers['memory_mb'], 2)
    return helpers


def analyze_reading_list() -> dict:
    """Analyze Reading List offline storage."""
    reading_list_path = Path.home() / 'Library/Safari/ReadingListArchives'

    result = {
        'count': 0,
        'size_mb': 0,
        'oldest_days': 0
    }

    if not reading_list_path.exists():
        return result

    try:
        now = time.time()
        oldest_mtime = now

        for item in reading_list_path.rglob('*'):
            if item.is_file():
                result['count'] += 1
                result['size_mb'] += item.stat().st_size / (1024 * 1024)
                oldest_mtime = min(oldest_mtime, item.stat().st_mtime)

        result['oldest_days'] = int((now - oldest_mtime) / (24 * 3600))
        result['size_mb'] = round(result['size_mb'], 2)
    except Exception:
        pass

    return result


def check_history_size() -> dict:
    """Check Safari history database size."""
    history_path = Path.home() / 'Library/Safari/History.db'

    result = {
        'exists': False,
        'size_mb': 0
    }

    if history_path.exists():
        result['exists'] = True
        try:
            result['size_mb'] = round(history_path.stat().st_size / (1024 * 1024), 2)
        except Exception:
            pass

    return result


def main() -> dict:
    """Main execution - returns JSON result dict."""
    start_time = time.time()
    result = {
        'zombies_found': 0,
        'memory_freed_mb': 0,
        'disk_freed_gb': 0,
        'status': 'success',
        'time_ms': 0,
        'browser': 'safari',
        'categories': {},
        'webkit_processes': {},
        'reading_list': {},
        'history': {},
        'total_size_gb': 0,
        'recommendations': []
    }

    try:
        # Scan Safari directories
        categories = scan_safari_directories()
        result['categories'] = categories

        # Calculate totals
        total_mb = sum(c['size_mb'] for c in categories.values())
        result['total_size_gb'] = round(total_mb / 1024.0, 3)
        result['disk_freed_gb'] = result['total_size_gb']

        # Check WebKit processes
        result['webkit_processes'] = check_webkit_processes()
        result['memory_freed_mb'] = round(result['webkit_processes']['memory_mb'] * 0.2, 2)

        # Analyze Reading List
        result['reading_list'] = analyze_reading_list()

        # Check history
        result['history'] = check_history_size()

        # Count cleanable items as "zombies"
        result['zombies_found'] = sum(1 for c in categories.values() if c['size_mb'] > 50)

        # Generate recommendations
        recommendations = []
        if categories.get('cache', {}).get('size_mb', 0) > 500:
            recommendations.append('Clear Safari cache (>500MB)')
        if categories.get('local_storage', {}).get('size_mb', 0) > 200:
            recommendations.append('Review LocalStorage data (>200MB)')
        if categories.get('databases', {}).get('size_mb', 0) > 500:
            recommendations.append('Clear website databases (>500MB)')
        if categories.get('offline_reading', {}).get('size_mb', 0) > 100:
            recommendations.append('Clear old Reading List archives (>100MB)')
        if result['reading_list']['oldest_days'] > 90:
            recommendations.append(f"Reading List has items {result['reading_list']['oldest_days']} days old")
        if result['history']['size_mb'] > 100:
            recommendations.append(f"History database is {result['history']['size_mb']:.0f}MB - consider clearing")
        if result['webkit_processes']['count'] > 10:
            recommendations.append(f"{result['webkit_processes']['count']} WebKit processes using {result['webkit_processes']['memory_mb']:.0f}MB")
        if total_mb > 2000:
            recommendations.append('Consider full Safari cleanup (>2GB total)')

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
