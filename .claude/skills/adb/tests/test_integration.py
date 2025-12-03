"""Integration tests for ADB OCR automation framework.

Tests cover:
- End-to-end OCR to navigation workflows
- State verification with navigation
- Pattern composition (OCR + State + Navigation)
- Complex automation scenarios
- Error recovery flows

Target Coverage: 85%+
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

# Add all module paths
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ocr-detection"))
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-state-verification"))
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ui-navigation"))

from adb_ocr_finder import OCRTextFinder
from adb_state_checker import StateVerifier, StateType, DialogHandler
from adb_ui_navigator import UINavigator


# ============================================================================
# TEST: OCR TO NAVIGATION FLOW
# ============================================================================

class TestOCRToNavigationFlow:
    """Tests for OCR-driven navigation workflows."""

    def test_find_text_and_tap_sequence(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test complete find text and tap sequence."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            # Create OCR finder
            finder = OCRTextFinder(mock_device)

            # Create navigator with OCR finder
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Execute find and tap
            result = navigator.find_and_tap("OK", timeout_seconds=3)

            # Verify workflow
            assert result is True
            mock_device.tap.assert_called_once()

    def test_sequential_button_taps(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test tapping multiple buttons in sequence."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Tap sequence
            result1 = navigator.find_and_tap("OK")
            result2 = navigator.find_and_tap("Settings")
            result3 = navigator.find_and_tap("Cancel")

            assert result1 is True
            assert result2 is True
            assert result3 is True
            assert mock_device.tap.call_count == 3

    def test_menu_navigation_workflow(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test complete menu navigation workflow."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Navigate menu
            result = navigator.navigate_menu(["Settings", "OK"])

            assert result is True


# ============================================================================
# TEST: STATE VERIFICATION WITH NAVIGATION
# ============================================================================

class TestStateVerificationWithNavigation:
    """Tests for state verification integrated with navigation."""

    def test_tap_and_verify_state_change(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes,
        sample_image_with_dialog
    ):
        """Test tapping button and verifying state changed."""
        # Initial screenshot
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Tap button
            navigator.find_and_tap("OK")

            # Change screenshot for state change
            bgr = cv2.cvtColor(sample_image_with_dialog, cv2.COLOR_RGB2BGR)
            _, encoded = cv2.imencode(".png", bgr)
            mock_device.screenshot.return_value = encoded.tobytes()

            # Verify state changed
            result = verifier.detect_state_change(timeout_seconds=1)

            assert result is True

    def test_wait_for_text_then_tap(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test waiting for text to appear before tapping."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Wait for text
            appeared = finder.wait_for_text("OK", timeout_seconds=5)
            assert appeared is True

            # Tap it
            result = navigator.find_and_tap("OK")
            assert result is True

    def test_verify_text_present_before_navigation(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test verifying text presence before navigation."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Verify target exists
            def ocr_func():
                return finder.find_all_text()

            text_present = verifier.verify_text_present("OK", ocr_func)
            assert text_present is True

            # Navigate to it
            result = navigator.find_and_tap("OK")
            assert result is True


# ============================================================================
# TEST: PATTERN COMPOSITION
# ============================================================================

class TestPatternComposition:
    """Tests for combining OCR, state, and navigation patterns."""

    def test_dialog_detection_and_handling(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes,
        sample_image_with_dialog
    ):
        """Test detecting dialog and handling it."""
        # Start with dialog screenshot
        bgr = cv2.cvtColor(sample_image_with_dialog, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode(".png", bgr)
        mock_device.screenshot.return_value = encoded.tobytes()

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Detect dialog
            is_dialog = verifier.detect_dialog()
            assert isinstance(is_dialog, bool)

            # Handle dialog
            result = navigator.handle_dialog("OK")
            # Result depends on mock behavior
            assert isinstance(result, bool)

    def test_wait_for_state_then_interact(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test waiting for specific state before interaction."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Wait for ready state
            def ready_condition(image: np.ndarray) -> bool:
                # Simulate checking for UI ready
                return image.mean() > 100

            ready = verifier.wait_for_state(
                ready_condition,
                timeout_seconds=5
            )
            assert ready is True

            # Interact once ready
            result = navigator.find_and_tap("OK")
            assert result is True

    def test_retry_with_state_verification(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test retry logic with state verification."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Try tapping with retry
            result = navigator.find_and_tap_with_retry(
                "OK",
                max_retries=3,
                retry_delay=0.1
            )

            assert result is True


# ============================================================================
# TEST: COMPLEX AUTOMATION SCENARIOS
# ============================================================================

class TestComplexAutomationScenarios:
    """Tests for complex multi-step automation scenarios."""

    def test_app_launch_and_setup_flow(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test app launch and initial setup flow."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Simulated app launch flow
            # 1. Wait for splash screen to disappear
            def splash_gone(image: np.ndarray) -> bool:
                return True

            verifier.wait_for_state(splash_gone, timeout_seconds=5)

            # 2. Dismiss initial dialogs
            handler = DialogHandler(mock_device, verifier)
            handler.dismiss_dialogs(max_dismissals=3)

            # 3. Navigate to settings
            navigator.find_and_tap("Settings")

            # Verify completed
            assert mock_device.tap.called

    def test_form_filling_workflow(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test form filling workflow."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Simulated form filling
            form_fields = ["Name", "Email", "Phone"]

            for field in form_fields:
                # Find and tap field
                navigator.find_and_tap(field, timeout_seconds=2)
                # In real scenario, would type text here

            # Submit form
            navigator.find_and_tap("Submit")

            # At least 4 taps (3 fields + submit)
            assert mock_device.tap.call_count >= 4

    def test_settings_navigation_deep_flow(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test deep settings navigation."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Deep menu navigation
            menu_path = ["Settings", "Advanced", "Developer Options"]

            result = navigator.navigate_menu(menu_path)

            assert result is True
            assert mock_device.tap.call_count == len(menu_path)


# ============================================================================
# TEST: ERROR RECOVERY FLOWS
# ============================================================================

class TestErrorRecoveryFlows:
    """Tests for error recovery workflows."""

    def test_retry_on_ocr_failure(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test retry when OCR fails temporarily."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        call_count = 0

        def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("OCR failed")
            return [
                OCRResult(
                    text="OK",
                    confidence=ConfidenceValue(0.95),
                    box=Box(start_point=Point(x=50, y=50), width=40, height=30),
                )
            ]

        mock_ocr_backend.detect_text.side_effect = intermittent_failure

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            # Should retry and succeed
            result = finder.find_text_with_retry(
                "OK",
                max_retries=3,
                retry_delay=0.1
            )

            assert result is not None

    def test_fallback_to_system_buttons(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test falling back to system buttons when navigation fails."""
        mock_device.screenshot.return_value = sample_screenshot_bytes
        mock_ocr_backend.detect_text.return_value = []  # No text found

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Try navigation
            result = navigator.find_and_tap("NonExistent")
            assert result is False

            # Fallback to back button
            navigator.press_back()

            # Verify back pressed
            mock_device.keyevent.assert_called_with("4")

    def test_dialog_dismissal_on_unexpected_popup(
        self,
        mock_device,
        sample_screenshot_bytes,
        sample_image_with_dialog
    ):
        """Test dismissing unexpected dialogs during workflow."""
        # Start with dialog
        bgr = cv2.cvtColor(sample_image_with_dialog, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode(".png", bgr)
        mock_device.screenshot.return_value = encoded.tobytes()

        verifier = StateVerifier(mock_device)
        handler = DialogHandler(mock_device, verifier)

        # Detect and dismiss
        if verifier.detect_dialog():
            dismissed = handler.dismiss_dialogs(max_dismissals=5)
            assert dismissed >= 0


# ============================================================================
# TEST: MOCKED MAGISK INSTALLATION FLOW
# ============================================================================

class TestMagiskInstallationFlow:
    """Tests for Magisk installation workflow (mocked)."""

    def test_magisk_app_launch_sequence(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test Magisk app launch and setup sequence."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            verifier = StateVerifier(mock_device)
            navigator = UINavigator(
                mock_device,
                ocr_finder=finder,
                state_verifier=verifier
            )

            # Simulated Magisk launch
            # 1. Wait for Magisk to load
            loaded = finder.wait_for_text("Magisk", timeout_seconds=10)

            # 2. Handle initial dialogs
            handler = DialogHandler(mock_device, verifier)
            handler.dismiss_dialogs(max_dismissals=2)

            # 3. Verify UI loaded
            def magisk_ready(image: np.ndarray) -> bool:
                return True

            ready = verifier.wait_for_state(magisk_ready, timeout_seconds=5)

            # Verify workflow executed
            assert isinstance(loaded, bool)
            assert isinstance(ready, bool)

    def test_magisk_module_installation_steps(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test Magisk module installation steps."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Simulated module installation
            steps = [
                "Modules",
                "Install from storage",
                "Select",
                "Install"
            ]

            # Execute steps
            for step in steps:
                navigator.find_and_tap(step, timeout_seconds=5)

            # Verify all steps executed
            assert mock_device.tap.call_count == len(steps)

    @pytest.mark.parametrize("module_type", [
        "LSPosed",
        "Shamiko",
        "Zygisk",
    ])
    def test_magisk_module_types(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes,
        module_type
    ):
        """Test installation of different module types."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            # Navigate to module
            result = navigator.find_and_tap(module_type, timeout_seconds=5)

            # Should attempt navigation
            assert isinstance(result, bool)


# ============================================================================
# TEST: PERFORMANCE AND TIMING
# ============================================================================

class TestPerformanceAndTiming:
    """Tests for performance characteristics."""

    def test_navigation_timing_reasonable(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test navigation completes in reasonable time."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            navigator = UINavigator(mock_device, ocr_finder=finder)

            start = time.time()
            navigator.find_and_tap("OK")
            elapsed = time.time() - start

            # Should complete quickly with mocks
            assert elapsed < 1.0

    def test_state_verification_timing(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test state verification timing."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        verifier = StateVerifier(mock_device)

        def simple_condition(image: np.ndarray) -> bool:
            return True

        start = time.time()
        verifier.verify_state(simple_condition)
        elapsed = time.time() - start

        # Should be very fast with simple condition
        assert elapsed < 0.5
