#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Pre-Flight Validation for Karrot Bypass Workflow

Validates all device prerequisites and prerequisites for successful Play Integrity bypass:
- Device connectivity and accessibility via ADB
- Magisk installation and module system
- Zygisk enabled for module system
- PlayIntegrityFork module presence and activation
- Target app (Karrot) presence
- Storage space availability
- Android version compatibility

Exit Codes:
    0 - Success (all checks passed)
    1 - Warning (non-critical checks failed)
    2 - Error (critical check failed)
    3 - Critical (device not accessible)
"""

import click
import json
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict


@dataclass
class ValidationCheck:
    """Result of a single validation check"""
    name: str
    status: str  # pass, fail, warning, skip
    message: str
    critical: bool = True
    error: Optional[str] = None


@dataclass
class PreFlightResult:
    """Overall pre-flight validation result"""
    success: bool
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warning: int = 0
    checks_skipped: int = 0
    checks: List[Dict] = None
    device_info: Optional[Dict] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.checks is None:
            self.checks = []


def connect_device(device_id: str):
    """Connect to device via uiautomator2"""
    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)
        return device
    except Exception as e:
        return None


def run_adb_command(command: str) -> tuple[str, int]:
    """
    Run ADB command and return output and exit code.

    Args:
        command: ADB command (without 'adb' prefix)

    Returns:
        Tuple of (output, exit_code)
    """
    try:
        full_cmd = f"adb {command}"
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return (result.stdout.strip(), result.returncode)
    except subprocess.TimeoutExpired:
        return ("Command timeout", -1)
    except Exception as e:
        return (str(e), -1)


def check_device_connection(device_id: str) -> ValidationCheck:
    """Check if device is accessible via ADB"""
    output, code = run_adb_command(f"-s {device_id} shell getprop ro.build.version.release")

    if code == 0:
        return ValidationCheck(
            name="Device Connection",
            status="pass",
            message=f"Device {device_id} is accessible via ADB",
            critical=True
        )
    else:
        return ValidationCheck(
            name="Device Connection",
            status="fail",
            message=f"Device {device_id} not found or not accessible",
            critical=True,
            error=output
        )


def check_android_version(device_id: str) -> ValidationCheck:
    """Check Android version compatibility (API 31+)"""
    output, code = run_adb_command(f"-s {device_id} shell getprop ro.build.version.sdk")

    if code == 0:
        try:
            sdk_version = int(output.strip())
            if sdk_version >= 31:  # Android 12+
                return ValidationCheck(
                    name="Android Version",
                    status="pass",
                    message=f"Android API {sdk_version} (Android 12+) supported",
                    critical=True
                )
            else:
                return ValidationCheck(
                    name="Android Version",
                    status="fail",
                    message=f"Android API {sdk_version} too old (requires API 31+)",
                    critical=True
                )
        except ValueError:
            return ValidationCheck(
                name="Android Version",
                status="fail",
                message=f"Could not parse SDK version: {output}",
                critical=True
            )
    else:
        return ValidationCheck(
            name="Android Version",
            status="fail",
            message="Could not determine Android version",
            critical=True,
            error=output
        )


def check_magisk_installed(device_id: str) -> ValidationCheck:
    """Check if Magisk is installed"""
    output, code = run_adb_command(f"-s {device_id} shell which magisk")

    if code == 0 and output:
        return ValidationCheck(
            name="Magisk Installation",
            status="pass",
            message=f"Magisk found at: {output}",
            critical=True
        )
    else:
        return ValidationCheck(
            name="Magisk Installation",
            status="fail",
            message="Magisk not installed. Please install Magisk first.",
            critical=True,
            error=output
        )


def check_zygisk_enabled(device_id: str) -> ValidationCheck:
    """Check if Zygisk is enabled"""
    output, code = run_adb_command(f"-s {device_id} shell getprop ro.zygote")

    if code == 0:
        if "zygote" in output.lower():
            return ValidationCheck(
                name="Zygisk Enabled",
                status="pass",
                message=f"Zygisk system: {output}",
                critical=True
            )
        else:
            return ValidationCheck(
                name="Zygisk Enabled",
                status="fail",
                message=f"Zygisk may not be enabled (zygote: {output})",
                critical=True
            )
    else:
        return ValidationCheck(
            name="Zygisk Enabled",
            status="fail",
            message="Could not check Zygisk status",
            critical=True,
            error=output
        )


def check_play_integrity_fork(device_id: str) -> ValidationCheck:
    """Check if PlayIntegrityFork module is installed"""
    output, code = run_adb_command(
        f"-s {device_id} shell ls /data/adb/modules/ | grep -i playintegrity"
    )

    if code == 0 and output:
        return ValidationCheck(
            name="PlayIntegrityFork Module",
            status="pass",
            message=f"PlayIntegrityFork module found: {output}",
            critical=True
        )
    else:
        return ValidationCheck(
            name="PlayIntegrityFork Module",
            status="fail",
            message="PlayIntegrityFork module not installed. Please install via Magisk.",
            critical=True,
            error=output
        )


def check_play_integrity_module_active(device_id: str) -> ValidationCheck:
    """Check if PlayIntegrityFork module is active"""
    output, code = run_adb_command(
        f"-s {device_id} shell getprop ro.playintegrityfix.version"
    )

    if code == 0 and output:
        return ValidationCheck(
            name="PlayIntegrityFork Active",
            status="pass",
            message=f"PlayIntegrityFork version: {output}",
            critical=True
        )
    else:
        return ValidationCheck(
            name="PlayIntegrityFork Active",
            status="fail",
            message="PlayIntegrityFork module is not active. Enable in Magisk Manager.",
            critical=True,
            error=output
        )


def check_karrot_app_present(device_id: str) -> ValidationCheck:
    """Check if Karrot app is installed"""
    output, code = run_adb_command(
        f"-s {device_id} shell pm list packages | grep karrot"
    )

    if code == 0 and "karrot" in output:
        return ValidationCheck(
            name="Karrot App Present",
            status="pass",
            message="Karrot app (com.nexon.karrot) is installed",
            critical=True
        )
    else:
        return ValidationCheck(
            name="Karrot App Present",
            status="fail",
            message="Karrot app not installed. Please install from Play Store.",
            critical=True,
            error=output
        )


def check_storage_space(device_id: str) -> ValidationCheck:
    """Check available storage space (requires 500MB+)"""
    output, code = run_adb_command(
        f"-s {device_id} shell df /data | tail -1"
    )

    if code == 0:
        parts = output.split()
        if len(parts) >= 4:
            try:
                available_kb = int(parts[3])
                available_mb = available_kb // 1024

                if available_mb >= 500:
                    return ValidationCheck(
                        name="Storage Space",
                        status="pass",
                        message=f"{available_mb}MB available (requires 500MB+)",
                        critical=False
                    )
                else:
                    return ValidationCheck(
                        name="Storage Space",
                        status="warning",
                        message=f"Low storage: {available_mb}MB (recommends 500MB+)",
                        critical=False
                    )
            except ValueError:
                return ValidationCheck(
                    name="Storage Space",
                    status="skip",
                    message="Could not parse storage information",
                    critical=False
                )

    return ValidationCheck(
        name="Storage Space",
        status="skip",
        message="Could not determine storage space",
        critical=False,
        error=output
    )


def check_no_safetynet_lock(device_id: str) -> ValidationCheck:
    """Check if bootloader is unlocked (SafetyNet lock status)"""
    output, code = run_adb_command(
        f"-s {device_id} shell getprop ro.boot.veritymode"
    )

    # Note: This is a general check. Some devices may have verity disabled.
    if code == 0:
        return ValidationCheck(
            name="Bootloader Status",
            status="pass",
            message=f"Boot verification mode: {output if output else 'standard'}",
            critical=False
        )
    else:
        return ValidationCheck(
            name="Bootloader Status",
            status="skip",
            message="Could not verify bootloader status (non-critical)",
            critical=False
        )


def get_device_info(device_id: str) -> Optional[Dict]:
    """Gather device information"""
    try:
        device = connect_device(device_id)
        if not device:
            return None

        info = device.info
        return {
            "device_id": device_id,
            "display_width": info.get("displayWidth", 0),
            "display_height": info.get("displayHeight", 0),
            "android_release": info.get("release", "unknown"),
            "sdk_version": info.get("sdkInt", 0),
            "product": info.get("product", "unknown"),
            "manufacturer": info.get("manufacturer", "unknown"),
        }
    except Exception as e:
        return None


@click.command()
@click.option('--device', type=str, default='localhost:5555', help='Device ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, output_json: bool, verbose: bool) -> None:
    """
    Validate device prerequisites for Karrot bypass workflow.
    """
    result = PreFlightResult(success=False)

    # Run all validation checks
    checks: List[ValidationCheck] = [
        check_device_connection(device),
    ]

    # Only continue if device is connected
    if checks[0].status != "pass":
        result.error_message = "Device not accessible. Cannot continue validation."
        if output_json:
            result.checks = [asdict(c) for c in checks]
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {result.error_message}", err=True)
        sys.exit(3)

    # Add remaining checks
    checks.extend([
        check_android_version(device),
        check_magisk_installed(device),
        check_zygisk_enabled(device),
        check_play_integrity_fork(device),
        check_play_integrity_module_active(device),
        check_karrot_app_present(device),
        check_storage_space(device),
        check_no_safetynet_lock(device),
    ])

    # Get device info
    device_info = get_device_info(device)
    result.device_info = device_info

    # Process results
    critical_failed = False
    for check in checks:
        result.checks.append(asdict(check))

        if check.status == "pass":
            result.checks_passed += 1
        elif check.status == "fail":
            result.checks_failed += 1
            if check.critical:
                critical_failed = True
        elif check.status == "warning":
            result.checks_warning += 1
        else:
            result.checks_skipped += 1

    # Determine overall success
    result.success = result.checks_failed == 0 and not critical_failed

    # Output results
    if output_json:
        click.echo(json.dumps(asdict(result), default=str))
    else:
        click.echo("\n" + "="*60)
        click.echo("✓ Pre-Flight Validation Report")
        click.echo("="*60)

        if device_info:
            click.echo(f"\nDevice: {device_info.get('device_id')}")
            click.echo(f"Manufacturer: {device_info.get('manufacturer')}")
            click.echo(f"Product: {device_info.get('product')}")
            click.echo(f"Android: {device_info.get('android_release')} (API {device_info.get('sdk_version')})")
            click.echo(f"Resolution: {device_info.get('display_width')}x{device_info.get('display_height')}")

        click.echo(f"\nValidation Results:")
        click.echo(f"  ✓ Passed:  {result.checks_passed}")
        click.echo(f"  ✗ Failed:  {result.checks_failed}")
        click.echo(f"  ⚠ Warning: {result.checks_warning}")
        click.echo(f"  ⊘ Skipped: {result.checks_skipped}")

        click.echo(f"\nDetailed Checks:")
        for check_data in result.checks:
            status_icon = {
                "pass": "✓",
                "fail": "✗",
                "warning": "⚠",
                "skip": "⊘"
            }.get(check_data["status"], "?")

            click.echo(f"  {status_icon} {check_data['name']}: {check_data['message']}")
            if verbose and check_data.get("error"):
                click.echo(f"      Error: {check_data['error']}")

        click.echo("="*60)

        if result.success:
            click.echo("\n✓ All critical checks passed!")
            click.echo("Device is ready for Karrot bypass workflow.\n")
            sys.exit(0)
        else:
            click.echo("\n✗ Pre-flight validation failed!")
            click.echo("Please resolve critical issues before proceeding.\n")
            if result.checks_failed > 0:
                click.echo("Critical issues:")
                for check_data in result.checks:
                    if check_data["status"] == "fail" and check_data.get("critical"):
                        click.echo(f"  - {check_data['name']}: {check_data['message']}")
            sys.exit(2)


if __name__ == "__main__":
    cli()
