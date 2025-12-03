#!/usr/bin/env python3
"""
Pattern Detector - Classify project activity patterns
Implements activity scoring algorithm and recommends actions
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from enum import Enum


class ActivityLevel(str, Enum):
    ACTIVE = "ACTIVE"
    SEMI_ACTIVE = "SEMI_ACTIVE"
    INACTIVE = "INACTIVE"


class ActionRecommendation(str, Enum):
    KEEP = "KEEP"
    WARN = "WARN"
    ARCHIVE = "ARCHIVE"
    DELETE = "DELETE"


class PatternDetector:
    def __init__(self, project_scan_file: str, git_analysis_file: str):
        self.project_scan_file = Path(project_scan_file)
        self.git_analysis_file = Path(git_analysis_file)
        self.projects: List[Dict] = []
        self.git_metrics: Dict[str, Dict] = {}
        self.classifications: List[Dict] = []

    def load_data(self):
        """Load project scan and git analysis data"""
        # Load project scan
        if not self.project_scan_file.exists():
            print(f"Error: Project scan file not found: {self.project_scan_file}", file=sys.stderr)
            sys.exit(1)

        with open(self.project_scan_file, 'r') as f:
            data = json.load(f)
            self.projects = data.get('projects', [])

        # Load git analysis
        if not self.git_analysis_file.exists():
            print(f"Error: Git analysis file not found: {self.git_analysis_file}", file=sys.stderr)
            sys.exit(1)

        with open(self.git_analysis_file, 'r') as f:
            data = json.load(f)
            metrics = data.get('metrics', [])

            # Index by path for easy lookup
            self.git_metrics = {m['path']: m for m in metrics}

        print(f"Loaded {len(self.projects)} projects and {len(self.git_metrics)} git repos", file=sys.stderr)

    def calculate_file_modification_score(self, days_since_mod: float) -> float:
        """Calculate file modification recency score (0-30 points)"""
        if days_since_mod is None or days_since_mod > 365:
            return 0

        if days_since_mod < 1:
            return 30
        elif days_since_mod < 7:
            return 25
        elif days_since_mod < 30:
            return 20
        elif days_since_mod < 90:
            return 15
        elif days_since_mod < 180:
            return 10
        else:
            return 5

    def calculate_git_activity_score(self, git_metrics: Dict) -> float:
        """Calculate git activity score (0-30 points)"""
        if not git_metrics or not git_metrics.get('is_git_repo', False):
            return 0

        score = 0

        # Days since last commit (0-15 points)
        days_since_last = git_metrics.get('days_since_last_commit')
        if days_since_last is not None:
            if days_since_last < 1:
                score += 15
            elif days_since_last < 7:
                score += 12
            elif days_since_last < 30:
                score += 10
            elif days_since_last < 90:
                score += 7
            elif days_since_last < 180:
                score += 4
            else:
                score += 1

        # Commit frequency (0-15 points)
        freq = git_metrics.get('commit_frequency', {})
        commits_7d = freq.get('7_days', {}).get('commits', 0)
        commits_30d = freq.get('30_days', {}).get('commits', 0)

        if commits_7d >= 5:
            score += 15
        elif commits_7d >= 2:
            score += 12
        elif commits_30d >= 10:
            score += 10
        elif commits_30d >= 5:
            score += 7
        elif commits_30d >= 1:
            score += 5

        return min(score, 30)  # Cap at 30

    def calculate_package_age_score(self, package_ages: Dict) -> float:
        """Calculate package age score (0-20 points)"""
        if not package_ages:
            return 10  # Neutral score for projects without package files

        # Get most recently updated package file
        min_age = min(age['days_old'] for age in package_ages.values())

        if min_age < 7:
            return 20
        elif min_age < 30:
            return 17
        elif min_age < 90:
            return 14
        elif min_age < 180:
            return 10
        elif min_age < 365:
            return 5
        else:
            return 0

    def calculate_running_process_score(self, has_processes: bool) -> float:
        """Calculate running process score (0-20 points)"""
        return 20 if has_processes else 0

    def calculate_activity_score(self, project: Dict, git_metrics: Dict) -> Tuple[float, Dict]:
        """Calculate overall activity score using weighted algorithm"""
        file_stats = project.get('file_stats', {})
        days_since_mod = file_stats.get('days_since_modification')
        package_ages = project.get('package_ages')
        has_processes = project.get('has_running_processes', False)

        # Calculate component scores
        file_mod_score = self.calculate_file_modification_score(days_since_mod)
        git_score = self.calculate_git_activity_score(git_metrics)
        package_score = self.calculate_package_age_score(package_ages)
        process_score = self.calculate_running_process_score(has_processes)

        # Total score (0-100)
        total_score = file_mod_score + git_score + package_score + process_score

        breakdown = {
            'file_modification_score': round(file_mod_score, 2),
            'git_activity_score': round(git_score, 2),
            'package_age_score': round(package_score, 2),
            'running_process_score': round(process_score, 2),
            'total_score': round(total_score, 2)
        }

        return total_score, breakdown

    def classify_activity(self, score: float) -> ActivityLevel:
        """Classify project based on activity score"""
        if score >= 60:
            return ActivityLevel.ACTIVE
        elif score >= 30:
            return ActivityLevel.SEMI_ACTIVE
        else:
            return ActivityLevel.INACTIVE

    def recommend_action(
        self,
        activity_level: ActivityLevel,
        days_since_mod: float,
        days_since_commit: float,
        has_processes: bool
    ) -> ActionRecommendation:
        """Recommend action based on activity analysis"""
        # Always keep if processes are running
        if has_processes:
            return ActionRecommendation.KEEP

        # Active projects
        if activity_level == ActivityLevel.ACTIVE:
            return ActionRecommendation.KEEP

        # Semi-active projects - warn
        if activity_level == ActivityLevel.SEMI_ACTIVE:
            return ActionRecommendation.WARN

        # Inactive projects - archive or delete based on age
        if days_since_mod and days_since_mod > 365:
            return ActionRecommendation.DELETE
        elif days_since_commit and days_since_commit > 180:
            return ActionRecommendation.ARCHIVE
        else:
            return ActionRecommendation.WARN

    def classify_project(self, project: Dict) -> Dict:
        """Classify a single project"""
        project_path = project['path']
        git_metrics = self.git_metrics.get(project_path, {})

        # Calculate activity score
        score, breakdown = self.calculate_activity_score(project, git_metrics)

        # Classify activity level
        activity_level = self.classify_activity(score)

        # Get metrics for recommendation
        days_since_mod = project.get('file_stats', {}).get('days_since_modification')
        days_since_commit = git_metrics.get('days_since_last_commit')
        has_processes = project.get('has_running_processes', False)

        # Recommend action
        action = self.recommend_action(
            activity_level,
            days_since_mod,
            days_since_commit,
            has_processes
        )

        return {
            'path': project_path,
            'name': project['name'],
            'types': project.get('types', []),
            'activity_level': activity_level.value,
            'activity_score': score,
            'score_breakdown': breakdown,
            'recommended_action': action.value,
            'days_since_modification': days_since_mod,
            'days_since_last_commit': days_since_commit,
            'has_running_processes': has_processes,
            'file_count': project.get('file_stats', {}).get('file_count', 0),
            'git_commits_30d': git_metrics.get('commit_frequency', {}).get('30_days', {}).get('commits', 0),
            'classification_timestamp': datetime.now().isoformat()
        }

    def classify_all_projects(self):
        """Classify all projects"""
        print("\nClassifying projects...", file=sys.stderr)

        for project in self.projects:
            classification = self.classify_project(project)
            self.classifications.append(classification)
            print(f"  {project['name']}: {classification['activity_level']} (score: {classification['activity_score']})", file=sys.stderr)

    def generate_archival_list(self, min_days_inactive: int = 90) -> List[Dict]:
        """Generate list of projects recommended for archival"""
        archival_candidates = []

        for classification in self.classifications:
            # Skip if processes are running
            if classification['has_running_processes']:
                continue

            # Check if inactive for minimum period
            days_inactive = classification.get('days_since_modification')
            if days_inactive and days_inactive >= min_days_inactive:
                action = classification['recommended_action']
                if action in [ActionRecommendation.ARCHIVE.value, ActionRecommendation.DELETE.value]:
                    archival_candidates.append({
                        'path': classification['path'],
                        'name': classification['name'],
                        'action': action,
                        'days_inactive': round(days_inactive, 2),
                        'activity_score': classification['activity_score'],
                        'reason': self.get_archival_reason(classification)
                    })

        # Sort by days inactive (descending)
        archival_candidates.sort(key=lambda x: x['days_inactive'], reverse=True)

        return archival_candidates

    def get_archival_reason(self, classification: Dict) -> str:
        """Generate human-readable reason for archival"""
        reasons = []

        days_mod = classification.get('days_since_modification')
        days_commit = classification.get('days_since_last_commit')

        if days_mod and days_mod > 365:
            reasons.append(f"No file modifications in {int(days_mod)} days")

        if days_commit and days_commit > 180:
            reasons.append(f"No git commits in {int(days_commit)} days")

        if classification['git_commits_30d'] == 0:
            reasons.append("No commits in last 30 days")

        if not classification['has_running_processes']:
            reasons.append("No running processes")

        return "; ".join(reasons) if reasons else "Low activity score"

    def get_summary_stats(self) -> Dict:
        """Generate summary statistics"""
        stats = {
            'total_projects': len(self.classifications),
            'by_activity_level': {
                ActivityLevel.ACTIVE.value: 0,
                ActivityLevel.SEMI_ACTIVE.value: 0,
                ActivityLevel.INACTIVE.value: 0
            },
            'by_action': {
                ActionRecommendation.KEEP.value: 0,
                ActionRecommendation.WARN.value: 0,
                ActionRecommendation.ARCHIVE.value: 0,
                ActionRecommendation.DELETE.value: 0
            },
            'avg_activity_score': 0
        }

        total_score = 0

        for classification in self.classifications:
            # Count by activity level
            activity_level = classification['activity_level']
            stats['by_activity_level'][activity_level] += 1

            # Count by action
            action = classification['recommended_action']
            stats['by_action'][action] += 1

            # Sum scores
            total_score += classification['activity_score']

        # Calculate average
        if self.classifications:
            stats['avg_activity_score'] = round(total_score / len(self.classifications), 2)

        return stats

    def export_json(self, output_path: str):
        """Export classification results to JSON"""
        archival_list = self.generate_archival_list(min_days_inactive=90)
        summary_stats = self.get_summary_stats()

        report = {
            'classification_timestamp': datetime.now().isoformat(),
            'summary': summary_stats,
            'classifications': self.classifications,
            'archival_candidates': archival_list,
            'archival_summary': {
                'total_candidates': len(archival_list),
                'for_archive': sum(1 for c in archival_list if c['action'] == ActionRecommendation.ARCHIVE.value),
                'for_deletion': sum(1 for c in archival_list if c['action'] == ActionRecommendation.DELETE.value)
            }
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{'='*60}", file=sys.stderr)
        print("CLASSIFICATION SUMMARY", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Total projects: {summary_stats['total_projects']}", file=sys.stderr)
        print(f"\nActivity Levels:", file=sys.stderr)
        print(f"  ACTIVE: {summary_stats['by_activity_level'][ActivityLevel.ACTIVE.value]}", file=sys.stderr)
        print(f"  SEMI_ACTIVE: {summary_stats['by_activity_level'][ActivityLevel.SEMI_ACTIVE.value]}", file=sys.stderr)
        print(f"  INACTIVE: {summary_stats['by_activity_level'][ActivityLevel.INACTIVE.value]}", file=sys.stderr)
        print(f"\nRecommended Actions:", file=sys.stderr)
        print(f"  KEEP: {summary_stats['by_action'][ActionRecommendation.KEEP.value]}", file=sys.stderr)
        print(f"  WARN: {summary_stats['by_action'][ActionRecommendation.WARN.value]}", file=sys.stderr)
        print(f"  ARCHIVE: {summary_stats['by_action'][ActionRecommendation.ARCHIVE.value]}", file=sys.stderr)
        print(f"  DELETE: {summary_stats['by_action'][ActionRecommendation.DELETE.value]}", file=sys.stderr)
        print(f"\nArchival Candidates: {len(archival_list)}", file=sys.stderr)
        print(f"Average Activity Score: {summary_stats['avg_activity_score']}/100", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nReport exported to: {output_file}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Classify project activity patterns')
    parser.add_argument(
        '--project-scan',
        default='./data/project-scan.json',
        help='Input project scan JSON file'
    )
    parser.add_argument(
        '--git-analysis',
        default='./data/git-analysis.json',
        help='Input git analysis JSON file'
    )
    parser.add_argument(
        '--output',
        default='./data/activity-classification.json',
        help='Output JSON file path'
    )

    args = parser.parse_args()

    detector = PatternDetector(args.project_scan, args.git_analysis)
    detector.load_data()
    detector.classify_all_projects()
    detector.export_json(args.output)


if __name__ == '__main__':
    main()
