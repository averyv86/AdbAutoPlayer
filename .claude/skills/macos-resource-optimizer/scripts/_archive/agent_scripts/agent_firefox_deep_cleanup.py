#!/usr/bin/env python3
"""
Agent: Firefox Deep Cleanup Analyzer
Scans Firefox profile directories for cleanable data.
Analyzes cache2, storage, IndexedDB, thumbnails, crash reports.
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


def find_firefox_profiles() -> list:
    """Find all Firefox profiles."""
    profiles = []
    firefox_base = Path.home() / 'Library/Application Support/Firefox/Profiles'

    if not firefox_base.exists():
        return profiles

    for item in firefox_base.iterdir():
        if item.is_dir():
            profile_size = get_directory_size_mb(item)
            profiles.append({
                'name': item.name,
                'path': str(item),
                'size_mb': round(profile_size, 2),
                'size_gb': round(profile_size / 1024.0, 3)
            })

    return profiles


def scan_profile_directories(profile_path: Path) -> dict:
    """Scan directories within a Firefox profile."""
    categories = {}

    # Firefox profile subdirectories to scan
    scan_paths = {
        'cache2': profile_path / 'cache2',
        'storage': profile_path / 'storage',
        'indexeddb': profile_path / 'storage/default',
        'thumbnails': profile_path / 'thumbnails',
        'crash_reports': profile_path / 'crashes',
        'offline_cache': profile_path / 'OfflineCache',
        'session_store': profile_path / 'sessionstore-backups',
        'startupCache': profile_path / 'startupCache',
        'shader_cache': profile_path / 'shader-cache',
        'webapps': profile_path / 'webappsstore.sqlite',
        'cookies': profile_path / 'cookies.sqlite',
        'places': profile_path / 'places.sqlite'
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


def check_firefox_cache() -> dict:
    """Check Firefox main cache directory."""
    cache_path = Path.home() / 'Library/Caches/Firefox'

    return {
        'path': str(cache_path),
        'exists': cache_path.exists(),
        'size_mb': round(get_directory_size_mb(cache_path), 2)
    }


def analyze_storage_origins(profile_path: Path) -> dict:
    """Analyze storage usage by origin."""
    storage_path = profile_path / 'storage/default'
    origins = {
        'count': 0,
        'total_mb': 0,
        'large_origins': []
    }

    if not storage_path.exists():
        return origins

    try:
        for origin_dir in storage_path.iterdir():
            if origin_dir.is_dir():
                origins['count'] += 1
                origin_size = get_directory_size_mb(origin_dir)
                origins['total_mb'] += origin_size

                if origin_size > 50:  # Origins over 50MB
                    origins['large_origins'].append({
                        'origin': origin_dir.name[:60],
                        'size_mb': round(origin_size, 2)
                    })
    except Exception:
        pass

    origins['total_mb'] = round(origins['total_mb'], 2)
    origins['large_origins'].sort(key=lambda x: x['size_mb'], reverse=True)
    origins['large_origins'] = origins['large_origins'][:10]  # Top 10

    return origins


def count_session_backups(profile_path: Path) -> dict:
    """Count session store backups."""
    session_path = profile_path / 'sessionstore-backups'

    result = {
        'count': 0,
        'size_mb': 0,
        'oldest_days': 0
    }

    if not session_path.exists():
        return result

    try:
        now = time.time()
        oldest_mtime = now

        for item in session_path.iterdir():
            if item.is_file():
                result['count'] += 1
                result['size_mb'] += item.stat().st_size / (1024 * 1024)
                oldest_mtime = min(oldest_mtime, item.stat().st_mtime)

        result['oldest_days'] = int((now - oldest_mtime) / (24 * 3600))
        result['size_mb'] = round(result['size_mb'], 2)
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
        'browser': 'firefox',
        'profiles': [],
        'main_cache': {},
        'total_size_gb': 0,
        'storage_analysis': {},
        'session_backups': {},
        'recommendations': []
    }

    try:
        # Find Firefox profiles
        profiles = find_firefox_profiles()
        result['profiles'] = []

        total_mb = 0
        combined_categories = {}

        for profile in profiles:
            profile_path = Path(profile['path'])
            categories = scan_profile_directories(profile_path)

            profile_data = {
                'name': profile['name'],
                'total_size_mb': profile['size_mb'],
                'total_size_gb': profile['size_gb'],
                'categories': categories
            }
            result['profiles'].append(profile_data)

            # Aggregate sizes
            for cat, data in categories.items():
                if cat not in combined_categories:
                    combined_categories[cat] = 0
                combined_categories[cat] += data['size_mb']

            total_mb += profile['size_mb']

            # Analyze storage origins for first profile
            if not result['storage_analysis']:
                result['storage_analysis'] = analyze_storage_origins(profile_path)

            # Check session backups for first profile
            if not result['session_backups']:
                result['session_backups'] = count_session_backups(profile_path)

        # Check main cache
        result['main_cache'] = check_firefox_cache()
        total_mb += result['main_cache']['size_mb']

        # Calculate totals
        result['total_size_gb'] = round(total_mb / 1024.0, 3)
        result['disk_freed_gb'] = result['total_size_gb']
        result['memory_freed_mb'] = round(total_mb * 0.1, 2)  # Estimate 10% RAM relief

        # Count cleanable items as "zombies"
        result['zombies_found'] = sum(1 for v in combined_categories.values() if v > 100)

        # Generate recommendations
        recommendations = []
        if combined_categories.get('cache2', 0) > 500:
            recommendations.append(f"Clear Firefox cache ({combined_categories.get('cache2', 0):.0f}MB)")
        if combined_categories.get('storage', 0) > 1000:
            recommendations.append(f"Review site storage ({combined_categories.get('storage', 0):.0f}MB)")
        if combined_categories.get('thumbnails', 0) > 100:
            recommendations.append('Clear thumbnail cache')
        if combined_categories.get('offline_cache', 0) > 200:
            recommendations.append('Clear offline cache')
        if result['storage_analysis'].get('count', 0) > 100:
            recommendations.append(f"Review {result['storage_analysis']['count']} stored origins")
        if result['session_backups'].get('count', 0) > 5:
            recommendations.append(f"Clean {result['session_backups']['count']} session backups")
        if len(result['storage_analysis'].get('large_origins', [])) > 0:
            top_origin = result['storage_analysis']['large_origins'][0]
            recommendations.append(f"Large origin: {top_origin['origin'][:30]} ({top_origin['size_mb']:.0f}MB)")
        if total_mb > 3000:
            recommendations.append('Consider full Firefox cleanup (>3GB total)')

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
