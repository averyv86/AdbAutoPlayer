#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Browser Tab Analyzer - Estimate tab count and memory usage

Analyzes browser processes to estimate:
- Number of tabs open
- Memory usage per tab
- Total browser memory consumption
- Potential memory recovery from tab suspension

Works WITHOUT Chrome extension by analyzing helper processes.

Usage:
    # Analyze all browsers
    uv run scripts/tab_analyzer.py

    # Analyze specific browser
    uv run scripts/tab_analyzer.py --browser=chrome

    # JSON output
    uv run scripts/tab_analyzer.py --format=json

    # TOON output
    uv run scripts/tab_analyzer.py --format=toon

Author: MoAI-ADK
Version: 2.0.0 (Phase 2)
Date: 2025-12-01
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from toon_codec import encode_toon


@dataclass
class BrowserProfile:
    """Browser-specific process patterns and heuristics."""
    name: str
    process_patterns: List[str]
    helper_pattern: str
    avg_helpers_per_tab: float
    avg_mb_per_tab: float
    baseline_memory_mb: int  # Browser overhead without tabs


BROWSER_PROFILES = {
    "chrome": BrowserProfile(
        name="Chrome",
        process_patterns=["Google Chrome", "Chrome"],
        helper_pattern="Chrome Helper",
        avg_helpers_per_tab=2.5,
        avg_mb_per_tab=80,
        baseline_memory_mb=300
    ),
    "dia": BrowserProfile(
        name="Dia",
        process_patterns=["Dia", "Dia Browser"],
        helper_pattern="Dia Helper",
        avg_helpers_per_tab=2.5,
        avg_mb_per_tab=80,
        baseline_memory_mb=300
    ),
    "firefox": BrowserProfile(
        name="Firefox",
        process_patterns=["Firefox"],
        helper_pattern="firefox",
        avg_helpers_per_tab=1.8,
        avg_mb_per_tab=65,
        baseline_memory_mb=250
    ),
    "safari": BrowserProfile(
        name="Safari",
        process_patterns=["Safari"],
        helper_pattern="com.apple.WebKit.WebContent",
        avg_helpers_per_tab=1.5,
        avg_mb_per_tab=55,
        baseline_memory_mb=200
    )
}


@dataclass
class TabAnalysis:
    """Result of tab analysis for a browser."""
    browser: str
    running: bool
    estimated_tabs: int
    helper_processes: int
    total_memory_mb: int
    avg_memory_per_tab_mb: int
    estimated_recovery_mb: int
    recovery_percentage: float


