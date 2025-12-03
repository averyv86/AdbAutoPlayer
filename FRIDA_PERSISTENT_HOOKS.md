# Keeping Frida Hooks Active After CLI Disconnects

**Purpose**: Practical guide to maintaining Frida instrumentation hooks that survive after the Frida CLI disconnects or the controlling computer terminates the connection.

**Use Cases**:
- Long-running background monitoring on Android devices
- Continuous hook activity without keeping CLI connected
- Battery-efficient hook deployment for mobile apps
- Testing scenarios requiring persistent instrumentation

---

## Solution 1: Frida Server (Always Recommended)

The most reliable and tested approach for persistent hooks on Android.

### How It Works

Frida Server runs as a persistent daemon on the Android device that:
1. Stays running indefinitely (unless killed)
2. Accepts connections from Frida CLI on demand
3. Maintains hooks across multiple connection/disconnection cycles
4. Requires root access to attach to other apps

### Implementation Steps

**1. Download and Push Frida Server to Device**:

```bash
# Download frida-server (match your Android architecture)
# For ARM64: frida-server-16.4.11-android-arm64.xz
# For ARMv7: frida-server-16.4.11-android-arm.xz
# For x86: frida-server-16.4.11-android-x86.xz

unxz frida-server-16.4.11-android-arm64.xz

adb push frida-server-16.4.11-android-arm64 /data/local/tmp/frida-server

adb shell chmod +x /data/local/tmp/frida-server
```

**2. Run Frida Server on Device** (via adb shell):

```bash
adb shell /data/local/tmp/frida-server
```

Or run in background with nohup:

```bash
adb shell "nohup /data/local/tmp/frida-server > /dev/null 2>&1 &"
```

**3. Connect from CLI (repeatedly)**:

```bash
# First connection - inject hooks
frida-ps -U  # List processes on USB device
frida -U -f com.example.app -l script.js

# Disconnect and reconnect later - hooks remain active
frida -U com.example.app --attach  # Reattach without script
```

### Verification

```bash
# Check if Frida server is running
adb shell ps | grep frida-server

# Check listening ports
adb shell netstat -tuln | grep 27042  # Default Frida port
```

### Advantages
- Simple, standard solution
- No code modifications needed
- Works across multiple sessions
- Hooks persist indefinitely until device reboot
- Can attach/detach multiple times

### Limitations
- Requires root access
- Hooks lost on device reboot
- Server uses persistent battery

---

## Solution 2: Frida Gadget (Best for App-Embedded Hooks)

Embed Frida directly into an Android app APK for hooks that survive the app lifecycle.

### How It Works

Frida Gadget is a native library that:
1. Gets embedded in the app's APK during build
2. Loads when the app starts
3. Keeps hooks active as long as the app runs
4. Doesn't require root access
5. Doesn't require CLI connection

### Implementation Steps

**1. Add Frida Gadget to Your App**:

Download the gadget library matching your architecture:

```bash
# For ARM64
wget https://github.com/frida/frida/releases/download/16.4.11/frida-gadget-16.4.11-android-arm64.so.xz

unxz frida-gadget-16.4.11-android-arm64.so.xz

# Copy to your app's jniLibs folder
mkdir -p app/src/main/jniLibs/arm64-v8a
cp frida-gadget-16.4.11-android-arm64.so app/src/main/jniLibs/arm64-v8a/libfrida-gadget.so
```

**2. Load Gadget in Your Code** (Java/Kotlin):

```java
public class MyApplication extends Application {
    static {
        System.loadLibrary("frida-gadget");
    }

    @Override
    public void onCreate() {
        super.onCreate();
        // Gadget loads automatically, hooks are now active
    }
}
```

**3. Configure Gadget** (config.json):

Create `app/src/main/assets/frida-gadget-config.json`:

```json
{
  "interaction": {
    "type": "listen",
    "address": "tcp",
    "port": 27042
  },
  "enableDatabase": true
}
```

**4. Load Custom Instrumentation Script** (optional):

```json
{
  "interaction": {
    "type": "script",
    "script": "/data/local/tmp/hooks.js"
  },
  "enableDatabase": true
}
```

### Advanced: Direct Script Injection

Embed JavaScript directly in the config:

```json
{
  "interaction": {
    "type": "inline",
    "script": "console.log('Frida Gadget loaded'); Interceptor.attach(Module.findExportByName('libc.so', 'open'), {...})"
  }
}
```

### Advantages
- No root required
- Survives app restarts
- Can be deployed via app updates
- Hooks active immediately when app launches
- No external CLI needed

### Limitations
- Requires app rebuild/repackaging
- Only works while app is running
- Slightly increases app size (~3MB)
- App must have debug mode or be properly signed

