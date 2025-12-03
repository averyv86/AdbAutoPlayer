#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pillow>=10.0.0",
# ]
# ///

"""
ADB Screen Capture - Capture Android Device Screen

Captures current screen from connected Android device using ADB screencap
and saves to local filesystem. Works with physical devices and emulators.

Usage:
    uv run adb-screen-capture.py
    uv run adb-screen-capture.py --device 127.0.0.1:5555
    uv run adb-screen-capture.py --output /tmp/screen.png
    uv run adb-screen-capture.py --json

Examples:
    # Capture from first connected device
    uv run adb-screen-capture.py

    # Capture from specific device
    uv run adb-screen-capture.py --device 127.0.0.1:5555

    # Save to custom location
    uv run adb-screen-capture.py --output ~/screenshots/latest.png

    # JSON output for scripting
    uv run adb-screen-capture.py --json

Exit Codes:
    0 - Success (screenshot captured and saved)
    1 - Warning (device offline or no devices found)
    2 - Error (ADB not found or permission denied)
    3 - Critical (file write error)

Requirements:
    - ADB installed and in PATH
    - Android device connected and authorized
    - Write permissions for output directory

Notes:
    - Creates output directory if it doesn't exist
    - Overwrites existing files silently
    - Uses /sdcard/screenshot.png as temporary storage on device
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
import click
from PIL import Image
import io

# ========== SECTION 3: CONSTANTS ==========
ADB_COMMAND = "adb"
DEVICE_SCREENCAP_PATH = "/sdcard/screenshot.png"
DEFAULT_OUTPUT_DIR = Path.home() / ".adb-captures"
DEFAULT_OUTPUT_FILE = "screenshot.png"
ADB_TIMEOUT = 30

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """
    Auto-detect project root by searching for markers.

    Searches upward from current directory looking for .git, pyproject.toml,
    .moai, or .claude to identify project root.

    Args:
        start_path: Starting directory for search (default: cwd)

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root cannot be found
    """
    current = start_path.resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
class ScreenCaptureResult:
    """Result of screen capture operation."""

    def __init__(self, device: str, local_path: Path, size: tuple = None,
                 success: bool = False, error: str = None):
        self.device = device
        self.local_path = local_path
        self.size = size
        self.success = success
        self.error = error
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "device": self.device,
            "timestamp": self.timestamp,
            "local_path": str(self.local_path),
            "size": self.size,
            "success": self.success,
            "error": self.error
        }

# ========== SECTION 6: CORE LOGIC ==========
def get_adb_devices() -> list:
    """
    Get list of connected ADB devices.

    Returns:
        List of device IDs (empty if none connected)

    Raises:
        RuntimeError: If ADB command fails
    """
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=ADB_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError(f"ADB error: {result.stderr}")

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
        raise RuntimeError(f"{ADB_COMMAND} not found. Install ADB first.")

def select_device(specified_device: str = None) -> str:
    """
    Select ADB device to use.

    Args:
        specified_device: Device ID if specified, otherwise select first

    Returns:
        Device ID to use

    Raises:
        RuntimeError: If no devices found or specified device not connected
    """
    if specified_device:
        # Check if specified device is connected
        devices = get_adb_devices()
        if specified_device not in devices:
            raise RuntimeError(
                f"Device {specified_device} not found or not authorized"
            )
        return specified_device

    # Find first connected device
    devices = get_adb_devices()
    if not devices:
        raise RuntimeError(
            "No devices connected. Connect device and run 'adb devices'"
        )
    return devices[0]

def capture_screen(device: str) -> bytes:
    """
    Capture screen from Android device.

    Args:
        device: Device ID (from adb devices)

    Returns:
        Screenshot image data as bytes

    Raises:
        RuntimeError: If screencap fails
    """
    # Run screencap on device
    result = subprocess.run(
        [ADB_COMMAND, "-s", device, "shell", "screencap", "-p",
         DEVICE_SCREENCAP_PATH],
        capture_output=True,
        timeout=ADB_TIMEOUT
    )
    if result.returncode != 0:
        raise RuntimeError(f"Screencap failed: {result.stderr.decode()}")

    # Pull image from device
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device, "pull", DEVICE_SCREENCAP_PATH, "-"],
            capture_output=True,
            timeout=ADB_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to pull screenshot from device")
        return result.stdout
    finally:
        # Clean up temporary file on device
        subprocess.run(
            [ADB_COMMAND, "-s", device, "shell", "rm", DEVICE_SCREENCAP_PATH],
            capture_output=True,
            timeout=10
        )

def get_image_size(image_data: bytes) -> tuple:
    """
    Get image dimensions from image data.

    Args:
        image_data: Raw image bytes

    Returns:
        Tuple of (width, height)

    Raises:
        RuntimeError: If image data is invalid
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        return image.size
    except Exception as e:
        raise RuntimeError(f"Failed to parse image: {e}")

def save_screenshot(image_data: bytes, output_path: Path) -> None:
    """
    Save screenshot data to file.

    Args:
        image_data: Raw image bytes
        output_path: Path to save screenshot

    Raises:
        RuntimeError: If write fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(image_data)
    except IOError as e:
        raise RuntimeError(f"Failed to write screenshot: {e}")

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: ScreenCaptureResult) -> str:
    """Format result for human-readable output."""
    if result.success:
        size_str = f"{result.size[0]}x{result.size[1]}" if result.size else "unknown"
        return (
            f"✅ Screenshot captured successfully\n"
            f"   Device: {result.device}\n"
            f"   Size: {size_str}\n"
            f"   Saved: {result.local_path}\n"
            f"   Time: {result.timestamp}"
        )
    else:
        return f"❌ Failed to capture screenshot: {result.error}"

def format_json_output(result: ScreenCaptureResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    default=None,
    help='Device ID (default: first connected device)'
)
@click.option(
    '--output',
    type=click.Path(),
    default=None,
    help=f'Output file path (default: {DEFAULT_OUTPUT_DIR}/screenshot.png)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: str, output: str, output_json: bool) -> None:
    """
    Capture Android device screen via ADB.

    Captures current screen and saves locally. Works with physical devices
    and emulators.

    Examples:
        uv run adb-screen-capture.py
        uv run adb-screen-capture.py --device 127.0.0.1:5555
        uv run adb-screen-capture.py --output ~/screen.png
    """
    result = ScreenCaptureResult(device or "auto", Path(output or "") if output else None)

    try:
        # Select device
        selected_device = select_device(device)
        result.device = selected_device

        # Capture screen
        image_data = capture_screen(selected_device)

        # Get image size
        size = get_image_size(image_data)
        result.size = size

        # Determine output path
        if not output:
            output_path = DEFAULT_OUTPUT_DIR / DEFAULT_OUTPUT_FILE
        else:
            output_path = Path(output)

        # Save screenshot
        save_screenshot(image_data, output_path)
        result.local_path = output_path
        result.success = True

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
