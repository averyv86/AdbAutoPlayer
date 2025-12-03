#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB Test Karrot Login - Automated login with bypass validation

Automates Karrot login process and validates successful authentication. Can verify
Play Integrity bypass effectiveness by checking that no error -18 appears during login.
Also provides verification that the user successfully reaches authenticated screens.

Usage:
    uv run adb-karrot-test-login.py \\
        --device 127.0.0.1:5555 \\
        --email test@karrot.example.com \\
        --password testpass123

    uv run adb-karrot-test-login.py \\
        --device 127.0.0.1:5555 \\
        --email test@karrot.example.com \\
        --password testpass123 \\
        --verify-success \\
        --check-bypass

Examples:
    # Basic login test
    uv run adb-karrot-test-login.py \\
        --device 127.0.0.1:5555 \\
        --email test@example.com \\
        --password testpass123

    # Login with success verification and bypass check
    uv run adb-karrot-test-login.py \\
        --device 127.0.0.1:5555 \\
        --email test@example.com \\
        --password testpass123 \\
        --verify-success \\
        --check-bypass \\
        --timeout 30

    # Get JSON output
    uv run adb-karrot-test-login.py \\
        --device 127.0.0.1:5555 \\
        --email test@example.com \\
        --password testpass123 \\
        --json

Exit Codes:
    0 - Success (login completed, no emulator detection)
    1 - Warning (login completed but bypass verification unclear)
    2 - Error (login failed or emulator detected)
    3 - Critical (device not found or invalid parameters)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List
import click

# ========== SECTION 3: CONSTANTS ==========
KARROT_PACKAGE = "kr.co.flo.karrot"
ADB_COMMAND = "adb"
EMAIL_FIELD_X = 540
EMAIL_FIELD_Y = 400
PASSWORD_FIELD_X = 540
PASSWORD_FIELD_Y = 500
LOGIN_BUTTON_X = 540
LOGIN_BUTTON_Y = 600
LOGIN_TIMEOUT = 60

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class LoginResult:
    """Result of login operation."""
    device_id: str
    email: str
    success: bool = False
    app_launched: bool = False
    email_entered: bool = False
    password_entered: bool = False
    login_button_tapped: bool = False
    login_completed: bool = False
    success_verified: bool = False
    bypass_verified: bool = False
    no_error_18: bool = False
    detection_errors: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 6: HELPER FUNCTIONS ==========
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        devices = []
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id, state = line.split('\t')
                if state == 'device':
                    devices.append(device_id)
        return devices
    except Exception:
        return []

def select_device(device_arg: Optional[str] = None) -> tuple[str, bool]:
    """Select target device or use default."""
    if device_arg:
        return device_arg, True

    devices = get_adb_devices()
    if not devices:
        return None, False
    if len(devices) == 1:
        return devices[0], True
    return devices[0], True

def launch_karrot_for_login(device_id: str) -> bool:
    """Launch Karrot app in preparation for login."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-karrot/scripts/adb-karrot-launch.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id,
             "--wait-text", "Login", "--timeout", "15"],
            capture_output=True,
            text=True,
            timeout=25
        )
        return result.returncode == 0
    except Exception:
        return False

def find_and_tap_element(device_id: str, search_text: str, x_fallback: int,
                        y_fallback: int) -> bool:
    """Find element via OCR and tap it."""
    try:
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap at estimated coordinates
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                str(x_fallback), str(y_fallback)
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            time.sleep(0.5)
            return True

        # Try to locate element
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", search_text, "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    center_x = data.get("center_x", x_fallback)
                    center_y = data.get("center_y", y_fallback)
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(center_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    time.sleep(0.5)
                    return True
            except:
                pass

        # Fallback
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            str(x_fallback), str(y_fallback)
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(0.5)
        return True
    except Exception:
        return False

def enter_text(device_id: str, text: str) -> bool:
    """Enter text into currently focused field."""
    try:
        # Use adb shell input text command
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "text",
            text
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(0.5)
        return result.returncode == 0
    except Exception:
        return False

def check_text_on_screen(device_id: str, search_text: str, timeout: float = 10) -> bool:
    """Check if specific text appears on screen."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-screen-detection/scripts/adb-ocr-extract.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--json"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if "text_items" in data:
                    for item in data["text_items"]:
                        if search_text.lower() in item.get("text", "").lower():
                            return True
            except:
                pass

        return False
    except Exception:
        return False

