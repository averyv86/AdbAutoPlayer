#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pytesseract>=0.3.10",
#     "pillow>=10.0.0",
# ]
# ///

"""
ADB Swipe - Perform Swipe Gesture on Device Screen

Executes directional swipe gestures for scrolling and navigation.
Supports up, down, left, right directions with configurable distance.

Usage:
    uv run adb-swipe.py --direction up --distance 300
    uv run adb-swipe.py --direction left --distance 500
    uv run adb-swipe.py --direction down --distance 400 --start-y 1000

Examples:
    # Scroll down (swipe up)
    uv run adb-swipe.py --direction up --distance 300

    # Navigate to next page (swipe left)
    uv run adb-swipe.py --direction left --distance 500

    # Custom starting position
    uv run adb-swipe.py --direction up --distance 300 --start-x 500 --start-y 1000

    # With verification
    uv run adb-swipe.py --direction up --distance 300 --verify-text "End of list"

Exit Codes:
    0 - Success (swipe executed)
    1 - Partial (swipe executed but verification failed)
    2 - Error (device error)
    3 - Critical (invalid input or ADB not found)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass
import click
import pytesseract
from PIL import Image
import io

# ========== SECTION 3: CONSTANTS ==========
ADB_COMMAND = "adb"
MIN_DISTANCE = 50
MAX_DISTANCE = 2000
SWIPE_DURATION = 500  # milliseconds
DIRECTIONS = ['up', 'down', 'left', 'right']
ADB_TIMEOUT = 30
DEVICE_SCREENCAP_PATH = "/sdcard/screenshot.png"
DEFAULT_TIMEOUT = 5

# Screen dimensions (typical Android)
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2400
MARGIN = 100

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
class SwipeResult:
    """Result of swipe operation."""
    device: str
    direction: str
    distance: int
    success: bool = False
    start_pos: dict = None
    end_pos: dict = None
    verify_text: str = None
    verified: bool = False
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "device": self.device,
            "direction": self.direction,
            "distance": self.distance,
            "success": self.success,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "verify_text": self.verify_text,
            "verified": self.verified,
            "error": self.error
        }

# ========== SECTION 6: CORE LOGIC ==========
def get_device() -> str:
    """Get first connected device."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=ADB_TIMEOUT
        )
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id, status = line.split('\t')
                if status == 'device':
                    return device_id
        raise RuntimeError("No devices connected")
    except FileNotFoundError:
        raise RuntimeError(f"{ADB_COMMAND} not found")

def calculate_swipe_coords(direction: str, distance: int, start_x: int,
                           start_y: int) -> tuple:
    """
    Calculate start and end coordinates for swipe.

    Args:
        direction: up, down, left, right
        distance: Pixels to swipe
        start_x: Starting X position
        start_y: Starting Y position

    Returns:
        ((x1, y1), (x2, y2))
    """
    if direction == 'up':
        # Swipe up: move start_y down to end_y
        return (start_x, start_y), (start_x, start_y - distance)
    elif direction == 'down':
        # Swipe down: move start_y up to end_y
        return (start_x, start_y), (start_x, start_y + distance)
    elif direction == 'left':
        # Swipe left: move start_x right to end_x
        return (start_x, start_y), (start_x - distance, start_y)
    elif direction == 'right':
        # Swipe right: move start_x left to end_x
        return (start_x, start_y), (start_x + distance, start_y)

