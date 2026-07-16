#!/usr/bin/env python3
"""
Build Artifact Cleaner - Remove old build directories and dependencies
Cleans node_modules, target, dist, build, .next, __pycache__ from inactive projects
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime, timedelta
import json


class BuildArtifactCleaner:
    """Clean build artifacts from inactive projects"""

    # Artifact directories to clean
    ARTIFACTS = {
        'node_modules': 'Node.js dependencies',
        'target': 'Rust build artifacts',
        'dist': 'Distribution builds',
        'build': 'Build outputs',
        '.next': 'Next.js build cache',
        '__pycache__': 'Python bytecode',
        '.venv': 'Python virtual environments',
        'venv': 'Python virtual environments',
        'env': 'Python virtual environments',
        '.tox': 'Tox test environments',
        '.pytest_cache': 'Pytest cache',
        'coverage': 'Coverage reports',
        '.turbo': 'Turborepo cache',
        '.parcel-cache': 'Parcel cache',
        '.cache': 'Generic build cache',
    }

    def __init__(self,
                 search_path: Path = None,
                 inactive_days: int = 90,
                 dry_run: bool = True,
                 min_size_mb: int = 100):
        """
        Initialize cleaner

        Args:
            search_path: Root directory to search (default: home)
            inactive_days: Clean projects inactive for this many days
            dry_run: Preview changes without deleting
            min_size_mb: Only clean artifacts larger than this (in MB)
        """
        self.search_path = search_path or Path.home()
        self.inactive_threshold = datetime.now() - timedelta(days=inactive_days)
        self.dry_run = dry_run
        self.min_size_bytes = min_size_mb * 1024 * 1024
        self.results: List[Dict] = []

    def get_dir_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        try:
            result = subprocess.run(
                ['du', '-sk', str(path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
        except Exception:
            return 0

    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_last_modified(self, path: Path) -> datetime:
        """Get last modified time of directory (most recent file)"""
        try:
            # Get most recent modification time in directory
            result = subprocess.run(
                ['find', str(path), '-type', 'f', '-exec', 'stat', '-f', '%m', '{}', ';'],
                capture_output=True,
                text=True,
                timeout=30
            )

            timestamps = [int(t) for t in result.stdout.strip().split('\n') if t]
            if timestamps:
                return datetime.fromtimestamp(max(timestamps))
        except Exception:
            pass

        # Fallback to directory stat
        return datetime.fromtimestamp(path.stat().st_mtime)

    def is_active_project(self, project_dir: Path) -> bool:
        """Check if project has recent activity"""
        last_modified = self.get_last_modified(project_dir)
        return last_modified > self.inactive_threshold

    def find_artifacts(self) -> List[Dict]:
        """Find all build artifacts in search path"""
        artifacts = []

        # Use find to locate artifact directories
        for artifact_name, description in self.ARTIFACTS.items():
            try:
                result = subprocess.run(
                    ['find', str(self.search_path), '-type', 'd', '-name', artifact_name, '-not', '-path', '*/.*'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                paths = [Path(p) for p in result.stdout.strip().split('\n') if p]

                for path in paths:
                    # Skip if in hidden directory (except our search path)
                    if any(part.startswith('.') for part in path.parts[len(self.search_path.parts):]):
                        continue

                    size = self.get_dir_size(path)

                    # Skip small artifacts
                    if size < self.min_size_bytes:
                        continue

                    # Get project directory (parent of artifact)
                    project_dir = path.parent

                    artifacts.append({
                        'artifact_name': artifact_name,
                        'description': description,
                        'path': str(path),
                        'project_dir': str(project_dir),
                        'size': size,
                        'last_modified': self.get_last_modified(project_dir),
                        'is_active': self.is_active_project(project_dir)
                    })

            except Exception as e:
                print(f"⚠️  Error searching for {artifact_name}: {e}", file=sys.stderr)

        return artifacts

    def group_by_project(self, artifacts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group artifacts by project directory"""
        projects = {}

        for artifact in artifacts:
            project_dir = artifact['project_dir']
            if project_dir not in projects:
                projects[project_dir] = []
            projects[project_dir].append(artifact)

        return projects

    def clean_artifacts(self, artifacts: List[Dict]) -> Dict:
        """Clean artifacts and return summary"""
        # Filter to only inactive projects
        inactive_artifacts = [a for a in artifacts if not a['is_active']]

        if not inactive_artifacts:
            return {
                'total_found': len(artifacts),
                'active_projects': len([a for a in artifacts if a['is_active']]),
                'inactive_cleaned': 0,
                'space_recovered': 0,
                'message': 'No inactive artifacts to clean'
            }

        # Group by project
        projects = self.group_by_project(inactive_artifacts)

        total_recovered = 0
        cleaned_count = 0

        for project_dir, project_artifacts in projects.items():
            project_size = sum(a['size'] for a in project_artifacts)

            print(f"\n📦 Project: {project_dir}")
            print(f"   Artifacts: {len(project_artifacts)}")
            print(f"   Total Size: {self.format_size(project_size)}")

            for artifact in project_artifacts:
                if self.dry_run:
                    print(f"   Would delete: {artifact['artifact_name']} ({self.format_size(artifact['size'])})")
                    total_recovered += artifact['size']
                    cleaned_count += 1
                else:
                    try:
                        shutil.rmtree(artifact['path'])
                        print(f"   ✅ Deleted: {artifact['artifact_name']} ({self.format_size(artifact['size'])})")
                        total_recovered += artifact['size']
                        cleaned_count += 1
                    except Exception as e:
                        print(f"   ❌ Failed to delete {artifact['artifact_name']}: {e}")

        return {
            'total_found': len(artifacts),
            'active_projects': len([a for a in artifacts if a['is_active']]),
            'inactive_cleaned': cleaned_count,
            'space_recovered': total_recovered,
            'projects_cleaned': len(projects)
        }

    def analyze_and_clean(self) -> Dict:
        """Full analysis and cleaning workflow"""
        print(f"\n🔍 Searching for build artifacts in: {self.search_path}")
        print(f"   Inactive threshold: {self.inactive_threshold.strftime('%Y-%m-%d')}")
        print(f"   Minimum size: {self.format_size(self.min_size_bytes)}")
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE CLEANING'}")
        print("=" * 60)

        # Find artifacts
        artifacts = self.find_artifacts()

        if not artifacts:
            return {
                'artifacts_found': 0,
                'message': 'No build artifacts found'
            }

        # Analyze by type
        by_type: Dict[str, List[Dict]] = {}
        for artifact in artifacts:
            artifact_name = artifact['artifact_name']
            if artifact_name not in by_type:
                by_type[artifact_name] = []
            by_type[artifact_name].append(artifact)

        print(f"\n📊 Found {len(artifacts)} artifacts across {len(by_type)} types:")
        for artifact_type, items in by_type.items():
            total_size = sum(a['size'] for a in items)
            active_count = len([a for a in items if a['is_active']])
            print(f"   • {artifact_type}: {len(items)} instances ({self.format_size(total_size)}, {active_count} active)")

        # Clean inactive artifacts
        print(f"\n🧹 {'Analyzing' if self.dry_run else 'Cleaning'} inactive projects...")
        summary = self.clean_artifacts(artifacts)

        return {
            'search_path': str(self.search_path),
            'dry_run': self.dry_run,
            'inactive_days': (datetime.now() - self.inactive_threshold).days,
            'artifacts_found': len(artifacts),
            'artifact_types': len(by_type),
            **summary
        }


