#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB Magisk Install App - Install Magisk Manager APK via adb install

Installs Magisk Manager APK on device via standard ADB install mechanism.
Supports force reinstall, verification, and proper error reporting.

Usage:
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/magisk/Magisk-v30.6.apk
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/Magisk-v30.6.apk --force
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/Magisk-v30.6.apk --verify
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/Magisk-v30.6.apk --json

Examples:
    # Basic install
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
        --apk-path /tmp/magisk/Magisk-v30.6.apk

    # Force reinstall (replace existing)
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
        --apk-path /tmp/magisk/Magisk-v30.6.apk --force

    # Verify app after install
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
        --apk-path /tmp/magisk/Magisk-v30.6.apk --verify

    # Get JSON output for integration
    uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
        --apk-path /tmp/magisk/Magisk-v30.6.apk --json

Exit Codes:
    0 - Success (app installed)
    1 - Warning (app installed but verification incomplete)
    2 - Error (installation failed)
    3 - Critical (invalid APK or device)
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
MAGISK_ACTIVITY = f"{MAGISK_PACKAGE}/.ui.MainActivity"
ADB_COMMAND = "adb"
INSTALL_TIMEOUT = 60

# ========== SECTION 4: DATA MODELS ==========
@dataclass
class AppInstallResult:
    """Result of Magisk app installation."""
    device_id: str
    success: bool
    apk_path: str = ""
    app_installed: bool = False
    verification_passed: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 5: HELPER FUNCTIONS ==========
def verify_apk_file(apk_path: str) -> bool:
    """Verify APK file exists and is readable."""
    path = Path(apk_path)
    return path.exists() and path.is_file() and path.stat().st_size > 0

def install_apk_on_device(device_id: str, apk_path: str, force: bool = False) -> tuple[bool, Optional[str]]:
    """Install APK on device via adb install."""
    try:
        cmd = [ADB_COMMAND, "-s", device_id, "install"]

        if force:
            cmd.append("-r")  # Replace existing app

        cmd.append(apk_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=INSTALL_TIMEOUT
        )

        # Check for success markers
        if result.returncode == 0 and "Success" in result.stdout:
            return True, None

        # Check for error messages
        if "INSTALL_FAILED" in result.stdout or "Error" in result.stderr:
            error_msg = result.stdout or result.stderr
            return False, error_msg

        return result.returncode == 0, None

    except subprocess.TimeoutExpired:
        return False, "Installation timeout (>60s)"
    except Exception as e:
        return False, str(e)

def check_app_installed(device_id: str) -> bool:
    """Check if Magisk app is installed on device."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "shell", "pm", "list", "packages", MAGISK_PACKAGE],
            capture_output=True,
            text=True,
            timeout=10
        )
        return MAGISK_PACKAGE in result.stdout
    except Exception:
        return False

def verify_app_launch(device_id: str, timeout: float = 15) -> bool:
    """Verify Magisk app can launch."""
    try:
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "am", "start",
            "-n", MAGISK_ACTIVITY
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Error" not in result.stderr and result.returncode == 0
    except Exception:
        return False

# ========== SECTION 6: CORE LOGIC ==========
def install_app(device_id: str, apk_path: str, force: bool = False,
               verify: bool = False) -> AppInstallResult:
    """Install Magisk Manager APK."""
    start_time = time.time()
    result = AppInstallResult(
        device_id=device_id,
        success=False,
        apk_path=apk_path,
        timestamp=start_time
    )

    # Step 1: Verify APK file
    if not verify_apk_file(apk_path):
        result.error = f"APK file not found or invalid: {apk_path}"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    # Step 2: Install APK
    app_installed, install_error = install_apk_on_device(device_id, apk_path, force=force)
    result.app_installed = app_installed

    if not app_installed:
        result.error = f"Installation failed: {install_error}"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 3: Verify installation if requested
    if verify:
        # Wait a bit for package manager to update
        time.sleep(1)

        if check_app_installed(device_id):
            # Try to launch app
            time.sleep(1)
            if verify_app_launch(device_id):
                result.verification_passed = True
                result.exit_code = 0
            else:
                result.error = "App installed but failed to launch"
                result.exit_code = 1
        else:
            result.error = "App installation not detected by pm list packages"
            result.exit_code = 1
    else:
        result.verification_passed = True
        result.exit_code = 0

    result.success = result.app_installed and result.verification_passed
    result.duration = time.time() - start_time

    return result

# ========== SECTION 7: FORMATTERS ==========
def format_human_output(result: AppInstallResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Magisk Manager installed on {result.device_id}")
    else:
        lines.append(f"❌ Failed to install Magisk Manager on {result.device_id}")

    lines.append(f"  APK: {result.apk_path}")
    lines.append(f"  Installation: {'✅ Yes' if result.app_installed else '❌ No'}")

    if result.verification_passed:
        lines.append(f"  Verification: ✅ Passed")
    elif result.app_installed:
        lines.append(f"  Verification: ⚠️  Not verified")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: AppInstallResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    required=True,
    help='Target device ID (e.g., 127.0.0.1:5555)'
)
@click.option(
    '--apk-path',
    type=str,
    required=True,
    help='Path to Magisk APK file'
)
@click.option(
    '--force',
    is_flag=True,
    help='Force reinstall (replace existing)'
)
@click.option(
    '--verify',
    is_flag=True,
    help='Verify app after installation'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: str, apk_path: str, force: bool, verify: bool,
        output_json: bool) -> None:
    """
    Install Magisk Manager APK on device.

    Installs the Magisk Manager APK via adb install with optional
    force reinstall and verification of successful installation.

    Examples:
        uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
            --apk-path /tmp/Magisk-v30.6.apk
        uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \\
            --apk-path /tmp/Magisk-v30.6.apk --force --verify
    """
    # Install app
    result = install_app(
        device_id=device,
        apk_path=apk_path,
        force=force,
        verify=verify
    )

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
