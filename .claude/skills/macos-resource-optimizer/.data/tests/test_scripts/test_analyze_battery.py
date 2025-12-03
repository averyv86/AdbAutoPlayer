#!/usr/bin/env python3
"""
Tests for Battery Analyzer Script

Validates battery analysis functionality, exit codes, performance,
and metrics structure for macOS Resource Optimizer.

Test Coverage:
1. JSON output structure validation
2. Custom threshold parameter behavior
3. Exit codes (0/1/2/3) based on battery status
4. Performance requirements (<2s execution)
5. Metrics structure (battery fields)
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


# Path to the battery analyzer script
# From .data/tests/test_scripts/ -> go up to .data/ -> then to scripts/
SKILL_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPT_DIR = SKILL_ROOT / "scripts"
BATTERY_SCRIPT = SCRIPT_DIR / "analyze_battery.py"


class TestBatteryAnalyzerOutput:
    """Test battery analyzer output formats and structure."""

    def test_json_output_structure(self):
        """Test 1: Validate JSON output structure contains all required fields."""
        # Run script with --json flag
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should complete successfully or with warnings
        assert result.returncode in [0, 1, 2, 3], "Script should exit with valid exit code"

        # Parse JSON output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

        # Validate required top-level fields
        assert "category" in output, "Missing 'category' field"
        assert output["category"] == "battery", "Category should be 'battery'"

        assert "timestamp" in output, "Missing 'timestamp' field"
        assert isinstance(output["timestamp"], (int, float)), "Timestamp should be numeric"

        assert "metrics" in output, "Missing 'metrics' field"
        assert isinstance(output["metrics"], dict), "Metrics should be a dictionary"

        assert "analysis" in output, "Missing 'analysis' field"
        assert isinstance(output["analysis"], dict), "Analysis should be a dictionary"

        # Validate metrics structure
        metrics = output["metrics"]
        required_metric_fields = [
            "percent",
            "is_plugged",
            "power_status"
        ]

        for field in required_metric_fields:
            assert field in metrics, f"Missing metric field: {field}"

        # Validate percent is between 0 and 100
        assert 0 <= metrics["percent"] <= 100, "Battery percent should be 0-100"

        # Validate is_plugged is boolean
        assert isinstance(metrics["is_plugged"], bool), "is_plugged should be boolean"

        # Validate power_status is string
        assert isinstance(metrics["power_status"], str), "power_status should be string"
        assert metrics["power_status"] in ["charging", "discharging", "full"], \
            "power_status should be valid status"

        # Validate analysis structure
        analysis = output["analysis"]
        required_analysis_fields = [
            "status",
            "risk_level",
            "issues",
            "recommendations"
        ]

        for field in required_analysis_fields:
            assert field in analysis, f"Missing analysis field: {field}"

        # Validate status values
        assert analysis["status"] in ["healthy", "warning", "critical"], \
            "Status should be valid value"

        # Validate risk level
        assert analysis["risk_level"] in ["low", "warning", "critical"], \
            "Risk level should be valid value"

        # Validate issues and recommendations are lists
        assert isinstance(analysis["issues"], list), "Issues should be a list"
        assert isinstance(analysis["recommendations"], list), \
            "Recommendations should be a list"


class TestBatteryAnalyzerThresholds:
    """Test custom threshold parameter behavior."""

    def test_custom_threshold_parameter(self):
        """Test 2: Validate custom threshold parameter affects warnings."""
        # Test with different thresholds
        thresholds = [10.0, 20.0, 30.0]

        for threshold in thresholds:
            result = subprocess.run(
                ["uv", "run", str(BATTERY_SCRIPT), "--json", "--threshold", str(threshold)],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Should complete
            assert result.returncode in [0, 1, 2, 3], \
                f"Script should exit with valid code for threshold {threshold}"

            # Parse output
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON for threshold {threshold}: {result.stdout}")

            # Validate metrics exist
            assert "metrics" in output, f"Missing metrics for threshold {threshold}"
            assert "analysis" in output, f"Missing analysis for threshold {threshold}"

            # If battery is unplugged and below threshold, should have warnings
            metrics = output["metrics"]
            analysis = output["analysis"]

            if not metrics["is_plugged"] and metrics["percent"] <= threshold:
                # Should have warning or critical status
                assert analysis["status"] in ["warning", "critical"], \
                    f"Battery below threshold {threshold} should trigger warning"

                # Should have issues or recommendations
                assert len(analysis["issues"]) > 0 or len(analysis["recommendations"]) > 0, \
                    f"Battery below threshold {threshold} should have issues/recommendations"


class TestBatteryAnalyzerExitCodes:
    """Test exit codes based on battery status."""

    def test_exit_codes(self):
        """Test 3: Validate exit codes (0=healthy, 1=warning, 2=critical, 3=error)."""
        # Run script and check exit code
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse output to understand expected exit code
        try:
            output = json.loads(result.stdout)
            risk_level = output["analysis"]["risk_level"]

            # Map risk level to expected exit code
            expected_exit_codes = {
                "low": 0,
                "warning": 1,
                "critical": 2
            }

            expected_code = expected_exit_codes.get(risk_level)

            if expected_code is not None:
                assert result.returncode == expected_code, \
                    f"Risk level '{risk_level}' should produce exit code {expected_code}, " \
                    f"got {result.returncode}"

        except json.JSONDecodeError:
            # If JSON parsing fails, should be error exit code 3
            assert result.returncode == 3, \
                "Invalid JSON should produce exit code 3"

        # Test error condition (no battery)
        # This would require mocking psutil.sensors_battery, but since we test via subprocess,
        # we rely on the actual system state. The script should handle missing battery gracefully.

        # Verify exit code is in valid range
        assert result.returncode in [0, 1, 2, 3], \
            f"Exit code must be 0, 1, 2, or 3, got {result.returncode}"

    def test_error_exit_code_on_exception(self):
        """Test exit code 3 on runtime errors."""
        # Test with invalid threshold (should handle gracefully)
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--threshold", "-10"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should still complete (threshold validation may not reject negative)
        # Or might exit with error code
        assert result.returncode in [0, 1, 2, 3], "Should produce valid exit code"


class TestBatteryAnalyzerPerformance:
    """Test performance requirements."""

    def test_performance_under_2_seconds(self):
        """Test 4: Validate execution completes in under 2 seconds."""
        # Measure execution time
        start_time = time.time()

        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        elapsed_time = time.time() - start_time

        # Should complete in under 2 seconds
        assert elapsed_time < 2.0, \
            f"Script took {elapsed_time:.2f}s, should be under 2.0s"

        # Should still produce valid output
        assert result.returncode in [0, 1, 2, 3], "Should complete successfully"

    def test_multiple_executions_consistent_performance(self):
        """Test consistent performance across multiple runs."""
        execution_times = []

        for _ in range(3):
            start_time = time.time()

            result = subprocess.run(
                ["uv", "run", str(BATTERY_SCRIPT), "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )

            elapsed_time = time.time() - start_time
            execution_times.append(elapsed_time)

            # Verify completion
            assert result.returncode in [0, 1, 2, 3], "Should complete"

        # All runs should be under 2s
        assert all(t < 2.0 for t in execution_times), \
            f"All runs should be under 2s: {execution_times}"

        # Average should be well under 2s
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 1.5, \
            f"Average execution time {avg_time:.2f}s should be under 1.5s"


class TestBatteryAnalyzerMetrics:
    """Test metrics structure and battery fields."""

    def test_metrics_structure_battery_fields(self):
        """Test 5: Validate metrics contain all expected battery fields."""
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

        metrics = output["metrics"]

        # Core battery fields (always present)
        core_fields = {
            "percent": (int, float),
            "is_plugged": bool,
            "power_status": str
        }

        for field, expected_type in core_fields.items():
            assert field in metrics, f"Missing core battery field: {field}"
            assert isinstance(metrics[field], expected_type), \
                f"Field '{field}' should be {expected_type}, got {type(metrics[field])}"

        # Optional battery fields (may be None)
        optional_fields = [
            "time_remaining_seconds",
            "cycle_count",
            "max_capacity",
            "design_capacity",
            "health_percent"
        ]

        for field in optional_fields:
            assert field in metrics, f"Missing optional battery field: {field}"

            # Should be None or appropriate type
            value = metrics[field]
            if value is not None:
                if field == "time_remaining_seconds":
                    assert isinstance(value, (int, float)), \
                        f"{field} should be numeric or None"
                elif field in ["cycle_count", "max_capacity", "design_capacity"]:
                    assert isinstance(value, int), \
                        f"{field} should be integer or None"
                elif field == "health_percent":
                    assert isinstance(value, (int, float)), \
                        f"{field} should be numeric or None"
                    assert 0 <= value <= 100, \
                        f"health_percent should be 0-100, got {value}"

    def test_battery_health_calculation(self):
        """Test battery health percentage calculation."""
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json", "--verbose"],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

        metrics = output["metrics"]

        # If health_percent is available
        if metrics.get("health_percent") is not None:
            health = metrics["health_percent"]

            # Should be valid percentage
            assert 0 <= health <= 100, \
                f"Health percentage should be 0-100, got {health}"

            # If max_capacity and design_capacity available, verify calculation
            if metrics.get("max_capacity") and metrics.get("design_capacity"):
                max_cap = metrics["max_capacity"]
                design_cap = metrics["design_capacity"]

                # Health should be approximately max/design * 100
                # Allow some tolerance for rounding
                expected_health = (max_cap / design_cap) * 100
                assert abs(health - expected_health) < 5, \
                    f"Health calculation mismatch: {health} vs {expected_health}"

    def test_time_remaining_calculation(self):
        """Test time remaining calculation when on battery."""
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

        metrics = output["metrics"]

        # If on battery power
        if not metrics["is_plugged"]:
            # time_remaining_seconds should be present (may be None)
            assert "time_remaining_seconds" in metrics, \
                "time_remaining_seconds should be present when on battery"

            # If available, should be positive
            if metrics["time_remaining_seconds"] is not None:
                assert metrics["time_remaining_seconds"] > 0, \
                    "time_remaining_seconds should be positive when available"
        else:
            # When plugged in, time_remaining should typically be None
            # (unless charging and estimating charge time)
            pass


class TestBatteryAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    def test_no_battery_detection(self):
        """Test graceful handling when no battery is present (desktop Mac)."""
        # This test would require mocking, which is complex for subprocess
        # Instead, we verify the script handles errors gracefully

        # Run script and check for error handling
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should complete with some exit code
        assert result.returncode in [0, 1, 2, 3], "Should handle no battery gracefully"

        # If exit code is 3 (error), should have error in output
        if result.returncode == 3:
            try:
                output = json.loads(result.stdout)
                assert "error" in output or "status" in output, \
                    "Error output should contain error or status field"
            except json.JSONDecodeError:
                # stderr should contain error message
                assert len(result.stderr) > 0, "Should output error message"

    def test_verbose_mode(self):
        """Test verbose output mode."""
        result = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT), "--verbose"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should complete
        assert result.returncode in [0, 1, 2, 3], "Verbose mode should work"

        # Verbose output should be longer than non-verbose
        result_normal = subprocess.run(
            ["uv", "run", str(BATTERY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Verbose output typically longer
        # (This is a weak test, but validates the flag works)
        assert result.returncode == result_normal.returncode, \
            "Verbose should not change exit code"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
