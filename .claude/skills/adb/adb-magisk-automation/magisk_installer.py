#!/usr/bin/env python3
"""Magisk Installation State Machine.

This module provides a state machine for automating Magisk installation
and Zygisk enablement via ADB.

States:
1. MAGISK_HOME - Main Magisk app screen
2. INSTALL_OPTIONS - Installation options screen
3. INSTALL_METHOD - Method selection screen
4. FILE_PICKER - File selection (for patch method)
5. PROGRESS - Installation progress
6. COMPLETE - Installation complete
7. POST_REBOOT - After device restart
8. SETTINGS - Magisk settings screen
9. ZYGISK_ENABLED - Zygisk successfully enabled

Created based on Magisk v27.0/30.6 UI flow.
Tested on Samsung SM-S908E (2560x1440).
"""

import time
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from adb_core.resolution_aware_tap import ResolutionAwareTap, TapResult
except ImportError:
    # Fallback for standalone usage
    from resolution_aware_tap import ResolutionAwareTap, TapResult


class MagiskState(Enum):
    """States in the Magisk installation flow."""
    UNKNOWN = auto()
    MAGISK_HOME = auto()
    INSTALL_OPTIONS = auto()
    INSTALL_METHOD = auto()
    FILE_PICKER = auto()
    PROGRESS = auto()
    COMPLETE = auto()
    POST_REBOOT = auto()
    SETTINGS = auto()
    ZYGISK_ENABLED = auto()
    ERROR = auto()


class InstallMethod(Enum):
    """Magisk installation methods."""
    DIRECT_INSTALL = "Direct Install (Recommended)"
    SELECT_AND_PATCH = "Select and Patch a File"


@dataclass
class MagiskStatus:
    """Current Magisk installation status."""
    installed_version: Optional[str] = None
    zygisk_enabled: bool = False
    ramdisk_supported: bool = False
    app_version: Optional[str] = None
    is_rooted: bool = False

    @property
    def needs_installation(self) -> bool:
        """Check if Magisk needs to be installed."""
        return self.installed_version is None or self.installed_version == "N/A"


@dataclass
class StateTransition:
    """Represents a state transition action."""
    from_state: MagiskState
    to_state: MagiskState
    action: str  # Text to tap or action to perform
    verify_text: Optional[str] = None  # Text to verify after transition


