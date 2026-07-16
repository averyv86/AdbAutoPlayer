#!/usr/bin/env python3
"""
Test script for ADBKeyboard Korean text input setup.

This script helps verify that ADBKeyboard is properly installed and configured
for Korean text input on your Android device via ADB.

Usage:
    python test_korean_input.py [options]

Examples:
    python test_korean_input.py                    # Check setup status
    python test_korean_input.py --device 127.0.0.1:5555  # Specify device
    python test_korean_input.py --test-korean     # Test Korean input
    python test_korean_input.py --test-all        # Run all tests
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ADBKeyboardTester:
    """Test ADBKeyboard installation and functionality."""

    def __init__(self, device: str = None):
        """Initialize tester.

        Args:
            device: Optional device serial/IP:port. If None, uses first connected device.
        """
        self.device = device
        self.adb_cmd = ["adb"]
        if device:
            self.adb_cmd.extend(["-s", device])

    def run_adb(self, command: str, check: bool = False) -> str:
        """Execute ADB command and return output.

        Args:
            command: ADB shell command (without 'adb' prefix).
            check: If True, raise exception on error.

        Returns:
            str: Command output.
        """
        full_cmd = self.adb_cmd + ["shell"] + command.split()
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if check and result.returncode != 0:
                raise RuntimeError(f"Command failed: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {' '.join(full_cmd)}")
            return ""
        except Exception as e:
            logger.error(f"Error running ADB command: {e}")
            return ""

    def check_device_connected(self) -> bool:
        """Check if device is connected.

        Returns:
            bool: True if device is connected.
        """
        try:
            result = subprocess.run(
                self.adb_cmd + ["shell", "getprop", "ro.serialno"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False

    def check_adbkeyboard_installed(self) -> bool:
        """Check if ADBKeyboard is installed.

        Returns:
            bool: True if installed.
        """
        output = self.run_adb("pm list packages | grep adbkeyboard")
        return bool(output)

    def check_adbkeyboard_enabled(self) -> bool:
        """Check if ADBKeyboard is enabled.

        Returns:
            bool: True if enabled.
        """
        output = self.run_adb("ime list -a | grep AdbIME")
        return bool(output)

    def get_default_ime(self) -> str:
        """Get currently set default input method.

        Returns:
            str: Default IME package/class.
        """
        return self.run_adb("settings get secure default_input_method")

    def list_imes(self) -> list[str]:
        """List all available input methods.

        Returns:
            list: List of IME package names.
        """
        output = self.run_adb("ime list -a")
        imes = []
        for line in output.split("\n"):
            if ":" in line:
                ime = line.split(":")[0].strip()
                if ime:
                    imes.append(ime)
        return imes

    def test_broadcast(self, text: str) -> bool:
        """Test Unicode text input via broadcast.

        Args:
            text: Text to input.

        Returns:
            bool: True if broadcast sent.
        """
        try:
            escaped_text = text.replace("'", "\\'")
            cmd = f"am broadcast -a ADB_INPUT_TEXT --es msg '{escaped_text}'"
            full_cmd = self.adb_cmd + ["shell"] + [cmd]

            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )

            success = result.returncode == 0 and "Broadcasting" in result.stdout
            if success:
                logger.info(f"Broadcast sent successfully: {text}")
            else:
                logger.warning(f"Broadcast may have failed: {result.stdout}")

            return success

        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")
            return False

    def status_report(self) -> dict:
        """Generate status report.

        Returns:
            dict: Status information.
        """
        device_connected = self.check_device_connected()

        status = {
            "device_connected": device_connected,
            "adbkeyboard_installed": False,
            "adbkeyboard_enabled": False,
            "default_ime": "",
            "available_imes": [],
        }

        if not device_connected:
            logger.error("Device not connected!")
            return status

        status["adbkeyboard_installed"] = self.check_adbkeyboard_installed()
        status["adbkeyboard_enabled"] = self.check_adbkeyboard_enabled()
        status["default_ime"] = self.get_default_ime()
        status["available_imes"] = self.list_imes()

        return status

    def print_status(self):
        """Print formatted status report."""
        status = self.status_report()

        print("\n" + "=" * 60)
        print("ADBKeyboard Status Report")
        print("=" * 60)

        if not status["device_connected"]:
            print("ERROR: Device not connected!")
            return

        device_label = self.device or "(default)"
        print(f"Device: {device_label}")
        print(f"\nInstallation Status:")
        print(f"  ADBKeyboard Installed: {'✓ YES' if status['adbkeyboard_installed'] else '✗ NO'}")
        print(f"  ADBKeyboard Enabled:   {'✓ YES' if status['adbkeyboard_enabled'] else '✗ NO'}")

        print(f"\nInput Method Configuration:")
        print(f"  Default IME: {status['default_ime'] or '(not set)'}")
        print(f"  Available IMEs ({len(status['available_imes'])}):")
        for ime in status["available_imes"]:
            print(f"    - {ime}")

        print(f"\nSetup Status:")
        setup_complete = (
            status["adbkeyboard_installed"]
            and status["adbkeyboard_enabled"]
            and "adbkeyboard" in status["default_ime"].lower()
        )
        if setup_complete:
            print("  ✓ READY FOR KOREAN INPUT")
        else:
            print("  ✗ SETUP INCOMPLETE - Follow installation steps")

        print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test ADBKeyboard setup for Korean text input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_korean_input.py                    Check current status
  python test_korean_input.py --device 127.0.0.1:5555  Test specific device
  python test_korean_input.py --test-korean      Send Korean test text
  python test_korean_input.py --test-all         Run all tests
        """,
    )

    parser.add_argument(
        "-d",
        "--device",
        help="Device serial or IP:port (e.g., 127.0.0.1:5555)",
    )
    parser.add_argument(
        "--test-korean",
        action="store_true",
        help="Test Korean text input with '서초동'",
    )
    parser.add_argument(
        "--test-mixed",
        action="store_true",
        help="Test mixed English + Korean text",
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Run all tests",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    tester = ADBKeyboardTester(args.device)

    # Always show status first
    tester.print_status()

    # Run tests if requested
    if args.test_korean or args.test_all:
        print("Testing Korean input...")
        if tester.test_broadcast("서초동"):
            print("✓ Korean input test passed")
        else:
            print("✗ Korean input test failed")

        time.sleep(0.5)

    if args.test_mixed or args.test_all:
        print("Testing mixed input...")
        if tester.test_broadcast("Test 테스트 123"):
            print("✓ Mixed input test passed")
        else:
            print("✗ Mixed input test failed")

        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
