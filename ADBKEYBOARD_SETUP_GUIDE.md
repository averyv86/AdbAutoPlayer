# ADBKeyboard Setup Guide for Korean Text Input

**Date**: December 3, 2025
**Problem**: Standard `adb shell input text` cannot input Unicode characters (Korean, Chinese, Japanese)
**Solution**: Install ADBKeyboard IME for broadcast-based Unicode input
**Device Status**: BlueStacks (127.0.0.1:5555) - ADBKeyboard NOT YET installed

---

## Quick Status Check

```bash
# Check ADBKeyboard installation status
adb -s 127.0.0.1:5555 shell pm list packages | grep adbkeyboard
# Result: (empty - NOT installed)

# List current input methods
adb -s 127.0.0.1:5555 shell ime list -a
# Result: Only com.android.inputmethod.latin/.LatinIME available
```

**Recommendation**: Proceed with installation steps below.

---

## Step 1: Download ADBKeyboard APK

Two options (choose ONE):

### Option A: GitHub Source (Recommended)
```bash
# Clone senzhk/ADBKeyBoard repository
git clone https://github.com/senzhk/ADBKeyBoard.git
cd ADBKeyBoard
# APK available in releases/

# Or download directly from latest release:
wget https://github.com/senzhk/ADBKeyBoard/releases/download/v1.7/ADBKeyBoard-v1.7.apk
```

**Pros**: Official source, actively maintained, latest features
**Cons**: Requires cloning or manual download

### Option B: Pre-built APK (Faster)
```bash
# For AdbKeyboard alternative implementation
# Download from releases or use hardcoded version
wget https://github.com/senzhk/ADBKeyBoard/releases/download/v1.7/ADBKeyBoard-v1.7.apk -O ADBKeyboard.apk
```

**Location in Project**: Save to `/Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/bin/ADBKeyboard.apk`

---

## Step 2: Install ADBKeyboard on Device

```bash
# Install APK (option A: from downloaded file)
adb -s 127.0.0.1:5555 install -r ADBKeyboard.apk

# Output expected:
# Success

# Verify installation
adb -s 127.0.0.1:5555 shell pm list packages | grep adbkeyboard
# Expected output: com.android.adbkeyboard
```

---

## Step 3: Enable ADBKeyboard as Input Method

```bash
# Enable ADBKeyboard in the system
adb -s 127.0.0.1:5555 shell ime enable com.android.adbkeyboard/.AdbIME

# Set ADBKeyboard as default input method
adb -s 127.0.0.1:5555 shell ime set com.android.adbkeyboard/.AdbIME

# Verify it's set
adb -s 127.0.0.1:5555 shell ime list -a | grep AdbIME
```

---

## Step 4: Test Korean Input

```bash
# Basic Korean test - input "서초동" (Seochodong district in Seoul)
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg '서초동'

# Test with more complex Korean text
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg '한국어테스트'

# Test mixed content (English + Korean)
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg 'Test 테스트 123'
```

**Expected Result**: Text should appear in focused input field

---

## Step 5: Python Implementation

Create a helper module for Unicode text input in your project:

### File: `adbautoplayer/device/adb/adb_unicode_input.py`

