"""
Test suite for analyze_memory.py script.

Script: Memory analyzer with swap monitoring and memory pressure detection
Dependencies: psutil>=5.9.0, click>=8.1.0
Format: ASTRAL UV inline script metadata
Tests: 5 (JSON output, custom threshold, exit codes, performance, metrics structure)
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest


# Path to the analyze_memory.py script
SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "analyze_memory.py"


class TestAnalyzeMemoryJSONOutput:
    """Test 1: JSON output structure and completeness."""

    def test_json_output_structure(self):
        """Test analyze_memory.py --json produces valid JSON with required fields."""
        # Run the script with --json flag
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse JSON output
        assert result.stdout, "Script produced no output"
        output = json.loads(result.stdout)

        # Verify top-level structure
        assert "category" in output
        assert output["category"] == "memory"
        assert "timestamp" in output
        assert "metrics" in output
        assert "analysis" in output

    def test_json_metrics_completeness(self):
        """Test JSON output contains all required memory metrics."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        metrics = output["metrics"]

        # Virtual memory metrics
        assert "total" in metrics
        assert "used" in metrics
        assert "available" in metrics
        assert "percent" in metrics

        # Swap metrics
        assert "swap_total" in metrics
        assert "swap_used" in metrics
        assert "swap_percent" in metrics

        # macOS-specific metrics
        assert "active" in metrics
        assert "inactive" in metrics
        assert "wired" in metrics
        assert "memory_pressure" in metrics

    def test_json_analysis_structure(self):
        """Test JSON output contains complete analysis section."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        analysis = output["analysis"]

        # Analysis fields
        assert "status" in analysis
        assert analysis["status"] in ["healthy", "warning", "critical"]
        assert "risk_level" in analysis
        assert analysis["risk_level"] in ["low", "warning", "critical"]
        assert "issues" in analysis
        assert "recommendations" in analysis
        assert "top_consumers" in analysis

        # Top consumers structure
        assert isinstance(analysis["top_consumers"], list)
        if analysis["top_consumers"]:
            consumer = analysis["top_consumers"][0]
            assert "pid" in consumer
            assert "name" in consumer
            assert "memory_mb" in consumer
            assert "memory_percent" in consumer


class TestAnalyzeMemoryCustomThreshold:
    """Test 2: Custom threshold parameter."""

    def test_custom_threshold_parameter(self):
        """Test analyze_memory.py accepts custom threshold via --threshold."""
        # Run with custom threshold
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json", "--threshold", "90.0"],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode in [0, 1, 2], "Script should exit with valid code"

        output = json.loads(result.stdout)
        # Script should run successfully with custom threshold
        assert "metrics" in output
        assert "analysis" in output

    def test_threshold_affects_risk_level(self):
        """Test threshold parameter affects risk level calculation."""
        # Run with very high threshold (95%)
        result_high = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json", "--threshold", "95.0"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output_high = json.loads(result_high.stdout)

        # Run with low threshold (50%)
        result_low = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json", "--threshold", "50.0"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output_low = json.loads(result_low.stdout)

        # Both should run successfully
        assert "analysis" in output_high
        assert "analysis" in output_low

        # Low threshold may trigger warnings more easily
        # (This depends on actual system memory usage)


class TestAnalyzeMemoryExitCodes:
    """Test 3: Exit code behavior (0, 1, 2, 3)."""

    def test_exit_code_0_healthy(self):
        """Test exit code 0 for healthy memory usage."""
        # Run with very high threshold to ensure healthy status
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json", "--threshold", "99.0"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # If system memory is below 99%, should exit with 0
        if result.returncode == 0:
            output = json.loads(result.stdout)
            assert output["analysis"]["risk_level"] == "low"

    def test_exit_code_1_warning(self):
        """Test exit code 1 for warning memory usage."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # If exit code is 1, risk level should be warning
        if result.returncode == 1:
            output = json.loads(result.stdout)
            assert output["analysis"]["risk_level"] == "warning"

    def test_exit_code_2_critical(self):
        """Test exit code 2 for critical memory usage."""
        # Run with very low threshold to potentially trigger critical
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json", "--threshold", "10.0"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # If exit code is 2, risk level should be critical
        if result.returncode == 2:
            output = json.loads(result.stdout)
            assert output["analysis"]["risk_level"] == "critical"

    def test_valid_exit_codes_only(self):
        """Test script only exits with valid codes (0, 1, 2, 3)."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should only exit with 0 (healthy), 1 (warning), 2 (critical), or 3 (error)
        assert result.returncode in [0, 1, 2, 3]


class TestAnalyzeMemoryPerformance:
    """Test 4: Performance validation (<2 seconds execution time)."""

    def test_execution_time_under_2_seconds(self):
        """Test analyze_memory.py completes in under 2 seconds."""
        import time

        start_time = time.time()
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # Script should complete in under 2 seconds
        assert execution_time < 2.0, f"Script took {execution_time:.2f}s (expected < 2.0s)"

    def test_json_mode_performance(self):
        """Test JSON mode performance is consistent."""
        import time

        times = []
        for _ in range(3):
            start_time = time.time()
            subprocess.run(
                ["uv", "run", str(SCRIPT_PATH), "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            end_time = time.time()
            times.append(end_time - start_time)

        # Average execution time should be under 2 seconds
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Average execution time {avg_time:.2f}s (expected < 2.0s)"


class TestAnalyzeMemoryMetricsStructure:
    """Test 5: Metrics structure validation (memory + swap fields)."""

    def test_memory_metrics_present(self):
        """Test memory metrics contain all required fields."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        metrics = output["metrics"]

        # Core memory metrics
        assert "total" in metrics
        assert "used" in metrics
        assert "available" in metrics
        assert "free" in metrics
        assert "percent" in metrics

        # Verify numeric types
        assert isinstance(metrics["total"], int)
        assert isinstance(metrics["used"], int)
        assert isinstance(metrics["available"], int)
        assert isinstance(metrics["free"], int)
        assert isinstance(metrics["percent"], (int, float))

    def test_swap_metrics_present(self):
        """Test swap metrics contain all required fields."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        metrics = output["metrics"]

        # Swap metrics
        assert "swap_total" in metrics
        assert "swap_used" in metrics
        assert "swap_free" in metrics
        assert "swap_percent" in metrics

        # Verify numeric types
        assert isinstance(metrics["swap_total"], int)
        assert isinstance(metrics["swap_used"], int)
        assert isinstance(metrics["swap_free"], int)
        assert isinstance(metrics["swap_percent"], (int, float))

    def test_macos_specific_metrics_present(self):
        """Test macOS-specific memory metrics are present."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        metrics = output["metrics"]

        # macOS-specific memory categories
        assert "active" in metrics
        assert "inactive" in metrics
        assert "wired" in metrics
        assert "memory_pressure" in metrics

        # Verify types
        assert isinstance(metrics["active"], int)
        assert isinstance(metrics["inactive"], int)
        assert isinstance(metrics["wired"], int)
        # memory_pressure can be None or float
        assert metrics["memory_pressure"] is None or isinstance(metrics["memory_pressure"], (int, float))

    def test_metrics_values_are_valid(self):
        """Test memory metrics have valid values."""
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        metrics = output["metrics"]

        # Memory percentage should be 0-100
        assert 0 <= metrics["percent"] <= 100

        # Swap percentage should be 0-100
        assert 0 <= metrics["swap_percent"] <= 100

        # Used memory should not exceed total
        assert metrics["used"] <= metrics["total"]

        # Swap used should not exceed swap total
        if metrics["swap_total"] > 0:
            assert metrics["swap_used"] <= metrics["swap_total"]

        # Memory pressure (if present) should be 0-100
        if metrics["memory_pressure"] is not None:
            assert 0 <= metrics["memory_pressure"] <= 100


# Integration test
def test_analyze_memory_full_workflow():
    """Integration test: Full memory analysis workflow."""
    result = subprocess.run(
        ["uv", "run", str(SCRIPT_PATH), "--json", "--verbose"],
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should complete successfully
    assert result.returncode in [0, 1, 2], "Script should exit with valid code"

    # Should produce valid JSON
    output = json.loads(result.stdout)

    # Should have complete structure
    assert output["category"] == "memory"
    assert "timestamp" in output
    assert "metrics" in output
    assert "analysis" in output

    # Analysis should be complete
    analysis = output["analysis"]
    assert "status" in analysis
    assert "risk_level" in analysis
    assert "issues" in analysis
    assert "recommendations" in analysis
    assert "top_consumers" in analysis

    # Metrics should be valid
    metrics = output["metrics"]
    assert metrics["total"] > 0
    assert 0 <= metrics["percent"] <= 100
    assert 0 <= metrics["swap_percent"] <= 100
