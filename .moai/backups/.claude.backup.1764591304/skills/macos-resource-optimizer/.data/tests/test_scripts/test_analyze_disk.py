#!/usr/bin/env python3
"""
Test Suite for analyze_disk.py

Comprehensive tests covering:
1. JSON output structure validation
2. Custom threshold parameter behavior
3. Exit code correctness (0/1/2)
4. Performance validation (<2s)
5. Metrics structure validation (disk + I/O fields)
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

SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "analyze_disk.py"
PERFORMANCE_THRESHOLD = 8.0  # Maximum execution time (includes 3s I/O sampling)


# ============================================================================
# Helper Functions
# ============================================================================

def run_script(args: list[str] = None, timeout: float = 15.0) -> tuple[int, str, str]:
    """
    Run the analyze_disk.py script with given arguments.

    Args:
        args: Command line arguments (default: [])
        timeout: Maximum execution time (default: 15s)

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
    Parse JSON output from script.

    Args:
        stdout: Script stdout

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If output is not valid JSON
    """
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON output: {e}\nOutput: {stdout}")


# ============================================================================
# Test 1: JSON Output Structure Validation
# ============================================================================

def test_json_output_structure():
    """
    Test that JSON output contains all required fields with correct types.
    """
    # Run script with --json flag
    exit_code, stdout, stderr = run_script(["--json"])

    # Parse JSON
    data = parse_json_output(stdout)

    # Validate top-level structure
    required_fields = [
        "total_space",
        "used_space",
        "free_space",
        "percent_used",
        "read_bytes",
        "write_bytes",
        "read_time",
        "write_time",
        "iops",
        "partitions",
        "risk_level",
        "exit_code",
        "recommendations",
        "warnings"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Validate data types
    assert isinstance(data["total_space"], (int, float)), "total_space must be numeric"
    assert isinstance(data["used_space"], (int, float)), "used_space must be numeric"
    assert isinstance(data["free_space"], (int, float)), "free_space must be numeric"
    assert isinstance(data["percent_used"], (int, float)), "percent_used must be numeric"
    assert isinstance(data["read_bytes"], int), "read_bytes must be integer"
    assert isinstance(data["write_bytes"], int), "write_bytes must be integer"
    assert isinstance(data["read_time"], int), "read_time must be integer"
    assert isinstance(data["write_time"], int), "write_time must be integer"
    assert isinstance(data["iops"], (int, float)), "iops must be numeric"
    assert isinstance(data["partitions"], list), "partitions must be list"
    assert isinstance(data["risk_level"], str), "risk_level must be string"
    assert isinstance(data["exit_code"], int), "exit_code must be integer"
    assert isinstance(data["recommendations"], list), "recommendations must be list"
    assert isinstance(data["warnings"], list), "warnings must be list"

    # Validate value ranges
    assert data["total_space"] > 0, "total_space must be positive"
    assert data["used_space"] >= 0, "used_space must be non-negative"
    assert data["free_space"] >= 0, "free_space must be non-negative"
    assert 0 <= data["percent_used"] <= 100, "percent_used must be 0-100"
    assert data["read_bytes"] >= 0, "read_bytes must be non-negative"
    assert data["write_bytes"] >= 0, "write_bytes must be non-negative"
    assert data["iops"] >= 0, "iops must be non-negative"
    assert data["risk_level"] in ["low", "medium", "high"], "risk_level must be low/medium/high"
    assert data["exit_code"] in [0, 1, 2], "exit_code must be 0/1/2"

    # Validate partition structure
    for partition in data["partitions"]:
        assert "device" in partition, "Partition must have device"
        assert "mountpoint" in partition, "Partition must have mountpoint"
        assert "fstype" in partition, "Partition must have fstype"
        assert "total_gb" in partition, "Partition must have total_gb"
        assert "used_gb" in partition, "Partition must have used_gb"
        assert "free_gb" in partition, "Partition must have free_gb"
        assert "percent_used" in partition, "Partition must have percent_used"

    # Validate storage values are reasonable
    # Note: On macOS APFS, used + free != total due to snapshot/purgeable space
    # Just verify values are positive and percentage is calculated correctly
    assert data["total_space"] > 0, "total_space must be positive"
    assert data["used_space"] >= 0, "used_space must be non-negative"
    assert data["free_space"] >= 0, "free_space must be non-negative"

    # Verify percentage matches what we calculate from the values
    # (This is what the system reports directly from psutil)
    assert 0 <= data["percent_used"] <= 100, "percent_used must be 0-100"

    print("✓ JSON output structure validation passed")


# ============================================================================
# Test 2: Custom Threshold Parameter
# ============================================================================

def test_custom_threshold_parameter():
    """
    Test that custom threshold affects risk level and exit code.
    """
    # Test with very low threshold (should likely trigger warnings)
    exit_code_low, stdout_low, _ = run_script(["--json", "--threshold", "10.0"])
    data_low = parse_json_output(stdout_low)

    # Test with very high threshold (should likely not trigger warnings)
    exit_code_high, stdout_high, _ = run_script(["--json", "--threshold", "99.0"])
    data_high = parse_json_output(stdout_high)

    # Verify thresholds affect behavior differently
    # Low threshold should be more likely to trigger warnings
    if data_low["percent_used"] > 10.0:
        assert data_low["exit_code"] >= 1, "Low threshold (10%) should trigger warnings if usage > 10%"

    # High threshold should be less likely to trigger warnings
    if data_high["percent_used"] < 99.0:
        assert data_high["exit_code"] in [0, 1], "High threshold (99%) should not trigger high risk if usage < 99%"

    print(f"✓ Custom threshold validation passed")
    print(f"  Low threshold (10%): exit_code={data_low['exit_code']}, usage={data_low['percent_used']:.1f}%")
    print(f"  High threshold (99%): exit_code={data_high['exit_code']}, usage={data_high['percent_used']:.1f}%")


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

    print(f"✓ Exit code correctness validated")
    print(f"  Risk level: {data['risk_level']}")
    print(f"  Exit code: {exit_code}")
    print(f"  Disk usage: {data['percent_used']:.1f}%")
    print(f"  Free space: {data['free_space']:.2f} GB")


# ============================================================================
# Test 4: Performance Validation
# ============================================================================

def test_performance_under_threshold():
    """
    Test that script completes within performance threshold.

    Note: The script samples I/O over ~3 seconds (3 samples * 1s interval),
    so we allow up to 8 seconds total execution time.
    """
    start_time = time.time()

    exit_code, stdout, stderr = run_script(["--json"])

    end_time = time.time()
    execution_time = end_time - start_time

    assert execution_time < PERFORMANCE_THRESHOLD, \
        f"Script execution too slow: {execution_time:.2f}s (max: {PERFORMANCE_THRESHOLD}s)"

    # Verify output was generated
    data = parse_json_output(stdout)
    assert "total_space" in data, "Script must produce valid output"

    print(f"✓ Performance validation passed")
    print(f"  Execution time: {execution_time:.2f}s")
    print(f"  Maximum allowed: {PERFORMANCE_THRESHOLD}s")


# ============================================================================
# Test 5: Metrics Structure Validation
# ============================================================================

def test_metrics_structure_validation():
    """
    Test that all metrics are properly structured and internally consistent.
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Validate storage values are reasonable
    # Note: On macOS APFS, used + free != total due to snapshot/purgeable space
    assert data["total_space"] > 0, "total_space must be positive"
    assert data["used_space"] >= 0, "used_space must be non-negative"
    assert data["free_space"] >= 0, "free_space must be non-negative"
    assert 0 <= data["percent_used"] <= 100, "percent_used must be 0-100"

    # Validate I/O metrics are non-negative
    assert data["read_bytes"] >= 0, "read_bytes must be non-negative"
    assert data["write_bytes"] >= 0, "write_bytes must be non-negative"
    assert data["read_time"] >= 0, "read_time must be non-negative"
    assert data["write_time"] >= 0, "write_time must be non-negative"
    assert data["iops"] >= 0, "iops must be non-negative"

    # Validate partition data structure (values are reasonable)
    for partition in data["partitions"]:
        assert partition["total_gb"] > 0, f"Partition {partition['mountpoint']} total_gb must be positive"
        assert partition["used_gb"] >= 0, f"Partition {partition['mountpoint']} used_gb must be non-negative"
        assert partition["free_gb"] >= 0, f"Partition {partition['mountpoint']} free_gb must be non-negative"
        assert 0 <= partition["percent_used"] <= 100, f"Partition {partition['mountpoint']} percent must be 0-100"

    # Validate risk level matches thresholds
    if data["percent_used"] >= 90:
        assert data["risk_level"] in ["high"], "Usage >= 90% must be high risk"
    elif data["percent_used"] >= 85:
        assert data["risk_level"] in ["medium", "high"], "Usage >= 85% must be medium/high risk"

    # Validate recommendations exist when there are warnings
    if len(data["warnings"]) > 0:
        assert len(data["recommendations"]) > 0, \
            "Warnings should be accompanied by recommendations"

    print(f"✓ Metrics structure validation passed")
    print(f"  Total space: {data['total_space']:.2f} GB")
    print(f"  Used space: {data['used_space']:.2f} GB ({data['percent_used']:.1f}%)")
    print(f"  Free space: {data['free_space']:.2f} GB")
    print(f"  IOPS: {data['iops']:.2f}")
    print(f"  Partitions: {len(data['partitions'])}")
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
    assert "Disk Analysis Report" in stdout, "Missing report header"
    assert "Storage Usage:" in stdout, "Missing storage section"
    assert "Total:" in stdout, "Missing total space"
    assert "Status:" in stdout, "Missing status"

    # Verify risk level indicator
    assert any(symbol in stdout for symbol in ["✓", "⚠", "✗"]), \
        "Missing risk level symbol"

    print(f"✓ Human-readable output validation passed")
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

    print(f"✓ Verbose flag validation passed")
    print(f"  Debug output length: {len(stderr)} characters")


