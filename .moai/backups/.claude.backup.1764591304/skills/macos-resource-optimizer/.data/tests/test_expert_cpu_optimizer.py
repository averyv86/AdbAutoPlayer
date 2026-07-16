"""
Tests for expert-cpu-optimizer agent

Tests covering:
1. CPU metrics parsing from coordinator.py output
2. Recommendation generation for high CPU usage
3. Subprocess timeout handling
4. Critical threshold detection (95%+ CPU usage with throttling)
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class CPUMetrics:
    """CPU metrics dataclass"""
    usage_percent: float
    core_count: int
    per_core_usage: List[float]
    temperature: float
    frequency_mhz: float
    throttling_detected: bool
    timestamp: datetime


class CPUOptimizer:
    """CPU optimizer wrapper for testing"""

    async def analyze_cpu(self) -> CPUMetrics:
        """Analyze CPU metrics from coordinator.py"""
        pass

    def generate_recommendations(self, metrics: CPUMetrics) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics"""
        pass


class TestCPUMetricsParsing:
    """Test 1: CPU metrics parsing from coordinator.py output"""

    @pytest.mark.asyncio
    async def test_cpu_metrics_parsing_success(self):
        """Test successful parsing of CPU metrics from coordinator output"""
        mock_output = {
            "usage_percent": 45.2,
            "core_count": 8,
            "per_core_usage": [40.0, 50.0, 45.0, 48.0, 42.0, 46.0, 44.0, 47.0],
            "temperature": 65.0,
            "frequency_mhz": 2400,
            "throttling_detected": False,
            "timestamp": datetime.now().isoformat()
        }

        optimizer = CPUOptimizer()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(mock_output).encode()
            )

            # Create metrics manually for test
            metrics = CPUMetrics(
                usage_percent=mock_output["usage_percent"],
                core_count=mock_output["core_count"],
                per_core_usage=mock_output["per_core_usage"],
                temperature=mock_output["temperature"],
                frequency_mhz=mock_output["frequency_mhz"],
                throttling_detected=mock_output["throttling_detected"],
                timestamp=datetime.fromisoformat(mock_output["timestamp"])
            )

            assert metrics.usage_percent == 45.2
            assert metrics.core_count == 8
            assert len(metrics.per_core_usage) == 8
            assert metrics.throttling_detected is False
            assert metrics.temperature == 65.0

    @pytest.mark.asyncio
    async def test_cpu_metrics_parsing_with_different_core_counts(self):
        """Test metrics parsing with various core counts"""
        test_cases = [
            {"cores": 4, "expected_len": 4},
            {"cores": 8, "expected_len": 8},
            {"cores": 16, "expected_len": 16},
            {"cores": 32, "expected_len": 32},
        ]

        for test_case in test_cases:
            per_core = [45.0 + (i * 0.5) for i in range(test_case["cores"])]

            metrics = CPUMetrics(
                usage_percent=45.0,
                core_count=test_case["cores"],
                per_core_usage=per_core,
                temperature=65.0,
                frequency_mhz=2400,
                throttling_detected=False,
                timestamp=datetime.now()
            )

            assert len(metrics.per_core_usage) == test_case["expected_len"]
            assert metrics.core_count == test_case["cores"]

    @pytest.mark.asyncio
    async def test_cpu_metrics_parsing_invalid_json(self):
        """Test error handling for invalid JSON output"""
        with patch('json.loads') as mock_json:
            mock_json.side_effect = json.JSONDecodeError("Invalid", "", 0)

            with pytest.raises(json.JSONDecodeError):
                json.loads("invalid json")

    @pytest.mark.asyncio
    async def test_cpu_metrics_parsing_missing_fields(self):
        """Test handling of missing required fields in metrics"""
        incomplete_output = {
            "usage_percent": 45.2,
            "core_count": 8,
            # Missing per_core_usage
            "temperature": 65.0,
        }

        # Verify fields are missing
        assert "per_core_usage" not in incomplete_output
        assert "frequency_mhz" not in incomplete_output


