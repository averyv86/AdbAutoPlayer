#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pytesseract>=0.3.10",
#     "opencv-python>=4.8.0",
#     "pillow>=10.0.0",
#     "numpy>=1.24.0",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
ADB Find Element - Locate UI Elements on Device Screen (Hybrid Detection)

Finds UI elements using multiple detection methods with intelligent fallback:
1. Semantic Detection (UIAutomator2) - Fastest, most reliable
2. Template Image Matching - Fast, requires template
3. OCR Text Search - Slowest, always works

Supports hybrid strategy that automatically tries all methods in sequence.

Usage:
    uv run adb-find-element.py --method hybrid --target "Login"
    uv run adb-find-element.py --method semantic --target "Button"
    uv run adb-find-element.py --method template --template ./template.png
    uv run adb-find-element.py --method ocr --target "Login" --threshold 0.8

Examples:
    # Hybrid detection (recommended - uses semantic + fallback)
    uv run adb-find-element.py --method hybrid --target "Login"

    # Direct semantic detection (fast, requires device)
    uv run adb-find-element.py --method semantic --target "Button"

    # Template matching (requires template image)
    uv run adb-find-element.py --method template --template ~/button.png

    # OCR text search (slow but always works)
    uv run adb-find-element.py --method ocr --target "Settings" --threshold 0.9

    # JSON output with coordinates
    uv run adb-find-element.py --method hybrid --target "Login" --json

Exit Codes:
    0 - Success (element found)
    1 - Warning (element not found)
    2 - Error (invalid method or file not found)
    3 - Critical (detection error)

Requirements:
    - For semantic/hybrid: Device with UIAutomator2 support
    - For template: Template image file
    - For OCR: Tesseract installed

Notes:
    - Threshold: 0.5-1.0 (higher = stricter matching)
    - Recommended: hybrid method for best results
    - Returns bounding box in (x, y, width, height) format