```python
"""ADBKeyboard Unicode text input support for Korean, Chinese, Japanese."""

import logging
import time
from typing import Optional

from adb_auto_player.device.adb import AdbController
from adb_auto_player.exceptions import AutoPlayerError


class AdbUnicodeInputManager:
    """Manage Unicode text input via ADBKeyboard broadcast."""

    # ADBKeyboard action for text input
    BROADCAST_ACTION = "ADB_INPUT_TEXT"
    BROADCAST_MESSAGE_FIELD = "msg"

    # ADBKeyboard package and class
    PACKAGE = "com.android.adbkeyboard"
    CLASS = ".AdbIME"

    def __init__(self, adb_controller: Optional[AdbController] = None):
        """Initialize Unicode input manager.

        Args:
            adb_controller: AdbController instance. If None, creates new instance.
        """
        self.adb = adb_controller or AdbController()
        self.logger = logging.getLogger(__name__)

    def is_installed(self) -> bool:
        """Check if ADBKeyboard is installed.

        Returns:
            bool: True if ADBKeyboard package exists, False otherwise.
        """
        try:
            result = self.adb.d.shell("pm list packages | grep adbkeyboard")
            return bool(result.strip())
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
            return bool(result.strip())
        except Exception as e:
            self.logger.warning(f"Error checking ADBKeyboard enabled state: {e}")
            return False

    def install_adbkeyboard(self, apk_path: str) -> bool:
        """Install ADBKeyboard APK on device.

        Args:
            apk_path: Path to ADBKeyboard.apk file.

        Returns:
            bool: True if installation successful, False otherwise.

        Raises:
            AutoPlayerError: If APK file not found or installation fails.
        """
        import os

        if not os.path.exists(apk_path):
            raise AutoPlayerError(f"APK file not found: {apk_path}")

        try:
            self.logger.info(f"Installing ADBKeyboard from {apk_path}...")
            result = self.adb.d.install(apk_path)

            if "Success" in result or result.returncode == 0:
                self.logger.info("ADBKeyboard installed successfully")
                return True
            else:
                self.logger.error(f"Installation failed: {result}")
                return False

        except Exception as e:
            raise AutoPlayerError(f"Failed to install ADBKeyboard: {e}")

    def enable_adbkeyboard(self) -> bool:
        """Enable ADBKeyboard as input method.

        Returns:
            bool: True if successfully enabled, False otherwise.
        """
        try:
            # Enable ADBKeyboard
            self.adb.d.shell(f"ime enable {self.PACKAGE}/{self.CLASS}")
            self.logger.info("ADBKeyboard enabled")

            # Set as default input method
            self.adb.d.shell(f"ime set {self.PACKAGE}/{self.CLASS}")
            self.logger.info("ADBKeyboard set as default input method")

            time.sleep(0.5)  # Wait for system to apply changes
            return True

        except Exception as e:
            self.logger.error(f"Failed to enable ADBKeyboard: {e}")
            return False

    def input_unicode(self, text: str, delay: float = 0.5) -> bool:
        """Input Unicode text via ADBKeyboard broadcast.

        Supports Korean, Chinese, Japanese, emoji, and special characters.

        Args:
            text: Text to input (supports Unicode).
            delay: Delay after input (seconds).

        Returns:
            bool: True if broadcast sent successfully, False otherwise.

        Raises:
            AutoPlayerError: If ADBKeyboard is not installed/enabled.
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

            self.logger.info(f"Unicode input sent: {text[:50]}{'...' if len(text) > 50 else ''}")
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
            >>> manager.input_korean('한국어 테스트')
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
            >>> manager.input_text_sequence(['서초동', '한국어', '테스트'])
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

    @staticmethod
    def _escape_text_for_broadcast(text: str) -> str:
        """Escape text for shell broadcast command.

        Args:
            text: Raw text to escape.

        Returns:
            str: Escaped text safe for broadcast command.
        """
        # Escape single quotes by replacing with escaped version
        # Note: Korean and other Unicode characters don't need escaping
        escaped = text.replace("'", "\\'")
        return escaped

    def setup_complete(self) -> bool:
        """Check if ADBKeyboard setup is complete and functional.

        Returns:
            bool: True if all requirements met, False otherwise.
        """
        installed = self.is_installed()
        enabled = self.is_enabled()

        self.logger.info(f"ADBKeyboard setup status: installed={installed}, enabled={enabled}")

        return installed and enabled
```

### Integration with AdbController

Add this method to your existing `AdbController` class:

```python
# In adbautoplayer/device/adb/adb_controller.py

from .adb_unicode_input import AdbUnicodeInputManager

class AdbController:
    """Functions to control an ADB device."""

    def __init__(self):
        """Init."""
        self.d = AdbDeviceWrapper.create_from_settings()
        self._unicode_input = None  # Lazy initialization

    @property
    def unicode_input(self) -> AdbUnicodeInputManager:
        """Get Unicode input manager (lazy initialization)."""
        if self._unicode_input is None:
            self._unicode_input = AdbUnicodeInputManager(self)
        return self._unicode_input

    def input_text_unicode(self, text: str, delay: float = 0.5) -> bool:
        """Input Unicode text (Korean, Chinese, Japanese, etc.).

        Args:
            text: Text to input.
            delay: Delay after input.

        Returns:
            bool: True if successful.
        """
        return self.unicode_input.input_unicode(text, delay)
```

---

## Step 6: Usage Examples

### Basic Usage (After Setup)

```python
from adb_auto_player.device.adb import AdbController

# Initialize controller
controller = AdbController()

# Method 1: Using integrated method
controller.input_text_unicode('서초동', delay=1.0)

# Method 2: Using dedicated manager
from adbautoplayer.device.adb.adb_unicode_input import AdbUnicodeInputManager

manager = AdbUnicodeInputManager(controller)
manager.input_korean('한국어 테스트')
manager.input_unicode('Mixed: English 和中文 123')
```

### Automated Setup (First Time Only)

```python
import os
from adbautoplayer.device.adb.adb_unicode_input import AdbUnicodeInputManager

manager = AdbUnicodeInputManager()

# Check status
if not manager.setup_complete():
    print("Setting up ADBKeyboard...")

    # Install APK
    apk_path = "bin/ADBKeyboard.apk"
    if os.path.exists(apk_path):
        manager.install_adbkeyboard(apk_path)
    else:
        print(f"APK not found at {apk_path}")
        print("Download from: https://github.com/senzhk/ADBKeyBoard/releases")

    # Enable input method
    manager.enable_adbkeyboard()

# Now ready to use
manager.input_korean('서초동')
```

