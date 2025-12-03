# Frida Investigation Guide for Karrot App (com.towneers.www)

**Purpose**: Use Frida to detect and bypass anti-automation protection in Karrot app
**Status**: Investigation Ready
**Last Updated**: 2025-12-03

---

## Quick Reference

### Current Status
- **Device**: 127.0.0.1:5555 (Samsung Galaxy S24)
- **Frida Server**: ✅ Installed at `/data/local/tmp/frida-server`
- **Frida CLI**: ✅ Installed locally (v17.4.4)
- **Karrot App**: ✅ Package found (com.towneers.www)
- **Connection Status**: ⚠️ Needs forward setup (see Step 1 below)

### Problem Summary
Any tap on clickable elements in Karrot app crashes the process silently:
1. App receives tap event
2. Process immediately terminates (no exception, no logcat warning)
3. Silent kill suggests active protection mechanism

**Hypothesis**: Anti-automation library (possibly LIAPP) is detecting ADB input and killing process

---

## Investigation Steps

### Step 1: Forward Frida Server (TCP Connection)

Frida needs to communicate with frida-server via TCP. Set up port forwarding:

```bash
# Forward device port 27042 (default Frida server port) to localhost
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042

# Verify connection
frida-ps -H localhost:27042
```

Expected output: List of running processes

### Step 2: Start Karrot App with Frida

Start the app and attach Frida hook immediately:

```bash
# Option A: Start with auto-attach
frida -H localhost:27042 -f com.towneers.www -l hook.js

# Option B: Attach to running process
adb -s 127.0.0.1:5555 shell am start -n com.towneers.www/.MainActivity
sleep 3
frida -H localhost:27042 -n "com.towneers.www" -l hook.js
```

### Step 3: Hook Detection (View Input Interception)

**Frida Script**: `hooks/detect_click_handler.js`

This script intercepts click handling at multiple levels:

```javascript
// Level 1: View.performClick() - Most direct hook
var View = Java.use("android.view.View");
var performClick = View.performClick.overload();

var clickCount = 0;
performClick.implementation = function() {
    clickCount++;
    console.log("[CLICK] View.performClick() called #" + clickCount);
    console.log("  View type: " + this.getClass().getName());
    console.log("  View ID: " + this.getId());
    return performClick.call(this);
};

// Level 2: MotionEvent.getSource() - Event validation
var MotionEvent = Java.use("android.view.MotionEvent");
var getSource = MotionEvent.getSource.overload();

getSource.implementation = function() {
    var source = getSource.call(this);
    console.log("[INPUT] MotionEvent.getSource() = 0x" + source.toString(16));
    return source;
};

// Level 3: InputEvent interception
var InputEvent = Java.use("android.view.InputEvent");
var getDeviceId = InputEvent.getDeviceId.overload();

getDeviceId.implementation = function() {
    var deviceId = getDeviceId.call(this);
    console.log("[INPUT] Device ID: " + deviceId);
    return deviceId;
};
```

### Step 4: Search for Anti-Bot Patterns

**Common anti-automation detection patterns**:

```javascript
// Pattern 1: LIAPP check
try {
    Java.use("com.liapp.checkfile.CheckFile");
    console.log("[!] LIAPP protection detected!");
} catch (e) {}

// Pattern 2: Generic isAutomation checks
var Runtime = Java.use("java.lang.Runtime");
var getDeclaredMethods = Java.use("java.lang.Class").getDeclaredMethods;

try {
    var clz = Runtime.getRuntime().getClass();
    var methods = clz.getDeclaredMethods();
    for (var i = 0; i < methods.length; i++) {
        var methodName = methods[i].getName();
        if (methodName.indexOf("isAutomation") !== -1 ||
            methodName.indexOf("isFake") !== -1 ||
            methodName.indexOf("isBot") !== -1) {
            console.log("[!] Suspicious method: " + methodName);
        }
    }
} catch (e) {}

// Pattern 3: InputDevice validation
var InputDevice = Java.use("android.view.InputDevice");
var getDevice = InputDevice.getDevice;

getDevice.implementation = function(deviceId) {
    var device = getDevice.call(this, deviceId);
    console.log("[DEBUG] InputDevice " + deviceId + ": " + device);
    return device;
};

// Pattern 4: Process validation
var ActivityManager = Java.use("android.app.ActivityManager");
try {
    var getRunningServices = ActivityManager.getRunningServices;
    getRunningServices.implementation = function(maxNum) {
        console.log("[DEBUG] getRunningServices called with maxNum: " + maxNum);
        return getRunningServices.call(this, maxNum);
    };
} catch (e) {}
```

