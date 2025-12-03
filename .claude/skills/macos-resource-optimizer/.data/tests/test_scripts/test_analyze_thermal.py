#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for analyze_thermal.py

Comprehensive tests covering:
1. JSON output structure validation
2. Custom threshold parameter behavior
3. Exit code correctness (0/1/2)
4. Performance validation (<2s)
5. Metrics structure validation (thermal fields)
"""

import json
import subprocess
import sys
import time
from pathlib import Path
import pytest


# ============================================================================
# Test Configuration
# ============================================================================

SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "analyze_thermal.py"
PERFORMANCE_THRESHOLD = 2.0  # Maximum execution time in seconds


# ============================================================================
# Helper Functions
# ============================================================================

def run_script(args: list[str] = None, timeout: float = 10.0) -> tuple[int, str, str]:
    """
    Run the analyze_thermal.py script with given arguments.

    Args:
        args: Command line arguments (default: [])
        timeout: Maximum execution time (default: 10s)

    Returns:
        (exit_code, stdout, stderr)
    """
    if args is None:
        args = []

    cmd = ["uv", "run", str(SCRIPT_PATH)] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        pytest.fail(f"Script execution timed out after {timeout}s")


def parse_json_output(stdout: str) -> dict:
    """
    Parse JSON output from script and normalize to flat structure for test compatibility.

    Args:
        stdout: Script stdout

    Returns:
        Parsed JSON dict (normalized to flat structure for backward compatibility)

    Raises:
        ValueError: If output is not valid JSON
    """
    try:
        data = json.loads(stdout)

        # Check if this is the new wrapped format (analyze_all.py compatible)
        if "category" in data and "metrics" in data and "analysis" in data:
            # Flatten to old structure for test compatibility
            metrics = data["metrics"]
            analysis = data["analysis"]

            # Determine exit_code from risk_level
            risk_to_exit_code = {"low": 0, "medium": 1, "high": 2}
            exit_code = risk_to_exit_code.get(analysis["risk_level"], 0)

            return {
                # Metrics fields
                "cpu_temp": metrics.get("cpu_temp"),
                "gpu_temp": metrics.get("gpu_temp"),
                "avg_temp": metrics.get("avg_temp"),
                "max_temp": metrics.get("max_temp"),
                "fan_speeds": metrics.get("fan_speeds", []),
                "thermal_pressure": metrics.get("thermal_pressure"),
                "sensors_available": metrics.get("sensors_available"),
                "sensor_count": metrics.get("sensor_count"),
                "sensor_details": metrics.get("sensor_details", {}),
                "cpu_usage": metrics.get("cpu_usage"),
                "cpu_count": metrics.get("cpu_count"),
                # Analysis fields
                "risk_level": analysis.get("risk_level"),
                "exit_code": exit_code,
                "recommendations": analysis.get("recommendations", []),
                "warnings": analysis.get("warnings", []),
                # Keep wrapper fields for validation
                "_wrapped": True,
                "_category": data.get("category"),
                "_timestamp": data.get("timestamp")
            }
        else:
            # Old flat format (still supported for backward compatibility)
            return data

    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON output: {e}\nOutput: {stdout}")


# ============================================================================
# Test 1: JSON Output Structure Validation
# ============================================================================

def test_json_output_structure():
    """
    Test that JSON output contains all required thermal fields with correct types.
    """
    # Run script with --json flag
    exit_code, stdout, stderr = run_script(["--json"])

    # Parse JSON (normalizes to flat structure)
    data = parse_json_output(stdout)

    # Validate wrapper format (if present)
    if data.get("_wrapped"):
        assert data["_category"] == "thermal", "Category must be 'thermal'"
        assert isinstance(data["_timestamp"], (int, float)), "timestamp must be numeric"

    # Validate top-level structure (normalized)
    required_fields = [
        "cpu_temp",
        "gpu_temp",
        "avg_temp",
        "max_temp",
        "fan_speeds",
        "thermal_pressure",
        "sensors_available",
        "sensor_count",
        "sensor_details",
        "cpu_usage",
        "cpu_count",
        "risk_level",
        "exit_code",
        "recommendations",
        "warnings"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Validate data types
    assert isinstance(data["fan_speeds"], list), "fan_speeds must be list"
    assert isinstance(data["thermal_pressure"], str), "thermal_pressure must be string"
    assert isinstance(data["sensors_available"], bool), "sensors_available must be boolean"
    assert isinstance(data["sensor_count"], int), "sensor_count must be integer"
    assert isinstance(data["sensor_details"], dict), "sensor_details must be dict"
    assert isinstance(data["cpu_usage"], (int, float)), "cpu_usage must be numeric"
    assert isinstance(data["cpu_count"], int), "cpu_count must be integer"
    assert isinstance(data["risk_level"], str), "risk_level must be string"
    assert isinstance(data["exit_code"], int), "exit_code must be integer"
    assert isinstance(data["recommendations"], list), "recommendations must be list"
    assert isinstance(data["warnings"], list), "warnings must be list"

    # Validate value ranges
    assert data["thermal_pressure"] in ["low", "medium", "high"], \
        "thermal_pressure must be low/medium/high"
    assert data["sensor_count"] >= 0, "sensor_count must be non-negative"
    assert 0 <= data["cpu_usage"] <= 100, "cpu_usage must be 0-100"
    assert data["cpu_count"] > 0, "cpu_count must be positive"
    assert data["risk_level"] in ["low", "medium", "high"], \
        "risk_level must be low/medium/high"
    assert data["exit_code"] in [0, 1, 2], "exit_code must be 0/1/2"

    # Validate optional temperature fields
    if data["cpu_temp"] is not None:
        assert isinstance(data["cpu_temp"], (int, float)), "cpu_temp must be numeric"
        assert 0 <= data["cpu_temp"] <= 150, "cpu_temp must be 0-150�C"

    if data["gpu_temp"] is not None:
        assert isinstance(data["gpu_temp"], (int, float)), "gpu_temp must be numeric"
        assert 0 <= data["gpu_temp"] <= 150, "gpu_temp must be 0-150�C"

    if data["avg_temp"] is not None:
        assert isinstance(data["avg_temp"], (int, float)), "avg_temp must be numeric"
        assert 0 <= data["avg_temp"] <= 150, "avg_temp must be 0-150�C"

    if data["max_temp"] is not None:
        assert isinstance(data["max_temp"], (int, float)), "max_temp must be numeric"
        assert 0 <= data["max_temp"] <= 150, "max_temp must be 0-150�C"

    # Validate sensor details
    for sensor_name, temp in data["sensor_details"].items():
        assert isinstance(sensor_name, str), "Sensor name must be string"
        assert isinstance(temp, (int, float)), "Sensor temperature must be numeric"
        assert 0 <= temp <= 150, "Sensor temperature must be 0-150�C"

    # Validate fan speeds
    for rpm in data["fan_speeds"]:
        assert isinstance(rpm, int), "Fan speed must be integer"
        assert rpm >= 0, "Fan speed must be non-negative"

    print(" JSON output structure validation passed")
    print(f"  Sensors available: {data['sensors_available']}")
    print(f"  Sensor count: {data['sensor_count']}")
    print(f"  Thermal pressure: {data['thermal_pressure']}")


# ============================================================================
# Test 2: Custom Threshold Parameter
# ============================================================================

def test_custom_threshold_parameter():
    """
    Test that custom threshold affects risk level and exit code.
    """
    # Test with very low threshold (should trigger warnings if any heat)
    exit_code_low, stdout_low, _ = run_script(["--json", "--temp-warning", "40.0", "--temp-critical", "50.0"])
    data_low = parse_json_output(stdout_low)

    # Test with very high threshold (should not trigger warnings)
    exit_code_high, stdout_high, _ = run_script(["--json", "--temp-warning", "95.0", "--temp-critical", "100.0"])
    data_high = parse_json_output(stdout_high)

    # Verify threshold affects assessment (if sensors available)
    if data_low["sensors_available"] and data_low["cpu_temp"] is not None:
        # Low threshold should be more likely to trigger warnings
        assert len(data_low["warnings"]) >= len(data_high["warnings"]), \
            "Lower threshold should generate more/equal warnings"

    # High threshold should likely be low risk unless truly critical
    assert data_high["exit_code"] in [0, 1], \
        "Very high threshold (95�C) should not trigger high risk under normal conditions"

    print(f" Custom threshold validation passed")
    print(f"  Low threshold (40�C): exit_code={data_low['exit_code']}, warnings={len(data_low['warnings'])}")
    print(f"  High threshold (95�C): exit_code={data_high['exit_code']}, warnings={len(data_high['warnings'])}")


# ============================================================================
# Test 3: Exit Code Correctness
# ============================================================================

def test_exit_code_correctness():
    """
    Test that exit codes match risk levels:
    - 0: low risk (healthy)
    - 1: medium risk (warning)
    - 2: high risk (critical)
    """
    # Run script with default settings
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Exit code must match risk level
    risk_to_exit_code = {
        "low": 0,
        "medium": 1,
        "high": 2
    }

    expected_exit_code = risk_to_exit_code[data["risk_level"]]
    assert exit_code == expected_exit_code, \
        f"Exit code {exit_code} doesn't match risk level '{data['risk_level']}' (expected {expected_exit_code})"

    # Exit code must also match exit_code field in JSON
    assert exit_code == data["exit_code"], \
        f"Script exit code {exit_code} doesn't match JSON exit_code {data['exit_code']}"

    print(f" Exit code correctness validated")
    print(f"  Risk level: {data['risk_level']}")
    print(f"  Exit code: {exit_code}")
    print(f"  Thermal pressure: {data['thermal_pressure']}")
    print(f"  Sensors available: {data['sensors_available']}")


# ============================================================================
# Test 4: Performance Validation
# ============================================================================

def test_performance_under_2_seconds():
    """
    Test that script completes in under 2 seconds.

    Note: Thermal analysis should be fast as it's primarily reading sensor data.
    """
    start_time = time.time()

    exit_code, stdout, stderr = run_script(["--json"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Allow 2 seconds maximum
    max_allowed_time = PERFORMANCE_THRESHOLD

    assert execution_time < max_allowed_time, \
        f"Script execution too slow: {execution_time:.2f}s (max: {max_allowed_time}s)"

    # Verify output was generated
    data = parse_json_output(stdout)
    assert "thermal_pressure" in data, "Script must produce valid output"

    print(f" Performance validation passed")
    print(f"  Execution time: {execution_time:.2f}s")
    print(f"  Maximum allowed: {max_allowed_time}s")


# ============================================================================
# Test 5: Metrics Structure Validation
# ============================================================================

def test_metrics_structure_validation():
    """
    Test that all thermal metrics are properly structured and internally consistent.
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Validate sensor consistency
    if data["sensors_available"]:
        assert data["sensor_count"] > 0, \
            "If sensors available, count must be positive"
        assert len(data["sensor_details"]) > 0, \
            "If sensors available, sensor_details must not be empty"
        assert data["sensor_count"] == len(data["sensor_details"]), \
            "sensor_count must match sensor_details length"
    else:
        assert data["sensor_count"] == 0, \
            "If no sensors, count must be 0"
        assert len(data["sensor_details"]) == 0, \
            "If no sensors, sensor_details must be empty"

    # Validate temperature consistency
    if data["sensor_details"]:
        all_temps = list(data["sensor_details"].values())

        # Check avg_temp
        if data["avg_temp"] is not None:
            expected_avg = sum(all_temps) / len(all_temps)
            assert abs(data["avg_temp"] - expected_avg) < 0.1, \
                f"Average temperature {data['avg_temp']}�C doesn't match calculated {expected_avg:.2f}�C"

        # Check max_temp
        if data["max_temp"] is not None:
            expected_max = max(all_temps)
            assert abs(data["max_temp"] - expected_max) < 0.1, \
                f"Maximum temperature {data['max_temp']}�C doesn't match calculated {expected_max:.2f}�C"

    # Validate thermal pressure logic
    if data["max_temp"] is not None:
        if data["max_temp"] >= 80:
            assert data["thermal_pressure"] in ["medium", "high"], \
                "High temperature (>=80�C) should result in medium/high pressure"
        elif data["max_temp"] < 60:
            assert data["thermal_pressure"] in ["low", "medium"], \
                "Low temperature (<60�C) should result in low/medium pressure"

    # Validate risk level matches thresholds (default: warning=75�C, critical=85�C)
    if data["cpu_temp"] is not None:
        if data["cpu_temp"] >= 85:
            assert data["risk_level"] in ["high"], \
                "CPU temp >= 85�C should be high risk"
        elif data["cpu_temp"] >= 75:
            assert data["risk_level"] in ["medium", "high"], \
                "CPU temp >= 75�C should be medium/high risk"

    # Validate recommendations exist when there are warnings
    if len(data["warnings"]) > 0:
        assert len(data["recommendations"]) > 0, \
            "Warnings should be accompanied by recommendations"

    # Validate CPU context
    assert data["cpu_count"] > 0, "CPU count must be positive"
    assert 0 <= data["cpu_usage"] <= 100, "CPU usage must be 0-100%"

    print(f" Metrics structure validation passed")
    print(f"  Sensors available: {data['sensors_available']}")
    print(f"  Sensor count: {data['sensor_count']}")
    print(f"  Thermal pressure: {data['thermal_pressure']}")
    print(f"  CPU usage: {data['cpu_usage']}%")
    print(f"  Warnings: {len(data['warnings'])}")
    print(f"  Recommendations: {len(data['recommendations'])}")


