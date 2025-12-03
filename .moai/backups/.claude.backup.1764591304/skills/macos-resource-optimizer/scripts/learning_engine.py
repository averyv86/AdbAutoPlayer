#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Self-Learning Optimization Engine - Adaptive Resource Optimization

Implements claude-flow-inspired learning mechanisms:
- Reflexion Memory: Learn from past optimization results
- Pattern Recognition: Identify recurring resource issues
- Adaptive Thresholds: Learn optimal settings per app
- Success Metrics: Track what works best
- Auto-Consolidation: Build app-specific optimization profiles
- Feedback Loop: Continuous improvement

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


# Learning database location
LEARNING_DB_PATH = Path(__file__).parent.parent / ".moai/memory/optimization-history.json"
PATTERNS_DB_PATH = Path(__file__).parent.parent / ".moai/memory/learned-patterns.json"
PROFILES_DB_PATH = Path(__file__).parent.parent / ".moai/memory/app-profiles.json"


@dataclass
class OptimizationRecord:
    """Record of a single optimization execution."""
    timestamp: str
    category: str  # memory, cpu, disk, network, battery, thermal
    before_metrics: Dict
    after_metrics: Dict
    actions_taken: List[str]
    apps_affected: List[str]
    success: bool
    improvement_percent: float
    execution_time_seconds: float
    user_feedback: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LearnedPattern:
    """A learned optimization pattern."""
    pattern_id: str
    pattern_type: str  # "recurring_issue", "successful_strategy", "app_behavior"
    category: str
    description: str
    frequency: int  # How many times this pattern occurred
    success_rate: float  # 0.0 to 1.0
    avg_improvement: float  # Average improvement percentage
    recommended_action: str
    confidence_score: float  # 0.0 to 1.0
    last_seen: str
    apps_involved: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AppProfile:
    """Learned profile for a specific app."""
    app_name: str
    avg_memory_mb: float
    avg_restart_recovery_mb: float
    avg_restart_time_seconds: float
    restart_success_rate: float
    typical_helper_count: int
    optimization_count: int
    last_optimized: str
    recommended_threshold_mb: float
    is_memory_heavy: bool
    notes: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class LearningEngine:
    """
    Self-learning optimization engine.

    Inspired by claude-flow's reflexion memory and auto-consolidation patterns.
    """

    def __init__(self):
        """Initialize learning engine."""
        self.history_db = self._load_db(LEARNING_DB_PATH, [])
        self.patterns_db = self._load_db(PATTERNS_DB_PATH, [])
        self.profiles_db = self._load_db(PROFILES_DB_PATH, {})

    def _load_db(self, path: Path, default):
        """Load database from file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_db(self, path: Path, data):
        """Save database to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def record_optimization(self, record: OptimizationRecord):
        """
        Record optimization result (Reflexion Memory pattern).

        This implements claude-flow's "learn from past experiences" mechanism.
        """
        self.history_db.append(record.to_dict())
        self._save_db(LEARNING_DB_PATH, self.history_db)

        # Trigger pattern recognition
        self._recognize_patterns()

        # Update app profiles
        self._update_app_profiles(record)

        print(f"✅ 학습 완료: {record.category} 최적화 결과 저장")

    def _recognize_patterns(self):
        """
        Identify patterns from history (Neural Pattern Training).

        This implements claude-flow's "trains neural patterns" mechanism.
        """
        if len(self.history_db) < 3:
            return  # Need at least 3 records to identify patterns

        # Pattern 1: Recurring high-memory apps
        memory_records = [r for r in self.history_db if r.get('category') == 'memory']
        app_frequency = defaultdict(int)
        app_improvements = defaultdict(list)

        for record in memory_records:
            for app in record.get('apps_affected', []):
                app_frequency[app] += 1
                app_improvements[app].append(record.get('improvement_percent', 0))

        # Identify recurring offenders
        for app, freq in app_frequency.items():
            if freq >= 3:  # App optimized 3+ times
                avg_improvement = statistics.mean(app_improvements[app])
                success_count = sum(1 for r in memory_records
                                  if app in r.get('apps_affected', []) and r.get('success', False))
                success_rate = success_count / freq

                pattern = LearnedPattern(
                    pattern_id=f"recurring_memory_{app.lower().replace(' ', '_')}",
                    pattern_type="recurring_issue",
                    category="memory",
                    description=f"{app} repeatedly consumes high memory",
                    frequency=freq,
                    success_rate=success_rate,
                    avg_improvement=avg_improvement,
                    recommended_action=f"Restart {app} when memory usage exceeds learned threshold",
                    confidence_score=min(freq / 10, 1.0),  # Max confidence at 10 occurrences
                    last_seen=datetime.now().isoformat(),
                    apps_involved=[app]
                )

                # Update or add pattern
                self._update_pattern(pattern)

        self._save_db(PATTERNS_DB_PATH, [p for p in self.patterns_db])
        print(f"🧠 패턴 인식 완료: {len(self.patterns_db)}개 패턴 학습됨")

    def _update_pattern(self, new_pattern: LearnedPattern):
        """Update or add a learned pattern."""
        # Find existing pattern
        for i, existing in enumerate(self.patterns_db):
            if existing.get('pattern_id') == new_pattern.pattern_id:
                # Update existing
                self.patterns_db[i] = new_pattern.to_dict()
                return

        # Add new pattern
        self.patterns_db.append(new_pattern.to_dict())

    def _update_app_profiles(self, record: OptimizationRecord):
        """
        Update app-specific profiles (Auto-Consolidation pattern).

        This implements claude-flow's "auto-consolidate successful patterns".
        """
        for app in record.apps_affected:
            if app not in self.profiles_db:
                # Create new profile
                self.profiles_db[app] = AppProfile(
                    app_name=app,
                    avg_memory_mb=0,
                    avg_restart_recovery_mb=0,
                    avg_restart_time_seconds=0,
                    restart_success_rate=0,
                    typical_helper_count=0,
                    optimization_count=0,
                    last_optimized=record.timestamp,
                    recommended_threshold_mb=500,  # Default threshold
                    is_memory_heavy=False,
                    notes=[]
                ).to_dict()

            # Update profile
            profile = self.profiles_db[app]
            profile['optimization_count'] += 1
            profile['last_optimized'] = record.timestamp

            # Update averages (running average)
            n = profile['optimization_count']
            before_mem = record.before_metrics.get('memory_mb', 0)
            after_mem = record.after_metrics.get('memory_mb', 0)
            recovery = before_mem - after_mem

            profile['avg_memory_mb'] = (profile['avg_memory_mb'] * (n-1) + before_mem) / n
            profile['avg_restart_recovery_mb'] = (profile['avg_restart_recovery_mb'] * (n-1) + recovery) / n
            profile['avg_restart_time_seconds'] = (profile['avg_restart_time_seconds'] * (n-1) +
                                                   record.execution_time_seconds) / n

            # Update success rate
            if record.success:
                profile['restart_success_rate'] = (profile['restart_success_rate'] * (n-1) + 1.0) / n
            else:
                profile['restart_success_rate'] = (profile['restart_success_rate'] * (n-1)) / n

            # Adaptive threshold learning
            if profile['avg_memory_mb'] > 1000:  # > 1GB average
                profile['is_memory_heavy'] = True
                profile['recommended_threshold_mb'] = profile['avg_memory_mb'] * 0.8
            else:
                profile['is_memory_heavy'] = False
                profile['recommended_threshold_mb'] = 500

        self._save_db(PROFILES_DB_PATH, self.profiles_db)
        print(f"📊 앱 프로필 업데이트: {len(record.apps_affected)}개 앱")

    def get_recommendations(self, current_metrics: Dict) -> List[Dict]:
        """
        Get AI-powered recommendations based on learned patterns.

        This implements adaptive decision-making based on historical data.
        """
        recommendations = []

        # Check learned patterns
        for pattern_dict in self.patterns_db:
            pattern = LearnedPattern(**pattern_dict)

            if pattern.confidence_score > 0.6:  # High confidence patterns only
                for app in pattern.apps_involved:
                    current_app_mem = current_metrics.get('apps', {}).get(app, {}).get('memory_mb', 0)

                    # Check if app exceeds learned threshold
                    profile = self.profiles_db.get(app, {})
                    threshold = profile.get('recommended_threshold_mb', 500)

                    if current_app_mem > threshold:
                        recommendations.append({
                            'app': app,
                            'action': pattern.recommended_action,
                            'reason': f"Learned pattern: {pattern.description}",
                            'confidence': pattern.confidence_score,
                            'expected_recovery_mb': profile.get('avg_restart_recovery_mb', 0),
                            'pattern_frequency': pattern.frequency,
                            'success_rate': pattern.success_rate
                        })

        return recommendations

    def get_adaptive_thresholds(self) -> Dict[str, float]:
        """
        Get learned optimal thresholds for each app.

        Returns adaptive thresholds based on historical performance.
        """
        thresholds = {}
        for app, profile in self.profiles_db.items():
            thresholds[app] = profile.get('recommended_threshold_mb', 500)
        return thresholds

    def generate_learning_report(self) -> Dict:
        """
        Generate comprehensive learning report.

        This implements claude-flow's session-end summary pattern.
        """
        total_optimizations = len(self.history_db)
        if total_optimizations == 0:
            return {"status": "no_data", "message": "학습 데이터 없음"}

        # Calculate statistics
        successful = sum(1 for r in self.history_db if r.get('success', False))
        success_rate = successful / total_optimizations

        avg_improvement = statistics.mean([r.get('improvement_percent', 0)
                                          for r in self.history_db if r.get('success', False)])

        # Most optimized apps
        app_counts = defaultdict(int)
        for record in self.history_db:
            for app in record.get('apps_affected', []):
                app_counts[app] += 1

        top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Learned patterns summary
        high_confidence_patterns = [p for p in self.patterns_db
                                   if p.get('confidence_score', 0) > 0.7]

        return {
            "total_optimizations": total_optimizations,
            "success_rate": success_rate,
            "avg_improvement_percent": avg_improvement,
            "top_optimized_apps": [{"app": app, "count": count} for app, count in top_apps],
            "learned_patterns_count": len(self.patterns_db),
            "high_confidence_patterns": len(high_confidence_patterns),
            "app_profiles_count": len(self.profiles_db),
            "learning_status": "active" if total_optimizations >= 10 else "learning",
            "recommendation": self._get_learning_recommendation(total_optimizations)
        }

    def _get_learning_recommendation(self, total_optimizations: int) -> str:
        """Get recommendation based on learning progress."""
        if total_optimizations < 5:
            return "더 많은 데이터 수집 필요 (5회 미만)"
        elif total_optimizations < 10:
            return "패턴 학습 중 (10회 미만)"
        elif total_optimizations < 20:
            return "충분한 학습 데이터, 적응형 최적화 활성화"
        else:
            return "고도 학습 완료, AI 기반 자동 최적화 가능"

    def clear_old_records(self, days: int = 30):
        """Clear records older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        self.history_db = [r for r in self.history_db
                          if datetime.fromisoformat(r.get('timestamp', '')) > cutoff]
        self._save_db(LEARNING_DB_PATH, self.history_db)
        print(f"🧹 {days}일 이전 기록 정리 완료")


def main():
    """CLI interface for learning engine."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Self-Learning Optimization Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--record', action='store_true',
                       help='Record optimization result')
    parser.add_argument('--report', action='store_true',
                       help='Generate learning report')
    parser.add_argument('--get-recommendations', action='store_true',
                       help='Get AI-powered recommendations')
    parser.add_argument('--get-thresholds', action='store_true',
                       help='Get adaptive thresholds')
    parser.add_argument('--clear-old', type=int, metavar='DAYS',
                       help='Clear records older than DAYS')

    # Recording parameters
    parser.add_argument('--category', help='Category (memory, cpu, etc.)')
    parser.add_argument('--before', help='Before metrics (JSON)')
    parser.add_argument('--after', help='After metrics (JSON)')
    parser.add_argument('--apps', help='Apps affected (JSON array)')
    parser.add_argument('--actions', help='Actions taken (JSON array)')
    parser.add_argument('--success', type=bool, default=True, help='Success flag')
    parser.add_argument('--improvement', type=float, help='Improvement percentage')
    parser.add_argument('--time', type=float, help='Execution time (seconds)')

    # Recommendation parameters
    parser.add_argument('--current', help='Current metrics (JSON)')

    args = parser.parse_args()

    engine = LearningEngine()

    if args.record:
        # Record optimization
        if not all([args.category, args.before, args.after, args.apps]):
            print("❌ 오류: --record에는 --category, --before, --after, --apps가 필요합니다")
            return 1

        record = OptimizationRecord(
            timestamp=datetime.now().isoformat(),
            category=args.category,
            before_metrics=json.loads(args.before),
            after_metrics=json.loads(args.after),
            actions_taken=json.loads(args.actions) if args.actions else [],
            apps_affected=json.loads(args.apps),
            success=args.success,
            improvement_percent=args.improvement or 0.0,
            execution_time_seconds=args.time or 0.0
        )

        engine.record_optimization(record)
        print(f"✅ 기록 완료: {args.category} 최적화")
        return 0

    elif args.report:
        # Generate report
        report = engine.generate_learning_report()
        print("\n📊 자기 학습 시스템 리포트")
        print("=" * 60)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    elif args.get_recommendations:
        # Get recommendations
        if not args.current:
            print("❌ 오류: --get-recommendations에는 --current가 필요합니다")
            return 1

        current_metrics = json.loads(args.current)
        recommendations = engine.get_recommendations(current_metrics)

        print("\n🎯 AI 기반 권장사항")
        print("=" * 60)
        print(json.dumps(recommendations, indent=2, ensure_ascii=False))
        return 0

    elif args.get_thresholds:
        # Get adaptive thresholds
        thresholds = engine.get_adaptive_thresholds()

        print("\n📏 학습된 적응형 임계값")
        print("=" * 60)
        for app, threshold in sorted(thresholds.items()):
            print(f"{app}: {threshold:.0f} MB")
        return 0

    elif args.clear_old:
        # Clear old records
        engine.clear_old_records(days=args.clear_old)
        return 0

    else:
        # Default: Show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
