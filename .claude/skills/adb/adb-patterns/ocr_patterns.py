"""Reusable OCR Patterns for ADB Automation.

Provides composable patterns extracted from Phase 1 implementations:
- OCRTextFinderPattern: Generic text location with confidence thresholding
- StateVerifierPattern: State validation with condition callbacks
- MenuNavigatorPattern: Sequential menu navigation
- DialogHandlerPattern: Generic dialog detection and response
- RetryableOperationPattern: Retry logic with exponential backoff

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
from typing import Optional, Callable, List, Any, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class Box:
    """Bounding box for OCR results."""
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Get center point of box."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class OCRTextFinderPattern:
    """Generic text location pattern with confidence thresholding.

    Provides reusable OCR text finding with flexible confidence levels
    and timeout-based waiting.

    Example:
        >>> finder = OCRTextFinderPattern(device, ocr_backend)
        >>> result = finder.find("Settings", min_confidence=0.7)
        >>> if result:
        ...     print(f"Found at {result.box.center}")

        >>> # Wait for text to appear
        >>> if finder.wait_for("Loading...", timeout=10):
        ...     print("Loading screen appeared")
    """

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ocr_backend: Any,
        default_confidence: ConfidenceValue = ConfidenceValue(0.6),
    ):
        """Initialize OCR Text Finder Pattern.

        Args:
            device: AdbDeviceWrapper instance for screen capture
            ocr_backend: OCR backend (TesseractBackend or compatible)
            default_confidence: Default minimum confidence threshold (0.0-1.0)
        """
        self.device = device
        self.ocr_backend = ocr_backend
        self.default_confidence = default_confidence
        self.logger = logger

    def _capture_screen(self) -> np.ndarray:
        """Capture screenshot and convert to numpy array.

        Returns:
            RGB image as numpy array

        Raises:
            RuntimeError: If screenshot fails
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
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            raise RuntimeError(f"Screenshot capture failed: {e}")

    def find(
        self,
        target: str,
        min_confidence: Optional[float] = None,
        case_sensitive: bool = False,
    ) -> Optional[OCRResult]:
        """Find target text on screen.

        Args:
            target: Text to search for
            min_confidence: Optional confidence override (0.0-1.0)
            case_sensitive: Whether to match case exactly

        Returns:
            OCRResult with location if found, None otherwise

        Example:
            >>> result = finder.find("OK", min_confidence=0.8)
            >>> if result:
            ...     x, y = result.box.center
            ...     device.tap(str(x), str(y))
        """
        try:
            confidence = (
                ConfidenceValue(min_confidence)
                if min_confidence is not None
                else self.default_confidence
            )

            image = self._capture_screen()
            results = self.ocr_backend.detect_text(
                image, min_confidence=confidence
            )

            # Search for match
            for result in results:
                result_text = result.text if case_sensitive else result.text.lower()
                search_text = target if case_sensitive else target.lower()

                if search_text in result_text:
                    self.logger.info(
                        f"✅ Found text: '{target}' "
                        f"(confidence: {result.confidence.value:.2f})"
                    )
                    return result

            self.logger.debug(f"❌ Text not found: '{target}'")
            return None

        except Exception as e:
            self.logger.error(f"Text find failed: {e}")
            return None

    def wait_for(
        self,
        target: str,
        timeout: int = 10,
        check_interval: float = 0.5,
        min_confidence: Optional[float] = None,
    ) -> bool:
        """Wait for text to appear on screen.

        Args:
            target: Text to wait for
            timeout: Maximum wait time in seconds
            check_interval: Time between checks in seconds
            min_confidence: Optional confidence override

        Returns:
            True if text appeared within timeout, False otherwise

        Example:
            >>> if finder.wait_for("Success", timeout=5):
            ...     print("Operation completed")
        """
        start_time = time.time()
        elapsed = 0

        while elapsed < timeout:
            result = self.find(target, min_confidence=min_confidence)
            if result:
                self.logger.info(
                    f"✅ Text appeared after {elapsed:.1f}s: '{target}'"
                )
                return True

            time.sleep(check_interval)
            elapsed = time.time() - start_time

        self.logger.warning(
            f"⏱️ Timeout waiting for text '{target}' ({timeout}s)"
        )
        return False

    def find_all(
        self, min_confidence: Optional[float] = None
    ) -> List[OCRResult]:
        """Find all text on current screen.

        Args:
            min_confidence: Optional confidence override

        Returns:
            List of all detected text blocks

        Example:
            >>> all_text = finder.find_all(min_confidence=0.7)
            >>> for result in all_text:
            ...     print(f"{result.text}: {result.box.center}")
        """
        try:
            confidence = (
                ConfidenceValue(min_confidence)
                if min_confidence is not None
                else self.default_confidence
            )

            image = self._capture_screen()
            results = self.ocr_backend.detect_text(
                image, min_confidence=confidence
            )

            self.logger.info(f"Found {len(results)} text blocks on screen")
            return results

        except Exception as e:
            self.logger.error(f"find_all failed: {e}")
            return []


