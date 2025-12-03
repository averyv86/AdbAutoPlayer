"""Integration tests for Guitar Girl game automation with timing and detection.

Tests cover:
- Note detection with confidence thresholds
- Timing-aware tap system
- Rhythm analysis from tap history
- YOLO class definitions and fallbacks
- Game state management
- Integration with game mechanics
"""

import pytest
from time import time, sleep
from unittest.mock import Mock, patch, MagicMock
from collections import deque

from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.guitar_girl import (
    GuitarGirl,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.guitar_girl.yolo_classes import (
    YOLO_CLASSES,
    NoteType,
    get_class_by_id,
    get_class_by_name,
    get_all_templates,
    get_confidence_threshold,
    get_score_multiplier,
)


class TestYOLOClassDefinitions:
    """Test YOLO class definitions for Guitar Girl notes."""

    def test_yolo_classes_count(self):
        """Verify all 5 YOLO classes are defined."""
        assert len(YOLO_CLASSES) == 5
        assert all(cid in range(5) for cid in YOLO_CLASSES.keys())

    def test_yolo_class_by_id(self):
        """Test retrieving YOLO class by ID."""
        for class_id in range(5):
            note_class = get_class_by_id(class_id)
            assert note_class.class_id == class_id
            assert note_class.confidence_threshold > 0.0
            assert note_class.score_multiplier > 0.0

    def test_yolo_class_by_name(self):
        """Test retrieving YOLO class by name."""
        names = ["small_note", "big_note", "big_note2", "hold_note", "double_note"]
        for name in names:
            note_class = get_class_by_name(name)
            assert note_class.name == name
            assert note_class.template_fallback.endswith(".png")

    def test_yolo_class_invalid_id(self):
        """Test error handling for invalid class ID."""
        with pytest.raises(ValueError):
            get_class_by_id(5)

    def test_yolo_class_invalid_name(self):
        """Test error handling for invalid class name."""
        with pytest.raises(ValueError):
            get_class_by_name("invalid_note")

    def test_all_templates_retrieval(self):
        """Test retrieving all template file names."""
        templates = get_all_templates()
        assert len(templates) == 5
        assert all(t.endswith(".png") for t in templates)
        assert "note.png" in templates
        assert "big_note.png" in templates
        assert "big_note2.png" in templates

    def test_confidence_thresholds(self):
        """Test confidence thresholds for each class."""
        assert get_confidence_threshold(0) == 0.70  # small_note
        assert get_confidence_threshold(1) == 0.75  # big_note
        assert get_confidence_threshold(2) == 0.75  # big_note2
        assert get_confidence_threshold(3) == 0.80  # hold_note
        assert get_confidence_threshold(4) == 0.85  # double_note

    def test_score_multipliers(self):
        """Test score multipliers for note types."""
        assert get_score_multiplier(0) == 1.0  # small_note
        assert get_score_multiplier(1) == 1.5  # big_note
        assert get_score_multiplier(2) == 1.5  # big_note2
        assert get_score_multiplier(3) == 2.0  # hold_note
        assert get_score_multiplier(4) == 3.0  # double_note


class TestGuitarGirlInitialization:
    """Test Guitar Girl game initialization."""

    def test_guitar_girl_init(self):
        """Test GuitarGirl initialization with default values."""
        with patch.object(GuitarGirl, "open_eyes"):
            game = GuitarGirl()
            assert game.package_name_prefixes == ["com.neowiz.game.guitargirl"]
            assert len(game.tap_history) == 0
            assert game.last_tap_time == 0
            assert game.note_detection_stats["small_notes"] == 0
            assert game.note_detection_stats["misses"] == 0

    def test_tap_history_maxlen(self):
        """Test tap history maintains maxlen constraint."""
        with patch.object(GuitarGirl, "open_eyes"):
            game = GuitarGirl()
            assert game.tap_history.maxlen == 100

    def test_note_detection_stats_initialization(self):
        """Test note detection stats are properly initialized."""
        with patch.object(GuitarGirl, "open_eyes"):
            game = GuitarGirl()
            required_keys = [
                "small_notes",
                "big_notes",
                "big_notes2",
                "hold_notes",
                "double_notes",
                "misses",
            ]
            for key in required_keys:
                assert key in game.note_detection_stats
                assert game.note_detection_stats[key] == 0


class TestNoteDetectionLogic:
    """Test note detection with timing awareness."""

    @patch.object(GuitarGirl, "find_any_template")
    @patch.object(GuitarGirl, "open_eyes")
    def test_detect_notes_with_timing(self, mock_eyes, mock_find):
        """Test note detection returns tuple with result and note type."""
        game = GuitarGirl()

        # Mock template match result
        mock_result = Mock()
        mock_result.template = "big_note.png"
        mock_result.confidence = 0.76

        mock_find.return_value = mock_result

        detection = game._detect_notes_with_timing()

        assert detection is not None
        result, note_type = detection
        assert result == mock_result
        assert "big_note" in note_type

    @patch.object(GuitarGirl, "find_any_template")
    @patch.object(GuitarGirl, "open_eyes")
    def test_detect_notes_miss(self, mock_eyes, mock_find):
        """Test note detection handles no notes found."""
        game = GuitarGirl()
        mock_find.return_value = None

        detection = game._detect_notes_with_timing()

        assert detection is None
        assert game.note_detection_stats["misses"] == 1

    @patch.object(GuitarGirl, "find_any_template")
    @patch.object(GuitarGirl, "open_eyes")
    def test_detect_notes_increments_stats(self, mock_eyes, mock_find):
        """Test detection increments correct statistics."""
        game = GuitarGirl()

        # Test small note detection
        mock_result = Mock()
        mock_result.template = "note.png"
        mock_result.confidence = 0.72
        mock_find.return_value = mock_result

        game._detect_notes_with_timing()
        assert game.note_detection_stats["small_notes"] == 1

    @patch.object(GuitarGirl, "open_eyes")
    def test_tap_with_timing_tracking(self, mock_eyes):
        """Test tap timing is tracked correctly."""
        game = GuitarGirl()

        mock_result = Mock()
        before = time()
        game._tap_with_timing(mock_result)
        after = time()

        assert len(game.tap_history) == 1
        assert before <= game.last_tap_time <= after
        assert game.tap_history[0][1] == "tap"


class TestRhythmAnalysis:
    """Test rhythm analysis from tap history."""

    @patch.object(GuitarGirl, "open_eyes")
    def test_rhythm_analysis_empty_history(self, mock_eyes):
        """Test rhythm analysis with empty tap history."""
        game = GuitarGirl()
        rhythm = game._get_tap_rhythm_analysis()

        assert rhythm["avg_interval"] == 0
        assert rhythm["consistency"] == 0

    @patch.object(GuitarGirl, "open_eyes")
    def test_rhythm_analysis_single_tap(self, mock_eyes):
        """Test rhythm analysis with single tap."""
        game = GuitarGirl()
        game.tap_history.append((time(), "tap"))

        rhythm = game._get_tap_rhythm_analysis()

        assert rhythm["avg_interval"] == 0
        assert rhythm["consistency"] == 0

    @patch.object(GuitarGirl, "open_eyes")
    def test_rhythm_analysis_consistent_taps(self, mock_eyes):
        """Test rhythm analysis with consistent tap intervals."""
        game = GuitarGirl()
        base_time = time()

        # Add taps with 0.5 second intervals
        for i in range(5):
            game.tap_history.append((base_time + i * 0.5, "tap"))

        rhythm = game._get_tap_rhythm_analysis()

        # With perfect consistency, intervals should be ~0.5
        assert 0.4 < rhythm["avg_interval"] < 0.6
        assert rhythm["consistency"] > 95  # Very consistent

    @patch.object(GuitarGirl, "open_eyes")
    def test_rhythm_analysis_variable_taps(self, mock_eyes):
        """Test rhythm analysis with variable tap intervals."""
        game = GuitarGirl()
        base_time = time()

        # Add taps with varying intervals
        game.tap_history.append((base_time, "tap"))
        game.tap_history.append((base_time + 0.3, "tap"))
        game.tap_history.append((base_time + 0.8, "tap"))
        game.tap_history.append((base_time + 1.2, "tap"))

        rhythm = game._get_tap_rhythm_analysis()

        assert rhythm["avg_interval"] > 0
        assert rhythm["consistency"] < 100  # Inconsistent


class TestGameMechanics:
    """Test core game mechanics integration."""

    @patch.object(GuitarGirl, "is_game_running")
    @patch.object(GuitarGirl, "start_game")
    @patch.object(GuitarGirl, "open_eyes")
    def test_start_game_if_not_running(self, mock_eyes, mock_start, mock_is_running):
        """Test game restart logic."""
        game = GuitarGirl()

        # Test when game is running
        mock_is_running.return_value = True
        game._start_game_if_not_running()
        mock_start.assert_not_called()

        # Test when game is not running
        mock_is_running.return_value = False
        game._start_game_if_not_running()
        mock_start.assert_called_once()

    @patch.object(GuitarGirl, "tap")
    @patch.object(GuitarGirl, "open_eyes")
    def test_open_guitar_girl_tab(self, mock_eyes, mock_tap):
        """Test opening guitar girl tab."""
        game = GuitarGirl()
        game._open_guitar_girl_tab()

        mock_tap.assert_called_once()

    @patch.object(GuitarGirl, "find_any_template")
    @patch.object(GuitarGirl, "tap")
    @patch.object(GuitarGirl, "open_eyes")
    def test_check_for_popups(self, mock_eyes, mock_tap, mock_find):
        """Test popup detection and closing."""
        game = GuitarGirl()

        # Test when popup exists
        mock_result = Mock()
        mock_result.template = "close.png"
        mock_find.side_effect = [mock_result, None]

        with patch.object(game, "_tap_coordinates_till_template_disappears"):
            game._check_for_popups()


class TestPerformanceMetrics:
    """Test performance tracking and metrics."""

    @patch.object(GuitarGirl, "open_eyes")
    def test_note_detection_tracking(self, mock_eyes):
        """Test note detection statistics tracking."""
        with patch.object(GuitarGirl, "find_any_template") as mock_find:
            game = GuitarGirl()

            # Simulate multiple note detections
            for _ in range(3):
                mock_result = Mock()
                mock_result.template = "note.png"
                mock_find.return_value = mock_result
                game._detect_notes_with_timing()

            assert game.note_detection_stats["small_notes"] == 3

    @patch.object(GuitarGirl, "open_eyes")
    def test_mixed_note_detection_stats(self, mock_eyes):
        """Test mixed note type detection statistics."""
        with patch.object(GuitarGirl, "find_any_template") as mock_find:
            game = GuitarGirl()

            # Simulate different note types
            notes_sequence = [
                ("note.png", "small_note"),
                ("big_note.png", "big_note"),
                ("big_note2.png", "big_note2"),
            ]

            for template, _ in notes_sequence:
                mock_result = Mock()
                mock_result.template = template
                mock_find.return_value = mock_result
                game._detect_notes_with_timing()

            assert game.note_detection_stats["small_notes"] == 1
            assert game.note_detection_stats["big_notes"] == 1
            assert game.note_detection_stats["big_notes2"] == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch.object(GuitarGirl, "open_eyes")
    def test_tap_history_overflow(self, mock_eyes):
        """Test tap history respects maxlen constraint."""
        game = GuitarGirl()

        # Add more than maxlen taps
        for i in range(150):
            game.tap_history.append((time() + i * 0.01, f"tap_{i}"))

        # Should only keep last 100
        assert len(game.tap_history) == 100

    @patch.object(GuitarGirl, "find_any_template")
    @patch.object(GuitarGirl, "open_eyes")
    def test_detect_notes_timing_update(self, mock_eyes, mock_find):
        """Test timing is updated on detection."""
        game = GuitarGirl()

        initial_time = game.last_tap_time
        mock_result = Mock()
        mock_result.template = "note.png"
        mock_find.return_value = mock_result

        game._detect_notes_with_timing()

        assert game.last_tap_time > initial_time

    @patch.object(GuitarGirl, "open_eyes")
    def test_settings_property_raises(self, mock_eyes):
        """Test that settings property raises NotImplementedError."""
        game = GuitarGirl()

        with pytest.raises(RuntimeError, match="Not Implemented"):
            _ = game.settings


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
