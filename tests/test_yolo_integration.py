"""Integration tests for AFK Journey YOLO Detection System.

Tests cover:
- YOLO system initialization
- Confidence threshold management
- Object detection (YOLO + template fallback)
- Multiple object detection
- Detection performance tracking
- Detection history and analysis
- Integration with AFKJourneyYOLOEnhanced
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil

from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.yolo_integration import (
    AFKJourneyYOLOIntegration,
    DetectionResult,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.afk_journey_yolo_enhanced import (
    AFKJourneyYOLOEnhanced,
)


class TestYOLOIntegrationInit:
    """Test YOLO integration initialization."""

    def test_init_yolo_integration(self):
        """Test initializing YOLO integration."""
        integration = AFKJourneyYOLOIntegration()

        assert integration.yolo_detector is None
        assert integration.yolo_enabled is False
        assert integration.detection_stats["total_detections"] == 0
        assert integration.detection_stats["yolo_success"] == 0
        assert integration.detection_stats["template_fallback"] == 0

    def test_yolo_classes_defined(self):
        """Test that YOLO classes are properly defined."""
        integration = AFKJourneyYOLOIntegration()

        assert "hero" in integration.YOLO_CLASSES
        assert "enemy" in integration.YOLO_CLASSES
        assert "battle_button" in integration.YOLO_CLASSES
        assert "item" in integration.YOLO_CLASSES
        assert "altar" in integration.YOLO_CLASSES
        assert "text" in integration.YOLO_CLASSES

        # Check structure
        for class_name, class_info in integration.YOLO_CLASSES.items():
            assert "confidence" in class_info
            assert "template_fallback" in class_info
            assert 0.0 <= class_info["confidence"] <= 1.0


class TestConfidenceThreshold:
    """Test confidence threshold management."""

    def test_set_confidence_threshold(self):
        """Test setting confidence threshold for specific class."""
        integration = AFKJourneyYOLOIntegration()
        integration.set_confidence_threshold("hero", 0.75)

        assert integration.detection_stats["confidence_thresholds"]["hero"]["confidence"] == 0.75

    def test_set_all_confidence_thresholds(self):
        """Test setting all confidence thresholds."""
        integration = AFKJourneyYOLOIntegration()
        thresholds = {
            "hero": 0.80,
            "enemy": 0.75,
            "battle_button": 0.85,
        }

        integration.set_all_confidence_thresholds(thresholds)

        for class_name, threshold in thresholds.items():
            assert integration.detection_stats["confidence_thresholds"][class_name]["confidence"] == threshold

    def test_set_invalid_class_threshold(self):
        """Test setting threshold for invalid class."""
        integration = AFKJourneyYOLOIntegration()
        # Should not raise, just log warning
        integration.set_confidence_threshold("invalid_class", 0.50)

        # Original thresholds should be unchanged
        assert integration.detection_stats["confidence_thresholds"]["hero"]["confidence"] == 0.65


class TestDetectionResult:
    """Test DetectionResult data class."""

    def test_detection_result_creation(self):
        """Test creating a DetectionResult."""
        result = DetectionResult(
            detected=True,
            method="yolo",
            class_name="hero",
            confidence=0.92,
            x=100,
            y=200,
            width=50,
            height=60,
            timestamp=1234567890.123
        )

        assert result.detected is True
        assert result.method == "yolo"
        assert result.class_name == "hero"
        assert result.confidence == 0.92
        assert result.x == 100
        assert result.y == 200

    def test_template_detection_result(self):
        """Test creating a template detection result."""
        result = DetectionResult(
            detected=True,
            method="template",
            class_name="battle_button",
            confidence=0.70,
            x=150,
            y=250,
            width=80,
            height=40,
            timestamp=1234567890.456
        )

        assert result.method == "template"
        assert result.class_name == "battle_button"


class TestDetectionStats:
    """Test detection statistics tracking."""

    def test_initial_stats(self):
        """Test initial detection statistics."""
        integration = AFKJourneyYOLOIntegration()
        stats = integration.get_detection_stats()

        assert stats["total_detections"] == 0
        assert stats["yolo_success"] == 0
        assert stats["yolo_failed_fallback"] == 0
        assert stats["template_fallback"] == 0
        assert stats["total_failed"] == 0
        assert stats["yolo_enabled"] is False
        assert stats["success_rate"] == 0.0

    def test_stats_with_detections(self):
        """Test statistics after simulated detections."""
        integration = AFKJourneyYOLOIntegration()

        # Simulate detections
        integration.detection_stats["total_detections"] = 10
        integration.detection_stats["yolo_success"] = 6
        integration.detection_stats["template_fallback"] = 3
        integration.detection_stats["total_failed"] = 1

        stats = integration.get_detection_stats()

        assert stats["total_detections"] == 10
        assert stats["yolo_success"] == 6
        assert stats["template_fallback"] == 3
        assert stats["total_failed"] == 1
        # Success rate: (6 + 3) / 10 = 0.9
        assert stats["success_rate"] == 0.9

    def test_reset_detection_stats(self):
        """Test resetting detection statistics."""
        integration = AFKJourneyYOLOIntegration()

        # Add some stats
        integration.detection_stats["total_detections"] = 10
        integration.detection_stats["yolo_success"] = 5
        integration._detection_times.extend([10.0, 20.0, 30.0])

        # Reset
        integration.reset_detection_stats()

        assert integration.detection_stats["total_detections"] == 0
        assert integration.detection_stats["yolo_success"] == 0
        assert len(integration._detection_times) == 0
        assert len(integration._yolo_detection_times) == 0


class TestDetectionMocking:
    """Test detection with mocked YOLO detector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = AFKJourneyYOLOIntegration()
        # Mock the YOLO detector
        self.mock_detector = Mock()
        self.integration.yolo_detector = self.mock_detector
        self.integration.yolo_enabled = True

    def test_detect_object_success(self):
        """Test successful object detection."""
        # Mock detection result
        mock_detection = Mock()
        mock_detection.confidence = 0.92
        mock_detection.bounding_box = Mock()
        mock_detection.bounding_box.x1 = 100
        mock_detection.bounding_box.y1 = 200
        mock_detection.bounding_box.x2 = 150
        mock_detection.bounding_box.y2 = 260

        mock_frame = Mock()
        mock_frame.detections = [mock_detection]

        self.mock_detector.detect_classes.return_value = mock_frame
        self.mock_detector.get_largest_detection.return_value = mock_detection

        result = self.integration.detect_object(
            "/tmp/test.jpg",
            "hero",
            use_yolo=True,
            use_template_fallback=False
        )

        assert result is not None
        assert result.detected is True
        assert result.method == "yolo"
        assert result.class_name == "hero"
        assert result.confidence == 0.92

    def test_detect_multiple_objects(self):
        """Test detecting multiple object types."""
        # Mock detections for multiple classes
        mock_detections = []
        for class_name in ["hero", "enemy", "battle_button"]:
            mock_det = Mock()
            mock_det.confidence = 0.85
            mock_det.bounding_box = Mock()
            mock_det.bounding_box.x1, mock_det.bounding_box.y1 = 100, 200
            mock_det.bounding_box.x2, mock_det.bounding_box.y2 = 150, 260
            mock_detections.append((class_name, mock_det))

        def side_effect(*args, **kwargs):
            frame = Mock()
            frame.detections = [d for c, d in mock_detections if c in kwargs.get("classes", [])]
            return frame

        self.mock_detector.detect_classes.side_effect = side_effect
        self.mock_detector.get_largest_detection.side_effect = lambda dets, **kwargs: dets[0] if dets else None

        results = self.integration.detect_multiple_objects(
            "/tmp/test.jpg",
            ["hero", "enemy", "battle_button"],
            use_yolo=True
        )

        # Should have attempted detection for each class
        assert self.integration.detection_stats["total_detections"] == 3

    def test_detection_failure_increments_counter(self):
        """Test that failed detections increment counter."""
        mock_frame = Mock()
        mock_frame.detections = []
        self.mock_detector.detect_classes.return_value = mock_frame
        self.mock_detector.get_largest_detection.return_value = None

        result = self.integration.detect_object(
            "/tmp/test.jpg",
            "hero",
            use_yolo=True,
            use_template_fallback=False
        )

        assert result is None
        assert self.integration.detection_stats["yolo_failed_fallback"] == 1
        assert self.integration.detection_stats["total_failed"] == 1


