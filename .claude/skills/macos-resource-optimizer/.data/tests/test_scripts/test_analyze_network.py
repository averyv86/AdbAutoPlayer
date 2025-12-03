#!/usr/bin/env python3
"""
Test Suite for analyze_network.py

Comprehensive tests covering:
1. JSON output structure validation
2. Custom threshold parameter behavior
3. Exit code correctness (0/1/2)
4. Performance validation (<2s)
5. Metrics structure validation (network + connection fields)
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

SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "analyze_network.py"
PERFORMANCE_THRESHOLD = 2.0  # Maximum execution time in seconds (excluding sampling time)


# ============================================================================
# Helper Functions
# ============================================================================

def run_script(args: list[str] = None, timeout: float = 15.0) -> tuple[int, str, str]:
    """
    Run the analyze_network.py script with given arguments.

    Args:
        args: Command line arguments (default: [])
        timeout: Maximum execution time (default: 15s to account for sampling)

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
        "bytes_sent",
        "bytes_received",
        "packets_sent",
        "packets_received",
        "errors_in",
        "errors_out",
        "drops_in",
        "drops_out",
        "connection_count",
        "established_count",
        "listening_count",
        "time_wait_count",
        "close_wait_count",
        "bandwidth_usage_mb",
        "bytes_sent_per_sec",
        "bytes_received_per_sec",
        "error_rate_pct",
        "drop_rate_pct",
        "top_connections",
        "risk_level",
        "exit_code",
        "recommendations",
        "warnings"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Validate data types
    assert isinstance(data["bytes_sent"], int), "bytes_sent must be integer"
    assert isinstance(data["bytes_received"], int), "bytes_received must be integer"
    assert isinstance(data["packets_sent"], int), "packets_sent must be integer"
    assert isinstance(data["packets_received"], int), "packets_received must be integer"
    assert isinstance(data["errors_in"], int), "errors_in must be integer"
    assert isinstance(data["errors_out"], int), "errors_out must be integer"
    assert isinstance(data["drops_in"], int), "drops_in must be integer"
    assert isinstance(data["drops_out"], int), "drops_out must be integer"
    assert isinstance(data["connection_count"], int), "connection_count must be integer"
    assert isinstance(data["established_count"], int), "established_count must be integer"
    assert isinstance(data["listening_count"], int), "listening_count must be integer"
    assert isinstance(data["time_wait_count"], int), "time_wait_count must be integer"
    assert isinstance(data["close_wait_count"], int), "close_wait_count must be integer"
    assert isinstance(data["bandwidth_usage_mb"], (int, float)), "bandwidth_usage_mb must be numeric"
    assert isinstance(data["bytes_sent_per_sec"], (int, float)), "bytes_sent_per_sec must be numeric"
    assert isinstance(data["bytes_received_per_sec"], (int, float)), "bytes_received_per_sec must be numeric"
    assert isinstance(data["error_rate_pct"], (int, float)), "error_rate_pct must be numeric"
    assert isinstance(data["drop_rate_pct"], (int, float)), "drop_rate_pct must be numeric"
    assert isinstance(data["top_connections"], list), "top_connections must be list"
    assert isinstance(data["risk_level"], str), "risk_level must be string"
    assert isinstance(data["exit_code"], int), "exit_code must be integer"
    assert isinstance(data["recommendations"], list), "recommendations must be list"
    assert isinstance(data["warnings"], list), "warnings must be list"

    # Validate value ranges
    assert data["bytes_sent"] >= 0, "bytes_sent must be non-negative"
    assert data["bytes_received"] >= 0, "bytes_received must be non-negative"
    assert data["packets_sent"] >= 0, "packets_sent must be non-negative"
    assert data["packets_received"] >= 0, "packets_received must be non-negative"
    assert data["connection_count"] >= 0, "connection_count must be non-negative"
    assert data["bandwidth_usage_mb"] >= 0, "bandwidth_usage_mb must be non-negative"
    assert data["risk_level"] in ["low", "medium", "high"], "risk_level must be low/medium/high"
    assert data["exit_code"] in [0, 1, 2], "exit_code must be 0/1/2"

    # Validate connection counts consistency
    total_conn = data["connection_count"]
    assert data["established_count"] <= total_conn, "established_count cannot exceed total"
    assert data["listening_count"] <= total_conn, "listening_count cannot exceed total"
    assert data["time_wait_count"] <= total_conn, "time_wait_count cannot exceed total"
    assert data["close_wait_count"] <= total_conn, "close_wait_count cannot exceed total"

    # Validate top connections structure
    for conn in data["top_connections"]:
        assert "name" in conn, "Connection must have name"
        assert "pid" in conn, "Connection must have pid"
        assert "connections" in conn, "Connection must have connections count"
        assert "established" in conn, "Connection must have established count"

    print("✓ JSON output structure validation passed")


# ============================================================================
# Test 2: Custom Threshold Parameter
# ============================================================================

