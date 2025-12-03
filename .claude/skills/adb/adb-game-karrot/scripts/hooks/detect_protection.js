// Frida Hook: Detect Karrot App Protection Mechanisms
// Purpose: Identify which anti-automation library/method is active

console.log("[*] Karrot Protection Detection Hook Loaded");

Java.perform(function() {
    var findings = {
        liapp: false,
        systemExit: false,
        inputValidation: false,
        processMonitoring: false,
        debugDetection: false
    };

    // ========================================
    // Detection 1: LIAPP Protection Library
    // ========================================
    try {
        console.log("[*] Checking for LIAPP protection library...");

        // LIAPP main class
        try {
            var CheckFile = Java.use("com.liapp.checkfile.CheckFile");
            console.log("[!] LIAPP DETECTED: com.liapp.checkfile.CheckFile found");
            findings.liapp = true;
        } catch (e) {}

        // LIAPP verification interface
        try {
            var LiappInterface = Java.use("com.liapp.interfaces.a");
            console.log("[!] LIAPP DETECTED: Liapp interface found");
            findings.liapp = true;
        } catch (e) {}

        // LIAPP process validation
        try {
            var ProcessCheck = Java.use("com.liapp.process.ProcessCheck");
            console.log("[!] LIAPP DETECTED: Process check class found");
            findings.liapp = true;
        } catch (e) {}

    } catch (e) {
        console.log("[-] LIAPP detection error: " + e.getMessage());
    }

    // ========================================
    // Detection 2: System.exit() Interception
    // ========================================
    try {
        console.log("[*] Hooking System.exit() for detection...");

        var System = Java.use("java.lang.System");
        var exitMethod = System.exit.overload('I');
        var exitCount = 0;

        var originalExit = exitMethod.implementation;
        exitMethod.implementation = function(code) {
            exitCount++;
            console.log("[!!!] System.exit(" + code + ") called! Count: " + exitCount);

            // Print stack trace to identify caller
            var Exception = Java.use("java.lang.Exception");
            var e = Exception.$new("System.exit caller");
            var sw = Java.use("java.io.StringWriter").$new();
            var pw = Java.use("java.io.PrintWriter").$new(sw);
            e.printStackTrace(pw);
            console.log("[STACK] " + sw.toString());

            findings.systemExit = true;
            return originalExit.call(this, code);
        };

        console.log("[+] System.exit() hooked");

    } catch (e) {
        console.log("[-] System.exit hook error: " + e.getMessage());
    }

    // ========================================
    // Detection 3: InputEvent Source Validation
    // ========================================
    try {
        console.log("[*] Checking for input event validation...");

        var MotionEvent = Java.use("android.view.MotionEvent");
        var getSource = MotionEvent.getSource.overload();

        var sourceCheckCount = 0;
        var sourcesDetected = {};

        var originalGetSource = getSource.implementation;
        getSource.implementation = function() {
            var source = originalGetSource.call(this);
            sourceCheckCount++;
            sourcesDetected[source] = (sourcesDetected[source] || 0) + 1;

            if (sourceCheckCount <= 5) {
                console.log("[INPUT] MotionEvent.getSource() = 0x" + source.toString(16) + " (INPUTDEVICE_SOURCE_TOUCHSCREEN: 0x1002)");
            }

            return source;
        };

        if (sourceCheckCount > 0) {
            findings.inputValidation = true;
        }

        console.log("[+] Input validation monitoring active");

    } catch (e) {
        console.log("[-] Input validation hook error: " + e.getMessage());
    }

    // ========================================
    // Detection 4: Process/Activity Monitoring
    // ========================================
    try {
        console.log("[*] Checking for process monitoring...");

        var ActivityManager = Java.use("android.app.ActivityManager");
        var getRunningServices = ActivityManager.getRunningServices.overload('I');

        var callCount = 0;
        var originalGetRunningServices = getRunningServices.implementation;

        getRunningServices.implementation = function(maxNum) {
            callCount++;
            if (callCount <= 3) {
                console.log("[PROCESS] getRunningServices(" + maxNum + ") called");
            }
            findings.processMonitoring = true;
            return originalGetRunningServices.call(this, maxNum);
        };

        console.log("[+] Process monitoring hook active");

    } catch (e) {
        console.log("[-] Process monitoring hook error: " + e.getMessage());
    }

    // ========================================
    // Detection 5: Debug Detection
    // ========================================
    try {
        console.log("[*] Checking for debug detection...");

        var Debug = Java.use("android.os.Debug");
        var isDebuggerConnected = Debug.isDebuggerConnected.overload();

        var debugCheckCount = 0;
        var originalIsDebuggerConnected = isDebuggerConnected.implementation;

        isDebuggerConnected.implementation = function() {
            var result = originalIsDebuggerConnected.call(this);
            debugCheckCount++;
            if (debugCheckCount <= 3) {
                console.log("[DEBUG] isDebuggerConnected() = " + result);
            }
            if (result === true) {
                findings.debugDetection = true;
                console.log("[!] DEBUG DETECTION: Debugger check detected!");
            }
            return result;
        };

        console.log("[+] Debug detection monitoring active");

    } catch (e) {
        console.log("[-] Debug detection hook error: " + e.getMessage());
    }

    // ========================================
    // Detection 6: View Click Interception
    // ========================================
    try {
        console.log("[*] Checking for click interception...");

        var View = Java.use("android.view.View");
        var performClick = View.performClick.overload();

        var clickCount = 0;
        var originalPerformClick = performClick.implementation;

        performClick.implementation = function() {
            clickCount++;
            if (clickCount <= 5) {
                var viewClass = this.getClass().getSimpleName();
                var viewId = this.getId();
                console.log("[CLICK] View.performClick() #" + clickCount + ": " + viewClass + " (ID: " + viewId + ")");
            }

            try {
                var result = originalPerformClick.call(this);
                if (clickCount <= 5) {
                    console.log("[CLICK] Click processed successfully");
                }
                return result;
            } catch (e) {
                console.log("[ERROR] Click processing failed: " + e.getMessage());
                throw e;
            }
        };

        console.log("[+] Click interception monitoring active");

    } catch (e) {
        console.log("[-] Click interception hook error: " + e.getMessage());
    }

    // ========================================
    // Summary Report
    // ========================================
    console.log("\n" + "=".repeat(50));
    console.log("PROTECTION DETECTION SUMMARY");
    console.log("=".repeat(50));

    var detectedCount = 0;
    if (findings.liapp) {
        console.log("[!] LIAPP Protection: DETECTED");
        detectedCount++;
    } else {
        console.log("[-] LIAPP Protection: NOT detected");
    }

    if (findings.systemExit) {
        console.log("[!] System.exit() Usage: DETECTED");
        detectedCount++;
    } else {
        console.log("[-] System.exit() Usage: NOT detected");
    }

    if (findings.inputValidation) {
        console.log("[!] Input Event Validation: DETECTED");
        detectedCount++;
    } else {
        console.log("[-] Input Event Validation: NOT detected");
    }

    if (findings.processMonitoring) {
        console.log("[!] Process Monitoring: DETECTED");
        detectedCount++;
    } else {
        console.log("[-] Process Monitoring: NOT detected");
    }

    if (findings.debugDetection) {
        console.log("[!] Debug Detection: DETECTED");
        detectedCount++;
    } else {
        console.log("[-] Debug Detection: NOT detected");
    }

    console.log("\n[*] Total protection mechanisms detected: " + detectedCount);

    if (detectedCount === 0) {
        console.log("[+] No obvious protection mechanisms detected");
        console.log("[*] App may use custom detection logic");
    }

    console.log("=".repeat(50));
    console.log("[+] Detection hook ready. Waiting for app interaction...");
    console.log("[+] Try clicking buttons in the app and watch console for logs");

});
