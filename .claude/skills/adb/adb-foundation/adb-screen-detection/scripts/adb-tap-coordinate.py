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
ADB Tap Coordinate - Tap Device Screen at Coordinates

Performs tap action on Android device at specified coordinates.
Optionally verifies success by checking screen state after tap.

Usage:
    uv run adb-tap-coordinate.py --x 100 --y 200
    uv run adb-tap-coordinate.py --x 100 --y 200 --device 127.0.0.1:5555
    uv run adb-tap-coordinate.py --x 100 --y 200 --verify-text "Next Screen"

Examples:
    # Basic tap
    uv run adb-tap-coordinate.py --x 100 --y 200

    # Tap with screen verification
    uv run adb-tap-coordinate.py --x 100 --y 200 --verify-text "Welcome"

    # Tap with longer wait time
    uv run adb-tap-coordinate.py --x 100 --y 200 --timeout 10

    # JSON output for scripting
    uv run adb-tap-coordinate.py --x 100 --y 200 --json

Exit Codes:
    0 - Success (tap executed and verified)
    1 - Warning (tap executed but verification failed)
    2 - Error (device not found or ADB error)
    3 - Critical (invalid input or permission denied)

Requirements:
    - ADB installed
    - Device connected and authorized
    - Valid coordinates within screen bounds

Notes:
    - Coordinates: (0, 0) is top-left corner
    - Verification: Captures screen and checks for expected text
    - Timeout: Wait this long for verification text to appear
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
DEFAULT_TIMEOUT = 5
MAX_TIMEOUT = 30
ADB_TIMEOUT = 30
DEFAULT_SCREENSHOT_DIR = Path.home() / ".adb-captures"
DEVICE_SCREENCAP_PATH = "/sdcard/screenshot.png"

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
class TapResult:
    """Result of tap action."""
    device: str
    tap: dict  # {x, y}
    success: bool = False
    verified: bool = False
    verify_text: str = None
    verification_match: bool = False
    attempt: int = 1
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "device": self.device,
            "tap": self.tap,
            "success": self.success,
            "verified": self.verified,
            "verify_text": self.verify_text,
            "verification_match": self.verification_match,
            "attempt": self.attempt,
            "error": self.error
        }

# ========== SECTION 6: CORE LOGIC ==========
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=ADB_TIMEOUT
        )
        if result.returncode != 0:
            return []

        devices = []
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id = line.split('\t')[0]
                status = line.split('\t')[1]
                if status == 'device':
                    devices.append(device_id)
        return devices
    except FileNotFoundError:
        raise RuntimeError(f"{ADB_COMMAND} not found")

def select_device(specified_device: str = None) -> str:
    """Select device to use."""
    if specified_device:
        devices = get_adb_devices()
        if specified_device not in devices:
            raise RuntimeError(f"Device {specified_device} not found")
        return specified_device

    devices = get_adb_devices()
    if not devices:
        raise RuntimeError("No devices connected")
    return devices[0]

def perform_tap(device: str, x: int, y: int) -> None:
    """
    Perform tap action on device.

    Args:
        device: Device ID
        x: X coordinate
        y: Y coordinate

    Raises:
        RuntimeError: If tap fails
    """
    result = subprocess.run(
        [ADB_COMMAND, "-s", device, "shell", "input", "tap", str(x), str(y)],
        capture_output=True,
        timeout=ADB_TIMEOUT
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tap failed: {result.stderr.decode()}")

def capture_screen(device: str) -> bytes:
    """Capture device screen."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device, "shell", "screencap", "-p",
             DEVICE_SCREENCAP_PATH],
            capture_output=True,
            timeout=ADB_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError("Screencap failed")

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

def verify_screen_content(image_data: bytes, search_text: str) -> bool:
    """
    Verify screen contains expected text using OCR.

    Args:
        image_data: Screenshot image bytes
        search_text: Text to search for

    Returns:
        True if text found in screen
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        ocr_text = pytesseract.image_to_string(image).lower()
        return search_text.lower() in ocr_text
    except Exception:
        return False

def wait_for_verification(device: str, verify_text: str,
                         timeout: int) -> bool:
    """
    Wait for verification text to appear on screen.

    Args:
        device: Device ID
        verify_text: Text to search for
        timeout: Maximum wait time in seconds

    Returns:
        True if text found within timeout
    """
    start_time = time.time()
    interval = 0.5  # Check every 0.5 seconds

    while time.time() - start_time < timeout:
        try:
            image_data = capture_screen(device)
            if verify_screen_content(image_data, verify_text):
                return True
        except Exception:
            pass

        time.sleep(interval)

    return False

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: TapResult) -> str:
    """Format result for human-readable output."""
    if not result.success:
        return f"❌ Tap failed: {result.error}"

    status = "✅" if result.verified else "⚠️"
    output = [f"{status} Tap executed"]
    output.append(f"   Device: {result.device}")
    output.append(f"   Coordinates: ({result.tap['x']}, {result.tap['y']})")

    if result.verify_text:
        if result.verification_match:
            output.append(f"   ✅ Verified: '{result.verify_text}' found")
        else:
            output.append(f"   ❌ Verification failed: '{result.verify_text}' not found")

    return "\n".join(output)

def format_json_output(result: TapResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--x',
    type=int,
    required=True,
    help='X coordinate (0 = left)'
)
@click.option(
    '--y',
    type=int,
    required=True,
    help='Y coordinate (0 = top)'
)
@click.option(
    '--device',
    default=None,
    help='Device ID (default: first connected device)'
)
@click.option(
    '--verify-text',
    default=None,
    help='Text to verify after tap (enables screen verification)'
)
@click.option(
    '--timeout',
    type=int,
    default=DEFAULT_TIMEOUT,
    help=f'Verification timeout in seconds (max: {MAX_TIMEOUT})'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(x: int, y: int, device: str, verify_text: str, timeout: int,
        output_json: bool) -> None:
    """
    Tap device screen at coordinates.

    Performs tap action and optionally verifies screen state after tap.
    Useful for reliable UI automation with screen verification.

    Examples:
        uv run adb-tap-coordinate.py --x 100 --y 200
        uv run adb-tap-coordinate.py --x 100 --y 200 --verify-text "Welcome"
        uv run adb-tap-coordinate.py --x 100 --y 200 --timeout 10
    """
    # Validate input
    if timeout > MAX_TIMEOUT or timeout < 1:
        click.echo(f"❌ Error: timeout must be 1-{MAX_TIMEOUT} seconds", err=True)
        sys.exit(3)

    result = TapResult(device="", tap={"x": x, "y": y})

    try:
        # Select device
        selected_device = select_device(device)
        result.device = selected_device

        # Perform tap
        perform_tap(selected_device, x, y)
        result.success = True

        # Verify if requested
        if verify_text:
            result.verify_text = verify_text
            match = wait_for_verification(selected_device, verify_text, timeout)
            result.verification_match = match
            result.verified = True

        # Output result
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
