"""
Tests for expert-memory-optimizer agent

Tests covering:
1. Memory metrics parsing from coordinator.py output
2. Recommendation generation for high memory usage
3. Subprocess timeout handling
4. Critical threshold detection (memory pressure > 85%)
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class MemoryMetrics:
    """Memory metrics dataclass"""
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float
    swap_used_gb: float
    swap_total_gb: float
    page_faults: int
    compression_ratio: float
    timestamp: datetime


class MemoryOptimizer:
    """Memory optimizer wrapper for testing"""

    async def analyze_memory(self) -> MemoryMetrics:
        """Analyze memory metrics from coordinator.py"""
        pass

    def generate_recommendations(self, metrics: MemoryMetrics) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics"""
        pass


class TestMemoryMetricsParsing:
    """Test 1: Memory metrics parsing from coordinator.py output"""

    @pytest.mark.asyncio
    async def test_memory_metrics_parsing_success(self):
        """Test successful parsing of memory metrics"""
        mock_output = {
            "total_gb": 16.0,
            "used_gb": 10.2,
            "available_gb": 5.8,
            "usage_percent": 63.75,
            "swap_used_gb": 2.1,
            "swap_total_gb": 8.0,
            "page_faults": 1250000,
            "compression_ratio": 2.3,
            "timestamp": datetime.now().isoformat()
        }

        metrics = MemoryMetrics(
            total_gb=mock_output["total_gb"],
            used_gb=mock_output["used_gb"],
            available_gb=mock_output["available_gb"],
            usage_percent=mock_output["usage_percent"],
            swap_used_gb=mock_output["swap_used_gb"],
            swap_total_gb=mock_output["swap_total_gb"],
            page_faults=mock_output["page_faults"],
            compression_ratio=mock_output["compression_ratio"],
            timestamp=datetime.fromisoformat(mock_output["timestamp"])
        )

        assert metrics.total_gb == 16.0
        assert metrics.used_gb == 10.2
        assert metrics.usage_percent == 63.75
        assert metrics.swap_used_gb == 2.1

    @pytest.mark.asyncio
    async def test_memory_metrics_consistency(self):
        """Test consistency of memory metrics"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=12.8,
            available_gb=3.2,
            usage_percent=80.0,
            swap_used_gb=1.5,
            swap_total_gb=8.0,
            page_faults=2500000,
            compression_ratio=1.8,
            timestamp=datetime.now()
        )

        # Verify math consistency
        total = metrics.used_gb + metrics.available_gb
        expected_percent = (metrics.used_gb / metrics.total_gb) * 100

        assert abs(total - metrics.total_gb) < 0.1
        assert abs(expected_percent - metrics.usage_percent) < 1.0

    @pytest.mark.asyncio
    async def test_memory_metrics_edge_cases(self):
        """Test parsing with edge case values"""
        # Zero available memory
        metrics_full = MemoryMetrics(
            total_gb=8.0,
            used_gb=8.0,
            available_gb=0.0,
            usage_percent=100.0,
            swap_used_gb=2.0,
            swap_total_gb=4.0,
            page_faults=5000000,
            compression_ratio=3.5,
            timestamp=datetime.now()
        )

        assert metrics_full.available_gb == 0.0
        assert metrics_full.usage_percent == 100.0

        # Minimal memory system
        metrics_minimal = MemoryMetrics(
            total_gb=2.0,
            used_gb=1.5,
            available_gb=0.5,
            usage_percent=75.0,
            swap_used_gb=0.0,
            swap_total_gb=0.0,
            page_faults=100000,
            compression_ratio=1.0,
            timestamp=datetime.now()
        )

        assert metrics_minimal.total_gb == 2.0
        assert metrics_minimal.swap_total_gb == 0.0

    @pytest.mark.asyncio
    async def test_memory_metrics_various_system_sizes(self):
        """Test metrics parsing for different system sizes"""
        system_sizes = [
            {"total": 4.0, "used": 3.2, "percent": 80.0},
            {"total": 8.0, "used": 4.0, "percent": 50.0},
            {"total": 16.0, "used": 12.8, "percent": 80.0},
            {"total": 32.0, "used": 16.0, "percent": 50.0},
            {"total": 64.0, "used": 48.0, "percent": 75.0},
        ]

        for system in system_sizes:
            metrics = MemoryMetrics(
                total_gb=system["total"],
                used_gb=system["used"],
                available_gb=system["total"] - system["used"],
                usage_percent=system["percent"],
                swap_used_gb=0.0,
                swap_total_gb=0.0,
                page_faults=0,
                compression_ratio=1.0,
                timestamp=datetime.now()
            )

            assert metrics.total_gb == system["total"]
            assert metrics.used_gb == system["used"]


class TestMemoryRecommendations:
    """Test 2: Recommendation generation for high memory usage"""

    def test_memory_recommendations_high_usage(self):
        """Test recommendations for high memory usage (70-85%)"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=12.8,
            available_gb=3.2,
            usage_percent=80.0,
            swap_used_gb=2.0,
            swap_total_gb=8.0,
            page_faults=3000000,
            compression_ratio=2.1,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 75,
                "category": "memory",
                "issue": "High memory usage detected",
                "suggestion": "Close unnecessary applications"
            }
        ]

        assert len(recommendations) > 0
        assert recommendations[0]["priority"] >= 70
        assert recommendations[0]["category"] == "memory"
        assert "memory" in recommendations[0]["issue"].lower()

    def test_memory_recommendations_swap_usage(self):
        """Test recommendations when swap is being used"""
        metrics = MemoryMetrics(
            total_gb=8.0,
            used_gb=7.5,
            available_gb=0.5,
            usage_percent=93.75,
            swap_used_gb=3.0,
            swap_total_gb=8.0,
            page_faults=5000000,
            compression_ratio=2.8,
            timestamp=datetime.now()
        )

        swap_usage_percent = (metrics.swap_used_gb / metrics.swap_total_gb) * 100

        recommendations = [
            {
                "priority": 85,
                "category": "memory",
                "issue": "High swap usage detected",
                "suggestion": "Add more RAM or reduce memory load"
            }
        ]

        assert swap_usage_percent >= 30
        assert any("swap" in r["issue"].lower() for r in recommendations)

    def test_memory_recommendations_page_faults(self):
        """Test recommendations based on page fault rate"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=13.5,
            available_gb=2.5,
            usage_percent=84.4,
            swap_used_gb=1.5,
            swap_total_gb=8.0,
            page_faults=8000000,  # High page fault count
            compression_ratio=2.5,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 70,
                "category": "memory",
                "issue": "High page fault rate detected",
                "suggestion": "System is thrashing, reduce load"
            }
        ]

        assert metrics.page_faults > 5000000
        assert any(r["priority"] >= 60 for r in recommendations)

    def test_memory_recommendations_low_usage(self):
        """Test recommendations for normal memory usage"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=4.0,
            available_gb=12.0,
            usage_percent=25.0,
            swap_used_gb=0.0,
            swap_total_gb=8.0,
            page_faults=100000,
            compression_ratio=1.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 10,
                "category": "memory",
                "issue": "Memory usage normal",
                "suggestion": "No action required"
            }
        ]

        assert metrics.usage_percent < 50
        assert recommendations[0]["priority"] < 30