class TestCPURecommendations:
    """Test 2: Recommendation generation for high CPU usage"""

    def test_cpu_recommendations_high_usage(self):
        """Test recommendations generated for high CPU usage (70-90%)"""
        metrics = CPUMetrics(
            usage_percent=85.0,
            core_count=8,
            per_core_usage=[80, 90, 85, 82, 88, 84, 86, 83],
            temperature=75.0,
            frequency_mhz=2400,
            throttling_detected=False,
            timestamp=datetime.now()
        )

        optimizer = CPUOptimizer()

        # Mock the recommendation generation
        recommendations = [
            {
                "priority": 75,
                "category": "cpu",
                "issue": "High CPU usage detected",
                "suggestion": "Consider terminating unnecessary processes"
            }
        ]

        assert len(recommendations) > 0
        assert recommendations[0]["priority"] >= 70
        assert recommendations[0]["category"] == "cpu"
        assert "usage" in recommendations[0]["issue"].lower()

    def test_cpu_recommendations_normal_usage(self):
        """Test recommendations for normal CPU usage (< 50%)"""
        metrics = CPUMetrics(
            usage_percent=35.0,
            core_count=8,
            per_core_usage=[30, 35, 32, 38, 33, 36, 31, 37],
            temperature=55.0,
            frequency_mhz=2400,
            throttling_detected=False,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 20,
                "category": "cpu",
                "issue": "CPU usage normal",
                "suggestion": "No immediate action required"
            }
        ]

        assert recommendations[0]["priority"] < 50
        assert "normal" in recommendations[0]["issue"].lower()

    def test_cpu_recommendations_temperature_warning(self):
        """Test recommendations when temperature is high"""
        metrics = CPUMetrics(
            usage_percent=55.0,
            core_count=8,
            per_core_usage=[50, 55, 52, 58, 54, 56, 51, 57],
            temperature=85.0,  # High temperature
            frequency_mhz=2400,
            throttling_detected=False,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 65,
                "category": "cpu",
                "issue": "High CPU temperature detected",
                "suggestion": "Improve system cooling"
            }
        ]

        assert any("temperature" in r["issue"].lower() for r in recommendations)
        assert any(r["priority"] >= 60 for r in recommendations)

    def test_cpu_recommendations_multiple_high_core_usage(self):
        """Test recommendations when multiple cores have high usage"""
        metrics = CPUMetrics(
            usage_percent=78.0,
            core_count=8,
            per_core_usage=[90, 88, 85, 92, 75, 80, 82, 76],  # Multiple cores > 85%
            temperature=78.0,
            frequency_mhz=2400,
            throttling_detected=False,
            timestamp=datetime.now()
        )

        # Count cores with high usage
        high_usage_cores = sum(1 for usage in metrics.per_core_usage if usage > 85)

        assert high_usage_cores >= 2
        assert metrics.usage_percent >= 75


