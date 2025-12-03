"""Integration tests for Guitar Girl Enhanced Systems.

Tests cover:
- Checkpoint save/load/recovery
- YOLO-based note detection
- Action recording and playback
- Fully enhanced class integration
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil

from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.checkpoint_integration import (
    GuitarGirlCheckpointIntegration,
    GameState,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.yolo_integration import (
    GuitarGirlYOLOIntegration,
    DetectionResult,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.action_integration import (
    GuitarGirlActionIntegration,
    ActionStatistics,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl_fully_enhanced import (
    GuitarGirlFullyEnhanced,
)


class TestCheckpointIntegrationInit:
    """Test checkpoint integration initialization."""

    def test_init_checkpoint_integration(self):
        """Test initializing checkpoint integration."""
        integration = GuitarGirlCheckpointIntegration()

        assert integration.checkpoint_enabled is False
        assert integration.checkpoint_dir is not None
        assert len(integration._state_history) == 0

    def test_checkpoint_stats_defaults(self):
        """Test checkpoint stats defaults."""
        integration = GuitarGirlCheckpointIntegration()

        stats = integration.get_checkpoint_stats()
        assert stats["saved_checkpoints"] == 0
        assert stats["loaded_checkpoints"] == 0
        assert stats["recovery_attempts"] == 0
        assert stats["successful_recoveries"] == 0


class TestYOLOIntegrationInit:
    """Test YOLO integration initialization."""

    def test_init_yolo_integration(self):
        """Test initializing YOLO integration."""
        integration = GuitarGirlYOLOIntegration()

        assert integration.yolo_enabled is False
        assert integration.yolo_detector is None
        assert integration.yolo_stats["yolo_detections"] == 0

    def test_yolo_classes_defined(self):
        """Test that YOLO classes are defined."""
        integration = GuitarGirlYOLOIntegration()

        assert "small_note" in integration.YOLO_CLASSES
        assert "big_note" in integration.YOLO_CLASSES
        assert "hold_note" in integration.YOLO_CLASSES
        assert "double_note" in integration.YOLO_CLASSES
        assert "special_note" in integration.YOLO_CLASSES


class TestActionIntegrationInit:
    """Test action integration initialization."""

    def test_init_action_integration(self):
        """Test initializing action integration."""
        integration = GuitarGirlActionIntegration()

        assert integration.action_recorder is None
        assert integration.action_player is None
        assert integration.recording_enabled is False
        assert integration.action_stats.total_actions == 0

    def test_action_statistics_defaults(self):
        """Test action statistics defaults."""
        stats = ActionStatistics()

        assert stats.total_actions == 0
        assert stats.taps == 0
        assert stats.detections == 0
        assert stats.level_ups == 0
        assert stats.skill_uses == 0
        assert stats.checkpoints == 0


class TestCheckpointSystem:
    """Test checkpoint save/load functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = GuitarGirlCheckpointIntegration()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_init_checkpoint_directory(self):
        """Test initializing checkpoint directory."""
        result = self.integration._init_checkpoint_system(self.temp_dir)

        assert result is True
        assert self.integration.checkpoint_enabled is True
        assert Path(self.temp_dir).exists()

    def test_save_checkpoint_without_init(self):
        """Test saving checkpoint without initialization."""
        result = self.integration.save_checkpoint("test_ckpt")

        assert result is False

    def test_list_checkpoints_empty(self):
        """Test listing checkpoints when none exist."""
        self.integration._init_checkpoint_system(self.temp_dir)
        checkpoints = self.integration.list_checkpoints()

        assert checkpoints == []

    def test_cleanup_old_checkpoints(self):
        """Test cleaning up old checkpoints."""
        self.integration._init_checkpoint_system(self.temp_dir)
        deleted = self.integration.cleanup_old_checkpoints(keep_count=5)

        assert deleted == 0  # No checkpoints to delete


class TestYOLOSystem:
    """Test YOLO detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = GuitarGirlYOLOIntegration()

    def test_set_confidence_threshold_valid(self):
        """Test setting valid confidence threshold."""
        result = self.integration.set_confidence_threshold("small_note", 0.75)

        assert result is True
        assert self.integration.YOLO_CLASSES["small_note"]["confidence"] == 0.75

    def test_set_confidence_threshold_invalid_class(self):
        """Test setting threshold for invalid class."""
        result = self.integration.set_confidence_threshold("invalid_note", 0.75)

        assert result is False

    def test_set_confidence_threshold_invalid_value(self):
        """Test setting invalid confidence value."""
        result = self.integration.set_confidence_threshold("small_note", 1.5)

        assert result is False

    def test_get_detection_stats(self):
        """Test getting detection statistics."""
        stats = self.integration.get_detection_stats()

        assert "yolo_enabled" in stats
        assert "yolo_detections" in stats
        assert "template_fallback_used" in stats
        assert "total_detections" in stats


class TestActionRecording:
    """Test action recording functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = GuitarGirlActionIntegration()

    def test_record_tap_without_recording(self):
        """Test recording tap without active recording."""
        result = self.integration.record_tap(100, 200)

        assert result is False

    def test_record_detection_without_recording(self):
        """Test recording detection without active recording."""
        result = self.integration.record_note_detection("small_note", 0.95, [100, 200, 50, 60])

        assert result is False

    def test_record_level_up_without_recording(self):
        """Test recording level up without active recording."""
        result = self.integration.record_level_up("guitar_girl", 5)

        assert result is False

    def test_record_skill_use_without_recording(self):
        """Test recording skill use without active recording."""
        result = self.integration.record_skill_use("power_chord", 1)

        assert result is False


