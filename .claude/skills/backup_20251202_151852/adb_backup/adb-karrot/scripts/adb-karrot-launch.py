#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB Launch Karrot - Open Karrot application on device

Launches the Karrot app and optionally waits for specific UI elements (like login screen)
to appear before returning. The Karrot app is used for food delivery in South Korea
and we monitor its Play Integrity detection behavior.

Usage:
    uv run adb-karrot-launch.py
    uv run adb-karrot-launch.py --device 127.0.0.1:5555
    uv run adb-karrot-launch.py --wait-text "Login" --timeout 10
    uv run adb-karrot-launch.py --json

Examples:
    # Launch on default device
    uv run adb-karrot-launch.py

    # Specify device
    uv run adb-karrot-launch.py --device 192.168.1.100:5555

    # Wait for Login screen to appear
    uv run adb-karrot-launch.py \\
        --wait-text "Login" \\
        --timeout 15

    # Get JSON output
    uv run adb-karrot-launch.py --device 127.0.0.1:5555 --json

Exit Codes:
    0 - Success (app launched)
    1 - Warning (app launched but verification incomplete)
    2 - Error (app not launched or timeout)
    3 - Critical (invalid device or ADB failure)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

# ========== SECTION 3: CONSTANTS ==========
KARROT_PACKAGE = "kr.co.flo.karrot"
KARROT_ACTIVITY = f"{KARROT_PACKAGE}/.ui.MainActivity"
ADB_COMMAND = "adb"
LAUNCH_TIMEOUT = 10
VERIFICATION_TIMEOUT = 20  # Karrot takes longer to load

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class KarrotLaunchResult:
    """Result of Karrot app launch operation."""
    device_id: str
    success: bool
    app_launched: bool = False
    verification_passed: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
    wait_text: Optional[str] = None
    text_found: bool = False
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 6: HELPER FUNCTIONS ==========
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        devices = []
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id, state = line.split('\t')
                if state == 'device':
                    devices.append(device_id)
        return devices
    except Exception:
        return []

def select_device(device_arg: Optional[str] = None) -> tuple[str, bool]:
    """Select target device or use default."""
    if device_arg:
        return device_arg, True

    devices = get_adb_devices()
    if not devices:
        return None, False
    if len(devices) == 1:
        return devices[0], True
    return devices[0], True

def launch_karrot_app(device_id: str) -> bool:
    """Launch Karrot application via adb shell am start."""
    try:
        # First clear app data to ensure fresh start
        clear_cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "pm", "clear",
            KARROT_PACKAGE
        ]
        subprocess.run(clear_cmd, capture_output=True, timeout=5)
        time.sleep(1)

        # Launch app
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "am", "start",
            "-n", KARROT_ACTIVITY
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Error" not in result.stderr and result.returncode == 0
    except Exception as e:
        return False

def check_text_on_screen(device_id: str, search_text: str, timeout: float = 10) -> bool:
    """Check if text appears on screen using OCR via adb-ocr-extract.py."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-screen-detection/scripts/adb-ocr-extract.py"

        if not script_path.exists():
            return False

        # Use adb-ocr-extract to check for text
        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--json"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if "text_items" in data:
                    for item in data["text_items"]:
                        if search_text.lower() in item.get("text", "").lower():
                            return True
            except:
                pass

        return False
    except Exception:
        return False

# ========== SECTION 7: CORE LOGIC ==========
def launch_karrot(device_id: str, wait_text: Optional[str] = None,
                 timeout: float = VERIFICATION_TIMEOUT) -> KarrotLaunchResult:
    """Launch Karrot and optionally wait for verification."""
    start_time = time.time()
    result = KarrotLaunchResult(
        device_id=device_id,
        success=False,
        timestamp=start_time
    )

    # Step 1: Launch app
    app_launched = launch_karrot_app(device_id)
    result.app_launched = app_launched

    if not app_launched:
        result.error = "Failed to launch Karrot via adb shell am start"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 2: Wait for app to fully load
    time.sleep(3)  # Give app extra time to start

    # Step 3: Verify via text if requested
    if wait_text:
        result.wait_text = wait_text
        elapsed = 0
        poll_interval = 0.5
        max_wait = timeout

        while elapsed < max_wait:
            if check_text_on_screen(device_id, wait_text):
                result.text_found = True
                result.verification_passed = True
                break
            time.sleep(poll_interval)
            elapsed += poll_interval

        if not result.text_found:
            result.error = f"Timeout waiting for text '{wait_text}' (waited {timeout}s)"
            result.exit_code = 1  # Warning, app launched but verification failed
    else:
        # No verification requested, just confirm app launched
        result.verification_passed = True
        result.exit_code = 0

    result.success = result.app_launched and result.verification_passed
    result.duration = time.time() - start_time

    if result.success:
        result.exit_code = 0
    elif result.app_launched and not result.verification_passed:
        result.exit_code = 1  # Warning: app launched but verification incomplete
    else:
        result.exit_code = 2  # Error

    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: KarrotLaunchResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Karrot app launched on {result.device_id}")
    else:
        lines.append(f"❌ Failed to launch Karrot app on {result.device_id}")

    lines.append(f"  App Launched: {'✅ Yes' if result.app_launched else '❌ No'}")

    if result.wait_text:
        lines.append(f"  Waiting for: {result.wait_text}")
        lines.append(f"  Text Found: {'✅ Yes' if result.text_found else '❌ No'}")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: KarrotLaunchResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    help='Target device ID (e.g., 127.0.0.1:5555 or emulator-5554)'
)
@click.option(
    '--wait-text',
    type=str,
    help='Wait for this text to appear on screen (e.g., "Login")'
)
@click.option(
    '--timeout',
    type=float,
    default=VERIFICATION_TIMEOUT,
    help='Max seconds to wait for text (default: 20)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], wait_text: Optional[str], timeout: float,
        output_json: bool) -> None:
    """
    Launch Karrot application.

    Launches the Karrot app and optionally waits for UI elements to appear.
    The app will be launched with cleared data for fresh state.

    Examples:
        uv run adb-karrot-launch.py
        uv run adb-karrot-launch.py --device 127.0.0.1:5555
        uv run adb-karrot-launch.py --wait-text "Login" --timeout 20
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = KarrotLaunchResult(
            device_id="unknown",
            success=False,
            error="No connected ADB devices found",
            exit_code=3
        )
        if output_json:
            click.echo(format_json_output(error_result), err=True)
        else:
            click.echo(f"❌ Error: No connected ADB devices", err=True)
        sys.exit(3)

    # Launch Karrot
    result = launch_karrot(selected_device, wait_text=wait_text, timeout=timeout)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
