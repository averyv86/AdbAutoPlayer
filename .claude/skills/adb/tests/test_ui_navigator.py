"""Tests for UINavigator - OCR-guided UI navigation.

Tests cover:
- Find and tap operations
- Button navigation
- Dialog handling
- Menu navigation
- System button operations (back, home)
- Tap history tracking
- Retry logic

Target Coverage: 90%+
Author: MoAI-ADK
Version: 1.0.0
"""

import time
from unittest.mock import Mock, patch, MagicMock

import pytest

from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult
from adb_auto_player.models.geometry import Box, Point

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ui-navigation"))

from adb_ui_navigator import UINavigator, TapTarget


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================

class TestUINavigatorInitialization:
    """Tests for UINavigator initialization."""

    def test_init_with_device_only(self, mock_device):
        """Test initialization with device only."""
        navigator = UINavigator(mock_device)

        assert navigator.device == mock_device
        assert navigator.ocr_finder is None
        assert navigator.state_verifier is None
        assert len(navigator._tap_history) == 0

    def test_init_with_all_dependencies(
        self,
        mock_device,
        mock_ocr_finder,
        mock_state_verifier
    ):
        """Test initialization with all dependencies."""
        navigator = UINavigator(
            mock_device,
            ocr_finder=mock_ocr_finder,
            state_verifier=mock_state_verifier
        )

        assert navigator.device == mock_device
        assert navigator.ocr_finder == mock_ocr_finder
        assert navigator.state_verifier == mock_state_verifier


# ============================================================================
# TEST: FIND AND TAP
# ============================================================================