# ============================================================================
# Additional Tests
# ============================================================================

def test_human_readable_output():
    """
    Test that human-readable output is generated correctly (without --json).
    """
    exit_code, stdout, _ = run_script([])

    # Verify output contains expected sections
    assert "Thermal Analysis Report" in stdout, "Missing report header"
    assert "Temperature Summary:" in stdout, "Missing temperature summary section"
    assert "Status:" in stdout, "Missing status"
    assert "Thermal Pressure:" in stdout, "Missing thermal pressure"

    # Verify risk level indicator
    assert "LOW RISK" in stdout or "MEDIUM RISK" in stdout or "HIGH RISK" in stdout, "Missing risk level status"

    print(f" Human-readable output validation passed")
    print(f"  Output length: {len(stdout)} characters")


def test_verbose_flag():
    """
    Test that --verbose flag produces debug output.
    """
    # Run with verbose flag
    exit_code, stdout, stderr = run_script(["--json", "--verbose"])

    # Debug output should appear in stderr
    assert "[DEBUG]" in stderr or len(stderr) > 0, \
        "Verbose flag should produce debug output"

    print(f" Verbose flag validation passed")
    print(f"  Debug output length: {len(stderr)} characters")


def test_error_handling():
    """
    Test that script handles errors gracefully.
    """
    # Test with invalid threshold
    exit_code, stdout, stderr = run_script(["--temp-warning", "invalid"])

    # Should exit with error code (Click validation error)
    assert exit_code != 0, "Invalid threshold should cause error"

    print(f" Error handling validation passed")


