#!/usr/bin/env python3
# /// script
# dependencies = ["psutil>=5.9.0", "click>=8.1.0"]
# ///

"""
macOS All-Category Resource Analyzer

Executes parallel analysis across all 6 resource categories.
Aggregates results and provides comprehensive system health overview.

Usage:
    uv run analyze_all.py --json
    uv run analyze_all.py --summary
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import click


# Script locations (absolute paths)
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
    """Orchestrates parallel category analysis"""

    def __init__(self):
        self.execution_start = time.time()

    async def run_category_script(
        self, category: str, script_path: Path
    ) -> Dict[str, Any]:
        """Execute single category script asynchronously"""
        try:
            # Verify script exists
            if not script_path.exists():
                return self._create_error_result(
                    category, f"Script not found: {script_path}"
                )

            # Execute script with uv run
            proc = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                str(script_path),
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            # Valid exit codes: 0 (healthy), 1 (warning), 2 (critical)
            if proc.returncode in [0, 1, 2]:
                try:
                    return json.loads(stdout.decode())
                except json.JSONDecodeError as e:
                    return self._create_error_result(
                        category, f"Invalid JSON output: {str(e)}"
                    )
            else:
                # Script failed with error (exit code 3+)
                error_msg = stderr.decode() if stderr else "Unknown error"
                return self._create_error_result(category, error_msg)

        except FileNotFoundError:
            return self._create_error_result(category, "uv command not found")
        except Exception as e:
            return self._create_error_result(category, str(e))

    def _create_error_result(self, category: str, error_msg: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "category": category,
            "timestamp": time.time(),
            "error": error_msg,
            "analysis": {
                "status": "error",
                "risk_level": "unknown",
                "recommendations": [
                    f"Fix {category} analysis script: {error_msg}"
                ],
            },
        }

    async def analyze_all(self) -> Dict[str, Any]:
        """Execute all category analyses in parallel"""
        start_time = time.time()

        # Create tasks for all categories
        tasks = [
            self.run_category_script(category, script_path)
            for category, script_path in CATEGORY_SCRIPTS.items()
        ]

        # Execute in parallel with asyncio.gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        categories = {}
        overall_status = "healthy"
        max_risk = "low"
        total_recommendations = 0
        error_count = 0
        warning_count = 0
        critical_count = 0

        for result in results:
            # Handle exceptions from gather
            if isinstance(result, Exception):
                error_count += 1
                continue

            category = result.get("category", "unknown")
            categories[category] = result

            # Extract analysis data
            analysis = result.get("analysis", {})
            status = analysis.get("status", "error")
            risk = analysis.get("risk_level", "unknown")
            recommendations = analysis.get("recommendations", [])

            # Update overall status (critical > warning > healthy)
            if status in ["critical", "error"]:
                critical_count += 1
                overall_status = "critical"
            elif status == "warning":
                warning_count += 1
                if overall_status == "healthy":
                    overall_status = "warning"

            # Track highest risk level
            if risk == "high":
                max_risk = "high"
            elif risk == "medium" and max_risk == "low":
                max_risk = "medium"

            # Count recommendations
            total_recommendations += len(recommendations)

        execution_time = time.time() - start_time

        return {
            "timestamp": time.time(),
            "categories": categories,
            "summary": {
                "overall_status": overall_status,
                "max_risk_level": max_risk,
                "total_recommendations": total_recommendations,
                "categories_analyzed": len(categories),
                "error_count": error_count,
                "warning_count": warning_count,
                "critical_count": critical_count,
                "healthy_count": len(categories)
                - error_count
                - warning_count
                - critical_count,
                "execution_time_seconds": round(execution_time, 2),
            },
        }

    def generate_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        summary = result["summary"]
        categories = result["categories"]

        lines = [
            "",
            "=" * 60,
            "macOS System Resource Analysis (All Categories)",
            "=" * 60,
            "",
            f"Overall Status: {summary['overall_status'].upper()}",
            f"Risk Level: {summary['max_risk_level'].upper()}",
            f"Total Issues: {summary['total_recommendations']}",
            "",
            "Category Breakdown:",
            f"  • Categories Analyzed: {summary['categories_analyzed']}/6",
            f"  • Healthy: {summary['healthy_count']}",
            f"  • Warning: {summary['warning_count']}",
            f"  • Critical: {summary['critical_count']}",
            f"  • Error: {summary['error_count']}",
            "",
            f"Execution Time: {summary['execution_time_seconds']}s",
            "",
        ]

        # Add category-specific details
        if summary["total_recommendations"] > 0:
            lines.append("Top Recommendations:")
            lines.append("")

            # Collect all recommendations by priority
            all_recommendations = []
            for category, data in categories.items():
                analysis = data.get("analysis", {})
                recs = analysis.get("recommendations", [])
                status = analysis.get("status", "unknown")

                for rec in recs:
                    priority = 3 if status == "critical" else (2 if status == "warning" else 1)
                    all_recommendations.append((priority, category, rec))

            # Sort by priority (critical first)
            all_recommendations.sort(key=lambda x: x[0], reverse=True)

            # Display top 10 recommendations
            for i, (priority, category, rec) in enumerate(
                all_recommendations[:10], start=1
            ):
                priority_label = (
                    "CRITICAL" if priority == 3 else ("WARNING" if priority == 2 else "INFO")
                )
                lines.append(f"  {i}. [{priority_label}] {category}: {rec}")

            if len(all_recommendations) > 10:
                lines.append(
                    f"\n  ... and {len(all_recommendations) - 10} more recommendations"
                )

        lines.extend(["", "=" * 60, ""])

        return "\n".join(lines)


@click.command()
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON (default: false)",
)
@click.option(
    "--summary", is_flag=True, default=False, help="Show human-readable summary"
)
def main(output_json: bool, summary: bool):
    """Execute parallel system resource analysis"""
    try:
        analyzer = ParallelAnalyzer()
        result = asyncio.run(analyzer.analyze_all())

        # Default to summary if neither flag is specified
        if not output_json and not summary:
            summary = True

        if summary:
            # Human-readable summary
            click.echo(analyzer.generate_summary(result))
        else:
            # JSON output
            click.echo(json.dumps(result, indent=2))

        # Exit code based on overall status
        status = result["summary"]["overall_status"]
        if status == "critical":
            sys.exit(2)
        elif status == "warning":
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        click.echo("\n\nAnalysis interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        error_data = {
            "error": str(e),
            "status": "error",
            "timestamp": time.time(),
        }
        click.echo(json.dumps(error_data, indent=2), err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
