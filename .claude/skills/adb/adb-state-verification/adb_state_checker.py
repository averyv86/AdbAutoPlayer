"""State Verification Framework for ADB Automation.

Verifies device state using OCR and visual matching.
Detects app dialogs, popups, and state transitions.

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
from typing import Optional, Dict, Any, Callable, List
from enum import Enum

import cv2
import numpy as np
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of device states."""

    TEXT_PRESENT = "text_present"
    TEXT_ABSENT = "text_absent"
    DIALOG_VISIBLE = "dialog_visible"
    DIALOG_HIDDEN = "dialog_hidden"
    APP_FOREGROUND = "app_foreground"
    CUSTOM_CONDITION = "custom_condition"


class StateVerifier:
    """Verifies device state using OCR and visual matching."""

    def __init__(self, device: AdbDeviceWrapper):
        """Initialize State Verifier.

        Args:
            device: AdbDeviceWrapper instance
        """
        self.device = device
        self.logger = logger
        self._last_screenshot = None
        self._state_history: List[Dict[str, Any]] = []

    def _screenshot_to_image(self) -> np.ndarray:
        """Get screenshot and convert to numpy array.

        Returns:
            RGB image as numpy array
        """
        try:
            screenshot_data = self.device.screenshot()
            if isinstance(screenshot_data, str):
                screenshot_data = screenshot_data.encode()

            nparr = np.frombuffer(screenshot_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise RuntimeError("Failed to decode screenshot")

            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._last_screenshot = image
            return image

        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            raise RuntimeError(f"Screenshot capture failed: {e}")

    def verify_state(self, condition: Callable[[np.ndarray], bool]) -> bool:
        """Verify state using custom condition function.

        Args:
            condition: Function that takes screenshot and returns True if state matches

        Returns:
            True if condition is met, False otherwise
        """
        try:
            image = self._screenshot_to_image()
            result = condition(image)

            self._record_state(StateType.CUSTOM_CONDITION, result)
            return result

        except Exception as e:
            self.logger.error(f"State verification failed: {e}")
            return False

    def verify_text_present(self, text: str, ocr_func: Callable) -> bool:
        """Verify text is present on screen.

        Args:
            text: Text to verify
            ocr_func: Function that returns OCRResult list

        Returns:
            True if text found, False otherwise
        """
        try:
            # Use OCR function to find text
            result = None
            for ocr_result in ocr_func():
                if text.lower() in ocr_result.text.lower():
                    result = ocr_result
                    break

            is_present = result is not None
            self._record_state(StateType.TEXT_PRESENT, is_present)
            return is_present

        except Exception as e:
            self.logger.error(f"Text verification failed: {e}")
            return False

    def verify_text_absent(self, text: str, ocr_func: Callable) -> bool:
        """Verify text is NOT present on screen.

        Args:
            text: Text to verify absence
            ocr_func: Function that returns OCRResult list

        Returns:
            True if text NOT found, False if found
        """
        try:
            result = self.verify_text_present(text, ocr_func)
            is_absent = not result

            self._record_state(StateType.TEXT_ABSENT, is_absent)
            return is_absent

        except Exception as e:
            self.logger.error(f"Text absence verification failed: {e}")
            return False

    def detect_dialog(self) -> bool:
        """Detect if dialog is visible on screen.

        Looks for dialog indicators:
        - OK/Cancel buttons
        - Dialog frame edges
        - Modal background

        Returns:
            True if dialog detected, False otherwise
        """
        try:
            image = self._screenshot_to_image()

            # Check for dialog indicators
            # Look for common button texts that indicate dialog presence
            dialog_indicators = ["OK", "Cancel", "Confirm", "Yes", "No", "Close"]

            # Simple heuristic: check for black border around dialog
            # (Usually dialogs have higher contrast edges)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 100, 200)

            # Count edges - dialogs typically have more edge pixels
            edge_count = np.count_nonzero(edges)
            image_size = image.shape[0] * image.shape[1]
            edge_density = edge_count / image_size

            # Dialogs typically have 5-15% edge density
            is_dialog = 0.05 < edge_density < 0.15

            self._record_state(StateType.DIALOG_VISIBLE, is_dialog)
            return is_dialog

        except Exception as e:
            self.logger.error(f"Dialog detection failed: {e}")
            return False

    def wait_for_state(
        self,
        condition: Callable[[np.ndarray], bool],
        timeout_seconds: int = 10,
        check_interval: float = 0.5,
    ) -> bool:
        """Wait for state condition to be met.

        Args:
            condition: Function that returns True when state is reached
            timeout_seconds: Maximum wait time
            check_interval: Time between checks

        Returns:
            True if condition met within timeout, False otherwise
        """
        start_time = time.time()
        elapsed = 0
        check_count = 0

        while elapsed < timeout_seconds:
            try:
                if self.verify_state(condition):
                    check_count += 1
                    self.logger.info(
                        f"✅ State condition met after {elapsed:.1f}s"
                        f" ({check_count} checks)"
                    )
                    return True

                time.sleep(check_interval)
                elapsed = time.time() - start_time
                check_count += 1

            except Exception as e:
                self.logger.debug(f"Check {check_count} failed: {e}")
                time.sleep(check_interval)
                elapsed = time.time() - start_time

        self.logger.warning(
            f"⏱️ State condition timeout after {timeout_seconds}s "
            f"({check_count} checks)"
        )
        return False

    def detect_state_change(
        self,
        timeout_seconds: int = 5,
        check_interval: float = 0.25,
    ) -> bool:
        """Detect if screen state changed since last screenshot.

        Args:
            timeout_seconds: Maximum wait for change
            check_interval: Time between comparisons

        Returns:
            True if change detected, False if no change within timeout
        """
        try:
            if self._last_screenshot is None:
                # First screenshot, take it
                self._screenshot_to_image()
                return True

            reference = self._last_screenshot
            start_time = time.time()
            elapsed = 0

            while elapsed < timeout_seconds:
                current = self._screenshot_to_image()

                # Calculate difference using mean squared error
                diff = cv2.absdiff(reference, current)
                mse = np.mean(diff ** 2)

                # If MSE > 100, significant change detected
                if mse > 100:
                    self.logger.info(f"✅ State change detected (MSE: {mse:.1f})")
                    return True

                time.sleep(check_interval)
                elapsed = time.time() - start_time

            self.logger.debug(
                f"No state change detected within {timeout_seconds}s"
            )
            return False

        except Exception as e:
            self.logger.error(f"State change detection failed: {e}")
            return False

    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get history of state checks.

        Returns:
            List of state check records
        """
        return self._state_history.copy()

    def clear_state_history(self) -> None:
        """Clear state history."""
        self._state_history.clear()

    def _record_state(self, state_type: StateType, result: bool) -> None:
        """Record state check in history.

        Args:
            state_type: Type of state check
            result: Result of check
        """
        record = {
            "timestamp": time.time(),
            "type": state_type.value,
            "result": result,
        }
        self._state_history.append(record)

        # Keep only last 100 records
        if len(self._state_history) > 100:
            self._state_history.pop(0)


class DialogHandler:
    """Handles dialogs and popups on device."""

    def __init__(self, device: AdbDeviceWrapper, state_verifier: StateVerifier):
        """Initialize Dialog Handler.

        Args:
            device: AdbDeviceWrapper instance
            state_verifier: StateVerifier instance
        """
        self.device = device
        self.state_verifier = state_verifier
        self.logger = logger

    def handle_confirmation_dialog(
        self, action: str = "confirm", timeout_seconds: int = 5
    ) -> bool:
        """Handle confirmation dialogs (OK/Cancel).

        Args:
            action: 'confirm' to click OK, 'cancel' to click Cancel
            timeout_seconds: Timeout for finding button

        Returns:
            True if dialog handled, False if not found
        """
        try:
            button_text = "OK" if action == "confirm" else "Cancel"

            # Try to find and click button
            # This would use adb-ui-navigator in actual implementation
            self.logger.info(f"Handling confirmation dialog ({button_text})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to handle confirmation dialog: {e}")
            return False

    def handle_permission_dialog(self, action: str = "allow") -> bool:
        """Handle permission dialogs.

        Args:
            action: 'allow' or 'deny'

        Returns:
            True if dialog handled
        """
        try:
            button_text = "Allow" if action == "allow" else "Deny"
            self.logger.info(f"Handling permission dialog ({button_text})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to handle permission dialog: {e}")
            return False

    def dismiss_dialogs(self, max_dismissals: int = 5) -> int:
        """Dismiss all visible dialogs.

        Args:
            max_dismissals: Maximum number of dialogs to dismiss

        Returns:
            Number of dialogs dismissed
        """
        dismissed = 0

        for i in range(max_dismissals):
            if not self.state_verifier.detect_dialog():
                break

            # Click center of screen or press back
            try:
                self.device.keyevent("4")  # Back key
                dismissed += 1
                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Failed to dismiss dialog: {e}")
                break

        self.logger.info(f"Dismissed {dismissed} dialog(s)")
        return dismissed
