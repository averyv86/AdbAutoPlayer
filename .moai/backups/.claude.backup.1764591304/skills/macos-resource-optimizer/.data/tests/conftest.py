"""
Pytest configuration and fixtures for macOS Resource Optimizer tests

Provides:
- pytest-asyncio configuration
- Shared test fixtures
- Mock data factories
- Common test utilities
"""

import pytest
import pytest_asyncio
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for all tests"""
    return asyncio.DefaultEventLoopPolicy()


# Mock Data Factories

class MockMetricsFactory:
    """Factory for creating mock metrics objects"""

    @staticmethod
    def cpu_metrics(
        usage_percent: float = 45.2,
        core_count: int = 8,
        temperature: float = 65.0,
        throttling: bool = False
    ) -> Dict[str, Any]:
        """Create mock CPU metrics"""
        return {
            "usage_percent": usage_percent,
            "core_count": core_count,
            "per_core_usage": [usage_percent + (i * 0.5) for i in range(core_count)],
            "temperature": temperature,
            "frequency_mhz": 2400 if not throttling else 1800,
            "throttling_detected": throttling,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def memory_metrics(
        usage_percent: float = 63.75,
        total_gb: float = 16.0,
        swap_usage_percent: float = 0.0
    ) -> Dict[str, Any]:
        """Create mock memory metrics"""
        used_gb = total_gb * (usage_percent / 100)
        swap_used = 8.0 * (swap_usage_percent / 100)

        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": total_gb - used_gb,
            "usage_percent": usage_percent,
            "swap_used_gb": swap_used,
            "swap_total_gb": 8.0,
            "page_faults": 1250000 if usage_percent > 80 else 500000,
            "compression_ratio": 2.3 if usage_percent > 80 else 1.5,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def disk_metrics(
        usage_percent: float = 80.0,
        total_gb: float = 256.0,
        io_wait_percent: float = 12.5
    ) -> Dict[str, Any]:
        """Create mock disk metrics"""
        used_gb = total_gb * (usage_percent / 100)

        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": total_gb - used_gb,
            "usage_percent": usage_percent,
            "read_speed_mbs": 350.5,
            "write_speed_mbs": 280.2,
            "queue_depth": 4 if usage_percent < 85 else 12,
            "io_wait_percent": io_wait_percent,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def network_metrics(
        bandwidth_usage_percent: float = 65.0,
        packet_loss_percent: float = 0.08,
        latency_ms: float = 45.2
    ) -> Dict[str, Any]:
        """Create mock network metrics"""
        return {
            "bytes_sent_mb": 1024.5,
            "bytes_recv_mb": 2048.3,
            "packets_sent": 5000000,
            "packets_recv": 6000000,
            "packets_dropped": int(11000000 * (packet_loss_percent / 100)),
            "latency_ms": latency_ms,
            "packet_loss_percent": packet_loss_percent,
            "bandwidth_usage_percent": bandwidth_usage_percent,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def battery_metrics(
        charge_percent: float = 85.0,
        health_percent: float = 95.0,
        temperature_celsius: float = 35.0
    ) -> Dict[str, Any]:
        """Create mock battery metrics"""
        return {
            "charge_percent": charge_percent,
            "health_percent": health_percent,
            "time_remaining_minutes": int(charge_percent * 5),
            "is_charging": False,
            "cycle_count": 250,
            "max_capacity_mah": 5000.0,
            "current_capacity_mah": 5000.0 * (charge_percent / 100),
            "temperature_celsius": temperature_celsius,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def thermal_metrics(
        cpu_temp_celsius: float = 65.0,
        gpu_temp_celsius: float = 58.0,
        throttling: bool = False
    ) -> Dict[str, Any]:
        """Create mock thermal metrics"""
        return {
            "cpu_temp_celsius": cpu_temp_celsius,
            "gpu_temp_celsius": gpu_temp_celsius,
            "ssd_temp_celsius": cpu_temp_celsius - 20,
            "ambient_temp_celsius": 22.0,
            "max_temp_celsius": max(cpu_temp_celsius, gpu_temp_celsius),
            "throttling_active": throttling,
            "fan_speed_rpm": 3500 if not throttling else 7500,
            "fan_speed_percent": 65.0 if not throttling else 100.0,
            "timestamp": datetime.now().isoformat()
        }


@pytest.fixture
def metrics_factory():
    """Fixture providing metrics factory"""
    return MockMetricsFactory()


# Mock Subprocess Fixtures

@pytest.fixture
def mock_subprocess_success():
    """Fixture providing successful subprocess mock"""
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = b'{"status": "success"}'
    mock.stderr = b''
    return mock


@pytest.fixture
def mock_subprocess_timeout():
    """Fixture providing subprocess timeout mock"""
    mock = MagicMock()
    mock.side_effect = asyncio.TimeoutError("Analysis timeout")
    return mock


@pytest.fixture
def mock_subprocess_error():
    """Fixture providing subprocess error mock"""
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout = b''
    mock.stderr = b'Analysis failed'
    return mock


# Async Fixtures

@pytest_asyncio.fixture
async def mock_wrapper():
    """Fixture providing mock PythonEngineWrapper"""
    wrapper = AsyncMock()

    async def mock_analyze(category):
        await asyncio.sleep(0.01)  # Simulate work
        return {"status": "success", "category": category}

    wrapper.execute_analysis = mock_analyze
    wrapper.analyze_cpu = AsyncMock(return_value={"category": "cpu"})
    wrapper.analyze_memory = AsyncMock(return_value={"category": "memory"})
    wrapper.analyze_disk = AsyncMock(return_value={"category": "disk"})
    wrapper.analyze_network = AsyncMock(return_value={"category": "network"})
    wrapper.analyze_battery = AsyncMock(return_value={"category": "battery"})
    wrapper.analyze_thermal = AsyncMock(return_value={"category": "thermal"})

    return wrapper


@pytest_asyncio.fixture
async def mock_analyzer_timeout():
    """Fixture providing timeout-prone analyzer"""
    async def slow_analysis():
        await asyncio.sleep(10)
        return {"status": "success"}

    return slow_analysis


# Utility Fixtures

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture providing temporary directory"""
    return tmp_path


@pytest.fixture
def sample_json_file(tmp_path):
    """Fixture providing sample JSON file"""
    data = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "metrics": {"usage": 50.0}
    }

    json_file = tmp_path / "sample.json"
    json_file.write_text(json.dumps(data))

    return json_file


# Test Markers

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )
    config.addinivalue_line(
        "markers", "timeout: mark test as timeout test (deselect with '-m \"not timeout\"')"
    )
    config.addinivalue_line(
        "markers", "metrics: mark test as metrics parsing test"
    )
    config.addinivalue_line(
        "markers", "recommendations: mark test as recommendations test"
    )
    config.addinivalue_line(
        "markers", "thresholds: mark test as threshold detection test"
    )


# Pytest Hooks

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook for adding test timing information"""
    outcome = yield

    if call.when == "call":
        duration = call.duration
        if duration > 0.5:
            outcome.get_result().outcome = "warning"
            outcome.get_result().longrepr = f"Test slow: {duration:.2f}s"


# Cleanup

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test"""
    yield
    # Cleanup code here if needed
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
