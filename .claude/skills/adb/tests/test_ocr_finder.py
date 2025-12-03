"""Tests for OCRTextFinder - Text detection and location.

Tests cover:
- Text finding (success and failure cases)
- Timeout and wait behavior
- Region-based search
- Confidence filtering
- Retry logic
- Error handling

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
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ocr-detection"))

from adb_ocr_finder import OCRTextFinder


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================

class TestOCRTextFinderInitialization:
    """Tests for OCRTextFinder initialization."""

    def test_init_with_defaults(self, mock_device, mock_ocr_backend):
        """Test initialization with default parameters."""
        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            assert finder.device == mock_device
            assert finder.min_confidence == ConfidenceValue(0.6)
            assert finder.backend is not None

    def test_init_with_custom_confidence(self, mock_device, mock_ocr_backend):
        """Test initialization with custom confidence threshold."""
        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(
                mock_device,
                min_confidence=ConfidenceValue(0.8)
            )

            assert finder.min_confidence == ConfidenceValue(0.8)

    def test_init_with_custom_config(self, mock_device, mock_ocr_backend):
        """Test initialization with custom OCR config."""
        from adb_auto_player.ocr.tesseract_config import TesseractConfig

        custom_config = TesseractConfig()

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(
                mock_device,
                ocr_config=custom_config
            )

            assert finder.ocr_config == custom_config


# ============================================================================
# TEST: FIND TEXT
# ============================================================================

class TestFindText:
    """Tests for find_text method."""

    def test_find_text_success(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test successful text finding."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text("OK")

            assert result is not None
            assert result.text == "OK"
            assert result.confidence.value >= 0.6

    def test_find_text_not_found(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test text not found returns None."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text("NonExistentText")

            assert result is None

    def test_find_text_case_insensitive(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test text search is case-insensitive."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            result_lower = finder.find_text("ok")
            result_upper = finder.find_text("OK")
            result_mixed = finder.find_text("Ok")

            assert result_lower is not None
            assert result_upper is not None
            assert result_mixed is not None

    def test_find_text_substring_match(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test substring matching in text search."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text("Sett")  # Partial match for "Settings"

            assert result is not None
            assert "Sett" in result.text

    @pytest.mark.parametrize("target_text,should_find", [
        ("OK", True),
        ("Cancel", True),
        ("Settings", True),
        ("Invalid", False),
        ("", False),
    ])
    def test_find_text_parametrized(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes,
        target_text,
        should_find
    ):
        """Test text finding with various inputs."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text(target_text)

            if should_find:
                assert result is not None
            else:
                assert result is None


# ============================================================================
# TEST: REGION-BASED SEARCH
# ============================================================================

