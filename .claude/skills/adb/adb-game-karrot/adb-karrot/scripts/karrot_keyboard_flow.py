#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Karrot Signup Flow - Keyboard-Only Automation

Uses ONLY keyboard navigation to avoid anti-automation detection.
Implements crash recovery and state detection.

Flow:
1. Welcome screen -> Get started (2 TAB + ENTER)
2. Neighborhood selection -> Select first (TAB + ENTER)
3. Identity verification -> Verify (TAB + ENTER)
4. Phone entry -> Enter number
5. SMS verification -> Enter code
6. Home screen

Usage:
    uv run karrot_keyboard_flow.py [--phone 01012345678] [--neighborhood 서초동]
"""

import subprocess
import time
import argparse
import sys
from typing import Optional
from dataclasses import dataclass
from enum import Enum

# Constants
PACKAGE = "com.towneers.www"
LAUNCH_ACTIVITY = ".launcher.LauncherActivity"

class Screen(Enum):
    UNKNOWN = "unknown"
    WELCOME = "welcome"  # GuideActivity
    NEIGHBORHOOD = "neighborhood"  # KrSignUpOrInActivity - neighborhood selection
    VERIFICATION = "verification"  # Identity verification popup
    PHONE_ENTRY = "phone_entry"  # Phone number input
    SMS_CODE = "sms_code"  # SMS verification code
    HOME = "home"  # Main home screen
    CRASHED = "crashed"  # FallbackHome or null


@dataclass
class FlowConfig:
    phone: str = "01039705176"
    neighborhood: str = "서초동"
    max_retries: int = 5
    delay: float = 0.3


def run_adb(cmd: str, timeout: int = 10) -> tuple[int, str]:
    """Run ADB command and return (returncode, output)"""
    try:
        result = subprocess.run(
            f"adb shell {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def keyevent(keycode: str, delay: float = 0.2):
    """Send keyevent via ADB"""
    run_adb(f"input keyevent {keycode}")
    time.sleep(delay)


def tap(x: int, y: int, delay: float = 0.5):
    """Tap at coordinates (use sparingly - may crash app)"""
    run_adb(f"input tap {x} {y}")
    time.sleep(delay)


def text_input(text: str, delay: float = 0.5):
    """Input text (ASCII only)"""
    # Only ASCII characters work with input text
    if text.isascii():
        run_adb(f'input text "{text}"')
        time.sleep(delay)
    else:
        print(f"Warning: Non-ASCII text '{text}' cannot be input directly")


def get_current_activity() -> str:
    """Get current focused activity"""
    _, output = run_adb("dumpsys activity activities 2>/dev/null | grep mFocusedApp")
    return output.strip()


def detect_screen() -> Screen:
    """Detect current screen based on activity"""
    activity = get_current_activity()

    if "mFocusedApp=null" in activity or activity == "":
        return Screen.CRASHED
    if "FallbackHome" in activity:
        return Screen.CRASHED
    if "GuideActivity" in activity:
        return Screen.WELCOME
    if "KrSignUpOrInActivity" in activity:
        # Could be neighborhood or verification screen
        # Need to check UI elements
        return Screen.NEIGHBORHOOD
    if "MainActivity" in activity or "HomeActivity" in activity:
        return Screen.HOME

    return Screen.UNKNOWN


def restart_app():
    """Force stop and restart Karrot"""
    print("🔄 Restarting Karrot...")
    run_adb(f"am force-stop {PACKAGE}")
    time.sleep(1)
    run_adb(f"monkey -p {PACKAGE} -c android.intent.category.LAUNCHER 1")
    time.sleep(5)


def navigate_welcome_to_neighborhood(delay: float = 0.3):
    """Navigate from Welcome screen to Neighborhood selection"""
    print("📱 Welcome screen -> Neighborhood selection")
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    time.sleep(2)


def select_neighborhood(delay: float = 0.3):
    """Select first neighborhood in the list"""
    print("🏘️ Selecting neighborhood...")
    # Navigate down to neighborhood list
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    time.sleep(2)


def click_verify_button(delay: float = 0.3):
    """Click Verify button on identity verification popup"""
    print("✅ Clicking Verify button...")
    # Navigate to Verify button (bottom of popup)
    for _ in range(5):
        keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    time.sleep(2)


def enter_phone_number(phone: str, delay: float = 0.3):
    """Enter phone number"""
    print(f"📞 Entering phone number: {phone}")
    # Navigate to phone input field
    keyevent("KEYCODE_TAB", delay)
    # Enter number (ASCII only)
    text_input(phone, delay)
    # Submit
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    time.sleep(3)


def run_flow(config: FlowConfig) -> bool:
    """Run the complete signup flow"""
    retries = 0

    while retries < config.max_retries:
        screen = detect_screen()
        print(f"\n📍 Current screen: {screen.value}")

        if screen == Screen.CRASHED:
            print(f"💥 App crashed! Retry {retries + 1}/{config.max_retries}")
            restart_app()
            retries += 1
            time.sleep(2)
            continue

        if screen == Screen.WELCOME:
            navigate_welcome_to_neighborhood(config.delay)
            continue

        if screen == Screen.NEIGHBORHOOD:
            select_neighborhood(config.delay)
            continue

        if screen == Screen.VERIFICATION:
            click_verify_button(config.delay)
            continue

        if screen == Screen.PHONE_ENTRY:
            enter_phone_number(config.phone, config.delay)
            continue

        if screen == Screen.HOME:
            print("🎉 SUCCESS! Reached home screen!")
            return True

        if screen == Screen.UNKNOWN:
            print("❓ Unknown screen, trying TAB + ENTER...")
            keyevent("KEYCODE_TAB", config.delay)
            keyevent("KEYCODE_ENTER", config.delay)
            time.sleep(2)
            continue

    print(f"❌ Failed after {config.max_retries} retries")
    return False


def main():
    parser = argparse.ArgumentParser(description="Karrot Signup Flow Automation")
    parser.add_argument("--phone", default="01039705176", help="Phone number")
    parser.add_argument("--neighborhood", default="서초동", help="Neighborhood name")
    parser.add_argument("--retries", type=int, default=5, help="Max retries")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between actions")
    args = parser.parse_args()

    config = FlowConfig(
        phone=args.phone,
        neighborhood=args.neighborhood,
        max_retries=args.retries,
        delay=args.delay
    )

    print("=" * 60)
    print("🥕 Karrot Signup Flow - Keyboard-Only Automation")
    print("=" * 60)
    print(f"📞 Phone: {config.phone}")
    print(f"🏘️ Neighborhood: {config.neighborhood}")
    print(f"🔄 Max retries: {config.max_retries}")
    print("=" * 60)

    # Ensure app is running
    screen = detect_screen()
    if screen == Screen.CRASHED:
        restart_app()

    # Run flow
    success = run_flow(config)

    if success:
        print("\n✅ Flow completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Flow failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