---

## Solution 3: Persistent Background Service (Android Native)

Combine Frida Server with an Android service that automatically restarts it.

### How It Works

Create an Android service that:
1. Starts Frida Server when device boots
2. Restarts the server if it crashes
3. Runs in background indefinitely

### Implementation Steps

**1. Create Frida Server Wrapper Service** (Java):

```java
package com.example.frida;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;
import java.io.InputStream;

public class FridaServerService extends Service {
    private static final String TAG = "FridaServer";
    private Process fridaProcess;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startFridaServer();
        return START_STICKY;  // Restart if killed
    }

    private void startFridaServer() {
        try {
            String fridaPath = "/data/local/tmp/frida-server";
            ProcessBuilder pb = new ProcessBuilder(fridaPath);
            fridaProcess = pb.start();
            Log.d(TAG, "Frida Server started");
        } catch (Exception e) {
            Log.e(TAG, "Error starting Frida Server", e);
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (fridaProcess != null) {
            fridaProcess.destroy();
        }
        // Service will be restarted due to START_STICKY
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
```

**2. Add to AndroidManifest.xml**:

```xml
<manifest>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />

    <application>
        <service
            android:name=".FridaServerService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="other" />
    </application>
</manifest>
```

**3. Start Service on Boot**:

```java
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Intent serviceIntent = new Intent(context, FridaServerService.class);
            context.startForegroundService(serviceIntent);
        }
    }
}
```

Add to manifest:

```xml
<receiver
    android:name=".BootReceiver"
    android:enabled="true"
    android:exported="false">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED" />
    </intent-filter>
</receiver>
```

### Advantages
- Survives device reboots
- Automatically restarts if crashed
- Full control over server lifecycle
- Can monitor and log server status

### Limitations
- Requires Android app development
- Needs boot permission
- More complex than simple server approach

---

## Solution 4: Script-Level Hook Persistence

Configure your Frida JavaScript to maintain hooks even when the connection drops.

### Implementation

**Script with Built-in Persistence**:

```javascript
// hooks.js - Persistent instrumentation

// Global state to maintain across connection drops
const hooks = {};

// Hook target function
function setupPersistentHook() {
    try {
        const libc = Module.findBaseAddress('libc.so');
        if (!libc) {
            console.log('[Hooks] libc.so not found');
            return;
        }

        const openFunc = Module.findExportByName('libc.so', 'open');

        Interceptor.attach(openFunc, {
            onEnter: function(args) {
                const path = Memory.readUtf8String(args[0]);
                hooks.lastOpen = {
                    path: path,
                    timestamp: Date.now()
                };
                console.log('[open] ' + path);
            },
            onLeave: function(retval) {
                // Hook remains active even if client disconnects
            }
        });

        console.log('[Hooks] Persistent open() hook installed');
    } catch (e) {
        console.log('[Error] ' + e.toString());
    }
}

// Install on script load
setupPersistentHook();

// Expose state for inspection
rpc.exports = {
    getLastOpen: function() {
        return hooks.lastOpen;
    },
    getStatus: function() {
        return {
            state: 'active',
            timestamp: Date.now(),
            lastOpen: hooks.lastOpen
        };
    }
};
```

**Attach with Server Loop**:

```bash
#!/bin/bash
# keep-frida-running.sh

PACKAGE="com.example.app"
SCRIPT="hooks.js"

while true; do
    echo "[$(date)] Connecting to $PACKAGE..."

    frida -U -f "$PACKAGE" -l "$SCRIPT" --no-pause

    echo "[$(date)] Connection lost, reconnecting in 5s..."
    sleep 5
done
```

Run with:

```bash
bash keep-frida-running.sh
```

### Advantages
- Hooks survive client disconnection
- Can monitor hook activity
- Flexible logging and persistence
- Works with existing Frida infrastructure

### Limitations
- Hooks lost when app crashes/restarts
- Requires running reconnection script
- Client must have access to device

---

## Solution 5: Dump and Restore Hooks

Save hook state and reapply after disconnection.

### Implementation

**Save Hook State**:

```javascript
// Save current hook state before disconnecting
const hookState = {
    hooked_functions: [
        {
            module: 'libc.so',
            function: 'open',
            params: 2
        }
    ],
    timestamp: Date.now()
};

// Export state for external storage
rpc.exports = {
    getHookState: function() {
        return hookState;
    },
    applyHooks: function(state) {
        // Reapply hooks from saved state
        state.hooked_functions.forEach(function(hook) {
            const addr = Module.findExportByName(hook.module, hook.function);
            if (addr) {
                Interceptor.attach(addr, {
                    onEnter: function(args) { console.log('[' + hook.function + ']'); }
                });
            }
        });
        return true;
    }
};
```

