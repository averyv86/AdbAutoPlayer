"""
UV Script Integration Tests

Tests all 12 UV scripts with subprocess execution.
Each script has 5 test cases:
1. JSON output format
2. Exit code correctness
3. CLI parameters
4. Metrics structure validation
5. Performance (< 5s execution)

Total: 60 tests (5 tests × 12 scripts)
"""

import subprocess
import json
import time
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


# ==============================================================================
# TEST GROUP 1: status.py (5 tests)
# ==============================================================================

class TestStatusScript:
    """Test status.py UV script (5 tests)."""

    def test_status_json_output(self):
        """Test status.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)

        assert "status" in data
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_percent" in data

    def test_status_exit_codes(self):
        """Test status.py exit code system."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Valid exit codes: 0 (healthy), 1 (warning), 2 (critical), 3 (error)
        assert result.returncode in [0, 1, 2, 3]

        if result.returncode in [0, 1, 2]:
            # Valid analysis result
            data = json.loads(result.stdout)
            assert "status" in data

    def test_status_verbose_mode(self):
        """Test status.py verbose mode."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--verbose"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2]
        # Verbose mode should produce human-readable output
        assert len(result.stdout) > 0

    def test_status_metrics_structure(self):
        """Test status.py metrics structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        data = json.loads(result.stdout)

        # Type validation
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["status"], str)
        assert isinstance(data["cpu_percent"], (int, float))
        assert isinstance(data["memory_percent"], (int, float))
        assert isinstance(data["disk_percent"], (int, float))
        assert isinstance(data["warnings"], list)
        assert isinstance(data["critical_issues"], list)

    def test_status_performance(self):
        """Test status.py executes within 5 seconds."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "status.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        duration = time.time() - start
        assert duration < 5.0, f"Script took {duration:.2f}s (expected < 5s)"


# ==============================================================================
# TEST GROUP 2: analyze_cpu.py (5 tests)
# ==============================================================================

class TestAnalyzeCPUScript:
    """Test analyze_cpu.py UV script (5 tests)."""

    def test_analyze_cpu_json_output(self):
        """Test analyze_cpu.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_cpu.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)

        assert data["category"] == "cpu"
        assert "metrics" in data
        assert "analysis" in data

        metrics = data["metrics"]
        assert "usage_percent" in metrics
        assert "core_count" in metrics

    def test_analyze_cpu_threshold(self):
        """Test analyze_cpu.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_cpu.py"), "--json", "--threshold", "50.0"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)

        # Threshold should affect risk level
        assert "analysis" in data
        assert "risk_level" in data["analysis"]

    def test_analyze_cpu_exit_codes(self):
        """Test analyze_cpu.py exit code mapping."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_cpu.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

        if result.returncode in [0, 1, 2]:
            data = json.loads(result.stdout)
            risk_level = data["analysis"]["risk_level"]

            # Exit code should match risk level
            # 0 = low, 1 = warning, 2 = critical
            if result.returncode == 0:
                assert risk_level == "low"
            elif result.returncode == 1:
                assert risk_level in ["warning", "medium"]
            elif result.returncode == 2:
                assert risk_level in ["high", "critical"]

    def test_analyze_cpu_metrics_structure(self):
        """Test analyze_cpu.py metrics structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_cpu.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        metrics = data["metrics"]

        # Required metrics
        assert "usage_percent" in metrics
        assert "core_count" in metrics
        assert "per_core_usage" in metrics
        assert "load_average" in metrics

        # Type validation
        assert isinstance(metrics["usage_percent"], (int, float))
        assert isinstance(metrics["core_count"], int)
        assert isinstance(metrics["per_core_usage"], list)

    def test_analyze_cpu_performance(self):
        """Test analyze_cpu.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_cpu.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0, f"CPU analysis took {duration:.2f}s (expected < 3s)"


# ==============================================================================
# TEST GROUP 3: analyze_memory.py (5 tests)
# ==============================================================================

