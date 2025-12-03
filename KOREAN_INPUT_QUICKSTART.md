# Korean Text Input - Quick Start Guide

**Setup Time**: 5-10 minutes
**Complexity**: Beginner-friendly
**Device**: BlueStacks (127.0.0.1:5555)

---

## TL;DR - Get Started in 3 Minutes

```bash
# 1. Download ADBKeyboard APK
cd /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer
wget https://github.com/senzhk/ADBKeyBoard/releases/download/v1.7/ADBKeyBoard-v1.7.apk -O bin/ADBKeyboard.apk

# 2. Install on device
adb -s 127.0.0.1:5555 install -r bin/ADBKeyboard.apk

# 3. Enable as input method
adb -s 127.0.0.1:5555 shell ime enable com.android.adbkeyboard/.AdbIME
adb -s 127.0.0.1:5555 shell ime set com.android.adbkeyboard/.AdbIME

# 4. Test Korean input
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg '서초동'

# Done! ✓
```

---

## Verify Setup Works

```bash
# Run test script
python test_korean_input.py --test-all

# Expected output:
# Device: (default)
# ADBKeyboard Installed: ✓ YES
# ADBKeyboard Enabled:   ✓ YES
# Setup Status: ✓ READY FOR KOREAN INPUT
```

---

## Use in Your Python Code

### Simple One-Liner

```python
from adb_auto_player.device.adb import AdbController

controller = AdbController()
controller.input_text_unicode('서초동')  # Korean input!
```

### Using Unicode Input Manager

```python
from adb_auto_player.device.adb import AdbController
from adb_auto_player.device.adb.adb_unicode_input import AdbUnicodeInputManager

controller = AdbController()
manager = controller.unicode_input

# Korean
manager.input_korean('한국어 테스트')

# Chinese
manager.input_chinese('中文测试')

# Japanese
manager.input_japanese('日本語テスト')

# Mixed
manager.input_unicode('English + 한글 + 中文 + 日本語')
```

### In Game Bot

```python
from adb_auto_player.device.adb import AdbController
import time

class PlayerSetup:
    def __init__(self):
        self.adb = AdbController()

    def set_player_name(self, korean_name: str):
        """Set player name in Korean."""
        # Click name input field
        self.adb.d.click(540, 300)
        time.sleep(0.5)

        # Clear existing text
        self.adb.d.shell("input keyevent KEYCODE_CTRL_A")
        self.adb.d.shell("input keyevent KEYCODE_DEL")
        time.sleep(0.3)

        # Input Korean name
        self.adb.input_text_unicode(korean_name)
        time.sleep(0.5)

        # Confirm
        self.adb.d.click(540, 400)  # OK button

# Usage
setup = PlayerSetup()
setup.set_player_name('플레이어이름')  # Player name in Korean
```

---

## Troubleshooting 30 Seconds

| Issue | Fix |
|-------|-----|
| "device not found" | Check: `adb devices` |
| "APK install failed" | Try: `adb install -r` (reinstall) |
| "Text doesn't appear" | Check: `adb shell ime list -a` (verify enabled) |
| "Permission denied" | Device issue, usually auto-resolves |

---

## Files Created

1. `adb_unicode_input.py` - Unicode input manager class
2. `test_korean_input.py` - Testing script
3. `ADBKEYBOARD_SETUP_GUIDE.md` - Full setup documentation
4. `bin/ADBKeyboard.apk` - (Download needed)

---

## Next Steps

1. Download ADBKeyboard.apk
2. Run `python test_korean_input.py --test-all`
3. If status shows "✓ READY", you're done!
4. If status shows "✗", follow [ADBKEYBOARD_SETUP_GUIDE.md](ADBKEYBOARD_SETUP_GUIDE.md)

---

## Common Korean Text Examples

```python
# City names
controller.input_text_unicode('서초동')      # Seochodong
controller.input_text_unicode('강남구')      # Gangnam-gu
controller.input_text_unicode('서울')        # Seoul

# Player names
controller.input_text_unicode('플레이어')    # Player
controller.input_text_unicode('용사')        # Warrior

# Game text
controller.input_text_unicode('확인')        # Confirm
controller.input_text_unicode('취소')        # Cancel
controller.input_text_unicode('완료')        # Complete
```

---

**Documentation**: See [ADBKEYBOARD_SETUP_GUIDE.md](ADBKEYBOARD_SETUP_GUIDE.md) for detailed information
