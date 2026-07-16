# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pure-python-adb>=0.3.0",
# ]
# ///
"""
ADB Karrot Safe Tap - Detection Avoidance Tap Functionality

This script provides human-like tap behavior with random delays and coordinate
variance to avoid LIAPP detection in Karrot applications.

Features:
- Random delay (500-2000ms) before tap
- Random coordinate variance (+/-10px)
- Human-like behavior simulation
- CLI interface with argparse

Target coordinates (1440x2560 resolution):
- welcome_get_started: (720, 2350)  # SAFE: Upper part of button, avoids ad zone (y>2187)
- welcome_login: (872, 2493)
- login_phone_input: (410, 254)
- login_confirm: (720, 2520)
- login_back: (40, 56)

Usage:
    uv run adb-karrot-safe-tap.py --target welcome_get_started
    uv run adb-karrot-safe-tap.py --x 720 --y 2350
    uv run adb-karrot-safe-tap.py --target login_confirm --device 127.0.0.1:5555
"""

import argparse
import random
import sys
import time
from typing import Optional, Tuple

from ppadb.client import Client as AdbClient


# Predefined target coordinates for Karrot app (1440x2560 resolution)
# NOTE: welcome_get_started uses y=2350 (not 2374) to avoid BlueStacks ad zone (y>2187)
TARGET_COORDINATES = {
    "welcome_get_started": (720, 2350),  # SAFE: Upper part of button
    "welcome_login": (872, 2493),
    "login_phone_input": (410, 254),
    "login_confirm": (720, 2520),
    "login_back": (40, 56),
}

# Safe tap configuration
DEFAULT_DEVICE = "127.0.0.1:5555"
MIN_DELAY_MS = 500
MAX_DELAY_MS = 2000
COORDINATE_VARIANCE = 10


def get_random_delay() -> float:
    """Generate random delay between MIN_DELAY_MS and MAX_DELAY_MS."""
    delay_ms = random.randint(MIN_DELAY_MS, MAX_DELAY_MS)
    return delay_ms / 1000.0


def apply_coordinate_variance(x: int, y: int, variance: int = COORDINATE_VARIANCE) -> Tuple[int, int]:
    """Apply random variance to coordinates for human-like behavior."""
    variance_x = random.randint(-variance, variance)
    variance_y = random.randint(-variance, variance)
    return (x + variance_x, y + variance_y)


def simulate_human_behavior() -> None:
    """Add additional random micro-delays to simulate human behavior."""
    # Small random pause to simulate human reaction time
    micro_delay = random.uniform(0.05, 0.15)
    time.sleep(micro_delay)


def connect_device(device_serial: str) -> Optional[object]:
    """Connect to ADB device."""
    try:
        # Parse host and port from device serial
        if ":" in device_serial:
            host, port = device_serial.rsplit(":", 1)
            port = int(port)
        else:
            host = device_serial
            port = 5555

        client = AdbClient(host="127.0.0.1", port=5037)

        # Try to connect to the device
        try:
            client.remote_connect(host, port)
        except Exception:
            pass  # Device might already be connected

        device = client.device(device_serial)
        if device is None:
            print(f"Error: Device {device_serial} not found")
            print("Available devices:")
            for d in client.devices():
                print(f"  - {d.serial}")
            return None

        return device
    except Exception as e:
        print(f"Error connecting to device: {e}")
        return None


def safe_tap(device: object, x: int, y: int, verbose: bool = False) -> bool:
    """
    Perform a safe tap with detection avoidance measures.

    Args:
        device: ADB device object
        x: Target X coordinate
        y: Target Y coordinate
        verbose: Print detailed information

    Returns:
        True if tap was successful, False otherwise
    """
    try:
        # Step 1: Random delay before tap
        delay = get_random_delay()
        if verbose:
            print(f"Waiting {delay:.3f}s before tap...")
        time.sleep(delay)

        # Step 2: Apply coordinate variance
        tap_x, tap_y = apply_coordinate_variance(x, y)
        if verbose:
            print(f"Original coordinates: ({x}, {y})")
            print(f"Adjusted coordinates: ({tap_x}, {tap_y})")

        # Step 3: Simulate human behavior
        simulate_human_behavior()

        # Step 4: Perform the tap
        device.shell(f"input tap {tap_x} {tap_y}")

        if verbose:
            print(f"Tap executed at ({tap_x}, {tap_y})")

        return True

    except Exception as e:
        print(f"Error performing tap: {e}")
        return False


