"""
Test Suite for analyze_all.py - Parallel System Analysis Orchestrator

Validates:
- JSON output structure
- Parallel execution performance (<8.0s for 6 categories)
- Exit codes based on overall status
- All categories analyzed
- Human-readable summary flag
- Aggregation logic (overall status, max risk level)
- Error handling and partial failures
"""

import subprocess
import json
import pytest
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


class TestAnalyzeAllScript:
    """Test analyze_all.py parallel orchestration"""

    def test_json_output_structure(self):
        """Test 1: Verify JSON output contains all required fields"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10  # Allow time for parallel execution
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

        # Validate JSON output
        data = json.loads(result.stdout)

        # Validate top-level structure
        assert "timestamp" in data, "Missing 'timestamp' field"
        assert "categories" in data, "Missing 'categories' field"
        assert "summary" in data, "Missing 'summary' field"

        # Validate timestamp format (ISO 8601)
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str), "Timestamp must be string"
        assert "T" in timestamp, "Timestamp should be ISO 8601 format"

        # Validate summary fields
        summary = data["summary"]
        required_summary_fields = [
            "overall_status",
            "max_risk_level",
            "total_recommendations",
            "categories_analyzed",
            "execution_time_seconds"
        ]

        for field in required_summary_fields:
            assert field in summary, f"Missing summary field: {field}"

        # Validate summary field types
        assert summary["overall_status"] in ["healthy", "warning", "critical"], \
            f"Invalid overall_status: {summary['overall_status']}"
        assert summary["max_risk_level"] in ["low", "medium", "high"], \
            f"Invalid max_risk_level: {summary['max_risk_level']}"
        assert isinstance(summary["total_recommendations"], int), \
            "total_recommendations must be integer"
        assert isinstance(summary["categories_analyzed"], int), \
            "categories_analyzed must be integer"
        assert isinstance(summary["execution_time_seconds"], (int, float)), \
            "execution_time_seconds must be numeric"

        # Validate categories
        categories = data["categories"]
        assert isinstance(categories, dict), "Categories must be dict"
        assert len(categories) >= 1, "At least one category should be analyzed"

        # Each category should have proper structure
        for category_name, category_data in categories.items():
            assert "category" in category_data, f"Missing 'category' in {category_name}"
            assert "analysis" in category_data, f"Missing 'analysis' in {category_name}"

            # Validate analysis structure (if successful)
            analysis = category_data["analysis"]
            if isinstance(analysis, dict):
                # Check for common fields (may vary by category)
                assert "status" in analysis or "error" in analysis, \
                    f"Analysis should have 'status' or 'error' field for {category_name}"

    def test_parallel_execution_performance(self):
        """Test 2: Verify parallel execution completes within performance target"""
        start = time.time()

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        duration = time.time() - start

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        # Check execution time from script output
        execution_time = data["summary"]["execution_time_seconds"]

        # Performance target: <8.0s for parallel execution
        # Sequential would be 6 categories × ~2s = 12s
        # Parallel should be ~2-3s (overlap)
        assert execution_time < 8.0, \
            f"Execution took {execution_time:.2f}s (target: <8.0s for parallel)"

        # Wall-clock time should also be reasonable
        assert duration < 10.0, \
            f"Total wall-clock time {duration:.2f}s (expected <10s for parallel)"

        # Verify actual parallelism benefit
        # With 6 categories, parallel should be significantly faster than sequential
        categories_count = data["summary"]["categories_analyzed"]
        expected_sequential = categories_count * 2.0  # Rough estimate

        # Parallel should save at least 30% compared to sequential
        assert execution_time < expected_sequential * 0.7, \
            f"Parallel execution ({execution_time:.2f}s) not faster enough than " \
            f"estimated sequential ({expected_sequential:.2f}s)"

    def test_exit_codes(self):
        """Test 3: Verify exit codes based on overall status"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        overall_status = data["summary"]["overall_status"]

        # Exit code should match status
        # 0 = healthy, 1 = warning, 2 = critical
        if overall_status == "healthy":
            assert result.returncode == 0, \
                f"Exit code should be 0 for 'healthy' status, got {result.returncode}"
        elif overall_status == "warning":
            assert result.returncode == 1, \
                f"Exit code should be 1 for 'warning' status, got {result.returncode}"
        elif overall_status == "critical":
            assert result.returncode == 2, \
                f"Exit code should be 2 for 'critical' status, got {result.returncode}"

    def test_all_categories_analyzed(self):
        """Test 4: Verify all 6 categories are analyzed"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        categories = data["categories"]
        summary = data["summary"]

        # Should analyze 6 categories (or report why not)
        expected_categories = ["cpu", "memory", "disk", "network", "battery", "thermal"]

        # Check that we got results for most categories
        assert summary["categories_analyzed"] >= 3, \
            "Should analyze at least 3 categories (cpu, memory, disk minimum)"

        # Battery and thermal might not be available on all systems
        # But CPU, memory, disk, network should always work
        critical_categories = ["cpu", "memory", "disk", "network"]

        found_critical = 0
        for cat in critical_categories:
            if cat in categories:
                assert "analysis" in categories[cat], \
                    f"Category '{cat}' missing 'analysis' field"
                found_critical += 1

        assert found_critical >= 3, \
            f"Should have at least 3 critical categories, found {found_critical}"

        # Verify each category has proper structure
        for category_name, category_data in categories.items():
            assert category_data["category"] == category_name, \
                f"Category name mismatch: {category_data['category']} != {category_name}"

    def test_summary_flag(self):
        """Test 5: Verify --summary flag produces human-readable output"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--summary"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

        # Should contain human-readable summary (not JSON)
        output = result.stdout

        # Verify key summary sections are present
        required_sections = [
            "macOS System Resource Analysis",
            "Overall Status:",
            "Risk Level:",
            "Categories Analyzed:",
            "Execution Time:"
        ]

        for section in required_sections:
            assert section in output, \
                f"Missing required section in summary: '{section}'"

        # Verify it's NOT JSON
        try:
            json.loads(output)
            pytest.fail("--summary output should be human-readable, not JSON")
        except json.JSONDecodeError:
            pass  # Expected behavior


