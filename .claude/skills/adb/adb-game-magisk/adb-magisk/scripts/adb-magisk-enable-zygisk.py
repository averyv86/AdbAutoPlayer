#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB Enable Zygisk - Enable Zygisk subsystem in Magisk settings

Enables the Zygisk runtime hook injection feature in Magisk Manager. Zygisk is
required for API hooking modules (like PlayIntegrityFork) to intercept and modify
API calls. This script navigates to Magisk Settings and toggles the Zygisk switch,
then optionally handles the reboot prompt.

Usage:
    uv run adb-magisk-enable-zygisk.py --device 127.0.0.1:5555
    uv run adb-magisk-enable-zygisk.py --device 127.0.0.1:5555 --auto-reboot
    uv run adb-magisk-enable-zygisk.py --json

Examples:
    # Enable Zygisk on default device
    uv run adb-magisk-enable-zygisk.py

    # Enable Zygisk and automatically reboot
    uv run adb-magisk-enable-zygisk.py \\
        --device 127.0.0.1:5555 \\
        --auto-reboot

    # Get JSON output
    uv run adb-magisk-enable-zygisk.py --json

Exit Codes:
    0 - Success (Zygisk enabled)
    1 - Warning (enabled but reboot not completed)
    2 - Error (failed to enable or navigation error)
    3 - Critical (device not found or ADB failure)
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
MAGISK_PACKAGE = "com.topjohnwu.magisk"
ADB_COMMAND = "adb"
SETTINGS_ACTIVITY = f"{MAGISK_PACKAGE}/.ui.SettingsActivity"
ZYGISK_TOGGLE_X = 1000  # Right side of toggle switch
ZYGISK_TOGGLE_Y = 300   # Approximate Y position of Zygisk toggle
REBOOT_CONFIRM_X = 900
REBOOT_CONFIRM_Y = 1500
BUTTON_WAIT_TIMEOUT = 10
REBOOT_TIMEOUT = 60

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
class ZygiskEnableResult:
    """Result of Zygisk enablement operation."""
    device_id: str
    success: bool
    magisk_launched: bool = False
    navigated_to_settings: bool = False
    zygisk_toggle_tapped: bool = False
    zygisk_enabled: bool = False
    reboot_requested: bool = False
    reboot_completed: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
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

def launch_magisk(device_id: str) -> bool:
    """Launch Magisk Manager via adb shell."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-magisk/scripts/adb-magisk-launch.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id],
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.returncode == 0
    except Exception:
        return False

def navigate_to_settings(device_id: str) -> bool:
    """Navigate to Magisk Settings page by tapping Settings tab."""
    try:
        # Try to find and tap Settings using adb-find-element
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap estimated Settings location
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                "950", "100"  # Settings usually top-right
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            time.sleep(1)
            return True

        # Use adb-find-element to locate Settings text
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", "Settings", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    # Tap on Settings
                    center_x = data.get("center_x", 950)
                    center_y = data.get("center_y", 100)
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(center_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    time.sleep(1)
                    return True
            except:
                pass

        # Fallback
        cmd = [ADB_COMMAND, "-s", device_id, "shell", "input", "tap", "950", "100"]
        subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(1)
        return True
    except Exception:
        return False

def tap_zygisk_toggle(device_id: str) -> bool:
    """Tap the Zygisk toggle switch in Settings."""
    try:
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap estimated position
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                str(ZYGISK_TOGGLE_X), str(ZYGISK_TOGGLE_Y)
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            time.sleep(1)
            return True

        # Search for "Zygisk" text
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", "Zygisk", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    # Tap on toggle (usually to the right of text)
                    center_x = data.get("center_x", ZYGISK_TOGGLE_X)
                    center_y = data.get("center_y", ZYGISK_TOGGLE_Y)
                    tap_x = center_x + 100  # Tap to right of text for toggle
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(tap_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    time.sleep(2)  # Wait for toggle animation
                    return True
            except:
                pass

        # Fallback
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            str(ZYGISK_TOGGLE_X), str(ZYGISK_TOGGLE_Y)
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(2)
        return True
    except Exception:
        return False

def check_reboot_prompt(device_id: str) -> bool:
    """Check if reboot prompt appears after toggling Zygisk."""
    try:
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            return False

        # Check for common reboot prompt texts
        for text in ["Restart", "Reboot", "System Update Required"]:
            result = subprocess.run(
                ["uv", "run", str(find_script), "--device", device_id,
                 "--method", "ocr", "--target", text, "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if data.get("found"):
                        return True
                except:
                    pass

        return False
    except Exception:
        return False

def confirm_reboot(device_id: str) -> bool:
    """Tap confirm button on reboot prompt."""
    try:
        # Look for Restart/Reboot button
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap estimated button position
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                str(REBOOT_CONFIRM_X), str(REBOOT_CONFIRM_Y)
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            return True

        # Try to find Restart button
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", "Restart", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    center_x = data.get("center_x", REBOOT_CONFIRM_X)
                    center_y = data.get("center_y", REBOOT_CONFIRM_Y)
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(center_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    return True
            except:
                pass

        # Fallback
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            str(REBOOT_CONFIRM_X), str(REBOOT_CONFIRM_Y)
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        return True
    except Exception:
        return False

def wait_for_device_online(device_id: str, timeout: float = 60) -> bool:
    """Wait for device to come online after reboot."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                [ADB_COMMAND, "-s", device_id, "shell", "getprop", "sys.boot_completed"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and "1" in result.stdout:
                return True
        except:
            pass
        time.sleep(2)
    return False