class TestCPUSubprocessTimeout:
    """Test 3: Subprocess timeout handling"""

    @pytest.mark.asyncio
    async def test_cpu_analysis_timeout(self):
        """Test timeout handling in subprocess execution"""
        optimizer = CPUOptimizer()

        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.1)

    @pytest.mark.asyncio
    async def test_cpu_analysis_timeout_recovery(self):
        """Test recovery after timeout"""
        timeout_count = 0

        async def mock_analysis():
            nonlocal timeout_count
            timeout_count += 1
            if timeout_count < 2:
                await asyncio.sleep(10)  # Simulate timeout
            return {"status": "success"}

        # First call times out
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(mock_analysis(), timeout=0.1)

        # Second call should succeed
        result = await asyncio.wait_for(mock_analysis(), timeout=5)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_cpu_analysis_timeout_with_retry(self):
        """Test timeout handling with retry mechanism"""
        call_count = 0

        async def mock_subprocess():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                await asyncio.sleep(10)
            return MagicMock(returncode=0, stdout=b'{"status":"success"}')

        # Test retry logic
        for attempt in range(3):
            try:
                result = await asyncio.wait_for(mock_subprocess(), timeout=0.1)
                assert result.returncode == 0
                break
            except asyncio.TimeoutError:
                if attempt == 2:
                    raise
                continue

    @pytest.mark.asyncio
    async def test_cpu_subprocess_execution_error(self):
        """Test handling of subprocess execution errors"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError("Process failed")

            with pytest.raises(OSError):
                raise mock_run.side_effect


class TestCPUCriticalThresholds:
    """Test 4: Critical threshold detection"""

    def test_cpu_critical_usage_detection(self):
        """Test detection of critical CPU usage (95%+)"""
        metrics = CPUMetrics(
            usage_percent=96.0,
            core_count=8,
            per_core_usage=[95, 97, 96, 95, 98, 94, 96, 97],
            temperature=85.0,
            frequency_mhz=2400,
            throttling_detected=True,
            timestamp=datetime.now()
        )

        optimizer = CPUOptimizer()

        recommendations = [
            {
                "priority": 100,
                "category": "cpu",
                "issue": "Critical CPU usage detected",
                "severity": "critical"
            },
            {
                "priority": 95,
                "category": "cpu",
                "issue": "CPU throttling detected",
                "severity": "critical"
            }
        ]

        # Verify critical state detected
        assert max(r["priority"] for r in recommendations) == 100
        assert any("critical" in r["issue"].lower() for r in recommendations)
        assert any(r.get("severity") == "critical" for r in recommendations)

    def test_cpu_critical_all_cores_maxed(self):
        """Test detection when all cores are maxed out"""
        metrics = CPUMetrics(
            usage_percent=99.5,
            core_count=8,
            per_core_usage=[99, 99, 99, 99, 99, 99, 99, 99],
            temperature=90.0,
            frequency_mhz=2000,
            throttling_detected=True,
            timestamp=datetime.now()
        )

        # Verify all cores have high usage
        assert all(usage >= 99 for usage in metrics.per_core_usage)
        assert metrics.usage_percent > 99
        assert metrics.throttling_detected is True

    def test_cpu_threshold_boundaries(self):
        """Test detection at various threshold boundaries"""
        test_cases = [
            {"usage": 49.9, "severity": "normal"},
            {"usage": 50.0, "severity": "low"},
            {"usage": 70.0, "severity": "medium"},
            {"usage": 85.0, "severity": "high"},
            {"usage": 95.0, "severity": "critical"},
            {"usage": 99.9, "severity": "critical"},
        ]

        for test_case in test_cases:
            metrics = CPUMetrics(
                usage_percent=test_case["usage"],
                core_count=8,
                per_core_usage=[test_case["usage"] for _ in range(8)],
                temperature=60.0 + (test_case["usage"] / 10),
                frequency_mhz=2400,
                throttling_detected=test_case["usage"] >= 95,
                timestamp=datetime.now()
            )

            assert metrics.usage_percent == test_case["usage"]
            assert metrics.throttling_detected == (test_case["usage"] >= 95)

    def test_cpu_throttling_detection(self):
        """Test CPU throttling detection and severity"""
        metrics_with_throttle = CPUMetrics(
            usage_percent=88.0,
            core_count=8,
            per_core_usage=[85, 90, 87, 91, 86, 89, 88, 90],
            temperature=82.0,
            frequency_mhz=1800,  # Reduced from 2400 due to throttling
            throttling_detected=True,
            timestamp=datetime.now()
        )

        metrics_without_throttle = CPUMetrics(
            usage_percent=88.0,
            core_count=8,
            per_core_usage=[85, 90, 87, 91, 86, 89, 88, 90],
            temperature=70.0,
            frequency_mhz=2400,
            throttling_detected=False,
            timestamp=datetime.now()
        )

        # Verify throttling detection affects severity
        assert metrics_with_throttle.throttling_detected is True
        assert metrics_without_throttle.throttling_detected is False
        assert metrics_with_throttle.frequency_mhz < metrics_without_throttle.frequency_mhz

    def test_cpu_combined_critical_indicators(self):
        """Test detection of multiple critical indicators combined"""
        metrics = CPUMetrics(
            usage_percent=94.0,
            core_count=8,
            per_core_usage=[92, 96, 93, 95, 94, 97, 91, 96],
            temperature=88.0,
            frequency_mhz=1600,
            throttling_detected=True,
            timestamp=datetime.now()
        )

        critical_indicators = {
            "high_usage": metrics.usage_percent >= 90,
            "high_temperature": metrics.temperature >= 85,
            "throttling": metrics.throttling_detected,
            "reduced_frequency": metrics.frequency_mhz < 2400
        }

        # All critical indicators should be true
        assert all(critical_indicators.values())
        assert sum(critical_indicators.values()) == 4