class TestParallelAggregation:
    """Test aggregation logic"""

    def test_overall_status_aggregation(self):
        """Test 6: Verify overall status is correctly aggregated from categories"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        categories = data["categories"]
        overall_status = data["summary"]["overall_status"]

        # Collect category statuses
        category_statuses = []
        for cat_data in categories.values():
            analysis = cat_data.get("analysis", {})
            if isinstance(analysis, dict):
                status = analysis.get("status", "error")
                category_statuses.append(status)

        # Aggregation logic validation:
        # - If any critical/error → overall should be critical
        # - If any warning (and no critical) → overall should be warning
        # - If all healthy → overall should be healthy

        has_critical = any(s in ["critical", "error"] for s in category_statuses)
        has_warning = any(s == "warning" for s in category_statuses)
        all_healthy = all(s == "healthy" for s in category_statuses)

        if has_critical:
            assert overall_status == "critical", \
                f"Overall status should be 'critical' when any category is critical/error. " \
                f"Statuses: {category_statuses}, Overall: {overall_status}"
        elif has_warning:
            assert overall_status == "warning", \
                f"Overall status should be 'warning' when any category is warning. " \
                f"Statuses: {category_statuses}, Overall: {overall_status}"
        elif all_healthy:
            assert overall_status == "healthy", \
                f"Overall status should be 'healthy' when all categories are healthy. " \
                f"Statuses: {category_statuses}, Overall: {overall_status}"

    def test_risk_level_aggregation(self):
        """Test 7: Verify max risk level is correctly determined"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        categories = data["categories"]
        max_risk = data["summary"]["max_risk_level"]

        # Collect all risk levels
        risk_levels = []
        for cat_data in categories.values():
            analysis = cat_data.get("analysis", {})
            if isinstance(analysis, dict):
                risk = analysis.get("risk_level", "unknown")
                risk_levels.append(risk)

        # Max risk should be the highest found
        # Priority: high > medium > low

        if any(r == "high" for r in risk_levels):
            assert max_risk == "high", \
                f"Max risk should be 'high' when any category has high risk. " \
                f"Risks: {risk_levels}, Max: {max_risk}"
        elif any(r == "medium" for r in risk_levels):
            assert max_risk == "medium", \
                f"Max risk should be 'medium' when any category has medium risk. " \
                f"Risks: {risk_levels}, Max: {max_risk}"
        else:
            assert max_risk == "low", \
                f"Max risk should be 'low' when all categories have low risk. " \
                f"Risks: {risk_levels}, Max: {max_risk}"


