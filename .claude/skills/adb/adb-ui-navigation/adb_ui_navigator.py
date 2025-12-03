"""UI Navigation Framework for ADB Automation.

Navigate device UI using OCR-guided tap sequences.
Find and tap buttons, handle menus, and perform dialog interactions.

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass

from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_auto_player.models.ocr import OCRResult

logger = logging.getLogger(__name__)


@dataclass
class TapTarget:
    """Represents a tap target with location and metadata."""

    x: int
    y: int
    element_text: str = ""
    confidence: float = 0.0
    attempts: int = 0


class UINavigator:
    """Navigates device UI using OCR-guided tap sequences."""

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ocr_finder: Callable = None,
        state_verifier: Callable = None,
    ):
        """Initialize UI Navigator.

        Args:
            device: AdbDeviceWrapper instance
            ocr_finder: Optional OCRTextFinder instance
            state_verifier: Optional StateVerifier instance
        """
        self.device = device
        self.ocr_finder = ocr_finder
        self.state_verifier = state_verifier
        self.logger = logger
        self._tap_history: List[TapTarget] = []

    def _calculate_tap_point(self, ocr_result: OCRResult) -> Tuple[int, int]:
        """Calculate tap point from OCR bounding box.

        Args:
            ocr_result: OCRResult with bounding box

        Returns:
            Tuple of (x, y) coordinates for center of element
        """
        box = ocr_result.box
        center_x = box.start_point.x + (box.width // 2)
        center_y = box.start_point.y + (box.height // 2)
        return center_x, center_y

    def find_and_tap(
        self,
        target_text: str,
        timeout_seconds: int = 5,
        post_tap_delay: float = 0.5,
        verify_after_tap: bool = False,
    ) -> bool:
        """Find text on screen and tap it.

        Args:
            target_text: Text to find and tap
            timeout_seconds: Timeout for finding text
            post_tap_delay: Delay after tap (for UI to respond)
            verify_after_tap: Verify state changed after tap

        Returns:
            True if tap successful, False otherwise
        """
        try:
            if not self.ocr_finder:
                self.logger.error("OCR finder not available")
                return False

            # Wait for text to appear
            if not self.ocr_finder.wait_for_text(
                target_text, timeout_seconds=timeout_seconds
            ):
                self.logger.warning(f"Text not found: {target_text}")
                return False

            # Find text location
            ocr_result = self.ocr_finder.find_text(target_text)
            if not ocr_result:
                self.logger.warning(f"Failed to locate text: {target_text}")
                return False

            # Calculate and perform tap
            x, y = self._calculate_tap_point(ocr_result)
            self.device.tap(str(x), str(y))

            # Record tap
            target = TapTarget(
                x=x,
                y=y,
                element_text=target_text,
                confidence=float(ocr_result.confidence.value),
            )
            self._tap_history.append(target)

            self.logger.info(f"✅ Tapped: '{target_text}' at ({x}, {y})")

            # Wait for UI response
            time.sleep(post_tap_delay)

            # Verify state changed if requested
            if verify_after_tap and self.state_verifier:
                if self.state_verifier.detect_state_change(timeout_seconds=2):
                    self.logger.info(f"State change verified after tap")

            return True

        except Exception as e:
            self.logger.error(f"find_and_tap failed: {e}")
            return False

    def navigate_to_button(
        self,
        button_text: str,
        max_taps: int = 1,
        post_tap_delay: float = 1.0,
    ) -> bool:
        """Navigate to button and tap it (with scrolling support).

        Args:
            button_text: Button text to find
            max_taps: Number of times to tap
            post_tap_delay: Delay between taps

        Returns:
            True if navigation successful
        """
        try:
            for tap_num in range(max_taps):
                if self.find_and_tap(
                    button_text,
                    timeout_seconds=3,
                    post_tap_delay=post_tap_delay,
                ):
                    if tap_num == max_taps - 1:
                        self.logger.info(
                            f"✅ Navigation to '{button_text}' complete"
                        )
                        return True
                else:
                    # Try scrolling if text not found
                    self.logger.debug(f"Text not found, attempting scroll")
                    if not self._scroll_screen(direction="down"):
                        self.logger.warning(
                            f"Failed to navigate to {button_text}"
                        )
                        return False

            return True

        except Exception as e:
            self.logger.error(f"navigate_to_button failed: {e}")
            return False

    def handle_dialog(
        self,
        button_to_click: str,
        timeout_seconds: int = 5,
        verify_dialog_closed: bool = True,
    ) -> bool:
        """Handle dialog by clicking specified button.

        Args:
            button_to_click: Text of button to click ('OK', 'Cancel', 'Yes', 'No')
            timeout_seconds: Timeout for finding button
            verify_dialog_closed: Verify dialog closed after click

        Returns:
            True if dialog handled successfully
        """
        try:
            self.logger.info(f"Handling dialog, clicking: {button_to_click}")

            # Find and click button
            if not self.find_and_tap(
                button_to_click, timeout_seconds=timeout_seconds
            ):
                self.logger.warning(f"Could not find button: {button_to_click}")
                return False

            # Verify dialog closed
            if verify_dialog_closed and self.state_verifier:
                time.sleep(0.5)
                if self.state_verifier.detect_dialog():
                    self.logger.warning("Dialog still visible after click")
                    return False

            self.logger.info(f"✅ Dialog handled successfully")
            return True

        except Exception as e:
            self.logger.error(f"handle_dialog failed: {e}")
            return False

    def navigate_menu(
        self, menu_items: List[str], timeout_per_item: int = 3
    ) -> bool:
        """Navigate through menu items in sequence.

        Args:
            menu_items: List of menu item texts in order
            timeout_per_item: Timeout for finding each item

        Returns:
            True if all items tapped successfully
        """
        try:
            for i, item in enumerate(menu_items):
                self.logger.info(f"Menu step {i + 1}/{len(menu_items)}: {item}")

                if not self.find_and_tap(
                    item, timeout_seconds=timeout_per_item, post_tap_delay=0.5
                ):
                    self.logger.error(f"Failed at menu item: {item}")
                    return False

            self.logger.info(f"✅ Menu navigation complete")
            return True

        except Exception as e:
            self.logger.error(f"navigate_menu failed: {e}")
            return False

    def find_and_tap_with_retry(
        self,
        target_text: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        post_tap_delay: float = 0.5,
    ) -> bool:
        """Find and tap with retry logic.

        Args:
            target_text: Text to find and tap
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            post_tap_delay: Delay after tap

        Returns:
            True if tap successful
        """
        try:
            for attempt in range(max_retries):
                if self.find_and_tap(
                    target_text,
                    timeout_seconds=2,
                    post_tap_delay=post_tap_delay,
                ):
                    return True

                if attempt < max_retries - 1:
                    self.logger.debug(
                        f"Attempt {attempt + 1} failed, retrying in {retry_delay}s"
                    )
                    time.sleep(retry_delay)

            self.logger.error(
                f"Failed to tap '{target_text}' after {max_retries} attempts"
            )
            return False

        except Exception as e:
            self.logger.error(f"find_and_tap_with_retry failed: {e}")
            return False

    def _scroll_screen(
        self, direction: str = "down", distance: int = 500
    ) -> bool:
        """Scroll screen in specified direction.

        Args:
            direction: 'up' or 'down'
            distance: Scroll distance in pixels

        Returns:
            True if scroll performed
        """
        try:
            # Get screen dimensions (assume 1440x3120 for standard device)
            screen_width = 1440
            screen_height = 3120

            if direction == "down":
                start_y = screen_height // 3
                end_y = start_y + distance
            else:  # up
                start_y = screen_height * 2 // 3
                end_y = start_y - distance

            center_x = screen_width // 2

            self.device.swipe(
                str(center_x), str(start_y), str(center_x), str(end_y), "300"
            )

            self.logger.debug(f"Scrolled {direction} by {distance}px")
            time.sleep(0.3)
            return True

        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return False

    def get_tap_history(self) -> List[TapTarget]:
        """Get history of all taps performed.

        Returns:
            List of TapTarget records
        """
        return self._tap_history.copy()

    def clear_tap_history(self) -> None:
        """Clear tap history."""
        self._tap_history.clear()

    def press_back(self, num_times: int = 1, delay_between: float = 0.5) -> bool:
        """Press back button.

        Args:
            num_times: Number of times to press back
            delay_between: Delay between presses

        Returns:
            True if successful
        """
        try:
            for i in range(num_times):
                self.device.keyevent("4")  # Back key code
                if i < num_times - 1:
                    time.sleep(delay_between)

            self.logger.info(f"Pressed back {num_times} time(s)")
            return True

        except Exception as e:
            self.logger.error(f"Back press failed: {e}")
            return False

    def press_home(self) -> bool:
        """Press home button.

        Returns:
            True if successful
        """
        try:
            self.device.keyevent("3")  # Home key code
            self.logger.info("Pressed home")
            return True

        except Exception as e:
            self.logger.error(f"Home press failed: {e}")
            return False

    def double_tap(
        self, target_text: str, delay_between: float = 0.1
    ) -> bool:
        """Double tap element.

        Args:
            target_text: Text to double tap
            delay_between: Delay between taps

        Returns:
            True if successful
        """
        try:
            # First tap
            if not self.find_and_tap(
                target_text, post_tap_delay=delay_between
            ):
                return False

            # Get location again
            if not self.ocr_finder:
                return False

            ocr_result = self.ocr_finder.find_text(target_text)
            if not ocr_result:
                return False

            # Second tap
            x, y = self._calculate_tap_point(ocr_result)
            self.device.tap(str(x), str(y))

            self.logger.info(f"✅ Double tapped: '{target_text}'")
            return True

        except Exception as e:
            self.logger.error(f"Double tap failed: {e}")
            return False
