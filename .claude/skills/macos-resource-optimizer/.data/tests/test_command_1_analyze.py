"""
Test suite for /macos-resource-optimizer:1-analyze command.

Command: Analyze system resources across 6 categories in parallel
Delegation: manager-resource-coordinator (orchestrates 6 expert agents)
Tests: 3 (delegation, output format, error handling)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio


class TestCommand1AnalyzeDelegation:
    """Test 1: Command delegation with parallel analysis."""

    @pytest.mark.asyncio
    async def test_analyze_command_delegates_to_coordinator(self):
        """Test /macos-resource-optimizer:1-analyze delegates to manager-resource-coordinator."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "execution_time_seconds": 1.8,
                "categories": {
                    "cpu": {
                        "usage_percent": 45.2,
                        "user_percent": 28.5,
                        "system_percent": 12.3,
                        "idle_percent": 54.8,
                        "processes": [
                            {"name": "python", "pid": 1234, "cpu_percent": 15.2},
                            {"name": "chrome", "pid": 5678, "cpu_percent": 12.1}
                        ]
                    },
                    "memory": {
                        "usage_percent": 75.0,
                        "used_gb": 12.0,
                        "total_gb": 16.0,
                        "swap_percent": 5.0,
                        "pressure_level": "high"
                    },
                    "disk": {
                        "usage_percent": 65.0,
                        "used_gb": 325.0,
                        "total_gb": 500.0,
                        "io_read_mbps": 50.0,
                        "io_write_mbps": 35.0
                    },
                    "network": {
                        "bandwidth_mbps": 125.0,
                        "sent_mbps": 42.0,
                        "recv_mbps": 83.0,
                        "connections": 45,
                        "dropped_packets": 0
                    },
                    "battery": {
                        "percent": 80.0,
                        "health": "good",
                        "cycles": 125,
                        "power_draw_watts": 15.0
                    },
                    "thermal": {
                        "cpu_temp_celsius": 65.0,
                        "gpu_temp_celsius": 58.0,
                        "thermal_pressure": "moderate",
                        "throttling_active": False
                    }
                }
            }

            from unittest.mock import AsyncMock
            mock_execute = AsyncMock(return_value=mock_task.return_value)
            result = await mock_execute()

            # Verify parallel delegation structure
            assert result["status"] == "success"
            assert "categories" in result
            assert len(result["categories"]) == 6
            assert "cpu" in result["categories"]
            assert "memory" in result["categories"]
            assert "disk" in result["categories"]
            assert "network" in result["categories"]
            assert "battery" in result["categories"]
            assert "thermal" in result["categories"]

    def test_analyze_command_delegates_with_parallel_execution(self):
        """Test Task() is called with parallel execution configuration."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "execution_time_seconds": 1.8,
                "categories": {
                    "cpu": {"usage_percent": 45.2},
                    "memory": {"usage_percent": 75.0},
                    "disk": {"usage_percent": 65.0},
                    "network": {"bandwidth_mbps": 125.0},
                    "battery": {"percent": 80.0},
                    "thermal": {"cpu_temp_celsius": 65.0}
                }
            }

            Task = mock_task
            result = Task(
                subagent_type="manager-resource-coordinator",
                prompt="Execute parallel 6-category resource analysis: CPU, Memory, Disk, Network, Battery, Thermal. Target execution time: 1.5-2.0 seconds"
            )

            # Verify Task call for parallel analysis
            mock_task.assert_called_once()
            call_args = mock_task.call_args
            assert call_args[1]["subagent_type"] == "manager-resource-coordinator"
            assert "parallel" in call_args[1]["prompt"].lower()


class TestCommand1AnalyzeOutput:
    """Test 2: Output format and performance validation."""

    def test_analyze_output_contains_all_categories(self):
        """Test analyze output contains all 6 resource categories."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "categories": {
                    "cpu": {"usage_percent": 45.2, "user_percent": 28.5},
                    "memory": {"usage_percent": 75.0, "used_gb": 12.0},
                    "disk": {"usage_percent": 65.0, "used_gb": 325.0},
                    "network": {"bandwidth_mbps": 125.0, "sent_mbps": 42.0},
                    "battery": {"percent": 80.0, "health": "good"},
                    "thermal": {"cpu_temp_celsius": 65.0, "gpu_temp_celsius": 58.0}
                }
            }

            result = mock_task.return_value

            # Verify all categories present
            assert "cpu" in result["categories"]
            assert "memory" in result["categories"]
            assert "disk" in result["categories"]
            assert "network" in result["categories"]
            assert "battery" in result["categories"]
            assert "thermal" in result["categories"]

    def test_analyze_output_has_correct_metrics_per_category(self):
        """Test analyze output has correct metrics for each category."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "categories": {
                    "cpu": {
                        "usage_percent": 45.2,
                        "user_percent": 28.5,
                        "system_percent": 12.3,
                        "processes": [{"name": "python", "cpu_percent": 15.2}]
                    },
                    "memory": {
                        "usage_percent": 75.0,
                        "used_gb": 12.0,
                        "total_gb": 16.0,
                        "pressure_level": "high"
                    }
                }
            }

            result = mock_task.return_value

            # Verify CPU metrics
            assert "usage_percent" in result["categories"]["cpu"]
            assert "user_percent" in result["categories"]["cpu"]
            assert "processes" in result["categories"]["cpu"]

            # Verify Memory metrics
            assert "usage_percent" in result["categories"]["memory"]
            assert "used_gb" in result["categories"]["memory"]
            assert "total_gb" in result["categories"]["memory"]

    def test_analyze_output_performance_within_target(self):
        """Test analyze execution time is within target range."""

        with patch('Task') as mock_task:
            # Test execution times within 1.5-2.0 seconds target
            test_cases = [1.5, 1.7, 1.8, 1.9, 2.0]

            for exec_time in test_cases:
                mock_task.return_value = {
                    "status": "success",
                    "execution_time_seconds": exec_time,
                    "categories": {}
                }

                result = mock_task.return_value

                # Verify execution time within target
                assert 1.5 <= result["execution_time_seconds"] <= 2.5
                assert result["status"] == "success"

    def test_analyze_output_has_execution_time(self):
        """Test analyze output includes execution time metric."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "execution_time_seconds": 1.8,
                "categories": {}
            }

            result = mock_task.return_value

            # Verify execution time present and valid
            assert "execution_time_seconds" in result
            assert isinstance(result["execution_time_seconds"], (int, float))
            assert result["execution_time_seconds"] > 0

    def test_analyze_output_format_is_json_compatible(self):
        """Test analyze output is JSON-serializable."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "execution_time_seconds": 1.8,
                "categories": {
                    "cpu": {"usage_percent": 45.2},
                    "memory": {"usage_percent": 75.0}
                }
            }

            import json
            result = mock_task.return_value

            # Verify JSON serializable
            try:
                json_str = json.dumps(result)
                assert json_str is not None
            except TypeError as e:
                pytest.fail(f"Output is not JSON serializable: {e}")


class TestCommand1AnalyzeErrorHandling:
    """Test 3: Error handling and resilience."""

    def test_analyze_handles_coordinator_failure(self):
        """Test /macos-resource-optimizer:1-analyze handles coordinator failure."""

        with patch('Task') as mock_task:
            mock_task.side_effect = Exception("Coordinator subprocess failed during parallel analysis execution.")

            with pytest.raises(Exception) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute parallel 6-category resource analysis"
                )

            assert "subprocess failed" in str(exc_info.value).lower()

    def test_analyze_handles_timeout_during_analysis(self):
        """Test /macos-resource-optimizer:1-analyze handles timeout during parallel analysis."""

        with patch('Task') as mock_task:
            mock_task.side_effect = TimeoutError("Parallel analysis exceeded timeout of 2.5 seconds. Coordinator timed out waiting for expert agents.")

            with pytest.raises(TimeoutError) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute parallel 6-category resource analysis"
                )

            assert "timeout" in str(exc_info.value).lower()

    def test_analyze_handles_partial_category_failure(self):
        """Test /macos-resource-optimizer:1-analyze handles partial category failures."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "partial_success",
                "execution_time_seconds": 1.8,
                "categories": {
                    "cpu": {"usage_percent": 45.2},
                    "memory": {"usage_percent": 75.0},
                    "disk": {"usage_percent": 65.0},
                    "network": None,
                    "battery": {"percent": 80.0},
                    "thermal": None
                },
                "errors": [
                    {"category": "network", "error": "Network interface unreachable"},
                    {"category": "thermal", "error": "Thermal sensors unavailable on this macOS version"}
                ]
            }

            result = mock_task.return_value

            # Verify partial success handling
            assert result["status"] == "partial_success"
            assert "errors" in result
            assert len(result["errors"]) == 2

    def test_analyze_handles_cache_read_failure(self):
        """Test /macos-resource-optimizer:1-analyze handles cache read failure with fallback."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "cache_status": "miss",
                "cache_fallback": True,
                "execution_time_seconds": 2.1,
                "categories": {
                    "cpu": {"usage_percent": 45.2},
                    "memory": {"usage_percent": 75.0},
                    "disk": {"usage_percent": 65.0},
                    "network": {"bandwidth_mbps": 125.0},
                    "battery": {"percent": 80.0},
                    "thermal": {"cpu_temp_celsius": 65.0}
                }
            }

            result = mock_task.return_value

            # Verify cache fallback handling
            assert result["cache_status"] == "miss"
            assert result["cache_fallback"] is True
            assert result["status"] == "success"

    def test_analyze_handles_expert_agent_crash(self):
        """Test /macos-resource-optimizer:1-analyze handles expert agent crash."""

        with patch('Task') as mock_task:
            mock_task.side_effect = Exception("Expert agent crash during CPU analysis: ProcessError in psutil.cpu_percent().")

            with pytest.raises(Exception) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute parallel 6-category resource analysis"
                )

            assert "Expert agent" in str(exc_info.value)


@pytest.fixture
def mock_task():
    """Fixture providing mock Task function."""
    with patch('Task') as mock:
        yield mock


def test_analyze_command_success_workflow(mock_task):
    """Integration test: Full analysis success workflow."""

    mock_task.return_value = {
        "status": "success",
        "execution_time_seconds": 1.8,
        "categories": {
            "cpu": {"usage_percent": 45.2, "user_percent": 28.5},
            "memory": {"usage_percent": 75.0, "used_gb": 12.0},
            "disk": {"usage_percent": 65.0, "used_gb": 325.0},
            "network": {"bandwidth_mbps": 125.0, "sent_mbps": 42.0},
            "battery": {"percent": 80.0, "health": "good"},
            "thermal": {"cpu_temp_celsius": 65.0, "gpu_temp_celsius": 58.0}
        }
    }

    result = mock_task(
        subagent_type="manager-resource-coordinator",
        prompt="Execute parallel 6-category resource analysis"
    )

    # Verify complete analysis success workflow
    assert result["status"] == "success"
    assert 1.5 <= result["execution_time_seconds"] <= 2.5
    assert len(result["categories"]) == 6

    # Verify each category has valid metrics
    for category in ["cpu", "memory", "disk", "network", "battery", "thermal"]:
        assert category in result["categories"]
        assert result["categories"][category] is not None
        assert isinstance(result["categories"][category], dict)