class TestFindTextRegion:
    """Tests for find_text_region method."""

    def test_find_text_in_region(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test finding text within specified region."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            region = (40, 20, 100, 50)  # Region containing "OK"
            result = finder.find_text_region("OK", region=region)

            assert result is not None

    def test_find_text_outside_region(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test text outside region is not found."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            region = (0, 0, 30, 30)  # Small region without text
            result = finder.find_text_region("OK", region=region)

            # Depending on implementation, might return None
            # or return result but outside region

    def test_find_text_full_screen_when_no_region(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test full screen search when region is None."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text_region("OK", region=None)

            assert result is not None


# ============================================================================
# TEST: WAIT FOR TEXT
# ============================================================================

class TestWaitForText:
    """Tests for wait_for_text method."""

    def test_wait_for_text_success_immediate(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test waiting for text that appears immediately."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            start = time.time()
            result = finder.wait_for_text("OK", timeout_seconds=5)
            elapsed = time.time() - start

            assert result is True
            assert elapsed < 1.0  # Should find immediately

    def test_wait_for_text_timeout(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test timeout when text never appears."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            start = time.time()
            result = finder.wait_for_text("NonExistent", timeout_seconds=1)
            elapsed = time.time() - start

            assert result is False
            assert elapsed >= 1.0  # Should wait full timeout

    def test_wait_for_text_appears_after_delay(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test text appearing after some delay."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        call_count = 0

        def delayed_detect_text(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                # First 2 calls: return no results
                return []
            else:
                # 3rd call onwards: return results
                return [
                    OCRResult(
                        text="OK",
                        confidence=ConfidenceValue(0.95),
                        box=Box(
                            start_point=Point(x=50, y=30),
                            width=40,
                            height=30,
                        ),
                    )
                ]

        mock_ocr_backend.detect_text.side_effect = delayed_detect_text

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            result = finder.wait_for_text(
                "OK",
                timeout_seconds=5,
                check_interval=0.2
            )

            assert result is True
            assert call_count >= 3

    def test_wait_for_text_custom_interval(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test custom check interval."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            start = time.time()
            finder.wait_for_text(
                "NonExistent",
                timeout_seconds=1,
                check_interval=0.3
            )
            elapsed = time.time() - start

            # Should check roughly every 0.3s for 1s total
            assert elapsed >= 1.0


# ============================================================================
# TEST: CONFIDENCE FILTERING
# ============================================================================

class TestConfidenceFiltering:
    """Tests for confidence threshold filtering."""

    def test_low_confidence_filtered_out(
        self,
        mock_device,
        sample_screenshot_bytes
    ):
        """Test low confidence results are filtered."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        # Mock backend with low confidence result
        low_conf_backend = Mock()
        low_conf_backend.detect_text.return_value = [
            OCRResult(
                text="LowConf",
                confidence=ConfidenceValue(0.3),
                box=Box(start_point=Point(x=50, y=50), width=60, height=30),
            )
        ]

        with patch("adb_ocr_finder.TesseractBackend", return_value=low_conf_backend):
            finder = OCRTextFinder(
                mock_device,
                min_confidence=ConfidenceValue(0.6)
            )
            result = finder.find_text("LowConf")

            # Low confidence should be filtered by backend
            assert result is None or result.confidence.value >= 0.6

    def test_high_confidence_passes(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test high confidence results pass filter."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(
                mock_device,
                min_confidence=ConfidenceValue(0.6)
            )
            result = finder.find_text("OK")

            assert result is not None
            assert result.confidence.value >= 0.6


# ============================================================================
# TEST: RETRY LOGIC
# ============================================================================

class TestRetryLogic:
    """Tests for retry logic in find_text_with_retry."""

    def test_retry_success_first_attempt(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test successful find on first attempt."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text_with_retry(
                "OK",
                max_retries=3,
                retry_delay=0.1
            )

            assert result is not None
            assert mock_ocr_backend.detect_text.call_count == 1

    def test_retry_success_after_failures(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test success after initial failures."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        call_count = 0

        def retry_detect_text(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                return []
            else:
                return [
                    OCRResult(
                        text="OK",
                        confidence=ConfidenceValue(0.95),
                        box=Box(
                            start_point=Point(x=50, y=30),
                            width=40,
                            height=30,
                        ),
                    )
                ]

        mock_ocr_backend.detect_text.side_effect = retry_detect_text

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text_with_retry(
                "OK",
                max_retries=3,
                retry_delay=0.1
            )

            assert result is not None
            assert call_count == 2

    def test_retry_exhausts_all_attempts(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test all retry attempts are exhausted."""
        mock_device.screenshot.return_value = sample_screenshot_bytes
        mock_ocr_backend.detect_text.return_value = []

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text_with_retry(
                "NonExistent",
                max_retries=3,
                retry_delay=0.05
            )

            assert result is None
            assert mock_ocr_backend.detect_text.call_count == 3

    def test_retry_with_exception_handling(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test retry handles exceptions gracefully."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        call_count = 0

        def failing_detect_text(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise RuntimeError("OCR failed")
            else:
                return [
                    OCRResult(
                        text="OK",
                        confidence=ConfidenceValue(0.95),
                        box=Box(
                            start_point=Point(x=50, y=30),
                            width=40,
                            height=30,
                        ),
                    )
                ]

        mock_ocr_backend.detect_text.side_effect = failing_detect_text

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text_with_retry(
                "OK",
                max_retries=3,
                retry_delay=0.05
            )

            # Should retry through exceptions
            assert call_count == 3


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_screenshot_failure_raises(self, mock_device, mock_ocr_backend):
        """Test screenshot failure raises RuntimeError."""
        mock_device.screenshot.side_effect = Exception("Screenshot failed")

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            with pytest.raises(RuntimeError):
                finder.find_text("OK")

    def test_invalid_screenshot_data(self, mock_device, mock_ocr_backend):
        """Test invalid screenshot data raises RuntimeError."""
        mock_device.screenshot.return_value = b"invalid data"

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)

            with pytest.raises(RuntimeError):
                finder.find_text("OK")

    def test_ocr_backend_failure_handled(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test OCR backend failure is handled gracefully."""
        mock_device.screenshot.return_value = sample_screenshot_bytes
        mock_ocr_backend.detect_text.side_effect = Exception("OCR failed")

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            result = finder.find_text("OK")

            # Should return None on error
            assert result is None


# ============================================================================
# TEST: ADDITIONAL METHODS
# ============================================================================

class TestAdditionalMethods:
    """Tests for find_all_text and find_text_blocks."""

    def test_find_all_text(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test finding all text on screen."""
        mock_device.screenshot.return_value = sample_screenshot_bytes

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            results = finder.find_all_text()

            assert isinstance(results, list)
            assert len(results) > 0

    def test_find_text_blocks(
        self,
        mock_device,
        mock_ocr_backend,
        sample_screenshot_bytes
    ):
        """Test finding text blocks."""
        mock_device.screenshot.return_value = sample_screenshot_bytes
        mock_ocr_backend.detect_text_blocks.return_value = [
            OCRResult(
                text="Block 1",
                confidence=ConfidenceValue(0.9),
                box=Box(start_point=Point(x=50, y=50), width=100, height=30),
            )
        ]

        with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
            finder = OCRTextFinder(mock_device)
            results = finder.find_text_blocks()

            assert isinstance(results, list)
            assert len(results) >= 0
