#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
# ]
# ///

"""
Parallel System Resource Analysis Orchestrator

Executes all 6 category analyzers concurrently and aggregates results
into comprehensive system health assessment.

Features:
- Async parallel execution of all analyzers
- Result aggregation and health score calculation
- Performance metrics tracking
- Graceful error handling
- Configurable thresholds per category

Exit codes:
- 0: All systems healthy
- 1: Warning level issues detected
- 2: Critical issues detected
- 3: Execution error
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

import click

# Embedded constants
SCRIPTS_DIR = Path(__file__).parent.resolve()

CATEGORY_SCRIPTS = {
    "cpu": SCRIPTS_DIR / "analyze_cpu.py",
    "memory": SCRIPTS_DIR / "analyze_memory.py",
    "disk": SCRIPTS_DIR / "analyze_disk.py",
    "network": SCRIPTS_DIR / "analyze_network.py",
    "battery": SCRIPTS_DIR / "analyze_battery.py",
    "thermal": SCRIPTS_DIR / "analyze_thermal.py",
}


class ParallelAnalyzer:
    """Embedded parallel orchestration engine"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}
        self.errors = []
        self.execution_times = {}

    async def run_category_script(
        self,
        category: str,
        script_path: Path,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a single category script with asyncio.

        Args:
            category: Category name (cpu, memory, etc.)
            script_path: Path to analyzer script
            threshold: Optional threshold override

        Returns:
            Analysis result with execution metadata
        """
        cmd = ["uv", "run", str(script_path), "--json"]
        if threshold is not None:
            cmd.extend(["--threshold", str(threshold)])

        start_time = time.time()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            duration = time.time() - start_time

            if proc.returncode in (0, 1, 2):
                # Success (0), warning (1), or critical (2)
                result = json.loads(stdout.decode())
                result["execution_time"] = duration
                result["exit_code"] = proc.returncode
                return result
            else:
                # Error (3 or other)
                error_msg = stderr.decode() if stderr else "Unknown error"
                return {
                    "category": category,
                    "status": "error",
                    "error": error_msg,
                    "execution_time": duration,
                    "exit_code": proc.returncode
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "category": category,
                "status": "error",
                "error": str(e),
                "execution_time": duration,
                "exit_code": 3
            }

    async def analyze_all(
        self,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Run all category analyzers in parallel.

        Args:
            thresholds: Optional per-category threshold overrides

        Returns:
            Aggregated analysis results
        """
        if thresholds is None:
            thresholds = {}

        # Create tasks for parallel execution
        tasks = [
            self.run_category_script(category, script_path, thresholds.get(category))
            for category, script_path in CATEGORY_SCRIPTS.items()
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        categories = {}
        errors = []
        total_duration = 0.0

        for i, result in enumerate(results):
            category = list(CATEGORY_SCRIPTS.keys())[i]

            if isinstance(result, Exception):
                errors.append({
                    "category": category,
                    "error": str(result)
                })
                continue

            categories[category] = result
            total_duration += result.get("execution_time", 0.0)

            # Track errors from script execution
            if result.get("status") == "error":
                errors.append({
                    "category": category,
                    "error": result.get("error", "Unknown error")
                })

        # Calculate overall health
        overall_status = self._calculate_overall_status(categories)
        risk_level = self._calculate_risk_level(categories)
        health_score = self._calculate_health_score(categories)

        return {
            "timestamp": datetime.now().isoformat(),
            "categories": categories,
            "overall": {
                "status": overall_status,
                "risk_level": risk_level,
                "health_score": health_score,
                "errors": errors,
                "successful_categories": len([c for c in categories.values() if c.get("status") != "error"]),
                "total_categories": len(CATEGORY_SCRIPTS)
            },
            "performance": {
                "total_duration": round(total_duration, 3),
                "average_duration": round(total_duration / len(categories) if categories else 0.0, 3),
                "parallelization": f"{len(CATEGORY_SCRIPTS)}x concurrent",
                "categories_per_second": round(len(categories) / total_duration if total_duration > 0 else 0, 2)
            }
        }

    def _calculate_overall_status(self, categories: Dict[str, Any]) -> str:
        """
        Aggregate status across categories.

        Priority: critical > warning > healthy > unknown
        """
        statuses = []
        for cat_data in categories.values():
            analysis = cat_data.get("analysis", {})
            status = analysis.get("status", "unknown")
            statuses.append(status)

        if any(s == "critical" for s in statuses):
            return "critical"
        elif any(s == "warning" for s in statuses):
            return "warning"
        elif all(s == "healthy" for s in statuses):
            return "healthy"
        else:
            return "unknown"

    def _calculate_risk_level(self, categories: Dict[str, Any]) -> str:
        """
        Aggregate risk level across categories.

        Priority: critical > high > medium > low > unknown
        """
        risk_levels = []
        for cat_data in categories.values():
            analysis = cat_data.get("analysis", {})
            risk = analysis.get("risk_level", "unknown")
            risk_levels.append(risk)

        if any(r == "critical" for r in risk_levels):
            return "critical"
        elif any(r == "high" for r in risk_levels):
            return "high"
        elif any(r == "medium" for r in risk_levels):
            return "medium"
        elif all(r == "low" for r in risk_levels):
            return "low"
        else:
            return "unknown"

    def _calculate_health_score(self, categories: Dict[str, Any]) -> float:
        """
        Calculate overall system health score (0-100).

        Weights by category:
        - CPU: 20%
        - Memory: 20%
        - Disk: 15%
        - Network: 15%
        - Battery: 15%
        - Thermal: 15%
        """
        weights = {
            "cpu": 0.20,
            "memory": 0.20,
            "disk": 0.15,
            "network": 0.15,
            "battery": 0.15,
            "thermal": 0.15
        }

        weighted_score = 0.0
        total_weight = 0.0

        for category, weight in weights.items():
            cat_data = categories.get(category, {})
            analysis = cat_data.get("analysis", {})

            # Convert status to score
            status = analysis.get("status", "unknown")
            if status == "healthy":
                score = 100.0
            elif status == "warning":
                score = 50.0
            elif status == "critical":
                score = 0.0
            else:
                continue  # Skip unknown statuses

            weighted_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_score / total_weight, 1)


def format_human_readable(result: Dict[str, Any], verbose: bool) -> str:
    """Format analysis results for human consumption"""
    lines = []

    lines.append("\n📊 System Resource Analysis (Parallel)")
    lines.append("=" * 70)

    overall = result["overall"]
    perf = result["performance"]

    # Status emoji mapping
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "❌",
        "unknown": "❓",
        "error": "🔥"
    }

    # Overall status
    status = overall["status"]
    lines.append(f"\nOverall Status: {status_emoji.get(status, '❓')} {status.upper()}")
    lines.append(f"Risk Level: {overall['risk_level'].upper()}")
    lines.append(f"Health Score: {overall['health_score']}/100")
    lines.append(f"Successful Checks: {overall['successful_categories']}/{overall['total_categories']}")

    # Performance metrics
    lines.append(f"\n⚡ Performance:")
    lines.append(f"  Total Time: {perf['total_duration']}s")
    lines.append(f"  Average Time: {perf['average_duration']}s per category")
    lines.append(f"  Parallelization: {perf['parallelization']}")
    lines.append(f"  Throughput: {perf['categories_per_second']} categories/sec")

    # Errors
    if overall["errors"]:
        lines.append(f"\n🔥 Errors Detected ({len(overall['errors'])}):")
        for error in overall["errors"]:
            lines.append(f"  • {error['category']}: {error['error']}")

    # Category details (if verbose)
    if verbose:
        lines.append("\n" + "-" * 70)
        lines.append("📋 Category Details:\n")

        for category, data in result["categories"].items():
            analysis = data.get("analysis", {})
            metrics = data.get("metrics", {})

            status = analysis.get("status", "unknown")
            risk = analysis.get("risk_level", "unknown")
            exec_time = data.get("execution_time", 0.0)

            lines.append(f"\n{category.upper()}:")
            lines.append(f"  Status: {status_emoji.get(status, '❓')} {status}")
            lines.append(f"  Risk: {risk}")
            lines.append(f"  Execution: {exec_time:.3f}s")

            # Show key metrics
            if metrics:
                lines.append(f"  Metrics:")
                for key, value in list(metrics.items())[:3]:  # Show first 3 metrics
                    if isinstance(value, (int, float)):
                        lines.append(f"    • {key}: {value}")

            # Show recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                lines.append(f"  Recommendations ({len(recommendations)}):")
                for rec in recommendations[:2]:  # Show first 2
                    # Handle both dict and string recommendations
                    if isinstance(rec, dict):
                        action = rec.get("action", rec.get("issue", str(rec)))
                    else:
                        action = str(rec)
                    lines.append(f"    • {action}")
    else:
        # Summary only
        lines.append(f"\n💡 Tip: Use --verbose for detailed category analysis")

    return "\n".join(lines)


