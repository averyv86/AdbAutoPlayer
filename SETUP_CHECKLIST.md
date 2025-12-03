# ADBKeyboard Korean Input - Setup Checklist

**Estimated Time**: 5-10 minutes
**Difficulty**: Beginner-friendly
**Device**: BlueStacks (127.0.0.1:5555)

---

## Pre-Setup (1 minute)

- [ ] Device is powered on
- [ ] BlueStacks is running
- [ ] ADB connection is working: `adb devices`
- [ ] Project directory is ready: `/Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer`

---

## Step 1: Download ADBKeyboard APK (2 minutes)

```bash
cd /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer
wget https://github.com/senzhk/ADBKeyBoard/releases/download/v1.7/ADBKeyBoard-v1.7.apk -O bin/ADBKeyboard.apk
```

**Verification**:
```bash
ls -lh bin/ADBKeyboard.apk
# Should show: -rw-r--r-- ... 2.1M ... ADBKeyboard.apk
```

- [ ] APK file downloaded
- [ ] File size is ~2.1 MB
- [ ] No errors in download

---

## Step 2: Install APK on Device (2 minutes)

```bash
adb -s 127.0.0.1:5555 install -r bin/ADBKeyboard.apk
```

**Expected Output**:
```
Success
```

**Verification**:
```bash
adb -s 127.0.0.1:5555 shell pm list packages | grep adbkeyboard
# Should show: com.android.adbkeyboard
```

- [ ] Install command ran successfully
- [ ] Output shows "Success"
- [ ] `pm list packages` shows `com.android.adbkeyboard`

---

## Step 3: Enable Input Method (1 minute)

```bash
adb -s 127.0.0.1:5555 shell ime enable com.android.adbkeyboard/.AdbIME
adb -s 127.0.0.1:5555 shell ime set com.android.adbkeyboard/.AdbIME
```

**Verification**:
```bash
adb -s 127.0.0.1:5555 shell settings get secure default_input_method
# Should show: com.android.adbkeyboard/.AdbIME
```

- [ ] ime enable command executed
- [ ] ime set command executed
- [ ] Default IME is set to AdbIME

---

## Step 4: Test Korean Input (1 minute)

### Command Line Test

```bash
adb -s 127.0.0.1:5555 shell am broadcast -a ADB_INPUT_TEXT --es msg '서초동'
```

**Verification**:
- Look at BlueStacks screen
- If text input field is focused, "서초동" should appear
- Text should be properly formatted in Korean

- [ ] Broadcast command runs without error
- [ ] Text appears on device (if input field is focused)

### Python Test Script

```bash
python test_korean_input.py
```

**Expected Output**:
```
============================================================
ADBKeyboard Status Report
============================================================
Device: (default)

Installation Status:
  ADBKeyboard Installed: ✓ YES
  ADBKeyboard Enabled:   ✓ YES

Input Method Configuration:
  Default IME: com.android.adbkeyboard/.AdbIME
  Available IMEs (1):
    - com.android.adbkeyboard/.AdbIME

Setup Status:
  ✓ READY FOR KOREAN INPUT
============================================================
```

- [ ] Test script runs without errors
- [ ] Status shows "READY FOR KOREAN INPUT"

### Extended Tests

```bash
python test_korean_input.py --test-korean
python test_korean_input.py --test-all --verbose
```

- [ ] `--test-korean` shows "Korean input test passed"
- [ ] `--test-all` shows all tests passing

---

## Step 5: Python Integration (1 minute)

### Test Import

```python
# In Python REPL or test file
from adb_auto_player.device.adb import AdbController
controller = AdbController()
manager = controller.unicode_input
print(manager.setup_complete())
# Should output: True
```

- [ ] Import successful (no errors)
- [ ] `unicode_input` property exists
- [ ] `setup_complete()` returns True

### Quick Function Test

```python
# Still in Python
controller.input_text_unicode('한글테스트')
# Should succeed (returns True or shows no error)
```

- [ ] Function call succeeds
- [ ] No exceptions raised

---

## Post-Setup Verification (2 minutes)

### File Check

```bash
# Check Python module exists
ls -la adbautoplayer/device/adb/adb_unicode_input.py

# Check test script exists
ls -la test_korean_input.py

# Check documentation exists
ls -la KOREAN_INPUT_QUICKSTART.md
ls -la ADBKEYBOARD_SETUP_GUIDE.md
```