"""

# ========== SECTION 2: IMPORTS ==========
import json
import sys
from pathlib import Path
from dataclasses import dataclass
import click
import cv2
import numpy as np
from PIL import Image
import pytesseract

# ========== SECTION 3: CONSTANTS ==========
DEFAULT_SCREENSHOT_DIR = Path.home() / ".adb-captures"
DEFAULT_THRESHOLD = 0.8
MIN_THRESHOLD = 0.5
MAX_THRESHOLD = 1.0
DETECTION_METHODS = ['ocr', 'template', 'semantic', 'hybrid']
DEFAULT_DEVICE = 'localhost:5555'

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
class ElementLocation:
    """Location and properties of found UI element."""
    found: bool
    method: str
    target: str = None
    coordinates: dict = None  # {x, y, width, height}
    confidence: float = 0.0
    center: dict = None  # {x, y}
    message: str = None
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "found": self.found,
            "method": self.method,
            "target": self.target,
            "coordinates": self.coordinates,
            "center": self.center,
            "confidence": round(self.confidence, 3),
            "message": self.message,
            "error": self.error
        }

# ========== SECTION 6: CORE LOGIC ==========
def get_screenshot(image_path: str = None) -> np.ndarray:
    """
    Load screenshot as OpenCV image.

    Args:
        image_path: Custom path or None for default

    Returns:
        OpenCV image (BGR format)

    Raises:
        RuntimeError: If image not found
    """
    if image_path:
        path = Path(image_path)
    else:
        default = DEFAULT_SCREENSHOT_DIR / "screenshot.png"
        if not default.exists():
            raise RuntimeError("No screenshot found. Capture one first.")
        path = default

    if not path.exists():
        raise RuntimeError(f"Image not found: {path}")

    img = cv2.imread(str(path))
    if img is None:
        raise RuntimeError(f"Failed to load image: {path}")
    return img

def find_element_by_ocr(screenshot: np.ndarray, target_text: str,
                        threshold: float) -> ElementLocation:
    """
    Find element by OCR text search.

    Args:
        screenshot: OpenCV image
        target_text: Text to search for
        threshold: Confidence threshold (0.5-1.0)

    Returns:
        ElementLocation with found coordinates
    """
    result = ElementLocation(found=False, method='ocr', target=target_text)

    try:
        # Convert BGR to RGB for Tesseract
        rgb_img = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        # Get OCR data with coordinates
        data = pytesseract.image_to_data(pil_img, output_type='dict')

        best_match = None
        best_confidence = 0.0

        # Search for matching text
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) / 100.0

            # Match if threshold met
            if target_text.lower() in text.lower() and conf >= threshold:
                if conf > best_confidence:
                    best_confidence = conf
                    best_match = {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'text': text
                    }

        if best_match:
            result.found = True
            result.confidence = best_confidence
            result.coordinates = {
                'x': best_match['x'],
                'y': best_match['y'],
                'width': best_match['width'],
                'height': best_match['height']
            }
            result.center = {
                'x': best_match['x'] + best_match['width'] // 2,
                'y': best_match['y'] + best_match['height'] // 2
            }
            result.message = f"Element found at ({result.center['x']}, {result.center['y']})"
        else:
            result.message = f"Text '{target_text}' not found (threshold: {threshold})"

    except pytesseract.TesseractNotFoundError:
        result.error = "Tesseract not installed"
        return result
    except Exception as e:
        result.error = f"OCR error: {e}"
        return result

    return result

def find_element_by_template(screenshot: np.ndarray, template_path: str,
                            threshold: float) -> ElementLocation:
    """
    Find element by template image matching.

    Args:
        screenshot: OpenCV image (screenshot)
        template_path: Path to template image
        threshold: Matching threshold (0.5-1.0)

    Returns:
        ElementLocation with found coordinates
    """
    result = ElementLocation(found=False, method='template',
                            target=Path(template_path).name)

    try:
        # Load template
        template = cv2.imread(template_path)
        if template is None:
            result.error = f"Failed to load template: {template_path}"
            return result

        # Template matching
        result_match = cv2.matchTemplate(screenshot, template,
                                        cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_match)

        if max_val >= threshold:
            result.found = True
            result.confidence = float(max_val)
            h, w = template.shape[:2]
            result.coordinates = {
                'x': max_loc[0],
                'y': max_loc[1],
                'width': w,
                'height': h
            }
            result.center = {
                'x': max_loc[0] + w // 2,
                'y': max_loc[1] + h // 2
            }
            result.message = f"Template matched at ({result.center['x']}, {result.center['y']})"
        else:
            result.message = f"No match found (confidence: {max_val:.2f}, threshold: {threshold})"

    except Exception as e:
        result.error = f"Template matching error: {e}"
        return result

    return result

def find_element_by_semantic(target_text: str, device_id: str = DEFAULT_DEVICE,
                            timeout: int = 10) -> ElementLocation:
    """
    Find element using UIAutomator2 semantic detection.

    Args:
        target_text: Text to search for
        device_id: Device ID (default: localhost:5555)
        timeout: Timeout in seconds

    Returns:
        ElementLocation with found coordinates
    """
    result = ElementLocation(found=False, method='semantic', target=target_text)

    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)

        # Try to find element by text
        selector = device(text=target_text)
        if selector.wait(timeout=timeout):
            info = selector.info
            bounds = info.get('bounds', {})
            if bounds:
                x = bounds.get('left', 0)
                y = bounds.get('top', 0)
                width = bounds.get('right', 0) - x
                height = bounds.get('bottom', 0) - y
                center_x = x + width // 2
                center_y = y + height // 2

                result.found = True
                result.confidence = 1.0  # Semantic detection is fully confident
                result.coordinates = {'x': x, 'y': y, 'width': width, 'height': height}
                result.center = {'x': center_x, 'y': center_y}
                result.message = f"Semantic match found at ({center_x}, {center_y})"
                return result

    except ImportError:
        result.error = "uiautomator2 not installed"
    except Exception as e:
        result.error = f"Semantic detection error: {e}"

    return result

def find_element_hybrid(target_text: str, screenshot: np.ndarray,
                       template_path: str = None, device_id: str = DEFAULT_DEVICE,
                       threshold: float = DEFAULT_THRESHOLD) -> ElementLocation:
    """
    Find element using hybrid fallback strategy.
    Priority 1: Semantic detection (uiautomator2)
    Priority 2: Template matching
    Priority 3: OCR detection

    Args:
        target_text: Text to search for
        screenshot: OpenCV image
        template_path: Optional template path
        device_id: Device ID for semantic detection
        threshold: Matching threshold for template/OCR

    Returns:
        ElementLocation with found coordinates
    """
    # Priority 1: Semantic detection
    result = find_element_by_semantic(target_text, device_id)
    if result.found:
        result.message += " (via semantic detection)"
        return result

    # Priority 2: Template matching (if template provided)
    if template_path:
        result = find_element_by_template(screenshot, template_path, threshold)
        if result.found:
            result.message += " (via template matching)"
            return result

    # Priority 3: OCR detection
    result = find_element_by_ocr(screenshot, target_text, threshold)
    if result.found:
        result.message += " (via OCR detection)"
        return result

    # All methods failed
    result = ElementLocation(found=False, method='hybrid', target=target_text)
    result.message = f"Element not found using hybrid strategy (semantic, template, OCR)"
    return result

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: ElementLocation) -> str:
    """Format result for human-readable output."""
    if result.found:
        return (
            f"✅ Element found\n"
            f"   Method: {result.method}\n"
            f"   Target: {result.target}\n"
            f"   Position: ({result.center['x']}, {result.center['y']})\n"
            f"   Box: {result.coordinates}\n"
            f"   Confidence: {result.confidence:.1%}\n"
            f"   {result.message}"
        )
    else:
        msg = result.error if result.error else result.message
        return f"❌ Element not found: {msg}"

def format_json_output(result: ElementLocation) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--method',
    type=click.Choice(DETECTION_METHODS),
    required=True,
    help='Detection method: ocr, template, semantic, or hybrid'
)
@click.option(
    '--target',
    default=None,
    help='Text to search for (required for OCR, semantic, hybrid methods)'
)
@click.option(
    '--template',
    type=click.Path(exists=False),
    default=None,
    help='Template image path (required for template method, optional for hybrid)'
)
@click.option(
    '--image',
    type=click.Path(exists=False),
    default=None,
    help='Screenshot path (default: latest capture, required for ocr/template)'
)
@click.option(
    '--device',
    default=DEFAULT_DEVICE,
    help='Device ID for semantic detection'
)
@click.option(
    '--threshold',
    type=float,
    default=DEFAULT_THRESHOLD,
    help=f'Matching threshold {MIN_THRESHOLD}-{MAX_THRESHOLD}'
)
@click.option(
    '--timeout',
    type=int,
    default=10,
    help='Timeout for semantic detection (seconds)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(method: str, target: str, template: str, image: str, device: str,
        threshold: float, timeout: int, output_json: bool) -> None:
    """
    Find UI element on device screen using hybrid detection strategy.

    Methods:
        ocr       - Text search using Tesseract OCR
        template  - Template image matching
        semantic  - UIAutomator2 accessibility tree (fastest, most reliable)
        hybrid    - Try semantic → template → OCR (recommended)

    Examples:
        uv run adb-find-element.py --method hybrid --target "Login"
        uv run adb-find-element.py --method semantic --target "Button"
        uv run adb-find-element.py --method ocr --target "Settings"
        uv run adb-find-element.py --method template --template button.png
    """
    # Validate inputs
    if method in ['ocr', 'semantic', 'hybrid'] and not target:
        click.echo(f"❌ Error: --target required for {method.upper()} method", err=True)
        sys.exit(2)

    if method == 'template' and not template:
        click.echo("❌ Error: --template required for template method", err=True)
        sys.exit(2)

    if not (MIN_THRESHOLD <= threshold <= MAX_THRESHOLD):
        click.echo(f"❌ Error: threshold must be {MIN_THRESHOLD}-{MAX_THRESHOLD}",
                   err=True)
        sys.exit(2)

    result = ElementLocation(found=False, method=method,
                           target=target or Path(template).name if template else None)

    try:
        # Handle semantic and hybrid methods (no screenshot needed)
        if method == 'semantic':
            result = find_element_by_semantic(target, device, timeout)
        elif method == 'hybrid':
            # Load screenshot for fallback methods
            try:
                screenshot = get_screenshot(image)
            except RuntimeError:
                # If no screenshot, try semantic only
                result = find_element_by_semantic(target, device, timeout)
                if not result.found:
                    result.message = "Hybrid: semantic detection failed and no screenshot for fallback"
            else:
                # Try hybrid with screenshot fallback
                result = find_element_hybrid(target, screenshot, template, device, threshold)
        else:
            # Load screenshot for ocr/template methods
            screenshot = get_screenshot(image)

            # Find element
            if method == 'ocr':
                result = find_element_by_ocr(screenshot, target, threshold)
            else:  # template
                result = find_element_by_template(screenshot, template, threshold)

        # Output result
        if output_json:
            click.echo(format_json_output(result))
        else:
            click.echo(format_human_output(result))

        sys.exit(0 if result.found else 1)

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
