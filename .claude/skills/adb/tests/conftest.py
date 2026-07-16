"""Pytest fixtures for ADB OCR automation tests.

Provides reusable mocks and test data for OCR, state verification, and navigation tests.

Author: MoAI-ADK
Version: 1.0.0
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Generator

import cv2
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper
from adb_auto_player.ocr.tesseract_backend import TesseractBackend
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.ocr import OCRResult
from adb_auto_player.models.geometry import Box, Point


# ============================================================================
# DEVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_device() -> Mock:
    """Create mock ADB device with standard behavior.

    Returns:
        Mock AdbDeviceWrapper with screenshot, tap, swipe, keyevent methods
    """
    device = Mock(spec=AdbDeviceWrapper)

    # Mock screenshot returns PNG bytes
    device.screenshot.return_value = b"\x89PNG\r\n\x1a\n"

    # Mock tap/swipe/keyevent with no-op
    device.tap.return_value = None
    device.swipe.return_value = None
    device.keyevent.return_value = None

    return device


@pytest.fixture
def mock_device_with_screenshot(sample_screenshot_bytes: bytes) -> Mock:
    """Create mock device that returns valid screenshot.

    Args:
        sample_screenshot_bytes: Pre-generated screenshot bytes

    Returns:
        Mock device with realistic screenshot
    """
    device = Mock(spec=AdbDeviceWrapper)
    device.screenshot.return_value = sample_screenshot_bytes
    device.tap.return_value = None
    device.swipe.return_value = None
    device.keyevent.return_value = None

    return device


# ============================================================================
# IMAGE FIXTURES
# ============================================================================

@pytest.fixture
def sample_image() -> np.ndarray:
    """Create sample RGB image with text.

    Returns:
        Numpy array (300x400x3) with drawn text
    """
    img = np.ones((300, 400, 3), dtype=np.uint8) * 255

    # Add text elements
    cv2.putText(
        img,
        "OK",
        (50, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        img,
        "Cancel",
        (200, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        img,
        "Settings",
        (50, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 0),
        2,
    )

    # Add dialog frame
    cv2.rectangle(img, (30, 180), (370, 280), (0, 0, 0), 2)
    cv2.putText(
        img,
        "Confirm Action?",
        (50, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        1,
    )

    return img


@pytest.fixture
def sample_screenshot_bytes(sample_image: np.ndarray) -> bytes:
    """Convert sample image to PNG bytes.

    Args:
        sample_image: RGB numpy array

    Returns:
        PNG encoded bytes
    """
    # Convert RGB to BGR for OpenCV
    bgr_image = cv2.cvtColor(sample_image, cv2.COLOR_RGB2BGR)
    success, encoded = cv2.imencode(".png", bgr_image)
    if not success:
        raise RuntimeError("Failed to encode test image")
    return encoded.tobytes()


@pytest.fixture
def sample_image_with_dialog() -> np.ndarray:
    """Create image with visible dialog.

    Returns:
        Image with prominent dialog elements
    """
    img = np.ones((600, 400, 3), dtype=np.uint8) * 255

    # Background
    img[100:500, :] = 230

    # Dialog box
    cv2.rectangle(img, (50, 200), (350, 400), (0, 0, 0), 3)
    cv2.rectangle(img, (52, 202), (348, 398), (255, 255, 255), -1)

    # Dialog text
    cv2.putText(
        img,
        "Dialog Title",
        (70, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 0),
        2,
    )

    # Buttons
    cv2.rectangle(img, (70, 330), (170, 370), (100, 100, 100), -1)
    cv2.putText(img, "OK", (100, 357), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.rectangle(img, (230, 330), (330, 370), (100, 100, 100), -1)
    cv2.putText(img, "Cancel", (240, 357), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return img


@pytest.fixture
def blank_image() -> np.ndarray:
    """Create blank white image with no features.

    Returns:
        Plain white image
    """
    return np.ones((300, 400, 3), dtype=np.uint8) * 255


# ============================================================================
# OCR MOCKS
# ============================================================================

@pytest.fixture
def mock_ocr_backend() -> Mock:
    """Create mock OCR backend with predefined results.

    Returns:
        Mock TesseractBackend with detect_text method
    """
    backend = Mock(spec=TesseractBackend)

    def detect_text_side_effect(
        image: np.ndarray,
        min_confidence: ConfidenceValue = ConfidenceValue(0.6)
    ) -> list[OCRResult]:
        """Simulate OCR detection."""
        # Return predefined results based on image content
        results = [
            OCRResult(
                text="OK",
                confidence=ConfidenceValue(0.95),
                box=Box(
                    start_point=Point(x=50, y=30),
                    width=40,
                    height=30,
                ),
            ),
            OCRResult(
                text="Cancel",
                confidence=ConfidenceValue(0.92),
                box=Box(
                    start_point=Point(x=200, y=30),
                    width=80,
                    height=30,
                ),
            ),
            OCRResult(
                text="Settings",
                confidence=ConfidenceValue(0.88),
                box=Box(
                    start_point=Point(x=50, y=130),
                    width=100,
                    height=30,
                ),
            ),
        ]
        return results

    backend.detect_text.side_effect = detect_text_side_effect
    backend.detect_text_blocks.return_value = []

    return backend


@pytest.fixture
def sample_ocr_result() -> OCRResult:
    """Create sample OCR result.

    Returns:
        OCRResult with realistic data
    """
    return OCRResult(
        text="Sample Text",
        confidence=ConfidenceValue(0.85),
        box=Box(
            start_point=Point(x=100, y=100),
            width=120,
            height=40,
        ),
    )


@pytest.fixture
def multiple_ocr_results() -> list[OCRResult]:
    """Create multiple OCR results for testing.

    Returns:
        List of OCRResult objects
    """
    return [
        OCRResult(
            text="Button1",
            confidence=ConfidenceValue(0.95),
            box=Box(start_point=Point(x=50, y=50), width=80, height=30),
        ),
        OCRResult(
            text="Button2",
            confidence=ConfidenceValue(0.90),
            box=Box(start_point=Point(x=150, y=50), width=80, height=30),
        ),
        OCRResult(
            text="Label",
            confidence=ConfidenceValue(0.75),
            box=Box(start_point=Point(x=50, y=100), width=60, height=25),
        ),
    ]


# ============================================================================
# INTEGRATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_ocr_finder(mock_device: Mock, mock_ocr_backend: Mock) -> Mock:
    """Create mock OCRTextFinder for integration tests.

    Args:
        mock_device: Mock ADB device
        mock_ocr_backend: Mock OCR backend

    Returns:
        Mock OCRTextFinder with find_text, wait_for_text methods
    """
    finder = MagicMock()

    # Mock find_text to return result if text matches
    def find_text_side_effect(target_text: str):
        ocr_results = mock_ocr_backend.detect_text(np.zeros((300, 400, 3), dtype=np.uint8))
        for result in ocr_results:
            if target_text.lower() in result.text.lower():
                return result
        return None

    finder.find_text.side_effect = find_text_side_effect
    finder.wait_for_text.return_value = True
    finder.find_all_text.return_value = mock_ocr_backend.detect_text(
        np.zeros((300, 400, 3), dtype=np.uint8)
    )

    return finder


@pytest.fixture
def mock_state_verifier(mock_device: Mock) -> Mock:
    """Create mock StateVerifier for integration tests.

    Args:
        mock_device: Mock ADB device

    Returns:
        Mock StateVerifier with verify methods
    """
    verifier = MagicMock()

    verifier.verify_state.return_value = True
    verifier.verify_text_present.return_value = True
    verifier.verify_text_absent.return_value = False
    verifier.detect_dialog.return_value = True
    verifier.wait_for_state.return_value = True
    verifier.detect_state_change.return_value = True
    verifier.get_state_history.return_value = []

    return verifier


# ============================================================================
# PARAMETRIZED TEST DATA
# ============================================================================

@pytest.fixture(params=[
    ("OK", True),
    ("Cancel", True),
    ("Settings", True),
    ("NonExistent", False),
    ("Button", False),
])
def text_search_case(request):
    """Parametrized fixture for text search test cases.

    Returns:
        Tuple of (search_text, should_find)
    """
    return request.param


@pytest.fixture(params=[
    (0.5, True),
    (0.8, True),
    (0.95, True),
    (0.99, False),
])
def confidence_threshold_case(request):
    """Parametrized fixture for confidence threshold tests.

    Returns:
        Tuple of (threshold, should_pass)
    """
    return request.param


@pytest.fixture(params=[
    (1, 0.5),  # 1 retry, 0.5s delay
    (3, 0.3),  # 3 retries, 0.3s delay
    (5, 0.1),  # 5 retries, 0.1s delay
])
def retry_config_case(request):
    """Parametrized fixture for retry configuration tests.

    Returns:
        Tuple of (max_retries, retry_delay)
    """
    return request.param


# ============================================================================
# SESSION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get test data directory path.

    Returns:
        Path to test_data directory
    """
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="function", autouse=True)
def reset_mocks():
    """Reset all mocks after each test.

    Ensures clean state between tests.
    """
    yield
    # Cleanup happens automatically with function-scoped fixtures