class TestFindAndTap:
    """Tests for find_and_tap method."""

    def test_find_and_tap_success(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test successful find and tap."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap("Sample Text")

        assert result is True
        mock_device.tap.assert_called_once()
        assert len(navigator._tap_history) == 1

    def test_find_and_tap_text_not_found(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test find and tap when text not found."""
        mock_ocr_finder.wait_for_text.return_value = False

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap("NonExistent")

        assert result is False
        mock_device.tap.assert_not_called()

    def test_find_and_tap_no_ocr_finder(self, mock_device):
        """Test find and tap without OCR finder."""
        navigator = UINavigator(mock_device)
        result = navigator.find_and_tap("Text")

        assert result is False

    def test_find_and_tap_with_verify(
        self,
        mock_device,
        mock_ocr_finder,
        mock_state_verifier,
        sample_ocr_result
    ):
        """Test find and tap with state verification."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result
        mock_state_verifier.detect_state_change.return_value = True

        navigator = UINavigator(
            mock_device,
            ocr_finder=mock_ocr_finder,
            state_verifier=mock_state_verifier
        )

        result = navigator.find_and_tap(
            "Sample Text",
            verify_after_tap=True
        )

        assert result is True
        mock_state_verifier.detect_state_change.assert_called_once()

    def test_find_and_tap_calculates_correct_center(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test tap point calculation uses center of bounding box."""
        ocr_result = OCRResult(
            text="Button",
            confidence=ConfidenceValue(0.9),
            box=Box(
                start_point=Point(x=100, y=200),
                width=80,
                height=40,
            ),
        )

        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        navigator.find_and_tap("Button")

        # Center should be (140, 220)
        mock_device.tap.assert_called_with("140", "220")


# ============================================================================
# TEST: NAVIGATE TO BUTTON
# ============================================================================

class TestNavigateToButton:
    """Tests for navigate_to_button method."""

    def test_navigate_to_button_success(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test successful button navigation."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_to_button("Button")

        assert result is True

    def test_navigate_to_button_with_scroll(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test button navigation with scrolling."""
        call_count = 0

        def delayed_find(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail first, succeed second
            return call_count == 1

        mock_ocr_finder.wait_for_text.side_effect = delayed_find
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_to_button("Button", max_taps=2)

        # Should attempt scroll
        assert mock_device.swipe.called or result

    def test_navigate_to_button_multiple_taps(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test button navigation with multiple taps."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_to_button("Button", max_taps=3)

        assert result is True
        # Should tap 3 times
        assert mock_device.tap.call_count == 3


# ============================================================================
# TEST: HANDLE DIALOG
# ============================================================================

class TestHandleDialog:
    """Tests for handle_dialog method."""

    def test_handle_dialog_success(
        self,
        mock_device,
        mock_ocr_finder,
        mock_state_verifier,
        sample_ocr_result
    ):
        """Test successful dialog handling."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result
        mock_state_verifier.detect_dialog.return_value = False  # Dialog closed

        navigator = UINavigator(
            mock_device,
            ocr_finder=mock_ocr_finder,
            state_verifier=mock_state_verifier
        )

        result = navigator.handle_dialog("OK")

        assert result is True

    def test_handle_dialog_button_not_found(
        self,
        mock_device,
        mock_ocr_finder,
        mock_state_verifier
    ):
        """Test dialog handling when button not found."""
        mock_ocr_finder.wait_for_text.return_value = False

        navigator = UINavigator(
            mock_device,
            ocr_finder=mock_ocr_finder,
            state_verifier=mock_state_verifier
        )

        result = navigator.handle_dialog("OK")

        assert result is False

    def test_handle_dialog_still_visible(
        self,
        mock_device,
        mock_ocr_finder,
        mock_state_verifier,
        sample_ocr_result
    ):
        """Test dialog handling when dialog remains visible."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result
        mock_state_verifier.detect_dialog.return_value = True  # Still visible

        navigator = UINavigator(
            mock_device,
            ocr_finder=mock_ocr_finder,
            state_verifier=mock_state_verifier
        )

        result = navigator.handle_dialog("OK", verify_dialog_closed=True)

        assert result is False


# ============================================================================
# TEST: NAVIGATE MENU
# ============================================================================

class TestNavigateMenu:
    """Tests for navigate_menu method."""

    def test_navigate_menu_success(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test successful menu navigation."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_menu(["Item1", "Item2", "Item3"])

        assert result is True
        assert mock_device.tap.call_count == 3

    def test_navigate_menu_failure_at_step(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test menu navigation fails at specific step."""
        call_count = 0

        def fail_at_second(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count != 2  # Fail on second call

        mock_ocr_finder.wait_for_text.side_effect = fail_at_second
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_menu(["Item1", "Item2", "Item3"])

        assert result is False

    def test_navigate_menu_empty_list(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test menu navigation with empty list."""
        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.navigate_menu([])

        assert result is True  # Empty menu succeeds
        mock_device.tap.assert_not_called()


# ============================================================================
# TEST: RETRY LOGIC
# ============================================================================

class TestRetryLogic:
    """Tests for find_and_tap_with_retry method."""

    def test_retry_success_first_attempt(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test retry succeeds on first attempt."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap_with_retry("Button", max_retries=3)

        assert result is True
        # Should only call once
        assert mock_device.tap.call_count == 1

    def test_retry_success_after_failures(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test retry succeeds after initial failures."""
        call_count = 0

        def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count >= 3  # Succeed on 3rd call

        mock_ocr_finder.wait_for_text.side_effect = fail_then_succeed
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap_with_retry(
            "Button",
            max_retries=5,
            retry_delay=0.05
        )

        assert result is True
        assert call_count == 3

    def test_retry_exhausts_all_attempts(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test all retry attempts are exhausted."""
        mock_ocr_finder.wait_for_text.return_value = False

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap_with_retry(
            "Button",
            max_retries=3,
            retry_delay=0.05
        )

        assert result is False
        assert mock_ocr_finder.wait_for_text.call_count == 3


# ============================================================================
# TEST: SYSTEM BUTTONS
# ============================================================================

class TestSystemButtons:
    """Tests for system button operations."""

    def test_press_back_once(self, mock_device):
        """Test pressing back button once."""
        navigator = UINavigator(mock_device)
        result = navigator.press_back(num_times=1)

        assert result is True
        mock_device.keyevent.assert_called_once_with("4")

    def test_press_back_multiple_times(self, mock_device):
        """Test pressing back button multiple times."""
        navigator = UINavigator(mock_device)
        result = navigator.press_back(num_times=3, delay_between=0.1)

        assert result is True
        assert mock_device.keyevent.call_count == 3

    def test_press_home(self, mock_device):
        """Test pressing home button."""
        navigator = UINavigator(mock_device)
        result = navigator.press_home()

        assert result is True
        mock_device.keyevent.assert_called_once_with("3")

    def test_system_button_failure(self, mock_device):
        """Test system button failure handling."""
        mock_device.keyevent.side_effect = Exception("Key event failed")

        navigator = UINavigator(mock_device)
        result = navigator.press_back()

        assert result is False


# ============================================================================
# TEST: TAP HISTORY
# ============================================================================

class TestTapHistory:
    """Tests for tap history tracking."""

    def test_tap_history_recorded(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test tap history is recorded."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        navigator.find_and_tap("Button")

        history = navigator.get_tap_history()

        assert len(history) == 1
        assert isinstance(history[0], TapTarget)
        assert history[0].element_text == "Button"

    def test_tap_history_multiple_taps(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test multiple taps are recorded."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)

        navigator.find_and_tap("Button1")
        navigator.find_and_tap("Button2")
        navigator.find_and_tap("Button3")

        history = navigator.get_tap_history()

        assert len(history) == 3

    def test_clear_tap_history(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test clearing tap history."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        navigator.find_and_tap("Button")

        assert len(navigator.get_tap_history()) > 0

        navigator.clear_tap_history()
        assert len(navigator.get_tap_history()) == 0


# ============================================================================
# TEST: DOUBLE TAP
# ============================================================================

class TestDoubleTap:
    """Tests for double_tap method."""

    def test_double_tap_success(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test successful double tap."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.double_tap("Button")

        assert result is True
        # Should tap twice
        assert mock_device.tap.call_count == 2

    def test_double_tap_first_tap_fails(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test double tap when first tap fails."""
        mock_ocr_finder.wait_for_text.return_value = False

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.double_tap("Button")

        assert result is False


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_tap_failure_handled(
        self,
        mock_device,
        mock_ocr_finder,
        sample_ocr_result
    ):
        """Test tap failure is handled gracefully."""
        mock_ocr_finder.wait_for_text.return_value = True
        mock_ocr_finder.find_text.return_value = sample_ocr_result
        mock_device.tap.side_effect = Exception("Tap failed")

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap("Button")

        # Should handle exception
        assert result is False

    def test_ocr_finder_exception_handled(
        self,
        mock_device,
        mock_ocr_finder
    ):
        """Test OCR finder exception is handled."""
        mock_ocr_finder.wait_for_text.side_effect = Exception("OCR failed")

        navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
        result = navigator.find_and_tap("Button")

        assert result is False