@click.command()
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON instead of human-readable format')
@click.option('--cpu-threshold', type=float, default=None,
              help='CPU usage warning threshold (default: 70.0%%)')
@click.option('--memory-threshold', type=float, default=None,
              help='Memory usage warning threshold (default: 85.0%%)')
@click.option('--disk-threshold', type=float, default=None,
              help='Disk usage warning threshold (default: 90.0%%)')
@click.option('--network-threshold', type=float, default=None,
              help='Network error rate threshold (default: 1.0%%)')
@click.option('--battery-threshold', type=float, default=None,
              help='Battery level warning threshold (default: 20.0%%)')
@click.option('--thermal-threshold', type=float, default=None,
              help='Thermal warning threshold in Celsius (default: 75.0°C)')
@click.option('--verbose', is_flag=True,
              help='Show detailed output for each category')
def main(
    output_json: bool,
    cpu_threshold: Optional[float],
    memory_threshold: Optional[float],
    disk_threshold: Optional[float],
    network_threshold: Optional[float],
    battery_threshold: Optional[float],
    thermal_threshold: Optional[float],
    verbose: bool
):
    """
    Run parallel analysis across all resource categories.

    Executes CPU, memory, disk, network, battery, and thermal analyzers
    concurrently, then aggregates results into comprehensive system health report.

    Examples:
        # Basic analysis
        uv run analyze_all.py

        # JSON output for automation
        uv run analyze_all.py --json

        # Detailed verbose output
        uv run analyze_all.py --verbose

        # Custom thresholds
        uv run analyze_all.py --cpu-threshold 80 --memory-threshold 90
    """
    thresholds = {}
    if cpu_threshold is not None:
        thresholds["cpu"] = cpu_threshold
    if memory_threshold is not None:
        thresholds["memory"] = memory_threshold
    if disk_threshold is not None:
        thresholds["disk"] = disk_threshold
    if network_threshold is not None:
        thresholds["network"] = network_threshold
    if battery_threshold is not None:
        thresholds["battery"] = battery_threshold
    if thermal_threshold is not None:
        thresholds["thermal"] = thermal_threshold

    try:
        analyzer = ParallelAnalyzer(verbose=verbose)
        result = asyncio.run(analyzer.analyze_all(thresholds))

        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            # Human-readable format
            output = format_human_readable(result, verbose)
            click.echo(output)

        # Exit code based on overall risk
        risk = result["overall"]["risk_level"]
        if risk == "critical":
            sys.exit(2)
        elif risk in ["high", "medium", "warning"]:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "command": "analyze_all"
        }
        if output_json:
            click.echo(json.dumps(error_data, indent=2), err=True)
        else:
            click.echo(f"❌ Error running parallel analysis: {e}", err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