class TestGuitarGirlFullyEnhanced:
    """Test fully enhanced Guitar Girl class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_fully_enhanced_init(self, mock_base_init):
        """Test fully enhanced initialization."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        assert hasattr(game, 'checkpoint_manager') or hasattr(game, 'checkpoint_dir')
        assert hasattr(game, 'yolo_detector') or hasattr(game, 'yolo_enabled')
        assert hasattr(game, 'action_recorder') or hasattr(game, 'recording_enabled')

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_comprehensive_stats(self, mock_base_init):
        """Test comprehensive statistics."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        stats = game.get_comprehensive_stats()

        assert "checkpoint_stats" in stats
        assert "yolo_stats" in stats
        assert "action_stats" in stats
        assert "session_summary" in stats
        assert stats["game"] == "guitar-girl"

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_tap_and_record(self, mock_base_init):
        """Test tap and record functionality."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        # Without active recording, should return False
        result = game.tap_and_record(100, 200)
        assert result is False

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_level_up_and_record(self, mock_base_init):
        """Test level up and record functionality."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        result = game.level_up_and_record("guitar_girl", 5)
        assert result is False

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_use_skill_and_record(self, mock_base_init):
        """Test skill use and record functionality."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        result = game.use_skill_and_record("power_chord", 1)
        assert result is False


class TestCheckpointStatistics:
    """Test checkpoint statistics tracking."""

    def test_initial_checkpoint_stats(self):
        """Test initial checkpoint statistics."""
        integration = GuitarGirlCheckpointIntegration()
        stats = integration.get_checkpoint_stats()

        assert stats["total_checkpoints"] == 0
        assert stats["saved_checkpoints"] == 0
        assert stats["loaded_checkpoints"] == 0
        assert stats["recovery_attempts"] == 0
        assert stats["successful_recoveries"] == 0


class TestYOLOStatistics:
    """Test YOLO detection statistics."""

    def test_initial_detection_stats(self):
        """Test initial detection statistics."""
        integration = GuitarGirlYOLOIntegration()
        stats = integration.get_detection_stats()

        assert stats["yolo_detections"] == 0
        assert stats["template_fallback_used"] == 0
        assert stats["failed_detections"] == 0
        assert stats["total_detections"] == 0


class TestActionStatistics:
    """Test action recording statistics."""

    def test_initial_action_stats(self):
        """Test initial action statistics."""
        integration = GuitarGirlActionIntegration()
        stats = integration.get_action_stats()

        assert stats["total_actions"] == 0
        assert stats["taps"] == 0
        assert stats["detections"] == 0
        assert stats["level_ups"] == 0
        assert stats["skill_uses"] == 0
        assert stats["checkpoints"] == 0

    def test_reset_action_stats(self):
        """Test resetting action statistics."""
        integration = GuitarGirlActionIntegration()

        # Simulate adding actions
        integration.action_stats.total_actions = 10
        integration.action_stats.taps = 5
        integration.action_stats.detections = 3

        # Reset
        integration.reset_action_stats()

        assert integration.action_stats.total_actions == 0
        assert integration.action_stats.taps == 0
        assert integration.action_stats.detections == 0


class TestGameStateDataclass:
    """Test GameState dataclass."""

    def test_game_state_creation(self):
        """Test creating GameState."""
        state = GameState(
            timestamp=1234567890.0,
            level=5,
            score=1000,
            big_notes=10,
            small_notes=50,
        )

        assert state.timestamp == 1234567890.0
        assert state.level == 5
        assert state.score == 1000
        assert state.big_notes == 10
        assert state.small_notes == 50

    def test_game_state_defaults(self):
        """Test GameState default values."""
        state = GameState(timestamp=1234567890.0)

        assert state.level == 0
        assert state.score == 0
        assert state.songs_completed == 0


class TestDetectionResultDataclass:
    """Test DetectionResult dataclass."""

    def test_detection_result_creation(self):
        """Test creating DetectionResult."""
        result = DetectionResult(
            class_name="small_note",
            confidence=0.95,
            x=100,
            y=200,
            width=50,
            height=60,
            method="yolo",
            detection_time=0.015,
        )

        assert result.class_name == "small_note"
        assert result.confidence == 0.95
        assert result.x == 100
        assert result.method == "yolo"


class TestErrorRecoveryIntegration:
    """Test integrated error recovery."""

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl.GuitarGirl.__init__')
    def test_integrated_error_recovery(self, mock_base_init):
        """Test integrated error recovery."""
        mock_base_init.return_value = None

        game = GuitarGirlFullyEnhanced()

        # Without initialized systems
        result = game.integrated_error_recovery("test_error")

        # Should fail gracefully
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
