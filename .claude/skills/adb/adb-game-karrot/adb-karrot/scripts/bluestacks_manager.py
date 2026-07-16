#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
BlueStacks Emulator Manager for Karrot Automation

This script manages BlueStacks emulator lifecycle:
- Start/stop BlueStacks app
- Wait for ADB connection
- Launch Karrot app
- Full automation pipeline

Usage:
    uv run bluestacks_manager.py --start           # Start BlueStacks and wait for ADB
    uv run bluestacks_manager.py --start --karrot  # Start BlueStacks and launch Karrot
    uv run bluestacks_manager.py --stop            # Stop BlueStacks
    uv run bluestacks_manager.py --status          # Check BlueStacks and ADB status
    uv run bluestacks_manager.py --connect         # Just connect ADB
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# Configuration
BLUESTACKS_APP = "/Applications/BlueStacks.app"
ADB_HOST = "127.0.0.1"
ADB_PORT = 5555
ADB_DEVICE = f"{ADB_HOST}:{ADB_PORT}"

KARROT_PACKAGE = "com.towneers.www"
KARROT_ACTIVITY = ".launcher.LauncherActivity"

# Timeouts
BOOT_TIMEOUT_SEC = 120  # Max wait for emulator boot
ADB_CONNECT_TIMEOUT_SEC = 60  # Max wait for ADB connection
BOOT_COMPLETE_TIMEOUT_SEC = 60  # Max wait for boot_completed


def log(message: str, level: str = "INFO") -> None:
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_cmd(cmd: str, timeout: int = 30, capture: bool = True) -> tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def is_bluestacks_running() -> bool:
    """Check if BlueStacks is running."""
    code, out, _ = run_cmd("pgrep -f 'BlueStacks'")
    return code == 0 and bool(out)


def is_adb_connected() -> bool:
    """Check if ADB is connected to the emulator."""
    code, out, _ = run_cmd(f"adb devices | grep {ADB_DEVICE}")
    return code == 0 and ADB_DEVICE in out and "device" in out


def is_boot_completed() -> bool:
    """Check if Android has fully booted."""
    code, out, _ = run_cmd(f"adb -s {ADB_DEVICE} shell getprop sys.boot_completed", timeout=5)
    return code == 0 and out.strip() == "1"


def start_bluestacks() -> bool:
    """Start BlueStacks application."""
    if is_bluestacks_running():
        log("BlueStacks is already running")
        return True

    log("Starting BlueStacks...")
    code, _, err = run_cmd(f"open -a '{BLUESTACKS_APP}'")

    if code != 0:
        log(f"Failed to start BlueStacks: {err}", "ERROR")
        return False

    log("BlueStacks starting...")
    return True


def stop_bluestacks() -> bool:
    """Stop BlueStacks application."""
    if not is_bluestacks_running():
        log("BlueStacks is not running")
        return True

    log("Stopping BlueStacks...")

    # Try graceful quit first
    run_cmd("osascript -e 'tell application \"BlueStacks\" to quit'", timeout=10)
    time.sleep(2)

    # Force kill if still running
    if is_bluestacks_running():
        run_cmd("pkill -9 -f 'BlueStacks'")
        time.sleep(1)

    if is_bluestacks_running():
        log("Failed to stop BlueStacks", "ERROR")
        return False

    log("BlueStacks stopped")
    return True


def wait_for_adb_connection(timeout: int = ADB_CONNECT_TIMEOUT_SEC) -> bool:
    """Wait for ADB connection to emulator."""
    log(f"Waiting for ADB connection to {ADB_DEVICE}...")

    start_time = time.time()
    attempt = 0

    while time.time() - start_time < timeout:
        attempt += 1

        # Try to connect
        run_cmd(f"adb connect {ADB_DEVICE}", timeout=5)

        if is_adb_connected():
            log(f"ADB connected after {attempt} attempts")
            return True

        elapsed = int(time.time() - start_time)
        if attempt % 5 == 0:
            log(f"Still waiting for ADB... ({elapsed}s elapsed)")

        time.sleep(2)

    log(f"ADB connection timeout after {timeout}s", "ERROR")
    return False