### Step 5: Monitor Process Termination

Track when and why the process crashes:

```javascript
// Hook Process.start to see if app spawns verification process
var ProcessBuilder = Java.use("java.lang.ProcessBuilder");
var start = ProcessBuilder.start.overload();

start.implementation = function() {
    var cmd = this.command();
    var cmdStr = "";
    for (var i = 0; i < cmd.size(); i++) {
        cmdStr += cmd.get(i).toString() + " ";
    }
    console.log("[PROCESS] Starting: " + cmdStr);
    return start.call(this);
};

// Hook Runtime.exec()
var Runtime = Java.use("java.lang.Runtime");
var exec = Runtime.exec.overload('[Ljava/lang/String;');

exec.implementation = function(cmdArray) {
    var cmdStr = "";
    for (var i = 0; i < cmdArray.length; i++) {
        cmdStr += cmdArray[i] + " ";
    }
    console.log("[PROCESS] Executing: " + cmdStr);
    return exec.call(this, cmdArray);
};

// Hook System.exit()
var System = Java.use("java.lang.System");
var exitMethod = System.exit.overload('I');

exitMethod.implementation = function(code) {
    console.log("[!!!] System.exit(" + code + ") called!");
    console.log("[!!!] Stack trace:");
    var Exception = Java.use("java.lang.Exception");
    var e = Exception.$new();
    e.printStackTrace();
    return exitMethod.call(this, code);
};
```

### Step 6: Bypass Strategies

Once protection is detected, apply bypass:

**Strategy A: Disable Source Validation**

```javascript
var MotionEvent = Java.use("android.view.MotionEvent");
var getSource = MotionEvent.getSource.overload();

var originalGetSource = getSource.implementation;
getSource.implementation = function() {
    // Return valid finger touch source
    return 0x1002; // TOOL_TYPE_FINGER
};
console.log("[BYPASS] MotionEvent.getSource() hooked to return 0x1002");
```

**Strategy B: Hook View.performClick() at Interceptor Level**

```javascript
var View = Java.use("android.view.View");
var performClick = View.performClick.overload();

performClick.implementation = function() {
    try {
        console.log("[INTERCEPT] performClick on: " + this.getClass().getSimpleName());
        var result = performClick.call(this);
        console.log("[SUCCESS] Click processed without termination");
        return result;
    } catch (e) {
        console.log("[ERROR] Click failed: " + e.getMessage());
        throw e;
    }
};
```

**Strategy C: Intercept Verification Methods**

```javascript
// Hook potential isAutomation() checks
var ActivityManager = Java.use("android.app.ActivityManager");
try {
    // If app calls getRunningServices() to detect automation
    var getRunningServices = ActivityManager.getRunningServices;
    getRunningServices.implementation = function(maxNum) {
        // Return empty list (no background processes)
        return Java.use("java.util.ArrayList").$new();
    };
    console.log("[BYPASS] getRunningServices spoofed to return empty list");
} catch (e) {}

// Hook Debug.isDebuggerConnected()
var Debug = Java.use("android.os.Debug");
try {
    var isDebuggerConnected = Debug.isDebuggerConnected.overload();
    isDebuggerConnected.implementation = function() {
        return false;
    };
    console.log("[BYPASS] Debug.isDebuggerConnected() spoofed to false");
} catch (e) {}
```

**Strategy D: Catch and Prevent System.exit()**

```javascript
var System = Java.use("java.lang.System");
var exit = System.exit.overload('I');

exit.implementation = function(code) {
    console.log("[!!!] BLOCKED: System.exit(" + code + ") attempt intercepted!");
    // Don't call original - prevent exit
    // return; // Comment out to allow exit for testing

    // OR: Rethrow with no effect
    return null;
};
console.log("[BYPASS] System.exit() disabled");
```

---

## Frida Hook Files

