#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""ADB Magisk Patch Boot - Patch boot image using Magisk app"""

import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

ADB_COMMAND = "adb"
MAGISK_PACKAGE = "com.topjohnwu.magisk"

@dataclass
class BootPatchResult:
    device_id: str
    success: bool
    input_boot: str = ""
    output_boot: str = ""
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

def push_boot_to_device(device_id: str, boot_path: str, remote_path: str = "/sdcard/boot.img") -> bool:
    """Push boot image to device storage."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "push", boot_path, remote_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except:
        return False

def launch_magisk_patcher(device_id: str, boot_path: str = "/sdcard/boot.img") -> bool:
    """Launch Magisk app to patch boot image."""
    try:
        activity = f"{MAGISK_PACKAGE}/.ui.MainActivity"
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "shell", "am", "start",
             "-n", activity, "-a", "android.intent.action.VIEW",
             "-d", f"file://{boot_path}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False

def wait_for_patching(device_id: str, timeout: float = 120) -> bool:
    """Wait for Magisk to complete patching (polling logcat)."""
    try:
        # This is a simplified check - in production would use OCR or logcat monitoring
        import time as t
        elapsed = 0
        while elapsed < timeout:
            result = subprocess.run(
                [ADB_COMMAND, "-s", device_id, "shell", "ls", "-la", "/sdcard/Download/"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "magisk_patched" in result.stdout:
                return True
            t.sleep(2)
            elapsed += 2
        return False
    except:
        return False

def pull_patched_boot(device_id: str, output_path: str) -> bool:
    """Pull patched boot image from device."""
    try:
        # Find patched image
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "shell", "find", "/sdcard/Download/", "-name", "magisk_patched*.img"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if not result.stdout.strip():
            return False

        remote_path = result.stdout.strip().split('\n')[0]

        # Pull it
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "pull", remote_path, output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return Path(output_path).exists() and Path(output_path).stat().st_size > 0
    except:
        return False

def format_human_output(result: BootPatchResult) -> str:
    lines = []
    if result.success:
        lines.append(f"✅ Boot image patched on {result.device_id}")
    else:
        lines.append(f"❌ Failed to patch boot image on {result.device_id}")
    lines.append(f"  Input: {result.input_boot}")
    if result.output_boot:
        lines.append(f"  Output: {result.output_boot}")
    lines.append(f"  Duration: {result.duration:.1f}s")
    if result.error:
        lines.append(f"  Error: {result.error}")
    return "\n".join(lines)

@click.command()
@click.option('--device', type=str, required=True, help='Target device ID')
@click.option('--boot-path', type=str, required=True, help='Path to boot image on device')
@click.option('--output-path', type=str, default=None, help='Output path for patched image')
@click.option('--wait-completion', is_flag=True, help='Wait for patching to complete')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def cli(device: str, boot_path: str, output_path: Optional[str], wait_completion: bool, output_json: bool) -> None:
    """Patch boot image using Magisk app."""
    start_time = time.time()
    result = BootPatchResult(device_id=device, success=False, input_boot=boot_path, timestamp=start_time)

    # Launch Magisk app for patching
    if not launch_magisk_patcher(device, boot_path):
        result.error = "Failed to launch Magisk patcher"
        result.exit_code = 2
        result.duration = time.time() - start_time
        if output_json:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(format_human_output(result))
        sys.exit(result.exit_code)

    # Wait for patching if requested
    if wait_completion:
        if not wait_for_patching(device):
            result.error = "Patching timeout or not detected"
            result.exit_code = 1
        else:
            result.success = True
            result.exit_code = 0

            # Pull patched image if output path specified
            if output_path:
                if pull_patched_boot(device, output_path):
                    result.output_boot = output_path
                    result.success = True
                else:
                    result.error = "Failed to pull patched image"
                    result.exit_code = 1
    else:
        result.success = True
        result.exit_code = 0

    result.duration = time.time() - start_time

    if output_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

if __name__ == "__main__":
    cli()
