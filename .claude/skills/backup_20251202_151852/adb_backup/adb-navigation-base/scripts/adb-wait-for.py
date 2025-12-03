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
ADB Wait For - Wait for Element or Text to Appear

Polls device screen waiting for specific text or element to appear.
Essential for synchronization between automation steps.

Usage:
    uv run adb-wait-for.py --method text --target "Loaded"
    uv run adb-wait-for.py --method text --target "Button" --timeout 10
    uv run adb-wait-for.py --method text --target "Ready" --interval 0.5

Examples:
    # Wait for text (default 10s)
    uv run adb-wait-for.py --method text --target "Login"

    # Wait with custom timeout
    uv run adb-wait-for.py --method text --target "Processing" --timeout 20

    # Fast polling (check every 0.5s instead of default 1s)
    uv run adb-wait-for.py --method text --target "Done" --interval 0.2

Exit Codes:
    0 - Success (element found)
    1 - Timeout (element not found within timeout)
    2 - Error (device error)
    3 - Critical (invalid input or OCR error)
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
DEFAULT_TIMEOUT = 10
MIN_TIMEOUT = 1
MAX_TIMEOUT = 60
DEFAULT_INTERVAL = 1.0
MIN_INTERVAL = 0.1
MAX_INTERVAL = 5.0
ADB_TIMEOUT = 30
DEVICE_SCREENCAP_PATH = "/sdcard/screenshot.png"
DETECTION_METHODS = ['text']

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
class WaitForResult:
    """Result of wait-for operation."""
    device: str
    method: str
    target: str
    found: bool = False
    elapsed_time: float = 0.0
    attempts: int = 0
    timeout: int = 0
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "device": self.device,
            "method": self.method,
            "target": self.target,
            "found": self.found,
            "elapsed_time": round(self.elapsed_time, 2),
            "attempts": self.attempts,
            "timeout": self.timeout,
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

def text_on_screen(image_data: bytes, text: str) -> bool:
    """Check if text appears on screen."""
    try:
        image = Image.open(io.BytesIO(image_data))
        ocr_text = pytesseract.image_to_string(image).lower()
        return text.lower() in ocr_text
    except Exception:
        return False

def wait_for_text(device: str, target: str, timeout: int,
                 interval: float) -> tuple:
    """
    Wait for text to appear on screen.

    Returns:
        (found, elapsed_time, attempts)
    """
    start_time = time.time()
    attempts = 0

    while time.time() - start_time < timeout:
        attempts += 1
        try:
            image_data = capture_screen(device)
            if text_on_screen(image_data, target):
                elapsed = time.time() - start_time
                return True, elapsed, attempts
        except Exception:
            pass

        time.sleep(interval)

    elapsed = time.time() - start_time
    return False, elapsed, attempts

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: WaitForResult) -> str:
    """Format result for human-readable output."""
    if result.found:
        return (
            f"✅ Element found\n"
            f"   Target: '{result.target}'\n"
            f"   Time: {result.elapsed_time:.1f}s\n"
            f"   Attempts: {result.attempts}"
        )
    else:
        return (
            f"⏱️ Timeout (not found)\n"
            f"   Target: '{result.target}'\n"
            f"   Waited: {result.elapsed_time:.1f}s\n"
            f"   Timeout: {result.timeout}s\n"
            f"   Attempts: {result.attempts}"
        )

def format_json_output(result: WaitForResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--method',
    type=click.Choice(DETECTION_METHODS),
    required=True,
    help='Detection method'
)
@click.option(
    '--target',
    required=True,
    help='Text or pattern to wait for'
)
@click.option(
    '--device',
    default=None,
    help='Device ID'
)
@click.option(
    '--timeout',
    type=int,
    default=DEFAULT_TIMEOUT,
    help=f'Timeout in seconds ({MIN_TIMEOUT}-{MAX_TIMEOUT})'
)
@click.option(
    '--interval',
    type=float,
    default=DEFAULT_INTERVAL,
    help=f'Polling interval ({MIN_INTERVAL}-{MAX_INTERVAL}s)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='JSON output'
)
def cli(method: str, target: str, device: str, timeout: int,
        interval: float, output_json: bool) -> None:
    """
    Wait for element or text to appear on screen.

    Polls the device screen waiting for specific content.
    """
    if not (MIN_TIMEOUT <= timeout <= MAX_TIMEOUT):
        click.echo(f"❌ Error: timeout must be {MIN_TIMEOUT}-{MAX_TIMEOUT}s", err=True)
        sys.exit(3)

    if not (MIN_INTERVAL <= interval <= MAX_INTERVAL):
        click.echo(f"❌ Error: interval must be {MIN_INTERVAL}-{MAX_INTERVAL}s", err=True)
        sys.exit(3)

    result = WaitForResult(device="", method=method, target=target, timeout=timeout)

    try:
        selected_device = device or get_device()
        result.device = selected_device

        if method == 'text':
            found, elapsed, attempts = wait_for_text(
                selected_device, target, timeout, interval
            )
        else:
            found, elapsed, attempts = False, 0.0, 0

        result.found = found
        result.elapsed_time = elapsed
        result.attempts = attempts

        if output_json:
            click.echo(format_json_output(result))
        else:
            click.echo(format_human_output(result))

        sys.exit(0 if found else 1)

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
