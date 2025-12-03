# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pure-python-adb>=0.3.0",
# ]
# ///
"""
ADB Karrot Multi-Device Control

This script provides multi-device control for Karrot automation,
supporting parallel execution across multiple Android devices.

Features:
- List connected devices with detailed status
- Execute commands on specific device
- Parallel execution across all devices
- Device health checking
- Automatic device discovery

Usage:
    uv run adb-karrot-multi-device.py --list
    uv run adb-karrot-multi-device.py --device 127.0.0.1:5555 --command "input tap 720 2374"
    uv run adb-karrot-multi-device.py --all --command "input keyevent KEYCODE_HOME"
    uv run adb-karrot-multi-device.py --health
"""

import argparse
import concurrent.futures
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from ppadb.client import Client as AdbClient


class DeviceState(Enum):
    """Device connection state."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """Device information container."""
    serial: str
    state: DeviceState
    model: Optional[str] = None
    product: Optional[str] = None
    device_name: Optional[str] = None
    android_version: Optional[str] = None
    sdk_version: Optional[str] = None
    resolution: Optional[str] = None
    battery_level: Optional[int] = None

    def __str__(self) -> str:
        parts = [f"{self.serial} ({self.state.value})"]
        if self.model:
            parts.append(f"Model: {self.model}")
        if self.android_version:
            parts.append(f"Android: {self.android_version}")
        if self.resolution:
            parts.append(f"Resolution: {self.resolution}")
        if self.battery_level is not None:
            parts.append(f"Battery: {self.battery_level}%")
        return " | ".join(parts)


@dataclass
class CommandResult:
    """Result of command execution on a device."""
    device_serial: str
    success: bool
    output: str
    error: Optional[str] = None
    duration_ms: float = 0.0


class MultiDeviceController:
    """Controller for managing multiple ADB devices."""

    def __init__(self, adb_host: str = "127.0.0.1", adb_port: int = 5037):
        self.adb_host = adb_host
        self.adb_port = adb_port
        self._client: Optional[AdbClient] = None

    def _get_client(self) -> AdbClient:
        """Get or create ADB client."""
        if self._client is None:
            self._client = AdbClient(host=self.adb_host, port=self.adb_port)
        return self._client

    def connect_device(self, host: str, port: int = 5555) -> bool:
        """Connect to a device over TCP/IP."""
        try:
            client = self._get_client()
            client.remote_connect(host, port)
            return True
        except Exception as e:
            print(f"Failed to connect to {host}:{port}: {e}")
            return False

    def disconnect_device(self, serial: str) -> bool:
        """Disconnect a device."""
        try:
            if ":" in serial:
                host, port = serial.rsplit(":", 1)
                client = self._get_client()
                client.remote_disconnect(host, int(port))
            return True
        except Exception as e:
            print(f"Failed to disconnect {serial}: {e}")
            return False

    def list_devices(self, detailed: bool = False) -> list:
        """List all connected devices."""
        try:
            client = self._get_client()
            devices = client.devices()

            device_infos = []
            for device in devices:
                info = DeviceInfo(
                    serial=device.serial,
                    state=DeviceState.ONLINE,
                )

                if detailed:
                    try:
                        # Get device properties
                        info.model = self._get_prop(device, "ro.product.model")
                        info.product = self._get_prop(device, "ro.product.name")
                        info.device_name = self._get_prop(device, "ro.product.device")
                        info.android_version = self._get_prop(device, "ro.build.version.release")
                        info.sdk_version = self._get_prop(device, "ro.build.version.sdk")
                        info.resolution = self._get_resolution(device)
                        info.battery_level = self._get_battery_level(device)
                    except Exception:
                        pass  # Non-critical failures

                device_infos.append(info)

            return device_infos

        except Exception as e:
            print(f"Failed to list devices: {e}")
            return []

    def _get_prop(self, device, prop: str) -> Optional[str]:
        """Get a device property."""
        try:
            result = device.shell(f"getprop {prop}").strip()
            return result if result else None
        except Exception:
            return None

    def _get_resolution(self, device) -> Optional[str]:
        """Get device resolution."""
        try:
            result = device.shell("wm size")
            if "Physical size:" in result:
                return result.split("Physical size:")[-1].strip()
            elif "x" in result:
                return result.strip()
            return None
        except Exception:
            return None

    def _get_battery_level(self, device) -> Optional[int]:
        """Get device battery level."""
        try:
            result = device.shell("dumpsys battery | grep level")
            if "level:" in result:
                level_str = result.split("level:")[-1].strip()
                return int(level_str)
            return None
        except Exception:
            return None

    def execute_command(
        self,
        serial: str,
        command: str,
        timeout: float = 30.0,
    ) -> CommandResult:
        """Execute a shell command on a specific device."""
        start_time = time.time()

        try:
            client = self._get_client()
            device = client.device(serial)

            if device is None:
                return CommandResult(
                    device_serial=serial,
                    success=False,
                    output="",
                    error=f"Device {serial} not found",
                )

            # Execute command
            output = device.shell(command, timeout=int(timeout))
            duration = (time.time() - start_time) * 1000

            return CommandResult(
                device_serial=serial,
                success=True,
                output=output.strip(),
                duration_ms=duration,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return CommandResult(
                device_serial=serial,
                success=False,
                output="",
                error=str(e),
                duration_ms=duration,
            )

    def execute_parallel(
        self,
        command: str,
        devices: Optional[list] = None,
        max_workers: int = 5,
        timeout: float = 30.0,
    ) -> list:
        """Execute a command on multiple devices in parallel."""
        if devices is None:
            device_infos = self.list_devices()
            devices = [d.serial for d in device_infos]

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.execute_command, serial, command, timeout): serial
                for serial in devices
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    serial = futures[future]
                    results.append(CommandResult(
                        device_serial=serial,
                        success=False,
                        output="",
                        error=str(e),
                    ))

        return results

    def check_health(self, serial: str) -> dict:
        """Check health of a specific device."""
        health = {
            "serial": serial,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        try:
            client = self._get_client()
            device = client.device(serial)

            if device is None:
                health["status"] = "offline"
                health["checks"]["connection"] = {"status": "failed", "message": "Device not found"}
                return health

            # Connection check
            health["checks"]["connection"] = {"status": "passed"}

            # Responsiveness check
            start = time.time()
            result = device.shell("echo test")
            latency = (time.time() - start) * 1000
            health["checks"]["responsiveness"] = {
                "status": "passed" if latency < 1000 else "warning",
                "latency_ms": round(latency, 2),
            }

            # Battery check
            battery = self._get_battery_level(device)
            if battery is not None:
                health["checks"]["battery"] = {
                    "status": "passed" if battery > 20 else "warning",
                    "level": battery,
                }

            # Storage check
            try:
                storage_result = device.shell("df /data | tail -1")
                parts = storage_result.split()
                if len(parts) >= 5:
                    use_percent = int(parts[4].replace("%", ""))
                    health["checks"]["storage"] = {
                        "status": "passed" if use_percent < 90 else "warning",
                        "used_percent": use_percent,
                    }
            except Exception:
                pass

            # Memory check
            try:
                mem_result = device.shell("cat /proc/meminfo | grep -E '^(MemTotal|MemFree)'")
                lines = mem_result.strip().split("\n")
                mem_info = {}
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].replace(":", "")
                        value = int(parts[1])
                        mem_info[key] = value

                if "MemTotal" in mem_info and "MemFree" in mem_info:
                    free_percent = (mem_info["MemFree"] / mem_info["MemTotal"]) * 100
                    health["checks"]["memory"] = {
                        "status": "passed" if free_percent > 10 else "warning",
                        "free_percent": round(free_percent, 2),
                    }
            except Exception:
                pass

            # Determine overall status
            all_passed = all(
                c.get("status") == "passed"
                for c in health["checks"].values()
            )
            any_failed = any(
                c.get("status") == "failed"
                for c in health["checks"].values()
            )

            if any_failed:
                health["status"] = "unhealthy"
            elif all_passed:
                health["status"] = "healthy"
            else:
                health["status"] = "degraded"

        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)

        return health

    def check_all_health(self) -> list:
        """Check health of all connected devices."""
        device_infos = self.list_devices()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.check_health, d.serial): d.serial
                for d in device_infos
            }

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    serial = futures[future]
                    results.append({
                        "serial": serial,
                        "status": "error",
                        "error": str(e),
                    })

        return results


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ADB Karrot Multi-Device Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list
  %(prog)s --list --detailed
  %(prog)s --device 127.0.0.1:5555 --command "input tap 720 2374"
  %(prog)s --all --command "input keyevent KEYCODE_HOME"
  %(prog)s --health
  %(prog)s --connect 192.168.1.100:5555
        """
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all connected devices"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed device information (with --list)"
    )

    parser.add_argument(
        "--device", "-d",
        help="Target device serial for command execution"
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Execute command on all devices"
    )

    parser.add_argument(
        "--command", "-c",
        help="Shell command to execute"
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="Check health of all devices"
    )

    parser.add_argument(
        "--connect",
        help="Connect to a device (format: host:port)"
    )

    parser.add_argument(
        "--disconnect",
        help="Disconnect a device"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="Command timeout in seconds (default: 30)"
    )

    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=5,
        help="Maximum parallel executions (default: 5)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print verbose output"
    )

    return parser.parse_args()


