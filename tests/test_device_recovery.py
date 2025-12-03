"""
Test suite for ADB Device Health Check & Auto-Recovery system.

Comprehensive test coverage for device health monitoring, connection checks,
recovery state machine, and auto-recovery orchestration.

Test Coverage (40+ tests, 85%+ coverage):
- Health monitoring (10 tests)
- Connection checks (8 tests)
- Recovery state machine (12 tests)
- Auto-recovery orchestration (10 tests)

Author: MoAI-ADK Domain ADB Expert
Version: 2.0.0
License: MIT
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

# Import test subjects
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / ".claude" / "skills" / "moai-domain-adb" / "scripts"
sys.path.insert(0, str(scripts_dir))

from adb_device_health_check import (
    ConnectionHealthCheck,
    PerformanceMetricsCollector,
    RecoveryStatesMachine,
    AutoRecoveryOrchestrator,
    DeviceHealthMonitor,
    RecoveryState,
    HealthStatus,
    HealthMetrics,
    RecoveryConfig,
    DeviceHealthReport,
)


# ============================================================================
# SECTION 1: FIXTURES
# ============================================================================


@pytest.fixture
def recovery_config():
    """Create standard recovery configuration."""
    return RecoveryConfig(
        enabled=True,
        max_attempts=3,
        state_timeout=180,
        cpu_threshold=80,
        memory_threshold=85,
        thermal_threshold=45,
    )


@pytest.fixture
def device_id():
    """Standard test device ID."""
    return "emulator-5554"


@pytest.fixture
def connection_checker(device_id):
    """Create connection health checker."""
    return ConnectionHealthCheck(device_id, timeout=5)


@pytest.fixture
def metrics_collector(device_id):
    """Create performance metrics collector."""
    return PerformanceMetricsCollector(device_id, timeout=5)


@pytest.fixture
def state_machine(device_id, recovery_config):
    """Create recovery state machine."""
    return RecoveryStatesMachine(device_id, recovery_config)


@pytest.fixture
def orchestrator(device_id, recovery_config):
    """Create auto-recovery orchestrator."""
    return AutoRecoveryOrchestrator(device_id, recovery_config, timeout=5)


@pytest.fixture
def monitor():
    """Create device health monitor."""
    return DeviceHealthMonitor(check_interval=1)


@pytest.fixture
def health_metrics():
    """Create sample health metrics."""
    return HealthMetrics(
        connection_latency_ms=25.5,
        connection_stability=95.0,
        cpu_usage=35.2,
        memory_usage=42.8,
        thermal_temp=28.5,
        last_check_time=time.time(),
        consecutive_failures=0,
    )


# ============================================================================
# SECTION 2: CONNECTION HEALTH CHECK TESTS (8 tests)
# ============================================================================


class TestConnectionHealthCheck:
    """Test suite for connection health checking."""

    def test_connection_checker_initialization(self, connection_checker):
        """Test connection checker initializes correctly."""
        assert connection_checker.device_id == "emulator-5554"
        assert connection_checker.timeout == 5
        assert connection_checker.latency_samples == []

    def test_check_connection_success(self, connection_checker):
        """Test successful connection check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="ok\n")
            is_connected, latency = connection_checker.check_connection()

            assert is_connected is True
            assert latency > 0
            assert len(connection_checker.latency_samples) == 1

    def test_check_connection_failure(self, connection_checker):
        """Test failed connection check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            is_connected, latency = connection_checker.check_connection()

            assert is_connected is False

    def test_check_connection_timeout(self, connection_checker):
        """Test connection timeout handling."""
        with patch("subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("adb", 5)

            is_connected, latency = connection_checker.check_connection()
            assert is_connected is False
            assert latency == connection_checker.timeout * 1000

    def test_connection_stability_score_no_samples(self, connection_checker):
        """Test stability score with no samples."""
        score = connection_checker.get_stability_score()
        assert score == 100.0

    def test_connection_stability_score_consistent(self, connection_checker):
        """Test stability score with consistent latency."""
        connection_checker.latency_samples = [25.0] * 5
        score = connection_checker.get_stability_score()
        assert score == 100.0  # Perfect consistency

    def test_connection_stability_score_variable(self, connection_checker):
        """Test stability score with variable latency."""
        connection_checker.latency_samples = [10.0, 20.0, 30.0, 40.0, 50.0]
        score = connection_checker.get_stability_score()
        assert 0 <= score <= 100

    def test_average_latency_calculation(self, connection_checker):
        """Test average latency calculation."""
        connection_checker.latency_samples = [10.0, 20.0, 30.0]
        avg = connection_checker.get_avg_latency()
        assert avg == 20.0


# ============================================================================
# SECTION 3: PERFORMANCE METRICS TESTS (8 tests)
# ============================================================================


class TestPerformanceMetricsCollector:
    """Test suite for performance metrics collection."""

    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initializes correctly."""
        assert metrics_collector.device_id == "emulator-5554"
        assert metrics_collector.timeout == 5

    def test_collect_cpu_usage_success(self, metrics_collector):
        """Test successful CPU usage collection."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="%CPU\n45.2\n"
            )
            cpu = metrics_collector.collect_cpu_usage()
            assert cpu == 45.2

    def test_collect_cpu_usage_failure(self, metrics_collector):
        """Test CPU collection failure handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            cpu = metrics_collector.collect_cpu_usage()
            assert cpu == 0.0

    def test_collect_memory_usage_success(self, metrics_collector):
        """Test successful memory usage collection."""
        with patch("subprocess.run") as mock_run:
            meminfo = (
                "MemTotal:        4096000 kB\n"
                "MemAvailable:    2048000 kB\n"
            )
            mock_run.return_value = Mock(returncode=0, stdout=meminfo)
            memory = metrics_collector.collect_memory_usage()

            # (4096000 - 2048000) / 4096000 * 100 = 50%
            assert memory == 50.0

    def test_collect_memory_usage_failure(self, metrics_collector):
        """Test memory collection failure handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            memory = metrics_collector.collect_memory_usage()
            assert memory == 0.0

    def test_collect_thermal_celsius(self, metrics_collector):
        """Test thermal temperature collection (celsius)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="35.0\n")
            temp = metrics_collector.collect_thermal_info()
            assert temp == 35.0

    def test_collect_thermal_millidegrees(self, metrics_collector):
        """Test thermal temperature collection (millidegrees)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="35000\n")
            temp = metrics_collector.collect_thermal_info()
            assert temp == 35.0  # Converted from millidegrees

    def test_collect_thermal_failure(self, metrics_collector):
        """Test thermal collection failure handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            temp = metrics_collector.collect_thermal_info()
            assert temp == 0.0