class MagiskInstaller:
    """State machine for Magisk installation.

    Usage:
        installer = MagiskInstaller(device_id="localhost:5555")

        # Check current status
        status = installer.get_magisk_status()
        print(f"Installed: {status.installed_version}")
        print(f"Zygisk: {status.zygisk_enabled}")

        # Navigate to install screen
        installer.navigate_to_install()

        # Full installation (requires boot.img for non-rooted devices)
        installer.install_magisk(boot_img_path="/sdcard/Download/boot.img")

        # Enable Zygisk (after installation)
        installer.enable_zygisk()
    """

    PACKAGE_NAME = "com.topjohnwu.magisk"
    MAIN_ACTIVITY = ".ui.MainActivity"

    # UI text markers for state detection
    STATE_MARKERS = {
        MagiskState.MAGISK_HOME: ["Installed", "Zygisk", "Ramdisk"],
        MagiskState.INSTALL_OPTIONS: ["Options", "Preserve AVB"],
        MagiskState.INSTALL_METHOD: ["Method", "LET'S GO", "Select and Patch"],
        MagiskState.FILE_PICKER: ["Recent", "Downloads", "Browse"],
        MagiskState.PROGRESS: ["Unpacking", "Patching", "All done"],
        MagiskState.COMPLETE: ["All done", "Reboot"],
        MagiskState.SETTINGS: ["Settings", "Zygisk", "Hide"],
    }

    def __init__(self, device_id: str = "localhost:5555"):
        """Initialize the Magisk installer.

        Args:
            device_id: ADB device identifier
        """
        self.device_id = device_id
        self.tap = ResolutionAwareTap(device_id)
        self.current_state = MagiskState.UNKNOWN
        self._callbacks: Dict[str, Callable] = {}

    def on_state_change(self, callback: Callable[[MagiskState, MagiskState], None]) -> None:
        """Register callback for state changes.

        Args:
            callback: Function called with (old_state, new_state)
        """
        self._callbacks['state_change'] = callback

    def _notify_state_change(self, old_state: MagiskState, new_state: MagiskState) -> None:
        """Notify registered callbacks of state change."""
        if 'state_change' in self._callbacks:
            self._callbacks['state_change'](old_state, new_state)

    def launch_magisk(self) -> bool:
        """Launch Magisk app.

        Returns:
            True if app launched successfully
        """
        cmd = f"am start -n {self.PACKAGE_NAME}/{self.MAIN_ACTIVITY}"
        self.tap.shell(cmd)
        time.sleep(2)

        # Verify app launched
        return self.detect_state() != MagiskState.UNKNOWN

    def detect_state(self) -> MagiskState:
        """Detect current UI state from UI dump.

        Returns:
            Detected MagiskState
        """
        ui_xml = self.tap.get_ui_dump(force_refresh=True)
        text_elements = [elem.text for elem in self.tap.get_all_text_elements(ui_xml)]

        # Check each state's markers
        for state, markers in self.STATE_MARKERS.items():
            if all(any(marker.lower() in text.lower() for text in text_elements)
                   for marker in markers):
                old_state = self.current_state
                self.current_state = state
                if old_state != state:
                    self._notify_state_change(old_state, state)
                return state

        return MagiskState.UNKNOWN

    def get_magisk_status(self) -> MagiskStatus:
        """Get current Magisk installation status.

        Returns:
            MagiskStatus with current state
        """
        # Ensure we're on home screen
        if self.current_state != MagiskState.MAGISK_HOME:
            self.launch_magisk()

        ui_xml = self.tap.get_ui_dump(force_refresh=True)
        status = MagiskStatus()

        # Parse installed version
        installed_match = re.search(r'text="Installed"[^>]*>.*?text="([^"]+)"', ui_xml, re.DOTALL)
        if installed_match:
            version = installed_match.group(1)
            status.installed_version = None if version == "N/A" else version
            status.is_rooted = version != "N/A"

        # Parse Zygisk status
        zygisk_match = re.search(r'text="Zygisk"[^>]*>.*?text="(Yes|No)"', ui_xml, re.DOTALL)
        if zygisk_match:
            status.zygisk_enabled = zygisk_match.group(1) == "Yes"

        # Parse Ramdisk status
        ramdisk_match = re.search(r'text="Ramdisk"[^>]*>.*?text="(Yes|No)"', ui_xml, re.DOTALL)
        if ramdisk_match:
            status.ramdisk_supported = ramdisk_match.group(1) == "Yes"

        # Parse app version
        app_match = re.search(r'text="(\d+\.\d+)\s*\((\d+)\)"', ui_xml)
        if app_match:
            status.app_version = f"{app_match.group(1)} ({app_match.group(2)})"

        return status

    def navigate_to_install(self) -> bool:
        """Navigate from home to install screen.

        Returns:
            True if navigation successful
        """
        if self.current_state != MagiskState.MAGISK_HOME:
            if not self.launch_magisk():
                return False

        # Tap Install button
        result = self.tap.find_and_tap("Install", timeout=5)
        if result != TapResult.SUCCESS:
            return False

        time.sleep(1)

        # Verify we reached install options
        return self.detect_state() in [
            MagiskState.INSTALL_OPTIONS,
            MagiskState.INSTALL_METHOD
        ]

    def select_install_method(self, method: InstallMethod) -> bool:
        """Select installation method.

        Args:
            method: Installation method to select

        Returns:
            True if method selected successfully
        """
        # First tap NEXT to expand method section if needed
        self.tap.find_and_tap("NEXT", timeout=3)
        time.sleep(1)

        # Check if method is available
        ui_xml = self.tap.get_ui_dump()

        if method == InstallMethod.DIRECT_INSTALL:
            # Direct Install requires existing root
            if "Direct Install" not in ui_xml:
                print("Direct Install not available (requires root)")
                return False
            return self.tap.find_and_tap("Direct Install") == TapResult.SUCCESS

        elif method == InstallMethod.SELECT_AND_PATCH:
            return self.tap.find_and_tap("Select and Patch") == TapResult.SUCCESS

        return False

    def wait_for_installation_complete(self, timeout: int = 300) -> bool:
        """Wait for installation to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if installation completed successfully
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            ui_xml = self.tap.get_ui_dump()

            # Check for completion
            if "All done" in ui_xml:
                self.current_state = MagiskState.COMPLETE
                return True

            # Check for errors
            if "Error" in ui_xml or "failed" in ui_xml.lower():
                self.current_state = MagiskState.ERROR
                return False

            time.sleep(2)

        return False

    def tap_reboot(self) -> bool:
        """Tap reboot button after installation.

        Returns:
            True if reboot initiated
        """
        if self.current_state != MagiskState.COMPLETE:
            return False

        result = self.tap.find_and_tap("Reboot", timeout=5)
        return result == TapResult.SUCCESS

    def navigate_to_settings(self) -> bool:
        """Navigate to Magisk settings.

        Returns:
            True if navigation successful
        """
        if self.current_state != MagiskState.MAGISK_HOME:
            if not self.launch_magisk():
                return False

        # Settings is typically a gear icon in top-right
        # Look for it by resource-id
        element = self.tap.find_element_by_resource_id(
            f"{self.PACKAGE_NAME}:id/action_settings"
        )

        if element:
            center_x, center_y = element.bounds.center
            result = self.tap.tap_with_verification(center_x, center_y)
            if result == TapResult.SUCCESS:
                time.sleep(1)
                return self.detect_state() == MagiskState.SETTINGS

        return False

    def enable_zygisk(self) -> bool:
        """Enable Zygisk in settings.

        Returns:
            True if Zygisk enabled successfully
        """
        # Navigate to settings first
        if self.current_state != MagiskState.SETTINGS:
            if not self.navigate_to_settings():
                return False

        # Find and tap Zygisk toggle
        ui_xml = self.tap.get_ui_dump()

        # Look for Zygisk toggle
        zygisk_element = self.tap.find_element_by_text("Zygisk", ui_xml=ui_xml)
        if not zygisk_element:
            return False

        # The toggle is usually to the right of the text
        toggle_x = zygisk_element.bounds.x2 + 100
        toggle_y = zygisk_element.bounds.center[1]

        result = self.tap.tap_with_verification(toggle_x, toggle_y)

        if result == TapResult.SUCCESS:
            # Verify Zygisk is now enabled
            time.sleep(1)
            status = self.get_magisk_status()
            return status.zygisk_enabled

        return False

    def install_magisk(
        self,
        boot_img_path: Optional[str] = None,
        method: Optional[InstallMethod] = None
    ) -> bool:
        """Perform full Magisk installation.

        Args:
            boot_img_path: Path to boot.img (required for non-rooted devices)
            method: Installation method (auto-detected if None)

        Returns:
            True if installation completed successfully
        """
        # Get current status
        status = self.get_magisk_status()

        # Determine method
        if method is None:
            if status.is_rooted:
                method = InstallMethod.DIRECT_INSTALL
            else:
                method = InstallMethod.SELECT_AND_PATCH

        # Navigate to install
        if not self.navigate_to_install():
            return False

        # Select method
        if not self.select_install_method(method):
            return False

        # Handle file selection for patch method
        if method == InstallMethod.SELECT_AND_PATCH:
            if not boot_img_path:
                print("boot.img path required for Select and Patch method")
                return False

            # Tap LET'S GO
            self.tap.find_and_tap("LET'S GO", timeout=5)
            time.sleep(1)

            # File picker will open - need to navigate to the file
            # This is device-specific and may need manual intervention
            print(f"Please select file: {boot_img_path}")
            # Wait for file selection
            time.sleep(5)

        # Wait for installation
        if not self.wait_for_installation_complete():
            return False

        # Installation complete!
        return True

    def full_setup(self, boot_img_path: Optional[str] = None) -> Dict[str, bool]:
        """Perform full Magisk + Zygisk setup.

        Args:
            boot_img_path: Path to boot.img (if needed)

        Returns:
            Dict with setup results
        """
        results = {
            'magisk_installed': False,
            'zygisk_enabled': False,
            'reboot_required': False
        }

        # Check current status
        status = self.get_magisk_status()

        if status.needs_installation:
            # Install Magisk
            results['magisk_installed'] = self.install_magisk(boot_img_path)
            results['reboot_required'] = True
        else:
            results['magisk_installed'] = True

        # Enable Zygisk if not already enabled
        if not status.zygisk_enabled and results['magisk_installed']:
            results['zygisk_enabled'] = self.enable_zygisk()
            if results['zygisk_enabled']:
                results['reboot_required'] = True

        return results


def main():
    """Demo/test the Magisk installer."""
    print("Magisk Installer - State Machine Demo")
    print("=" * 50)

    installer = MagiskInstaller("localhost:5555")

    # Register state change callback
    def on_state_change(old_state, new_state):
        print(f"State: {old_state.name} -> {new_state.name}")

    installer.on_state_change(on_state_change)

    # Launch and check status
    print("\n1. Launching Magisk app...")
    installer.launch_magisk()

    print("\n2. Getting status...")
    status = installer.get_magisk_status()
    print(f"   Installed: {status.installed_version or 'N/A'}")
    print(f"   Zygisk: {'Yes' if status.zygisk_enabled else 'No'}")
    print(f"   Ramdisk: {'Yes' if status.ramdisk_supported else 'No'}")
    print(f"   Rooted: {'Yes' if status.is_rooted else 'No'}")

    print("\n3. Current state:", installer.detect_state().name)

    print("\n4. Navigating to Install screen...")
    if installer.navigate_to_install():
        print("   Successfully navigated to Install screen")
        print("   Current state:", installer.detect_state().name)
    else:
        print("   Failed to navigate to Install screen")

    print("\nDemo complete!")


if __name__ == "__main__":
    main()