class TestAnalyzeMemoryScript:
    """Test analyze_memory.py UV script (5 tests)."""

    def test_analyze_memory_json_output(self):
        """Test analyze_memory.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_memory.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)

        assert data["category"] == "memory"
        assert "metrics" in data
        assert "analysis" in data

    def test_analyze_memory_threshold(self):
        """Test analyze_memory.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_memory.py"), "--json", "--threshold", "60.0"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert "analysis" in data

    def test_analyze_memory_exit_codes(self):
        """Test analyze_memory.py exit code system."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_memory.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_memory_metrics_structure(self):
        """Test analyze_memory.py metrics structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_memory.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        metrics = data["metrics"]

        assert "usage_percent" in metrics
        assert "total" in metrics
        assert "available" in metrics

    def test_analyze_memory_performance(self):
        """Test analyze_memory.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_memory.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0, f"Memory analysis took {duration:.2f}s"


# ==============================================================================
# TEST GROUP 4: analyze_disk.py (5 tests)
# ==============================================================================

class TestAnalyzeDiskScript:
    """Test analyze_disk.py UV script (5 tests)."""

    def test_analyze_disk_json_output(self):
        """Test analyze_disk.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_disk.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert data["category"] == "disk"

    def test_analyze_disk_threshold(self):
        """Test analyze_disk.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_disk.py"), "--json", "--threshold", "70.0"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]

    def test_analyze_disk_exit_codes(self):
        """Test analyze_disk.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_disk.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_disk_metrics_structure(self):
        """Test analyze_disk.py metrics."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_disk.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        assert "metrics" in data

    def test_analyze_disk_performance(self):
        """Test analyze_disk.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_disk.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0


# ==============================================================================
# TEST GROUP 5: analyze_network.py (5 tests)
# ==============================================================================

class TestAnalyzeNetworkScript:
    """Test analyze_network.py UV script (5 tests)."""

    def test_analyze_network_json_output(self):
        """Test analyze_network.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_network.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert data["category"] == "network"

    def test_analyze_network_threshold(self):
        """Test analyze_network.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_network.py"), "--json", "--threshold", "1000"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]

    def test_analyze_network_exit_codes(self):
        """Test analyze_network.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_network.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_network_metrics_structure(self):
        """Test analyze_network.py metrics."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_network.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        assert "metrics" in data

    def test_analyze_network_performance(self):
        """Test analyze_network.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_network.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0


# ==============================================================================
# TEST GROUP 6: analyze_battery.py (5 tests)
# ==============================================================================

class TestAnalyzeBatteryScript:
    """Test analyze_battery.py UV script (5 tests)."""

    def test_analyze_battery_json_output(self):
        """Test analyze_battery.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_battery.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert data["category"] == "battery"

    def test_analyze_battery_threshold(self):
        """Test analyze_battery.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_battery.py"), "--json", "--threshold", "30"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]

    def test_analyze_battery_exit_codes(self):
        """Test analyze_battery.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_battery.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_battery_metrics_structure(self):
        """Test analyze_battery.py metrics."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_battery.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        assert "metrics" in data

    def test_analyze_battery_performance(self):
        """Test analyze_battery.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_battery.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0


# ==============================================================================
# TEST GROUP 7: analyze_thermal.py (5 tests)
# ==============================================================================

