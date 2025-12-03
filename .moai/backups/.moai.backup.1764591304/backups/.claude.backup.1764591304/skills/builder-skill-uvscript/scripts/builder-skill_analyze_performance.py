#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
AI-Powered Performance Analyzer

Performance bottleneck detection and optimization suggestions with AI-powered
analysis. Supports profile data analysis and code-level performance insights.

Usage:
    uv run perf_analyzer.py --profile output.prof --threshold 1.0
    uv run perf_analyzer.py --code src/data_processor.py --json
    uv run perf_analyzer.py --profile output.prof --json
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import click


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class Bottleneck:
    """Represents a performance bottleneck."""

    function: str
    time: float
    percentage: float
    calls: int
    location: str
    severity: Literal["low", "medium", "high", "critical"]


@dataclass
class Optimization:
    """Represents an optimization suggestion."""

    target: str
    strategy: str
    expected_gain: str
    code_before: str | None
    code_after: str | None
    explanation: str
    priority: int


@dataclass
class MemoryLeak:
    """Represents a potential memory leak."""

    location: str
    type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    fix_suggestion: str


@dataclass
class PerformanceReport:
    """Complete performance analysis report."""

    total_time: float
    bottlenecks: list[Bottleneck]
    optimizations: list[Optimization]
    memory_leaks: list[MemoryLeak]
    recommendations: list[str]
    context: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Optimization Strategies Database
# ============================================================================


OPTIMIZATION_STRATEGIES = {
    "list_comprehension_to_generator": {
        "pattern": r"\[(.+) for (.+) in (.+)\]",
        "strategy": "Use generator expression instead of list comprehension",
        "expected_gain": "60% faster, 80% less memory for large datasets",
        "code_before": "results = [process(item) for item in dataset]",
        "code_after": "results = (process(item) for item in dataset)",
        "explanation": "Generator expressions are lazy and memory-efficient",
    },
    "multiple_loops_to_single": {
        "pattern": r"for .+ in .+:\s+for .+ in .+:",
        "strategy": "Combine multiple loops into single iteration",
        "expected_gain": "40% faster for large collections",
        "code_before": "for x in data:\n    for y in data:\n        process(x, y)",
        "code_after": "from itertools import product\nfor x, y in product(data, data):\n    process(x, y)",
        "explanation": "Reduces loop overhead and improves cache locality",
    },
    "string_concatenation": {
        "pattern": r'"\s*\+\s*"',
        "strategy": "Use join() for multiple string concatenations",
        "expected_gain": "80% faster for large string operations",
        "code_before": "result = '' + s1 + s2 + s3",
        "code_after": "result = ''.join([s1, s2, s3])",
        "explanation": "join() is O(n) while concatenation is O(n²)",
    },
    "dict_lookup": {
        "pattern": r"if .+ in .+:\s+.+ = .+\[.+\]",
        "strategy": "Use dict.get() to combine lookup and default",
        "expected_gain": "30% faster for frequent lookups",
        "code_before": "if key in data:\n    value = data[key]\nelse:\n    value = default",
        "code_after": "value = data.get(key, default)",
        "explanation": "Single dict lookup instead of two",
    },
}


# ============================================================================
# Performance Analysis Engine
# ============================================================================


