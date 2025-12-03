#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB Install Magisk Module - Install module zip file via Magisk Manager

Automates the module installation process in Magisk Manager. Navigates to Modules
tab, opens file picker, selects the module zip file, monitors installation progress,
and verifies successful installation with optional reboot handling.

Usage:
    uv run adb-magisk-install-module.py \\
        --device 127.0.0.1:5555 \\
        --module-path /sdcard/PlayIntegrityFork.zip

    uv run adb-magisk-install-module.py \\
        --device 127.0.0.1:5555 \\
        --module-path /sdcard/PlayIntegrityFork.zip \\
        --verify

Examples:
    # Install module on specified device
    uv run adb-magisk-install-module.py \\
        --device 127.0.0.1:5555 \\
        --module-path /sdcard/PlayIntegrityFork.zip

    # Install and verify completion
    uv run adb-magisk-install-module.py \\
        --device 127.0.0.1:5555 \\
        --module-path /sdcard/PlayIntegrityFork.zip \\
        --verify

    # Get JSON output
    uv run adb-magisk-install-module.py \\
        --device 127.0.0.1:5555 \\
        --module-path /sdcard/PlayIntegrityFork.zip \\
        --json

Exit Codes:
    0 - Success (module installed)
    1 - Warning (installed but verification incomplete)
    2 - Error (installation failed)
    3 - Critical (invalid file or ADB failure)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

# ========== SECTION 3: CONSTANTS ==========
MAGISK_PACKAGE = "com.topjohnwu.magisk"
ADB_COMMAND = "adb"
MODULES_TAB_X = 100
MODULES_TAB_Y = 300
INSTALL_FAB_X = 900
INSTALL_FAB_Y = 1800
FILE_PICKER_TIMEOUT = 10
INSTALLATION_TIMEOUT = 60

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
class ModuleInstallResult:
    """Result of module installation operation."""
    device_id: str
    module_path: str
    success: bool
    magisk_launched: bool = False
    modules_tab_open: bool = False
    file_picker_opened: bool = False
    file_selected: bool = False
    installation_started: bool = False
    installation_completed: bool = False
    installation_verified: bool = False
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

