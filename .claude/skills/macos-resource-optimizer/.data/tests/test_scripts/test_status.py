"""
Test suite for status.py script

Tests JSON output, human-readable output, exit codes, performance, and error handling.
"""

import subprocess
import json
import time
import pytest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "scripts"
STATUS_SCRIPT = SCRIPTS_DIR / "status.py"


class TestStatusScript:
    """Test suite for status.py system health check"""

    def test_json_output_structure(self):
        """Test that JSON output contains all required fields"""
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should succeed (exit code 0 or 1 for healthy/warning)
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

        # Parse JSON output
        data = json.loads(result.stdout)

        # Verify required top-level fields
        assert "status" in data, "Missing 'status' field"
        assert "metrics" in data, "Missing 'metrics' field"
        assert "warnings" in data, "Missing 'warnings' field"
        assert "critical_issues" in data, "Missing 'critical_issues' field"
        assert "timestamp" in data, "Missing 'timestamp' field"

        # Verify metrics structure
        metrics = data["metrics"]
        assert "cpu" in metrics, "Missing CPU metrics"
        assert "memory" in metrics, "Missing memory metrics"
        assert "disk" in metrics, "Missing disk metrics"
        assert "network" in metrics, "Missing network metrics"
        assert "battery" in metrics, "Missing battery metrics"
        assert "thermal" in metrics, "Missing thermal metrics"

        # Verify CPU metrics
        assert "usage" in metrics["cpu"], "Missing CPU usage"
        assert "cores" in metrics["cpu"], "Missing CPU cores"
        assert 0 <= metrics["cpu"]["usage"] <= 100, "Invalid CPU usage percentage"

        # Verify memory metrics
        assert "percent" in metrics["memory"], "Missing memory percent"
        assert "total_gb" in metrics["memory"], "Missing memory total"
        assert 0 <= metrics["memory"]["percent"] <= 100, "Invalid memory percentage"

        # Verify disk metrics
        assert "percent" in metrics["disk"], "Missing disk percent"
        assert "total_gb" in metrics["disk"], "Missing disk total"
        assert 0 <= metrics["disk"]["percent"] <= 100, "Invalid disk percentage"

        # Verify status is valid
        assert data["status"] in ["healthy", "warning", "critical"], "Invalid status value"

    def test_human_readable_output(self):
        """Test human-readable output format and content"""
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should succeed
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

        output = result.stdout

        # Verify header and footer
        assert "macOS System Health Status" in output, "Missing header"
        assert "=" * 60 in output, "Missing separator lines"

        # Verify key sections are present
        assert "CPU:" in output, "Missing CPU section"
        assert "Memory:" in output, "Missing Memory section"
        assert "Disk:" in output, "Missing Disk section"
        assert "Overall Status:" in output, "Missing overall status"

        # Verify at least one status indicator
        assert any(status in output for status in ["HEALTHY", "WARNING", "CRITICAL"]), \
            "Missing status indicator"

    def test_verbose_output(self):
        """Test verbose mode includes additional details"""
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--verbose"],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode in [0, 1, 2]
        output = result.stdout

        # Verbose mode should include network details
        assert "Network:" in output or "🌐" in output, "Missing network section in verbose mode"

    def test_exit_codes(self):
        """Test that exit codes match system status"""
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        data = json.loads(result.stdout)
        status = data["status"]

        # Verify exit code matches status
        if status == "healthy":
            assert result.returncode == 0, "Healthy status should return exit code 0"
        elif status == "warning":
            assert result.returncode == 1, "Warning status should return exit code 1"
        elif status == "critical":
            assert result.returncode == 2, "Critical status should return exit code 2"

    def test_performance(self):
        """Test that script completes within 2 seconds"""
        start_time = time.time()

        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        elapsed = time.time() - start_time

        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Script took {elapsed:.2f}s (should be < 2.0s)"

        # Should still succeed
        assert result.returncode in [0, 1, 2], "Script failed during performance test"

    def test_error_handling(self):
        """Test error handling with invalid arguments"""
        # Test with invalid flag
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--invalid-flag"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should fail gracefully (click will handle invalid args)
        assert result.returncode != 0, "Should fail with invalid arguments"

    def test_json_and_verbose_combined(self):
        """Test that JSON and verbose flags work together"""
        result = subprocess.run(
            ["uv", "run", str(STATUS_SCRIPT), "--json", "--verbose"],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode in [0, 1, 2]

        # Should still produce valid JSON (verbose is ignored in JSON mode)
        data = json.loads(result.stdout)
        assert "status" in data
        assert "metrics" in data

    def test_metrics_consistency(self):
        """Test that metrics are consistent across multiple runs"""
        results = []

        # Run script 3 times
        for _ in range(3):
            result = subprocess.run(
                ["uv", "run", str(STATUS_SCRIPT), "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            data = json.loads(result.stdout)
            results.append(data)
            time.sleep(0.1)

        # CPU cores should be consistent
        cores = [r["metrics"]["cpu"]["cores"] for r in results]
        assert len(set(cores)) == 1, "CPU core count should be consistent"

        # Total memory should be consistent
        total_mem = [r["metrics"]["memory"]["total_gb"] for r in results]
        assert all(abs(total_mem[0] - m) < 0.01 for m in total_mem), \
            "Total memory should be consistent"

        # Total disk should be consistent
        total_disk = [r["metrics"]["disk"]["total_gb"] for r in results]
        assert all(abs(total_disk[0] - d) < 0.1 for d in total_disk), \
            "Total disk should be consistent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