class StateVerifierPattern:
    """State validation pattern with condition callbacks.

    Provides flexible state verification using custom condition functions.
    Supports waiting for state changes with timeout.

    Example:
        >>> verifier = StateVerifierPattern(device)
        >>>
        >>> # Check if loading spinner is gone
        >>> def loading_complete(image):
        ...     # Custom logic to detect loading state
        ...     return not has_loading_spinner(image)
        >>>
        >>> if verifier.verify(loading_complete):
        ...     print("Loading complete")
        >>>
        >>> # Wait for state change
        >>> verifier.wait_for_state(loading_complete, timeout=10)
    """

    def __init__(self, device: AdbDeviceWrapper):
        """Initialize State Verifier Pattern.

        Args:
            device: AdbDeviceWrapper instance
        """
        self.device = device
        self.logger = logger
        self._last_screenshot: Optional[np.ndarray] = None

    def _capture_screen(self) -> np.ndarray:
        """Capture screenshot and convert to numpy array.

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

    def verify(self, condition: Callable[[np.ndarray], bool]) -> bool:
        """Verify state using custom condition function.

        Args:
            condition: Function that takes screenshot and returns True if state matches

        Returns:
            True if condition is met, False otherwise

        Example:
            >>> def is_home_screen(image):
            ...     # Custom home screen detection logic
            ...     return detect_home_icon(image)
            >>>
            >>> if verifier.verify(is_home_screen):
            ...     print("Currently on home screen")
        """
        try:
            image = self._capture_screen()
            result = condition(image)
            return result

        except Exception as e:
            self.logger.error(f"State verification failed: {e}")
            return False

    def wait_for_state(
        self,
        condition: Callable[[np.ndarray], bool],
        timeout: int = 10,
        check_interval: float = 0.5,
    ) -> bool:
        """Wait for state condition to be met.

        Args:
            condition: Function that returns True when state is reached
            timeout: Maximum wait time in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if condition met within timeout, False otherwise

        Example:
            >>> def dialog_closed(image):
            ...     return not has_dialog(image)
            >>>
            >>> # Wait up to 5 seconds for dialog to close
            >>> if verifier.wait_for_state(dialog_closed, timeout=5):
            ...     print("Dialog closed successfully")
        """
        start_time = time.time()
        elapsed = 0
        check_count = 0

        while elapsed < timeout:
            if self.verify(condition):
                check_count += 1
                self.logger.info(
                    f"✅ State condition met after {elapsed:.1f}s "
                    f"({check_count} checks)"
                )
                return True

            time.sleep(check_interval)
            elapsed = time.time() - start_time
            check_count += 1

        self.logger.warning(
            f"⏱️ State condition timeout after {timeout}s "
            f"({check_count} checks)"
        )
        return False

    def detect_state_change(
        self,
        timeout: int = 5,
        check_interval: float = 0.25,
        threshold_mse: float = 100.0,
    ) -> bool:
        """Detect if screen state changed since last screenshot.

        Args:
            timeout: Maximum wait for change
            check_interval: Time between comparisons
            threshold_mse: MSE threshold for detecting change

        Returns:
            True if change detected, False if no change within timeout

        Example:
            >>> # Capture initial state
            >>> verifier.verify(lambda img: True)
            >>>
            >>> # Tap something
            >>> device.tap("100", "200")
            >>>
            >>> # Verify screen changed
            >>> if verifier.detect_state_change(timeout=3):
            ...     print("UI updated after tap")
        """
        try:
            if self._last_screenshot is None:
                # First screenshot, take it
                self._capture_screen()
                return True

            reference = self._last_screenshot
            start_time = time.time()
            elapsed = 0

            while elapsed < timeout:
                current = self._capture_screen()

                # Calculate difference using mean squared error
                diff = cv2.absdiff(reference, current)
                mse = np.mean(diff ** 2)

                # Check if change detected
                if mse > threshold_mse:
                    self.logger.info(
                        f"✅ State change detected (MSE: {mse:.1f})"
                    )
                    return True

                time.sleep(check_interval)
                elapsed = time.time() - start_time

            self.logger.debug(
                f"No state change detected within {timeout}s"
            )
            return False

        except Exception as e:
            self.logger.error(f"State change detection failed: {e}")
            return False


class MenuNavigatorPattern:
    """Sequential menu navigation pattern.

    Navigates through menu items in order, with automatic retry and
    state verification support.

    Example:
        >>> navigator = MenuNavigatorPattern(device, ocr_finder)
        >>>
        >>> # Navigate: Settings > Display > Brightness
        >>> menu_path = ["Settings", "Display", "Brightness"]
        >>> if navigator.navigate(menu_path, timeout_per_item=3):
        ...     print("Reached Brightness settings")
    """

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ocr_finder: OCRTextFinderPattern,
        state_verifier: Optional[StateVerifierPattern] = None,
    ):
        """Initialize Menu Navigator Pattern.

        Args:
            device: AdbDeviceWrapper instance
            ocr_finder: OCRTextFinderPattern for finding menu items
            state_verifier: Optional StateVerifierPattern for verification
        """
        self.device = device
        self.ocr_finder = ocr_finder
        self.state_verifier = state_verifier
        self.logger = logger

    def navigate(
        self,
        menu_path: List[str],
        timeout_per_item: int = 3,
        post_tap_delay: float = 0.5,
        verify_state_change: bool = True,
    ) -> bool:
        """Navigate through menu items in sequence.

        Args:
            menu_path: List of menu item texts in order
            timeout_per_item: Timeout for finding each item
            post_tap_delay: Delay after each tap
            verify_state_change: Verify state changed after each tap

        Returns:
            True if all items tapped successfully, False otherwise

        Example:
            >>> # Simple navigation
            >>> navigator.navigate(["File", "Open", "Recent"])

            >>> # With custom timeouts
            >>> navigator.navigate(
            ...     ["Settings", "Advanced"],
            ...     timeout_per_item=5,
            ...     post_tap_delay=1.0
            ... )
        """
        try:
            for i, item in enumerate(menu_path):
                self.logger.info(
                    f"Menu step {i + 1}/{len(menu_path)}: {item}"
                )

                # Find menu item
                result = self.ocr_finder.find(item)
                if not result:
                    self.logger.error(
                        f"Failed to find menu item: {item}"
                    )
                    return False

                # Tap menu item
                x, y = result.box.center
                self.device.tap(str(x), str(y))

                # Wait for UI to respond
                time.sleep(post_tap_delay)

                # Verify state changed if requested
                if verify_state_change and self.state_verifier:
                    if not self.state_verifier.detect_state_change(
                        timeout=2
                    ):
                        self.logger.warning(
                            f"No state change detected after tapping {item}"
                        )

            self.logger.info("✅ Menu navigation complete")
            return True

        except Exception as e:
            self.logger.error(f"Menu navigation failed: {e}")
            return False

    def navigate_with_scroll(
        self,
        menu_path: List[str],
        max_scrolls_per_item: int = 3,
        scroll_direction: str = "down",
    ) -> bool:
        """Navigate menu with scrolling support.

        Args:
            menu_path: List of menu item texts
            max_scrolls_per_item: Max scrolls before giving up on item
            scroll_direction: 'up' or 'down'

        Returns:
            True if navigation successful

        Example:
            >>> # Navigate with scrolling if item not visible
            >>> navigator.navigate_with_scroll(
            ...     ["Settings", "About Phone"],
            ...     max_scrolls_per_item=5
            ... )
        """
        try:
            for i, item in enumerate(menu_path):
                self.logger.info(
                    f"Menu step {i + 1}/{len(menu_path)}: {item}"
                )

                found = False
                for scroll_attempt in range(max_scrolls_per_item + 1):
                    result = self.ocr_finder.find(item)
                    if result:
                        # Tap menu item
                        x, y = result.box.center
                        self.device.tap(str(x), str(y))
                        time.sleep(0.5)
                        found = True
                        break

                    # Try scrolling
                    if scroll_attempt < max_scrolls_per_item:
                        self._scroll(direction=scroll_direction)
                        time.sleep(0.3)

                if not found:
                    self.logger.error(
                        f"Failed to find menu item after scrolling: {item}"
                    )
                    return False

            self.logger.info("✅ Menu navigation with scroll complete")
            return True

        except Exception as e:
            self.logger.error(f"Menu navigation with scroll failed: {e}")
            return False

    def _scroll(
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
            return True

        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return False


class DialogHandlerPattern:
    """Generic dialog detection and response pattern.

    Detects dialogs and handles them by clicking specified buttons.
    Supports verification that dialog was closed after handling.

    Example:
        >>> handler = DialogHandlerPattern(device, ocr_finder, state_verifier)
        >>>
        >>> # Detect and handle dialog
        >>> if handler.detect():
        ...     handler.handle("OK", verify_closed=True)
        >>>
        >>> # Dismiss all dialogs
        >>> handler.dismiss_all(max_dismissals=3)
    """

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ocr_finder: OCRTextFinderPattern,
        state_verifier: StateVerifierPattern,
    ):
        """Initialize Dialog Handler Pattern.

        Args:
            device: AdbDeviceWrapper instance
            ocr_finder: OCRTextFinderPattern for finding buttons
            state_verifier: StateVerifierPattern for verification
        """
        self.device = device
        self.ocr_finder = ocr_finder
        self.state_verifier = state_verifier
        self.logger = logger

    def detect(self) -> bool:
        """Detect if dialog is visible on screen.

        Uses edge detection heuristics to identify dialog presence.

        Returns:
            True if dialog detected, False otherwise

        Example:
            >>> if handler.detect():
            ...     print("Dialog is visible")
            ...     handler.handle("Cancel")
        """
        try:
            # Capture screen
            screenshot_data = self.device.screenshot()
            if isinstance(screenshot_data, str):
                screenshot_data = screenshot_data.encode()

            nparr = np.frombuffer(screenshot_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                return False

            # Convert to grayscale and detect edges
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)

            # Count edges - dialogs typically have more edge pixels
            edge_count = np.count_nonzero(edges)
            image_size = image.shape[0] * image.shape[1]
            edge_density = edge_count / image_size

            # Dialogs typically have 5-15% edge density
            is_dialog = 0.05 < edge_density < 0.15

            if is_dialog:
                self.logger.info(
                    f"Dialog detected (edge density: {edge_density:.3f})"
                )

            return is_dialog

        except Exception as e:
            self.logger.error(f"Dialog detection failed: {e}")
            return False

    def handle(
        self,
        button: str,
        timeout: int = 5,
        verify_closed: bool = True,
    ) -> bool:
        """Handle dialog by clicking specified button.

        Args:
            button: Text of button to click ('OK', 'Cancel', 'Yes', 'No')
            timeout: Timeout for finding button
            verify_closed: Verify dialog closed after click

        Returns:
            True if dialog handled successfully

        Example:
            >>> # Click OK and verify dialog closed
            >>> handler.handle("OK", verify_closed=True)

            >>> # Click Cancel without verification
            >>> handler.handle("Cancel", verify_closed=False)
        """
        try:
            self.logger.info(f"Handling dialog, clicking: {button}")

            # Find button
            result = self.ocr_finder.find(button)
            if not result:
                self.logger.warning(f"Could not find button: {button}")
                return False

            # Tap button
            x, y = result.box.center
            self.device.tap(str(x), str(y))

            # Wait for UI to respond
            time.sleep(0.5)

            # Verify dialog closed
            if verify_closed:
                if self.detect():
                    self.logger.warning("Dialog still visible after click")
                    return False

            self.logger.info("✅ Dialog handled successfully")
            return True

        except Exception as e:
            self.logger.error(f"handle dialog failed: {e}")
            return False

    def dismiss_all(
        self, max_dismissals: int = 5, method: str = "back"
    ) -> int:
        """Dismiss all visible dialogs.

        Args:
            max_dismissals: Maximum number of dialogs to dismiss
            method: 'back' to press back button, 'tap' to tap screen center

        Returns:
            Number of dialogs dismissed

        Example:
            >>> # Dismiss all dialogs using back button
            >>> count = handler.dismiss_all(max_dismissals=3)
            >>> print(f"Dismissed {count} dialog(s)")

            >>> # Dismiss by tapping screen center
            >>> handler.dismiss_all(method="tap")
        """
        dismissed = 0

        for i in range(max_dismissals):
            if not self.detect():
                break

            try:
                if method == "back":
                    self.device.keyevent("4")  # Back key
                else:  # tap
                    # Tap screen center
                    self.device.tap("720", "1560")

                dismissed += 1
                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Failed to dismiss dialog: {e}")
                break

        self.logger.info(f"Dismissed {dismissed} dialog(s)")
        return dismissed


class RetryableOperationPattern(Generic[T]):
    """Retry logic pattern with exponential backoff.

    Provides generic retry functionality with configurable backoff strategy.
    Useful for unreliable operations that may need multiple attempts.

    Example:
        >>> retry = RetryableOperationPattern()
        >>>
        >>> # Retry a function
        >>> def unstable_operation():
        ...     # May fail occasionally
        ...     return fetch_data_from_api()
        >>>
        >>> result = retry.execute(
        ...     unstable_operation,
        ...     max_retries=3,
        ...     backoff=0.5
        ... )

        >>> # Retry with custom error handling
        >>> def should_retry(error):
        ...     return isinstance(error, NetworkError)
        >>>
        >>> retry.execute(
        ...     operation,
        ...     max_retries=5,
        ...     should_retry=should_retry
        ... )
    """

    def __init__(self):
        """Initialize Retryable Operation Pattern."""
        self.logger = logger

    def execute(
        self,
        operation: Callable[[], T],
        max_retries: int = 3,
        backoff: float = 0.5,
        backoff_multiplier: float = 2.0,
        should_retry: Optional[Callable[[Exception], bool]] = None,
    ) -> Optional[T]:
        """Execute operation with retry logic.

        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            backoff: Initial backoff delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            should_retry: Optional function to determine if error is retryable

        Returns:
            Result of operation if successful, None if all retries failed

        Example:
            >>> def fetch_data():
            ...     response = requests.get("https://api.example.com/data")
            ...     return response.json()
            >>>
            >>> retry = RetryableOperationPattern()
            >>> data = retry.execute(
            ...     fetch_data,
            ...     max_retries=3,
            ...     backoff=1.0,
            ...     backoff_multiplier=2.0
            ... )
        """
        last_error = None
        current_backoff = backoff

        for attempt in range(max_retries):
            try:
                result = operation()
                if attempt > 0:
                    self.logger.info(
                        f"✅ Operation succeeded on attempt {attempt + 1}"
                    )
                return result

            except Exception as e:
                last_error = e

                # Check if error is retryable
                if should_retry and not should_retry(e):
                    self.logger.error(
                        f"Non-retryable error: {e}"
                    )
                    return None

                self.logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                )

                # Sleep with exponential backoff before retry
                if attempt < max_retries - 1:
                    self.logger.debug(
                        f"Retrying in {current_backoff:.2f}s..."
                    )
                    time.sleep(current_backoff)
                    current_backoff *= backoff_multiplier

        self.logger.error(
            f"❌ Operation failed after {max_retries} attempts: {last_error}"
        )
        return None

    def execute_until_success(
        self,
        operation: Callable[[], T],
        timeout: int = 30,
        check_interval: float = 1.0,
    ) -> Optional[T]:
        """Execute operation repeatedly until success or timeout.

        Args:
            operation: Function to execute
            timeout: Maximum time to keep trying (seconds)
            check_interval: Time between attempts (seconds)

        Returns:
            Result of operation if successful within timeout, None otherwise

        Example:
            >>> def wait_for_ready():
            ...     if service.is_ready():
            ...         return service.get_status()
            ...     raise NotReadyError()
            >>>
            >>> retry = RetryableOperationPattern()
            >>> status = retry.execute_until_success(
            ...     wait_for_ready,
            ...     timeout=60,
            ...     check_interval=2.0
            ... )
        """
        start_time = time.time()
        elapsed = 0
        attempt = 0

        while elapsed < timeout:
            try:
                result = operation()
                self.logger.info(
                    f"✅ Operation succeeded after {elapsed:.1f}s "
                    f"({attempt + 1} attempts)"
                )
                return result

            except Exception as e:
                attempt += 1
                self.logger.debug(
                    f"Attempt {attempt} failed: {e}"
                )

                time.sleep(check_interval)
                elapsed = time.time() - start_time

        self.logger.error(
            f"❌ Operation failed after timeout ({timeout}s, "
            f"{attempt} attempts)"
        )
        return None
