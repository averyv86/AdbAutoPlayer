#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""ADB Magisk Extract Boot - Extract boot.img from device via adb pull"""

import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

ADB_COMMAND = "adb"

@dataclass
class BootExtractResult:
    device_id: str
    success: bool
    boot_path: str = ""
    partition: str = "boot"
    size_bytes: int = 0
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

def get_active_partition(device_id: str) -> str:
    """Detect active boot partition (boot_a or boot_b)."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "shell", "getprop", "ro.boot.slot_suffix"],
            capture_output=True,
            text=True,
            timeout=5
        )
        suffix = result.stdout.strip()
        if suffix in ["_a", "_b"]:
            return f"boot{suffix}"
        return "boot"
    except:
        return "boot"

def extract_boot_image(device_id: str, output_path: str, partition: Optional[str] = None) -> tuple[bool, Optional[str], int]:
    """Extract boot image from device."""
    try:
        if not partition:
            partition = get_active_partition(device_id)

        # Pull from device
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "pull", f"/dev/block/by-name/{partition}", output_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = Path(output_path)
        if output.exists() and output.stat().st_size > 0:
            return True, None, output.stat().st_size
        else:
            return False, "Boot image file empty or not created", 0

    except subprocess.TimeoutExpired:
        return False, "Extraction timeout", 0
    except Exception as e:
        return False, str(e), 0

def format_human_output(result: BootExtractResult) -> str:
    lines = []
    if result.success:
        lines.append(f"✅ Boot image extracted from {result.device_id}")
    else:
        lines.append(f"❌ Failed to extract boot image from {result.device_id}")
    lines.append(f"  Partition: {result.partition}")
    lines.append(f"  Output: {result.boot_path}")
    if result.size_bytes > 0:
        lines.append(f"  Size: {result.size_bytes / (1024*1024):.1f} MB")
    lines.append(f"  Duration: {result.duration:.1f}s")
    if result.error:
        lines.append(f"  Error: {result.error}")
    return "\n".join(lines)

@click.command()
@click.option('--device', type=str, required=True, help='Target device ID')
@click.option('--output-path', type=str, required=True, help='Output path for boot image')
@click.option('--partition', type=str, default=None, help='Boot partition (boot_a or boot_b)')
@click.option('--verify', is_flag=True, help='Verify integrity')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def cli(device: str, output_path: str, partition: Optional[str], verify: bool, output_json: bool) -> None:
    """Extract boot image from device."""
    start_time = time.time()
    result = BootExtractResult(device_id=device, success=False, boot_path=output_path, timestamp=start_time)

    success, error, size = extract_boot_image(device, output_path, partition)
    result.success = success
    result.error = error
    result.size_bytes = size
    result.exit_code = 0 if success else 2
    result.duration = time.time() - start_time

    if output_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

if __name__ == "__main__":
    cli()