- [ ] adb_unicode_input.py exists
- [ ] test_korean_input.py exists
- [ ] Documentation files exist

### Device Check

```bash
# Verify device status
adb -s 127.0.0.1:5555 shell ime list -a | grep AdbIME

# Verify default input method
adb -s 127.0.0.1:5555 shell settings get secure default_input_method
```

- [ ] AdbIME appears in IME list
- [ ] Default IME is AdbIME

### Code Check

```bash
# Check if AdbController modified correctly
grep -n "unicode_input" adbautoplayer/device/adb/adb_controller.py

# Check imports
grep -n "AdbUnicodeInputManager" adbautoplayer/device/adb/adb_controller.py
```

- [ ] AdbController has unicode_input property
- [ ] AdbController imports AdbUnicodeInputManager
- [ ] input_text_unicode method exists

---

## Final Confirmation

### All Checks Passed?

- [ ] **Step 1**: APK downloaded ✓
- [ ] **Step 2**: APK installed ✓
- [ ] **Step 3**: Input method enabled ✓
- [ ] **Step 4**: Tests pass ✓
- [ ] **Step 5**: Python integration works ✓
- [ ] **Verification**: Files and device config confirmed ✓

### Status

If all checkboxes are checked:

```
✓ SETUP COMPLETE - READY FOR KOREAN INPUT!
```

---

## Troubleshooting Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Device not found | `adb devices` | Restart ADB: `adb kill-server && adb start-server` |
| APK install fails | `adb install` output | Try: `adb install -r -g ADBKeyboard.apk` |
| Text doesn't appear | `ime list -a` | Re-enable: `ime set com.android.adbkeyboard/.AdbIME` |
| Import error | Check file exists | Run from project root directory |
| Unicode corruption | Encoding | Ensure `# -*- coding: utf-8 -*-` at file top |

**Detailed troubleshooting**: See `ADBKEYBOARD_SETUP_GUIDE.md`

---

## Next Steps After Setup

1. **Immediate**: Commit changes to Git
   ```bash
   git add adbautoplayer/device/adb/adb_unicode_input.py
   git add adbautoplayer/device/adb/adb_controller.py
   git add test_korean_input.py
   git add *.md
   git commit -m "feat: Add ADBKeyboard Korean text input support"
   ```

2. **Short-term**: Test with game bots
   - Try entering Korean player names
   - Test Korean location names
   - Verify in-game Korean text handling

3. **Documentation**: Share with team
   - Point to `KOREAN_INPUT_QUICKSTART.md` for quick start
   - Share success criteria and testing results
   - Create Korean game bot guide

---

## Support & Help

### Quick Questions?
- **How do I use it?** → See `KOREAN_INPUT_QUICKSTART.md`
- **Detailed setup?** → See `ADBKEYBOARD_SETUP_GUIDE.md`
- **Technical details?** → See `IMPLEMENTATION_DETAILS.md`

### Issues?
1. Run: `python test_korean_input.py --verbose`
2. Check: Device logs `adb logcat | grep AdbIME`
3. Refer: Troubleshooting section in `ADBKEYBOARD_SETUP_GUIDE.md`

### Want to know more?
- Read: `DELIVERY_SUMMARY.txt` (overview)
- Read: `KOREAN_INPUT_SETUP_SUMMARY.md` (executive summary)
- Read: `IMPLEMENTATION_DETAILS.md` (technical deep dive)

---

## Time Tracking

- **Step 1 (Download)**: 2 min ⏱
- **Step 2 (Install)**: 2 min ⏱
- **Step 3 (Enable)**: 1 min ⏱
- **Step 4 (Test)**: 1 min ⏱
- **Step 5 (Verify)**: 2 min ⏱

**Total**: ~8 minutes for complete setup

---

## Success Criteria Met?

```
Device: 127.0.0.1:5555
ADBKeyboard: ✓ Installed
Input Method: ✓ Enabled
Tests: ✓ Passing
Python: ✓ Ready
Documentation: ✓ Complete

STATUS: ✓ READY FOR KOREAN INPUT
```

---

**Congratulations!** You can now input Korean text in Android apps via ADB! 🎉

For next steps, see your project's game bot integration guide.