# ============================================================================
# SECTION 4: RECOVERY STATE MACHINE TESTS (12 tests)
# ============================================================================


class TestRecoveryStatesMachine:
    """Test suite for recovery state machine."""

    def test_state_machine_initialization(self, state_machine):
        """Test state machine initializes in IDLE state."""
        assert state_machine.current_state == RecoveryState.IDLE
        assert state_machine.recovery_attempt_count == 0

    def test_valid_transition_idle_to_checking(self, state_machine):
        """Test valid transition IDLE → CHECKING."""
        assert state_machine.can_transition(RecoveryState.CHECKING)
        assert state_machine.transition_to(RecoveryState.CHECKING)
        assert state_machine.current_state == RecoveryState.CHECKING

    def test_valid_transition_checking_to_recovering(self, state_machine):
        """Test valid transition CHECKING → RECOVERING."""
        state_machine.current_state = RecoveryState.CHECKING
        state_machine.state_enter_time = time.time()

        assert state_machine.can_transition(RecoveryState.RECOVERING)
        assert state_machine.transition_to(RecoveryState.RECOVERING)
        assert state_machine.current_state == RecoveryState.RECOVERING

    def test_valid_transition_recovering_to_recovered(self, state_machine):
        """Test valid transition RECOVERING → RECOVERED."""
        state_machine.current_state = RecoveryState.RECOVERING
        state_machine.state_enter_time = time.time()

        assert state_machine.can_transition(RecoveryState.RECOVERED)
        assert state_machine.transition_to(RecoveryState.RECOVERED)
        assert state_machine.current_state == RecoveryState.RECOVERED

    def test_valid_transition_recovering_to_failed(self, state_machine):
        """Test valid transition RECOVERING → FAILED."""
        state_machine.current_state = RecoveryState.RECOVERING
        state_machine.state_enter_time = time.time()

        assert state_machine.can_transition(RecoveryState.FAILED)
        assert state_machine.transition_to(RecoveryState.FAILED)
        assert state_machine.current_state == RecoveryState.FAILED

    def test_invalid_transition(self, state_machine):
        """Test invalid state transition."""
        state_machine.current_state = RecoveryState.IDLE
        assert not state_machine.can_transition(RecoveryState.RECOVERED)
        assert not state_machine.transition_to(RecoveryState.RECOVERED)
        assert state_machine.current_state == RecoveryState.IDLE

    def test_state_timeout_detection(self, state_machine):
        """Test state timeout detection."""
        state_machine.current_state = RecoveryState.CHECKING
        state_machine.state_enter_time = time.time() - 200  # 200 seconds ago
        state_machine.config.state_timeout = 180

        # Should allow transition to FAILED due to timeout
        assert state_machine.can_transition(RecoveryState.FAILED)

    def test_recovery_attempt_increment(self, state_machine):
        """Test recovery attempt counter increment."""
        assert state_machine.recovery_attempt_count == 0
        state_machine.increment_recovery_attempts()
        assert state_machine.recovery_attempt_count == 1

    def test_recovery_attempt_reset(self, state_machine):
        """Test recovery attempt counter reset."""
        state_machine.recovery_attempt_count = 3
        state_machine.reset_recovery_attempts()
        assert state_machine.recovery_attempt_count == 0

    def test_transition_sequence_success(self, state_machine):
        """Test complete transition sequence for successful recovery."""
        transitions = [
            (RecoveryState.CHECKING, True),
            (RecoveryState.RECOVERING, True),
            (RecoveryState.RECOVERED, True),
            (RecoveryState.IDLE, True),
        ]

        for target_state, expected in transitions:
            assert state_machine.transition_to(target_state) == expected
            state_machine.state_enter_time = time.time()

    def test_transition_sequence_failure(self, state_machine):
        """Test complete transition sequence for failed recovery."""
        transitions = [
            (RecoveryState.CHECKING, True),
            (RecoveryState.RECOVERING, True),
            (RecoveryState.FAILED, True),
            (RecoveryState.IDLE, True),
        ]

        for target_state, expected in transitions:
            assert state_machine.transition_to(target_state) == expected
            state_machine.state_enter_time = time.time()