def test_custom_threshold_parameter():
    """
    Test that custom connection threshold affects risk level and exit code.
    """
    # Test with very low connection threshold (should trigger warnings)
    exit_code_low, stdout_low, _ = run_script(["--json", "--connection-threshold", "10"])
    data_low = parse_json_output(stdout_low)

    # Test with very high connection threshold (should not trigger warnings)
    exit_code_high, stdout_high, _ = run_script(["--json", "--connection-threshold", "10000"])
    data_high = parse_json_output(stdout_high)

    # Verify both runs completed
    assert data_low["exit_code"] in [0, 1, 2], "Low threshold must return valid exit code"
    assert data_high["exit_code"] in [0, 1, 2], "High threshold must return valid exit code"

    # Low threshold should likely trigger warnings if there are any connections
    if data_low["connection_count"] > 10:
        assert data_low["exit_code"] in [1, 2], "Low threshold (10) should trigger warnings with many connections"

    # High threshold should likely be low risk
    assert data_high["exit_code"] in [0, 1], "High threshold (10000) should not trigger high risk"

    print(f"✓ Custom threshold validation passed")
    print(f"  Low threshold (10): exit_code={data_low['exit_code']}, connections={data_low['connection_count']}")
    print(f"  High threshold (10000): exit_code={data_high['exit_code']}, connections={data_high['connection_count']}")


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
    print(f"  Bandwidth usage: {data['bandwidth_usage_mb']:.2f} MB/s")
    print(f"  Connection count: {data['connection_count']}")


# ============================================================================
# Test 4: Performance Validation
# ============================================================================