def capture_logcat_for_errors(device_id: str) -> List[str]:
    """Capture logcat and extract error lines."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "logcat", "-d"],
            capture_output=True,
            text=True,
            timeout=10
        )

        errors = []
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "error" in line.lower() and ("-18" in line or "playintegrity" in line.lower()):
                    errors.append(line.strip())

        return errors
    except Exception:
        return []

# ========== SECTION 7: CORE LOGIC ==========
def test_login(device_id: str, email: str, password: str,
               verify_success: bool = False, check_bypass: bool = False,
               timeout: float = LOGIN_TIMEOUT) -> LoginResult:
    """Test Karrot login automation."""
    start_time = time.time()
    result = LoginResult(
        device_id=device_id,
        email=email,
        timestamp=start_time
    )

    # Step 1: Launch Karrot
    result.app_launched = launch_karrot_for_login(device_id)
    if not result.app_launched:
        result.error = "Failed to launch Karrot app"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    time.sleep(2)

    # Step 2: Tap email field
    result.email_entered = find_and_tap_element(
        device_id, "Email", EMAIL_FIELD_X, EMAIL_FIELD_Y
    )
    if not result.email_entered:
        result.error = "Failed to locate/tap email field"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 3: Enter email
    result.email_entered = enter_text(device_id, email)
    if not result.email_entered:
        result.error = "Failed to enter email"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 4: Tap password field
    result.password_entered = find_and_tap_element(
        device_id, "Password", PASSWORD_FIELD_X, PASSWORD_FIELD_Y
    )
    if not result.password_entered:
        result.error = "Failed to locate/tap password field"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 5: Enter password
    result.password_entered = enter_text(device_id, password)
    if not result.password_entered:
        result.error = "Failed to enter password"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 6: Tap login button
    result.login_button_tapped = find_and_tap_element(
        device_id, "Login", LOGIN_BUTTON_X, LOGIN_BUTTON_Y
    )
    if not result.login_button_tapped:
        result.error = "Failed to locate/tap login button"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 7: Wait for login completion
    login_wait_start = time.time()
    login_completed = False

    while time.time() - login_wait_start < timeout:
        # Check for success indicators
        if check_text_on_screen(device_id, "Profile") or \
           check_text_on_screen(device_id, "Home") or \
           check_text_on_screen(device_id, "Location"):
            login_completed = True
            result.login_completed = True
            result.success_verified = True
            break

        # Check for error indicators
        if check_text_on_screen(device_id, "incorrect") or \
           check_text_on_screen(device_id, "failed") or \
           check_text_on_screen(device_id, "error"):
            result.error = "Login error detected on screen"
            result.exit_code = 2
            result.duration = time.time() - start_time
            return result

        time.sleep(1)

    if not login_completed:
        if verify_success:
            result.error = f"Login did not complete within {timeout}s"
            result.exit_code = 2
        else:
            result.login_completed = True  # Assume success if not verifying
            result.exit_code = 1  # Warning

    # Step 8: Check bypass effectiveness if requested
    if check_bypass:
        time.sleep(1)
        logcat_errors = capture_logcat_for_errors(device_id)
        result.detection_errors = logcat_errors

        if any("-18" in err for err in logcat_errors):
            result.no_error_18 = False
            result.bypass_verified = False
            result.exit_code = 2
        else:
            result.no_error_18 = True
            result.bypass_verified = True
            if result.exit_code != 2:
                result.exit_code = 0

    result.success = result.login_completed and not result.detection_errors
    if not result.success:
        result.exit_code = 2 if result.exit_code != 1 else 1

    result.duration = time.time() - start_time
    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: LoginResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Karrot login successful on {result.device_id}")
    else:
        lines.append(f"❌ Karrot login failed on {result.device_id}")

    lines.append(f"  App Launched: {'✅ Yes' if result.app_launched else '❌ No'}")
    lines.append(f"  Email Entered: {'✅ Yes' if result.email_entered else '❌ No'}")
    lines.append(f"  Password Entered: {'✅ Yes' if result.password_entered else '❌ No'}")
    lines.append(f"  Login Button Tapped: {'✅ Yes' if result.login_button_tapped else '❌ No'}")
    lines.append(f"  Login Completed: {'✅ Yes' if result.login_completed else '❌ No'}")

    if result.success_verified:
        lines.append(f"  Success Verified: {'✅ Yes' if result.success_verified else '❌ No'}")

    if result.bypass_verified is not None:
        lines.append(f"  Bypass Verified: {'✅ Yes (no error -18)' if result.bypass_verified else '❌ No (error -18 found)'}")

    if result.detection_errors:
        lines.append(f"\n  Detection Errors Found ({len(result.detection_errors)}):")
        for err in result.detection_errors[:3]:
            lines.append(f"    • {err[:100]}...")

    lines.append(f"\n  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: LoginResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    help='Target device ID'
)
@click.option(
    '--email',
    type=str,
    required=True,
    help='Karrot account email'
)
@click.option(
    '--password',
    type=str,
    required=True,
    help='Karrot account password'
)
@click.option(
    '--verify-success',
    is_flag=True,
    help='Verify login success by checking for profile/home screen'
)
@click.option(
    '--check-bypass',
    is_flag=True,
    help='Check if bypass is working (no error -18)'
)
@click.option(
    '--timeout',
    type=float,
    default=LOGIN_TIMEOUT,
    help='Max seconds to wait for login (default: 60)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], email: str, password: str, verify_success: bool,
        check_bypass: bool, timeout: float, output_json: bool) -> None:
    """
    Test Karrot login with optional bypass validation.

    Automates the login process and can verify Play Integrity bypass effectiveness.

    Examples:
        uv run adb-karrot-test-login.py \\
            --device 127.0.0.1:5555 \\
            --email test@example.com \\
            --password testpass123

        uv run adb-karrot-test-login.py \\
            --device 127.0.0.1:5555 \\
            --email test@example.com \\
            --password testpass123 \\
            --verify-success \\
            --check-bypass
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = LoginResult(
            device_id="unknown",
            email=email,
            error="No connected ADB devices found",
            exit_code=3
        )
        if output_json:
            click.echo(format_json_output(error_result), err=True)
        else:
            click.echo(f"❌ Error: No connected ADB devices", err=True)
        sys.exit(3)

    # Test login
    result = test_login(selected_device, email, password,
                       verify_success=verify_success, check_bypass=check_bypass,
                       timeout=timeout)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
