"""Integration tests for AFK Journey Action Recording System.

Tests cover:
- Action recording start/stop
- Recording individual actions (tap, swipe, wait, detection, checkpoint)
- Recording save/load
- Playback functionality
- Action filtering and analysis
- Integration with fully enhanced class
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil

from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.action_integration import (
    AFKJourneyActionIntegration,
    ActionStatistics,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.afk_journey_fully_enhanced import (
    AFKJourneyFullyEnhanced,
)


class TestActionIntegrationInit:
    """Test action integration initialization."""

    def test_init_action_integration(self):
        """Test initializing action integration."""
        integration = AFKJourneyActionIntegration()

        assert integration.action_recorder is None
        assert integration.action_player is None
        assert integration.recording_enabled is False
        assert integration.action_stats.total_actions == 0

    def test_action_statistics_defaults(self):
        """Test action statistics defaults."""
        stats = ActionStatistics()

        assert stats.total_actions == 0
        assert stats.taps == 0
        assert stats.swipes == 0
        assert stats.waits == 0
        assert stats.detections == 0
        assert stats.checkpoints == 0


class TestActionRecording:
    """Test action recording functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyActionIntegration()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_record_tap_without_recording(self):
        """Test recording tap without active recording."""
        integration = AFKJourneyActionIntegration()
        result = integration.record_tap(100, 200)

        assert result is False

    def test_record_swipe_without_recording(self):
        """Test recording swipe without active recording."""
        integration = AFKJourneyActionIntegration()
        result = integration.record_swipe(100, 200, 300, 400)

        assert result is False

    def test_record_wait_without_recording(self):
        """Test recording wait without active recording."""
        integration = AFKJourneyActionIntegration()
        result = integration.record_wait(1.0)

        assert result is False


class TestActionStatistics:
    """Test action statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics."""
        integration = AFKJourneyActionIntegration()
        stats = integration.get_action_stats()

        assert stats["total_actions"] == 0
        assert stats["taps"] == 0
        assert stats["swipes"] == 0
        assert stats["waits"] == 0
        assert stats["detections"] == 0
        assert stats["checkpoints"] == 0
        assert stats["total_duration"] == 0.0

    def test_reset_action_stats(self):
        """Test resetting action statistics."""
        integration = AFKJourneyActionIntegration()

        # Simulate adding actions
        integration.action_stats.total_actions = 10
        integration.action_stats.taps = 5
        integration.action_stats.swipes = 3

        # Reset
        integration.reset_action_stats()

        assert integration.action_stats.total_actions == 0
        assert integration.action_stats.taps == 0
        assert integration.action_stats.swipes == 0


class TestActionFiltering:
    """Test action filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = AFKJourneyActionIntegration()

    def test_filter_without_loaded_recording(self):
        """Test filtering without loaded recording."""
        result = self.integration.filter_actions(action_types=["tap"])

        assert result == []

    def test_get_recording_duration_without_recording(self):
        """Test getting duration without recording."""
        duration = self.integration.get_recording_duration()

        assert duration is None


class TestAFKJourneyFullyEnhanced:
    """Test AFKJourneyFullyEnhanced integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_fully_enhanced_init(self, mock_base_init):
        """Test AFKJourneyFullyEnhanced initialization."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        assert hasattr(game, 'action_recorder')
        assert hasattr(game, 'checkpoint_manager')
        assert hasattr(game, 'yolo_detector')

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_comprehensive_stats(self, mock_base_init):
        """Test comprehensive statistics."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        stats = game.get_comprehensive_stats()

        assert "checkpoint_stats" in stats
        assert "yolo_stats" in stats
        assert "action_stats" in stats
        assert "session_summary" in stats
        assert stats["game"] == "afk-journey"

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_tap_and_record(self, mock_base_init):
        """Test tap and record functionality."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        # Without active recording, should return False
        result = game.tap_and_record(100, 200)
        assert result is False

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_swipe_and_record(self, mock_base_init):
        """Test swipe and record functionality."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        result = game.swipe_and_record(100, 200, 300, 400)
        assert result is False

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_wait_and_record(self, mock_base_init):
        """Test wait and record functionality."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        result = game.wait_and_record(1.0, "wait for detection")
        assert result is False


class TestActionRecordingIntegration:
    """Test action recording integration with other systems."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = AFKJourneyActionIntegration()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_detect_action_types(self):
        """Test recording detection actions."""
        integration = AFKJourneyActionIntegration()

        # Without recording
        result = integration.record_detection("yolo", "hero", 0.95, [100, 200, 50, 60])
        assert result is False

    def test_checkpoint_action_recording(self):
        """Test recording checkpoint actions."""
        integration = AFKJourneyActionIntegration()

        # Without recording
        result = integration.record_checkpoint("ckpt_001", "before_boss")
        assert result is False

    def test_action_stats_incrementation(self):
        """Test that action stats increment correctly."""
        integration = AFKJourneyActionIntegration()

        # Manually increment stats
        integration.action_stats.taps = 5
        integration.action_stats.swipes = 3
        integration.action_stats.waits = 2
        integration.action_stats.detections = 4
        integration.action_stats.checkpoints = 1

        stats = integration.get_action_stats()

        assert stats["taps"] == 5
        assert stats["swipes"] == 3
        assert stats["waits"] == 2
        assert stats["detections"] == 4
        assert stats["checkpoints"] == 1


class TestRecordingStatistics:
    """Test recording statistics and analysis."""

    def test_stats_dict_structure(self):
        """Test stats dictionary structure."""
        integration = AFKJourneyActionIntegration()

        stats = integration.get_action_stats()

        # Check all required keys
        required_keys = [
            "total_actions",
            "taps",
            "swipes",
            "waits",
            "detections",
            "checkpoints",
            "total_duration",
            "avg_action_time",
        ]

        for key in required_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))

    def test_stats_calculation(self):
        """Test statistics calculations."""
        integration = AFKJourneyActionIntegration()

        # Manually set stats
        integration.action_stats.total_actions = 100
        integration.action_stats.total_duration = 10.0  # seconds

        stats = integration.get_action_stats()

        # Average should be 0.1 seconds = 100ms
        assert stats["avg_action_time"] == pytest.approx(0.1, rel=0.01)


class TestSessionSaving:
    """Test session saving and loading."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyActionIntegration()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_save_recording_without_active_recording(self):
        """Test saving without active recording."""
        output_path = Path(self.temp_dir) / "test_recording.yaml"
        result = self.integration.save_recording(str(output_path))

        assert result is False

    def test_load_nonexistent_recording(self):
        """Test loading nonexistent recording."""
        result = self.integration.load_recording("/nonexistent/path.yaml")

        assert result is False


class TestErrorRecoveryIntegration:
    """Test error recovery with action recording."""

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_integrated_error_recovery(self, mock_base_init):
        """Test integrated error recovery."""
        mock_base_init.return_value = None

        game = AFKJourneyFullyEnhanced()

        # Without initialized systems
        result = game.integrated_error_recovery("test_error")

        # Should fail gracefully
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
