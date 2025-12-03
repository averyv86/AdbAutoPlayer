#!/usr/bin/env python3
"""
Project Scanner - Detect and analyze project directories
Scans for projects, checks file modification timestamps, and correlates with running processes
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import subprocess
import sys

class ProjectScanner:
    def __init__(self, scan_paths: List[str], exclude_paths: List[str] = None):
        self.scan_paths = [Path(p).expanduser() for p in scan_paths]
        self.exclude_paths = set([Path(p).expanduser() for p in (exclude_paths or [])])
        self.projects: List[Dict] = []

    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be excluded from scan"""
        path_str = str(path)

        # Skip excluded paths
        for exclude in self.exclude_paths:
            if path_str.startswith(str(exclude)):
                return True

        # Skip common non-project directories
        skip_dirs = {
            'node_modules', '.git', 'dist', 'build', '__pycache__',
            '.venv', 'venv', 'target', '.cache', '.tmp'
        }

        return any(skip in path.parts for skip in skip_dirs)

    def find_git_projects(self) -> List[Path]:
        """Find all directories containing .git folders"""
        projects = []

        for scan_path in self.scan_paths:
            if not scan_path.exists():
                print(f"Warning: Scan path does not exist: {scan_path}", file=sys.stderr)
                continue

            print(f"Scanning {scan_path}...", file=sys.stderr)

            for root, dirs, files in os.walk(scan_path):
                root_path = Path(root)

                # Skip excluded paths
                if self.should_skip_path(root_path):
                    dirs.clear()  # Don't recurse into this directory
                    continue

                # Found a git project
                if '.git' in dirs:
                    projects.append(root_path)
                    # Don't recurse into nested git repos
                    dirs.clear()

        return projects

    def get_file_stats(self, project_path: Path) -> Dict:
        """Get file modification statistics for a project"""
        now = time.time()
        file_count = 0
        most_recent = 0
        oldest = now

        # Track file types
        extensions = {}

        for root, dirs, files in os.walk(project_path):
            # Skip common build/cache directories
            dirs[:] = [d for d in dirs if d not in {
                'node_modules', '.git', 'dist', 'build', '__pycache__',
                '.venv', 'venv', 'target', '.cache', '.tmp'
            }]

            for file in files:
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    mtime = stat.st_mtime

                    file_count += 1
                    most_recent = max(most_recent, mtime)
                    oldest = min(oldest, mtime)

                    # Track extensions
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1

                except (OSError, PermissionError):
                    continue

        return {
            'file_count': file_count,
            'most_recent_modification': datetime.fromtimestamp(most_recent).isoformat() if most_recent > 0 else None,
            'oldest_file': datetime.fromtimestamp(oldest).isoformat() if oldest < now else None,
            'days_since_modification': (now - most_recent) / 86400 if most_recent > 0 else 999999,
            'file_types': extensions
        }

    def detect_project_type(self, project_path: Path) -> List[str]:
        """Detect project type based on manifest files"""
        types = []

        manifest_files = {
            'package.json': 'JavaScript/Node.js',
            'requirements.txt': 'Python',
            'setup.py': 'Python',
            'pyproject.toml': 'Python',
            'Cargo.toml': 'Rust',
            'go.mod': 'Go',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'Gemfile': 'Ruby',
            'composer.json': 'PHP',
            'Makefile': 'C/C++/Make'
        }

        for manifest, lang in manifest_files.items():
            if (project_path / manifest).exists():
                types.append(lang)

        return types or ['Unknown']

    def get_package_age(self, project_path: Path) -> Optional[Dict]:
        """Get age of package manifest files"""
        manifest_files = [
            'package.json',
            'requirements.txt',
            'Cargo.toml',
            'go.mod',
            'pyproject.toml'
        ]

        ages = {}
        now = time.time()

        for manifest in manifest_files:
            manifest_path = project_path / manifest
            if manifest_path.exists():
                try:
                    stat = manifest_path.stat()
                    days_old = (now - stat.st_mtime) / 86400
                    ages[manifest] = {
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'days_old': round(days_old, 2)
                    }
                except (OSError, PermissionError):
                    continue

        return ages if ages else None

    def get_running_processes(self) -> Dict[str, List[Dict]]:
        """Get running processes grouped by working directory"""
        processes_by_dir = {}

        try:
            # Use ps to get process info with working directory
            result = subprocess.run(
                ['ps', 'axo', 'pid,command,lstart'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return processes_by_dir

            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.strip().split(None, 2)
                if len(parts) < 2:
                    continue

                pid, command = parts[0], parts[1]

                # Try to get working directory for this PID
                try:
                    lsof_result = subprocess.run(
                        ['lsof', '-a', '-p', pid, '-d', 'cwd', '-Fn'],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )

                    for lsof_line in lsof_result.stdout.strip().split('\n'):
                        if lsof_line.startswith('n'):
                            cwd = lsof_line[1:]
                            if cwd not in processes_by_dir:
                                processes_by_dir[cwd] = []

                            processes_by_dir[cwd].append({
                                'pid': int(pid),
                                'command': command
                            })
                            break
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Warning: Could not get process info: {e}", file=sys.stderr)

        return processes_by_dir

    def correlate_processes(self, project_path: Path, processes_by_dir: Dict) -> List[Dict]:
        """Find processes running in this project directory"""
        project_str = str(project_path)
        related_processes = []

        for cwd, processes in processes_by_dir.items():
            if cwd.startswith(project_str):
                related_processes.extend(processes)

        return related_processes

    def scan_projects(self) -> List[Dict]:
        """Scan all projects and gather activity data"""
        git_projects = self.find_git_projects()
        processes_by_dir = self.get_running_processes()

        print(f"\nFound {len(git_projects)} git projects", file=sys.stderr)

        for project_path in git_projects:
            print(f"Analyzing {project_path}...", file=sys.stderr)

            file_stats = self.get_file_stats(project_path)
            project_types = self.detect_project_type(project_path)
            package_ages = self.get_package_age(project_path)
            related_processes = self.correlate_processes(project_path, processes_by_dir)

            project_data = {
                'path': str(project_path),
                'name': project_path.name,
                'types': project_types,
                'file_stats': file_stats,
                'package_ages': package_ages,
                'running_processes': related_processes,
                'has_running_processes': len(related_processes) > 0,
                'scan_timestamp': datetime.now().isoformat()
            }

            self.projects.append(project_data)

        return self.projects

    def export_json(self, output_path: str):
        """Export scan results to JSON"""
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'scan_paths': [str(p) for p in self.scan_paths],
            'projects_found': len(self.projects),
            'projects': self.projects
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReport exported to: {output_file}", file=sys.stderr)
        print(f"Total projects scanned: {len(self.projects)}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Scan for projects and analyze activity')
    parser.add_argument(
        '--scan-paths',
        nargs='+',
        default=['~/Projects', '~/Documents', '~/Desktop'],
        help='Paths to scan for projects'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=[],
        help='Paths to exclude from scan'
    )
    parser.add_argument(
        '--output',
        default='./data/project-scan.json',
        help='Output JSON file path'
    )

    args = parser.parse_args()

    scanner = ProjectScanner(args.scan_paths, args.exclude)
    scanner.scan_projects()
    scanner.export_json(args.output)


if __name__ == '__main__':
    main()
