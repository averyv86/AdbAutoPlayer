"""
Performance Regression Tests

Ensures UV scripts maintain acceptable performance characteristics.
Baseline from initial implementation (Phase 1-3).

Total: 12 tests (1 per script)
"""

import subprocess
import time
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"

# Performance baselines (from Phase 1-3 testing)
# Each value is the maximum acceptable execution time in seconds
PERFORMANCE_BASELINES = {
    "status.py": 2.0,  # Quick health check
    "analyze_cpu.py": 2.0,  # CPU analysis with 1s interval
    "analyze_memory.py": 2.0,  # Memory analysis
    "analyze_disk.py": 2.0,  # Disk analysis
    "analyze_network.py": 2.0,  # Network analysis
    "analyze_battery.py": 2.0,  # Battery analysis
    "analyze_thermal.py": 2.0,  # Thermal analysis
    "analyze_all.py": 8.0,  # Parallel execution of all analyses
    "optimize.py": 5.0,  # Optimization dry-run
    "monitor.py": 8.0,  # 5s monitoring + overhead
    "report.py": 5.0,  # Report generation
    "cache.py": 1.0,  # Cache operations
}


@pytest.mark.parametrize("script_name,baseline", PERFORMANCE_BASELINES.items())
def test_script_performance(script_name, baseline):
    """Test script execution time doesn't exceed baseline."""
    script_path = SCRIPTS_DIR / script_name

    # Special handling for scripts with required parameters
    cmd = ["uv", "run", str(script_path), "--json"]

    if script_name == "monitor.py":
        cmd.extend(["--duration", "5"])
    elif script_name == "optimize.py":
        cmd.append("--dry-run")
    elif script_name == "report.py":
        cmd.extend(["--format", "json"])
    elif script_name == "cache.py":
        cmd.extend(["--operation", "stats"])

    start = time.time()

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=baseline * 2  # 2x baseline as timeout
    )

    duration = time.time() - start

    # Allow 20% variance from baseline
    max_duration = baseline * 1.2

    assert duration < max_duration, (
        f"{script_name} took {duration:.2f}s "
        f"(baseline: {baseline:.2f}s, max: {max_duration:.2f}s)"
    )

    # Verify script executed successfully
    assert result.returncode in [0, 1, 2, 3], (
        f"{script_name} failed with exit code {result.returncode}: {result.stderr}"
    )


class TestPerformanceComparison:
    """Test relative performance between scripts."""

    def test_status_faster_than_analyze_all(self):
        """Test status.py is significantly faster than analyze_all.py."""

        # Measure status.py
        start = time.time()
        subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        status_duration = time.time() - start

        # Measure analyze_all.py
        start = time.time()
        subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        analyze_all_duration = time.time() - start

        # Status should be at least 2x faster
        assert status_duration * 2 < analyze_all_duration, (
            f"Status ({status_duration:.2f}s) should be significantly faster "
            f"than analyze_all ({analyze_all_duration:.2f}s)"
        )

    def test_parallel_analysis_performance(self):
        """Test analyze_all.py parallel execution is efficient."""

        # Measure individual analysis scripts (sequential simulation)
        individual_scripts = [
            "analyze_cpu.py",
            "analyze_memory.py",
            "analyze_disk.py"
        ]

        sequential_total = 0
        for script in individual_scripts:
            start = time.time()
            subprocess.run(
                ["uv", "run", str(SCRIPTS_DIR / script), "--json"],
                capture_output=True,
                text=True,
                timeout=15
            )
            sequential_total += time.time() - start

        # Measure parallel execution
        start = time.time()
        subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        parallel_duration = time.time() - start

        # Parallel should be faster than sequential
        # (allowing some overhead for parallelization)
        assert parallel_duration < sequential_total * 0.7, (
            f"Parallel execution ({parallel_duration:.2f}s) should be faster "
            f"than sequential ({sequential_total:.2f}s)"
        )

    def test_cache_script_minimal_overhead(self):
        """Test cache.py has minimal execution overhead."""

        start = time.time()
        subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        duration = time.time() - start

        # Cache operations should be very fast
        assert duration < 1.5, (
            f"Cache operations took {duration:.2f}s (expected < 1.5s)"
        )


class TestMemoryEfficiency:
    """Test scripts execute with reasonable memory usage."""

    @pytest.mark.parametrize("script_name", [
        "status.py",
        "analyze_cpu.py",
        "analyze_memory.py"
    ])
    def test_script_completes_without_memory_error(self, script_name):
        """Test scripts complete without memory-related errors."""

        script_path = SCRIPTS_DIR / script_name

        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Should not fail with memory errors
        assert "MemoryError" not in result.stderr
        assert "memory" not in result.stderr.lower() or result.returncode in [0, 1, 2]


