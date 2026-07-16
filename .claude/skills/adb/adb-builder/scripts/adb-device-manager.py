#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.0.0",
#     "tabulate>=0.9.0",
# ]
# ///
"""
adb-device-manager: Unified ADB Device Management Utility

TRUST 5 Principles:
  1. Transparency - Clear status reporting and error messages
  2. Reliability - Robust error handling and retries
  3. Usability - Simple, intuitive CLI interface
  4. Security - Safe operation with validation
  5. Testability - Comprehensive logging and verification

Provides unified interface for:
  - Listing connected devices
  - Device connection management
  - Device properties inspection
  - Device state validation
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Device:
    """Device information"""
    serial: str
    state: str
    device_type: str
    api_level: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None


class DeviceManager:
    """Unified ADB device management"""

    def __init__(self):
        self.devices: List[Device] = []
        self.errors: List[str] = []

    def list_devices(self, verbose: bool = False) -> List[Device]:
        """List all connected devices with optional verbose info"""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.errors.append(f"Failed to list devices: {result.stderr}")
                return []

            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = []

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                serial = parts[0]
                state = parts[1]

                device = Device(
                    serial=serial,
                    state=state,
                    device_type=self._get_device_type(serial)
                )

                if verbose:
                    device.api_level = self._get_api_level(serial)
                    device.model = self._get_property(serial, "ro.product.model")
                    device.manufacturer = self._get_property(serial, "ro.product.manufacturer")

                devices.append(device)

            self.devices = devices
            return devices

        except subprocess.TimeoutExpired:
            self.errors.append("Device listing timeout")
            return []

    def connect_device(self, host: str, port: int = 5555) -> bool:
        """Connect to TCP ADB device"""
        try:
            result = subprocess.run(
                ["adb", "connect", f"{host}:{port}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True
            else:
                self.errors.append(f"Connection failed: {result.stderr}")
                return False

        except Exception as e:
            self.errors.append(f"Connection error: {str(e)}")
            return False

    def disconnect_device(self, serial: str) -> bool:
        """Disconnect from device"""
        try:
            result = subprocess.run(
                ["adb", "disconnect", serial],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.errors.append(f"Disconnection error: {str(e)}")
            return False

    def get_device_info(self, serial: str) -> Dict[str, str]:
        """Get detailed device information"""
        return {
            "Serial": serial,
            "API Level": self._get_api_level(serial),
            "Model": self._get_property(serial, "ro.product.model"),
            "Manufacturer": self._get_property(serial, "ro.product.manufacturer"),
            "Android Version": self._get_property(serial, "ro.build.version.release"),
            "Build ID": self._get_property(serial, "ro.build.id"),
            "Device Name": self._get_property(serial, "ro.device"),
        }

    def _get_device_type(self, serial: str) -> str:
        """Determine device type (emulator or physical)"""
        if "emulator" in serial:
            return "emulator"
        elif "127.0.0.1" in serial:
            return "remote"
        else:
            return "device"

    def _get_api_level(self, serial: str) -> Optional[str]:
        """Get Android API level"""
        return self._get_property(serial, "ro.build.version.sdk")

    def _get_property(self, serial: str, prop: str) -> Optional[str]:
        """Get device property via adb shell"""
        try:
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", prop],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "N/A"
        except:
            return "N/A"


def format_device_table(devices: List[Device]) -> str:
    """Format devices as ASCII table"""
    try:
        from tabulate import tabulate
        headers = ["Serial", "State", "Type"]
        rows = [[d.serial, d.state, d.device_type] for d in devices]
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        # Fallback without tabulate
        lines = ["Serial\tState\tType"]
        for d in devices:
            lines.append(f"{d.serial}\t{d.state}\t{d.device_type}")
        return "\n".join(lines)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: adb-device-manager.py [list|connect|disconnect|info]")
        return 1

    manager = DeviceManager()
    command = sys.argv[1]

    if command == "list":
        verbose = "--verbose" in sys.argv or "-v" in sys.argv
        devices = manager.list_devices(verbose=verbose)

        print(f"\n📱 Connected Devices ({len(devices)}):\n")
        print(format_device_table(devices))

        if verbose:
            for device in devices:
                print(f"\n📋 {device.serial}:")
                info = manager.get_device_info(device.serial)
                for key, value in info.items():
                    print(f"  {key}: {value}")

    elif command == "connect":
        if len(sys.argv) < 3:
            print("Usage: adb-device-manager.py connect <host> [port]")
            return 1

        host = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 5555

        print(f"Connecting to {host}:{port}...")
        if manager.connect_device(host, port):
            print(f"✅ Connected successfully")
        else:
            print(f"❌ Connection failed: {manager.errors[0] if manager.errors else 'Unknown error'}")
            return 1

    elif command == "disconnect":
        if len(sys.argv) < 3:
            print("Usage: adb-device-manager.py disconnect <serial>")
            return 1

        serial = sys.argv[2]
        if manager.disconnect_device(serial):
            print(f"✅ Disconnected {serial}")
        else:
            print(f"❌ Disconnection failed")
            return 1

    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: adb-device-manager.py info <serial>")
            return 1

        serial = sys.argv[2]
        info = manager.get_device_info(serial)
        print(f"\n📋 Device Information: {serial}\n")
        for key, value in info.items():
            print(f"  {key}: {value}")

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