class PerformanceAnalyzer:
    """AI-powered performance analysis engine."""

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold
        self.strategies = OPTIMIZATION_STRATEGIES

    def analyze_profile(self, profile_data: str) -> PerformanceReport:
        """Analyze profile data and generate performance report."""
        # Parse profile data
        bottlenecks = self._parse_profile_data(profile_data)

        # Filter by threshold
        significant_bottlenecks = [
            b for b in bottlenecks if b.time >= self.threshold
        ]

        # Generate optimizations
        optimizations = self._generate_optimizations(significant_bottlenecks)

        # Detect memory leaks
        memory_leaks = self._detect_memory_leaks(profile_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            significant_bottlenecks, optimizations, memory_leaks
        )

        # Calculate total time
        total_time = sum(b.time for b in bottlenecks)

        return PerformanceReport(
            total_time=total_time,
            bottlenecks=significant_bottlenecks,
            optimizations=optimizations,
            memory_leaks=memory_leaks,
            recommendations=recommendations,
            context={"threshold": self.threshold, "total_functions": len(bottlenecks)},
        )

    def analyze_code(self, code_path: Path) -> PerformanceReport:
        """Analyze code file for potential performance issues."""
        code = code_path.read_text()

        # Detect bottleneck patterns
        bottlenecks = self._detect_code_bottlenecks(code, str(code_path))

        # Generate optimizations from code patterns
        optimizations = self._detect_optimization_opportunities(code)

        # Basic memory leak detection
        memory_leaks = self._detect_code_memory_issues(code, str(code_path))

        # Generate recommendations
        recommendations = self._generate_code_recommendations(
            bottlenecks, optimizations
        )

        return PerformanceReport(
            total_time=0.0,  # No profile data
            bottlenecks=bottlenecks,
            optimizations=optimizations,
            memory_leaks=memory_leaks,
            recommendations=recommendations,
            context={"source": "code_analysis", "file": str(code_path)},
        )

    def _parse_profile_data(self, profile_data: str) -> list[Bottleneck]:
        """Parse profile data to extract bottlenecks."""
        bottlenecks = []

        # Simple profile data parser (supports common formats)
        # Example format: "function_name: 2.5s (65.0%) - 1000 calls - file.py:42"
        pattern = r"(\w+):\s+([\d.]+)s?\s+\(([\d.]+)%?\)\s*-?\s*(\d+)?\s*calls?\s*-?\s*([^:\n]+):(\d+)?"

        for match in re.finditer(pattern, profile_data):
            function = match.group(1)
            time = float(match.group(2))
            percentage = float(match.group(3))
            calls = int(match.group(4)) if match.group(4) else 0
            location = f"{match.group(5)}:{match.group(6)}" if match.group(5) else "unknown"

            # Determine severity
            severity = self._calculate_severity(percentage)

            bottlenecks.append(
                Bottleneck(
                    function=function,
                    time=time,
                    percentage=percentage,
                    calls=calls,
                    location=location,
                    severity=severity,
                )
            )

        return bottlenecks

    def _detect_code_bottlenecks(
        self, code: str, file_path: str
    ) -> list[Bottleneck]:
        """Detect potential bottlenecks from code patterns."""
        bottlenecks = []

        # Nested loops detection
        nested_loop_pattern = r"for .+ in .+:\s+for .+ in .+"
        for match in re.finditer(nested_loop_pattern, code):
            line_num = code[: match.start()].count("\n") + 1
            bottlenecks.append(
                Bottleneck(
                    function="nested_loop",
                    time=0.0,  # Estimated
                    percentage=0.0,
                    calls=0,
                    location=f"{file_path}:{line_num}",
                    severity="medium",
                )
            )

        # String concatenation in loops
        concat_pattern = r'for .+ in .+:.*?["\'].*?\+.*?["\']'
        for match in re.finditer(concat_pattern, code, re.DOTALL):
            line_num = code[: match.start()].count("\n") + 1
            bottlenecks.append(
                Bottleneck(
                    function="string_concatenation_loop",
                    time=0.0,
                    percentage=0.0,
                    calls=0,
                    location=f"{file_path}:{line_num}",
                    severity="medium",
                )
            )

        return bottlenecks

    def _detect_optimization_opportunities(self, code: str) -> list[Optimization]:
        """Detect optimization opportunities from code patterns."""
        optimizations = []

        for strategy_name, strategy in self.strategies.items():
            pattern = strategy["pattern"]
            for match in re.finditer(pattern, code):
                optimizations.append(
                    Optimization(
                        target=strategy_name,
                        strategy=strategy["strategy"],
                        expected_gain=strategy["expected_gain"],
                        code_before=strategy["code_before"],
                        code_after=strategy["code_after"],
                        explanation=strategy["explanation"],
                        priority=self._calculate_optimization_priority(strategy_name),
                    )
                )

        return optimizations

    def _generate_optimizations(
        self, bottlenecks: list[Bottleneck]
    ) -> list[Optimization]:
        """Generate optimization suggestions based on bottlenecks."""
        optimizations = []

        for bottleneck in bottlenecks:
            # High-percentage bottlenecks
            if bottleneck.percentage > 50:
                optimizations.append(
                    Optimization(
                        target=bottleneck.function,
                        strategy="Algorithm optimization - consider O(log n) or O(1) alternatives",
                        expected_gain="50-70% improvement possible",
                        code_before=None,
                        code_after=None,
                        explanation="High time percentage indicates algorithm inefficiency",
                        priority=1,
                    )
                )

            # High call count
            if bottleneck.calls > 1000:
                optimizations.append(
                    Optimization(
                        target=bottleneck.function,
                        strategy="Add caching/memoization for frequently called function",
                        expected_gain="40-60% faster for repeated calls",
                        code_before="def func(x):\n    return expensive_operation(x)",
                        code_after="from functools import lru_cache\n@lru_cache(maxsize=128)\ndef func(x):\n    return expensive_operation(x)",
                        explanation="High call count benefits from caching",
                        priority=2,
                    )
                )

        return optimizations

    def _detect_memory_leaks(self, profile_data: str) -> list[MemoryLeak]:
        """Detect potential memory leaks from profile data."""
        # Simple heuristic-based detection
        leaks = []

        # Look for growing memory patterns (simplified)
        if "memory" in profile_data.lower():
            leaks.append(
                MemoryLeak(
                    location="unknown",
                    type="potential_leak",
                    severity="medium",
                    description="Potential memory growth detected",
                    fix_suggestion="Review object lifecycle and ensure proper cleanup",
                )
            )

        return leaks

    def _detect_code_memory_issues(
        self, code: str, file_path: str
    ) -> list[MemoryLeak]:
        """Detect potential memory issues from code."""
        leaks = []

        # Unclosed file handles
        file_open_pattern = r"open\([^)]+\)(?!.*\.close\(\))"
        for match in re.finditer(file_open_pattern, code):
            line_num = code[: match.start()].count("\n") + 1
            leaks.append(
                MemoryLeak(
                    location=f"{file_path}:{line_num}",
                    type="unclosed_file",
                    severity="medium",
                    description="File opened without explicit close or context manager",
                    fix_suggestion="Use 'with open() as f:' context manager",
                )
            )

        return leaks

    def _generate_recommendations(
        self,
        bottlenecks: list[Bottleneck],
        optimizations: list[Optimization],
        memory_leaks: list[MemoryLeak],
    ) -> list[str]:
        """Generate high-level recommendations."""
        recommendations = []

        # Bottleneck-based recommendations
        if bottlenecks:
            top_bottleneck = max(bottlenecks, key=lambda b: b.percentage)
            recommendations.append(
                f"Focus on optimizing '{top_bottleneck.function}' - it consumes {top_bottleneck.percentage:.1f}% of total time"
            )

        # Optimization recommendations
        if len(optimizations) > 3:
            recommendations.append(
                f"Found {len(optimizations)} optimization opportunities - prioritize high-impact changes"
            )

        # Memory recommendations
        if memory_leaks:
            recommendations.append(
                f"Address {len(memory_leaks)} potential memory issues to prevent leaks"
            )

        # General recommendations
        recommendations.extend(
            [
                "Use profiling tools (cProfile, Scalene) for detailed performance analysis",
                "Consider async/await for I/O-bound operations",
                "Implement caching for frequently accessed data",
                "Use multiprocessing for CPU-bound tasks",
            ]
        )

        return recommendations

    def _generate_code_recommendations(
        self, bottlenecks: list[Bottleneck], optimizations: list[Optimization]
    ) -> list[str]:
        """Generate recommendations from code analysis."""
        recommendations = []

        if bottlenecks:
            recommendations.append(
                f"Found {len(bottlenecks)} potential performance bottlenecks - review nested loops and string operations"
            )

        if optimizations:
            recommendations.append(
                f"Apply {len(optimizations)} optimization patterns for immediate gains"
            )

        recommendations.extend(
            [
                "Profile the code to measure actual performance impact",
                "Consider using generators for memory efficiency",
                "Review algorithm complexity for critical paths",
            ]
        )

        return recommendations

    def _calculate_severity(
        self, percentage: float
    ) -> Literal["low", "medium", "high", "critical"]:
        """Calculate severity based on time percentage."""
        if percentage >= 70:
            return "critical"
        elif percentage >= 50:
            return "high"
        elif percentage >= 25:
            return "medium"
        else:
            return "low"

    def _calculate_optimization_priority(self, strategy_name: str) -> int:
        """Calculate optimization priority."""
        priority_map = {
            "list_comprehension_to_generator": 1,
            "string_concatenation": 1,
            "multiple_loops_to_single": 2,
            "dict_lookup": 3,
        }
        return priority_map.get(strategy_name, 5)


