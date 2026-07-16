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
ADB Smart Tap - Tap with Retry Logic and Verification

Performs tap action with automatic retry on failure and optional post-tap verification.
Essential for reliable automation of flaky UI elements.

Usage:
    uv run adb-tap.py --x 100 --y 200
    uv run adb-tap.py --x 100 --y 200 --retry 3
    uv run adb-tap.py --x 100 --y 200 --verify-text "Next"

Examples:
    # Simple tap
    uv run adb-tap.py --x 100 --y 200

    # Tap with retry (up to 3 attempts)
    uv run adb-tap.py --x 100 --y 200 --retry 3

    # Tap with verification (wait for text after tap)
    uv run adb-tap.py --x 100 --y 200 --verify-text "Welcome"

    # Full example: tap, retry 3x, verify within 10s
    uv run adb-tap.py --x 100 --y 200 --retry 3 --verify-text "Loaded" --timeout 10

Exit Codes:
    0 - Success (tap executed successfully)
    1 - Partial (tap executed but verification failed)
    2 - Error (device error or max retries exceeded)
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
DEFAULT_RETRY = 1
MAX_RETRY = 10
DEFAULT_TIMEOUT = 5
MAX_TIMEOUT = 30
RETRY_DELAY = 0.5
ADB_TIMEOUT = 30
DEVICE_SCREENCAP_PATH = "/sdcard/screenshot.png"
DEFAULT_SCREENSHOT_DIR = Path.home() / ".adb-captures"

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
class SmartTapResult:
    """Result of smart tap operation."""
    device: str
    tap: dict
    success: bool = False
    attempt: int = 1
    verify_text: str = None
    verified: bool = False
    error: str = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "device": self.device,
            "tap": self.tap,
            "success": self.success,
            "attempt": self.attempt,
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

def tap_device(device: str, x: int, y: int) -> None:
    """Perform single tap action."""
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
    """Wait for text to appear on screen."""
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
def format_human_output(result: SmartTapResult) -> str:
    """Format result for human-readable output."""
    if not result.success:
        return f"❌ Tap failed after {result.attempt} attempt(s): {result.error}"

    status = "✅" if result.verified or not result.verify_text else "⚠️"
    output = [f"{status} Tap successful (attempt {result.attempt})"]
    output.append(f"   Coordinates: ({result.tap['x']}, {result.tap['y']})")
    if result.verify_text:
        if result.verified:
            output.append(f"   ✅ Verified: '{result.verify_text}' found")
        else:
            output.append(f"   ❌ Verification failed: '{result.verify_text}' not found")
    return "\n".join(output)

def format_json_output(result: SmartTapResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option('--x', type=int, required=True, help='X coordinate')
@click.option('--y', type=int, required=True, help='Y coordinate')
@click.option('--device', default=None, help='Device ID')
@click.option('--retry', type=int, default=DEFAULT_RETRY,
              help=f'Retry attempts (1-{MAX_RETRY})')
@click.option('--verify-text', default=None,
              help='Text to verify after tap')
@click.option('--timeout', type=int, default=DEFAULT_TIMEOUT,
              help=f'Verification timeout (1-{MAX_TIMEOUT}s)')
@click.option('--json', 'output_json', is_flag=True, help='JSON output')
def cli(x: int, y: int, device: str, retry: int, verify_text: str,
        timeout: int, output_json: bool) -> None:
    """
    Smart tap with retry logic and verification.

    Automatically retries on failure and verifies success after tap.
    """
    if not (1 <= retry <= MAX_RETRY):
        click.echo(f"❌ Error: retry must be 1-{MAX_RETRY}", err=True)
        sys.exit(3)

    if not (1 <= timeout <= MAX_TIMEOUT):
        click.echo(f"❌ Error: timeout must be 1-{MAX_TIMEOUT}s", err=True)
        sys.exit(3)

    result = SmartTapResult(device="", tap={"x": x, "y": y})

    try:
        selected_device = device or get_device()
        result.device = selected_device

        for attempt in range(1, retry + 1):
            result.attempt = attempt
            try:
                tap_device(selected_device, x, y)
                result.success = True
                break
            except RuntimeError as e:
                if attempt == retry:
                    result.error = str(e)
                    raise
                time.sleep(RETRY_DELAY)

        if result.success and verify_text:
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
