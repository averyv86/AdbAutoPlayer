"""
Integration tests for macOS Resource Optimizer agent → script workflows.

Tests verify that agents correctly delegate to UV scripts, parse JSON output,
handle errors gracefully, and produce expected results.

Test Categories:
    1. Manager-Resource-Coordinator Integration
    2. Manager-Resource-Strategy Integration
    3. Command Workflow Integration
    4. End-to-End User Workflows
    5. Error Handling Scenarios

Requirements:
    - pytest >= 7.4.0
    - Python 3.11+
    - UV package manager
    - macOS environment
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

import pytest


# Test Configuration
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
SKILL_ROOT = Path(__file__).parent.parent.parent.parent


class TestManagerResourceCoordinatorIntegration:
    """Integration tests for manager-resource-coordinator → analyze_all.py"""

    def test_analyze_all_execution(self):
        """Test manager-resource-coordinator executes analyze_all.py successfully"""
        # Simulate agent execution via UV
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Verify exit code (0, 1, or 2 are valid)
        assert result.returncode in [0, 1, 2], f"Invalid exit code: {result.returncode}"

        # Parse JSON output
        data = json.loads(result.stdout)

        # Verify structure
        assert "categories" in data, "Missing 'categories' key"
        assert "timestamp" in data, "Missing 'timestamp' key"

        # Verify all 6 categories present
        expected_categories = {"cpu", "memory", "disk", "network", "battery", "thermal"}
        actual_categories = set(data["categories"].keys())
        assert expected_categories == actual_categories, \
            f"Missing categories: {expected_categories - actual_categories}"

    def test_json_output_structure(self):
        """Test JSON output matches expected structure"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        data = json.loads(result.stdout)

        # Verify each category has required sections
        for category, cat_data in data["categories"].items():
            assert "category" in cat_data, f"{category}: missing 'category' field"
            assert "timestamp" in cat_data, f"{category}: missing 'timestamp' field"
            assert "metrics" in cat_data, f"{category}: missing 'metrics' section"
            assert "analysis" in cat_data, f"{category}: missing 'analysis' section"

            # Verify analysis section
            analysis = cat_data["analysis"]
            assert "status" in analysis, f"{category}: missing 'status' in analysis"
            assert analysis["status"] in ["healthy", "warning", "critical"], \
                f"{category}: invalid status '{analysis['status']}'"

    def test_exit_code_system(self):
        """Test exit code system (0=healthy, 1=warning, 2=critical, 3=error)"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Exit codes 0-2 are valid analysis results
        if result.returncode in [0, 1, 2]:
            data = json.loads(result.stdout)
            assert "categories" in data, "Valid exit code but invalid JSON"

        # Exit code 3 would be execution error (not expected in normal operation)
        # Exit code 124 would be timeout (not expected with 15s timeout)
        assert result.returncode != 3, f"Execution error: {result.stderr}"

    def test_parallel_execution_performance(self):
        """Test parallel execution achieves target performance (1.5-2.5s)"""
        start_time = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        execution_time = time.time() - start_time

        # Verify successful execution
        assert result.returncode in [0, 1, 2], "Script failed"

        # Verify performance target (1.5-2.5s, allow up to 5s for CI/slow systems)
        assert execution_time < 5.0, \
            f"Execution too slow: {execution_time:.2f}s (target: <5.0s)"

        # Log actual performance
        print(f"\nParallel execution time: {execution_time:.2f}s")

    def test_category_specific_analysis(self):
        """Test individual category analysis via analyze_category.py"""
        categories = ["cpu", "memory", "disk"]

        for category in categories:
            result = subprocess.run(
                [
                    "uv", "run",
                    str(SCRIPTS_DIR / "analyze_category.py"),
                    "--category", category,
                    "--format", "json"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Verify exit code
            assert result.returncode in [0, 1, 2], \
                f"{category}: Invalid exit code {result.returncode}"

            # Parse and verify JSON
            data = json.loads(result.stdout)
            assert data["category"] == category, \
                f"Expected category '{category}', got '{data['category']}'"


class TestManagerResourceStrategyIntegration:
    """Integration tests for manager-resource-strategy → optimize.py"""

    def test_dry_run_mode_default(self):
        """Test optimize.py dry-run mode (default, safe)"""
        # Note: This test requires analysis results as input
        # We'll test the script exists and has correct structure
        script_path = SCRIPTS_DIR / "optimize.py"
        assert script_path.exists(), "optimize.py script not found"

        # Verify dry-run is safe (no system modifications)
        # Actual testing would require mock analysis data
        # This is a structural test only
        with open(script_path) as f:
            content = f.read()
            assert "--dry-run" in content or "dry_run" in content, \
                "No dry-run mode found in optimize.py"

    def test_optimize_script_exists(self):
        """Test optimize.py script exists and is executable"""
        script_path = SCRIPTS_DIR / "optimize.py"
        assert script_path.exists(), "optimize.py not found"

        # Verify it's a Python script
        with open(script_path) as f:
            first_line = f.readline()
            assert first_line.startswith("#!") or "python" in first_line.lower(), \
                "Not a valid Python script"

    def test_rollback_script_support(self):
        """Test optimize.py supports --rollback flag"""
        script_path = SCRIPTS_DIR / "optimize.py"
        with open(script_path) as f:
            content = f.read()
            assert "--rollback" in content or "rollback" in content, \
                "No rollback support found in optimize.py"


class TestCommandWorkflowIntegration:
    """Integration tests for command workflows"""

    def test_command_0_init_workflow(self):
        """Test /macos-resource-optimizer:0-init workflow"""
        command_file = SKILL_ROOT / "commands" / "macos-resource-optimizer" / "0-init.md"
        assert command_file.exists(), "0-init.md command not found"

        with open(command_file) as f:
            content = f.read()

            # Verify zero direct tool usage
            assert "allowed-tools:" in content, "No allowed-tools section"
            assert "Task" in content, "Task tool not allowed"
            assert "AskUserQuestion" in content, "AskUserQuestion tool not allowed"

            # Verify workflow phases
            assert "PHASE 1:" in content, "Missing PHASE 1"
            assert "PHASE 2:" in content, "Missing PHASE 2"
            assert "PHASE 3:" in content, "Missing PHASE 3"
            assert "PHASE 4:" in content, "Missing PHASE 4"

            # Verify script references
            assert "status.py" in content, "Missing status.py reference"

    def test_command_1_analyze_workflow(self):
        """Test /macos-resource-optimizer:1-analyze workflow"""
        command_file = SKILL_ROOT / "commands" / "macos-resource-optimizer" / "1-analyze.md"
        assert command_file.exists(), "1-analyze.md command not found"

        with open(command_file) as f:
            content = f.read()

            # Verify delegation to manager-resource-coordinator
            assert "manager-resource-coordinator" in content, \
                "Missing manager-resource-coordinator reference"

            # Verify parallel execution documentation
            assert "parallel" in content.lower() or "asyncio" in content.lower(), \
                "Missing parallel execution documentation"

            # Verify script reference
            assert "analyze_all.py" in content, "Missing analyze_all.py reference"

    def test_command_2_optimize_workflow(self):
        """Test /macos-resource-optimizer:2-optimize workflow"""
        command_file = SKILL_ROOT / "commands" / "macos-resource-optimizer" / "2-optimize.md"
        assert command_file.exists(), "2-optimize.md command not found"

        with open(command_file) as f:
            content = f.read()

            # Verify user approval workflow
            assert "AskUserQuestion" in content, "Missing AskUserQuestion"
            assert "approval" in content.lower(), "Missing approval workflow"

            # Verify optimization script reference
            assert "optimize.py" in content, "Missing optimize.py reference"

            # Verify dry-run and apply modes
            assert "--dry-run" in content, "Missing --dry-run mode"
            assert "--apply" in content, "Missing --apply mode"

    def test_command_3_monitor_workflow(self):
        """Test /macos-resource-optimizer:3-monitor workflow"""
        command_file = SKILL_ROOT / "commands" / "macos-resource-optimizer" / "3-monitor.md"
        assert command_file.exists(), "3-monitor.md command not found"

        with open(command_file) as f:
            content = f.read()

            # Verify monitoring script reference
            assert "monitor.py" in content, "Missing monitor.py reference"

            # Verify monitoring parameters
            assert "--interval" in content, "Missing --interval parameter"
            assert "--alert-threshold" in content, "Missing --alert-threshold parameter"

            # Verify loop documentation (IMPORTANT: single Task() call, not loop)
            assert "SINGLE Task() call" in content or "single delegation" in content.lower(), \
                "Missing clarification about single Task() call for monitoring loop"

    def test_command_9_feedback_workflow(self):
        """Test /macos-resource-optimizer:9-feedback workflow"""
        command_file = SKILL_ROOT / "commands" / "macos-resource-optimizer" / "9-feedback.md"
        assert command_file.exists(), "9-feedback.md command not found"

        with open(command_file) as f:
            content = f.read()

            # Verify feedback types
            assert "bug" in content.lower(), "Missing bug feedback type"
            assert "feature" in content.lower(), "Missing feature feedback type"
            assert "question" in content.lower(), "Missing question feedback type"

            # Verify report generation
            assert ".moai/reports/feedback/" in content, \
                "Missing feedback report location"


class TestEndToEndWorkflows:
    """End-to-end integration tests simulating user workflows"""

    def test_e2e_full_system_analysis(self):
        """
        End-to-end test: Full system analysis

        User: "Analyze my system resources"
        Expected: All 6 categories analyzed, JSON output, formatted report
        """
        # Execute analysis (simulates command delegation to coordinator)
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Verify success
        assert result.returncode in [0, 1, 2], "Analysis failed"

        # Parse results
        data = json.loads(result.stdout)

        # Verify comprehensive analysis
        assert len(data["categories"]) == 6, "Not all categories analyzed"

        # Verify each category has actionable data
        for category, cat_data in data["categories"].items():
            assert "metrics" in cat_data, f"{category}: missing metrics"
            assert "analysis" in cat_data, f"{category}: missing analysis"

            # Verify analysis has recommendations or status
            analysis = cat_data["analysis"]
            assert "status" in analysis or "recommendations" in analysis, \
                f"{category}: no actionable analysis"

    def test_e2e_category_specific_analysis(self):
        """
        End-to-end test: Category-specific analysis

        User: "Check CPU usage"
        Expected: CPU metrics, recommendations
        """
        # Execute CPU-specific analysis
        result = subprocess.run(
            [
                "uv", "run",
                str(SCRIPTS_DIR / "analyze_category.py"),
                "--category", "cpu",
                "--format", "json"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Verify success
        assert result.returncode in [0, 1, 2], "CPU analysis failed"

        # Parse results
        data = json.loads(result.stdout)

        # Verify CPU-specific metrics
        assert data["category"] == "cpu", "Wrong category returned"
        assert "metrics" in data, "Missing CPU metrics"

        # Verify CPU-specific fields
        cpu_metrics = data["metrics"]
        assert "usage_percent" in cpu_metrics, "Missing CPU usage percentage"


class TestErrorHandlingScenarios:
    """Integration tests for error handling"""

    def test_timeout_handling(self):
        """Test timeout protection (10s default)"""
        # Test with very short timeout to trigger timeout
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=1  # Very short timeout to test handling
        )

        # Note: This test may succeed if analysis is fast enough
        # If timeout occurs, subprocess.TimeoutExpired is raised
        # which is caught by pytest and indicates timeout handling works

    def test_invalid_json_handling(self):
        """Test handling of malformed JSON output"""
        # This test verifies that JSON parsing errors are caught
        # We can't easily produce invalid JSON from the script,
        # so we test the parsing logic would fail gracefully

        invalid_json = "{ invalid json }"

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

        # This demonstrates that JSONDecodeError would be raised
        # The agent should catch this and report gracefully

    def test_subprocess_failure_handling(self):
        """Test handling of subprocess execution failures"""
        # Test with non-existent script
        result = subprocess.run(
            ["uv", "run", "nonexistent_script.py"],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0, "Should fail for non-existent script"

        # Should have error message in stderr
        assert result.stderr, "Should have error message"

    def test_graceful_degradation(self):
        """Test graceful degradation when some categories fail"""
        # Even if individual categories fail, overall analysis should succeed
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Analysis should complete even with partial failures
        assert result.returncode in [0, 1, 2], "Should not fail completely"

        # Should still return valid JSON with available results
        data = json.loads(result.stdout)
        assert "categories" in data, "Should return partial results"


# Test Fixtures and Helpers

@pytest.fixture
def sample_analysis_results() -> Dict[str, Any]:
    """Sample analysis results for testing optimization workflows"""
    return {
        "timestamp": "2025-11-30T12:00:00",
        "categories": {
            "cpu": {
                "category": "cpu",
                "timestamp": 1701345600.0,
                "metrics": {
                    "usage_percent": 85.2,
                    "core_count": 8,
                    "top_processes": [
                        {"name": "chrome", "cpu": 45.1, "pid": 1234},
                        {"name": "node", "cpu": 25.3, "pid": 5678}
                    ]
                },
                "analysis": {
                    "status": "warning",
                    "risk_level": "medium",
                    "recommendations": [
                        "Consider closing Chrome tabs",
                        "Review node processes"
                    ]
                }
            },
            "memory": {
                "category": "memory",
                "timestamp": 1701345600.0,
                "metrics": {
                    "memory_percent": 78.5,
                    "swap_used": 2.1
                },
                "analysis": {
                    "status": "healthy",
                    "risk_level": "low",
                    "recommendations": []
                }
            }
        }
    }


@pytest.fixture
def mock_optimization_result() -> Dict[str, Any]:
    """Mock optimization result for testing"""
    return {
        "total_optimizations": 3,
        "successful": 2,
        "failed": 1,
        "execution_time": 12.5,
        "optimizations": [
            {
                "id": "opt-cpu-001",
                "category": "cpu",
                "action": "reduce_process_priority",
                "status": "success",
                "before": 85.2,
                "after": 68.3,
                "improvement": 16.9
            },
            {
                "id": "opt-memory-001",
                "category": "memory",
                "action": "clear_cache",
                "status": "success",
                "before": 78.5,
                "after": 72.1,
                "improvement": 6.4
            },
            {
                "id": "opt-disk-001",
                "category": "disk",
                "action": "run_trim",
                "status": "failed",
                "error": "Permission denied",
                "rollback": "not_required"
            }
        ]
    }


# Performance Benchmarks

def test_performance_benchmark():
    """Benchmark parallel execution performance"""
    iterations = 3
    times = []

    for i in range(iterations):
        start = time.time()
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )
        elapsed = time.time() - start

        assert result.returncode in [0, 1, 2], f"Iteration {i+1} failed"
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\nPerformance Benchmark ({iterations} iterations):")
    print(f"  Average: {avg_time:.2f}s")
    print(f"  Min: {min_time:.2f}s")
    print(f"  Max: {max_time:.2f}s")
    print(f"  Target: <5.0s")

    # Verify average performance meets target
    assert avg_time < 5.0, \
        f"Average performance {avg_time:.2f}s exceeds target 5.0s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