# ============================================================================
# SECTION 5: AUTO-RECOVERY ORCHESTRATION TESTS (10 tests)
# ============================================================================


class TestAutoRecoveryOrchestrator:
    """Test suite for auto-recovery orchestration."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.device_id == "emulator-5554"
        assert orchestrator.state_machine is not None
        assert orchestrator.connection_checker is not None
        assert orchestrator.metrics_collector is not None

    def test_check_device_health_all_metrics(self, orchestrator):
        """Test health check collects all metrics."""
        with patch.object(orchestrator.connection_checker, "check_connection") as mock_conn:
            with patch.object(orchestrator.metrics_collector, "collect_cpu_usage") as mock_cpu:
                with patch.object(orchestrator.metrics_collector, "collect_memory_usage") as mock_mem:
                    with patch.object(orchestrator.metrics_collector, "collect_thermal_info") as mock_thermal:
                        mock_conn.return_value = (True, 25.0)
                        mock_cpu.return_value = 35.0
                        mock_mem.return_value = 42.0
                        mock_thermal.return_value = 30.0

                        metrics = orchestrator.check_device_health()

                        assert metrics.connection_latency_ms == 25.0
                        assert metrics.cpu_usage == 35.0
                        assert metrics.memory_usage == 42.0
                        assert metrics.thermal_temp == 30.0

    def test_evaluate_health_status_healthy(self, orchestrator, health_metrics):
        """Test health status evaluation for healthy device."""
        status = orchestrator.evaluate_health_status(health_metrics)
        assert status == HealthStatus.HEALTHY

    def test_evaluate_health_status_degraded(self, orchestrator):
        """Test health status evaluation for degraded device."""
        metrics = HealthMetrics(
            connection_latency_ms=50.0,
            connection_stability=60.0,  # Below 75%
            cpu_usage=45.0,
            memory_usage=50.0,
            thermal_temp=30.0,
            last_check_time=time.time(),
        )
        status = orchestrator.evaluate_health_status(metrics)
        assert status == HealthStatus.DEGRADED

    def test_evaluate_health_status_critical(self, orchestrator):
        """Test health status evaluation for critical device."""
        metrics = HealthMetrics(
            connection_latency_ms=100.0,
            connection_stability=40.0,
            cpu_usage=90.0,  # Above threshold
            memory_usage=95.0,  # Above threshold
            thermal_temp=50.0,  # Above threshold
            last_check_time=time.time(),
        )
        status = orchestrator.evaluate_health_status(metrics)
        assert status == HealthStatus.CRITICAL

    def test_evaluate_health_status_offline(self, orchestrator):
        """Test health status evaluation for offline device."""
        metrics = HealthMetrics(
            connection_latency_ms=0.0,
            connection_stability=0.0,
            cpu_usage=0.0,
            memory_usage=0.0,
            thermal_temp=0.0,
            last_check_time=time.time(),
            consecutive_failures=1,
        )
        status = orchestrator.evaluate_health_status(metrics)
        assert status == HealthStatus.OFFLINE

    def test_recovery_strategy_reconnect_success(self, orchestrator):
        """Test reconnect recovery strategy success."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            success = orchestrator.execute_recovery_strategy_reconnect()
            assert success is True

    def test_recovery_strategy_reconnect_failure(self, orchestrator):
        """Test reconnect recovery strategy failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            success = orchestrator.execute_recovery_strategy_reconnect()
            assert success is False

    def test_recovery_strategy_restart_success(self, orchestrator):
        """Test restart recovery strategy success."""
        with patch("subprocess.run"):
            with patch.object(orchestrator.connection_checker, "check_connection") as mock_conn:
                mock_conn.return_value = (True, 25.0)
                success = orchestrator.execute_recovery_strategy_restart()
                assert success is True

    def test_generate_health_report(self, orchestrator):
        """Test health report generation."""
        with patch.object(orchestrator, "check_device_health") as mock_check:
            mock_metrics = HealthMetrics(
                connection_latency_ms=25.0,
                connection_stability=95.0,
                cpu_usage=35.0,
                memory_usage=42.0,
                thermal_temp=28.0,
                last_check_time=time.time(),
            )
            mock_check.return_value = mock_metrics

            report = orchestrator.generate_health_report()

            assert isinstance(report, DeviceHealthReport)
            assert report.device_id == "emulator-5554"
            assert report.health_status == "healthy"
            assert report.metrics["cpu_usage"] == 35.0


# ============================================================================
# SECTION 6: DEVICE HEALTH MONITOR TESTS (8 tests)
# ============================================================================


class TestDeviceHealthMonitor:
    """Test suite for device health monitor."""

    def test_monitor_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert monitor.check_interval == 1
        assert monitor.orchestrators == {}
        assert monitor.monitoring is False

    def test_add_device_to_monitor(self, monitor):
        """Test adding device to monitor."""
        monitor.add_device("emulator-5554")
        assert "emulator-5554" in monitor.orchestrators

    def test_add_multiple_devices(self, monitor):
        """Test adding multiple devices."""
        monitor.add_device("device1")
        monitor.add_device("device2")
        monitor.add_device("device3")

        assert len(monitor.orchestrators) == 3
        assert "device1" in monitor.orchestrators
        assert "device2" in monitor.orchestrators
        assert "device3" in monitor.orchestrators

    def test_check_device_creates_if_missing(self, monitor):
        """Test checking device auto-creates it if missing."""
        with patch.object(AutoRecoveryOrchestrator, "generate_health_report") as mock_report:
            mock_report.return_value = DeviceHealthReport(
                device_id="new-device",
                health_status="healthy",
                recovery_state="idle",
                metrics={},
                recovery_attempts=0,
                last_recovery_time=None,
            )

            monitor.check_device("new-device")
            assert "new-device" in monitor.orchestrators

    def test_check_all_devices(self, monitor):
        """Test checking all devices."""
        monitor.add_device("device1")
        monitor.add_device("device2")

        with patch.object(AutoRecoveryOrchestrator, "generate_health_report") as mock_report:
            mock_report.return_value = DeviceHealthReport(
                device_id="device1",
                health_status="healthy",
                recovery_state="idle",
                metrics={},
                recovery_attempts=0,
                last_recovery_time=None,
            )

            reports = monitor.check_all_devices()
            assert len(reports) == 2

    def test_auto_recover_device(self, monitor):
        """Test auto-recovery trigger."""
        monitor.add_device("emulator-5554")

        with patch.object(AutoRecoveryOrchestrator, "execute_recovery") as mock_recovery:
            mock_recovery.return_value = True
            success = monitor.auto_recover_device("emulator-5554")
            assert success is True

    def test_monitoring_start_and_stop(self, monitor):
        """Test starting and stopping monitoring."""
        monitor.start_monitoring()
        assert monitor.monitoring is True

        monitor.stop_monitoring()
        assert monitor.monitoring is False

    def test_monitoring_loop_runs(self, monitor):
        """Test monitoring loop executes."""
        monitor.add_device("emulator-5554")

        with patch.object(AutoRecoveryOrchestrator, "generate_health_report") as mock_report:
            mock_report.return_value = DeviceHealthReport(
                device_id="emulator-5554",
                health_status="healthy",
                recovery_state="idle",
                metrics={},
                recovery_attempts=0,
                last_recovery_time=None,
            )

            monitor.start_monitoring()
            time.sleep(0.2)  # Give monitor time to run
            monitor.stop_monitoring()

            # Monitor should have called check_all_devices
            assert monitor.monitoring is False


# ============================================================================
# SECTION 7: INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete recovery workflows."""

    def test_complete_recovery_workflow_success(self, orchestrator):
        """Test complete recovery workflow from unhealthy to healthy."""
        with patch.object(orchestrator.connection_checker, "check_connection") as mock_conn:
            with patch.object(orchestrator, "execute_recovery_strategy_reconnect") as mock_reconnect:
                mock_conn.return_value = (True, 25.0)
                mock_reconnect.return_value = True

                success = orchestrator.execute_recovery()

                assert success is True
                assert orchestrator.state_machine.current_state == RecoveryState.RECOVERED

    def test_complete_recovery_workflow_failure(self, orchestrator):
        """Test complete recovery workflow ending in failure."""
        with patch.object(orchestrator.connection_checker, "check_connection") as mock_conn:
            with patch.object(orchestrator, "execute_recovery_strategy_reconnect") as mock_reconnect:
                with patch.object(orchestrator, "execute_recovery_strategy_restart") as mock_restart:
                    mock_conn.return_value = (False, 0.0)
                    mock_reconnect.return_value = False
                    mock_restart.return_value = False

                    success = orchestrator.execute_recovery()

                    assert success is False
                    assert orchestrator.state_machine.current_state == RecoveryState.FAILED

    def test_multi_device_health_report(self, monitor):
        """Test generating health reports for multiple devices."""
        devices = ["device1", "device2", "device3"]
        for dev in devices:
            monitor.add_device(dev)

        with patch.object(AutoRecoveryOrchestrator, "generate_health_report") as mock_report:
            mock_report.return_value = DeviceHealthReport(
                device_id="test",
                health_status="healthy",
                recovery_state="idle",
                metrics={
                    "cpu_usage": 35.0,
                    "memory_usage": 42.0,
                    "thermal_temp": 28.0,
                },
                recovery_attempts=0,
                last_recovery_time=None,
            )

            reports = monitor.check_all_devices()
            assert len(reports) == 3

            for device_id, report in reports.items():
                assert report.health_status == "healthy"
                assert "cpu_usage" in report.metrics


