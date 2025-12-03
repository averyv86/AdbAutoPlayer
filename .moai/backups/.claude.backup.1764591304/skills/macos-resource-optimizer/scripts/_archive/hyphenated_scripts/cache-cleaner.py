#!/usr/bin/env python3
"""
Cache Cleaner - Developer cache cleanup for NPM, Pip, Cargo, Browser, VS Code
Intelligently cleans developer caches with size reporting and recovery estimates
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import json


class CacheAnalyzer:
    """Analyze and clean various developer caches"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.home = Path.home()
        self.results: List[Dict] = []

    def get_dir_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        if not path.exists():
            return 0

        try:
            # Use du for accurate size calculation
            result = subprocess.run(
                ['du', '-sk', str(path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            # du returns size in KB
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        except Exception:
            # Fallback to Python calculation
            total = 0
            try:
                for entry in path.rglob('*'):
                    if entry.is_file():
                        total += entry.stat().st_size
            except Exception:
                pass
            return total

    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def clean_npm_cache(self) -> Dict:
        """Clean NPM cache"""
        cache_path = self.home / '.npm'

        if not cache_path.exists():
            return {
                'name': 'NPM Cache',
                'path': str(cache_path),
                'exists': False,
                'size': 0,
                'cleaned': False,
                'message': 'NPM cache directory not found'
            }

        initial_size = self.get_dir_size(cache_path)

        if self.dry_run:
            return {
                'name': 'NPM Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'message': f'Would clean {self.format_size(initial_size)} (dry-run)'
            }

        try:
            # Use npm cache clean --force
            subprocess.run(
                ['npm', 'cache', 'clean', '--force'],
                capture_output=True,
                timeout=60
            )

            final_size = self.get_dir_size(cache_path)
            recovered = initial_size - final_size

            return {
                'name': 'NPM Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': True,
                'recovered': recovered,
                'message': f'Cleaned {self.format_size(recovered)}'
            }
        except Exception as e:
            return {
                'name': 'NPM Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'error': str(e)
            }

    def clean_pip_cache(self) -> Dict:
        """Clean Pip cache"""
        cache_path = self.home / '.cache' / 'pip'

        if not cache_path.exists():
            return {
                'name': 'Pip Cache',
                'path': str(cache_path),
                'exists': False,
                'size': 0,
                'cleaned': False,
                'message': 'Pip cache directory not found'
            }

        initial_size = self.get_dir_size(cache_path)

        if self.dry_run:
            return {
                'name': 'Pip Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'message': f'Would clean {self.format_size(initial_size)} (dry-run)'
            }

        try:
            # Use pip cache purge
            subprocess.run(
                ['pip', 'cache', 'purge'],
                capture_output=True,
                timeout=60
            )

            final_size = self.get_dir_size(cache_path)
            recovered = initial_size - final_size

            return {
                'name': 'Pip Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': True,
                'recovered': recovered,
                'message': f'Cleaned {self.format_size(recovered)}'
            }
        except Exception as e:
            return {
                'name': 'Pip Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'error': str(e)
            }

    def clean_cargo_cache(self) -> Dict:
        """Clean Cargo cache"""
        cache_path = self.home / '.cargo' / 'registry'

        if not cache_path.exists():
            return {
                'name': 'Cargo Cache',
                'path': str(cache_path),
                'exists': False,
                'size': 0,
                'cleaned': False,
                'message': 'Cargo cache directory not found'
            }

        initial_size = self.get_dir_size(cache_path)

        if self.dry_run:
            return {
                'name': 'Cargo Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'message': f'Would clean {self.format_size(initial_size)} (dry-run)'
            }

        try:
            # Remove old downloads (keep index)
            downloads_path = cache_path / 'cache'
            if downloads_path.exists():
                shutil.rmtree(downloads_path)

            final_size = self.get_dir_size(cache_path)
            recovered = initial_size - final_size

            return {
                'name': 'Cargo Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': True,
                'recovered': recovered,
                'message': f'Cleaned {self.format_size(recovered)}'
            }
        except Exception as e:
            return {
                'name': 'Cargo Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'error': str(e)
            }

    def clean_browser_caches(self) -> List[Dict]:
        """Clean browser caches (Safari, Chrome, Firefox)"""
        results = []

        browser_caches = {
            'Safari': self.home / 'Library' / 'Caches' / 'com.apple.Safari',
            'Chrome': self.home / 'Library' / 'Caches' / 'Google' / 'Chrome',
            'Firefox': self.home / 'Library' / 'Caches' / 'Firefox',
        }

        for browser, cache_path in browser_caches.items():
            if not cache_path.exists():
                results.append({
                    'name': f'{browser} Cache',
                    'path': str(cache_path),
                    'exists': False,
                    'size': 0,
                    'cleaned': False,
                    'message': f'{browser} cache not found'
                })
                continue

            initial_size = self.get_dir_size(cache_path)

            if self.dry_run:
                results.append({
                    'name': f'{browser} Cache',
                    'path': str(cache_path),
                    'exists': True,
                    'size': initial_size,
                    'cleaned': False,
                    'message': f'Would clean {self.format_size(initial_size)} (dry-run)'
                })
                continue

            try:
                shutil.rmtree(cache_path)
                cache_path.mkdir(parents=True, exist_ok=True)

                results.append({
                    'name': f'{browser} Cache',
                    'path': str(cache_path),
                    'exists': True,
                    'size': initial_size,
                    'cleaned': True,
                    'recovered': initial_size,
                    'message': f'Cleaned {self.format_size(initial_size)}'
                })
            except Exception as e:
                results.append({
                    'name': f'{browser} Cache',
                    'path': str(cache_path),
                    'exists': True,
                    'size': initial_size,
                    'cleaned': False,
                    'error': str(e)
                })

        return results

    def clean_vscode_cache(self) -> Dict:
        """Clean VS Code cache"""
        cache_path = self.home / 'Library' / 'Application Support' / 'Code' / 'Cache'

        if not cache_path.exists():
            return {
                'name': 'VS Code Cache',
                'path': str(cache_path),
                'exists': False,
                'size': 0,
                'cleaned': False,
                'message': 'VS Code cache not found'
            }

        initial_size = self.get_dir_size(cache_path)

        if self.dry_run:
            return {
                'name': 'VS Code Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'message': f'Would clean {self.format_size(initial_size)} (dry-run)'
            }

        try:
            shutil.rmtree(cache_path)
            cache_path.mkdir(parents=True, exist_ok=True)

            return {
                'name': 'VS Code Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': True,
                'recovered': initial_size,
                'message': f'Cleaned {self.format_size(initial_size)}'
            }
        except Exception as e:
            return {
                'name': 'VS Code Cache',
                'path': str(cache_path),
                'exists': True,
                'size': initial_size,
                'cleaned': False,
                'error': str(e)
            }

    def clean_all(self) -> Dict:
        """Clean all caches and return summary"""
        self.results = []

        print("🧹 Analyzing caches..." if self.dry_run else "🧹 Cleaning caches...")

        # Clean each cache type
        self.results.append(self.clean_npm_cache())
        self.results.append(self.clean_pip_cache())
        self.results.append(self.clean_cargo_cache())
        self.results.extend(self.clean_browser_caches())
        self.results.append(self.clean_vscode_cache())

        # Calculate totals
        total_size = sum(r['size'] for r in self.results)
        total_recovered = sum(r.get('recovered', 0) for r in self.results)

        return {
            'dry_run': self.dry_run,
            'total_caches': len(self.results),
            'total_size': total_size,
            'total_recovered': total_recovered,
            'caches': self.results
        }


def main():
    """CLI interface for cache cleaning"""
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: cache-cleaner.py [OPTIONS]")
        print("\nOptions:")
        print("  --dry-run, -n    Show what would be cleaned without actually cleaning")
        print("  --help, -h       Show this help message")
        print("\nCaches cleaned:")
        print("  • NPM cache (~/.npm)")
        print("  • Pip cache (~/.cache/pip)")
        print("  • Cargo cache (~/.cargo/registry)")
        print("  • Browser caches (Safari, Chrome, Firefox)")
        print("  • VS Code cache")
        sys.exit(0)

    analyzer = CacheAnalyzer(dry_run=dry_run)

    print("\n🗑️  Cache Cleaner" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    results = analyzer.clean_all()

    print(f"\n📊 Summary")
    print("=" * 60)
    print(f"Total Caches: {results['total_caches']}")
    print(f"Total Size: {analyzer.format_size(results['total_size'])}")

    if dry_run:
        print(f"Potential Recovery: {analyzer.format_size(results['total_size'])}")
    else:
        print(f"Space Recovered: {analyzer.format_size(results['total_recovered'])}")

    print(f"\n📋 Details")
    print("=" * 60)
    for cache in results['caches']:
        status = "✅" if cache['cleaned'] else ("❌" if 'error' in cache else "⚠️")
        print(f"\n{status} {cache['name']}")
        print(f"   Path: {cache['path']}")
        print(f"   Size: {analyzer.format_size(cache['size'])}")
        if 'recovered' in cache:
            print(f"   Recovered: {analyzer.format_size(cache['recovered'])}")
        if 'message' in cache:
            print(f"   {cache['message']}")
        if 'error' in cache:
            print(f"   Error: {cache['error']}")

    # JSON output
    print(f"\n\nJSON Output:")
    print(json.dumps(results, indent=2))

    if dry_run:
        print("\n💡 Tip: Run without --dry-run to actually clean caches")


if __name__ == '__main__':
    main()
