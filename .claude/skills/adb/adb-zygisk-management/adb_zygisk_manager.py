"""Zygisk Management Framework for ADB Automation.

Manages Zygisk subsystem in Magisk settings.
Provides enable, disable, status checking, and verification capabilities.

Author: MoAI-ADK
Version: 1.0.0
"""

import logging
import time
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

from adb_auto_player.device.adb.adb_device import AdbDeviceWrapper

logger = logging.getLogger(__name__)


class ZygiskStatus(Enum):
    """Zygisk operational states."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"
    ERROR = "error"
    NOT_SUPPORTED = "not_supported"
    REBOOT_REQUIRED = "reboot_required"


@dataclass
class ZygiskOperationResult:
    """Result of a Zygisk operation."""

    status: ZygiskStatus
    success: bool
    message: str
    reboot_required: bool = False
    error: Optional[str] = None
    duration: float = 0.0
    attempts: int = 0


class ZygiskManager:
    """Manages Zygisk subsystem in Magisk settings."""

    def __init__(
        self,
        device: AdbDeviceWrapper,
        ui_navigator: Any,
        state_verifier: Any,
        ocr_finder: Any,
    ):
        """Initialize Zygisk Manager.

        Args:
            device: AdbDeviceWrapper instance
            ui_navigator: UINavigator instance for tapping
            state_verifier: StateVerifier instance for state checking
            ocr_finder: OCRTextFinder instance for text detection
        """
        self.device = device
        self.ui_navigator = ui_navigator
        self.state_verifier = state_verifier
        self.ocr_finder = ocr_finder
        self.logger = logger

        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.state_check_timeout = 5
        self.toggle_delay = 2.0
        self.navigation_timeout = 10

        # State tracking
        self._last_status = ZygiskStatus.UNKNOWN
        self._operation_history = []

    # ========== PUBLIC INTERFACE ==========

    def enable_zygisk(self) -> ZygiskOperationResult:
        """Navigate to Zygisk toggle and enable it.

        Returns:
            ZygiskOperationResult with operation status

        Process:
            1. Check if already enabled
            2. Navigate to Settings
            3. Find Zygisk toggle
            4. Tap toggle to enable
            5. Handle reboot dialog if appears
            6. Verify enabled state
        """
        start_time = time.time()
        self.logger.info("🔧 Enabling Zygisk...")

        try:
            # Check current status
            current_status = self.get_zygisk_status()
            if current_status == "enabled":
                self.logger.info("✅ Zygisk already enabled")
                return ZygiskOperationResult(
                    status=ZygiskStatus.ENABLED,
                    success=True,
                    message="Zygisk already enabled",
                    duration=time.time() - start_time,
                )

            # Navigate to Settings (assuming we're in Magisk)
            if not self._navigate_to_settings():
                raise RuntimeError("Failed to navigate to Magisk Settings")

            # Find and verify current toggle state
            toggle_state = self._check_toggle_state()
            if toggle_state == "enabled":
                self.logger.info("✅ Zygisk already enabled (toggle check)")
                return ZygiskOperationResult(
                    status=ZygiskStatus.ENABLED,
                    success=True,
                    message="Zygisk already enabled",
                    duration=time.time() - start_time,
                )

            # Tap toggle to enable
            if not self._tap_zygisk_toggle():
                raise RuntimeError("Failed to tap Zygisk toggle")

            # Wait for toggle animation
            time.sleep(self.toggle_delay)

            # Check for reboot dialog
            reboot_needed = self._handle_reboot_dialog()

            # Verify enabled state
            if not self.is_zygisk_enabled():
                raise RuntimeError("Toggle tapped but Zygisk not enabled")

            self.logger.info("✅ Zygisk enabled successfully")
            result = ZygiskOperationResult(
                status=ZygiskStatus.REBOOT_REQUIRED
                if reboot_needed
                else ZygiskStatus.ENABLED,
                success=True,
                message="Zygisk enabled successfully"
                + (" (reboot required)" if reboot_needed else ""),
                reboot_required=reboot_needed,
                duration=time.time() - start_time,
            )

            self._record_operation("enable", result)
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to enable Zygisk: {e}")
            result = ZygiskOperationResult(
                status=ZygiskStatus.ERROR,
                success=False,
                message=f"Failed to enable Zygisk: {e}",
                error=str(e),
                duration=time.time() - start_time,
            )
            self._record_operation("enable", result)
            return result

    def disable_zygisk(self) -> ZygiskOperationResult:
        """Navigate to Zygisk toggle and disable it.

        Returns:
            ZygiskOperationResult with operation status
        """
        start_time = time.time()
        self.logger.info("🔧 Disabling Zygisk...")

        try:
            # Check current status
            current_status = self.get_zygisk_status()
            if current_status == "disabled":
                self.logger.info("✅ Zygisk already disabled")
                return ZygiskOperationResult(
                    status=ZygiskStatus.DISABLED,
                    success=True,
                    message="Zygisk already disabled",
                    duration=time.time() - start_time,
                )

            # Navigate to Settings
            if not self._navigate_to_settings():
                raise RuntimeError("Failed to navigate to Magisk Settings")

            # Check toggle state
            toggle_state = self._check_toggle_state()
            if toggle_state == "disabled":
                self.logger.info("✅ Zygisk already disabled (toggle check)")
                return ZygiskOperationResult(
                    status=ZygiskStatus.DISABLED,
                    success=True,
                    message="Zygisk already disabled",
                    duration=time.time() - start_time,
                )

            # Tap toggle to disable
            if not self._tap_zygisk_toggle():
                raise RuntimeError("Failed to tap Zygisk toggle")

            # Wait for toggle animation
            time.sleep(self.toggle_delay)

            # Check for reboot dialog
            reboot_needed = self._handle_reboot_dialog()

            # Verify disabled state
            if self.is_zygisk_enabled():
                raise RuntimeError("Toggle tapped but Zygisk still enabled")

            self.logger.info("✅ Zygisk disabled successfully")
            result = ZygiskOperationResult(
                status=ZygiskStatus.REBOOT_REQUIRED
                if reboot_needed
                else ZygiskStatus.DISABLED,
                success=True,
                message="Zygisk disabled successfully"
                + (" (reboot required)" if reboot_needed else ""),
                reboot_required=reboot_needed,
                duration=time.time() - start_time,
            )

            self._record_operation("disable", result)
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to disable Zygisk: {e}")
            result = ZygiskOperationResult(
                status=ZygiskStatus.ERROR,
                success=False,
                message=f"Failed to disable Zygisk: {e}",
                error=str(e),
                duration=time.time() - start_time,
            )
            self._record_operation("disable", result)
            return result

    def is_zygisk_enabled(self) -> bool:
        """Check if 'Zygisk: Yes' text is visible on screen.

        Returns:
            True if Zygisk is enabled, False otherwise
        """
        try:
            # Try to find "Zygisk: Yes" or similar text
            result = self.ocr_finder.find_text("Zygisk: Yes")
            if result:
                self.logger.debug("✅ Found 'Zygisk: Yes' on screen")
                return True

            # Also check for toggle state indicator
            result = self.ocr_finder.find_text("Enabled")
            if result:
                # Check if it's near "Zygisk" text
                zygisk_result = self.ocr_finder.find_text("Zygisk")
                if zygisk_result:
                    # Simple proximity check
                    if abs(result.box.start_point.y - zygisk_result.box.start_point.y) < 100:
                        self.logger.debug("✅ Zygisk toggle appears enabled")
                        return True

            self.logger.debug("❌ Zygisk not enabled (text not found)")
            return False

        except Exception as e:
            self.logger.error(f"Error checking Zygisk enabled state: {e}")
            return False

    def verify_zygisk_active(self) -> bool:
        """Verify Zygisk actually activated (check logs/processes).

        Returns:
            True if Zygisk is active in system, False otherwise

        Verification methods:
            1. Check for zygisk processes
            2. Check Magisk logs for zygisk initialization
            3. Check /system/lib*/libzygisk.so existence
        """
        try:
            self.logger.debug("Verifying Zygisk active in system...")

            # Method 1: Check for zygisk-related processes
            ps_cmd = "ps -A | grep -i zygisk"
            result = self.device.shell(ps_cmd)

            if result and "zygisk" in result.lower():
                self.logger.info("✅ Zygisk process found")
                return True

            # Method 2: Check Magisk logs
            # This requires reading Magisk internal logs
            # For now, we'll use visual verification as fallback
            log_cmd = "logcat -d | grep -i zygisk | tail -n 5"
            result = self.device.shell(log_cmd)

            if result and any(
                keyword in result.lower() for keyword in ["zygisk init", "zygisk start"]
            ):
                self.logger.info("✅ Zygisk found in logcat")
                return True

            # Method 3: Check for libzygisk.so
            lib_cmd = "ls /system/lib*/libzygisk.so 2>/dev/null"
            result = self.device.shell(lib_cmd)

            if result and "libzygisk.so" in result:
                self.logger.info("✅ libzygisk.so found in system")
                return True

            self.logger.warning("⚠️  No active Zygisk indicators found")
            return False

        except Exception as e:
            self.logger.error(f"Error verifying Zygisk active: {e}")
            return False

    def get_zygisk_status(self) -> str:
        """Return: 'enabled', 'disabled', 'unknown', or 'error'.

        Returns:
            Status string indicating current Zygisk state
        """
        try:
            # Check OCR for status text
            if self.is_zygisk_enabled():
                self._last_status = ZygiskStatus.ENABLED
                return "enabled"

            # Check for disabled indicator
            result = self.ocr_finder.find_text("Zygisk: No")
            if result:
                self._last_status = ZygiskStatus.DISABLED
                return "disabled"

            # Check toggle state
            toggle_state = self._check_toggle_state()
            if toggle_state in ["enabled", "disabled"]:
                self._last_status = (
                    ZygiskStatus.ENABLED
                    if toggle_state == "enabled"
                    else ZygiskStatus.DISABLED
                )
                return toggle_state

            # Unknown state
            self._last_status = ZygiskStatus.UNKNOWN
            return "unknown"

        except Exception as e:
            self.logger.error(f"Error getting Zygisk status: {e}")
            self._last_status = ZygiskStatus.ERROR
            return "error"

    # ========== PRIVATE HELPERS ==========

    def _navigate_to_settings(self) -> bool:
        """Navigate to Magisk Settings page.

        Returns:
            True if navigation successful
        """
        try:
            self.logger.debug("Navigating to Magisk Settings...")

            # Try to find and tap Settings
            if self.ui_navigator.find_and_tap(
                "Settings", timeout_seconds=5, post_tap_delay=1.0
            ):
                self.logger.info("✅ Navigated to Settings")
                return True

            # Try alternative navigation
            if self.ui_navigator.find_and_tap(
                "⚙", timeout_seconds=3, post_tap_delay=1.0
            ):
                self.logger.info("✅ Navigated to Settings (icon)")
                return True

            self.logger.warning("❌ Failed to navigate to Settings")
            return False

        except Exception as e:
            self.logger.error(f"Navigation to Settings failed: {e}")
            return False

    def _tap_zygisk_toggle(self) -> bool:
        """Tap the Zygisk toggle switch.

        Returns:
            True if toggle tapped successfully

        Uses retry logic for robustness.
        """
        try:
            self.logger.debug("Attempting to tap Zygisk toggle...")

            for attempt in range(self.max_retries):
                # Find Zygisk text
                zygisk_result = self.ocr_finder.find_text("Zygisk")
                if not zygisk_result:
                    if attempt < self.max_retries - 1:
                        self.logger.debug(
                            f"Zygisk text not found, retry {attempt + 1}/{self.max_retries}"
                        )
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.logger.error("❌ Zygisk text not found after retries")
                        return False

                # Calculate toggle position (usually to the right)
                toggle_x = zygisk_result.box.start_point.x + zygisk_result.box.width + 100
                toggle_y = zygisk_result.box.start_point.y + (zygisk_result.box.height // 2)

                # Tap toggle
                self.device.tap(str(toggle_x), str(toggle_y))
                self.logger.info(f"✅ Tapped Zygisk toggle at ({toggle_x}, {toggle_y})")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to tap Zygisk toggle: {e}")
            return False

    def _check_toggle_state(self) -> str:
        """Check current toggle state.

        Returns:
            'enabled', 'disabled', or 'unknown'
        """
        try:
            # Check for visual indicators
            if self.is_zygisk_enabled():
                return "enabled"

            # Check for disabled indicator
            result = self.ocr_finder.find_text("Zygisk: No")
            if result:
                return "disabled"

            # Check generic toggle indicators
            results = self.ocr_finder.find_all_text()
            for result in results:
                text = result.text.lower()
                if "enabled" in text or "on" in text:
                    # Check proximity to Zygisk
                    zygisk_result = self.ocr_finder.find_text("Zygisk")
                    if zygisk_result:
                        if abs(result.box.start_point.y - zygisk_result.box.start_point.y) < 100:
                            return "enabled"

                if "disabled" in text or "off" in text:
                    zygisk_result = self.ocr_finder.find_text("Zygisk")
                    if zygisk_result:
                        if abs(result.box.start_point.y - zygisk_result.box.start_point.y) < 100:
                            return "disabled"

            return "unknown"

        except Exception as e:
            self.logger.error(f"Error checking toggle state: {e}")
            return "unknown"

    def _handle_reboot_dialog(self) -> bool:
        """Handle reboot dialog if it appears.

        Returns:
            True if reboot dialog appeared (regardless of action taken)
        """
        try:
            self.logger.debug("Checking for reboot dialog...")

            # Wait briefly for dialog to appear
            time.sleep(0.5)

            # Check for reboot-related text
            reboot_texts = ["Restart", "Reboot", "System Update Required", "Restart now"]

            for text in reboot_texts:
                result = self.ocr_finder.find_text(text)
                if result:
                    self.logger.info(f"✅ Reboot dialog detected: '{text}'")

                    # Try to dismiss dialog (tap Cancel/Later if available)
                    if self.ui_navigator.find_and_tap("Cancel", timeout_seconds=2):
                        self.logger.info("Dialog dismissed (Cancel)")
                    elif self.ui_navigator.find_and_tap("Later", timeout_seconds=2):
                        self.logger.info("Dialog dismissed (Later)")
                    else:
                        # Press back to dismiss
                        self.ui_navigator.press_back()
                        self.logger.info("Dialog dismissed (Back)")

                    return True

            self.logger.debug("No reboot dialog detected")
            return False

        except Exception as e:
            self.logger.error(f"Error handling reboot dialog: {e}")
            return False

    def _record_operation(self, operation: str, result: ZygiskOperationResult) -> None:
        """Record operation in history.

        Args:
            operation: Operation type ('enable' or 'disable')
            result: Operation result
        """
        record = {
            "timestamp": time.time(),
            "operation": operation,
            "success": result.success,
            "status": result.status.value,
            "duration": result.duration,
            "reboot_required": result.reboot_required,
        }
        self._operation_history.append(record)

        # Keep only last 50 operations
        if len(self._operation_history) > 50:
            self._operation_history.pop(0)

    # ========== UTILITY METHODS ==========

    def get_operation_history(self) -> list:
        """Get history of operations.

        Returns:
            List of operation records
        """
        return self._operation_history.copy()

    def clear_operation_history(self) -> None:
        """Clear operation history."""
        self._operation_history.clear()

    def get_last_status(self) -> ZygiskStatus:
        """Get last known status.

        Returns:
            Last cached ZygiskStatus
        """
        return self._last_status

    def check_magisk_available(self) -> bool:
        """Check if Magisk is installed and accessible.

        Returns:
            True if Magisk is available
        """
        try:
            # Check if Magisk package is installed
            result = self.device.shell("pm list packages | grep magisk")
            if result and "magisk" in result.lower():
                self.logger.debug("✅ Magisk package found")
                return True

            self.logger.warning("❌ Magisk package not found")
            return False

        except Exception as e:
            self.logger.error(f"Error checking Magisk availability: {e}")
            return False

    def check_zygisk_supported(self) -> bool:
        """Check if Zygisk is supported on this device.

        Returns:
            True if Zygisk is supported

        Zygisk requires:
            - Magisk >= 24.0
            - Root access
            - Android 5.0+
        """
        try:
            # Check Magisk version
            result = self.device.shell("su -v")
            if result and "magisk" in result.lower():
                # Parse version (e.g., "Magisk 26.1")
                import re

                version_match = re.search(r"(\d+)\.(\d+)", result)
                if version_match:
                    major = int(version_match.group(1))
                    if major >= 24:
                        self.logger.debug(f"✅ Magisk version sufficient: {major}")
                        return True
                    else:
                        self.logger.warning(
                            f"❌ Magisk version too old: {major} (need 24+)"
                        )
                        return False

            # Fallback: check if Settings has Zygisk option
            if not self._navigate_to_settings():
                return False

            result = self.ocr_finder.find_text("Zygisk")
            if result:
                self.logger.debug("✅ Zygisk option found in Settings")
                return True

            self.logger.warning("❌ Zygisk option not found in Settings")
            return False

        except Exception as e:
            self.logger.error(f"Error checking Zygisk support: {e}")
            return False


class ZygiskManagerError(Exception):
    """Base exception for ZygiskManager errors."""

    pass


class ZygiskNotSupportedError(ZygiskManagerError):
    """Raised when Zygisk is not supported on device."""

    pass


class ZygiskNavigationError(ZygiskManagerError):
    """Raised when navigation to Zygisk settings fails."""

    pass


class ZygiskToggleError(ZygiskManagerError):
    """Raised when toggle operation fails."""

    pass