class TestAFKJourneyYOLOEnhanced:
    """Test AFKJourneyYOLOEnhanced integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_init(self, mock_base_init):
        """Test AFKJourneyYOLOEnhanced initialization."""
        mock_base_init.return_value = None

        game = AFKJourneyYOLOEnhanced()

        assert hasattr(game, 'yolo_detector')
        assert hasattr(game, 'checkpoint_manager')
        assert hasattr(game, '_last_detections')
        assert len(game._last_detections) == 0

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_detection_history(self, mock_base_init):
        """Test detection history tracking."""
        mock_base_init.return_value = None

        game = AFKJourneyYOLOEnhanced()

        # Add some detections
        for i in range(5):
            result = DetectionResult(
                detected=True,
                method="yolo",
                class_name="hero",
                confidence=0.90 + (i * 0.01),
                x=100 + i,
                y=200,
                width=50,
                height=60,
                timestamp=1234567890.0 + i
            )
            game._add_to_detection_history(result)

        history = game.get_detection_history()
        assert len(history) == 5
        assert history[0].class_name == "hero"

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_detection_history_limit(self, mock_base_init):
        """Test detection history respects max limit."""
        mock_base_init.return_value = None

        game = AFKJourneyYOLOEnhanced()
        game._max_detection_history = 5

        # Add more than max
        for i in range(10):
            result = DetectionResult(
                detected=True,
                method="yolo",
                class_name="hero",
                confidence=0.90,
                x=100,
                y=200,
                width=50,
                height=60,
                timestamp=1234567890.0 + i
            )
            game._add_to_detection_history(result)

        assert len(game._last_detections) == 5

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_detection_success_rate(self, mock_base_init):
        """Test detection success rate calculation."""
        mock_base_init.return_value = None

        game = AFKJourneyYOLOEnhanced()

        # Add detections
        detections = [
            (True, "hero"),
            (True, "hero"),
            (False, "hero"),
            (True, "enemy"),
            (False, "enemy"),
        ]

        for detected, class_name in detections:
            result = DetectionResult(
                detected=detected,
                method="yolo" if detected else "template",
                class_name=class_name,
                confidence=0.90 if detected else 0.70,
                x=100,
                y=200,
                width=50,
                height=60,
                timestamp=1234567890.0
            )
            game._add_to_detection_history(result)

        # Overall success rate: 3/5 = 0.6
        assert game.get_detection_success_rate() == 0.6

        # Hero success rate: 2/3 ≈ 0.667
        hero_rate = game.get_detection_success_rate("hero")
        assert abs(hero_rate - 0.667) < 0.01

        # Enemy success rate: 1/2 = 0.5
        enemy_rate = game.get_detection_success_rate("enemy")
        assert enemy_rate == 0.5

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_optimize_confidence_thresholds(self, mock_base_init):
        """Test confidence threshold optimization."""
        mock_base_init.return_value = None

        game = AFKJourneyYOLOEnhanced()

        # Add detections with various confidences
        confidences = [0.65, 0.72, 0.85, 0.90, 0.95]
        for conf in confidences:
            result = DetectionResult(
                detected=True,
                method="yolo",
                class_name="hero",
                confidence=conf,
                x=100,
                y=200,
                width=50,
                height=60,
                timestamp=1234567890.0
            )
            game._add_to_detection_history(result)

        optimized = game.optimize_confidence_thresholds()

        assert "hero" in optimized
        # Should suggest threshold around lower end of successful detections
        assert optimized["hero"] > 0.65


class TestDetectionPerformance:
    """Test detection performance tracking."""

    def test_speed_tracking(self):
        """Test that detection speed is tracked."""
        integration = AFKJourneyYOLOIntegration()

        # Simulate detection times
        integration._detection_times.extend([10.5, 12.3, 11.8, 10.9])
        integration._yolo_detection_times.extend([5.2, 5.8])
        integration._template_detection_times.extend([45.0, 48.5])

        stats = integration.get_detection_stats()

        assert stats["avg_yolo_speed_ms"] == pytest.approx(5.5, rel=0.1)
        assert stats["avg_template_speed_ms"] == pytest.approx(46.75, rel=0.1)
        assert stats["avg_total_speed_ms"] == pytest.approx(11.375, rel=0.1)

    def test_speed_improvement_calculation(self):
        """Test speed improvement calculation."""
        integration = AFKJourneyYOLOIntegration()

        # Template: 100ms, YOLO: 30ms
        integration._yolo_detection_times.extend([30.0, 30.0])
        integration._template_detection_times.extend([100.0, 100.0])

        stats = integration.get_detection_stats()

        # Improvement: (100 - 30) / 100 = 0.7 = 70%
        assert stats["speed_improvement"] == pytest.approx(0.7, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