def perform_swipe(device: str, direction: str, distance: int, start_x: int,
                 start_y: int) -> tuple:
    """Perform swipe gesture and return start/end positions."""
    (x1, y1), (x2, y2) = calculate_swipe_coords(direction, distance, start_x, start_y)

    # Clamp coordinates to screen bounds
    x1 = max(MARGIN, min(x1, SCREEN_WIDTH - MARGIN))
    y1 = max(MARGIN, min(y1, SCREEN_HEIGHT - MARGIN))
    x2 = max(MARGIN, min(x2, SCREEN_WIDTH - MARGIN))
    y2 = max(MARGIN, min(y2, SCREEN_HEIGHT - MARGIN))

    result = subprocess.run(
        [ADB_COMMAND, "-s", device, "shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), str(SWIPE_DURATION)],
        capture_output=True,
        timeout=ADB_TIMEOUT
    )
    if result.returncode != 0:
        raise RuntimeError(f"Swipe failed: {result.stderr.decode()}")

    return {"x": x1, "y": y1}, {"x": x2, "y": y2}

def capture_screen(device: str) -> bytes:
    """Capture device screen."""
    try:
        subprocess.run(
            [ADB_COMMAND, "-s", device, "shell", "screencap", "-p",
             DEVICE_SCREENCAP_PATH],
            capture_output=True,
            timeout=ADB_TIMEOUT
        )
        result = subprocess.run(
            [ADB_COMMAND, "-s", device, "pull", DEVICE_SCREENCAP_PATH, "-"],
            capture_output=True,
            timeout=ADB_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to pull screenshot")
        return result.stdout
    finally:
        subprocess.run(
            [ADB_COMMAND, "-s", device, "shell", "rm", DEVICE_SCREENCAP_PATH],
            capture_output=True,
            timeout=10
        )

def verify_text_on_screen(image_data: bytes, text: str) -> bool:
    """Check if text appears on screen."""
    try:
        image = Image.open(io.BytesIO(image_data))
        ocr_text = pytesseract.image_to_string(image).lower()
        return text.lower() in ocr_text
    except Exception:
        return False

def wait_for_verification(device: str, text: str, timeout: int) -> bool:
    """Wait for verification text to appear."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            image_data = capture_screen(device)
            if verify_text_on_screen(image_data, text):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: SwipeResult) -> str:
    """Format result for human-readable output."""
    if not result.success:
        return f"❌ Swipe failed: {result.error}"

    status = "✅" if result.verified or not result.verify_text else "⚠️"
    output = [f"{status} Swipe executed"]
    output.append(f"   Direction: {result.direction}")
    output.append(f"   Distance: {result.distance}px")
    output.append(f"   From: ({result.start_pos['x']}, {result.start_pos['y']})")
    output.append(f"   To: ({result.end_pos['x']}, {result.end_pos['y']})")

    if result.verify_text:
        if result.verified:
            output.append(f"   ✅ Verified: '{result.verify_text}' found")
        else:
            output.append(f"   ❌ Verification failed: '{result.verify_text}' not found")

    return "\n".join(output)

def format_json_output(result: SwipeResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--direction',
    type=click.Choice(DIRECTIONS),
    required=True,
    help='Swipe direction'
)
@click.option(
    '--distance',
    type=int,
    required=True,
    help=f'Distance in pixels ({MIN_DISTANCE}-{MAX_DISTANCE})'
)
@click.option(
    '--device',
    default=None,
    help='Device ID'
)
@click.option(
    '--start-x',
    type=int,
    default=SCREEN_WIDTH // 2,
    help='Starting X coordinate'
)
@click.option(
    '--start-y',
    type=int,
    default=SCREEN_HEIGHT // 2,
    help='Starting Y coordinate'
)
@click.option(
    '--verify-text',
    default=None,
    help='Text to verify after swipe'
)
@click.option(
    '--timeout',
    type=int,
    default=DEFAULT_TIMEOUT,
    help='Verification timeout in seconds'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='JSON output'
)
def cli(direction: str, distance: int, device: str, start_x: int,
        start_y: int, verify_text: str, timeout: int, output_json: bool) -> None:
    """
    Perform swipe gesture on device screen.

    Swipes in specified direction for specified distance.
    """
    if not (MIN_DISTANCE <= distance <= MAX_DISTANCE):
        click.echo(f"❌ Error: distance must be {MIN_DISTANCE}-{MAX_DISTANCE}px", err=True)
        sys.exit(3)

    result = SwipeResult(device="", direction=direction, distance=distance)

    try:
        selected_device = device or get_device()
        result.device = selected_device

        start_pos, end_pos = perform_swipe(
            selected_device, direction, distance, start_x, start_y
        )
        result.success = True
        result.start_pos = start_pos
        result.end_pos = end_pos

        if verify_text:
            result.verify_text = verify_text
            result.verified = wait_for_verification(selected_device, verify_text, timeout)

        if output_json:
            click.echo(format_json_output(result))
        else:
            click.echo(format_human_output(result))

        sys.exit(0)

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
