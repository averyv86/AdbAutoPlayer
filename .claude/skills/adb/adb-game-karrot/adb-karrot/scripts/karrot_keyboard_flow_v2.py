#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Karrot Signup Flow V2 - Enhanced Keyboard-Only Automation

Improvements over v1:
1. Better screen detection using BOTH activity name AND UI dump
2. Handle the verification popup (seen after neighborhood selection)
3. Support phone number entry
4. Longer waits after navigation (app takes 5-10 seconds to load)
5. Better crash detection and recovery

Key navigation sequences discovered:
- Welcome screen: 2x TAB + ENTER -> Neighborhood
- Neighborhood screen: TAB to search, or DPAD_DOWN + ENTER to select first
- Verification popup: Multiple TAB to reach "Verify now (30 sec)" button, then ENTER
- Phone entry: TAB to input field, enter digits, TAB + ENTER to submit

Phone number to use: 01039705176
Neighborhood: 서초동 (but can use GPS selection instead)

Usage:
    uv run karrot_keyboard_flow_v2.py [--phone 01039705176] [--neighborhood 서초동]
"""

import subprocess
import time
import argparse
import sys
import re
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
    delay: float = 0.5
    long_wait: float = 8.0  # Wait after navigation (app takes 5-10s to load)


def run_adb(cmd: str, timeout: int = 15) -> tuple[int, str]:
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


def keyevent(keycode: str, delay: float = 0.3):
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
    _, output = run_adb("dumpsys activity activities 2>/dev/null | grep -A 5 mFocusedApp")
    return output.strip()


def get_ui_dump() -> str:
    """Get UI hierarchy dump"""
    _, output = run_adb("uiautomator dump /dev/tty 2>/dev/null")
    return output.strip()


def check_ui_contains(patterns: list[str]) -> bool:
    """Check if UI dump contains any of the given patterns"""
    ui_dump = get_ui_dump()
    for pattern in patterns:
        if pattern in ui_dump:
            return True
    return False


def detect_screen() -> Screen:
    """
    Detect current screen based on BOTH activity name AND UI content.
    This is more reliable than activity name alone.
    """
    activity = get_current_activity()
    
    # First check for crash conditions
    if "mFocusedApp=null" in activity or activity == "":
        return Screen.CRASHED
    if "FallbackHome" in activity:
        return Screen.CRASHED
    
    # Check for home screen
    if "MainActivity" in activity or "HomeActivity" in activity:
        return Screen.HOME
    
    # Check for welcome screen
    if "GuideActivity" in activity:
        return Screen.WELCOME
    
    # KrSignUpOrInActivity could be either neighborhood OR verification popup
    if "KrSignUpOrInActivity" in activity:
        # Check UI content to distinguish
        if check_ui_contains(["본인인증", "Verify now", "인증하기", "30초"]):
            return Screen.VERIFICATION
        elif check_ui_contains(["내 동네", "neighborhood", "서초동", "강남구"]):
            return Screen.NEIGHBORHOOD
        else:
            # Default to neighborhood if unsure
            return Screen.NEIGHBORHOOD
    
    # Check for phone entry screen
    if check_ui_contains(["휴대폰 번호", "phone number", "010"]):
        return Screen.PHONE_ENTRY
    
    # Check for SMS code screen
    if check_ui_contains(["인증번호", "verification code", "SMS"]):
        return Screen.SMS_CODE
    
    return Screen.UNKNOWN


def restart_app():
    """Force stop and restart Karrot"""
    print("🔄 Restarting Karrot...")
    run_adb(f"am force-stop {PACKAGE}")
    time.sleep(2)
    run_adb(f"monkey -p {PACKAGE} -c android.intent.category.LAUNCHER 1")
    time.sleep(8)  # Wait for app to fully load


def navigate_welcome_to_neighborhood(delay: float = 0.5, long_wait: float = 8.0):
    """Navigate from Welcome screen to Neighborhood selection"""
    print("📱 Welcome screen -> Neighborhood selection")
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    print(f"   ⏳ Waiting {long_wait}s for screen to load...")
    time.sleep(long_wait)


def select_neighborhood_gps(delay: float = 0.5, long_wait: float = 8.0):
    """Select neighborhood using GPS (first option)"""
    print("🏘️ Selecting neighborhood via GPS...")
    # DPAD_DOWN to select first neighborhood
    keyevent("KEYCODE_DPAD_DOWN", delay)
    keyevent("KEYCODE_ENTER", delay)
    print(f"   ⏳ Waiting {long_wait}s for verification popup...")
    time.sleep(long_wait)


def select_neighborhood_search(neighborhood: str, delay: float = 0.5, long_wait: float = 8.0):
    """Select neighborhood by searching (not recommended - Korean input is hard)"""
    print(f"🏘️ Searching for neighborhood: {neighborhood}")
    # TAB to search field
    keyevent("KEYCODE_TAB", delay)
    # Note: Korean input is problematic, GPS selection is preferred
    print("   ⚠️ Warning: Korean text input may not work via ADB")
    time.sleep(long_wait)


def click_verify_button(delay: float = 0.5, long_wait: float = 8.0):
    """
    Click Verify button on identity verification popup.
    The popup appears after neighborhood selection.
    Button text: "Verify now (30 sec)" or "본인인증 (30초)"
    """
    print("✅ Clicking Verify button on verification popup...")
    # Navigate through popup elements to reach Verify button
    # Popup structure: Title -> Description -> Verify button (bottom)
    for i in range(8):
        keyevent("KEYCODE_TAB", delay)
        if i == 7:
            print(f"   🎯 Tab {i+1}: Should be on Verify button")
    
    keyevent("KEYCODE_ENTER", delay)
    print(f"   ⏳ Waiting {long_wait}s for phone entry screen...")
    time.sleep(long_wait)


def enter_phone_number(phone: str, delay: float = 0.5, long_wait: float = 8.0):
    """Enter phone number"""
    print(f"📞 Entering phone number: {phone}")
    # Navigate to phone input field
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_TAB", delay)
    
    # Enter number (ASCII only)
    text_input(phone, delay)
    
    # Submit
    keyevent("KEYCODE_TAB", delay)
    keyevent("KEYCODE_ENTER", delay)
    print(f"   ⏳ Waiting {long_wait}s for SMS screen...")
    time.sleep(long_wait)


def enter_sms_code(code: str, delay: float = 0.5, long_wait: float = 8.0):
    """Enter SMS verification code (manual input required)"""
    print(f"📨 SMS code entry screen detected")
    print(f"   ⚠️ Manual SMS code entry required: {code}")
    print(f"   Press ENTER when done, or Ctrl+C to abort")
    try:
        input()
        print(f"   ⏳ Waiting {long_wait}s for home screen...")
        time.sleep(long_wait)
    except KeyboardInterrupt:
        print("\n   ⛔ Aborted by user")
        sys.exit(1)


def run_flow(config: FlowConfig) -> bool:
    """Run the complete signup flow"""
    retries = 0
    stuck_count = 0
    last_screen = None
    
    while retries < config.max_retries:
        screen = detect_screen()
        print(f"\n📍 Current screen: {screen.value}")
        
        # Detect if we're stuck on the same screen
        if screen == last_screen:
            stuck_count += 1
            if stuck_count >= 3:
                print(f"⚠️ Stuck on {screen.value} for 3 iterations, trying restart...")
                restart_app()
                stuck_count = 0
                retries += 1
                continue
        else:
            stuck_count = 0
        
        last_screen = screen
        
        if screen == Screen.CRASHED:
            print(f"💥 App crashed! Retry {retries + 1}/{config.max_retries}")
            restart_app()
            retries += 1
            continue
        
        if screen == Screen.WELCOME:
            navigate_welcome_to_neighborhood(config.delay, config.long_wait)
            continue
        
        if screen == Screen.NEIGHBORHOOD:
            select_neighborhood_gps(config.delay, config.long_wait)
            continue
        
        if screen == Screen.VERIFICATION:
            click_verify_button(config.delay, config.long_wait)
            continue
        
        if screen == Screen.PHONE_ENTRY:
            enter_phone_number(config.phone, config.delay, config.long_wait)
            continue
        
        if screen == Screen.SMS_CODE:
            enter_sms_code("", config.delay, config.long_wait)
            continue
        
        if screen == Screen.HOME:
            print("🎉 SUCCESS! Reached home screen!")
            return True
        
        if screen == Screen.UNKNOWN:
            print("❓ Unknown screen, trying TAB + ENTER...")
            keyevent("KEYCODE_TAB", config.delay)
            keyevent("KEYCODE_ENTER", config.delay)
            time.sleep(config.long_wait)
            continue
    
    print(f"❌ Failed after {config.max_retries} retries")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Karrot Signup Flow V2 - Enhanced Keyboard-Only Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default phone number (01039705176)
  uv run karrot_keyboard_flow_v2.py
  
  # Custom phone number
  uv run karrot_keyboard_flow_v2.py --phone 01012345678
  
  # Faster delays (less safe)
  uv run karrot_keyboard_flow_v2.py --delay 0.3 --long-wait 5
  
  # More retries
  uv run karrot_keyboard_flow_v2.py --retries 10
        """
    )
    parser.add_argument("--phone", default="01039705176", help="Phone number")
    parser.add_argument("--neighborhood", default="서초동", help="Neighborhood name (not used for GPS selection)")
    parser.add_argument("--retries", type=int, default=5, help="Max retries")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between keyevents")
    parser.add_argument("--long-wait", type=float, default=8.0, help="Wait time after screen navigation")
    args = parser.parse_args()
    
    config = FlowConfig(
        phone=args.phone,
        neighborhood=args.neighborhood,
        max_retries=args.retries,
        delay=args.delay,
        long_wait=args.long_wait
    )
    
    print("=" * 60)
    print("🥕 Karrot Signup Flow V2 - Enhanced Keyboard Automation")
    print("=" * 60)
    print(f"📞 Phone: {config.phone}")
    print(f"🏘️ Neighborhood: GPS selection (first option)")
    print(f"🔄 Max retries: {config.max_retries}")
    print(f"⏱️ Delay: {config.delay}s, Long wait: {config.long_wait}s")
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