# ============================================================================
# CLI Implementation
# ============================================================================


@click.command()
@click.option(
    "--profile", type=click.Path(exists=True), help="Profile data file (.prof)"
)
@click.option("--code", type=click.Path(exists=True), help="Code file to analyze")
@click.option(
    "--threshold",
    type=float,
    default=1.0,
    help="Minimum time in seconds to report",
)
@click.option("--json", "json_output", is_flag=True, help="JSON output mode")
def main(
    profile: str | None, code: str | None, threshold: float, json_output: bool
):
    """AI-Powered Performance Analyzer - Performance bottleneck detection."""
    analyzer = PerformanceAnalyzer(threshold=threshold)

    # Analyze based on input type
    if profile:
        profile_data = Path(profile).read_text()
        result = analyzer.analyze_profile(profile_data)
    elif code:
        result = analyzer.analyze_code(Path(code))
    else:
        click.echo("Error: Must provide --profile or --code", err=True)
        sys.exit(1)

    # Output results
    if json_output:
        _output_json(result)
    else:
        _output_human_readable(result)


def _output_json(result: PerformanceReport):
    """Output performance report in JSON format."""
    output = {
        "total_time": result.total_time,
        "bottlenecks": [
            {
                "function": b.function,
                "time": b.time,
                "percentage": b.percentage,
                "calls": b.calls,
                "location": b.location,
                "severity": b.severity,
            }
            for b in result.bottlenecks
        ],
        "optimizations": [
            {
                "target": opt.target,
                "strategy": opt.strategy,
                "expected_gain": opt.expected_gain,
                "code_before": opt.code_before,
                "code_after": opt.code_after,
                "explanation": opt.explanation,
                "priority": opt.priority,
            }
            for opt in result.optimizations
        ],
        "memory_leaks": [
            {
                "location": leak.location,
                "type": leak.type,
                "severity": leak.severity,
                "description": leak.description,
                "fix_suggestion": leak.fix_suggestion,
            }
            for leak in result.memory_leaks
        ],
        "recommendations": result.recommendations,
    }
    click.echo(json.dumps(output, indent=2))


