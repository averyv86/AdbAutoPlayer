#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Karrot App Crash Monitor with Auto-Recovery

Monitors com.towneers.www app for crashes and automatically recovers.

Features:
- Real-time logcat monitoring for crash patterns
- Package focus monitoring every 1 second
- Immediate crash detection (within 500ms)
- Auto-recovery with exponential backoff
- Status tracking and crash logging
- Daemon mode support
- PID file management

Usage:
    uv run karrot_monitor.py --start          # Start monitoring
    uv run karrot_monitor.py --stop           # Stop monitoring
    uv run karrot_monitor.py --status         # Show status
    uv run karrot_monitor.py --daemon         # Run as daemon
    uv run karrot_monitor.py --on-crash relaunch  # Action on crash
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Literal, Optional

# Constants
KARROT_PACKAGE = "com.towneers.www"
ALERT_PACKAGES = [
    "com.android.vending",  # Google Play Store
    "com.uncube.launcher3",  # Launcher
    "com.google.android.gms",  # Google Play Services
]

# File paths
PID_FILE = Path("/tmp/karrot-monitor.pid")
STATUS_FILE = Path("/tmp/karrot-monitor-status.json")
CRASH_LOG_FILE = Path("/tmp/karrot-crash-log.json")

# Crash detection patterns
CRASH_PATTERNS = [
    r"FATAL EXCEPTION",
    r"Process: com\.towneers\.www",
    r"java\.lang\.RuntimeException",
    r"ANR in com\.towneers\.www",
    r"ActivityManager: Force finishing activity.*com\.towneers\.www",
    r"AndroidRuntime.*com\.towneers\.www",
]

# Recovery configuration
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_BACKOFF_BASE = 2.0  # seconds
RECOVERY_BACKOFF_MULTIPLIER = 2.0


@dataclass
class MonitorStatus:
    """Monitor status data structure."""

    is_running: bool
    started_at: Optional[str]
    last_crash_time: Optional[str]
    crash_count: int
    recovery_count: int
    recovery_success_count: int
    recovery_failure_count: int
    current_recovery_attempts: int
    pid: Optional[int]


@dataclass
class CrashEvent:
    """Crash event data structure."""

    timestamp: str
    crash_type: str
    crash_details: str
    logcat_lines: list[str]
    recovery_attempted: bool
    recovery_success: bool