def main():
    """CLI interface for build artifact cleaning"""
    import argparse

    parser = argparse.ArgumentParser(description='Clean build artifacts from inactive projects')
    parser.add_argument('--path', type=str, help='Root directory to search (default: home)')
    parser.add_argument('--days', type=int, default=90, help='Clean projects inactive for N days (default: 90)')
    parser.add_argument('--min-size', type=int, default=100, help='Minimum artifact size in MB (default: 100)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without deleting')

    args = parser.parse_args()

    search_path = Path(args.path) if args.path else Path.home()

    cleaner = BuildArtifactCleaner(
        search_path=search_path,
        inactive_days=args.days,
        dry_run=args.dry_run,
        min_size_mb=args.min_size
    )

    results = cleaner.analyze_and_clean()

    print(f"\n📊 Summary")
    print("=" * 60)
    print(f"Artifacts Found: {results.get('artifacts_found', 0)}")
    print(f"Active Projects: {results.get('active_projects', 0)}")
    print(f"Inactive Cleaned: {results.get('inactive_cleaned', 0)}")
    print(f"Projects Cleaned: {results.get('projects_cleaned', 0)}")
    print(f"Space Recovered: {cleaner.format_size(results.get('space_recovered', 0))}")

    if args.dry_run:
        print("\n💡 Tip: Run without --dry-run to actually clean artifacts")

    # JSON output
    print(f"\n\nJSON Output:")
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