def print_result(result: CommandResult, verbose: bool = False) -> None:
    """Print command execution result."""
    status = "\033[92mSUCCESS\033[0m" if result.success else "\033[91mFAILED\033[0m"
    print(f"\n[{result.device_serial}] {status}")

    if verbose or not result.success:
        print(f"  Duration: {result.duration_ms:.2f}ms")

    if result.output:
        print(f"  Output: {result.output[:200]}")
        if len(result.output) > 200:
            print(f"  ... (truncated, total {len(result.output)} chars)")

    if result.error:
        print(f"  Error: {result.error}")


def print_health(health: dict) -> None:
    """Print health check result."""
    status_colors = {
        "healthy": "\033[92m",    # Green
        "degraded": "\033[93m",   # Yellow
        "unhealthy": "\033[91m",  # Red
        "error": "\033[95m",      # Magenta
        "offline": "\033[90m",    # Gray
    }
    reset = "\033[0m"

    status = health.get("status", "unknown")
    color = status_colors.get(status, "")

    print(f"\n[{health['serial']}] {color}{status.upper()}{reset}")

    if "error" in health:
        print(f"  Error: {health['error']}")

    for name, check in health.get("checks", {}).items():
        check_status = check.get("status", "unknown")
        if check_status == "passed":
            icon = "\033[92m[PASS]\033[0m"
        elif check_status == "warning":
            icon = "\033[93m[WARN]\033[0m"
        else:
            icon = "\033[91m[FAIL]\033[0m"

        details = []
        for k, v in check.items():
            if k != "status":
                details.append(f"{k}={v}")

        detail_str = ", ".join(details) if details else ""
        print(f"  {icon} {name}: {detail_str}")


