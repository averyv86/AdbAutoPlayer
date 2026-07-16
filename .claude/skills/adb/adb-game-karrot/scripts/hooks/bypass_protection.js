// Frida Hook: Bypass Karrot App Protection Mechanisms
// Purpose: Disable detected protection to allow automated clicks

console.log("[*] Karrot Protection Bypass Hook Loaded");
console.log("[*] This will attempt to disable all detected protection mechanisms");

Java.perform(function() {
    var bypassStatus = {
        liappBypassed: false,
        systemExitDisabled: false,
        inputValidationBypassed: false,
        processMonitoringBlocked: false,
        debugDetectionBypass: false,
        clickInterceptionEnabled: false
    };

    // ========================================
    // Bypass 1: Disable System.exit()
    // ========================================
    try {
        console.log("[*] Attempting to bypass System.exit()...");

        var System = Java.use("java.lang.System");
        var exitMethod = System.exit.overload('int');

        var exitAttempts = 0;
        exitMethod.implementation = function(code) {
            exitAttempts++;
            console.log("[!!!] BLOCKED: System.exit(" + code + ") attempt #" + exitAttempts);
            console.log("[!!!] App would have crashed, but exit was blocked!");

            // Print stack trace to see who called exit
            var Exception = Java.use("java.lang.Exception");
            var e = Exception.$new();
            var sw = Java.use("java.io.StringWriter").$new();
            var pw = Java.use("java.io.PrintWriter").$new(sw);
            e.printStackTrace(pw);
            console.log("[CALLER] " + sw.toString().split('\n')[0]);

            // Don't actually exit - return null instead
            bypassStatus.systemExitDisabled = true;
            // Intentionally not calling original exit
            return null;
        };

        console.log("[+] System.exit() disabled - app won't crash on protected checks");

    } catch (e) {
        console.log("[-] System.exit() bypass failed: " + e.message);
    }

    // ========================================
    // Bypass 2: Spoof Input Event Source
    // ========================================
    try {
        console.log("[*] Attempting to bypass input validation...");

        var MotionEvent = Java.use("android.view.MotionEvent");
        var getSource = MotionEvent.getSource.overload();

        var sourceCheckCount = 0;
        getSource.implementation = function() {
            sourceCheckCount++;
            // Always return valid finger touch source (0x1002 = TOOL_TYPE_FINGER)
            var spoofedSource = 0x1002;

            if (sourceCheckCount <= 5) {
                console.log("[INPUT] Spoofing MotionEvent.getSource() -> 0x" + spoofedSource.toString(16));
            }

            bypassStatus.inputValidationBypassed = true;
            return spoofedSource;
        };

        console.log("[+] Input event source validation bypassed");

    } catch (e) {
        console.log("[-] Input validation bypass failed: " + e.message);
    }

    // ========================================
    // Bypass 3: Block Process Monitoring
    // ========================================
    try {
        console.log("[*] Attempting to block process monitoring...");

        var ActivityManager = Java.use("android.app.ActivityManager");
        var getRunningServices = ActivityManager.getRunningServices.overload('int');

        var callCount = 0;
        getRunningServices.implementation = function(maxNum) {
            callCount++;
            if (callCount <= 3) {
                console.log("[PROCESS] getRunningServices() call intercepted - returning empty list");
            }
            // Return empty list instead of real processes
            bypassStatus.processMonitoringBlocked = true;
            return Java.use("java.util.ArrayList").$new();
        };

        console.log("[+] Process monitoring blocked - returns empty service list");

    } catch (e) {
        console.log("[-] Process monitoring bypass failed: " + e.message);
    }

    // ========================================
    // Bypass 4: Disable Debug Detection
    // ========================================
    try {
        console.log("[*] Attempting to bypass debug detection...");

        var Debug = Java.use("android.os.Debug");
        var isDebuggerConnected = Debug.isDebuggerConnected.overload();

        var debugCheckCount = 0;
        isDebuggerConnected.implementation = function() {
            debugCheckCount++;
            if (debugCheckCount <= 3) {
                console.log("[DEBUG] Spoofing isDebuggerConnected() -> false");
            }
            bypassStatus.debugDetectionBypass = true;
            return false;
        };

        console.log("[+] Debug detection bypassed - always reports not connected");

    } catch (e) {
        console.log("[-] Debug detection bypass failed: " + e.message);
    }

    // ========================================
    // Bypass 5: LIAPP Neutralization
    // ========================================
    try {
        console.log("[*] Attempting to disable LIAPP protection...");

        var liappBypassCount = 0;

        // LIAPP CheckFile bypass
        try {
            var CheckFile = Java.use("com.liapp.checkfile.CheckFile");
            var checkMethod = CheckFile.check.overload();

            checkMethod.implementation = function() {
                liappBypassCount++;
                console.log("[LIAPP] CheckFile.check() bypassed #" + liappBypassCount);
                bypassStatus.liappBypassed = true;
                return true;
            };

            console.log("[+] LIAPP CheckFile.check() disabled");
        } catch (e) {
            // LIAPP might not be installed
        }

        // LIAPP interface bypass
        try {
            var LiappIface = Java.use("com.liapp.interfaces.a");
            var invokeMethod = LiappIface.invoke.overload();

            invokeMethod.implementation = function() {
                console.log("[LIAPP] Liapp invoke() bypassed");
                bypassStatus.liappBypassed = true;
                return null;
            };

            console.log("[+] LIAPP interface.invoke() disabled");
        } catch (e) {}

        if (liappBypassCount > 0) {
            console.log("[+] LIAPP protection disabled");
        } else {
            console.log("[*] LIAPP not detected (no bypasses needed)");
        }

    } catch (e) {
        console.log("[-] LIAPP bypass failed: " + e.message);
    }

    // ========================================
    // Enhancement: Monitor Click Success
    // ========================================
    try {
        console.log("[*] Installing click success monitor...");

        var View = Java.use("android.view.View");
        var performClick = View.performClick.overload();

        var clickCount = 0;
        var successCount = 0;
        var failureCount = 0;

        performClick.implementation = function() {
            clickCount++;
            var viewClass = this.getClass().getSimpleName();

            try {
                var result = performClick.call(this);
                successCount++;

                if (successCount <= 10) {
                    console.log("[SUCCESS] Click #" + clickCount + " on " + viewClass + " processed successfully");
                }

                bypassStatus.clickInterceptionEnabled = true;
                return result;

            } catch (e) {
                failureCount++;
                console.log("[FAILED] Click #" + clickCount + " failed: " + e.message);
                throw e;
            }
        };

        console.log("[+] Click success monitoring enabled");

    } catch (e) {
        console.log("[-] Click monitoring installation failed: " + e.message);
    }

    // ========================================
    // Final Report
    // ========================================
    console.log("\n" + "=".repeat(50));
    console.log("BYPASS INSTALLATION SUMMARY");
    console.log("=".repeat(50));

    var bypassCount = 0;

    if (bypassStatus.systemExitDisabled) {
        console.log("[+] System.exit() disabled");
        bypassCount++;
    }

    if (bypassStatus.inputValidationBypassed) {
        console.log("[+] Input validation bypassed");
        bypassCount++;
    }

    if (bypassStatus.processMonitoringBlocked) {
        console.log("[+] Process monitoring blocked");
        bypassCount++;
    }

    if (bypassStatus.debugDetectionBypass) {
        console.log("[+] Debug detection bypassed");
        bypassCount++;
    }

    if (bypassStatus.liappBypassed) {
        console.log("[+] LIAPP protection disabled");
        bypassCount++;
    }

    if (bypassStatus.clickInterceptionEnabled) {
        console.log("[+] Click monitoring enabled");
        bypassCount++;
    }

    console.log("\n[*] Total bypasses installed: " + bypassCount);
    console.log("[+] All protection mechanisms should now be disabled!");
    console.log("[+] Try clicking buttons in the app - should work without crashes");
    console.log("\n[*] If app still crashes:");
    console.log("    1. Check logcat for actual crash reason");
    console.log("    2. Look for other protection mechanisms");
    console.log("    3. Try different bypass strategies");

    console.log("=".repeat(50));

    // Send results back to console
    send({
        type: "bypass_status",
        bypasses_installed: bypassCount,
        status: bypassStatus,
        ready: bypassCount > 0
    });

});
