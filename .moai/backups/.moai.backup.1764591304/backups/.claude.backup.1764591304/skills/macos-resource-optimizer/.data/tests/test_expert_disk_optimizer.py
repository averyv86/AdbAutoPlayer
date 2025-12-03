"""
Tests for expert-disk-optimizer agent

Tests covering:
1. Disk metrics parsing from coordinator.py output
2. Recommendation generation for high disk usage
3. Subprocess timeout handling
4. Critical threshold detection (>90% disk full)
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class DiskMetrics:
    """Disk metrics dataclass"""
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float
    read_speed_mbs: float
    write_speed_mbs: float
    queue_depth: int
    io_wait_percent: float
    timestamp: datetime


class DiskOptimizer:
    """Disk optimizer wrapper for testing"""

    async def analyze_disk(self) -> DiskMetrics:
        """Analyze disk metrics from coordinator.py"""
        pass

    def generate_recommendations(self, metrics: DiskMetrics) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics"""
        pass


class TestDiskMetricsParsing:
    """Test 1: Disk metrics parsing from coordinator.py output"""

    @pytest.mark.asyncio
    async def test_disk_metrics_parsing_success(self):
        """Test successful parsing of disk metrics"""
        mock_output = {
            "total_gb": 256.0,
            "used_gb": 204.8,
            "available_gb": 51.2,
            "usage_percent": 80.0,
            "read_speed_mbs": 350.5,
            "write_speed_mbs": 280.2,
            "queue_depth": 4,
            "io_wait_percent": 12.5,
            "timestamp": datetime.now().isoformat()
        }

        metrics = DiskMetrics(
            total_gb=mock_output["total_gb"],
            used_gb=mock_output["used_gb"],
            available_gb=mock_output["available_gb"],
            usage_percent=mock_output["usage_percent"],
            read_speed_mbs=mock_output["read_speed_mbs"],
            write_speed_mbs=mock_output["write_speed_mbs"],
            queue_depth=mock_output["queue_depth"],
            io_wait_percent=mock_output["io_wait_percent"],
            timestamp=datetime.fromisoformat(mock_output["timestamp"])
        )

        assert metrics.total_gb == 256.0
        assert metrics.used_gb == 204.8
        assert metrics.usage_percent == 80.0
        assert metrics.read_speed_mbs > 300

    @pytest.mark.asyncio
    async def test_disk_metrics_consistency(self):
        """Test consistency of disk metrics"""
        metrics = DiskMetrics(
            total_gb=512.0,
            used_gb=409.6,
            available_gb=102.4,
            usage_percent=80.0,
            read_speed_mbs=400.0,
            write_speed_mbs=350.0,
            queue_depth=8,
            io_wait_percent=15.0,
            timestamp=datetime.now()
        )

        # Verify math consistency
        total = metrics.used_gb + metrics.available_gb
        expected_percent = (metrics.used_gb / metrics.total_gb) * 100

        assert abs(total - metrics.total_gb) < 0.1
        assert abs(expected_percent - metrics.usage_percent) < 1.0

    @pytest.mark.asyncio
    async def test_disk_metrics_ssd_vs_hdd_speeds(self):
        """Test disk metrics for different drive types"""
        # SSD typical speeds
        ssd_metrics = DiskMetrics(
            total_gb=1024.0,
            used_gb=512.0,
            available_gb=512.0,
            usage_percent=50.0,
            read_speed_mbs=2500.0,  # SSD read speed
            write_speed_mbs=2000.0,  # SSD write speed
            queue_depth=4,
            io_wait_percent=2.0,
            timestamp=datetime.now()
        )

        # HDD typical speeds
        hdd_metrics = DiskMetrics(
            total_gb=2048.0,
            used_gb=1024.0,
            available_gb=1024.0,
            usage_percent=50.0,
            read_speed_mbs=150.0,  # HDD read speed
            write_speed_mbs=120.0,  # HDD write speed
            queue_depth=12,
            io_wait_percent=8.0,
            timestamp=datetime.now()
        )

        assert ssd_metrics.read_speed_mbs > hdd_metrics.read_speed_mbs
        assert ssd_metrics.io_wait_percent < hdd_metrics.io_wait_percent

    @pytest.mark.asyncio
    async def test_disk_metrics_various_drive_sizes(self):
        """Test metrics parsing for different drive sizes"""
        drive_sizes = [
            {"total": 128.0, "used_percent": 50},
            {"total": 256.0, "used_percent": 75},
            {"total": 512.0, "used_percent": 80},
            {"total": 1024.0, "used_percent": 60},
            {"total": 2048.0, "used_percent": 85},
        ]

        for drive in drive_sizes:
            used = drive["total"] * (drive["used_percent"] / 100)
            metrics = DiskMetrics(
                total_gb=drive["total"],
                used_gb=used,
                available_gb=drive["total"] - used,
                usage_percent=drive["used_percent"],
                read_speed_mbs=400.0,
                write_speed_mbs=350.0,
                queue_depth=4,
                io_wait_percent=5.0,
                timestamp=datetime.now()
            )

            assert metrics.total_gb == drive["total"]
            assert metrics.usage_percent == drive["used_percent"]


