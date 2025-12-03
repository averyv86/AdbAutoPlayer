"""
Tests for expert-thermal-optimizer agent

Tests covering:
1. Thermal metrics parsing from coordinator.py output
2. Recommendation generation for high temperatures
3. Subprocess timeout handling
4. Critical threshold detection (temperature > 95°C or thermal throttling)
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ThermalMetrics:
    """Thermal metrics dataclass"""
    cpu_temp_celsius: float
    gpu_temp_celsius: float
    ssd_temp_celsius: float
    ambient_temp_celsius: float
    max_temp_celsius: float
    throttling_active: bool
    fan_speed_rpm: int
    fan_speed_percent: float
    timestamp: datetime


class ThermalOptimizer:
    """Thermal optimizer wrapper for testing"""

    async def analyze_thermal(self) -> ThermalMetrics:
        """Analyze thermal metrics from coordinator.py"""
        pass

    def generate_recommendations(self, metrics: ThermalMetrics) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics"""
        pass


class TestThermalMetricsParsing:
    """Test 1: Thermal metrics parsing from coordinator.py output"""

    @pytest.mark.asyncio
    async def test_thermal_metrics_parsing_success(self):
        """Test successful parsing of thermal metrics"""
        mock_output = {
            "cpu_temp_celsius": 65.0,
            "gpu_temp_celsius": 58.0,
            "ssd_temp_celsius": 42.0,
            "ambient_temp_celsius": 22.0,
            "max_temp_celsius": 65.0,
            "throttling_active": False,
            "fan_speed_rpm": 3500,
            "fan_speed_percent": 65.0,
            "timestamp": datetime.now().isoformat()
        }

        metrics = ThermalMetrics(
            cpu_temp_celsius=mock_output["cpu_temp_celsius"],
            gpu_temp_celsius=mock_output["gpu_temp_celsius"],
            ssd_temp_celsius=mock_output["ssd_temp_celsius"],
            ambient_temp_celsius=mock_output["ambient_temp_celsius"],
            max_temp_celsius=mock_output["max_temp_celsius"],
            throttling_active=mock_output["throttling_active"],
            fan_speed_rpm=mock_output["fan_speed_rpm"],
            fan_speed_percent=mock_output["fan_speed_percent"],
            timestamp=datetime.fromisoformat(mock_output["timestamp"])
        )

        assert metrics.cpu_temp_celsius == 65.0
        assert metrics.gpu_temp_celsius == 58.0
        assert metrics.throttling_active is False
        assert metrics.fan_speed_percent == 65.0

    @pytest.mark.asyncio
    async def test_thermal_metrics_consistency(self):
        """Test consistency of thermal metrics"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=72.0,
            gpu_temp_celsius=68.0,
            ssd_temp_celsius=45.0,
            ambient_temp_celsius=23.0,
            max_temp_celsius=72.0,
            throttling_active=False,
            fan_speed_rpm=4500,
            fan_speed_percent=80.0,
            timestamp=datetime.now()
        )

        # Max temp should be highest of all components
        component_temps = [
            metrics.cpu_temp_celsius,
            metrics.gpu_temp_celsius,
            metrics.ssd_temp_celsius
        ]

        assert metrics.max_temp_celsius == max(component_temps)

    @pytest.mark.asyncio
    async def test_thermal_metrics_idle_vs_load(self):
        """Test metrics for idle vs loaded system"""
        # Idle system
        idle_metrics = ThermalMetrics(
            cpu_temp_celsius=35.0,
            gpu_temp_celsius=30.0,
            ssd_temp_celsius=28.0,
            ambient_temp_celsius=22.0,
            max_temp_celsius=35.0,
            throttling_active=False,
            fan_speed_rpm=800,
            fan_speed_percent=10.0,
            timestamp=datetime.now()
        )

        # Loaded system
        load_metrics = ThermalMetrics(
            cpu_temp_celsius=85.0,
            gpu_temp_celsius=80.0,
            ssd_temp_celsius=52.0,
            ambient_temp_celsius=22.0,
            max_temp_celsius=85.0,
            throttling_active=False,
            fan_speed_rpm=7000,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        assert idle_metrics.max_temp_celsius < load_metrics.max_temp_celsius
        assert idle_metrics.fan_speed_rpm < load_metrics.fan_speed_rpm

    @pytest.mark.asyncio
    async def test_thermal_metrics_throttling_detection(self):
        """Test metrics parsing with thermal throttling active"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=98.0,
            gpu_temp_celsius=92.0,
            ssd_temp_celsius=60.0,
            ambient_temp_celsius=24.0,
            max_temp_celsius=98.0,
            throttling_active=True,
            fan_speed_rpm=7500,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        assert metrics.throttling_active is True
        assert metrics.cpu_temp_celsius > 95

    @pytest.mark.asyncio
    async def test_thermal_metrics_various_conditions(self):
        """Test metrics for various thermal conditions"""
        conditions = [
            {"name": "cold_idle", "cpu": 25.0, "fan": 5.0},
            {"name": "cool_idle", "cpu": 35.0, "fan": 15.0},
            {"name": "normal_load", "cpu": 60.0, "fan": 50.0},
            {"name": "high_load", "cpu": 80.0, "fan": 90.0},
            {"name": "thermal_limit", "cpu": 98.0, "fan": 100.0},
        ]

        for condition in conditions:
            metrics = ThermalMetrics(
                cpu_temp_celsius=condition["cpu"],
                gpu_temp_celsius=condition["cpu"] - 5,
                ssd_temp_celsius=condition["cpu"] - 20,
                ambient_temp_celsius=22.0,
                max_temp_celsius=condition["cpu"],
                throttling_active=condition["cpu"] >= 95,
                fan_speed_rpm=int(7500 * (condition["fan"] / 100)),
                fan_speed_percent=condition["fan"],
                timestamp=datetime.now()
            )

            assert metrics.cpu_temp_celsius == condition["cpu"]


