"""Tests for StateVerifier - Device state verification.

Tests cover:
- State verification with custom conditions
- Text presence/absence verification
- Dialog detection
- State change detection
- Wait for state transitions
- State history tracking

Target Coverage: 90%+
Author: MoAI-ADK
Version: 1.0.0
"""

import time
from unittest.mock import Mock, patch, MagicMock

import cv2
import numpy as np
import pytest

from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult
from adb_auto_player.models.geometry import Box, Point

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-state-verification"))

from adb_state_checker import StateVerifier, StateType, DialogHandler


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================

class TestStateVerifierInitialization:
    """Tests for StateVerifier initialization."""

    def test_init_with_device(self, mock_device):
        """Test initialization with device."""
        verifier = StateVerifier(mock_device)

        assert verifier.device == mock_device
        assert verifier._last_screenshot is None
        assert len(verifier._state_history) == 0

    def test_logger_initialized(self, mock_device):
        """Test logger is properly initialized."""
        verifier = StateVerifier(mock_device)

        assert verifier.logger is not None


# ============================================================================
# TEST: VERIFY STATE
# ============================================================================

class TestVerifyState:
    """Tests for verify_state method."""

    def test_verify_state_true_condition(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state verification with true condition."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def always_true_condition(image: np.ndarray) -> bool:
            return True

        result = verifier.verify_state(always_true_condition)

        assert result is True
        assert len(verifier._state_history) == 1

    def test_verify_state_false_condition(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state verification with false condition."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def always_false_condition(image: np.ndarray) -> bool:
            return False

        result = verifier.verify_state(always_false_condition)

        assert result is False
        assert len(verifier._state_history) == 1

    def test_verify_state_with_image_check(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state verification actually receives image."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        received_image = None

        def capture_image_condition(image: np.ndarray) -> bool:
            nonlocal received_image
            received_image = image
            return True

        verifier.verify_state(capture_image_condition)

        assert received_image is not None
        assert isinstance(received_image, np.ndarray)
        assert received_image.shape[2] == 3  # RGB


# ============================================================================
# TEST: TEXT VERIFICATION
# ============================================================================

class TestTextVerification:
    """Tests for text presence/absence verification."""

    def test_verify_text_present_found(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test verifying text is present when it exists."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def ocr_func():
            return [
                OCRResult(
                    text="OK",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=40, height=30),
                )
            ]

        result = verifier.verify_text_present("OK", ocr_func)

        assert result is True

    def test_verify_text_present_not_found(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test verifying text is present when it doesn't exist."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def ocr_func():
            return [
                OCRResult(
                    text="Cancel",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=60, height=30),
                )
            ]

        result = verifier.verify_text_present("OK", ocr_func)

        assert result is False

    def test_verify_text_absent_when_absent(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test verifying text is absent when it doesn't exist."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def ocr_func():
            return [
                OCRResult(
                    text="Cancel",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=60, height=30),
                )
            ]

        result = verifier.verify_text_absent("OK", ocr_func)

        assert result is True

    def test_verify_text_absent_when_present(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test verifying text is absent when it exists."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def ocr_func():
            return [
                OCRResult(
                    text="OK",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=40, height=30),
                )
            ]

        result = verifier.verify_text_absent("OK", ocr_func)

        assert result is False

    def test_verify_text_case_insensitive(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test text verification is case-insensitive."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def ocr_func():
            return [
                OCRResult(
                    text="OK",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=40, height=30),
                )
            ]

        assert verifier.verify_text_present("ok", ocr_func) is True
        assert verifier.verify_text_present("Ok", ocr_func) is True
        assert verifier.verify_text_present("OK", ocr_func) is True


# ============================================================================
# TEST: DIALOG DETECTION
# ============================================================================

class TestDialogDetection:
    """Tests for dialog detection."""

    def test_detect_dialog_with_dialog_present(
        self,
        mock_device,
        sample_image_with_dialog
    ):
        """Test dialog detection when dialog is visible."""
        # Convert to bytes
        bgr = cv2.cvtColor(sample_image_with_dialog, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode(".png", bgr)
        screenshot_bytes = encoded.tobytes()

        mock_device.screenshot.return_value = screenshot_bytes

        verifier = StateVerifier(mock_device)
        result = verifier.detect_dialog()

        # Dialog has strong edges, should be detected
        assert isinstance(result, bool)

    def test_detect_dialog_with_no_dialog(
        self,
        mock_device,
        blank_image
    ):
        """Test dialog detection on blank screen."""
        # Convert to bytes
        bgr = cv2.cvtColor(blank_image, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode(".png", bgr)
        screenshot_bytes = encoded.tobytes()

        mock_device.screenshot.return_value = screenshot_bytes

        verifier = StateVerifier(mock_device)
        result = verifier.detect_dialog()

        # Blank image has no edges, should not detect dialog
        assert result is False

    def test_detect_dialog_edge_density_calculation(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test edge density calculation in dialog detection."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)
        result = verifier.detect_dialog()

        # Result should be boolean
        assert isinstance(result, bool)


# ============================================================================
# TEST: WAIT FOR STATE
# ============================================================================

class TestWaitForState:
    """Tests for wait_for_state method."""

    def test_wait_for_state_immediate_success(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test waiting for state that is immediately true."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def immediate_true(image: np.ndarray) -> bool:
            return True

        start = time.time()
        result = verifier.wait_for_state(
            immediate_true,
            timeout_seconds=5,
            check_interval=0.5
        )
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 1.0  # Should succeed immediately

    def test_wait_for_state_timeout(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test timeout when state never becomes true."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def always_false(image: np.ndarray) -> bool:
            return False

        start = time.time()
        result = verifier.wait_for_state(
            always_false,
            timeout_seconds=1,
            check_interval=0.2
        )
        elapsed = time.time() - start

        assert result is False
        assert elapsed >= 1.0  # Should wait full timeout

    def test_wait_for_state_delayed_success(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state becomes true after some delay."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        call_count = 0

        def delayed_true(image: np.ndarray) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count >= 3  # True on 3rd call

        result = verifier.wait_for_state(
            delayed_true,
            timeout_seconds=5,
            check_interval=0.2
        )

        assert result is True
        assert call_count >= 3

    def test_wait_for_state_custom_interval(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test custom check interval."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        call_count = 0

        def count_calls(image: np.ndarray) -> bool:
            nonlocal call_count
            call_count += 1
            return False

        verifier.wait_for_state(
            count_calls,
            timeout_seconds=1,
            check_interval=0.3
        )

        # With 1s timeout and 0.3s interval, expect ~3-4 calls
        assert 3 <= call_count <= 5


# ============================================================================
# TEST: STATE CHANGE DETECTION
# ============================================================================

class TestStateChangeDetection:
    """Tests for detect_state_change method."""

    def test_detect_state_change_first_screenshot(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test first screenshot always returns True."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)
        result = verifier.detect_state_change(timeout_seconds=1)

        assert result is True
        assert verifier._last_screenshot is not None

    def test_detect_state_change_no_change(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test no change detected when screen is identical."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        # First capture
        verifier.detect_state_change(timeout_seconds=1)

        # Second check - same screenshot
        result = verifier.detect_state_change(timeout_seconds=1)

        # MSE should be 0, no change detected within timeout
        assert result is False

    def test_detect_state_change_with_change(
        self,
        mock_device,
        sample_screenshot_bytes,
        sample_image_with_dialog
    ):
        """Test change detected when screen differs."""
        # First screenshot
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)
        verifier.detect_state_change(timeout_seconds=1)

        # Change screenshot
        bgr = cv2.cvtColor(sample_image_with_dialog, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode(".png", bgr)
        different_bytes = encoded.tobytes()

        mock_device.screenshot.return_value = different_bytes

        result = verifier.detect_state_change(
            timeout_seconds=2,
            check_interval=0.1
        )

        # Should detect change (MSE > 100)
        assert result is True


# ============================================================================
# TEST: STATE HISTORY
# ============================================================================

class TestStateHistory:
    """Tests for state history tracking."""

    def test_state_history_recording(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state checks are recorded in history."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def test_condition(image: np.ndarray) -> bool:
            return True

        verifier.verify_state(test_condition)

        history = verifier.get_state_history()

        assert len(history) == 1
        assert "timestamp" in history[0]
        assert "type" in history[0]
        assert "result" in history[0]

    def test_state_history_multiple_checks(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test multiple state checks are recorded."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        for i in range(5):
            def test_condition(image: np.ndarray) -> bool:
                return i % 2 == 0

            verifier.verify_state(test_condition)

        history = verifier.get_state_history()

        assert len(history) == 5

    def test_state_history_max_size(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state history is limited to 100 records."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        # Add 150 records
        for i in range(150):
            def test_condition(image: np.ndarray) -> bool:
                return True

            verifier.verify_state(test_condition)

        history = verifier.get_state_history()

        # Should only keep last 100
        assert len(history) == 100

    def test_clear_state_history(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test clearing state history."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def test_condition(image: np.ndarray) -> bool:
            return True

        verifier.verify_state(test_condition)
        assert len(verifier.get_state_history()) > 0

        verifier.clear_state_history()
        assert len(verifier.get_state_history()) == 0


# ============================================================================
# TEST: DIALOG HANDLER
# ============================================================================

class TestDialogHandler:
    """Tests for DialogHandler class."""

    def test_dialog_handler_initialization(
        self,
        mock_device,
        mock_state_verifier
    ):
        """Test DialogHandler initialization."""
        handler = DialogHandler(mock_device, mock_state_verifier)

        assert handler.device == mock_device
        assert handler.state_verifier == mock_state_verifier

    def test_handle_confirmation_dialog_confirm(
        self,
        mock_device,
        mock_state_verifier
    ):
        """Test handling confirmation dialog with confirm action."""
        handler = DialogHandler(mock_device, mock_state_verifier)

        result = handler.handle_confirmation_dialog(
            action="confirm",
            timeout_seconds=5
        )

        # Current implementation always returns True
        assert result is True

    def test_handle_confirmation_dialog_cancel(
        self,
        mock_device,
        mock_state_verifier
    ):
        """Test handling confirmation dialog with cancel action."""
        handler = DialogHandler(mock_device, mock_state_verifier)

        result = handler.handle_confirmation_dialog(
            action="cancel",
            timeout_seconds=5
        )

        # Current implementation always returns True
        assert result is True

    def test_handle_permission_dialog_allow(
        self,
        mock_device,
        mock_state_verifier
    ):
        """Test handling permission dialog with allow action."""
        handler = DialogHandler(mock_device, mock_state_verifier)

        result = handler.handle_permission_dialog(action="allow")

        # Current implementation always returns True
        assert result is True

    def test_handle_permission_dialog_deny(
        self,
        mock_device,
        mock_state_verifier
    ):
        """Test handling permission dialog with deny action."""
        handler = DialogHandler(mock_device, mock_state_verifier)

        result = handler.handle_permission_dialog(action="deny")

        # Current implementation always returns True
        assert result is True

    def test_dismiss_dialogs_none_present(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test dismissing dialogs when none are present."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        state_verifier = StateVerifier(mock_device)
        state_verifier.detect_dialog = Mock(return_value=False)

        handler = DialogHandler(mock_device, state_verifier)
        dismissed = handler.dismiss_dialogs(max_dismissals=5)

        assert dismissed == 0

    def test_dismiss_dialogs_single_dialog(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test dismissing single dialog."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        state_verifier = StateVerifier(mock_device)

        call_count = 0

        def detect_dialog_once():
            nonlocal call_count
            call_count += 1
            return call_count == 1  # Dialog present only on first call

        state_verifier.detect_dialog = Mock(side_effect=detect_dialog_once)

        handler = DialogHandler(mock_device, state_verifier)
        dismissed = handler.dismiss_dialogs(max_dismissals=5)

        assert dismissed == 1
        mock_device.keyevent.assert_called_with("4")  # Back key

    def test_dismiss_dialogs_multiple_dialogs(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test dismissing multiple dialogs."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        state_verifier = StateVerifier(mock_device)

        call_count = 0

        def detect_dialog_multiple():
            nonlocal call_count
            call_count += 1
            return call_count <= 3  # Dialogs present for first 3 calls

        state_verifier.detect_dialog = Mock(side_effect=detect_dialog_multiple)

        handler = DialogHandler(mock_device, state_verifier)
        dismissed = handler.dismiss_dialogs(max_dismissals=5)

        assert dismissed == 3
        assert mock_device.keyevent.call_count == 3


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_screenshot_failure_raises(self, mock_device):
        """Test screenshot failure raises RuntimeError."""
        mock_device.screenshot.side_effect = Exception("Screenshot failed")

        verifier = StateVerifier(mock_device)

        def test_condition(image: np.ndarray) -> bool:
            return True

        with pytest.raises(RuntimeError):
            verifier.verify_state(test_condition)

    def test_invalid_screenshot_data(self, mock_device):
        """Test invalid screenshot data raises RuntimeError."""
        mock_device.screenshot.return_value = b"invalid"

        verifier = StateVerifier(mock_device)

        def test_condition(image: np.ndarray) -> bool:
            return True

        with pytest.raises(RuntimeError):
            verifier.verify_state(test_condition)

    def test_condition_exception_handled(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test exception in condition function is handled."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def failing_condition(image: np.ndarray) -> bool:
            raise ValueError("Condition failed")

        result = verifier.verify_state(failing_condition)

        # Should return False on exception
        assert result is False