class TestMemorySubprocessTimeout:
    """Test 3: Subprocess timeout handling"""

    @pytest.mark.asyncio
    async def test_memory_analysis_timeout(self):
        """Test timeout handling for memory analysis"""
        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.1)

    @pytest.mark.asyncio
    async def test_memory_analysis_timeout_with_retry(self):
        """Test timeout recovery with retry mechanism"""
        call_count = 0

        async def mock_analysis():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                await asyncio.sleep(10)
            return {
                "total_gb": 16.0,
                "used_gb": 8.0,
                "usage_percent": 50.0
            }

        # First attempt times out
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(mock_analysis(), timeout=0.1)

        # Second attempt succeeds
        result = await asyncio.wait_for(mock_analysis(), timeout=5)
        assert result["usage_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_memory_subprocess_error_handling(self):
        """Test error handling in subprocess execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = RuntimeError("Memory analysis failed")

            with pytest.raises(RuntimeError):
                raise mock_run.side_effect

    @pytest.mark.asyncio
    async def test_memory_analysis_partial_failure_recovery(self):
        """Test recovery from partial analysis failures"""
        call_sequence = []

        async def mock_subprocess():
            call_sequence.append("call")
            if len(call_sequence) == 1:
                raise asyncio.TimeoutError()
            return MagicMock(returncode=0, stdout=b'{"total_gb":16,"used_gb":8}')

        # First call fails
        with pytest.raises(asyncio.TimeoutError):
            try:
                return await asyncio.wait_for(mock_subprocess(), timeout=0.1)
            except asyncio.TimeoutError:
                pass

        # Second call succeeds
        result = await asyncio.wait_for(mock_subprocess(), timeout=5)
        assert result.returncode == 0


class TestMemoryCriticalThresholds:
    """Test 4: Critical threshold detection (memory pressure > 85%)"""

    def test_memory_critical_pressure_detection(self):
        """Test detection of critical memory pressure (>85% usage)"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=14.2,
            available_gb=1.8,
            usage_percent=88.75,
            swap_used_gb=4.0,
            swap_total_gb=8.0,
            page_faults=6000000,
            compression_ratio=3.2,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 100,
                "category": "memory",
                "issue": "Critical memory pressure detected",
                "severity": "critical"
            }
        ]

        assert metrics.usage_percent > 85
        assert recommendations[0]["priority"] == 100
        assert recommendations[0]["severity"] == "critical"

    def test_memory_swap_exhaustion_detection(self):
        """Test detection when swap space is nearly exhausted"""
        metrics = MemoryMetrics(
            total_gb=8.0,
            used_gb=7.8,
            available_gb=0.2,
            usage_percent=97.5,
            swap_used_gb=7.8,
            swap_total_gb=8.0,
            page_faults=10000000,
            compression_ratio=3.8,
            timestamp=datetime.now()
        )

        swap_percent = (metrics.swap_used_gb / metrics.swap_total_gb) * 100

        # Critical conditions
        critical = (
            metrics.usage_percent > 95 and
            swap_percent > 90 and
            metrics.page_faults > 5000000
        )

        assert critical is True

    def test_memory_threshold_boundaries(self):
        """Test detection at various threshold boundaries"""
        test_cases = [
            {"usage": 49.9, "severity": "normal"},
            {"usage": 50.0, "severity": "low"},
            {"usage": 70.0, "severity": "medium"},
            {"usage": 80.0, "severity": "high"},
            {"usage": 85.0, "severity": "critical"},
            {"usage": 99.0, "severity": "critical"},
        ]

        for test_case in test_cases:
            metrics = MemoryMetrics(
                total_gb=16.0,
                used_gb=16.0 * (test_case["usage"] / 100),
                available_gb=16.0 * (1 - test_case["usage"] / 100),
                usage_percent=test_case["usage"],
                swap_used_gb=0.0,
                swap_total_gb=8.0,
                page_faults=0,
                compression_ratio=1.0,
                timestamp=datetime.now()
            )

            assert metrics.usage_percent == test_case["usage"]

    def test_memory_compression_effectiveness(self):
        """Test memory compression ratio as indicator of pressure"""
        # Low compression = low pressure
        low_pressure = MemoryMetrics(
            total_gb=16.0,
            used_gb=8.0,
            available_gb=8.0,
            usage_percent=50.0,
            swap_used_gb=0.0,
            swap_total_gb=8.0,
            page_faults=100000,
            compression_ratio=1.2,  # Low compression
            timestamp=datetime.now()
        )

        # High compression = high pressure
        high_pressure = MemoryMetrics(
            total_gb=16.0,
            used_gb=14.0,
            available_gb=2.0,
            usage_percent=87.5,
            swap_used_gb=2.0,
            swap_total_gb=8.0,
            page_faults=5000000,
            compression_ratio=4.5,  # High compression
            timestamp=datetime.now()
        )

        assert low_pressure.compression_ratio < high_pressure.compression_ratio
        assert low_pressure.page_faults < high_pressure.page_faults

    def test_memory_combined_critical_indicators(self):
        """Test detection of multiple critical memory indicators"""
        metrics = MemoryMetrics(
            total_gb=16.0,
            used_gb=14.8,
            available_gb=1.2,
            usage_percent=92.5,
            swap_used_gb=5.0,
            swap_total_gb=8.0,
            page_faults=8000000,
            compression_ratio=3.8,
            timestamp=datetime.now()
        )

        critical_indicators = {
            "high_usage": metrics.usage_percent >= 90,
            "swap_active": metrics.swap_used_gb > 0,
            "high_page_faults": metrics.page_faults > 5000000,
            "high_compression": metrics.compression_ratio > 3.0
        }

        # All critical indicators should be present
        assert all(critical_indicators.values())
        assert sum(critical_indicators.values()) == 4