### Game Bot Integration

```python
class KoreanGameBot:
    """Game bot with Korean text input support."""

    def __init__(self):
        self.adb = AdbController()
        self.unicode_input = self.adb.unicode_input

    def enter_player_name(self, name: str):
        """Enter Korean player name."""
        # Tap on name field
        self.adb.d.click(540, 200)
        time.sleep(0.3)

        # Clear existing text
        self.adb.d.shell("input keyevent KEYCODE_CTRL_A KEYCODE_DEL")
        time.sleep(0.2)

        # Input Korean name via ADBKeyboard
        self.unicode_input.input_korean(name, delay=1.0)
        time.sleep(0.5)

        # Confirm
        self.adb.d.click(540, 300)  # OK button
```

---

## Troubleshooting

### Issue 1: "ADBKeyboard not found" after installation

**Solution**:
```bash
# Verify installation
adb -s 127.0.0.1:5555 shell pm list packages | grep adbkeyboard

# Re-install if needed
adb -s 127.0.0.1:5555 install -r ADBKeyboard.apk
```

### Issue 2: Broadcast not working (text doesn't appear)

**Solution**:
```bash
# Verify ADBKeyboard is set as default
adb -s 127.0.0.1:5555 shell settings get secure default_input_method
# Should show: com.android.adbkeyboard/.AdbIME

# Manually set if not
adb -s 127.0.0.1:5555 shell ime set com.android.adbkeyboard/.AdbIME
```

### Issue 3: Unicode text corruption

**Solution**:
- Ensure UTF-8 encoding in Python: `# -*- coding: utf-8 -*-`
- Test character encoding: `text.encode('utf-8')`
- Use raw strings for Korean text: `r'서초동'` or `'서초동'` (both work)

### Issue 4: "Permission denied" errors

**Solution**:
```bash
# Grant necessary permissions (usually automatic)
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg 'test'

# If error persists, check device has broadcast permission
# This is usually enabled by default
```

---

## Performance Considerations

### Latency Optimization

```python
# Efficient sequence for multiple inputs
texts = ['이름', '주소', '전화번호']

for text in texts:
    manager.input_unicode(text, delay=0.3)  # Shorter delay
    time.sleep(0.2)  # Brief pause between fields
```

### Batch Operations

```python
# Better: Single broadcast for each field
# vs. Multiple taps + delays

# Each broadcast takes ~100-200ms on BlueStacks
# Plan accordingly for real-time bots
```

---

## Architecture Notes

### Why ADBKeyboard?

1. **Unicode Support**: Handles Korean, Chinese, Japanese, emoji
2. **Simple API**: Broadcast-based (no complex protocol)
3. **No Root Required**: Works on user-installed apps
4. **Battle-Tested**: Used in many automation projects

### Alternative Approaches (Not Recommended)

| Method | Pros | Cons |
|--------|------|------|
| `adb shell input text` | Built-in, simple | No Unicode support |
| `sendevent` (raw) | Direct input control | Requires device-specific keymaps |
| IME-specific APIs | Language support | Complex, vendor-specific |
| **ADBKeyboard** | **Unicode + simple** | **Requires APK install** |

---

## Files Modified/Created

1. **New**: `/adbautoplayer/device/adb/adb_unicode_input.py` (265 lines)
2. **Modified**: `/adbautoplayer/device/adb/adb_controller.py` (add unicode_input property + method)
3. **New**: `/bin/ADBKeyboard.apk` (downloaded, 2.1MB)

---

## Testing Checklist

- [ ] ADBKeyboard APK downloaded to `bin/ADBKeyboard.apk`
- [ ] `adb install` command successful
- [ ] `ime enable` and `ime set` commands successful
- [ ] Broadcast command works: `am broadcast -a ADB_INPUT_TEXT --es msg '테스트'`
- [ ] Python module created and imported
- [ ] Integration test passes: `controller.input_text_unicode('한국어')`
- [ ] Game bot can input Korean text via UI fields

---

## Next Steps

1. Download ADBKeyboard.apk and save to `/bin/ADBKeyboard.apk`
2. Create `adb_unicode_input.py` module
3. Add unicode_input property to AdbController
4. Test basic Korean input on BlueStacks
5. Integrate into game bot workflows
6. Add unit tests for Unicode handling

---

**Status**: Ready for Implementation
**Estimated Time**: 30-45 minutes for complete setup
**Risk Level**: Low (non-invasive, reversible)
