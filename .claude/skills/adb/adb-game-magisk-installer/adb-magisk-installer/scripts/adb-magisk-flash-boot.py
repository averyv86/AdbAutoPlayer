#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""ADB Magisk Flash Boot - Flash patched boot image via fastboot"""

import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

ADB_COMMAND = "adb"
FASTBOOT_COMMAND = "fastboot"

@dataclass
class BootFlashResult:
    device_id: str
    success: bool
    boot_path: str = ""
    partition: str = "boot"
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

def verify_boot_file(boot_path: str) -> tuple[bool, Optional[str]]:
    """Verify boot image file exists and is valid."""
    path = Path(boot_path)
    if not path.exists():
        return False, "Boot image file not found"
    if path.stat().st_size == 0:
        return False, "Boot image file is empty"
    if path.stat().st_size < 1000000:  # Less than 1MB seems wrong
        return False, "Boot image file seems too small"
    return True, None

def get_fastboot_device(device_id: str) -> Optional[str]:
    """Get fastboot device identifier."""
    try:
        result = subprocess.run(
            [FASTBOOT_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'fastboot' in line:
                return line.split('\t')[0]
        return device_id
    except:
        return device_id

def flash_boot_image(device_id: str, boot_path: str, partition: str = "boot") -> tuple[bool, Optional[str]]:
    """Flash boot image via fastboot."""
    try:
        result = subprocess.run(
            [FASTBOOT_COMMAND, "-s", device_id, "flash", partition, boot_path],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0 and ("Finished" in result.stdout or "finished" in result.stdout):
            return True, None
        else:
            return False, result.stdout or result.stderr

    except subprocess.TimeoutExpired:
        return False, "Flash operation timeout"
    except Exception as e:
        return False, str(e)

def reboot_device(device_id: str) -> bool:
    """Reboot device from fastboot."""
    try:
        result = subprocess.run(
            [FASTBOOT_COMMAND, "-s", device_id, "reboot"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False

def wait_for_device_boot(device_id: str, timeout: float = 60) -> bool:
    """Wait for device to boot after reboot."""
    try:
        elapsed = 0
        while elapsed < timeout:
            result = subprocess.run(
                [ADB_COMMAND, "-s", device_id, "shell", "getprop", "sys.boot_completed"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "1" in result.stdout:
                return True
            time.sleep(2)
            elapsed += 2
        return False
    except:
        return False

def format_human_output(result: BootFlashResult) -> str:
    lines = []
    if result.success:
        lines.append(f"✅ Boot image flashed on {result.device_id}")
    else:
        lines.append(f"❌ Failed to flash boot image on {result.device_id}")
    lines.append(f"  Partition: {result.partition}")
    lines.append(f"  Image: {result.boot_path}")
    lines.append(f"  Duration: {result.duration:.1f}s")
    if result.error:
        lines.append(f"  Error: {result.error}")
    return "\n".join(lines)

@click.command()
@click.option('--device', type=str, required=True, help='Target device ID')
@click.option('--boot-path', type=str, required=True, help='Path to patched boot image')
@click.option('--partition', type=str, default='boot', help='Target partition (boot, boot_a, boot_b)')
@click.option('--verify', is_flag=True, help='Verify before flashing')
@click.option('--reboot', is_flag=True, help='Reboot after flashing')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def cli(device: str, boot_path: str, partition: str, verify: bool, reboot: bool, output_json: bool) -> None:
    """Flash patched boot image via fastboot."""
    start_time = time.time()
    result = BootFlashResult(device_id=device, success=False, boot_path=boot_path, partition=partition, timestamp=start_time)

    # Verify boot file
    if verify:
        valid, error = verify_boot_file(boot_path)
        if not valid:
            result.error = error
            result.exit_code = 3
            result.duration = time.time() - start_time
            if output_json:
                click.echo(json.dumps(result.to_dict(), indent=2))
            else:
                click.echo(format_human_output(result))
            sys.exit(result.exit_code)

    # Flash boot image
    success, error = flash_boot_image(device, boot_path, partition)
    result.success = success
    result.error = error
    result.exit_code = 0 if success else 2

    # Reboot if requested
    if success and reboot:
        if reboot_device(device):
            if wait_for_device_boot(device):
                result.success = True
            else:
                result.error = "Device failed to boot after reboot"
                result.exit_code = 1
        else:
            result.error = "Reboot failed"
            result.exit_code = 1

    result.duration = time.time() - start_time

    if output_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

if __name__ == "__main__":
    cli()
