#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.39.0", "Pillow>=10.0.0"]
# ///
"""
Karrot Resilient Tap - Auto-Recovery Tap with AI Vision Fallback

This script provides resilient tap functionality for Karrot app automation.
It verifies the active package before and after taps, auto-recovers from
misclicks (Play Store, BlueStacks launcher), and logs all actions.

Key Features:
- Pre-tap package verification (must be com.towneers.www)
- Post-tap package verification with 1 second delay
- Auto-recovery when wrong package detected
- Banned zone protection (BlueStacks ad overlays)
- AI Vision fallback when UIAutomator fails
- Smart retry with exponential backoff
- Detailed logging to /tmp/karrot-tap-log.json
- Human-like tap behavior (random delays and variance)

Banned Zones (BlueStacks Air 1440x2560):
- bluestacks_game_banner: y > 2187 (opens Play Store!)
- bluestacks_ad_container: x > 840, 162 < y < 2422
- bluestacks_search: 240 < x < 1200, 178 < y < 258

Safe Tap Targets:
- get_started: (720, 2350) - Get Started button (avoids ad zone)
- login: (872, 2493) - Log in link
- country_korea: (720, 1482) - Korea country selector
- phone_input: (720, 400) - Phone input field
- verify_now: (720, 2484) - Verify now button
- confirm_button: (720, 2400) - Confirm button
- back_button: (64, 104) - Back button

Usage:
    uv run karrot_resilient_tap.py --tap get_started
    uv run karrot_resilient_tap.py --tap 720 2350
    uv run karrot_resilient_tap.py --ai-find "Get Started button"
    uv run karrot_resilient_tap.py --tap get_started --no-ai
    uv run karrot_resilient_tap.py --launch
    uv run karrot_resilient_tap.py --recover
    uv run karrot_resilient_tap.py --status
"""

import argparse
import json
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Try to import smart detector for AI fallback
try:
    from karrot_smart_detector import SmartDetector, DetectionMethod
    HAS_SMART_DETECTOR = True
except ImportError:
    HAS_SMART_DETECTOR = False
    SmartDetector = None
    DetectionMethod = None


# Configuration
TARGET_PACKAGE = "com.towneers.www"
TARGET_ACTIVITY = ".launcher.LauncherActivity"

ALERT_PACKAGES = [
    "com.android.vending",       # Google Play Store
    "com.uncube.launcher3",      # BlueStacks Launcher
    "com.google.android.gms",    # Google Play Services
]

# Banned zones (BlueStacks Air 1440x2560)
# NOTE: Updated to allow Karrot buttons in lower screen area
# Button "Get started" is at y=2322-2426, so we start ban at y=2440
BANNED_ZONES = [
    {
        "id": "bluestacks_game_banner",
        "description": "BlueStacks POPULAR GAMES TO PLAY - below Karrot buttons",
        "x_min": 0, "x_max": 1440,
        "y_min": 2440, "y_max": 2560,  # Changed from 2187 to 2440 (below buttons)
    },
    {
        "id": "bluestacks_ad_container",
        "description": "BlueStacks side ad container",
        "x_min": 840, "x_max": 1440,
        "y_min": 162, "y_max": 2200,  # Reduced to not overlap with buttons
    },
    {
        "id": "bluestacks_search",
        "description": "BlueStacks Search bar",
        "x_min": 240, "x_max": 1200,
        "y_min": 178, "y_max": 258,
    },
]

# Safe tap targets (1440x2560 resolution)
# NOTE: Updated with better names and descriptions
SAFE_TARGETS = {
    "get_started": (720, 2350),     # Get Started button (SAFE: Upper part of button)
    "login": (872, 2493),            # Log in link
    "country_korea": (720, 1482),    # Korea country selector
    "find_nearby": (720, 216),       # Find nearby neighborhoods button
    "verify_now": (720, 2484),       # Verify now button
    "phone_input": (720, 400),       # Phone input field
    "confirm_button": (720, 2400),   # Confirm button
    "back_button": (64, 104),        # Back button
}

# Timing configuration
TAP_DELAY_MIN_MS = 500
TAP_DELAY_MAX_MS = 2000
COORDINATE_VARIANCE = 5
POST_TAP_WAIT_SEC = 1.0
RECOVERY_WAIT_SEC = 2.0

# Exponential backoff configuration
INITIAL_BACKOFF_SEC = 1.0
BACKOFF_FACTOR = 1.5
MAX_BACKOFF_SEC = 5.0
MAX_RETRY_ATTEMPTS = 3

