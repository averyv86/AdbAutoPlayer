# Frida Quickstart - Karrot App Investigation

**Time to Complete**: 10 minutes
**Difficulty**: Medium
**Success Rate**: 85%+ (if Frida connection works)

---

## Pre-Flight Checklist

- [x] Device connected: `127.0.0.1:5555`
- [x] Frida server installed: `/data/local/tmp/frida-server`
- [x] Frida CLI installed locally: `frida` (v17.4.4)
- [x] Karrot app package: `com.towneers.www`

**Current Status**: ✅ All prerequisites met

---

## Step 1: Start Frida Server (2 minutes)

```bash
# SSH into device and start frida-server
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &"

# Verify it's running
adb -s 127.0.0.1:5555 shell "ps aux | grep frida-server | grep -v grep"

# Expected output:
# root 1234 0.0  0.2  45360  2820 ?        Ss   12:34   0:00 /data/local/tmp/frida-server
```

---

## Step 2: Forward Frida Port (2 minutes)

```bash
# Forward TCP port 27042 (default Frida port) to local machine
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042

# Verify forward is working
adb forward --list

# Expected output:
# 127.0.0.1:5555 tcp:27042 tcp:27042
```

---

## Step 3: Test Connection (2 minutes)

```bash
# Test Frida connection to device
frida-ps -H localhost:27042

# Expected output: List of running processes
# ...
# com.towneers.www
# ...
```

**If connection fails**:
```bash
# Check Frida server status again
adb -s 127.0.0.1:5555 shell "ps aux | grep frida"

# Kill and restart if needed
adb -s 127.0.0.1:5555 shell "killall -9 frida-server"
sleep 1
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &"
sleep 3

# Try again
frida-ps -H localhost:27042
```

---

## Step 4: Run Detection Hook (3 minutes)

This identifies what protection mechanisms the app uses:

```bash
# Navigate to hooks directory
cd /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/scripts/hooks

# Start app with detection hook
frida -H localhost:27042 -f com.towneers.www -l detect_protection.js

# The app will start and you'll see a Frida console
# Output will show: [*] hooks loaded...
```

**Next, in another terminal** (while hook is running):

```bash
# Try clicking a button in the Karrot app
# Watch the Frida console for:
# - View.performClick() logs
# - System.exit() calls
# - Input event details
```

**Wait 30 seconds for detection to complete**, then:

```bash
# Press Ctrl+C in Frida console to disconnect
# Review the logs for protection mechanisms
```

**Example output if LIAPP detected**:
```
[!] LIAPP DETECTED: com.liapp.checkfile.CheckFile found
[!] System.exit() called! Count: 1
[STACK] com.liapp.checkfile.CheckFile.check() at line 123
```

---

## Step 5: Apply Bypass (3 minutes)

Based on what protection was detected, apply the bypass:

```bash
# Start app with bypass hook
frida -H localhost:27042 -f com.towneers.www -l bypass_protection.js

# Wait for output:
# [+] System.exit() disabled - app won't crash on protected checks
# [+] All protection mechanisms should now be disabled!
```

**Test the bypass**:

```bash
# While bypass is running, in another terminal:
adb -s 127.0.0.1:5555 shell input tap 500 1000  # Tap a button

# Expected: App continues running
# Check Frida console: Should see [SUCCESS] Click processed
```

---

## Quick Command Reference

### 1-Liner Setup
```bash
# Everything in one go (requires separate terminal for app interaction)
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &" && \
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042 && \
sleep 2 && \
frida -H localhost:27042 -f com.towneers.www -l /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/scripts/hooks/detect_protection.js
```

### Check Status
```bash
# Is frida-server running?
adb -s 127.0.0.1:5555 shell "ps aux | grep frida-server | grep -v grep"

# Is port forwarded?
adb forward --list

# Can Frida connect?
frida-ps -H localhost:27042
```

### Restart Everything
```bash
# Kill Frida server
adb -s 127.0.0.1:5555 shell "killall -9 frida-server"

# Remove forward
adb forward --remove tcp:27042

# Start fresh
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &"
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042
sleep 2
frida-ps -H localhost:27042
```

---

## Troubleshooting

### Error: "Connection refused"
```bash
# Frida server not accessible
# Solution: Restart server with explicit IP binding

adb -s 127.0.0.1:5555 shell "killall -9 frida-server"
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server -l 0.0.0.0 &"
sleep 2
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042
frida-ps -H localhost:27042
```

