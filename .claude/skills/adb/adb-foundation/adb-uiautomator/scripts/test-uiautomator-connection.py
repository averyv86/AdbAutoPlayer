#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
Test uiautomator2 Installation and Device Connection

Verify that uiautomator2 is properly installed and can connect to an Android device.
Tests basic operations like getting device info and testing element detection.

Usage:
    uv run test-uiautomator-connection.py
    uv run test-uiautomator-connection.py --device 127.0.0.1:5555 --verbose
    uv run test-uiautomator-connection.py --list-devices

Exit Codes:
    0 - Success (device connected and operational)
    1 - Warning (device found but some operations failed)
    2 - Error (cannot connect to device)
    3 - Critical (invalid parameters or installation issue)
"""

import click
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class ConnectionTest:
    """Result of connection test"""
    success: bool
    device_id: Optional[str] = None
    device_model: Optional[str] = None
    device_serial: Optional[str] = None
    screen_resolution: Optional[str] = None
    android_version: Optional[str] = None
    uiautomator_works: bool = False
    element_detection_works: bool = False
    tests_passed: int = 0
    tests_failed: int = 0
    error: Optional[str] = None


def import_uiautomator2():
    """Safely import uiautomator2"""
    try:
        import uiautomator2 as u2
        return u2
    except ImportError as e:
        return None


def list_devices():
    """List all connected ADB devices"""
    try:
        from adbutils import adb
        devices = adb.device_list()
        return devices
    except Exception as e:
        return None


def test_device_info(device, verbose: bool = False):
    """Get device information"""
    try:
        info = device.info
        if verbose:
            click.echo(f"✓ Device Info: {info}", err=True)
        return info
    except Exception as e:
        if verbose:
            click.echo(f"✗ Failed to get device info: {e}", err=True)
        return None


def test_screen_resolution(device, verbose: bool = False):
    """Get screen resolution"""
    try:
        # Get resolution from device info
        info = device.info
        width = info.get('displayWidth', 0)
        height = info.get('displayHeight', 0)
        resolution = f"{width}x{height}"
        if verbose:
            click.echo(f"✓ Screen Resolution: {resolution}", err=True)
        return resolution
    except Exception as e:
        if verbose:
            click.echo(f"✗ Failed to get screen resolution: {e}", err=True)
        return None


def test_screenshot(device, verbose: bool = False):
    """Test screenshot capability"""
    try:
        img = device.screenshot()
        if img is not None:
            if verbose:
                click.echo(f"✓ Screenshot works (size: {img.size})", err=True)
            return True
        return False
    except Exception as e:
        if verbose:
            click.echo(f"✗ Screenshot failed: {e}", err=True)
        return False


def test_element_detection(device, verbose: bool = False):
    """Test element detection on home screen"""
    try:
        # Try to find any button on screen (generic test)
        elements = device(className="android.widget.Button")
        if elements.exists():
            if verbose:
                click.echo(f"✓ Element detection works (found button)", err=True)
            return True
        else:
            if verbose:
                click.echo(f"⚠ No button elements found (may be normal for current screen)", err=True)
            return True  # Not a failure, just no buttons on screen
    except Exception as e:
        if verbose:
            click.echo(f"✗ Element detection failed: {e}", err=True)
        return False


def test_accessibility_tree(device, verbose: bool = False):
    """Test accessibility tree dump"""
    try:
        dump = device.dump_hierarchy()
        if dump and len(dump) > 0:
            if verbose:
                click.echo(f"✓ Accessibility tree dump works (elements: {len(dump)})", err=True)
            return True
        return False
    except Exception as e:
        if verbose:
            click.echo(f"✗ Accessibility tree dump failed: {e}", err=True)
        return False


@click.command()
@click.option('--device', type=str, default='127.0.0.1:5555', help='Device ID')
@click.option('--list-devices', 'should_list_devices', is_flag=True, help='List all connected devices and exit')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def cli(device: str, should_list_devices: bool, output_json: bool, verbose: bool) -> None:
    """
    Test uiautomator2 installation and device connectivity.
    """
    # Import check
    u2 = import_uiautomator2()
    if u2 is None:
        result = ConnectionTest(
            success=False,
            error="uiautomator2 is not installed. Install with: pip install uiautomator2"
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {result.error}", err=True)
        sys.exit(3)

    # List devices mode
    if should_list_devices:
        click.echo("Available devices:")
        devices = list_devices()
        if devices:
            for dev in devices:
                click.echo(f"  - {dev}")
        else:
            click.echo("  No devices found")
        sys.exit(0)

    # Connection test mode
    if verbose:
        click.echo(f"Connecting to device: {device}", err=True)

    try:
        # Connect to device
        d = u2.connect(device)
        if d is None:
            result = ConnectionTest(
                success=False,
                device_id=device,
                error=f"Failed to connect to device {device}"
            )
            if output_json:
                click.echo(json.dumps(asdict(result)))
            else:
                click.echo(f"✗ Failed to connect to {device}", err=True)
            sys.exit(2)

        # Run tests
        result = ConnectionTest(
            success=True,
            device_id=device
        )

        # Test 1: Device info
        if verbose:
            click.echo("\n[Test 1/5] Getting device info...", err=True)
        info = test_device_info(d, verbose)
        if info:
            result.device_model = info.get('model')
            result.device_serial = info.get('serialno')
            result.android_version = info.get('release')
            result.tests_passed += 1
        else:
            result.tests_failed += 1

        # Test 2: Screen resolution
        if verbose:
            click.echo("[Test 2/5] Getting screen resolution...", err=True)
        resolution = test_screen_resolution(d, verbose)
        if resolution:
            result.screen_resolution = resolution
            result.tests_passed += 1
        else:
            result.tests_failed += 1

        # Test 3: Screenshot
        if verbose:
            click.echo("[Test 3/5] Testing screenshot...", err=True)
        if test_screenshot(d, verbose):
            result.tests_passed += 1
        else:
            result.tests_failed += 1

        # Test 4: Element detection
        if verbose:
            click.echo("[Test 4/5] Testing element detection...", err=True)
        if test_element_detection(d, verbose):
            result.element_detection_works = True
            result.tests_passed += 1
        else:
            result.tests_failed += 1

        # Test 5: Accessibility tree
        if verbose:
            click.echo("[Test 5/5] Testing accessibility tree...", err=True)
        if test_accessibility_tree(d, verbose):
            result.uiautomator_works = True
            result.tests_passed += 1
        else:
            result.tests_failed += 1

        # Output results
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo("\n" + "="*60, err=True)
            click.echo("✓ Device Connection Test Results", err=True)
            click.echo("="*60, err=True)
            if result.device_model:
                click.echo(f"  Device: {result.device_model}")
            if result.device_serial:
                click.echo(f"  Serial: {result.device_serial}")
            if result.android_version:
                click.echo(f"  Android: {result.android_version}")
            if result.screen_resolution:
                click.echo(f"  Resolution: {result.screen_resolution}")
            click.echo(f"\n  Tests Passed: {result.tests_passed}/5")
            click.echo(f"  Tests Failed: {result.tests_failed}/5")
            click.echo("\n  Capabilities:")
            click.echo(f"    {'✓' if result.uiautomator_works else '✗'} UIAutomator2 Working")
            click.echo(f"    {'✓' if result.element_detection_works else '✗'} Element Detection")
            click.echo("="*60, err=True)

        # Exit code
        if result.tests_failed == 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        result = ConnectionTest(
            success=False,
            device_id=device,
            error=str(e)
        )
        if output_json:
            click.echo(json.dumps(asdict(result)))
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(2)


if __name__ == "__main__":
    cli()