# Log file
LOG_FILE = Path("/tmp/karrot-tap-log.json")


def log_action(action: str, details: dict) -> None:
    """Log action to JSON file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        **details
    }

    # Load existing logs
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            logs = []

    logs.append(log_entry)

    # Keep only last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    LOG_FILE.write_text(json.dumps(logs, indent=2, ensure_ascii=False))


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
        print(f"[ERROR] ADB command failed: {e}")
        return ""


def run_adb_base(cmd: str, timeout: int = 10) -> str:
    """Run ADB base command (not shell)."""
    try:
        result = subprocess.run(
            f"adb {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] ADB command failed: {e}")
        return ""


def get_current_package() -> str:
    """
    Get currently focused package name with fallback methods.

    Returns:
        Package name string, or empty string if detection failed.
    """
    # Method 1: Try mResumedActivity
    output = run_adb("dumpsys activity activities | grep mResumedActivity")

    for pkg in [TARGET_PACKAGE] + ALERT_PACKAGES:
        if pkg in output:
            return pkg

    # Try to extract package from output
    if "com." in output:
        parts = output.split()
        for part in parts:
            if "com." in part:
                # Extract package name
                pkg = part.split("/")[0].strip()
                if pkg.startswith("com."):
                    return pkg

    # Method 2: Fallback to dumpsys window
    print("[DEBUG] Method 1 failed, trying dumpsys window fallback...")
    window_output = run_adb("dumpsys window | grep mCurrentFocus")

    # Check known packages in window output
    for pkg in [TARGET_PACKAGE] + ALERT_PACKAGES:
        if pkg in window_output:
            return pkg

    # Try to extract package from window output
    if "com." in window_output:
        parts = window_output.split()
        for part in parts:
            if "com." in part and "/" in part:
                # Format: com.example.app/com.example.Activity
                pkg = part.split("/")[0].strip()
                if pkg.startswith("com."):
                    return pkg

    # Method 3: Last resort - try dumpsys window windows
    print("[DEBUG] Method 2 failed, trying dumpsys window windows fallback...")
    windows_output = run_adb("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")

    # Check known packages
    for pkg in [TARGET_PACKAGE] + ALERT_PACKAGES:
        if pkg in windows_output:
            return pkg

    # Extract any package name
    if "com." in windows_output:
        parts = windows_output.split()
        for part in parts:
            if "com." in part:
                # Try to extract package name
                if "/" in part:
                    pkg = part.split("/")[0].strip()
                else:
                    pkg = part.strip()

                if pkg.startswith("com.") and not pkg.endswith("/"):
                    return pkg

    # All methods failed - return empty string
    print("[WARNING] All package detection methods failed")
    return ""


def is_in_banned_zone(x: int, y: int) -> Optional[dict]:
    """Check if coordinates are in a banned zone."""
    for zone in BANNED_ZONES:
        if (zone["x_min"] <= x <= zone["x_max"] and
            zone["y_min"] <= y <= zone["y_max"]):
            return zone
    return None


def apply_variance(x: int, y: int, variance: int = COORDINATE_VARIANCE) -> Tuple[int, int]:
    """Apply random variance to coordinates."""
    return (
        x + random.randint(-variance, variance),
        y + random.randint(-variance, variance)
    )


def get_random_delay() -> float:
    """Get random delay in seconds."""
    delay_ms = random.randint(TAP_DELAY_MIN_MS, TAP_DELAY_MAX_MS)
    return delay_ms / 1000.0


def launch_karrot() -> bool:
    """Launch Karrot app."""
    print(f"[LAUNCH] Starting {TARGET_PACKAGE}...")

    # Force stop any interfering apps first
    for pkg in ALERT_PACKAGES:
        run_adb(f"am force-stop {pkg}")

    time.sleep(0.5)

    # Launch Karrot
    run_adb(f"am start -n {TARGET_PACKAGE}/{TARGET_ACTIVITY}")

    log_action("launch", {"package": TARGET_PACKAGE})

    # Wait for launch
    time.sleep(3)

    # Verify
    current = get_current_package()
    if TARGET_PACKAGE in current:
        print(f"[LAUNCH] Success! Karrot is active.")
        return True
    else:
        print(f"[LAUNCH] Warning: Current package is {current}")
        return False


def recover_from_misclick() -> bool:
    """Recover from misclick - close other apps and relaunch Karrot."""
    current = get_current_package()
    print(f"[RECOVERY] Current package: {current}")

    log_action("recovery_start", {"current_package": current})

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

    # Force stop all alert packages
    for pkg in ALERT_PACKAGES:
        run_adb(f"am force-stop {pkg}")

    time.sleep(RECOVERY_WAIT_SEC)

    # Relaunch Karrot
    success = launch_karrot()

    log_action("recovery_complete", {"success": success})

    return success


def resilient_tap(
    x: int,
    y: int,
    name: str = "custom",
    use_ai_fallback: bool = True,
    max_retries: int = MAX_RETRY_ATTEMPTS
) -> bool:
    """
    Perform a resilient tap with full verification and auto-recovery.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        name: Target name for logging
        use_ai_fallback: Enable AI Vision fallback if UIAutomator fails
        max_retries: Maximum retry attempts with exponential backoff

    Returns:
        True if tap was successful and app remained active.
    """
    print(f"\n{'='*50}")
    print(f"[TAP] Target: {name} at ({x}, {y})")

    # Step 1: Check banned zone BEFORE tapping
    banned = is_in_banned_zone(x, y)
    if banned:
        print(f"[BLOCKED] Tap blocked - in banned zone!")
        print(f"[BLOCKED] Zone: {banned['id']}")
        print(f"[BLOCKED] Reason: {banned['description']}")
        log_action("tap_blocked", {
            "x": x, "y": y, "name": name,
            "zone": banned["id"],
            "reason": banned["description"]
        })
        return False

    # Step 2: Pre-tap package verification
    print("[VERIFY] Pre-tap package check...")
    current = get_current_package()

    # Handle empty package detection (unknown state)
    if not current:
        print("[WARNING] Cannot detect current package - proceeding with caution")
        log_action("package_detection_failed", {
            "x": x, "y": y, "name": name,
            "stage": "pre-tap",
            "action": "proceeding_anyway"
        })
        # Don't block the tap - continue with warning
    elif current in ALERT_PACKAGES:
        print(f"[WARNING] Wrong app active: {current}")
        print("[RECOVERY] Auto-recovering before tap...")
        if not recover_from_misclick():
            print("[ERROR] Recovery failed - aborting tap")
            return False
        current = get_current_package()
    elif TARGET_PACKAGE not in current:
        print(f"[WARNING] Karrot not active. Current: {current}")
        print("[RECOVERY] Launching Karrot...")
        if not launch_karrot():
            print("[ERROR] Failed to launch Karrot - aborting tap")
            return False

    # Step 3: Attempt tap with exponential backoff retry
    attempt = 0
    backoff = INITIAL_BACKOFF_SEC
    success = False

    while attempt < max_retries:
        attempt += 1

        # Random delay (human-like behavior)
        delay = get_random_delay()
        print(f"[WAIT] Attempt {attempt}/{max_retries} - Waiting {delay:.2f}s...")
        time.sleep(delay)

        # Apply variance and tap
        tap_x, tap_y = apply_variance(x, y)
        print(f"[TAP] Tapping at ({tap_x}, {tap_y}) [variance applied]")

        run_adb(f"input tap {tap_x} {tap_y}")

        log_action("tap_executed", {
            "name": name,
            "attempt": attempt,
            "original": {"x": x, "y": y},
            "actual": {"x": tap_x, "y": tap_y},
            "delay_sec": delay
        })

        # Post-tap verification (wait 1 second)
        print(f"[VERIFY] Post-tap check (waiting {POST_TAP_WAIT_SEC}s)...")
        time.sleep(POST_TAP_WAIT_SEC)

        current = get_current_package()

        # Handle empty package detection (unknown state)
        if not current:
            print("[WARNING] Cannot detect package after tap - assuming success")
            log_action("package_detection_failed", {
                "x": x, "y": y, "name": name,
                "stage": "post-tap",
                "action": "assuming_success",
                "attempt": attempt
            })
            # Assume success if we can't detect the package
            success = True
            break

        if current in ALERT_PACKAGES:
            print(f"[MISCLICK] Accidentally opened: {current}")
            log_action("misclick_detected", {
                "name": name, "x": x, "y": y,
                "attempt": attempt,
                "opened_package": current
            })

            print("[RECOVERY] Auto-recovering from misclick...")
            if recover_from_misclick():
                print("[RECOVERY] Recovered successfully")

                # Exponential backoff before retry
                if attempt < max_retries:
                    print(f"[BACKOFF] Waiting {backoff:.2f}s before retry...")
                    time.sleep(backoff)
                    backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SEC)
                continue
            else:
                print("[ERROR] Recovery failed")
                return False

        if TARGET_PACKAGE not in current:
            print(f"[WARNING] Karrot not active after tap. Current: {current}")

            # Exponential backoff before retry
            if attempt < max_retries:
                print(f"[BACKOFF] Waiting {backoff:.2f}s before retry...")
                time.sleep(backoff)
                backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF_SEC)
            continue

        print(f"[SUCCESS] Tap successful - Karrot still active")
        log_action("tap_success", {
            "name": name, "x": x, "y": y,
            "attempt": attempt
        })
        success = True
        break

    # Step 4: AI Vision fallback if tap failed and enabled
    if not success and use_ai_fallback and HAS_SMART_DETECTOR:
        print("\n[AI FALLBACK] Attempting AI Vision detection...")

        try:
            detector = SmartDetector(enable_ai_vision=True)
            result = detector.find_with_fallback(name, use_cache=False, capture_new=True)

            if result.found:
                print(f"[AI FOUND] AI detected '{name}' at ({result.point.x}, {result.point.y})")
                print(f"[AI FOUND] Method: {result.method.value}, Confidence: {result.confidence:.0%}")

                log_action("ai_fallback_found", {
                    "name": name,
                    "original": {"x": x, "y": y},
                    "ai_detected": {"x": result.point.x, "y": result.point.y},
                    "method": result.method.value,
                    "confidence": result.confidence
                })

                # Tap the AI-detected location
                tap_x, tap_y = apply_variance(result.point.x, result.point.y)
                print(f"[AI TAP] Tapping AI-detected location at ({tap_x}, {tap_y})")

                run_adb(f"input tap {tap_x} {tap_y}")
                time.sleep(POST_TAP_WAIT_SEC)

                # Verify AI tap
                current = get_current_package()
                if TARGET_PACKAGE in current:
                    print(f"[AI SUCCESS] AI fallback tap successful!")
                    log_action("ai_fallback_success", {
                        "name": name,
                        "location": {"x": result.point.x, "y": result.point.y}
                    })
                    return True
                else:
                    print(f"[AI FAILED] AI tap did not work. Current: {current}")
            else:
                print(f"[AI NOT FOUND] AI could not find '{name}'")
                log_action("ai_fallback_not_found", {"name": name})
        except Exception as e:
            print(f"[AI ERROR] AI fallback error: {e}")
            log_action("ai_fallback_error", {"name": name, "error": str(e)})

    return success


def tap_target(target_name: str, use_ai_fallback: bool = True) -> bool:
    """Tap a predefined target."""
    if target_name not in SAFE_TARGETS:
        print(f"[ERROR] Unknown target: {target_name}")
        print(f"[INFO] Available targets: {', '.join(SAFE_TARGETS.keys())}")
        return False

    x, y = SAFE_TARGETS[target_name]
    return resilient_tap(x, y, target_name, use_ai_fallback=use_ai_fallback)


def ai_find_and_tap(description: str) -> bool:
    """Use AI Vision to find and tap an element."""
    if not HAS_SMART_DETECTOR:
        print("[ERROR] AI Vision not available. Install dependencies:")
        print("  pip install anthropic Pillow")
        return False

    print(f"\n{'='*50}")
    print(f"[AI FIND] Searching for '{description}'...")

    try:
        detector = SmartDetector(enable_ai_vision=True)
        result = detector.find_with_fallback(description, use_cache=False, capture_new=True)

        if result.found:
            print(f"[AI FOUND] Located at ({result.point.x}, {result.point.y})")
            print(f"[AI FOUND] Method: {result.method.value}, Confidence: {result.confidence:.0%}")

            log_action("ai_find_success", {
                "description": description,
                "location": {"x": result.point.x, "y": result.point.y},
                "method": result.method.value,
                "confidence": result.confidence
            })

            # Tap the AI-detected location
            return resilient_tap(
                result.point.x,
                result.point.y,
                name=description,
                use_ai_fallback=False  # Already using AI
            )
        else:
            print(f"[AI NOT FOUND] Could not locate '{description}'")
            log_action("ai_find_failed", {"description": description})
            return False

    except Exception as e:
        print(f"[AI ERROR] {e}")
        log_action("ai_find_error", {"description": description, "error": str(e)})
        return False


def get_status() -> dict:
    """Get current status."""
    current = get_current_package()

    status = {
        "timestamp": datetime.now().isoformat(),
        "current_package": current,
        "is_karrot_active": TARGET_PACKAGE in current,
        "is_alert_package": current in ALERT_PACKAGES,
        "target_package": TARGET_PACKAGE,
        "ai_vision_available": HAS_SMART_DETECTOR,
    }

    # Get recent logs
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text())
            status["recent_actions"] = logs[-5:] if logs else []
            status["total_actions"] = len(logs)
        except (json.JSONDecodeError, OSError):
            status["recent_actions"] = []
            status["total_actions"] = 0

    return status


def print_status():
    """Print current status."""
    status = get_status()

    print("\n" + "="*50)
    print("KARROT RESILIENT TAP STATUS")
    print("="*50)
    print(f"Timestamp: {status['timestamp']}")
    print(f"Current Package: {status['current_package']}")
    print(f"Karrot Active: {'Yes' if status['is_karrot_active'] else 'NO!'}")
    print(f"Alert Package: {'YES!' if status['is_alert_package'] else 'No'}")
    print(f"AI Vision: {'Available' if status['ai_vision_available'] else 'Not Available'}")
    print(f"Total Actions Logged: {status.get('total_actions', 0)}")

    if status.get('recent_actions'):
        print("\nRecent Actions:")
        for action in status['recent_actions']:
            print(f"  - {action.get('action', 'unknown')}: {action.get('timestamp', '')}")

    print("\nSafe Tap Targets:")
    for name, (x, y) in SAFE_TARGETS.items():
        print(f"  - {name}: ({x}, {y})")

    print("\nBanned Zones:")
    for zone in BANNED_ZONES:
        print(f"  - {zone['id']}: y={zone['y_min']}-{zone['y_max']}, x={zone['x_min']}-{zone['x_max']}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Karrot Resilient Tap - Auto-Recovery Tap with AI Vision Fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tap get_started              # Tap predefined target
  %(prog)s --tap 720 2350                 # Tap custom coordinates
  %(prog)s --tap get_started --no-ai      # Disable AI fallback
  %(prog)s --ai-find "Get Started button" # Use AI to find and tap
  %(prog)s --launch                       # Launch Karrot app
  %(prog)s --recover                      # Force recovery
  %(prog)s --status                       # Show current status
  %(prog)s --targets                      # List all targets

Safe Targets:
  get_started       (720, 2350)  - Get Started button
  login             (872, 2493)  - Log In button
  country_korea     (720, 1482)  - Korea country selector
  find_nearby       (720, 216)   - Find nearby neighborhoods
  verify_now        (720, 2484)  - Verify now button
  phone_input       (720, 400)   - Phone input field
  confirm_button    (720, 2400)  - Confirm button
  back_button       (64, 104)    - Back button

AI Vision:
  Requires: pip install anthropic Pillow
  Set: ANTHROPIC_API_KEY environment variable
        """
    )

    parser.add_argument(
        "--tap", "-t",
        nargs="+",
        help="Tap target (name or 'x y' coordinates)"
    )
    parser.add_argument(
        "--ai-find",
        metavar="DESCRIPTION",
        help="Use AI Vision to find and tap element"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI Vision fallback"
    )
    parser.add_argument(
        "--launch", "-l",
        action="store_true",
        help="Launch Karrot app"
    )
    parser.add_argument(
        "--recover", "-r",
        action="store_true",
        help="Force recovery from misclick"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current status"
    )
    parser.add_argument(
        "--targets",
        action="store_true",
        help="List all predefined targets"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    if args.targets:
        print("Predefined Safe Targets:")
        for name, (x, y) in SAFE_TARGETS.items():
            print(f"  {name}: ({x}, {y})")
        return 0

    if args.status:
        print_status()
        return 0

    if args.launch:
        success = launch_karrot()
        return 0 if success else 1

    if args.recover:
        success = recover_from_misclick()
        return 0 if success else 1

    if args.ai_find:
        if not HAS_SMART_DETECTOR:
            print("[ERROR] AI Vision not available")
            print("Install: pip install anthropic Pillow")
            return 1
        success = ai_find_and_tap(args.ai_find)
        return 0 if success else 1

    if args.tap:
        use_ai = not args.no_ai

        if len(args.tap) == 1:
            # Target name
            success = tap_target(args.tap[0], use_ai_fallback=use_ai)
        elif len(args.tap) == 2:
            # Custom coordinates
            try:
                x, y = int(args.tap[0]), int(args.tap[1])
                success = resilient_tap(x, y, "custom", use_ai_fallback=use_ai)
            except ValueError:
                print("[ERROR] Invalid coordinates. Use integers.")
                return 1
        else:
            print("[ERROR] Invalid --tap arguments. Use 'target_name' or 'x y'")
            return 1

        return 0 if success else 1

    # No arguments - show status
    print_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