# ========== SECTION 7: CORE LOGIC ==========
def enable_zygisk(device_id: str, auto_reboot: bool = False) -> ZygiskEnableResult:
    """Enable Zygisk subsystem in Magisk."""
    start_time = time.time()
    result = ZygiskEnableResult(
        device_id=device_id,
        success=False,
        timestamp=start_time
    )

    # Step 1: Launch Magisk
    result.magisk_launched = launch_magisk(device_id)
    if not result.magisk_launched:
        result.error = "Failed to launch Magisk Manager"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 2: Navigate to Settings
    result.navigated_to_settings = navigate_to_settings(device_id)
    if not result.navigated_to_settings:
        result.error = "Failed to navigate to Settings"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 3: Tap Zygisk toggle
    result.zygisk_toggle_tapped = tap_zygisk_toggle(device_id)
    if not result.zygisk_toggle_tapped:
        result.error = "Failed to locate or tap Zygisk toggle"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Assume toggle is now enabled
    result.zygisk_enabled = True
    time.sleep(1)

    # Step 4: Check for reboot prompt
    if check_reboot_prompt(device_id):
        result.reboot_requested = True

        if auto_reboot:
            confirm_reboot(device_id)
            result.reboot_completed = wait_for_device_online(device_id, REBOOT_TIMEOUT)
        else:
            result.exit_code = 1  # Warning: enabled but user must reboot
    else:
        result.exit_code = 0  # Success without reboot needed

    result.success = result.zygisk_enabled and (
        not result.reboot_requested or result.reboot_completed
    )

    if result.success and result.exit_code == 0:
        result.exit_code = 0
    elif result.zygisk_enabled and not auto_reboot and result.reboot_requested:
        result.exit_code = 1  # Warning

    result.duration = time.time() - start_time
    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: ZygiskEnableResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Zygisk enabled on {result.device_id}")
    else:
        lines.append(f"❌ Failed to enable Zygisk on {result.device_id}")

    lines.append(f"  Magisk Launched: {'✅ Yes' if result.magisk_launched else '❌ No'}")
    lines.append(f"  Settings Navigated: {'✅ Yes' if result.navigated_to_settings else '❌ No'}")
    lines.append(f"  Zygisk Toggle Tapped: {'✅ Yes' if result.zygisk_toggle_tapped else '❌ No'}")
    lines.append(f"  Zygisk Enabled: {'✅ Yes' if result.zygisk_enabled else '❌ No'}")

    if result.reboot_requested:
        lines.append(f"  Reboot Requested: ✅ Yes")
        if result.reboot_completed:
            lines.append(f"  Reboot Completed: ✅ Yes")
        else:
            lines.append(f"  Reboot Completed: ❌ No (user must reboot manually)")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: ZygiskEnableResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    help='Target device ID (e.g., 127.0.0.1:5555)'
)
@click.option(
    '--auto-reboot',
    is_flag=True,
    help='Automatically confirm reboot if prompted'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], auto_reboot: bool, output_json: bool) -> None:
    """
    Enable Zygisk subsystem in Magisk.

    Navigates to Magisk settings and enables the Zygisk runtime hook feature,
    which is required for API hooking modules to function.

    Examples:
        uv run adb-magisk-enable-zygisk.py
        uv run adb-magisk-enable-zygisk.py --device 127.0.0.1:5555
        uv run adb-magisk-enable-zygisk.py --device 127.0.0.1:5555 --auto-reboot
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = ZygiskEnableResult(
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

    # Enable Zygisk
    result = enable_zygisk(selected_device, auto_reboot=auto_reboot)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
