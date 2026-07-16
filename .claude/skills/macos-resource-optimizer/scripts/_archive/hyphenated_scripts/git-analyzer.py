#!/usr/bin/env python3
"""
Git Analyzer - Analyze git repository activity
Parses git log for commit history, branch activity, and contributor analysis
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class GitAnalyzer:
    def __init__(self, project_scan_file: str):
        self.project_scan_file = Path(project_scan_file)
        self.projects: List[Dict] = []
        self.git_metrics: List[Dict] = []

    def load_project_scan(self):
        """Load project scan data"""
        if not self.project_scan_file.exists():
            print(f"Error: Project scan file not found: {self.project_scan_file}", file=sys.stderr)
            sys.exit(1)

        with open(self.project_scan_file, 'r') as f:
            data = json.load(f)
            self.projects = data.get('projects', [])

        print(f"Loaded {len(self.projects)} projects from scan", file=sys.stderr)

    def is_git_repo(self, project_path: Path) -> bool:
        """Check if directory is a git repository"""
        return (project_path / '.git').exists()

    def get_commit_history(self, project_path: Path, days: int = 90) -> List[Dict]:
        """Get commit history for the last N days"""
        try:
            # Get commits in JSON format
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            result = subprocess.run(
                [
                    'git', 'log',
                    '--since', since_date,
                    '--pretty=format:%H|%an|%ae|%at|%s',
                    '--no-merges'
                ],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 4)
                if len(parts) < 5:
                    continue

                commit_hash, author, email, timestamp, message = parts
                commits.append({
                    'hash': commit_hash,
                    'author': author,
                    'email': email,
                    'timestamp': int(timestamp),
                    'date': datetime.fromtimestamp(int(timestamp)).isoformat(),
                    'message': message
                })

            return commits

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Warning: Git log failed for {project_path}: {e}", file=sys.stderr)
            return []

    def get_days_since_last_commit(self, project_path: Path) -> Optional[float]:
        """Get days since last commit"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%at'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            last_commit_timestamp = int(result.stdout.strip())
            now = datetime.now().timestamp()
            days = (now - last_commit_timestamp) / 86400

            return round(days, 2)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError) as e:
            print(f"Warning: Could not get last commit for {project_path}: {e}", file=sys.stderr)
            return None

    def get_branch_activity(self, project_path: Path) -> Dict:
        """Analyze branch activity"""
        try:
            # Get all branches with last commit date
            result = subprocess.run(
                ['git', 'for-each-ref', '--sort=-committerdate', 'refs/heads/', '--format=%(refname:short)|%(committerdate:iso)'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {}

            branches = {}
            now = datetime.now()

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 1)
                if len(parts) < 2:
                    continue

                branch_name, last_commit_date = parts
                try:
                    commit_date = datetime.fromisoformat(last_commit_date.replace(' ', 'T').split('+')[0]).replace(tzinfo=None)
                    days_old = (now - commit_date).days

                    branches[branch_name] = {
                        'last_commit': commit_date.isoformat(),
                        'days_old': days_old,
                        'active': days_old < 30
                    }
                except (ValueError, IndexError):
                    continue

            # Get current branch
            current_branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            current_branch = current_branch_result.stdout.strip() if current_branch_result.returncode == 0 else 'unknown'

            return {
                'current_branch': current_branch,
                'branches': branches,
                'total_branches': len(branches),
                'active_branches': sum(1 for b in branches.values() if b['active']),
                'stale_branches': sum(1 for b in branches.values() if not b['active'])
            }

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Warning: Branch analysis failed for {project_path}: {e}", file=sys.stderr)
            return {}

    def analyze_contributors(self, commits: List[Dict]) -> Dict:
        """Analyze contributor activity"""
        if not commits:
            return {}

        contributor_commits = defaultdict(int)
        contributor_emails = {}

        for commit in commits:
            author = commit['author']
            email = commit['email']
            contributor_commits[author] += 1
            contributor_emails[author] = email

        contributors = [
            {
                'name': name,
                'email': contributor_emails[name],
                'commits': count
            }
            for name, count in contributor_commits.items()
        ]

        # Sort by commit count
        contributors.sort(key=lambda x: x['commits'], reverse=True)

        return {
            'total_contributors': len(contributors),
            'contributors': contributors,
            'primary_contributor': contributors[0] if contributors else None
        }

    def analyze_commit_frequency(self, commits: List[Dict]) -> Dict:
        """Analyze commit frequency patterns"""
        if not commits:
            return {}

        # Group commits by time period
        now = datetime.now()
        periods = {
            '7_days': 7,
            '30_days': 30,
            '90_days': 90
        }

        frequency = {}
        for period_name, days in periods.items():
            cutoff = now - timedelta(days=days)
            cutoff_timestamp = cutoff.timestamp()

            period_commits = [c for c in commits if c['timestamp'] >= cutoff_timestamp]
            frequency[period_name] = {
                'commits': len(period_commits),
                'avg_per_day': round(len(period_commits) / days, 2)
            }

        return frequency

    def analyze_project(self, project: Dict) -> Dict:
        """Analyze git activity for a single project"""
        project_path = Path(project['path'])

        if not self.is_git_repo(project_path):
            return {
                'path': str(project_path),
                'name': project['name'],
                'is_git_repo': False
            }

        print(f"Analyzing git repo: {project_path}", file=sys.stderr)

        # Get commit history
        commits_90d = self.get_commit_history(project_path, days=90)

        # Get days since last commit
        days_since_last = self.get_days_since_last_commit(project_path)

        # Analyze branches
        branch_activity = self.get_branch_activity(project_path)

        # Analyze contributors
        contributor_analysis = self.analyze_contributors(commits_90d)

        # Analyze commit frequency
        commit_frequency = self.analyze_commit_frequency(commits_90d)

        return {
            'path': str(project_path),
            'name': project['name'],
            'is_git_repo': True,
            'days_since_last_commit': days_since_last,
            'total_commits_90d': len(commits_90d),
            'commit_frequency': commit_frequency,
            'branch_activity': branch_activity,
            'contributor_analysis': contributor_analysis,
            'analysis_timestamp': datetime.now().isoformat()
        }

    def analyze_all_projects(self):
        """Analyze all projects from scan"""
        for project in self.projects:
            metrics = self.analyze_project(project)
            self.git_metrics.append(metrics)

    def export_json(self, output_path: str):
        """Export git analysis to JSON"""
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_projects': len(self.git_metrics),
            'git_repos': sum(1 for m in self.git_metrics if m.get('is_git_repo', False)),
            'metrics': self.git_metrics
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nGit analysis exported to: {output_file}", file=sys.stderr)
        print(f"Total git repos analyzed: {report['git_repos']}/{report['total_projects']}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze git repository activity')
    parser.add_argument(
        '--input',
        default='./data/project-scan.json',
        help='Input project scan JSON file'
    )
    parser.add_argument(
        '--output',
        default='./data/git-analysis.json',
        help='Output JSON file path'
    )

    args = parser.parse_args()

    analyzer = GitAnalyzer(args.input)
    analyzer.load_project_scan()
    analyzer.analyze_all_projects()
    analyzer.export_json(args.output)


if __name__ == '__main__':
    main()