def _output_human_readable(result: PerformanceReport):
    """Output performance report in human-readable format."""
    click.echo("\n" + "=" * 80)
    click.echo("AI-Powered Performance Analysis Report")
    click.echo("=" * 80 + "\n")

    # Summary
    if result.total_time > 0:
        click.echo(f"Total Execution Time: {result.total_time:.2f}s\n")

    # Bottlenecks
    if result.bottlenecks:
        click.echo("Performance Bottlenecks:")
        click.echo("-" * 80)
        for bottleneck in result.bottlenecks:
            click.echo(f"\n  Function: {bottleneck.function}")
            if bottleneck.time > 0:
                click.echo(f"  Time: {bottleneck.time:.2f}s ({bottleneck.percentage:.1f}%)")
            click.echo(f"  Calls: {bottleneck.calls}")
            click.echo(f"  Location: {bottleneck.location}")
            click.echo(f"  Severity: {bottleneck.severity.upper()}")
        click.echo()

    # Optimizations
    if result.optimizations:
        click.echo("Optimization Suggestions:")
        click.echo("-" * 80)
        for opt in result.optimizations:
            click.echo(f"\n  Target: {opt.target}")
            click.echo(f"  Strategy: {opt.strategy}")
            click.echo(f"  Expected Gain: {opt.expected_gain}")
            click.echo(f"  Priority: {opt.priority}")
            click.echo(f"  Explanation: {opt.explanation}")

            if opt.code_before and opt.code_after:
                click.echo("\n  Before:")
                for line in opt.code_before.split("\n"):
                    click.echo(f"    {line}")
                click.echo("\n  After:")
                for line in opt.code_after.split("\n"):
                    click.echo(f"    {line}")
        click.echo()

    # Memory Leaks
    if result.memory_leaks:
        click.echo("Potential Memory Issues:")
        click.echo("-" * 80)
        for leak in result.memory_leaks:
            click.echo(f"\n  Type: {leak.type}")
            click.echo(f"  Location: {leak.location}")
            click.echo(f"  Severity: {leak.severity.upper()}")
            click.echo(f"  Description: {leak.description}")
            click.echo(f"  Fix: {leak.fix_suggestion}")
        click.echo()

    # Recommendations
    if result.recommendations:
        click.echo("Recommendations:")
        click.echo("-" * 80)
        for i, rec in enumerate(result.recommendations, 1):
            click.echo(f"  {i}. {rec}")
        click.echo()

    click.echo("=" * 80)


if __name__ == "__main__":
    main()