class BrowserTabAnalyzer:
    """
    Analyze browser processes to estimate tab count and memory usage.

    Uses heuristics based on helper process counts and memory patterns.
    Does NOT require browser extension.
    """

    def __init__(self, browser: Optional[str] = None):
        """
        Initialize analyzer.

        Args:
            browser: Specific browser to analyze (chrome/dia/firefox/safari)
                    If None, analyzes all browsers
        """
        self.browser = browser

    def analyze_browser(self, profile: BrowserProfile) -> TabAnalysis:
        """
        Analyze a specific browser.

        Args:
            profile: Browser profile with patterns and heuristics

        Returns:
            TabAnalysis with estimated tab count and memory usage
        """
        main_processes = []
        helper_processes = []
        total_memory = 0

        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                name = proc.info.get('name', '')

                # Check if main browser process
                if any(pattern in name for pattern in profile.process_patterns):
                    if profile.helper_pattern not in name:
                        main_processes.append(proc)

                # Check if helper process
                if profile.helper_pattern in name:
                    helper_processes.append(proc)
                    try:
                        total_memory += proc.memory_info().rss / 1024 / 1024
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Check if browser is running
        if not main_processes:
            return TabAnalysis(
                browser=profile.name,
                running=False,
                estimated_tabs=0,
                helper_processes=0,
                total_memory_mb=0,
                avg_memory_per_tab_mb=0,
                estimated_recovery_mb=0,
                recovery_percentage=0.0
            )

        # Estimate tab count from helper processes
        helper_count = len(helper_processes)
        estimated_tabs = max(1, int(helper_count / profile.avg_helpers_per_tab))

        # Calculate memory metrics
        total_memory_mb = int(total_memory)
        working_memory = max(0, total_memory_mb - profile.baseline_memory_mb)
        avg_per_tab = int(working_memory / estimated_tabs) if estimated_tabs > 0 else profile.avg_mb_per_tab

        # Estimate recovery (assume 60% of tabs can be suspended)
        suspendable_ratio = 0.6
        memory_recovery_per_suspended_tab = 0.85  # 85% memory freed per suspended tab

        estimated_recovery = int(
            working_memory * suspendable_ratio * memory_recovery_per_suspended_tab
        )
        recovery_pct = (estimated_recovery / total_memory_mb * 100) if total_memory_mb > 0 else 0

        return TabAnalysis(
            browser=profile.name,
            running=True,
            estimated_tabs=estimated_tabs,
            helper_processes=helper_count,
            total_memory_mb=total_memory_mb,
            avg_memory_per_tab_mb=avg_per_tab,
            estimated_recovery_mb=estimated_recovery,
            recovery_percentage=round(recovery_pct, 1)
        )

    def analyze_all(self) -> List[TabAnalysis]:
        """
        Analyze all browsers or specific browser.

        Returns:
            List of TabAnalysis for each browser
        """
        results = []

        if self.browser:
            # Analyze specific browser
            if self.browser in BROWSER_PROFILES:
                profile = BROWSER_PROFILES[self.browser]
                results.append(self.analyze_browser(profile))
            else:
                print(f"Unknown browser: {self.browser}", file=sys.stderr)
                print(f"Available: {', '.join(BROWSER_PROFILES.keys())}", file=sys.stderr)
                sys.exit(1)
        else:
            # Analyze all browsers
            for profile in BROWSER_PROFILES.values():
                analysis = self.analyze_browser(profile)
                if analysis.running:  # Only include running browsers
                    results.append(analysis)

        return results

    def format_results(self, results: List[TabAnalysis], format: str = "text") -> str:
        """
        Format analysis results.

        Args:
            results: List of TabAnalysis
            format: Output format (text/json/toon)

        Returns:
            Formatted string
        """
        if format == "json":
            return json.dumps([{
                "browser": r.browser,
                "running": r.running,
                "estimated_tabs": r.estimated_tabs,
                "helper_processes": r.helper_processes,
                "total_memory_mb": r.total_memory_mb,
                "avg_memory_per_tab_mb": r.avg_memory_per_tab_mb,
                "estimated_recovery_mb": r.estimated_recovery_mb,
                "recovery_percentage": r.recovery_percentage
            } for r in results], indent=2)

        elif format == "toon":
            # TOON format for token efficiency
            toon_data = {
                "browsers": len(results),
                "total_tabs": sum(r.estimated_tabs for r in results),
                "total_memory_mb": sum(r.total_memory_mb for r in results),
                "total_recovery_mb": sum(r.estimated_recovery_mb for r in results),
                "details": [
                    {
                        "browser": r.browser,
                        "tabs": r.estimated_tabs,
                        "mem_mb": r.total_memory_mb,
                        "recovery_mb": r.estimated_recovery_mb
                    }
                    for r in results
                ]
            }
            return encode_toon(toon_data)

        else:  # text format
            lines = []
            lines.append("🔍 Browser Tab Analysis")
            lines.append("=" * 60)
            lines.append("")

            if not results:
                lines.append("No browsers running")
                return "\n".join(lines)

            for r in results:
                lines.append(f"📊 {r.browser}")
                lines.append(f"   Estimated tabs: {r.estimated_tabs}")
                lines.append(f"   Helper processes: {r.helper_processes}")
                lines.append(f"   Total memory: {r.total_memory_mb} MB")
                lines.append(f"   Avg per tab: {r.avg_memory_per_tab_mb} MB")
                lines.append(f"   Potential recovery: {r.estimated_recovery_mb} MB ({r.recovery_percentage}%)")
                lines.append("")

            total_tabs = sum(r.estimated_tabs for r in results)
            total_memory = sum(r.total_memory_mb for r in results)
            total_recovery = sum(r.estimated_recovery_mb for r in results)

            lines.append("📈 Summary")
            lines.append(f"   Total browsers: {len(results)}")
            lines.append(f"   Total tabs: {total_tabs}")
            lines.append(f"   Total memory: {total_memory} MB ({total_memory / 1024:.2f} GB)")
            lines.append(f"   Total recoverable: {total_recovery} MB ({total_recovery / 1024:.2f} GB)")
            lines.append("")

            return "\n".join(lines)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Browser Tab Analyzer - Estimate tab count and memory usage',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--browser',
                        choices=['chrome', 'dia', 'firefox', 'safari'],
                        help='Specific browser to analyze')
    parser.add_argument('--format',
                        choices=['text', 'json', 'toon'],
                        default='text',
                        help='Output format (default: text)')

    args = parser.parse_args()

    analyzer = BrowserTabAnalyzer(browser=args.browser)
    results = analyzer.analyze_all()

    output = analyzer.format_results(results, format=args.format)
    print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
