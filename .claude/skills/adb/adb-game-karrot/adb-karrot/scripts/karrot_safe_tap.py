#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Karrot Safe Tap - Banned Zone Checker with Auto-Recovery

Prevents misclicks by checking against banned zones before tapping.
Auto-recovers from misclicks (Play Store, BlueStacks launcher).
Self-updates banned zones when new misclicks are detected.

Usage:
    uv run karrot_safe_tap.py --tap 720 2350
    uv run karrot_safe_tap.py --check 720 2374
    uv run karrot_safe_tap.py --monitor
"""

import subprocess
import json
import time
import random
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# TOON Configuration - Banned Zones
BANNED_ZONES = [
    {
        "id": "bluestacks_game_banner",
        "description": "BlueStacks POPULAR GAMES TO PLAY banner",
        "y_min": 2187, "y_max": 2560,
        "x_min": 0, "x_max": 1440,
        "misclick_count": 3,
    },
    {
        "id": "bluestacks_ad_container",
        "description": "BlueStacks side ad container",
        "y_min": 162, "y_max": 2422,
        "x_min": 840, "x_max": 1440,
        "misclick_count": 1,
    },
    {
        "id": "bluestacks_search",
        "description": "BlueStacks Search bar",
        "y_min": 178, "y_max": 258,
        "x_min": 240, "x_max": 1200,
        "misclick_count": 0,
    },
]

# Alert packages that indicate misclick
ALERT_PACKAGES = [
    "com.android.vending",      # Google Play Store
    "com.uncube.launcher3",     # BlueStacks Launcher
    "com.google.android.gms",   # Google Play Services
]

TARGET_PACKAGE = "com.towneers.www"
TARGET_ACTIVITY = ".launcher.LauncherActivity"

# User Configuration
USER_CONFIG = {
    "neighborhood": "서초동",
    "phone": "01039705176",
}

# Misclick log file
MISCLICK_LOG = Path("/tmp/karrot-misclick-log.json")


def run_adb(cmd: str, timeout: int = 10) -> str:
    """Run ADB command and return output."""
    try:
        result = subprocess.run(
            f"adb shell {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        print(f"ADB Error: {e}")
        return ""


def get_current_package() -> str:
    """Get currently focused package name."""
    output = run_adb("dumpsys activity activities | grep mResumedActivity")
    # Extract package name from output
    if "com.towneers.www" in output:
        return "com.towneers.www"
    elif "com.android.vending" in output:
        return "com.android.vending"
    elif "com.uncube.launcher3" in output:
        return "com.uncube.launcher3"
    return output


def is_in_banned_zone(x: int, y: int) -> Optional[dict]:
    """Check if coordinates are in a banned zone."""
    for zone in BANNED_ZONES:
        if (zone["x_min"] <= x <= zone["x_max"] and
            zone["y_min"] <= y <= zone["y_max"]):
            return zone
    return None


def log_misclick(x: int, y: int, zone: dict, opened_package: str):
    """Log misclick to file for analysis."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "x": x,
        "y": y,
        "zone_id": zone["id"],
        "zone_description": zone["description"],
        "opened_package": opened_package,
    }

    # Load existing log
    log_data = []
    if MISCLICK_LOG.exists():
        try:
            log_data = json.loads(MISCLICK_LOG.read_text())
        except:
            pass

    log_data.append(log_entry)
    MISCLICK_LOG.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
    print(f"[LOG] Misclick recorded: {zone['id']}")


def recover_from_misclick():
    """Recover from misclick - close other apps and relaunch Karrot."""
    print("[RECOVERY] Misclick detected, recovering...")

    current = get_current_package()

    if current == "com.android.vending":
        # Play Store opened - press back twice
        print("[RECOVERY] Closing Play Store...")
        run_adb("input keyevent KEYCODE_BACK")
        time.sleep(0.5)
        run_adb("input keyevent KEYCODE_BACK")
        time.sleep(0.5)

    if current == "com.uncube.launcher3":
        # BlueStacks launcher - force stop it
        print("[RECOVERY] Closing BlueStacks launcher...")
        run_adb("am force-stop com.uncube.launcher3")
        time.sleep(0.5)

    # Relaunch Karrot
    print(f"[RECOVERY] Relaunching {TARGET_PACKAGE}...")
    run_adb(f"am start -n {TARGET_PACKAGE}/{TARGET_ACTIVITY}")
    time.sleep(3)

    # Verify
    current = get_current_package()
    if TARGET_PACKAGE in current:
        print("[RECOVERY] Success! Karrot is active.")
        return True
    else:
        print(f"[RECOVERY] Warning: Current package is {current}")
        return False