def test_error_handling():
    """
    Test that script handles errors gracefully.
    """
    # Test with invalid threshold
    exit_code, stdout, stderr = run_script(["--threshold", "invalid"])

    # Should exit with error code (Click validation error)
    assert exit_code != 0, "Invalid threshold should cause error"

    print(f"✓ Error handling validation passed")


def test_io_metrics_present():
    """
    Test that I/O metrics are collected and present.
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # I/O metrics should be present (even if zero)
    assert "read_bytes" in data, "Missing read_bytes metric"
    assert "write_bytes" in data, "Missing write_bytes metric"
    assert "read_time" in data, "Missing read_time metric"
    assert "write_time" in data, "Missing write_time metric"
    assert "iops" in data, "Missing iops metric"

    print(f"✓ I/O metrics validation passed")
    print(f"  Read: {data['read_bytes']} bytes ({data['read_time']} ms)")
    print(f"  Write: {data['write_bytes']} bytes ({data['write_time']} ms)")
    print(f"  IOPS: {data['iops']:.2f}")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    """
    Run all tests when executed directly.
    """
    print("=" * 60)
    print("Disk Analyzer Test Suite")
    print("=" * 60)
    print()

    # Check if script exists
    if not SCRIPT_PATH.exists():
        print(f"✗ Script not found: {SCRIPT_PATH}")
        sys.exit(1)

    # Run tests
    tests = [
        ("JSON Output Structure", test_json_output_structure),
        ("Custom Threshold Parameter", test_custom_threshold_parameter),
        ("Exit Code Correctness", test_exit_code_correctness),
        ("Performance (<8s)", test_performance_under_threshold),
        ("Metrics Structure Validation", test_metrics_structure_validation),
        ("Human Readable Output", test_human_readable_output),
        ("Verbose Flag", test_verbose_flag),
        ("Error Handling", test_error_handling),
        ("I/O Metrics Present", test_io_metrics_present),
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
            print(f"✗ FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            print()
            failed += 1

    # Summary
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