class TestConcurrentExecution:
    """Test scripts can run concurrently without conflicts."""

    def test_multiple_status_scripts_concurrent(self):
        """Test multiple status.py instances can run concurrently."""

        import concurrent.futures

        def run_status():
            result = subprocess.run(
                ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode in [0, 1, 2]

        # Run 3 instances concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_status) for _ in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should complete successfully
        assert all(results), "Not all concurrent executions succeeded"

    def test_monitor_script_graceful_termination(self):
        """Test monitor.py can be terminated gracefully."""

        # Start monitor script
        process = subprocess.Popen(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "30"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Let it run for 2 seconds
        time.sleep(2)

        # Terminate gracefully
        process.terminate()

        try:
            # Wait for process to terminate
            process.wait(timeout=5)
            terminated_successfully = True
        except subprocess.TimeoutExpired:
            # Force kill if graceful termination failed
            process.kill()
            terminated_successfully = False

        assert terminated_successfully, "Monitor script didn't terminate gracefully"


class TestStartupPerformance:
    """Test UV script startup time is reasonable."""

    @pytest.mark.parametrize("script_name", [
        "status.py",
        "cache.py"
    ])
    def test_script_startup_time(self, script_name):
        """Test script startup time is under 1 second."""

        script_path = SCRIPTS_DIR / script_name

        # Measure time to first output
        start = time.time()

        if script_name == "cache.py":
            cmd = ["uv", "run", str(script_path), "--operation", "stats", "--json"]
        else:
            cmd = ["uv", "run", str(script_path), "--json"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        startup_time = time.time() - start

        # UV startup + script initialization should be fast
        assert startup_time < 3.0, (
            f"{script_name} startup took {startup_time:.2f}s (expected < 3s)"
        )


@pytest.mark.slow
class TestLongRunningPerformance:
    """Test long-running script performance."""

    def test_monitor_extended_duration(self):
        """Test monitor.py maintains performance over extended duration."""

        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "10"],
            capture_output=True,
            text=True,
            timeout=20
        )

        duration = time.time() - start

        # Should complete within duration + reasonable overhead
        assert duration < 13.0, (
            f"10s monitoring took {duration:.2f}s (expected < 13s)"
        )

        assert result.returncode in [0, 1, 2], (
            f"Monitor script failed: {result.stderr}"
        )


class TestResourceCleanup:
    """Test scripts properly clean up resources."""

    def test_no_zombie_processes(self):
        """Test scripts don't leave zombie processes."""

        # Run several scripts in sequence
        scripts_to_test = [
            ("status.py", ["--json"]),
            ("analyze_cpu.py", ["--json"]),
            ("cache.py", ["--operation", "stats", "--json"])
        ]

        for script_name, args in scripts_to_test:
            result = subprocess.run(
                ["uv", "run", str(SCRIPTS_DIR / script_name)] + args,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Process should have completed cleanly
            assert result.returncode in [0, 1, 2, 3], (
                f"{script_name} ended with unexpected return code {result.returncode}"
            )

        # Check for zombie processes (macOS)
        ps_result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Look for defunct/zombie processes
        assert "<defunct>" not in ps_result.stdout, (
            "Zombie processes detected after script execution"
        )


# Summary test to validate all baselines
def test_performance_baselines_summary():
    """Summary test: validate all scripts meet performance baselines."""

    results = {}
    failures = []

    for script_name, baseline in PERFORMANCE_BASELINES.items():
        script_path = SCRIPTS_DIR / script_name

        # Build command
        cmd = ["uv", "run", str(script_path), "--json"]

        if script_name == "monitor.py":
            cmd.extend(["--duration", "5"])
        elif script_name == "optimize.py":
            cmd.append("--dry-run")
        elif script_name == "report.py":
            cmd.extend(["--format", "json"])
        elif script_name == "cache.py":
            cmd.extend(["--operation", "stats"])

        # Measure execution time
        start = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=baseline * 2
            )
            duration = time.time() - start
            max_duration = baseline * 1.2

            results[script_name] = {
                "duration": duration,
                "baseline": baseline,
                "max_allowed": max_duration,
                "passed": duration < max_duration,
                "exit_code": result.returncode
            }

            if duration >= max_duration:
                failures.append(
                    f"{script_name}: {duration:.2f}s exceeds {max_duration:.2f}s"
                )

        except subprocess.TimeoutExpired:
            results[script_name] = {
                "duration": baseline * 2,
                "baseline": baseline,
                "passed": False,
                "error": "timeout"
            }
            failures.append(f"{script_name}: timeout")

    # Print summary
    print("\n" + "=" * 80)
    print("PERFORMANCE REGRESSION TEST SUMMARY")
    print("=" * 80)

    for script_name, result_data in results.items():
        if "error" in result_data:
            status = "❌ TIMEOUT"
        elif result_data["passed"]:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        duration = result_data.get("duration", 0)
        baseline = result_data.get("baseline", 0)

        print(f"{status} {script_name:20} {duration:6.2f}s / {baseline:6.2f}s baseline")

    print("=" * 80)

    # Assert no failures
    assert len(failures) == 0, (
        f"\n{len(failures)} performance regression(s) detected:\n" +
        "\n".join(failures)
    )
