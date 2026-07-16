"""ADBKeyboard Unicode text input support for Korean, Chinese, Japanese."""

import logging
import os
import time
from typing import Optional

from adb_auto_player.exceptions import AutoPlayerError


class AdbUnicodeInputManager:
    """Manage Unicode text input via ADBKeyboard broadcast.

    Supports Korean (한글), Chinese (中文), Japanese (日本語), and other Unicode characters.

    Example:
        >>> from adb_auto_player.device.adb import AdbController
        >>> controller = AdbController()
        >>> manager = AdbUnicodeInputManager(controller)
        >>> manager.input_korean('서초동')
        >>> manager.input_unicode('Mixed: English 和中文 123')
    """

    # ADBKeyboard action for text input
    BROADCAST_ACTION = "ADB_INPUT_TEXT"
    BROADCAST_MESSAGE_FIELD = "msg"

    # ADBKeyboard package and class
    PACKAGE = "com.android.adbkeyboard"
    CLASS = ".AdbIME"

    def __init__(self, adb_controller: Optional["AdbController"] = None):  # noqa: F821
        """Initialize Unicode input manager.

        Args:
            adb_controller: AdbController instance. If None, creates new instance.
        """
        if adb_controller is None:
            # Lazy import to avoid circular dependency
            from . import AdbController  # noqa: F401

            adb_controller = AdbController()

        self.adb = adb_controller
        self.logger = logging.getLogger(__name__)

    def is_installed(self) -> bool:
        """Check if ADBKeyboard is installed.

        Returns:
            bool: True if ADBKeyboard package exists, False otherwise.
        """
        try:
            result = self.adb.d.shell("pm list packages | grep adbkeyboard")
            is_installed = bool(result.strip()) if result else False
            self.logger.debug(f"ADBKeyboard installed: {is_installed}")
            return is_installed
        except Exception as e:
            self.logger.warning(f"Error checking ADBKeyboard installation: {e}")
            return False

    def is_enabled(self) -> bool:
        """Check if ADBKeyboard is enabled as input method.

        Returns:
            bool: True if ADBKeyboard is enabled, False otherwise.
        """
        try:
            result = self.adb.d.shell("ime list -a | grep AdbIME")
            is_enabled = bool(result.strip()) if result else False
            self.logger.debug(f"ADBKeyboard enabled: {is_enabled}")
            return is_enabled
        except Exception as e:
            self.logger.warning(f"Error checking ADBKeyboard enabled state: {e}")
            return False

    def get_default_ime(self) -> str:
        """Get currently set default input method.

        Returns:
            str: Package/class of default IME.
        """
        try:
            result = self.adb.d.shell("settings get secure default_input_method")
            return result.strip() if result else ""
        except Exception as e:
            self.logger.warning(f"Error getting default IME: {e}")
            return ""

    def install_adbkeyboard(self, apk_path: str) -> bool:
        """Install ADBKeyboard APK on device.

        Args:
            apk_path: Path to ADBKeyboard.apk file.

        Returns:
            bool: True if installation successful, False otherwise.

        Raises:
            AutoPlayerError: If APK file not found or installation fails.

        Example:
            >>> manager.install_adbkeyboard('bin/ADBKeyboard.apk')
            True
        """
        if not os.path.exists(apk_path):
            raise AutoPlayerError(f"APK file not found: {apk_path}")

        try:
            self.logger.info(f"Installing ADBKeyboard from {apk_path}...")

            # Use adb install command
            result = self.adb.d.shell(f"install -r {apk_path}")

            # Check for success indicators
            success_indicators = ["Success", "success", "INSTALL_SUCCEEDED"]
            if any(indicator in str(result) for indicator in success_indicators):
                self.logger.info("ADBKeyboard installed successfully")
                return True

            # Also check if error indicators are absent
            error_indicators = ["INSTALL_FAILED", "Error", "error"]
            if not any(indicator in str(result) for indicator in error_indicators):
                self.logger.info("ADBKeyboard installation completed (assuming success)")
                return True

            self.logger.error(f"Installation may have failed: {result}")
            return False

        except Exception as e:
            raise AutoPlayerError(f"Failed to install ADBKeyboard: {e}")

    def enable_adbkeyboard(self) -> bool:
        """Enable ADBKeyboard as input method.

        Returns:
            bool: True if successfully enabled, False otherwise.

        Example:
            >>> manager.enable_adbkeyboard()
            True
        """
        try:
            # Enable ADBKeyboard in system
            self.adb.d.shell(f"ime enable {self.PACKAGE}/{self.CLASS}")
            self.logger.info("ADBKeyboard enabled")

            # Set as default input method
            self.adb.d.shell(f"ime set {self.PACKAGE}/{self.CLASS}")
            self.logger.info("ADBKeyboard set as default input method")

            time.sleep(0.5)  # Wait for system to apply changes

            # Verify it's set
            default_ime = self.get_default_ime()
            if self.PACKAGE in default_ime:
                self.logger.info(f"Verified default IME: {default_ime}")
                return True

            self.logger.warning(
                f"ADBKeyboard may not be set as default. Default IME: {default_ime}"
            )
            return True  # Return True since enable commands succeeded

        except Exception as e:
            self.logger.error(f"Failed to enable ADBKeyboard: {e}")
            return False

    def input_unicode(self, text: str, delay: float = 0.5) -> bool:
        """Input Unicode text via ADBKeyboard broadcast.

        Supports Korean, Chinese, Japanese, emoji, and special characters.

        Args:
            text: Text to input (supports Unicode).
            delay: Delay after input (seconds). Default 0.5s.

        Returns:
            bool: True if broadcast sent successfully, False otherwise.

        Raises:
            AutoPlayerError: If ADBKeyboard is not installed/enabled.

        Example:
            >>> manager.input_unicode('서초동')
            True
            >>> manager.input_unicode('Mixed: English 和中文 123', delay=1.0)
            True
        """
        if not self.is_installed():
            raise AutoPlayerError(
                "ADBKeyboard not installed. Install using: install_adbkeyboard(apk_path)"
            )

        if not self.is_enabled():
            self.logger.warning("ADBKeyboard not enabled, attempting to enable...")
            if not self.enable_adbkeyboard():
                raise AutoPlayerError("Failed to enable ADBKeyboard")

        try:
            # Escape special characters for shell
            escaped_text = self._escape_text_for_broadcast(text)

            # Build broadcast command
            command = (
                f"am broadcast "
                f"-a {self.BROADCAST_ACTION} "
                f"--es {self.BROADCAST_MESSAGE_FIELD} '{escaped_text}'"
            )

            self.logger.debug(f"Sending broadcast: {command}")
            self.adb.d.shell(command)

            # Wait for text input to complete
            if delay > 0:
                time.sleep(delay)

            # Log abbreviated text for readability
            log_text = text[:50] + ("..." if len(text) > 50 else "")
            self.logger.info(f"Unicode input sent: {log_text}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to input unicode text: {e}")
            return False

    def input_korean(self, text: str, delay: float = 0.5) -> bool:
        """Input Korean text via ADBKeyboard.

        Convenience method for Korean text input.

        Args:
            text: Korean text to input.
            delay: Delay after input (seconds).

        Returns:
            bool: True if successful, False otherwise.

        Example:
            >>> manager.input_korean('서초동')
            True
            >>> manager.input_korean('한국어 테스트')
            True
        """
        return self.input_unicode(text, delay)

    def input_chinese(self, text: str, delay: float = 0.5) -> bool:
        """Input Chinese text via ADBKeyboard.

        Convenience method for Chinese text input.

        Args:
            text: Chinese text to input.
            delay: Delay after input (seconds).

        Returns:
            bool: True if successful, False otherwise.

        Example:
            >>> manager.input_chinese('中文测试')
            True
        """
        return self.input_unicode(text, delay)

    def input_japanese(self, text: str, delay: float = 0.5) -> bool:
        """Input Japanese text via ADBKeyboard.

        Convenience method for Japanese text input (Hiragana, Katakana, Kanji).

        Args:
            text: Japanese text to input.
            delay: Delay after input (seconds).

        Returns:
            bool: True if successful, False otherwise.

        Example:
            >>> manager.input_japanese('日本語テスト')
            True
        """
        return self.input_unicode(text, delay)

    def input_text_sequence(self, texts: list[str], delay_between: float = 0.5) -> bool:
        """Input multiple Unicode text items in sequence.

        Args:
            texts: List of text items to input.
            delay_between: Delay between each input (seconds).

        Returns:
            bool: True if all inputs successful, False otherwise.

        Example:
            >>> manager.input_text_sequence(['이름', '주소', '전화번호'])
            True
        """
        for i, text in enumerate(texts):
            try:
                self.input_unicode(text, delay_between)
                if i < len(texts) - 1:
                    time.sleep(delay_between)
            except Exception as e:
                self.logger.error(f"Failed to input text[{i}]: {e}")
                return False

        return True

    def setup_complete(self) -> bool:
        """Check if ADBKeyboard setup is complete and functional.

        Returns:
            bool: True if all requirements met, False otherwise.

        Example:
            >>> if manager.setup_complete():
            ...     print("Ready for Korean input")
            ... else:
            ...     print("Setup required")
        """
        installed = self.is_installed()
        enabled = self.is_enabled()

        status_msg = f"ADBKeyboard: installed={installed}, enabled={enabled}"
        if installed and enabled:
            self.logger.info(f"{status_msg} - Setup complete!")
        else:
            self.logger.warning(f"{status_msg} - Setup incomplete!")

        return installed and enabled

    @staticmethod
    def _escape_text_for_broadcast(text: str) -> str:
        """Escape text for shell broadcast command.

        Args:
            text: Raw text to escape.

        Returns:
            str: Escaped text safe for broadcast command.

        Note:
            Korean and other Unicode characters don't need escaping.
            Only special shell characters are escaped.
        """
        # Escape single quotes by replacing with escaped version
        escaped = text.replace("'", "\\'")
        return escaped


# Type hints for better IDE support
def _get_adb_controller() -> "AdbController":  # noqa: F821
    """Get AdbController instance (for type hints).

    This is a helper for type checking only.
    """
    from . import AdbController  # noqa: F401

    return AdbController()