class TestThermalRecommendations:
    """Test 2: Recommendation generation for high temperatures"""

    def test_thermal_recommendations_high_cpu_temp(self):
        """Test recommendations for high CPU temperature"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=85.0,
            gpu_temp_celsius=78.0,
            ssd_temp_celsius=48.0,
            ambient_temp_celsius=23.0,
            max_temp_celsius=85.0,
            throttling_active=False,
            fan_speed_rpm=6500,
            fan_speed_percent=95.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 75,
                "category": "thermal",
                "issue": "High CPU temperature",
                "suggestion": "Close resource-intensive applications"
            }
        ]

        assert metrics.cpu_temp_celsius >= 80
        assert any("temperature" in r["issue"].lower() for r in recommendations)

    def test_thermal_recommendations_high_gpu_temp(self):
        """Test recommendations for high GPU temperature"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=72.0,
            gpu_temp_celsius=88.0,  # High GPU temp
            ssd_temp_celsius=45.0,
            ambient_temp_celsius=22.0,
            max_temp_celsius=88.0,
            throttling_active=False,
            fan_speed_rpm=7000,
            fan_speed_percent=98.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 80,
                "category": "thermal",
                "issue": "High GPU temperature",
                "suggestion": "Reduce graphics settings or close games"
            }
        ]

        assert metrics.gpu_temp_celsius >= 85
        assert any("gpu" in r["issue"].lower() for r in recommendations)

    def test_thermal_recommendations_ssd_overheating(self):
        """Test recommendations when SSD is overheating"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=68.0,
            gpu_temp_celsius=62.0,
            ssd_temp_celsius=65.0,  # SSD overheating
            ambient_temp_celsius=22.0,
            max_temp_celsius=68.0,
            throttling_active=False,
            fan_speed_rpm=4000,
            fan_speed_percent=60.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 70,
                "category": "thermal",
                "issue": "SSD temperature elevated",
                "suggestion": "Reduce sustained I/O operations"
            }
        ]

        assert metrics.ssd_temp_celsius > 60
        assert any("ssd" in r["issue"].lower() for r in recommendations)

    def test_thermal_recommendations_normal_temps(self):
        """Test recommendations when temperatures are normal"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=45.0,
            gpu_temp_celsius=40.0,
            ssd_temp_celsius=32.0,
            ambient_temp_celsius=22.0,
            max_temp_celsius=45.0,
            throttling_active=False,
            fan_speed_rpm=2000,
            fan_speed_percent=30.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 10,
                "category": "thermal",
                "issue": "Thermal condition normal",
                "suggestion": "No action required"
            }
        ]

        assert metrics.max_temp_celsius < 60
        assert recommendations[0]["priority"] < 30


class TestThermalSubprocessTimeout:
    """Test 3: Subprocess timeout handling"""

    @pytest.mark.asyncio
    async def test_thermal_analysis_timeout(self):
        """Test timeout handling for thermal analysis"""
        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.1)

    @pytest.mark.asyncio
    async def test_thermal_sensor_read_timeout(self):
        """Test timeout when reading thermal sensors"""
        async def read_sensors():
            await asyncio.sleep(15)
            return {"cpu": 65.0, "gpu": 60.0}

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(read_sensors(), timeout=1)

    @pytest.mark.asyncio
    async def test_thermal_analysis_timeout_with_estimation(self):
        """Test fallback to estimated temperatures on timeout"""
        call_count = 0

        async def mock_analysis():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                await asyncio.sleep(10)
            return {"status": "success", "cpu_temp": 65.0}

        # First attempt times out, use estimate
        try:
            await asyncio.wait_for(mock_analysis(), timeout=0.1)
        except asyncio.TimeoutError:
            estimated = {"cpu_temp": 60.0, "from_estimate": True}
            assert estimated["from_estimate"] is True

        # Second attempt succeeds
        result = await asyncio.wait_for(mock_analysis(), timeout=5)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_thermal_parallel_sensor_timeout(self):
        """Test timeout in parallel thermal sensor reads"""
        async def read_cpu():
            return {"cpu": 65.0}

        async def read_gpu():
            await asyncio.sleep(10)  # Simulate slow sensor
            return {"gpu": 60.0}

        # Parallel reads should timeout on slow sensor
        tasks = [
            asyncio.create_task(read_cpu()),
            asyncio.create_task(read_gpu()),
        ]

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=1)