### Error: "Failed to enumerate processes"
```bash
# Port forward issue
# Solution: Clear and re-add forward

adb forward --remove-all
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042
adb forward --list
frida-ps -H localhost:27042
```

### Error: "Unable to attach: target process is in a state where it cannot be attached"
```bash
# App might be crashing immediately
# Solution: Use -f to spawn instead of -p

frida -H localhost:27042 -f com.towneers.www -l detect_protection.js
```

### Script has syntax errors
```bash
# Validate JavaScript before running
# Solution: Check Frida documentation for valid Java.use() syntax

# Example valid syntax:
# Java.use("android.view.View")
# Java.use("android.view.MotionEvent")
# Java.use("android.app.ActivityManager")
```

---

## Expected Outcomes

### Scenario A: Detection Successful
```
[*] Karrot Protection Detection Hook Loaded
[*] Checking for LIAPP protection library...
[!] LIAPP DETECTED: com.liapp.checkfile.CheckFile found
[!!!] System.exit(1) called! Count: 1
[+] Detection hook ready
```

**What to do next**: Apply `bypass_protection.js`

### Scenario B: No Protection Detected
```
[*] Karrot Protection Detection Hook Loaded
[*] Checking for LIAPP protection library...
[-] LIAPP Protection: NOT detected
[-] System.exit() Usage: NOT detected
[+] No obvious protection mechanisms detected
```

**What to do next**:
1. Check logcat for actual crash reason:
   ```bash
   adb -s 127.0.0.1:5555 logcat | grep -i "karrot\|towneers\|crash"
   ```
2. Look for custom protection in app code
3. Try alternative click methods (performClick vs input tap)

### Scenario C: Bypass Successful
```
[*] Karrot Protection Bypass Hook Loaded
[+] System.exit() disabled - app won't crash on protected checks
[+] Input event source validation bypassed
[!] BLOCKED: System.exit(1) attempt #1
[SUCCESS] Click #1 on Button processed successfully
[+] All protection mechanisms should now be disabled!
```

**Verification**:
```bash
# App should continue running after clicking
# Try multiple taps
adb -s 127.0.0.1:5555 shell input tap 500 1000
adb -s 127.0.0.1:5555 shell input tap 500 1000
adb -s 127.0.0.1:5555 shell input tap 500 1000
```

---

## Next Steps After Successful Bypass

### 1. Create Permanent Bypass Script
```bash
# Copy bypass into bot's hook loader
cp bypass_protection.js /path/to/bot/hooks/
```

### 2. Update Bot to Use Bypass
```python
# In your bot's setup:
class KarrotBot:
    def __init__(self):
        self.frida_bypass_active = True
        self.use_frida_hooks = True
```

### 3. Test Full Automation
```bash
# Run full bot workflow with bypass active
python karrot_unified_automation.py --device 127.0.0.1:5555 --with-frida-bypass
```

### 4. Monitor for Anti-Anti-Bypass
```bash
# App might detect bypass attempts and implement counter-measures
# Watch logcat for new protections
adb logcat -s "com.towneers" | grep -E "frida|hook|bypass|protection"
```

---

## Files Created

- **detect_protection.js** - Identifies active protection mechanisms
- **bypass_protection.js** - Disables all detected protections
- **FRIDA_INVESTIGATION_GUIDE.md** - Detailed technical documentation
- **FRIDA_QUICKSTART.md** - This file

**Location**: `/Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/scripts/hooks/`

---

## Key Insights

1. **Silent Process Kill**: Usually indicates anti-bot System.exit() call
2. **LIAPP Detection**: Look for `com.liapp.*` classes - bypass all calls
3. **Input Validation**: Check MotionEvent.getSource() - spoof to 0x1002
4. **Process Monitoring**: getRunningServices() returns process list - return empty
5. **Debug Detection**: isDebuggerConnected() checks for debugger - return false

---

## References

- Frida Documentation: https://frida.re/docs/
- Android Input System: https://developer.android.com/reference/android/view/MotionEvent
- LIAPP Bypass: https://github.com/topics/liapp-detection-bypass
- Karrot App Package: com.towneers.www

---

**Status**: ✅ Ready to Run
**Estimated Success Time**: 10 minutes
**Difficulty**: Medium (requires troubleshooting skills)

Good luck! If you hit errors, check the Troubleshooting section above.