class KarrotMonitor:
    """Main monitor class for Karrot app."""

    def __init__(self, action_on_crash: Literal["relaunch", "notify", "none"] = "relaunch"):
        self.action_on_crash = action_on_crash
        self.status = self._load_status()
        self.crash_events: list[CrashEvent] = self._load_crash_log()
        self.stop_event = Event()
        self.logcat_process: Optional[subprocess.Popen] = None
        self.focus_monitor_thread: Optional[Thread] = None

    def _load_status(self) -> MonitorStatus:
        """Load status from file or create default."""
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE) as f:
                    data = json.load(f)
                return MonitorStatus(**data)
            except Exception:
                pass

        return MonitorStatus(
            is_running=False,
            started_at=None,
            last_crash_time=None,
            crash_count=0,
            recovery_count=0,
            recovery_success_count=0,
            recovery_failure_count=0,
            current_recovery_attempts=0,
            pid=None,
        )

    def _save_status(self):
        """Save current status to file."""
        with open(STATUS_FILE, "w") as f:
            json.dump(asdict(self.status), f, indent=2)

    def _load_crash_log(self) -> list[CrashEvent]:
        """Load crash log from file."""
        if CRASH_LOG_FILE.exists():
            try:
                with open(CRASH_LOG_FILE) as f:
                    data = json.load(f)
                return [CrashEvent(**event) for event in data]
            except Exception:
                pass
        return []

    def _save_crash_log(self):
        """Save crash log to file."""
        with open(CRASH_LOG_FILE, "w") as f:
            json.dump([asdict(event) for event in self.crash_events], f, indent=2)

    def _write_pid_file(self):
        """Write current PID to file."""
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid_file(self):
        """Remove PID file."""
        if PID_FILE.exists():
            PID_FILE.unlink()

    def _get_current_focus(self) -> Optional[str]:
        """Get currently focused package."""
        try:
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "window", "windows"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0:
                # Find mCurrentFocus or mFocusedApp
                for line in result.stdout.splitlines():
                    if "mCurrentFocus" in line or "mFocusedApp" in line:
                        # Extract package name
                        match = re.search(r"([a-z0-9.]+)/", line)
                        if match:
                            return match.group(1)
        except Exception as e:
            print(f"Error getting current focus: {e}", file=sys.stderr)

        return None

    def _is_crash_pattern(self, line: str) -> bool:
        """Check if line matches crash pattern."""
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in CRASH_PATTERNS)

    def _detect_crash_type(self, lines: list[str]) -> str:
        """Detect crash type from logcat lines."""
        text = "\n".join(lines)

        if "FATAL EXCEPTION" in text:
            return "FATAL_EXCEPTION"
        elif "ANR" in text:
            return "ANR"
        elif "Force finishing activity" in text:
            return "ACTIVITY_CRASH"
        elif "RuntimeException" in text:
            return "RUNTIME_EXCEPTION"
        else:
            return "UNKNOWN_CRASH"

    def _force_stop_interfering_apps(self):
        """Force stop apps that might interfere."""
        for package in ALERT_PACKAGES:
            try:
                subprocess.run(
                    ["adb", "shell", "am", "force-stop", package],
                    capture_output=True,
                    timeout=3,
                )
                print(f"Force stopped: {package}")
            except Exception as e:
                print(f"Failed to stop {package}: {e}", file=sys.stderr)

    def _launch_karrot(self) -> bool:
        """Launch Karrot app."""
        try:
            # Launch main activity
            result = subprocess.run(
                [
                    "adb",
                    "shell",
                    "am",
                    "start",
                    "-n",
                    f"{KARROT_PACKAGE}/com.towneers.www.MainActivity",
                ],
                capture_output=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("Karrot app launched successfully")
                return True
            else:
                print(f"Failed to launch Karrot: {result.stderr.decode()}", file=sys.stderr)
                return False

        except Exception as e:
            print(f"Error launching Karrot: {e}", file=sys.stderr)
            return False

    def _attempt_recovery(self, crash_event: CrashEvent) -> bool:
        """Attempt to recover from crash with exponential backoff."""
        for attempt in range(1, MAX_RECOVERY_ATTEMPTS + 1):
            print(f"\n🔄 Recovery attempt {attempt}/{MAX_RECOVERY_ATTEMPTS}")

            # Force stop interfering apps
            self._force_stop_interfering_apps()

            # Wait with exponential backoff
            backoff_time = RECOVERY_BACKOFF_BASE * (RECOVERY_BACKOFF_MULTIPLIER ** (attempt - 1))
            print(f"Waiting {backoff_time:.1f}s before relaunch...")
            time.sleep(backoff_time)

            # Relaunch Karrot
            if self._launch_karrot():
                # Wait to verify app stability
                time.sleep(3)

                # Check if app is still running
                current_focus = self._get_current_focus()
                if current_focus == KARROT_PACKAGE:
                    print("✅ Recovery successful - Karrot is running")
                    crash_event.recovery_success = True
                    self.status.recovery_success_count += 1
                    self.status.current_recovery_attempts = 0
                    return True
                else:
                    print(f"⚠️  App launched but focus is on: {current_focus}")
            else:
                print(f"❌ Recovery attempt {attempt} failed")

            self.status.current_recovery_attempts = attempt

        # All recovery attempts failed
        print(f"❌ All {MAX_RECOVERY_ATTEMPTS} recovery attempts failed")
        crash_event.recovery_success = False
        self.status.recovery_failure_count += 1
        self.status.current_recovery_attempts = 0
        return False

    def _handle_crash(self, crash_lines: list[str]):
        """Handle detected crash."""
        timestamp = datetime.now().isoformat()
        crash_type = self._detect_crash_type(crash_lines)

        print(f"\n🚨 CRASH DETECTED: {crash_type} at {timestamp}")
        print("Crash details:")
        for line in crash_lines[:5]:  # Show first 5 lines
            print(f"  {line}")

        # Create crash event
        crash_event = CrashEvent(
            timestamp=timestamp,
            crash_type=crash_type,
            crash_details="\n".join(crash_lines[:10]),
            logcat_lines=crash_lines,
            recovery_attempted=False,
            recovery_success=False,
        )

        # Update status
        self.status.crash_count += 1
        self.status.last_crash_time = timestamp

        # Perform recovery action
        if self.action_on_crash == "relaunch":
            crash_event.recovery_attempted = True
            self.status.recovery_count += 1

            recovery_success = self._attempt_recovery(crash_event)

            if recovery_success:
                print("✅ Auto-recovery completed successfully")
            else:
                print("❌ Auto-recovery failed")

        elif self.action_on_crash == "notify":
            print("📢 Notification mode - no auto-recovery")

        # Save crash event and status
        self.crash_events.append(crash_event)
        self._save_crash_log()
        self._save_status()

    def _monitor_logcat(self):
        """Monitor logcat for crash patterns."""
        print("Starting logcat monitor...")

        # Clear logcat buffer
        subprocess.run(["adb", "logcat", "-c"], capture_output=True)

        # Start logcat process
        self.logcat_process = subprocess.Popen(
            ["adb", "logcat", "-v", "time"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        crash_buffer: list[str] = []
        in_crash_sequence = False

        try:
            assert self.logcat_process.stdout is not None

            for line in self.logcat_process.stdout:
                if self.stop_event.is_set():
                    break

                line = line.strip()
                if not line:
                    continue

                # Check for crash pattern
                if self._is_crash_pattern(line):
                    if not in_crash_sequence:
                        in_crash_sequence = True
                        crash_buffer = [line]
                    else:
                        crash_buffer.append(line)

                    # Check if crash sequence is complete (no new crash lines for 500ms)
                    if len(crash_buffer) >= 3:
                        self._handle_crash(crash_buffer)
                        crash_buffer = []
                        in_crash_sequence = False

                elif in_crash_sequence:
                    # Continue collecting crash lines
                    if KARROT_PACKAGE in line or any(
                        keyword in line for keyword in ["Exception", "Error", "Crash", "ANR"]
                    ):
                        crash_buffer.append(line)
                    else:
                        # End of crash sequence
                        if len(crash_buffer) >= 3:
                            self._handle_crash(crash_buffer)
                        crash_buffer = []
                        in_crash_sequence = False

        except Exception as e:
            print(f"Error in logcat monitor: {e}", file=sys.stderr)

        finally:
            if self.logcat_process:
                self.logcat_process.terminate()
                self.logcat_process.wait()

    def _monitor_focus(self):
        """Monitor package focus every 1 second."""
        print("Starting focus monitor...")

        while not self.stop_event.is_set():
            try:
                current_focus = self._get_current_focus()

                if current_focus and current_focus in ALERT_PACKAGES:
                    print(f"⚠️  Alert package detected: {current_focus}")

                    if self.action_on_crash == "relaunch":
                        print("Force stopping alert package...")
                        self._force_stop_interfering_apps()

                        # Relaunch Karrot
                        time.sleep(1)
                        self._launch_karrot()

            except Exception as e:
                print(f"Error in focus monitor: {e}", file=sys.stderr)

            time.sleep(1)

    def start(self):
        """Start monitoring."""
        print(f"🚀 Starting Karrot monitor (action on crash: {self.action_on_crash})")

        # Update status
        self.status.is_running = True
        self.status.started_at = datetime.now().isoformat()
        self.status.pid = os.getpid()
        self._save_status()
        self._write_pid_file()

        # Start logcat monitor thread
        logcat_thread = Thread(target=self._monitor_logcat, daemon=True)
        logcat_thread.start()

        # Start focus monitor thread
        self.focus_monitor_thread = Thread(target=self._monitor_focus, daemon=True)
        self.focus_monitor_thread.start()

        print("✅ Monitor started successfully")
        print(f"PID: {os.getpid()}")
        print(f"Status file: {STATUS_FILE}")
        print(f"Crash log: {CRASH_LOG_FILE}")
        print("\nPress Ctrl+C to stop monitoring...\n")

        try:
            # Keep main thread alive
            while not self.stop_event.is_set():
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping monitor...")

        finally:
            self.stop()

    def stop(self):
        """Stop monitoring."""
        print("Stopping monitor...")

        self.stop_event.set()

        # Stop logcat process
        if self.logcat_process:
            self.logcat_process.terminate()
            self.logcat_process.wait()

        # Wait for threads
        if self.focus_monitor_thread:
            self.focus_monitor_thread.join(timeout=2)

        # Update status
        self.status.is_running = False
        self.status.pid = None
        self._save_status()
        self._remove_pid_file()

        print("✅ Monitor stopped")

    def show_status(self):
        """Show current status."""
        print("\n📊 Karrot Monitor Status")
        print("=" * 50)
        print(f"Running:              {self.status.is_running}")
        print(f"PID:                  {self.status.pid or 'N/A'}")
        print(f"Started at:           {self.status.started_at or 'N/A'}")
        print(f"Last crash:           {self.status.last_crash_time or 'Never'}")
        print(f"Total crashes:        {self.status.crash_count}")
        print(f"Recovery attempts:    {self.status.recovery_count}")
        print(f"Recovery successes:   {self.status.recovery_success_count}")
        print(f"Recovery failures:    {self.status.recovery_failure_count}")
        print(f"Current attempts:     {self.status.current_recovery_attempts}")
        print("=" * 50)

        if self.crash_events:
            print(f"\n📝 Recent crashes ({len(self.crash_events)}):")
            for event in self.crash_events[-5:]:
                print(f"  • {event.timestamp}: {event.crash_type}")
                print(f"    Recovery: {'✅ Success' if event.recovery_success else '❌ Failed'}")
        else:
            print("\n✅ No crashes detected")


def stop_existing_monitor():
    """Stop existing monitor process."""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())

            print(f"Stopping existing monitor (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)

            # Check if process is still running
            try:
                os.kill(pid, 0)
                print("Process still running, sending SIGKILL...")
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

            PID_FILE.unlink()
            print("✅ Existing monitor stopped")

        except Exception as e:
            print(f"Failed to stop existing monitor: {e}", file=sys.stderr)
            if PID_FILE.exists():
                PID_FILE.unlink()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Karrot App Crash Monitor")
    parser.add_argument(
        "--start", action="store_true", help="Start monitoring (foreground)"
    )
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (background)")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument(
        "--on-crash",
        choices=["relaunch", "notify", "none"],
        default="relaunch",
        help="Action to take on crash (default: relaunch)",
    )

    args = parser.parse_args()

    # Show status
    if args.status:
        monitor = KarrotMonitor()
        monitor.show_status()
        return

    # Stop monitor
    if args.stop:
        stop_existing_monitor()
        return

    # Start monitor
    if args.start or args.daemon:
        # Stop existing monitor first
        stop_existing_monitor()

        monitor = KarrotMonitor(action_on_crash=args.on_crash)

        if args.daemon:
            print("Starting monitor in daemon mode...")
            # Fork to background
            pid = os.fork()
            if pid > 0:
                print(f"✅ Monitor started in background (PID: {pid})")
                sys.exit(0)

            # Child process continues
            os.setsid()
            monitor.start()
        else:
            monitor.start()

        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
