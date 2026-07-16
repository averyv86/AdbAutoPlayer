"""
Test suite for /macos-resource-optimizer:0-init command.

UV Script Testing: Uses subprocess execution instead of Python imports.
Pattern: subprocess.run(["uv", "run", script_path]) for all script tests.

Command: Initialize configuration and validate Python engine setup
Tests: 13 (subprocess execution, validation, error handling)
"""

import pytest
import subprocess
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# Path to scripts directory (UV scripts)
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


class TestCommand0InitDelegation:
    """Test 1: Command delegation and script execution."""

    def test_init_validates_scripts_exist(self):
        """Test all required UV scripts exist in scripts directory."""

        required_scripts = [
            "status.py",
            "analyze_cpu.py",
            "analyze_memory.py",
            "analyze_disk.py",
            "analyze_network.py",
            "analyze_battery.py",
            "analyze_thermal.py",
            "analyze_all.py",
            "optimize.py",
            "monitor.py",
            "report.py",
            "cache.py"
        ]

        for script in required_scripts:
            script_path = SCRIPTS_DIR / script
            assert script_path.exists(), f"Required script not found: {script}"
            assert script_path.is_file(), f"Script is not a file: {script}"

    def test_status_script_execution(self):
        """Test status.py UV script executes successfully."""

        script_path = SCRIPTS_DIR / "status.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Valid exit codes: 0 (healthy), 1 (warning), 2 (critical)
        # Exit code 3 is error
        assert result.returncode in [0, 1, 2], (
            f"Script failed with exit code {result.returncode}: {result.stderr}"
        )

        # Parse JSON output
        data = json.loads(result.stdout)

        # Verify structure
        assert "status" in data
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_percent" in data
        assert data["status"] in ["healthy", "warning", "critical"]

    @pytest.mark.asyncio
    async def test_init_command_validates_python_version(self):
        """Test initialization validates Python version via script execution."""

        # Execute a simple script to verify Python environment
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert "Python 3" in result.stdout

        # Extract version
        version_str = result.stdout.strip().split()[1]
        major, minor = map(int, version_str.split('.')[:2])

        # Verify Python 3.11+
        assert major >= 3
        if major == 3:
            assert minor >= 11, f"Python 3.11+ required, got {version_str}"


class TestCommand0InitValidation:
    """Test 2: UV script validation and dependency checking."""

    def test_status_script_json_output_structure(self):
        """Test status.py produces valid JSON with required fields."""

        script_path = SCRIPTS_DIR / "status.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode in [0, 1, 2]

        data = json.loads(result.stdout)

        # Required fields
        required_fields = [
            "timestamp",
            "status",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "network_active",
            "warnings",
            "critical_issues"
        ]

        for field in required_fields:
            assert field in data, f"Required field missing: {field}"

        # Type validation
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["status"], str)
        assert isinstance(data["cpu_percent"], (int, float))
        assert isinstance(data["memory_percent"], (int, float))
        assert isinstance(data["warnings"], list)
        assert isinstance(data["critical_issues"], list)

    def test_status_script_exit_codes(self):
        """Test status.py exit code system works correctly."""

        script_path = SCRIPTS_DIR / "status.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Valid exit codes
        assert result.returncode in [0, 1, 2, 3], (
            f"Invalid exit code: {result.returncode}"
        )

        if result.returncode in [0, 1, 2]:
            # Should have valid JSON output
            data = json.loads(result.stdout)

            # Exit code should match status
            exit_code_mapping = {
                "healthy": 0,
                "warning": 1,
                "critical": 2
            }

            expected_code = exit_code_mapping[data["status"]]
            assert result.returncode == expected_code, (
                f"Exit code {result.returncode} doesn't match status {data['status']}"
            )

    def test_uv_dependencies_available(self):
        """Test UV can resolve script dependencies."""

        # Test UV is installed
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, "UV not installed or not in PATH"
        assert "uv" in result.stdout.lower()

    def test_cache_script_initialization(self):
        """Test cache.py script can initialize and report stats."""

        script_path = SCRIPTS_DIR / "cache.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--operation", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute successfully or report cache not initialized
        assert result.returncode in [0, 1, 3]

        if result.returncode in [0, 1]:
            data = json.loads(result.stdout)
            assert "operation" in data


class TestCommand0InitErrorHandling:
    """Test 3: Error handling for initialization and script failures."""

    def test_status_script_handles_invalid_flags(self):
        """Test status.py handles invalid command-line flags gracefully."""

        script_path = SCRIPTS_DIR / "status.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--invalid-flag-xyz"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

        # Should provide helpful error message
        output = result.stdout + result.stderr
        assert len(output) > 0, "No error message provided"

    def test_script_timeout_handling(self):
        """Test script execution with timeout constraint."""

        script_path = SCRIPTS_DIR / "status.py"

        # Should complete within 10 seconds
        try:
            result = subprocess.run(
                ["uv", "run", str(script_path), "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # If we get here, timeout didn't occur
            assert True
        except subprocess.TimeoutExpired:
            pytest.fail("Script exceeded 10 second timeout")

    def test_missing_script_handling(self):
        """Test error handling when script doesn't exist."""

        non_existent_script = SCRIPTS_DIR / "nonexistent_script.py"

        result = subprocess.run(
            ["uv", "run", str(non_existent_script)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should fail
        assert result.returncode != 0

    def test_analyze_cpu_script_error_handling(self):
        """Test analyze_cpu.py handles errors gracefully."""

        script_path = SCRIPTS_DIR / "analyze_cpu.py"

        # Script should handle execution and return proper exit codes
        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=15
        )

        # Valid exit codes: 0 (healthy), 1 (warning), 2 (critical), 3 (error)
        assert result.returncode in [0, 1, 2, 3]

        if result.returncode in [0, 1, 2]:
            # Should have valid output
            data = json.loads(result.stdout)
            assert "category" in data
            assert data["category"] == "cpu"

    def test_subprocess_execution_resilience(self):
        """Test subprocess execution handles various error conditions."""

        # Test 1: Valid script execution
        script_path = SCRIPTS_DIR / "status.py"
        result = subprocess.run(
            ["uv", "run", str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode in [0, 1, 2, 3]

        # Test 2: Script with parameters
        cpu_script = SCRIPTS_DIR / "analyze_cpu.py"
        result = subprocess.run(
            ["uv", "run", str(cpu_script), "--json", "--threshold", "75.0"],
            capture_output=True,
            text=True,
            timeout=15
        )
        assert result.returncode in [0, 1, 2, 3]


@pytest.fixture
def scripts_dir():
    """Fixture providing path to scripts directory."""
    return Path(__file__).parent.parent.parent / "scripts"


@pytest.fixture
def mock_subprocess_success():
    """Fixture providing mock successful subprocess execution."""
    with patch('subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"status": "success", "data": {}}',
            stderr=''
        )
        yield mock


def test_init_command_success_workflow(scripts_dir):
    """Integration test: Full initialization success workflow."""

    # Verify all scripts exist
    required_scripts = [
        "status.py",
        "analyze_cpu.py",
        "analyze_memory.py",
        "analyze_disk.py"
    ]

    for script_name in required_scripts:
        script_path = scripts_dir / script_name
        assert script_path.exists(), f"Script not found: {script_name}"

    # Execute status check
    status_script = scripts_dir / "status.py"
    result = subprocess.run(
        ["uv", "run", str(status_script), "--json"],
        capture_output=True,
        text=True,
        timeout=10
    )

    # Verify successful execution
    assert result.returncode in [0, 1, 2]
    data = json.loads(result.stdout)
    assert "status" in data
    assert "timestamp" in data