class TestErrorHandling:
    """Test error handling and partial failures"""

    def test_graceful_handling_of_failures(self):
        """Test 8: Verify script handles individual category failures gracefully"""
        # This test verifies the script doesn't crash if a category fails
        # The actual script should handle individual category failures

        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should complete even if some categories fail
        # Valid exit codes: 0 (healthy), 1 (warning), 2 (critical)
        assert result.returncode in [0, 1, 2], \
            f"Script should complete successfully, got exit code: {result.returncode}"

        # Should produce valid JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Script should produce valid JSON output: {e}")

        # Verify structure is intact even with partial failures
        assert "summary" in data, "Summary should exist even with partial failures"
        assert "categories" in data, "Categories should exist even with partial failures"

        # Check if any categories reported errors
        categories = data["categories"]
        error_categories = []

        for cat_name, cat_data in categories.items():
            analysis = cat_data.get("analysis", {})
            if isinstance(analysis, dict):
                if "error" in analysis or analysis.get("status") == "error":
                    error_categories.append(cat_name)

        # If there are errors, verify they're reported properly
        if error_categories:
            for cat_name in error_categories:
                cat_data = categories[cat_name]
                analysis = cat_data["analysis"]

                # Error should have meaningful message
                if "error" in analysis:
                    assert isinstance(analysis["error"], str), \
                        f"Error message should be string for {cat_name}"
                    assert len(analysis["error"]) > 0, \
                        f"Error message should not be empty for {cat_name}"

    def test_total_recommendations_count(self):
        """Test 9: Verify total recommendations are correctly counted"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        total_recommendations = data["summary"]["total_recommendations"]
        categories = data["categories"]

        # Count recommendations manually
        manual_count = 0
        for cat_data in categories.values():
            analysis = cat_data.get("analysis", {})
            if isinstance(analysis, dict):
                recommendations = analysis.get("recommendations", [])
                if isinstance(recommendations, list):
                    manual_count += len(recommendations)

        # Verify total matches manual count
        assert total_recommendations == manual_count, \
            f"Total recommendations ({total_recommendations}) doesn't match " \
            f"manual count ({manual_count})"

        # Total should be non-negative
        assert total_recommendations >= 0, \
            "Total recommendations should be non-negative"

    def test_categories_analyzed_count(self):
        """Test 10: Verify categories_analyzed count is accurate"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"
        data = json.loads(result.stdout)

        categories_analyzed = data["summary"]["categories_analyzed"]
        categories = data["categories"]

        # Count should match actual categories dictionary length
        actual_count = len(categories)

        assert categories_analyzed == actual_count, \
            f"categories_analyzed ({categories_analyzed}) doesn't match " \
            f"actual categories count ({actual_count})"

        # Should be between 1 and 6 (inclusive)
        assert 1 <= categories_analyzed <= 6, \
            f"categories_analyzed ({categories_analyzed}) should be between 1 and 6"


# Additional edge case tests

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_multiple_runs_consistency(self):
        """Test 11: Verify multiple runs produce consistent results"""
        results = []

        for i in range(2):
            result = subprocess.run(
                ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode in [0, 1, 2], \
                f"Run {i+1} failed with exit code: {result.returncode}"

            data = json.loads(result.stdout)
            results.append(data)

        # Compare key metrics (should be similar, allowing for small variations)
        for i in range(len(results) - 1):
            current = results[i]
            next_result = results[i + 1]

            # Categories analyzed should be the same
            assert current["summary"]["categories_analyzed"] == \
                   next_result["summary"]["categories_analyzed"], \
                   "categories_analyzed should be consistent across runs"

            # Overall status might vary slightly, but major categories should match
            current_categories = set(current["categories"].keys())
            next_categories = set(next_result["categories"].keys())

            assert current_categories == next_categories, \
                "Category sets should be consistent across runs"

    def test_json_flag_explicit(self):
        """Test 12: Verify --json flag explicitly produces JSON output"""
        result = subprocess.run(
            ["uv", "run", str(SCRIPTS_DIR / "analyze_all.py"), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"--json flag should produce valid JSON: {e}")

        # Verify it's structured JSON (not just JSON-serializable string)
        assert isinstance(data, dict), \
            "--json output should be a JSON object (dict)"

        # Verify no extraneous output
        # All output should be in JSON format (no extra print statements)
        assert result.stdout.strip().startswith("{"), \
            "JSON output should start with '{'"
        assert result.stdout.strip().endswith("}"), \
            "JSON output should end with '}'"