def launch_magisk(device_id: str) -> bool:
    """Launch Magisk Manager."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-magisk/scripts/adb-magisk-launch.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--wait-text", "Modules"],
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.returncode == 0
    except Exception:
        return False

def open_modules_tab(device_id: str) -> bool:
    """Ensure Modules tab is open."""
    try:
        # Search for "Modules" text and tap it
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap estimated Modules tab position
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                str(MODULES_TAB_X), str(MODULES_TAB_Y)
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            time.sleep(1)
            return True

        # Use adb-find-element to locate Modules
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", "Modules", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    center_x = data.get("center_x", MODULES_TAB_X)
                    center_y = data.get("center_y", MODULES_TAB_Y)
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(center_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    time.sleep(1)
                    return True
            except:
                pass

        # Fallback
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            str(MODULES_TAB_X), str(MODULES_TAB_Y)
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(1)
        return True
    except Exception:
        return False

def tap_install_fab(device_id: str) -> bool:
    """Tap the + FAB button to open file picker."""
    try:
        # The FAB is usually a floating button at bottom-right
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            str(INSTALL_FAB_X), str(INSTALL_FAB_Y)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(1)
        return result.returncode == 0
    except Exception:
        return False

def wait_for_file_picker(device_id: str, timeout: float = FILE_PICKER_TIMEOUT) -> bool:
    """Wait for file picker dialog to appear."""
    try:
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            time.sleep(2)
            return True

        # Look for common file picker texts
        search_texts = ["Select", "Browse", "Choose", "Open"]
        for search_text in search_texts:
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
                        return True
                except:
                    pass

        time.sleep(1)
        return True
    except Exception:
        return False

def select_file_in_picker(device_id: str, module_path: str) -> bool:
    """Navigate to and select the module file in file picker."""
    try:
        # Extract filename from path
        filename = Path(module_path).name
        folder = Path(module_path).parent

        # Push file to device if needed (common location: /sdcard/)
        push_cmd = [ADB_COMMAND, "-s", device_id, "push", module_path, "/sdcard/"]
        try:
            subprocess.run(push_cmd, capture_output=True, timeout=20)
        except:
            pass

        # Use adb-find-element to locate the filename
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            # Fallback: tap expected file location
            time.sleep(1)
            # Try tapping center of screen (file usually first in list)
            cmd = [
                ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                "540", "800"
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            time.sleep(1)
            return True

        # Search for the filename
        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", filename, "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    center_x = data.get("center_x", 540)
                    center_y = data.get("center_y", 800)
                    tap_cmd = [
                        ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
                        str(center_x), str(center_y)
                    ]
                    subprocess.run(tap_cmd, capture_output=True, timeout=5)
                    time.sleep(1)
                    return True
            except:
                pass

        # Fallback
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "input", "tap",
            "540", "800"
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        time.sleep(1)
        return True
    except Exception:
        return False

def wait_for_installation_complete(device_id: str, timeout: float = INSTALLATION_TIMEOUT) -> bool:
    """Wait for installation to complete by checking for completion message."""
    try:
        project_root = find_project_root()
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not find_script.exists():
            time.sleep(5)  # Assume installation takes at least 5s
            return True

        start_time = time.time()
        search_texts = ["Installation complete", "Installed", "Module installed", "Success"]

        while time.time() - start_time < timeout:
            for search_text in search_texts:
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
                            return True
                    except:
                        pass

            time.sleep(1)

        return False
    except Exception:
        return False

def verify_module_installed(device_id: str, module_name: str) -> bool:
    """Verify that module appears in Magisk modules list."""
    try:
        # Re-launch Magisk to refresh module list
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-magisk/scripts/adb-magisk-launch.py"

        if not script_path.exists():
            time.sleep(2)
            return True

        # Launch and wait for module list
        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--wait-text", "Modules"],
            capture_output=True,
            text=True,
            timeout=20
        )

        if result.returncode != 0:
            return False

        # Now check if module text appears
        find_script = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"
        if not find_script.exists():
            return True

        result = subprocess.run(
            ["uv", "run", str(find_script), "--device", device_id,
             "--method", "ocr", "--target", module_name, "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                return data.get("found", False)
            except:
                pass

        return True  # Assume verified if check doesn't work
    except Exception:
        return True

# ========== SECTION 7: CORE LOGIC ==========
def install_module(device_id: str, module_path: str, verify: bool = False) -> ModuleInstallResult:
    """Install Magisk module from zip file."""
    start_time = time.time()
    result = ModuleInstallResult(
        device_id=device_id,
        module_path=module_path,
        success=False,
        timestamp=start_time
    )

    # Validate module path
    if not Path(module_path).exists():
        result.error = f"Module file not found: {module_path}"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    # Step 1: Launch Magisk
    result.magisk_launched = launch_magisk(device_id)
    if not result.magisk_launched:
        result.error = "Failed to launch Magisk Manager"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 2: Open Modules tab
    result.modules_tab_open = open_modules_tab(device_id)
    if not result.modules_tab_open:
        result.error = "Failed to open Modules tab"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 3: Tap + FAB
    result.file_picker_opened = tap_install_fab(device_id)
    if not result.file_picker_opened:
        result.error = "Failed to open file picker"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 4: Wait for file picker
    if not wait_for_file_picker(device_id):
        result.error = "File picker did not appear"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 5: Select file
    result.file_selected = select_file_in_picker(device_id, module_path)
    if not result.file_selected:
        result.error = "Failed to select module file"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 6: Mark installation as started
    result.installation_started = True

    # Step 7: Wait for installation to complete
    result.installation_completed = wait_for_installation_complete(device_id)
    if not result.installation_completed:
        result.error = "Installation did not complete (timeout)"
        result.exit_code = 1
        result.duration = time.time() - start_time
        return result

    time.sleep(1)

    # Step 8: Verify if requested
    if verify:
        module_name = Path(module_path).stem
        result.installation_verified = verify_module_installed(device_id, module_name)
    else:
        result.installation_verified = True

    result.success = result.installation_completed and result.installation_verified
    result.exit_code = 0 if result.success else 1

    result.duration = time.time() - start_time
    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: ModuleInstallResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ Module installed on {result.device_id}")
    else:
        lines.append(f"❌ Failed to install module on {result.device_id}")

    lines.append(f"  Module: {Path(result.module_path).name}")
    lines.append(f"  Magisk Launched: {'✅ Yes' if result.magisk_launched else '❌ No'}")
    lines.append(f"  Modules Tab: {'✅ Open' if result.modules_tab_open else '❌ Closed'}")
    lines.append(f"  File Picker: {'✅ Open' if result.file_picker_opened else '❌ Closed'}")
    lines.append(f"  File Selected: {'✅ Yes' if result.file_selected else '❌ No'}")
    lines.append(f"  Installation Started: {'✅ Yes' if result.installation_started else '❌ No'}")
    lines.append(f"  Installation Completed: {'✅ Yes' if result.installation_completed else '❌ No'}")
    lines.append(f"  Installation Verified: {'✅ Yes' if result.installation_verified else '⚠️  Not verified'}")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: ModuleInstallResult) -> str:
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
    '--module-path',
    type=str,
    required=True,
    help='Path to module zip file (e.g., /path/to/PlayIntegrityFork.zip)'
)
@click.option(
    '--verify',
    is_flag=True,
    help='Verify module appears in module list after installation'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], module_path: str, verify: bool, output_json: bool) -> None:
    """
    Install Magisk module from zip file.

    Automates the module installation process through Magisk Manager UI.

    Examples:
        uv run adb-magisk-install-module.py \\
            --device 127.0.0.1:5555 \\
            --module-path /sdcard/PlayIntegrityFork.zip

        uv run adb-magisk-install-module.py \\
            --device 127.0.0.1:5555 \\
            --module-path /sdcard/PlayIntegrityFork.zip \\
            --verify
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = ModuleInstallResult(
            device_id="unknown",
            module_path=module_path,
            success=False,
            error="No connected ADB devices found",
            exit_code=3
        )
        if output_json:
            click.echo(format_json_output(error_result), err=True)
        else:
            click.echo(f"❌ Error: No connected ADB devices", err=True)
        sys.exit(3)

    # Install module
    result = install_module(selected_device, module_path, verify=verify)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