**Reconnect Script**:

```python
#!/usr/bin/env python3
import frida
import json

def attach_with_hooks(device_id, package, script_path):
    device = frida.get_device(device_id)

    # Try to attach first
    try:
        session = device.attach(package)
        with open(script_path) as f:
            script = session.create_script(f.read())
        script.load()
        return script
    except Exception as e:
        print(f"Initial attach failed: {e}")
        return None

if __name__ == '__main__':
    import sys
    package = sys.argv[1] if len(sys.argv) > 1 else 'com.example.app'

    script = attach_with_hooks('usb', package, 'hooks.js')
    if script:
        print("Hooks applied successfully")
```

---

## Quick Comparison Table

| Method | Root Required | Persistent | Setup Complexity | Battery Impact |
|--------|---------------|-----------|------------------|-----------------|
| **Frida Server** | Yes | Device reboot | Low | Medium |
| **Frida Gadget** | No | App runtime | Medium | Low |
| **Boot Service** | Yes | Device reboot | High | Medium-High |
| **Script Loop** | No | Connection only | Low | Low |
| **Save/Restore** | No | Manual | Medium | Low |

---

## Android-Specific Best Practices

### 1. Hook Location

```javascript
// Prefer loading from system libraries (stable)
const openFunc = Module.findExportByName('libc.so', 'open');

// Avoid app-specific libraries (may reload)
const appFunc = Module.findExportByName(null, 'com_example_MyClass_nativeFunc');
```

### 2. Error Handling

```javascript
Interceptor.attach(target, {
    onEnter: function(args) {
        try {
            // Hook logic
        } catch(e) {
            console.log('[Error] ' + e.toString());
            // Don't let hook errors crash the process
        }
    }
});
```

### 3. Memory Safety

```javascript
// Always check before reading memory
function safeReadString(ptr) {
    try {
        if (ptr.isNull()) return '[null]';
        return Memory.readUtf8String(ptr);
    } catch(e) {
        return '[invalid]';
    }
}
```

### 4. Battery Optimization

```javascript
// Reduce logging frequency for battery life
let logCounter = 0;
const LOG_FREQUENCY = 100;  // Log every 100 calls

Interceptor.attach(target, {
    onEnter: function(args) {
        if (++logCounter % LOG_FREQUENCY === 0) {
            console.log('[call #' + logCounter + ']');
        }
    }
});
```

---

## Troubleshooting

### Hooks Not Persisting

```bash
# Check if Frida server is still running
adb shell ps | grep frida-server

# Check if app crashed
adb logcat | grep -i crash

# Monitor hook status
frida -U com.example.app -c "rpc.call('getStatus')"
```

### Connection Drops Frequently

```bash
# Use longer timeout
frida -U --socket-timeout=60 com.example.app -l script.js

# Forward with adb for better stability
adb forward tcp:27042 tcp:27042
frida -H 127.0.0.1:27042 com.example.app -l script.js
```

### Hooks Active But Not Executing

```javascript
// Add verbose logging
Interceptor.attach(target, {
    onEnter: function(args) {
        console.log('[HOOK FIRED]');  // This should print
        // ... hook logic
    }
});
```

---

## Recommended Architecture for AdbAutoPlayer

Based on the AdbAutoPlayer project (game automation), here's the recommended approach:

**1. Primary Method: Frida Server**
```bash
# Push and run server
adb push frida-server-16.4.11-android-arm64 /data/local/tmp/frida-server
adb shell chmod +x /data/local/tmp/frida-server
adb shell nohup /data/local/tmp/frida-server &
```

**2. Backup Method: Gadget (if rebuilding app)**
Embed Frida Gadget in AdbAutoPlayer's instrumentation app to ensure hooks survive app restarts during game automation.

**3. Monitoring: Keep-Alive Script**
```python
# monitors_frida_connection.py
while True:
    try:
        device = frida.get_usb_device()
        device.get_frontmost_application()
        print("[OK] Frida connection active")
    except:
        print("[ERROR] Reconnecting...")
    sleep(10)
```

---

## Summary

**For immediate deployment**: Use **Frida Server** (Solution 1) - simplest, most tested
**For long-term reliability**: Add **boot service** (Solution 3) to restart on device reboot
**For app-embedded hooks**: Use **Frida Gadget** (Solution 2) if you control the app
**For monitoring**: Combine with **script loop** (Solution 4) for resilience

---

**References**:
- Frida Official Documentation: https://frida.re/docs/
- Frida CodeShare: https://codeshare.frida.re/
- Android Service Lifecycle: https://developer.android.com/guide/components/services
- Frida JavaScript API: https://frida.re/docs/javascript-api/

**Last Updated**: 2025-12-04