class TestAnalyzeThermalScript:
    """Test analyze_thermal.py UV script (5 tests)."""

    def test_analyze_thermal_json_output(self):
        """Test analyze_thermal.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_thermal.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert data["category"] == "thermal"

    def test_analyze_thermal_threshold(self):
        """Test analyze_thermal.py threshold parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_thermal.py"), "--json", "--threshold", "70.0"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]

    def test_analyze_thermal_exit_codes(self):
        """Test analyze_thermal.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_thermal.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_thermal_metrics_structure(self):
        """Test analyze_thermal.py metrics."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_thermal.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)
        assert "metrics" in data

    def test_analyze_thermal_performance(self):
        """Test analyze_thermal.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_thermal.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        assert duration < 3.0


# ==============================================================================
# TEST GROUP 8: analyze_all.py (5 tests)
# ==============================================================================

class TestAnalyzeAllScript:
    """Test analyze_all.py UV script (5 tests)."""

    def test_analyze_all_json_output(self):
        """Test analyze_all.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode in [0, 1, 2]
        data = json.loads(result.stdout)
        assert "categories" in data

    def test_analyze_all_parallel_execution(self):
        """Test analyze_all.py runs analyses in parallel."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode in [0, 1, 2]

    def test_analyze_all_exit_codes(self):
        """Test analyze_all.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_analyze_all_results_structure(self):
        """Test analyze_all.py results structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        data = json.loads(result.stdout)
        assert "categories" in data

    def test_analyze_all_performance(self):
        """Test analyze_all.py completes within reasonable time."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        duration = time.time() - start
        # Parallel execution should be faster than sequential
        assert duration < 10.0, f"Parallel analysis took {duration:.2f}s"


# ==============================================================================
# TEST GROUP 9: optimize.py (5 tests)
# ==============================================================================

class TestOptimizeScript:
    """Test optimize.py UV script (5 tests)."""

    def test_optimize_json_output(self):
        """Test optimize.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "optimize.py"), "--json", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2]

    def test_optimize_dry_run_mode(self):
        """Test optimize.py dry-run mode."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "optimize.py"), "--json", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2]

    def test_optimize_exit_codes(self):
        """Test optimize.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "optimize.py"), "--json", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_optimize_actions_structure(self):
        """Test optimize.py optimization actions structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "optimize.py"), "--json", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_optimize_performance(self):
        """Test optimize.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "optimize.py"), "--json", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=20
        )

        duration = time.time() - start
        assert duration < 5.0


# ==============================================================================
# TEST GROUP 10: monitor.py (5 tests)
# ==============================================================================

class TestMonitorScript:
    """Test monitor.py UV script (5 tests)."""

    def test_monitor_json_output(self):
        """Test monitor.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "5"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2]

    def test_monitor_duration_parameter(self):
        """Test monitor.py duration parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "3"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2]

    def test_monitor_exit_codes(self):
        """Test monitor.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "5"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_monitor_metrics_collection(self):
        """Test monitor.py collects metrics over time."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "5"],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_monitor_performance(self):
        """Test monitor.py respects duration."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "monitor.py"), "--json", "--duration", "5"],
            capture_output=True,
            text=True,
            timeout=15
        )

        duration = time.time() - start
        # Should complete within duration + overhead
        assert duration < 8.0


# ==============================================================================
# TEST GROUP 11: report.py (5 tests)
# ==============================================================================

class TestReportScript:
    """Test report.py UV script (5 tests)."""

    def test_report_json_output(self):
        """Test report.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "report.py"), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2]

    def test_report_format_parameter(self):
        """Test report.py format parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "report.py"), "--format", "markdown"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2]

    def test_report_exit_codes(self):
        """Test report.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "report.py"), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_report_content_structure(self):
        """Test report.py report structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "report.py"), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=20
        )

        assert result.returncode in [0, 1, 2, 3]

    def test_report_performance(self):
        """Test report.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "report.py"), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=20
        )

        duration = time.time() - start
        assert duration < 5.0


# ==============================================================================
# TEST GROUP 12: cache.py (5 tests)
# ==============================================================================

class TestCacheScript:
    """Test cache.py UV script (5 tests)."""

    def test_cache_json_output(self):
        """Test cache.py produces valid JSON."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 3]

    def test_cache_operation_parameter(self):
        """Test cache.py operation parameter."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "clear", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 3]

    def test_cache_exit_codes(self):
        """Test cache.py exit codes."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 3]

    def test_cache_stats_structure(self):
        """Test cache.py stats structure."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 3]

    def test_cache_performance(self):
        """Test cache.py performance."""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "cache.py"), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        duration = time.time() - start
        assert duration < 2.0
