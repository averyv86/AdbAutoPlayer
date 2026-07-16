"""OCR Text Detection Framework for ADB Automation.

Provides text finding and location capabilities for device UI automation.
Integrates Tesseract OCR with ADB device control for text-based element detection.

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
from typing import Optional, Callable, Any
import io

import cv2
import numpy as np
from adb_auto_player.ocr.tesseract_backend import TesseractBackend
from adb_auto_player.ocr.tesseract_config import TesseractConfig
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult
from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper

logger = logging.getLogger(__name__)


class OCRTextFinder:
    """Finds and locates text on device screen using OCR."""

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ocr_config: Optional[TesseractConfig] = None,
        min_confidence: ConfidenceValue = ConfidenceValue(0.6),
    ):
        """Initialize OCR Text Finder.

        Args:
            device: AdbDeviceWrapper instance for screen control
            ocr_config: Optional TesseractConfig override
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.device = device
        self.ocr_config = ocr_config or TesseractConfig()
        self.min_confidence = min_confidence
        self.backend = TesseractBackend(config=self.ocr_config)
        self.logger = logger

    def _screenshot_to_image(self) -> np.ndarray:
        """Get screenshot from device and convert to numpy array.

        Returns:
            RGB image as numpy array

        Raises:
            RuntimeError: If screenshot fails or is invalid
        """
        try:
            screenshot_data = self.device.screenshot()
            if isinstance(screenshot_data, str):
                screenshot_data = screenshot_data.encode()

            # Convert to numpy array
            nparr = np.frombuffer(screenshot_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise RuntimeError("Failed to decode screenshot")

            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image

        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            raise RuntimeError(f"Screenshot capture failed: {e}")

    def find_text(self, target_text: str) -> Optional[OCRResult]:
        """Find target text on screen.

        Args:
            target_text: Text to search for (case-sensitive)

        Returns:
            OCRResult with location if found, None otherwise
        """
        try:
            image = self._screenshot_to_image()
            results = self.backend.detect_text(
                image, min_confidence=self.min_confidence
            )

            # Search for exact match or substring
            for result in results:
                if target_text.lower() in result.text.lower():
                    self.logger.info(
                        f"✅ Found text: '{target_text}' at {result.box}"
                    )
                    return result

            self.logger.debug(f"❌ Text not found: '{target_text}'")
            return None

        except Exception as e:
            self.logger.error(f"find_text failed: {e}")
            return None

    def find_text_region(
        self, target_text: str, region: Optional[tuple[int, int, int, int]] = None
    ) -> Optional[OCRResult]:
        """Find text within a specific region.

        Args:
            target_text: Text to search for
            region: Optional (x, y, width, height) region to search in

        Returns:
            OCRResult if found, None otherwise
        """
        try:
            image = self._screenshot_to_image()

            # Crop image if region specified
            if region:
                x, y, width, height = region
                image = image[y : y + height, x : x + width]

            results = self.backend.detect_text(
                image, min_confidence=self.min_confidence
            )

            for result in results:
                if target_text.lower() in result.text.lower():
                    self.logger.info(f"✅ Found text in region: '{target_text}'")
                    return result

            return None

        except Exception as e:
            self.logger.error(f"find_text_region failed: {e}")
            return None

    def wait_for_text(
        self,
        target_text: str,
        timeout_seconds: int = 10,
        check_interval: float = 0.5,
    ) -> bool:
        """Wait for text to appear on screen.

        Args:
            target_text: Text to wait for
            timeout_seconds: Maximum wait time in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if text appeared within timeout, False otherwise
        """
        start_time = time.time()
        elapsed = 0

        while elapsed < timeout_seconds:
            try:
                result = self.find_text(target_text)
                if result:
                    self.logger.info(
                        f"✅ Text appeared after {elapsed:.1f}s: '{target_text}'"
                    )
                    return True

                time.sleep(check_interval)
                elapsed = time.time() - start_time

            except Exception as e:
                self.logger.debug(f"Error checking text: {e}")
                time.sleep(check_interval)
                elapsed = time.time() - start_time

        self.logger.warning(
            f"⏱️ Timeout waiting for text '{target_text}' ({timeout_seconds}s)"
        )
        return False

    def find_all_text(self) -> list[OCRResult]:
        """Find all text on current screen.

        Returns:
            List of all detected text blocks with locations
        """
        try:
            image = self._screenshot_to_image()
            results = self.backend.detect_text(
                image, min_confidence=self.min_confidence
            )
            self.logger.info(f"Found {len(results)} text blocks on screen")
            return results

        except Exception as e:
            self.logger.error(f"find_all_text failed: {e}")
            return []

    def find_text_blocks(self) -> list[OCRResult]:
        """Find text blocks (grouped words) on screen.

        Returns:
            List of text blocks with bounding boxes
        """
        try:
            image = self._screenshot_to_image()
            results = self.backend.detect_text_blocks(
                image, min_confidence=self.min_confidence
            )
            self.logger.info(f"Found {len(results)} text blocks")
            return results

        except Exception as e:
            self.logger.error(f"find_text_blocks failed: {e}")
            return []

    def find_text_with_retry(
        self,
        target_text: str,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Optional[OCRResult]:
        """Find text with retry logic on failure.

        Args:
            target_text: Text to search for
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            OCRResult if found, None otherwise
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                result = self.find_text(target_text)
                if result:
                    return result

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                )

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        self.logger.error(
            f"Failed to find text after {max_retries} attempts: {last_error}"
        )
        return None