Create these scripts in `/scripts/hooks/` directory:

### hooks/detect_protection.js
Detects which protection mechanism is active

### hooks/bypass_click_validation.js
Disables click source validation

### hooks/bypass_process_kill.js
Prevents System.exit() during click

### hooks/monitor_events.js
Logs all input events for analysis

---

## Testing Procedure

### Quick Test (5 minutes)

```bash
# 1. Setup forward
adb -s 127.0.0.1:5555 forward tcp:27042 tcp:27042

# 2. Start app with monitor hook
frida -H localhost:27042 -f com.towneers.www -l hooks/monitor_events.js

# 3. Try to tap button in app
# Watch console for:
# - View.performClick() calls
# - MotionEvent details
# - System.exit() attempts

# Expected: Either works OR we see exit attempt
```

### Full Analysis (15 minutes)

```bash
# 1. Start detection hook
frida -H localhost:27042 -f com.towneers.www -l hooks/detect_protection.js

# 2. Look for patterns in output:
# - LIAPP detection
# - Process verification attempts
# - InputDevice checks
# - getRunningServices calls

# 3. Based on findings, apply appropriate bypass
```

### Bypass Testing (20 minutes)

```bash
# 1. Start with both monitor + bypass
# Create combined script: hooks/combined_monitor_bypass.js

frida -H localhost:27042 -f com.towneers.www -l hooks/combined_monitor_bypass.js

# 2. Try clicks again
# Expected: App continues running, logs show bypassed checks

# 3. If still crashes:
# - Check logcat for actual error
# - Try alternative bypass strategy
```

---

## Expected Findings

### If LIAPP Detected
```javascript
// Bypass strategy
Java.use("com.liapp.checkfile.CheckFile").check.implementation = function() {
    return true;
};

Java.use("com.liapp.interfaces.a").invoke.implementation = function() {
    return null;
};
```

### If Event Source Validation
```javascript
// Bypass: Spoof valid source
var MotionEvent = Java.use("android.view.MotionEvent");
MotionEvent.getSource.implementation = function() {
    return 0x1002; // TOOL_TYPE_FINGER
};
```

### If Process Monitoring
```javascript
// Bypass: Disable exit
var System = Java.use("java.lang.System");
System.exit.implementation = function(code) {
    // Don't exit
    return null;
};
```

---

## Troubleshooting

### "Failed to enumerate processes"
```bash
# Frida server not running properly
adb -s 127.0.0.1:5555 shell "ps aux | grep frida-server"

# Restart if needed
adb -s 127.0.0.1:5555 shell "killall frida-server"
adb -s 127.0.0.1:5555 shell "/data/local/tmp/frida-server &"
sleep 2
```

### "Unable to attach"
```bash
# App might be crashed, restart it
adb -s 127.0.0.1:5555 shell "am force-stop com.towneers.www"
sleep 2
adb -s 127.0.0.1:5555 shell "am start -n com.towneers.www/.MainActivity"
```

### Script errors in Frida
```bash
# Check syntax and Java class availability
frida -H localhost:27042 -p 0 # Attach to system process for testing

# Test individual Java classes
# In Frida console:
Java.use("android.view.View")
Java.use("android.view.MotionEvent")
```

---

## Next Steps

1. **Execute detection hook** → Identify protection mechanism
2. **Apply appropriate bypass** → Test with specific strategy
3. **Document findings** → Record what worked
4. **Integrate into bot** → Use bypass in automated taps
5. **Monitor for anti-anti-bypass** → Watch for response to bypass attempt

---

## Success Criteria

✅ **Investigation Success**:
- Frida attaches without errors
- Hooks fire and log events
- Protection mechanism identified (LIAPP, System.exit, etc.)

✅ **Bypass Success**:
- App remains running after click
- Verification methods bypassed
- Input events processed normally

✅ **Automation Success**:
- Bot can tap elements without crashes
- Multiple taps in sequence work
- State changes reflect in UI

---

## References

- [Frida Documentation](https://frida.re/)
- [Java.use() API](https://frida.re/docs/javascript-api/)
- [Android Input System](https://developer.android.com/reference/android/view/MotionEvent)
- [LIAPP Detection Bypasses](https://github.com/topics/liapp-detection-bypass)

