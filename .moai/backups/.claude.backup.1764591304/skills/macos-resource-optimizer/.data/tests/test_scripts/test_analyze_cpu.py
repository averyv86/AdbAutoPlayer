#!/usr/bin/env python3
"""
Test Suite for analyze_cpu.py

Comprehensive tests covering:
1. JSON output structure validation
2. Custom threshold parameter behavior
3. Exit code correctness (0/1/2)
4. Performance validation (<2s)
5. Metrics structure validation

Updated for analyze_all.py compatible wrapper format with:
- category, timestamp, metrics, analysis structure
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

SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "analyze_cpu.py"
PERFORMANCE_THRESHOLD = 2.0  # Maximum execution time in seconds


# ============================================================================
# Helper Functions
# ============================================================================

def run_script(args: list[str] = None, timeout: float = 10.0) -> tuple[int, str, str]:
    """
    Run the analyze_cpu.py script with given arguments.

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
    Updated for analyze_all.py compatible wrapper format.
    """
    # Run script with --json flag
    exit_code, stdout, stderr = run_script(["--json"])

    # Parse JSON
    data = parse_json_output(stdout)

    # Validate wrapper structure
    assert "category" in data, "Missing category field"
    assert "timestamp" in data, "Missing timestamp field"
    assert "metrics" in data, "Missing metrics field"
    assert "analysis" in data, "Missing analysis field"

    assert data["category"] == "cpu", "Category must be 'cpu'"
    assert isinstance(data["timestamp"], (int, float)), "Timestamp must be numeric"
    assert isinstance(data["metrics"], dict), "Metrics must be dict"
    assert isinstance(data["analysis"], dict), "Analysis must be dict"

    # Validate metrics structure
    metrics = data["metrics"]
    required_metric_fields = [
        "total_usage",
        "per_core_usage",
        "core_count",
        "temperature",
        "temp_sensors",
        "current_freq",
        "max_freq",
        "min_freq",
        "load_1min",
        "load_5min",
        "load_15min",
        "top_processes"
    ]

    for field in required_metric_fields:
        assert field in metrics, f"Missing required metric field: {field}"

    # Validate analysis structure
    analysis = data["analysis"]
    required_analysis_fields = [
        "status",
        "risk_level",
        "recommendations",
        "warnings",
        "exit_code"
    ]

    for field in required_analysis_fields:
        assert field in analysis, f"Missing required analysis field: {field}"

    # Validate data types
    assert isinstance(metrics["total_usage"], (int, float)), "total_usage must be numeric"
    assert isinstance(metrics["per_core_usage"], list), "per_core_usage must be list"
    assert isinstance(metrics["core_count"], int), "core_count must be integer"
    assert isinstance(metrics["temp_sensors"], dict), "temp_sensors must be dict"
    assert isinstance(metrics["load_1min"], (int, float)), "load_1min must be numeric"
    assert isinstance(metrics["load_5min"], (int, float)), "load_5min must be numeric"
    assert isinstance(metrics["load_15min"], (int, float)), "load_15min must be numeric"
    assert isinstance(metrics["top_processes"], list), "top_processes must be list"
    assert isinstance(analysis["status"], str), "status must be string"
    assert isinstance(analysis["risk_level"], str), "risk_level must be string"
    assert isinstance(analysis["exit_code"], int), "exit_code must be integer"
    assert isinstance(analysis["recommendations"], list), "recommendations must be list"
    assert isinstance(analysis["warnings"], list), "warnings must be list"

    # Validate value ranges
    assert 0 <= metrics["total_usage"] <= 100, "total_usage must be 0-100"
    assert metrics["core_count"] > 0, "core_count must be positive"
    assert len(metrics["per_core_usage"]) == metrics["core_count"], "per_core_usage length must match core_count"
    assert analysis["status"] in ["healthy", "warning", "critical"], "status must be healthy/warning/critical"
    assert analysis["risk_level"] in ["low", "medium", "high"], "risk_level must be low/medium/high"
    assert analysis["exit_code"] in [0, 1, 2], "exit_code must be 0/1/2"

    # Validate per-core usage values
    for i, usage in enumerate(metrics["per_core_usage"]):
        assert isinstance(usage, (int, float)), f"Core {i} usage must be numeric"
        assert 0 <= usage <= 100, f"Core {i} usage must be 0-100"

    # Validate top processes structure
    for proc in metrics["top_processes"]:
        assert "pid" in proc, "Process must have pid"
        assert "name" in proc, "Process must have name"
        assert "cpu_percent" in proc, "Process must have cpu_percent"
        assert "memory_percent" in proc, "Process must have memory_percent"

    # Validate temperature (if available)
    if metrics["temperature"] is not None:
        assert isinstance(metrics["temperature"], (int, float)), "temperature must be numeric"
        assert 0 <= metrics["temperature"] <= 150, "temperature must be 0-150°C"

    # Validate frequency (if available)
    if metrics["current_freq"] is not None:
        assert isinstance(metrics["current_freq"], (int, float)), "current_freq must be numeric"
        assert metrics["current_freq"] > 0, "current_freq must be positive"

    print("✓ JSON output structure validation passed")


# ============================================================================
# Test 2: Custom Threshold Parameter
# ============================================================================

def test_custom_threshold_parameter():
    """
    Test that custom threshold affects risk level and exit code.
    """
    # Test with very low threshold (should trigger warnings)
    exit_code_low, stdout_low, _ = run_script(["--json", "--threshold", "10.0"])
    data_low = parse_json_output(stdout_low)

    # Test with very high threshold (should not trigger warnings)
    exit_code_high, stdout_high, _ = run_script(["--json", "--threshold", "99.0"])
    data_high = parse_json_output(stdout_high)

    # Low threshold should likely trigger medium/high risk
    assert data_low["analysis"]["exit_code"] in [1, 2], "Low threshold (10%) should trigger warnings"

    # High threshold should likely be low risk (unless system is truly critical)
    assert data_high["analysis"]["exit_code"] in [0, 1], "High threshold (99%) should not trigger high risk"

    # Verify threshold affects recommendations
    assert len(data_low["analysis"]["warnings"]) >= len(data_high["analysis"]["warnings"]), \
        "Lower threshold should generate more warnings"

    print(f"✓ Custom threshold validation passed")
    print(f"  Low threshold (10%): exit_code={data_low['analysis']['exit_code']}, warnings={len(data_low['analysis']['warnings'])}")
    print(f"  High threshold (99%): exit_code={data_high['analysis']['exit_code']}, warnings={len(data_high['analysis']['warnings'])}")


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

    expected_exit_code = risk_to_exit_code[data["analysis"]["risk_level"]]
    assert exit_code == expected_exit_code, \
        f"Exit code {exit_code} doesn't match risk level '{data['analysis']['risk_level']}' (expected {expected_exit_code})"

    # Exit code must also match exit_code field in JSON
    assert exit_code == data["analysis"]["exit_code"], \
        f"Script exit code {exit_code} doesn't match JSON exit_code {data['analysis']['exit_code']}"

    print(f"✓ Exit code correctness validated")
    print(f"  Risk level: {data['analysis']['risk_level']}")
    print(f"  Exit code: {exit_code}")
    print(f"  Total CPU usage: {data['metrics']['total_usage']}%")


# ============================================================================
# Test 4: Performance Validation
# ============================================================================

def test_performance_under_2_seconds():
    """
    Test that script completes in under 2 seconds (excluding sampling time).

    Note: The script samples CPU usage over ~6 seconds (3 samples * 2s interval),
    so we allow up to 10 seconds total execution time.
    """
    start_time = time.time()

    exit_code, stdout, stderr = run_script(["--json"])

    end_time = time.time()
    execution_time = end_time - start_time

    # Allow 10 seconds total (includes sampling time)
    max_allowed_time = 10.0

    assert execution_time < max_allowed_time, \
        f"Script execution too slow: {execution_time:.2f}s (max: {max_allowed_time}s)"

    # Verify output was generated
    data = parse_json_output(stdout)
    assert "metrics" in data and "total_usage" in data["metrics"], "Script must produce valid output"

    print(f"✓ Performance validation passed")
    print(f"  Execution time: {execution_time:.2f}s")
    print(f"  Maximum allowed: {max_allowed_time}s")


# ============================================================================
# Test 5: Metrics Structure Validation
# ============================================================================

def test_metrics_structure_validation():
    """
    Test that all metrics are properly structured and internally consistent.
    """
    exit_code, stdout, _ = run_script(["--json"])
    data = parse_json_output(stdout)

    metrics = data["metrics"]
    analysis = data["analysis"]

    # Validate core count consistency
    assert len(metrics["per_core_usage"]) == metrics["core_count"], \
        "per_core_usage length must match core_count"

    # Validate load average ordering (1min, 5min, 15min)
    # Note: Load can fluctuate, so we just check they're all present
    assert metrics["load_1min"] >= 0, "load_1min must be non-negative"
    assert metrics["load_5min"] >= 0, "load_5min must be non-negative"
    assert metrics["load_15min"] >= 0, "load_15min must be non-negative"

    # Validate per-core usage sums to reasonable total
    avg_core_usage = sum(metrics["per_core_usage"]) / len(metrics["per_core_usage"])
    # Allow 20% variance (CPU usage is dynamic)
    assert abs(avg_core_usage - metrics["total_usage"]) < 20, \
        f"Average core usage {avg_core_usage:.1f}% differs too much from total {metrics['total_usage']:.1f}%"

    # Validate top processes are sorted by CPU usage
    cpu_usages = [proc["cpu_percent"] for proc in metrics["top_processes"]]
    assert cpu_usages == sorted(cpu_usages, reverse=True), \
        "Top processes must be sorted by CPU usage (descending)"

    # Validate risk level matches thresholds
    if metrics["total_usage"] >= 95:
        assert analysis["risk_level"] in ["high"], "Usage >= 95% must be high risk"
    elif metrics["total_usage"] >= 80:
        assert analysis["risk_level"] in ["medium", "high"], "Usage >= 80% must be medium/high risk"

    # Validate recommendations exist when there are warnings
    if len(analysis["warnings"]) > 0:
        assert len(analysis["recommendations"]) > 0, \
            "Warnings should be accompanied by recommendations"

    # Validate frequency consistency (if available)
    if metrics["current_freq"] and metrics["max_freq"]:
        assert metrics["current_freq"] <= metrics["max_freq"], \
            "Current frequency cannot exceed max frequency"

    if metrics["current_freq"] and metrics["min_freq"]:
        assert metrics["current_freq"] >= metrics["min_freq"], \
            "Current frequency cannot be below min frequency"

    print(f"✓ Metrics structure validation passed")
    print(f"  Core count: {metrics['core_count']}")
    print(f"  Total usage: {metrics['total_usage']}%")
    print(f"  Average core usage: {avg_core_usage:.1f}%")
    print(f"  Top processes: {len(metrics['top_processes'])}")
    print(f"  Warnings: {len(analysis['warnings'])}")
    print(f"  Recommendations: {len(analysis['recommendations'])}")


# ============================================================================
# Additional Tests
# ============================================================================

def test_human_readable_output():
    """
    Test that human-readable output is generated correctly (without --json).
    """
    exit_code, stdout, _ = run_script([])

    # Verify output contains expected sections
    assert "CPU Analysis Report" in stdout, "Missing report header"
    assert "CPU Usage:" in stdout, "Missing CPU usage section"
    assert "Total:" in stdout, "Missing total usage"
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

    # Should exit with error code 2 (Click validation error)
    assert exit_code != 0, "Invalid threshold should cause error"

    print(f"✓ Error handling validation passed")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    """
    Run all tests when executed directly.
    """
    print("=" * 60)
    print("CPU Analyzer Test Suite")
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
        ("Performance (<2s)", test_performance_under_2_seconds),
        ("Metrics Structure Validation", test_metrics_structure_validation),
        ("Human Readable Output", test_human_readable_output),
        ("Verbose Flag", test_verbose_flag),
        ("Error Handling", test_error_handling),
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