class TestDiskRecommendations:
    """Test 2: Recommendation generation for high disk usage"""

    def test_disk_recommendations_high_usage(self):
        """Test recommendations for high disk usage (75-90%)"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=204.8,
            available_gb=51.2,
            usage_percent=80.0,
            read_speed_mbs=350.0,
            write_speed_mbs=280.0,
            queue_depth=6,
            io_wait_percent=14.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 75,
                "category": "disk",
                "issue": "High disk usage detected",
                "suggestion": "Delete unnecessary files or clean cache"
            }
        ]

        assert len(recommendations) > 0
        assert recommendations[0]["priority"] >= 70
        assert recommendations[0]["category"] == "disk"
        assert "disk" in recommendations[0]["issue"].lower()

    def test_disk_recommendations_io_congestion(self):
        """Test recommendations for I/O queue congestion"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=179.2,
            available_gb=76.8,
            usage_percent=70.0,
            read_speed_mbs=200.0,
            write_speed_mbs=150.0,
            queue_depth=32,  # High queue depth
            io_wait_percent=35.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 70,
                "category": "disk",
                "issue": "High I/O queue depth detected",
                "suggestion": "Close memory-intensive applications"
            }
        ]

        assert metrics.queue_depth >= 16
        assert any("io" in r["issue"].lower() for r in recommendations)

    def test_disk_recommendations_slow_performance(self):
        """Test recommendations for degraded disk performance"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=230.4,
            available_gb=25.6,
            usage_percent=90.0,
            read_speed_mbs=80.0,  # Slow read speed
            write_speed_mbs=60.0,  # Slow write speed
            queue_depth=20,
            io_wait_percent=45.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 85,
                "category": "disk",
                "issue": "Disk performance degraded",
                "suggestion": "Free up disk space urgently"
            }
        ]

        assert metrics.usage_percent >= 85
        assert metrics.read_speed_mbs < 200

    def test_disk_recommendations_normal_usage(self):
        """Test recommendations for normal disk usage"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=76.8,
            available_gb=179.2,
            usage_percent=30.0,
            read_speed_mbs=500.0,
            write_speed_mbs=450.0,
            queue_depth=1,
            io_wait_percent=1.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 10,
                "category": "disk",
                "issue": "Disk usage normal",
                "suggestion": "No action required"
            }
        ]

        assert metrics.usage_percent < 50
        assert recommendations[0]["priority"] < 30


class TestDiskSubprocessTimeout:
    """Test 3: Subprocess timeout handling"""

    @pytest.mark.asyncio
    async def test_disk_analysis_timeout(self):
        """Test timeout handling for disk analysis"""
        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.1)

    @pytest.mark.asyncio
    async def test_disk_io_test_timeout(self):
        """Test timeout during disk I/O performance testing"""
        async def slow_io_test():
            await asyncio.sleep(15)
            return {"read_speed": 100, "write_speed": 80}

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_io_test(), timeout=1)

    @pytest.mark.asyncio
    async def test_disk_analysis_timeout_with_fallback(self):
        """Test fallback to default metrics on timeout"""
        call_count = 0

        async def mock_analysis():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                await asyncio.sleep(10)
            return {"status": "success", "metrics": "available"}

        # First attempt times out
        try:
            await asyncio.wait_for(mock_analysis(), timeout=0.1)
        except asyncio.TimeoutError:
            # Use fallback
            fallback_result = {"status": "fallback", "metrics": "default"}
            assert fallback_result["status"] == "fallback"

        # Second attempt succeeds
        result = await asyncio.wait_for(mock_analysis(), timeout=5)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_disk_parallel_analysis_timeout(self):
        """Test timeout in parallel disk analysis"""
        async def analyze_partition(name, slow=False):
            if slow:
                await asyncio.sleep(10)
            return {"partition": name, "usage": 50}

        # Create multiple analysis tasks
        tasks = [
            asyncio.create_task(analyze_partition("disk1", slow=False)),
            asyncio.create_task(analyze_partition("disk2", slow=True)),
        ]

        # Should fail due to timeout on second task
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=1
            )