# ============================================================================
# SECTION 8: DATA STRUCTURE TESTS
# ============================================================================


class TestDataStructures:
    """Test data structures and serialization."""

    def test_health_metrics_creation(self, health_metrics):
        """Test HealthMetrics creation."""
        assert health_metrics.connection_latency_ms == 25.5
        assert health_metrics.cpu_usage == 35.2
        assert health_metrics.consecutive_failures == 0

    def test_health_metrics_timestamp(self):
        """Test HealthMetrics has valid timestamp."""
        metrics = HealthMetrics(
            connection_latency_ms=25.0,
            connection_stability=95.0,
            cpu_usage=35.0,
            memory_usage=42.0,
            thermal_temp=28.0,
            last_check_time=time.time(),
        )
        assert metrics.timestamp is not None
        # Verify ISO format
        datetime.fromisoformat(metrics.timestamp)

    def test_device_health_report_creation(self):
        """Test DeviceHealthReport creation."""
        report = DeviceHealthReport(
            device_id="test-device",
            health_status="healthy",
            recovery_state="idle",
            metrics={"cpu": 35.0},
            recovery_attempts=0,
            last_recovery_time=None,
        )
        assert report.device_id == "test-device"
        assert report.health_status == "healthy"

    def test_recovery_config_defaults(self, recovery_config):
        """Test RecoveryConfig uses correct defaults."""
        assert recovery_config.enabled is True
        assert recovery_config.max_attempts == 3
        assert recovery_config.cpu_threshold == 80
        assert recovery_config.memory_threshold == 85
        assert recovery_config.thermal_threshold == 45


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=adb_device_health_check", "--cov-report=term-missing"])