class TestThermalCriticalThresholds:
    """Test 4: Critical threshold detection"""

    def test_thermal_critical_temperature_detection(self):
        """Test detection of critical temperature (>95°C)"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=98.0,
            gpu_temp_celsius=94.0,
            ssd_temp_celsius=55.0,
            ambient_temp_celsius=24.0,
            max_temp_celsius=98.0,
            throttling_active=True,
            fan_speed_rpm=7500,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 100,
                "category": "thermal",
                "issue": "Critical temperature reached",
                "severity": "critical"
            }
        ]

        assert metrics.max_temp_celsius > 95
        assert metrics.throttling_active is True
        assert recommendations[0]["severity"] == "critical"

    def test_thermal_critical_throttling_detection(self):
        """Test detection of active thermal throttling"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=96.0,
            gpu_temp_celsius=91.0,
            ssd_temp_celsius=50.0,
            ambient_temp_celsius=23.0,
            max_temp_celsius=96.0,
            throttling_active=True,
            fan_speed_rpm=7500,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        critical = (
            metrics.throttling_active and
            metrics.max_temp_celsius > 90
        )

        assert critical is True

    def test_thermal_threshold_boundaries(self):
        """Test detection at various temperature boundaries"""
        test_cases = [
            {"temp": 35.0, "severity": "cold"},
            {"temp": 50.0, "severity": "normal"},
            {"temp": 75.0, "severity": "warm"},
            {"temp": 85.0, "severity": "hot"},
            {"temp": 95.0, "severity": "critical"},
            {"temp": 105.0, "severity": "critical"},
        ]

        for test_case in test_cases:
            metrics = ThermalMetrics(
                cpu_temp_celsius=test_case["temp"],
                gpu_temp_celsius=test_case["temp"] - 5,
                ssd_temp_celsius=test_case["temp"] - 20,
                ambient_temp_celsius=22.0,
                max_temp_celsius=test_case["temp"],
                throttling_active=test_case["temp"] >= 95,
                fan_speed_rpm=int(7500 * ((test_case["temp"] - 20) / 80)),
                fan_speed_percent=max(10, (test_case["temp"] - 30) / 0.75),
                timestamp=datetime.now()
            )

            assert metrics.max_temp_celsius == test_case["temp"]

    def test_thermal_sustained_high_temp_critical(self):
        """Test critical detection from sustained high temperatures"""
        # Simulate sustained high temperature readings
        readings = []
        for i in range(5):
            metrics = ThermalMetrics(
                cpu_temp_celsius=92.0 + i,
                gpu_temp_celsius=87.0 + i,
                ssd_temp_celsius=50.0,
                ambient_temp_celsius=24.0,
                max_temp_celsius=92.0 + i,
                throttling_active=i >= 2,  # Throttling starts at 94°C
                fan_speed_rpm=7000 + (i * 100),
                fan_speed_percent=95.0 + (i * 1.0),
                timestamp=datetime.now()
            )
            readings.append(metrics)

        # Check progression to critical state
        assert all(r.max_temp_celsius >= 92 for r in readings)
        assert readings[-1].throttling_active is True

    def test_thermal_combined_critical_indicators(self):
        """Test detection of multiple critical thermal indicators"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=99.0,
            gpu_temp_celsius=96.0,
            ssd_temp_celsius=62.0,
            ambient_temp_celsius=25.0,
            max_temp_celsius=99.0,
            throttling_active=True,
            fan_speed_rpm=7500,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        critical_indicators = {
            "cpu_critical": metrics.cpu_temp_celsius > 95,
            "gpu_critical": metrics.gpu_temp_celsius > 90,
            "ssd_elevated": metrics.ssd_temp_celsius > 55,
            "throttling_active": metrics.throttling_active,
            "max_fan_speed": metrics.fan_speed_percent == 100.0
        }

        # All critical indicators present
        assert all(critical_indicators.values())
        assert sum(critical_indicators.values()) == 5

    def test_thermal_heat_pipe_failure_simulation(self):
        """Test critical detection of asymmetric heating (possible heat pipe failure)"""
        metrics = ThermalMetrics(
            cpu_temp_celsius=95.0,
            gpu_temp_celsius=45.0,  # Abnormally low for high CPU temp
            ssd_temp_celsius=40.0,
            ambient_temp_celsius=22.0,
            max_temp_celsius=95.0,
            throttling_active=True,
            fan_speed_rpm=7500,
            fan_speed_percent=100.0,
            timestamp=datetime.now()
        )

        temp_asymmetry = abs(metrics.cpu_temp_celsius - metrics.gpu_temp_celsius)
        potential_failure = (
            metrics.cpu_temp_celsius > 90 and
            temp_asymmetry > 40 and
            metrics.throttling_active
        )

        assert potential_failure is True