def wait_for_boot_complete(timeout: int = BOOT_COMPLETE_TIMEOUT_SEC) -> bool:
    """Wait for Android to fully boot."""
    log("Waiting for Android boot to complete...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_boot_completed():
            log("Android boot completed")
            return True

        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0 and elapsed > 0:
            log(f"Still booting... ({elapsed}s)")

        time.sleep(2)

    log(f"Boot completion timeout after {timeout}s", "ERROR")
    return False


def launch_karrot() -> bool:
    """Launch Karrot app."""
    log(f"Launching Karrot ({KARROT_PACKAGE})...")

    # Force stop first
    run_cmd(f"adb -s {ADB_DEVICE} shell am force-stop {KARROT_PACKAGE}")
    time.sleep(1)

    # Start app
    code, out, err = run_cmd(
        f"adb -s {ADB_DEVICE} shell am start -n {KARROT_PACKAGE}/{KARROT_ACTIVITY}"
    )

    if code != 0:
        log(f"Failed to launch Karrot: {err}", "ERROR")
        return False

    log("Karrot launched")
    return True


def get_status() -> dict:
    """Get current status of BlueStacks and ADB."""
    return {
        "bluestacks_running": is_bluestacks_running(),
        "adb_connected": is_adb_connected(),
        "boot_completed": is_boot_completed() if is_adb_connected() else False,
        "adb_device": ADB_DEVICE,
    }


def print_status() -> None:
    """Print current status."""
    status = get_status()

    print("\n" + "=" * 50)
    print("BLUESTACKS MANAGER STATUS")
    print("=" * 50)
    print(f"BlueStacks Running:  {'Yes' if status['bluestacks_running'] else 'No'}")
    print(f"ADB Connected:       {'Yes' if status['adb_connected'] else 'No'}")
    print(f"Boot Completed:      {'Yes' if status['boot_completed'] else 'No'}")
    print(f"ADB Device:          {status['adb_device']}")
    print("=" * 50 + "\n")


def full_start(launch_karrot_app: bool = False) -> bool:
    """Full startup sequence: Start BlueStacks, wait for ADB, optionally launch Karrot."""
    log("=" * 50)
    log("FULL STARTUP SEQUENCE")
    log("=" * 50)

    # Step 1: Start BlueStacks
    if not start_bluestacks():
        return False

    # Wait for BlueStacks process to initialize
    log("Waiting for BlueStacks to initialize (10s)...")
    time.sleep(10)

    # Step 2: Wait for ADB connection
    if not wait_for_adb_connection():
        return False

    # Step 3: Wait for boot completion
    if not wait_for_boot_complete():
        log("Boot not complete, but continuing...", "WARN")

    # Step 4: Optionally launch Karrot
    if launch_karrot_app:
        time.sleep(2)  # Give system a moment
        if not launch_karrot():
            return False

    log("=" * 50)
    log("STARTUP COMPLETE!")
    log("=" * 50)
    print_status()

    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BlueStacks Emulator Manager for Karrot Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --start                Start BlueStacks and wait for ADB
  %(prog)s --start --karrot       Start BlueStacks and launch Karrot
  %(prog)s --stop                 Stop BlueStacks
  %(prog)s --status               Check status
  %(prog)s --connect              Connect ADB only
  %(prog)s --launch-karrot        Launch Karrot (requires running emulator)
        """
    )

    parser.add_argument(
        "--start", "-s",
        action="store_true",
        help="Start BlueStacks emulator"
    )
    parser.add_argument(
        "--stop", "-x",
        action="store_true",
        help="Stop BlueStacks emulator"
    )
    parser.add_argument(
        "--status", "-t",
        action="store_true",
        help="Show current status"
    )
    parser.add_argument(
        "--connect", "-c",
        action="store_true",
        help="Connect ADB to emulator"
    )
    parser.add_argument(
        "--karrot", "-k",
        action="store_true",
        help="Launch Karrot after startup"
    )
    parser.add_argument(
        "--launch-karrot", "-l",
        action="store_true",
        help="Launch Karrot app (standalone)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Handle commands
    if args.stop:
        success = stop_bluestacks()
        return 0 if success else 1

    if args.status:
        print_status()
        return 0

    if args.connect:
        success = wait_for_adb_connection()
        if success and wait_for_boot_complete():
            print_status()
        return 0 if success else 1

    if args.launch_karrot:
        if not is_adb_connected():
            log("ADB not connected. Use --start first.", "ERROR")
            return 1
        success = launch_karrot()
        return 0 if success else 1

    if args.start:
        success = full_start(launch_karrot_app=args.karrot)
        return 0 if success else 1

    # Default: show status
    print_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