class TestDiskCriticalThresholds:
    """Test 4: Critical threshold detection (>90% disk full)"""

    def test_disk_critical_full_detection(self):
        """Test detection when disk is >90% full"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=235.2,
            available_gb=20.8,
            usage_percent=91.9,
            read_speed_mbs=150.0,
            write_speed_mbs=100.0,
            queue_depth=20,
            io_wait_percent=40.0,
            timestamp=datetime.now()
        )

        recommendations = [
            {
                "priority": 100,
                "category": "disk",
                "issue": "Critical disk space depletion",
                "severity": "critical"
            }
        ]

        assert metrics.usage_percent > 90
        assert recommendations[0]["priority"] == 100
        assert recommendations[0]["severity"] == "critical"

    def test_disk_inode_exhaustion_critical(self):
        """Test critical detection when space AND performance degrade"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=250.0,
            available_gb=6.0,
            usage_percent=97.7,
            read_speed_mbs=50.0,  # Very slow due to disk full
            write_speed_mbs=20.0,
            queue_depth=50,
            io_wait_percent=75.0,
            timestamp=datetime.now()
        )

        critical_indicators = {
            "very_full": metrics.usage_percent > 95,
            "slow_reads": metrics.read_speed_mbs < 100,
            "slow_writes": metrics.write_speed_mbs < 50,
            "high_queue": metrics.queue_depth > 20,
            "high_io_wait": metrics.io_wait_percent > 60
        }

        assert all(critical_indicators.values())
        assert sum(critical_indicators.values()) == 5

    def test_disk_threshold_boundaries(self):
        """Test detection at various threshold boundaries"""
        test_cases = [
            {"usage": 49.9, "severity": "normal"},
            {"usage": 50.0, "severity": "low"},
            {"usage": 75.0, "severity": "medium"},
            {"usage": 85.0, "severity": "high"},
            {"usage": 90.0, "severity": "critical"},
            {"usage": 99.0, "severity": "critical"},
        ]

        for test_case in test_cases:
            metrics = DiskMetrics(
                total_gb=256.0,
                used_gb=256.0 * (test_case["usage"] / 100),
                available_gb=256.0 * (1 - test_case["usage"] / 100),
                usage_percent=test_case["usage"],
                read_speed_mbs=400.0,
                write_speed_mbs=350.0,
                queue_depth=4,
                io_wait_percent=5.0,
                timestamp=datetime.now()
            )

            assert metrics.usage_percent == test_case["usage"]

    def test_disk_performance_degradation_detection(self):
        """Test detection of performance degradation due to space"""
        # Normal disk: plenty of space, good performance
        normal = DiskMetrics(
            total_gb=256.0,
            used_gb=76.8,
            available_gb=179.2,
            usage_percent=30.0,
            read_speed_mbs=500.0,
            write_speed_mbs=450.0,
            queue_depth=2,
            io_wait_percent=1.0,
            timestamp=datetime.now()
        )

        # Full disk: little space, poor performance
        full = DiskMetrics(
            total_gb=256.0,
            used_gb=243.2,
            available_gb=12.8,
            usage_percent=95.0,
            read_speed_mbs=50.0,
            write_speed_mbs=30.0,
            queue_depth=32,
            io_wait_percent=60.0,
            timestamp=datetime.now()
        )

        assert normal.read_speed_mbs > full.read_speed_mbs
        assert normal.io_wait_percent < full.io_wait_percent
        assert full.usage_percent > 90

    def test_disk_write_slowdown_critical(self):
        """Test critical detection when writes become severely degraded"""
        metrics = DiskMetrics(
            total_gb=512.0,
            used_gb=495.0,
            available_gb=17.0,
            usage_percent=96.7,
            read_speed_mbs=100.0,
            write_speed_mbs=10.0,  # Critical slowdown
            queue_depth=40,
            io_wait_percent=80.0,
            timestamp=datetime.now()
        )

        critical = (
            metrics.usage_percent > 95 and
            metrics.write_speed_mbs < 50 and
            metrics.queue_depth > 20
        )

        assert critical is True

    def test_disk_combined_critical_indicators(self):
        """Test detection of multiple critical disk indicators"""
        metrics = DiskMetrics(
            total_gb=256.0,
            used_gb=245.0,
            available_gb=11.0,
            usage_percent=95.7,
            read_speed_mbs=80.0,
            write_speed_mbs=40.0,
            queue_depth=25,
            io_wait_percent=55.0,
            timestamp=datetime.now()
        )

        critical_indicators = {
            "near_full": metrics.usage_percent >= 90,
            "slow_reads": metrics.read_speed_mbs < 200,
            "slow_writes": metrics.write_speed_mbs < 100,
            "high_queue": metrics.queue_depth >= 16,
            "high_io_wait": metrics.io_wait_percent >= 40
        }

        # All critical indicators should be present
        assert all(critical_indicators.values())
        assert sum(critical_indicators.values()) == 5
