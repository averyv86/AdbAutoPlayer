#!/usr/bin/env python3
"""
Performance Regression Tests for macOS Resource Optimizer Scripts

These tests ensure all scripts maintain performance targets.
Run with: pytest tests/test_performance/ -v --tb=short
"""

import time
import subprocess
import pytest
from pathlib import Path
from typing import List, Tuple

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"

# Performance targets (seconds)
TARGETS = {
    "status.py": 0.5,
    "analyze_cpu.py": 0.5,
    "analyze_memory.py": 0.5,
    "analyze_disk.py": 0.5,
    "analyze_network.py": 0.5,
    "analyze_battery.py": 0.5,
    "analyze_thermal.py": 0.5,
    "analyze_all.py": 2.5,  # CRITICAL
    "optimize.py": 3.0,
    "report.py": 2.0,
    "cache.py": 0.2,
}


def run_script_with_timing(script_name: str, args: List[str]) -> Tuple[float, int]:
    """Run a script and measure execution time"""
    script_path = SCRIPTS_DIR / script_name
    cmd = ["uv", "run", str(script_path)] + args

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            text=True
        )
        duration = time.time() - start
        return duration, result.returncode
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return duration, -1


@pytest.mark.performance
class TestScriptPerformance:
    """Performance regression tests for all UV scripts"""

    def test_status_performance(self):
        """status.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("status.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["status.py"], (
            f"status.py took {duration:.3f}s (target: <{TARGETS['status.py']}s)"
        )

    def test_analyze_cpu_performance(self):
        """analyze_cpu.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_cpu.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_cpu.py"], (
            f"analyze_cpu.py took {duration:.3f}s (target: <{TARGETS['analyze_cpu.py']}s)"
        )

    def test_analyze_memory_performance(self):
        """analyze_memory.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_memory.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_memory.py"], (
            f"analyze_memory.py took {duration:.3f}s (target: <{TARGETS['analyze_memory.py']}s)"
        )

    def test_analyze_disk_performance(self):
        """analyze_disk.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_disk.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_disk.py"], (
            f"analyze_disk.py took {duration:.3f}s (target: <{TARGETS['analyze_disk.py']}s)"
        )

    def test_analyze_network_performance(self):
        """analyze_network.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_network.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_network.py"], (
            f"analyze_network.py took {duration:.3f}s (target: <{TARGETS['analyze_network.py']}s)"
        )

    def test_analyze_battery_performance(self):
        """analyze_battery.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_battery.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_battery.py"], (
            f"analyze_battery.py took {duration:.3f}s (target: <{TARGETS['analyze_battery.py']}s)"
        )

    def test_analyze_thermal_performance(self):
        """analyze_thermal.py must complete in <0.5s"""
        duration, exit_code = run_script_with_timing("analyze_thermal.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_thermal.py"], (
            f"analyze_thermal.py took {duration:.3f}s (target: <{TARGETS['analyze_thermal.py']}s)"
        )

    @pytest.mark.critical
    def test_analyze_all_performance(self):
        """CRITICAL: analyze_all.py must complete in <2.5s"""
        duration, exit_code = run_script_with_timing("analyze_all.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["analyze_all.py"], (
            f"analyze_all.py took {duration:.3f}s (target: <{TARGETS['analyze_all.py']}s) - "
            f"CRITICAL PERFORMANCE REGRESSION"
        )

    def test_optimize_performance(self):
        """optimize.py must complete in <3.0s (dry-run mode)"""
        duration, exit_code = run_script_with_timing("optimize.py", ["--dry-run", "--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["optimize.py"], (
            f"optimize.py took {duration:.3f}s (target: <{TARGETS['optimize.py']}s)"
        )

    def test_report_performance(self):
        """report.py must complete in <2.0s"""
        duration, exit_code = run_script_with_timing("report.py", ["--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["report.py"], (
            f"report.py took {duration:.3f}s (target: <{TARGETS['report.py']}s)"
        )

    def test_cache_performance(self):
        """cache.py must complete in <0.2s"""
        duration, exit_code = run_script_with_timing("cache.py", ["--stats", "--json"])

        assert exit_code in [0, 1, 2], f"Unexpected exit code: {exit_code}"
        assert duration < TARGETS["cache.py"], (
            f"cache.py took {duration:.3f}s (target: <{TARGETS['cache.py']}s)"
        )


@pytest.mark.performance
class TestParallelExecution:
    """Test parallel execution efficiency of analyze_all.py"""

    def test_analyze_all_uses_parallel_execution(self):
        """Verify analyze_all.py benefits from parallel execution"""
        # Run individual analyzers sequentially
        individual_scripts = [
            "analyze_cpu.py",
            "analyze_memory.py",
            "analyze_disk.py",
            "analyze_network.py",
            "analyze_battery.py",
            "analyze_thermal.py"
        ]

        sequential_total = 0
        for script in individual_scripts:
            duration, _ = run_script_with_timing(script, ["--json"])
            sequential_total += duration

        # Run analyze_all.py (parallel)
        parallel_duration, _ = run_script_with_timing("analyze_all.py", ["--json"])

        # Parallel should be significantly faster than sequential
        efficiency = (1 - parallel_duration / sequential_total) * 100

        assert parallel_duration < sequential_total, (
            f"Parallel execution ({parallel_duration:.3f}s) should be faster than "
            f"sequential ({sequential_total:.3f}s)"
        )
        assert efficiency > 40, (
            f"Parallel efficiency too low: {efficiency:.1f}% "
            f"(expected >40% improvement)"
        )


@pytest.mark.performance
class TestMemoryEfficiency:
    """Test memory efficiency during script execution"""

    def test_analyze_all_memory_efficiency(self):
        """Verify analyze_all.py doesn't cause memory issues"""
        # This is a basic sanity check - actual memory profiling would require psutil
        duration, exit_code = run_script_with_timing("analyze_all.py", ["--json"])

        # If script completes successfully without timeout, memory usage is acceptable
        assert exit_code in [0, 1, 2], "Script failed or crashed (possible OOM)"
        assert duration < 5.0, "Script took too long (possible memory thrashing)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