def test_performance_under_2_seconds():
    """
    Test that script completes in reasonable time.

    Note: The script samples network I/O over ~2 seconds (SAMPLE_INTERVAL),
    so we allow up to 5 seconds total execution time.
    """
    start_time = time.time()

    exit_code, stdout, stderr = run_script(["--json"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Allow 5 seconds total (includes sampling time)
    max_allowed_time = 5.0

    assert execution_time < max_allowed_time, \
        f"Script execution too slow: {execution_time:.2f}s (max: {max_allowed_time}s)"

    # Verify output was generated
    data = parse_json_output(stdout)
    assert "bandwidth_usage_mb" in data, "Script must produce valid output"

    print(f"✓ Performance validation passed")
    print(f"  Execution time: {execution_time:.2f}s")
    print(f"  Maximum allowed: {max_allowed_time}s")


# ============================================================================
# Test 5: Metrics Structure Validation
# ============================================================================

def test_metrics_structure_validation():
    """
    Test that network and connection metrics are properly structured and internally consistent.
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Validate network I/O metrics
    assert data["bytes_sent"] >= 0, "bytes_sent must be non-negative"
    assert data["bytes_received"] >= 0, "bytes_received must be non-negative"
    assert data["packets_sent"] >= 0, "packets_sent must be non-negative"
    assert data["packets_received"] >= 0, "packets_received must be non-negative"

    # Validate error/drop metrics
    assert data["errors_in"] >= 0, "errors_in must be non-negative"
    assert data["errors_out"] >= 0, "errors_out must be non-negative"
    assert data["drops_in"] >= 0, "drops_in must be non-negative"
    assert data["drops_out"] >= 0, "drops_out must be non-negative"

    # Validate connection metrics
    assert data["connection_count"] >= 0, "connection_count must be non-negative"
    assert data["established_count"] >= 0, "established_count must be non-negative"
    assert data["listening_count"] >= 0, "listening_count must be non-negative"
    assert data["time_wait_count"] >= 0, "time_wait_count must be non-negative"
    assert data["close_wait_count"] >= 0, "close_wait_count must be non-negative"

    # Validate bandwidth metrics
    assert data["bandwidth_usage_mb"] >= 0, "bandwidth_usage_mb must be non-negative"
    assert data["bytes_sent_per_sec"] >= 0, "bytes_sent_per_sec must be non-negative"
    assert data["bytes_received_per_sec"] >= 0, "bytes_received_per_sec must be non-negative"

    # Validate quality metrics
    assert 0 <= data["error_rate_pct"] <= 100, "error_rate_pct must be 0-100%"
    assert 0 <= data["drop_rate_pct"] <= 100, "drop_rate_pct must be 0-100%"

    # Validate connection count consistency
    total_conn = data["connection_count"]
    established = data["established_count"]
    listening = data["listening_count"]
    time_wait = data["time_wait_count"]
    close_wait = data["close_wait_count"]

    assert established <= total_conn, "established_count cannot exceed total"
    assert listening <= total_conn, "listening_count cannot exceed total"

    # Validate top connections structure
    for conn in data["top_connections"]:
        assert conn["connections"] > 0, "Connection count must be positive"
        assert conn["established"] >= 0, "Established count must be non-negative"
        assert conn["established"] <= conn["connections"], "Established cannot exceed total connections"

    # Validate risk level consistency
    if data["bandwidth_usage_mb"] >= 100 or data["connection_count"] >= 1000:
        assert data["risk_level"] in ["medium", "high"], "High bandwidth/connections should trigger warnings"

    # Validate recommendations exist when there are warnings
    if len(data["warnings"]) > 0:
        assert len(data["recommendations"]) > 0, \
            "Warnings should be accompanied by recommendations"

    print(f"✓ Metrics structure validation passed")
    print(f"  Bandwidth: {data['bandwidth_usage_mb']:.2f} MB/s")
    print(f"  Total connections: {data['connection_count']}")
    print(f"  Established: {data['established_count']}")
    print(f"  Listening: {data['listening_count']}")
    print(f"  Error rate: {data['error_rate_pct']:.4f}%")
    print(f"  Drop rate: {data['drop_rate_pct']:.4f}%")
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
    assert "Network Analysis Report" in stdout, "Missing report header"
    assert "Network I/O:" in stdout, "Missing network I/O section"
    assert "Bandwidth Usage:" in stdout, "Missing bandwidth section"
    assert "Connections:" in stdout, "Missing connections section"
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
    # Test with invalid connection threshold
    exit_code, stdout, stderr = run_script(["--connection-threshold", "invalid"])

    # Should exit with error code 2 (Click validation error)
    assert exit_code != 0, "Invalid threshold should cause error"

    print(f"✓ Error handling validation passed")


def test_analyze_all_compatibility():
    """
    Test that JSON output format is compatible with analyze_all.py wrapper structure.

    Expected structure:
    {
        "category": "network",
        "timestamp": <float>,
        "metrics": { ... all metric fields ... },
        "analysis": {
            "status": "healthy" | "warning" | "critical",
            "risk_level": "low" | "medium" | "high",
            "recommendations": [...],
            "warnings": [...]
        }
    }
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    # Validate wrapper structure
    assert "category" in data, "Missing 'category' field"
    assert data["category"] == "network", "Category must be 'network'"

    assert "timestamp" in data, "Missing 'timestamp' field"
    assert isinstance(data["timestamp"], (int, float)), "Timestamp must be numeric"

    assert "metrics" in data, "Missing 'metrics' field"
    assert isinstance(data["metrics"], dict), "Metrics must be a dict"

    assert "analysis" in data, "Missing 'analysis' field"
    assert isinstance(data["analysis"], dict), "Analysis must be a dict"

    # Validate metrics content
    metrics = data["metrics"]
    required_metric_fields = [
        "bytes_sent", "bytes_received", "packets_sent", "packets_received",
        "errors_in", "errors_out", "drops_in", "drops_out",
        "connection_count", "established_count", "listening_count",
        "time_wait_count", "close_wait_count",
        "bandwidth_usage_mb", "bytes_sent_per_sec", "bytes_received_per_sec",
        "error_rate_pct", "drop_rate_pct", "top_connections"
    ]

    for field in required_metric_fields:
        assert field in metrics, f"Missing metric field: {field}"

    # Validate analysis content
    analysis = data["analysis"]
    assert "status" in analysis, "Missing 'status' in analysis"
    assert "risk_level" in analysis, "Missing 'risk_level' in analysis"
    assert "recommendations" in analysis, "Missing 'recommendations' in analysis"
    assert "warnings" in analysis, "Missing 'warnings' in analysis"

    # Validate status values
    assert analysis["status"] in ["healthy", "warning", "critical"], \
        f"Invalid status: {analysis['status']}"
    assert analysis["risk_level"] in ["low", "medium", "high"], \
        f"Invalid risk_level: {analysis['risk_level']}"

    # Validate status mapping from risk_level
    status_mapping = {
        "low": "healthy",
        "medium": "warning",
        "high": "critical"
    }
    expected_status = status_mapping[analysis["risk_level"]]
    assert analysis["status"] == expected_status, \
        f"Status mapping incorrect: {analysis['status']} != {expected_status} for risk_level '{analysis['risk_level']}'"

    # Validate recommendations and warnings are lists
    assert isinstance(analysis["recommendations"], list), "Recommendations must be a list"
    assert isinstance(analysis["warnings"], list), "Warnings must be a list"

    print(f"✓ analyze_all.py compatibility validation passed")
    print(f"  Category: {data['category']}")
    print(f"  Status: {analysis['status']} (risk: {analysis['risk_level']})")
    print(f"  Metrics count: {len(metrics)}")
    print(f"  Recommendations: {len(analysis['recommendations'])}")
    print(f"  Warnings: {len(analysis['warnings'])}")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    """
    Run all tests when executed directly.
    """
    print("=" * 60)
    print("Network Analyzer Test Suite")
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
        ("Performance (<5s)", test_performance_under_2_seconds),
        ("Metrics Structure Validation", test_metrics_structure_validation),
        ("Human Readable Output", test_human_readable_output),
        ("Verbose Flag", test_verbose_flag),
        ("Error Handling", test_error_handling),
        ("analyze_all.py Compatibility", test_analyze_all_compatibility),
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