def test_sensor_unavailable_graceful_fallback():
    """
    Test that script handles unavailable sensors gracefully.
    """
    # Run script (may not have sensor access)
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Script should complete successfully even without sensors
    assert exit_code in [0, 1, 2], "Script should complete with valid exit code"

    # If no sensors, should have appropriate message
    if not data["sensors_available"]:
        assert "sensors not accessible" in " ".join(data["warnings"]).lower() or \
               len(data["recommendations"]) > 0, \
            "Should provide warning or recommendations when sensors unavailable"

    print(f" Sensor unavailable fallback validation passed")
    print(f"  Sensors available: {data['sensors_available']}")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    """
    Run all tests when executed directly.
    """
    print("=" * 60)
    print("Thermal Analyzer Test Suite")
    print("=" * 60)
    print()

    # Check if script exists
    if not SCRIPT_PATH.exists():
        print(f" Script not found: {SCRIPT_PATH}")
        sys.exit(1)

    # Run tests
    tests = [
        ("JSON Output Structure", test_json_output_structure),
        ("Custom Threshold Parameter", test_custom_threshold_parameter),
        ("Exit Code Correctness", test_exit_code_correctness),
        ("Performance (<2s)", test_performance_under_2_seconds),
        ("Metrics Structure Validation", test_metrics_structure_validation),
        ("Human Readable Output", test_human_readable_output),
        ("Verbose Flag", test_verbose_flag),
        ("Error Handling", test_error_handling),
        ("Sensor Unavailable Fallback", test_sensor_unavailable_graceful_fallback),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f" FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f" ERROR: {e}")
            print()
            failed += 1

    # Summary
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
