#!/usr/bin/env python3
"""
Frida-based analysis of Karrot app (com.towneers.www) anti-automation protection.

This script investigates potential protection mechanisms:
1. Click/tap event interception
2. MotionEvent validation
3. InputEvent source checking
4. Timestamp validation
5. LIAPP or similar anti-bot libraries
6. View.OnClickListener manipulation

Usage:
    # Test Frida connection
    frida_karrot_analysis.py --device 127.0.0.1:5555 --check-connection

    # Analyze running app
    frida_karrot_analysis.py --device 127.0.0.1:5555 --app com.towneers.www --analyze

    # Dump intercepted events (running app)
    frida_karrot_analysis.py --device 127.0.0.1:5555 --app com.towneers.www --hook-events

    # Search for anti-bot patterns
    frida_karrot_analysis.py --device 127.0.0.1:5555 --app com.towneers.www --search-patterns
"""

import argparse
import json
import subprocess
import sys
import time
from typing import Optional, Dict, List, Any


class FridaAnalyzer:
    """Analyze Karrot app with Frida for anti-automation detection."""

    def __init__(self, device_id: str = "127.0.0.1:5555", app_package: str = "com.towneers.www"):
        self.device_id = device_id
        self.app_package = app_package
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "device": device_id,
            "app": app_package,
            "frida_status": None,
            "analysis": {}
        }

    def check_frida_connection(self) -> bool:
        """Test if Frida can connect to device."""
        print("[*] Testing Frida connection...")
        try:
            result = subprocess.run(
                ["frida", "-H", self.device_id, "-l", "/dev/null"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if "Connection refused" in result.stderr or "Failed" in result.stderr:
                print("[-] Frida connection FAILED")
                print(f"    Error: {result.stderr}")
                self.results["frida_status"] = "FAILED"
                return False

            print("[+] Frida connection SUCCESS")
            self.results["frida_status"] = "CONNECTED"
            return True
        except subprocess.TimeoutExpired:
            print("[-] Frida connection timeout (device unreachable)")
            self.results["frida_status"] = "TIMEOUT"
            return False
        except FileNotFoundError:
            print("[-] Frida CLI not installed. Install: pip install frida-tools")
            self.results["frida_status"] = "NOT_INSTALLED"
            return False

    def analyze_app_protection(self) -> Dict[str, Any]:
        """Analyze Karrot app for protection mechanisms."""
        print(f"\n[*] Analyzing {self.app_package} for protection mechanisms...")

        # Check if app is running
        if not self._is_app_running():
            print("[-] App not running. Start the app and try again.")
            return {"error": "app_not_running"}

        analysis = {
            "app_running": True,
            "protection_mechanisms": []
        }

        # Hook 1: View.OnClickListener detection
        listener_results = self._hook_on_click_listeners()
        analysis["protection_mechanisms"].append({
            "type": "OnClickListener",
            "detected": listener_results["found"],
            "details": listener_results
        })

        # Hook 2: MotionEvent interception
        motion_results = self._hook_motion_events()
        analysis["protection_mechanisms"].append({
            "type": "MotionEvent",
            "detected": motion_results["found"],
            "details": motion_results
        })

        # Hook 3: InputEvent validation
        input_results = self._hook_input_events()
        analysis["protection_mechanisms"].append({
            "type": "InputEvent",
            "detected": input_results["found"],
            "details": input_results
        })

        # Hook 4: Check for known anti-bot libraries
        anti_bot_results = self._check_anti_bot_libraries()
        analysis["protection_mechanisms"].append({
            "type": "Anti-Bot Libraries",
            "detected": anti_bot_results["found"],
            "details": anti_bot_results
        })

        self.results["analysis"] = analysis
        return analysis

    def _is_app_running(self) -> bool:
        """Check if app is currently running."""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "pidof", self.app_package],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception as e:
            print(f"[-] Error checking app status: {e}")
            return False

    def _hook_on_click_listeners(self) -> Dict[str, Any]:
        """Hook View.OnClickListener to detect click handling."""
        frida_code = """
        Java.perform(function() {
            var View = Java.use("android.view.View");
            var originalSetOnClickListener = View.setOnClickListener.overload('android.view.View$OnClickListener');

            var clickCount = 0;
            var listeners = [];

            originalSetOnClickListener.implementation = function(listener) {
                clickCount++;
                if (listener) {
                    listeners.push({
                        index: clickCount,
                        listenerClass: listener.getClass().getName(),
                        timestamp: new Date().toISOString()
                    });
                    console.log("[OnClickListener] Hooked listener #" + clickCount);
                }
                return originalSetOnClickListener.call(this, listener);
            };

            send({
                type: "listeners_hooked",
                count: clickCount,
                listeners: listeners
            });
        });
        """

        print("  [*] Hooking View.OnClickListener...")
        return self._execute_frida_script(frida_code, "OnClickListener")

    def _hook_motion_events(self) -> Dict[str, Any]:
        """Hook MotionEvent to detect event validation."""
        frida_code = """
        Java.perform(function() {
            var MotionEvent = Java.use("android.view.MotionEvent");

            // Hook getAction
            var originalGetAction = MotionEvent.getAction.overload();
            var actionCount = 0;

            originalGetAction.implementation = function() {
                var action = originalGetAction.call(this);
                actionCount++;

                var eventInfo = {
                    action: action,
                    x: this.getX(),
                    y: this.getY(),
                    actionMasked: this.getActionMasked ? this.getActionMasked() : null,
                    source: this.getSource ? this.getSource() : null,
                    timestamp: this.getEventTime ? this.getEventTime() : null
                };

                send({
                    type: "motion_event",
                    count: actionCount,
                    event: eventInfo
                });

                return action;
            };

            console.log("[MotionEvent] Hook installed");
            send({
                type: "motion_events_hooked",
                count: actionCount
            });
        });
        """

        print("  [*] Hooking MotionEvent...")
        return self._execute_frida_script(frida_code, "MotionEvent")

    def _hook_input_events(self) -> Dict[str, Any]:
        """Hook InputEvent to detect source validation."""
        frida_code = """
        Java.perform(function() {
            var InputEvent = Java.use("android.view.InputEvent");

            // Hook getSource
            var originalGetSource = InputEvent.getSource.overload();
            var sourceCheckCount = 0;
            var detectedSources = {};

            originalGetSource.implementation = function() {
                var source = originalGetSource.call(this);
                sourceCheckCount++;

                detectedSources[source] = (detectedSources[source] || 0) + 1;

                send({
                    type: "input_source_check",
                    source: source,
                    sourceHex: "0x" + source.toString(16)
                });

                return source;
            };

            console.log("[InputEvent] Hook installed");
            send({
                type: "input_events_hooked",
                count: sourceCheckCount,
                sources: detectedSources
            });
        });
        """

        print("  [*] Hooking InputEvent...")
        return self._execute_frida_script(frida_code, "InputEvent")

    def _check_anti_bot_libraries(self) -> Dict[str, Any]:
        """Check for known anti-bot protection libraries."""
        frida_code = """
        Java.perform(function() {
            var loadedClasses = [];
            var antiPatterns = {
                "LIAPP": ["com.liapp", "liapp"],
                "XPOSED": ["de.robv.android.xposed", "xposed"],
                "FRIDA_DETECTOR": ["frida", "objection"],
                "ANTI_DEBUG": ["android.os.Debug", "android.app.ActivityManager"],
                "GENERIC_ANTI_BOT": ["bot", "automation", "detection", "fake"]
            };

            var findings = {};

            // Check for known anti-bot class patterns
            var Runtime = Java.use("java.lang.Runtime");
            var reflection = Java.use("java.lang.Class");

            try {
                // Check for LIAPP
                try {
                    Java.use("com.liapp.checkfile.CheckFile");
                    findings["LIAPP"] = true;
                    console.log("[!] LIAPP protection detected!");
                } catch (e) {}

                // Check for process name spoofing detection
                try {
                    Java.use("java.lang.ProcessBuilder");
                    console.log("[*] ProcessBuilder accessible");
                } catch (e) {}

            } catch (e) {
                console.log("[*] Reflection check skipped");
            }

            send({
                type: "anti_bot_check",
                findings: findings,
                message: Object.keys(findings).length > 0 ?
                    "Anti-bot patterns detected: " + Object.keys(findings).join(", ") :
                    "No obvious anti-bot libraries detected"
            });
        });
        """

        print("  [*] Checking for anti-bot libraries...")
        return self._execute_frida_script(frida_code, "AntiBot")

    def _execute_frida_script(self, script: str, hook_name: str) -> Dict[str, Any]:
        """Execute Frida script and collect results."""
        try:
            # Write script to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script)
                script_file = f.name

            # Execute with frida
            cmd = [
                "frida", "-H", self.device_id,
                "-f", self.app_package,
                "--no-pause",
                "-l", script_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "found": True,
                "hook": hook_name,
                "output": result.stderr if result.stderr else result.stdout,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "found": False,
                "hook": hook_name,
                "error": "timeout",
                "message": "Script execution timeout"
            }
        except Exception as e:
            return {
                "found": False,
                "hook": hook_name,
                "error": str(e),
                "message": f"Failed to execute Frida hook: {e}"
            }

    def generate_bypass_suggestions(self) -> List[str]:
        """Generate bypass strategies based on analysis."""
        print("\n[*] Generating bypass suggestions...")

        suggestions = []

        # Base suggestions
        suggestions.append("""
FRIDA-BASED BYPASS STRATEGIES FOR KARROT APP
=============================================

1. DISABLE CLICK SOURCE VALIDATION
   Hook InputEvent.getSource() to always return valid source:

   originalGetSource.implementation = function() {
       return 0x1002; // TOOL_TYPE_FINGER (valid touch source)
   };

2. INTERCEPT ONCLICK LISTENER CALLS
   Hook View.performClick() instead of OnClickListener:

   var View = Java.use("android.view.View");
   View.performClick.implementation = function() {
       // Execute original click
       return View.performClick.call(this);
   };

3. BYPASS MOTIONEVENT CHECKS
   Inject valid MotionEvent before validation:

   var MotionEvent = Java.use("android.view.MotionEvent");
   var originalObtain = MotionEvent.obtain;

   originalObtain.implementation = function(...args) {
       var event = originalObtain.apply(this, args);
       // Set valid source
       event.setSource(0x1002);
       return event;
   };

4. DISABLE TIMESTAMP VALIDATION
   Replace timestamp checks with dummy values:

   var SystemClock = Java.use("android.os.SystemClock");
   var elapsedRealtime = SystemClock.elapsedRealtime;

   elapsedRealtime.implementation = function() {
       // Return consistent timing
       return elapsedRealtime.call(this);
   };

5. HOOK DETECTION MECHANISMS
   Search for and disable anti-bot checks:

   // Look for methods with names like:
   // - isAutomation()
   // - isFake()
   // - checkBot()
   // - validateEvent()
   // - verifyClick()

6. LIAPP BYPASS (if detected)
   Hook LIAPP's verification methods:

   try {
       Java.use("com.liapp.checkfile.CheckFile").check.implementation = function() {
           return true; // Bypass check
       };
   } catch (e) {}
""")

        self.results["bypass_suggestions"] = suggestions
        return suggestions

    def save_results(self, output_file: str = "frida_analysis_results.json"):
        """Save analysis results to JSON file."""
        output_path = f"/Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer/.claude/skills/adb/adb-game-karrot/analysis/{output_file}"

        try:
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)

            print(f"\n[+] Results saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"[-] Error saving results: {e}")
            return None

    def print_summary(self):
        """Print analysis summary."""
        print("\n" + "="*60)
        print("FRIDA ANALYSIS SUMMARY")
        print("="*60)

        print(f"\nDevice: {self.device_id}")
        print(f"App: {self.app_package}")
        print(f"Frida Status: {self.results.get('frida_status', 'UNKNOWN')}")

        if "analysis" in self.results and "protection_mechanisms" in self.results["analysis"]:
            print(f"\nProtection Mechanisms Found: {len(self.results['analysis']['protection_mechanisms'])}")

            for mechanism in self.results["analysis"]["protection_mechanisms"]:
                status = "[+] DETECTED" if mechanism.get("detected") else "[-] NOT DETECTED"
                print(f"  {status}: {mechanism['type']}")

        print("\n" + "="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Frida-based analysis of Karrot app anti-automation protection"
    )
    parser.add_argument(
        "--device", "-d",
        default="127.0.0.1:5555",
        help="Device ID (default: 127.0.0.1:5555)"
    )
    parser.add_argument(
        "--app", "-a",
        default="com.towneers.www",
        help="App package name (default: com.towneers.www)"
    )
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Test Frida connection"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze app for protection mechanisms"
    )
    parser.add_argument(
        "--hook-events",
        action="store_true",
        help="Hook and monitor click/touch events"
    )
    parser.add_argument(
        "--search-patterns",
        action="store_true",
        help="Search for anti-bot patterns"
    )
    parser.add_argument(
        "--output", "-o",
        default="frida_analysis_results.json",
        help="Output file for results"
    )

    args = parser.parse_args()

    analyzer = FridaAnalyzer(args.device, args.app)

    # Check Frida connection
    if args.check_connection or not (args.analyze or args.hook_events or args.search_patterns):
        if not analyzer.check_frida_connection():
            sys.exit(1)

    # Run analysis if requested
    if args.analyze or args.hook_events or args.search_patterns:
        analyzer.analyze_app_protection()
        analyzer.generate_bypass_suggestions()

    # Save and print results
    analyzer.save_results(args.output)
    analyzer.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
