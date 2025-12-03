#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pytesseract>=0.3.10",
#     "pillow>=10.0.0",
#     "numpy>=1.24.0",
# ]
# ///

"""
ADB OCR Extract - Extract Text from Device Screen

Uses Tesseract OCR to extract all visible text from Android device screenshot.
Can search for specific text and return its position.

Usage:
    uv run adb-ocr-extract.py
    uv run adb-ocr-extract.py --image /path/to/screenshot.png
    uv run adb-ocr-extract.py --search "Login"
    uv run adb-ocr-extract.py --json

Examples:
    # Extract all text from latest screenshot
    uv run adb-ocr-extract.py

    # Extract from specific image
    uv run adb-ocr-extract.py --image ~/screenshot.png

    # Search for specific text
    uv run adb-ocr-extract.py --search "Settings"

    # JSON output with coordinates
    uv run adb-ocr-extract.py --image ~/screenshot.png --search "Login" --json

Exit Codes:
    0 - Success (text extracted)
    1 - Warning (no text found or OCR confidence low)
    2 - Error (image not found or OCR failed)
    3 - Critical (Tesseract not installed)

Requirements:
    - Tesseract installed (brew install tesseract)
    - Python pytesseract package
    - Screenshot image file

Notes:
    - Requires Tesseract 4.x or higher
    - Set TESSDATA_PREFIX if OCR fails
    - Returns bounding boxes for detected text
"""

# ========== SECTION 2: IMPORTS ==========
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
import click
import pytesseract
from PIL import Image
import numpy as np

# ========== SECTION 3: CONSTANTS ==========
DEFAULT_SCREENSHOT_DIR = Path.home() / ".adb-captures"
OCR_CONFIDENCE_THRESHOLD = 10  # Tesseract confidence 0-100
MAX_SEARCH_MATCHES = 10

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root by searching for markers."""
    current = start_path.resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class OCRTextResult:
    """Result of OCR text extraction."""
    text: list  # List of detected text strings
    detected: bool
    search_found: bool = False
    search_term: str = None
    coordinates: dict = None  # Text to coordinates mapping
    avg_confidence: float = 0.0
    timestamp: str = None
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "text": self.text,
            "detected": self.detected,
            "search_found": self.search_found,
            "search_term": self.search_term,
            "coordinates": self.coordinates,
            "avg_confidence": round(self.avg_confidence, 2),
            "error": self.error
        }

# ========== SECTION 6: CORE LOGIC ==========
def load_image(image_path: Path) -> Image.Image:
    """
    Load image from file.

    Args:
        image_path: Path to image file

    Returns:
        PIL Image object

    Raises:
        RuntimeError: If image cannot be loaded
    """
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        raise RuntimeError(f"Image not found: {image_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load image: {e}")

def extract_text_with_coords(image: Image.Image) -> tuple:
    """
    Extract text and bounding boxes using Tesseract.

    Args:
        image: PIL Image object

    Returns:
        Tuple of (text_list, coordinates_dict, confidence)

    Raises:
        RuntimeError: If OCR fails
    """
    try:
        # Get detailed data with confidence scores
        data = pytesseract.image_to_data(image, output_type='dict')

        text_list = []
        coordinates = {}
        confidences = []

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])

            # Only include text with reasonable confidence
            if text and conf > OCR_CONFIDENCE_THRESHOLD:
                text_list.append(text)
                confidences.append(conf)

                # Store coordinates
                bbox = (
                    data['left'][i],
                    data['top'][i],
                    data['left'][i] + data['width'][i],
                    data['top'][i] + data['height'][i]
                )
                coordinates[text] = [list(bbox)]

        avg_conf = np.mean(confidences) if confidences else 0.0
        return text_list, coordinates, float(avg_conf)

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract not installed. Install with: brew install tesseract"
        )
    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {e}")

def find_text_in_results(text_list: list, search_term: str) -> bool:
    """
    Search for text in OCR results (case-insensitive).

    Args:
        text_list: List of detected text
        search_term: Text to search for

    Returns:
        True if search term found in results
    """
    search_lower = search_term.lower()
    for text in text_list:
        if search_lower in text.lower():
            return True
    return False

def get_screenshot_path(image_path: str = None) -> Path:
    """
    Get screenshot path from argument or use default.

    Args:
        image_path: User-specified path or None

    Returns:
        Path to screenshot file

    Raises:
        RuntimeError: If no screenshot found
    """
    if image_path:
        return Path(image_path)

    # Try default location
    default = DEFAULT_SCREENSHOT_DIR / "screenshot.png"
    if default.exists():
        return default

    raise RuntimeError(
        f"No screenshot found. Use --image to specify path."
    )

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: OCRTextResult) -> str:
    """Format result for human-readable output."""
    if not result.detected:
        return f"❌ No text detected in image"

    output = [f"✅ Text extracted (confidence: {result.avg_confidence:.0f}%)"]
    output.append(f"   Detected {len(result.text)} text elements")

    if result.search_term:
        if result.search_found:
            output.append(f"   ✅ Found: '{result.search_term}'")
        else:
            output.append(f"   ❌ Not found: '{result.search_term}'")

    output.append("\n   Text elements:")
    for text in result.text[:10]:  # Show first 10
        output.append(f"     • {text}")

    if len(result.text) > 10:
        output.append(f"     ... and {len(result.text) - 10} more")

    return "\n".join(output)

def format_json_output(result: OCRTextResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--image',
    type=click.Path(exists=False),
    default=None,
    help='Path to screenshot image (default: latest capture)'
)
@click.option(
    '--search',
    default=None,
    help='Search for specific text in results'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(image: str, search: str, output_json: bool) -> None:
    """
    Extract text from Android device screenshot using OCR.

    Uses Tesseract to detect all visible text in screenshot.
    Can search for specific text strings.

    Examples:
        uv run adb-ocr-extract.py
        uv run adb-ocr-extract.py --image ~/screen.png
        uv run adb-ocr-extract.py --search "Login"
    """
    result = OCRTextResult(text=[], detected=False)

    try:
        # Get screenshot path
        screenshot_path = get_screenshot_path(image)

        # Load image
        img = load_image(screenshot_path)

        # Extract text
        text_list, coordinates, confidence = extract_text_with_coords(img)

        result.text = text_list
        result.detected = len(text_list) > 0
        result.coordinates = coordinates
        result.avg_confidence = confidence

        # Search if requested
        if search:
            result.search_term = search
            result.search_found = find_text_in_results(text_list, search)

        # Output result
        if output_json:
            click.echo(format_json_output(result))
        else:
            click.echo(format_human_output(result))

        sys.exit(0 if result.detected else 1)

    except RuntimeError as e:
        result.error = str(e)
        if output_json:
            click.echo(format_json_output(result), err=True)
        else:
            click.echo(f"❌ Error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        result.error = f"Unexpected error: {e}"
        if output_json:
            click.echo(format_json_output(result), err=True)
        else:
            click.echo(f"❌ Fatal: {e}", err=True)
        sys.exit(3)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