def main() -> int:
    """Main entry point."""
    args = parse_args()
    controller = MultiDeviceController()

    # Connect mode
    if args.connect:
        if ":" in args.connect:
            host, port = args.connect.rsplit(":", 1)
            port = int(port)
        else:
            host = args.connect
            port = 5555

        if controller.connect_device(host, port):
            print(f"Connected to {host}:{port}")
            return 0
        else:
            return 1

    # Disconnect mode
    if args.disconnect:
        if controller.disconnect_device(args.disconnect):
            print(f"Disconnected {args.disconnect}")
            return 0
        else:
            return 1

    # List mode
    if args.list:
        devices = controller.list_devices(detailed=args.detailed)
        if not devices:
            print("No devices connected")
            return 0

        print(f"Connected devices ({len(devices)}):")
        for device in devices:
            print(f"  {device}")
        return 0

    # Health check mode
    if args.health:
        health_results = controller.check_all_health()
        if not health_results:
            print("No devices connected")
            return 0

        print(f"Device Health Check ({len(health_results)} devices):")
        for health in health_results:
            print_health(health)

        # Summary
        healthy = sum(1 for h in health_results if h.get("status") == "healthy")
        print(f"\n--- Summary: {healthy}/{len(health_results)} healthy ---")

        return 0

    # Command execution mode
    if args.command:
        if args.all:
            print(f"Executing on all devices: {args.command}")
            results = controller.execute_parallel(
                args.command,
                max_workers=args.parallel,
                timeout=args.timeout,
            )

            for result in results:
                print_result(result, args.verbose)

            # Summary
            success_count = sum(1 for r in results if r.success)
            print(f"\n--- Summary: {success_count}/{len(results)} succeeded ---")

            return 0 if success_count == len(results) else 1

        elif args.device:
            print(f"Executing on {args.device}: {args.command}")
            result = controller.execute_command(
                args.device,
                args.command,
                timeout=args.timeout,
            )
            print_result(result, args.verbose)
            return 0 if result.success else 1

        else:
            print("Error: Must specify --device or --all for command execution")
            return 1

    # No action specified
    print("No action specified. Use --help for usage information.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