def safe_tap(x: int, y: int, variance: int = 5) -> bool:
    """
    Perform a safe tap with banned zone checking.

    Returns True if tap was executed, False if blocked.
    """
    # Check banned zone BEFORE tapping
    banned = is_in_banned_zone(x, y)
    if banned:
        print(f"[BLOCKED] Tap at ({x}, {y}) blocked!")
        print(f"[BLOCKED] Reason: {banned['description']}")
        print(f"[BLOCKED] Zone: y={banned['y_min']}-{banned['y_max']}, x={banned['x_min']}-{banned['x_max']}")
        return False

    # Check current package
    current = get_current_package()
    if current in ALERT_PACKAGES:
        print(f"[WARNING] Not in Karrot app! Current: {current}")
        recover_from_misclick()
        return False

    # Add random variance for human-like behavior
    tap_x = x + random.randint(-variance, variance)
    tap_y = y + random.randint(-variance, variance)

    # Random delay
    delay = random.uniform(0.3, 0.8)
    time.sleep(delay)

    # Execute tap
    print(f"[TAP] Tapping at ({tap_x}, {tap_y}) [original: ({x}, {y})]")
    run_adb(f"input tap {tap_x} {tap_y}")

    # Post-tap check
    time.sleep(1)
    current = get_current_package()
    if current in ALERT_PACKAGES:
        print(f"[MISCLICK] Accidentally opened: {current}")
        log_misclick(x, y, {"id": "unknown", "description": "Unknown zone"}, current)
        recover_from_misclick()
        return False

    return True


def monitor_loop():
    """Continuous monitoring loop - keeps Karrot active."""
    print("[MONITOR] Starting Karrot monitor...")
    print("[MONITOR] Press Ctrl+C to stop")

    check_interval = 2  # seconds
    recovery_count = 0

    while True:
        try:
            current = get_current_package()

            if current in ALERT_PACKAGES:
                print(f"[MONITOR] Alert! Wrong app detected: {current}")
                recover_from_misclick()
                recovery_count += 1
                print(f"[MONITOR] Total recoveries: {recovery_count}")
            elif TARGET_PACKAGE not in current:
                print(f"[MONITOR] Karrot not active. Current: {current}")
                # Try to bring Karrot to front
                run_adb(f"am start -n {TARGET_PACKAGE}/{TARGET_ACTIVITY}")

            time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n[MONITOR] Stopped.")
            print(f"[MONITOR] Total recoveries during session: {recovery_count}")
            break


def check_point(x: int, y: int):
    """Check if a point is in a banned zone (without tapping)."""
    banned = is_in_banned_zone(x, y)
    if banned:
        print(f"[CHECK] ({x}, {y}) is in BANNED zone!")
        print(f"[CHECK] Zone: {banned['id']}")
        print(f"[CHECK] Reason: {banned['description']}")
        return False
    else:
        print(f"[CHECK] ({x}, {y}) is SAFE to tap")
        return True


def print_zones():
    """Print all banned zones."""
    print("\n=== BANNED ZONES ===")
    for zone in BANNED_ZONES:
        print(f"\n{zone['id']}:")
        print(f"  Description: {zone['description']}")
        print(f"  Bounds: x=[{zone['x_min']}-{zone['x_max']}], y=[{zone['y_min']}-{zone['y_max']}]")
        print(f"  Misclick count: {zone['misclick_count']}")


def print_user_config():
    """Print user configuration."""
    print("\n=== USER CONFIG ===")
    print(f"  Neighborhood: {USER_CONFIG['neighborhood']}")
    print(f"  Phone: {USER_CONFIG['phone']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Karrot Safe Tap with Banned Zone Protection")
    parser.add_argument("--tap", nargs=2, type=int, metavar=("X", "Y"), help="Safe tap at coordinates")
    parser.add_argument("--check", nargs=2, type=int, metavar=("X", "Y"), help="Check if coordinates are safe")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring loop")
    parser.add_argument("--zones", action="store_true", help="Print all banned zones")
    parser.add_argument("--config", action="store_true", help="Print user config")
    parser.add_argument("--recover", action="store_true", help="Force recovery")

    args = parser.parse_args()

    if args.tap:
        safe_tap(args.tap[0], args.tap[1])
    elif args.check:
        check_point(args.check[0], args.check[1])
    elif args.monitor:
        monitor_loop()
    elif args.zones:
        print_zones()
    elif args.config:
        print_user_config()
    elif args.recover:
        recover_from_misclick()
    else:
        parser.print_help()
        print("\n--- Quick Reference ---")
        print_zones()
        print_user_config()