def safe_tap_sequence(device: object, coordinates: list, verbose: bool = False) -> bool:
    """
    Perform a sequence of safe taps.

    Args:
        device: ADB device object
        coordinates: List of (x, y) tuples
        verbose: Print detailed information

    Returns:
        True if all taps were successful, False otherwise
    """
    for i, (x, y) in enumerate(coordinates):
        if verbose:
            print(f"\n--- Tap {i + 1}/{len(coordinates)} ---")

        if not safe_tap(device, x, y, verbose):
            return False

        # Additional delay between taps
        if i < len(coordinates) - 1:
            inter_tap_delay = random.uniform(0.3, 0.8)
            if verbose:
                print(f"Inter-tap delay: {inter_tap_delay:.3f}s")
            time.sleep(inter_tap_delay)

    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ADB Karrot Safe Tap - Detection avoidance tap functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Predefined targets:
  welcome_get_started  - Welcome screen "Get Started" button (720, 2374)
  welcome_login        - Welcome screen "Log In" button (872, 2493)
  login_phone_input    - Phone number input field (410, 254)
  login_confirm        - Login confirm button (720, 2520)
  login_back           - Login back button (40, 56)

Examples:
  %(prog)s --target welcome_get_started
  %(prog)s --x 720 --y 2374
  %(prog)s --target login_confirm --device 127.0.0.1:5555 --verbose
  %(prog)s --sequence welcome_get_started welcome_login
        """
    )

    parser.add_argument(
        "--device", "-d",
        default=DEFAULT_DEVICE,
        help=f"Device serial (default: {DEFAULT_DEVICE})"
    )

    parser.add_argument(
        "--target", "-t",
        choices=list(TARGET_COORDINATES.keys()),
        help="Predefined target to tap"
    )

    parser.add_argument(
        "--x",
        type=int,
        help="X coordinate for custom tap"
    )

    parser.add_argument(
        "--y",
        type=int,
        help="Y coordinate for custom tap"
    )

    parser.add_argument(
        "--sequence", "-s",
        nargs="+",
        choices=list(TARGET_COORDINATES.keys()),
        help="Sequence of predefined targets to tap"
    )

    parser.add_argument(
        "--min-delay",
        type=int,
        default=MIN_DELAY_MS,
        help=f"Minimum delay in ms (default: {MIN_DELAY_MS})"
    )

    parser.add_argument(
        "--max-delay",
        type=int,
        default=MAX_DELAY_MS,
        help=f"Maximum delay in ms (default: {MAX_DELAY_MS})"
    )

    parser.add_argument(
        "--variance",
        type=int,
        default=COORDINATE_VARIANCE,
        help=f"Coordinate variance in pixels (default: {COORDINATE_VARIANCE})"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print verbose output"
    )

    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List all predefined targets and exit"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    global MIN_DELAY_MS, MAX_DELAY_MS, COORDINATE_VARIANCE

    args = parse_args()

    # List targets mode
    if args.list_targets:
        print("Predefined targets (1440x2560 resolution):")
        for name, (x, y) in TARGET_COORDINATES.items():
            print(f"  {name}: ({x}, {y})")
        return 0

    # Update global settings
    MIN_DELAY_MS = args.min_delay
    MAX_DELAY_MS = args.max_delay
    COORDINATE_VARIANCE = args.variance

    # Validate arguments
    if args.sequence:
        pass  # Sequence mode
    elif args.target:
        pass  # Target mode
    elif args.x is not None and args.y is not None:
        pass  # Custom coordinate mode
    else:
        print("Error: Must specify --target, --sequence, or both --x and --y")
        return 1

    # Connect to device
    device = connect_device(args.device)
    if device is None:
        return 1

    if args.verbose:
        print(f"Connected to device: {args.device}")
        print(f"Delay range: {MIN_DELAY_MS}-{MAX_DELAY_MS}ms")
        print(f"Coordinate variance: +/-{COORDINATE_VARIANCE}px")

    # Execute tap(s)
    if args.sequence:
        coordinates = [TARGET_COORDINATES[t] for t in args.sequence]
        if args.verbose:
            print(f"Executing sequence: {args.sequence}")
        success = safe_tap_sequence(device, coordinates, args.verbose)
    elif args.target:
        x, y = TARGET_COORDINATES[args.target]
        if args.verbose:
            print(f"Tapping target: {args.target}")
        success = safe_tap(device, x, y, args.verbose)
    else:
        if args.verbose:
            print(f"Tapping custom coordinates")
        success = safe_tap(device, args.x, args.y, args.verbose)

    if success:
        print("Tap completed successfully")
        return 0
    else:
        print("Tap failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
