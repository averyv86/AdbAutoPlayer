#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///

"""
Karrot Automation Crash Monitor
================================

Continuous monitoring and auto-recovery for com.towneers.www automation.

Features:
- Background monitoring with 2-second polling
- Detects crashes via FallbackHome or null focused app
- Auto-recovery: force-stop + monkey restart + 10s wait
- Crash logging with timestamp and logcat snippets
- Integration API: check_and_recover() for flow runner
- Daemon mode: standalone background process with watchdog

Usage:
    # Standalone daemon mode
    uv run karrot_crash_monitor.py --daemon

    # Integration with flow runner
    from karrot_crash_monitor import check_and_recover

    if not check_and_recover():
        print("Recovery was needed")

Author: MoAI-ADK
Version: 1.0.0
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

# ============================================================================
# Configuration
# ============================================================================

KARROT_PACKAGE = "com.towneers.www"
POLL_INTERVAL = 2  # seconds
RESTART_WAIT = 10  # seconds after restart
FORCE_STOP_WAIT = 2  # seconds after force stop
CRASH_LOG_PATH = "/tmp/karrot_crashes.log"
LOGCAT_LINES = 100  # lines to capture on crash

# Crash indicators
CRASH_INDICATORS = [
    "com.android.launcher3.fallback.FallbackHome",  # Fallback launcher
    "null",  # Null focused app
    "",  # Empty string (no app)
]


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class AppState:
    """Current state of Karrot app"""
    is_running: bool
    is_foreground: bool
    focused_app: Optional[str]
    crashed: bool
    timestamp: datetime


# ============================================================================
# ADB Interface
# ============================================================================

def run_adb_command(command: list[str], timeout: int = 5) -> tuple[bool, str]:
    """
    Execute ADB command and return success status + output.

    Args:
        command: ADB command as list (e.g., ["adb", "shell", "dumpsys", "window"])
        timeout: Command timeout in seconds

    Returns:
        (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.error(f"ADB command timed out: {' '.join(command)}")
        return False, ""
    except FileNotFoundError:
        logging.error("ADB not found. Please install Android SDK platform-tools.")
        return False, ""
    except Exception as e:
        logging.error(f"ADB command failed: {e}")
        return False, ""


def get_focused_app() -> Optional[str]:
    """
    Get currently focused app package name.

    Returns:
        Package name or None if detection failed
    """
    success, output = run_adb_command(["adb", "shell", "dumpsys", "window", "windows"])

    if not success:
        return None

    # Parse dumpsys output for mCurrentFocus
    for line in output.split("\n"):
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            # Extract package name from patterns like:
            # mCurrentFocus=Window{abc u0 com.towneers.www/...}
            # mFocusedApp=AppWindowToken{abc token=Token{xyz ActivityRecord{123 u0 com.towneers.www/...}}}
            parts = line.split()
            for part in parts:
                if "/" in part and ("." in part or "com." in part):
                    # Extract package from "com.towneers.www/..." or "com.towneers.www}"
                    package = part.split("/")[0].split("{")[-1].strip()
                    return package

    return None


def is_app_running(package: str) -> bool:
    """
    Check if app process is running.

    Args:
        package: App package name

    Returns:
        True if running, False otherwise
    """
    success, output = run_adb_command(["adb", "shell", "pidof", package])
    return success and output.strip() != ""


def force_stop_app(package: str) -> bool:
    """
    Force stop app.

    Args:
        package: App package name

    Returns:
        True if successful, False otherwise
    """
    success, _ = run_adb_command(["adb", "shell", "am", "force-stop", package])
    return success


def start_app_with_monkey(package: str) -> bool:
    """
    Start app using monkey command.

    Args:
        package: App package name

    Returns:
        True if successful, False otherwise
    """
    success, _ = run_adb_command(["adb", "shell", "monkey", "-p", package, "1"])
    return success


def capture_logcat(lines: int = 100) -> str:
    """
    Capture recent logcat entries.

    Args:
        lines: Number of lines to capture

    Returns:
        Logcat output as string
    """
    success, output = run_adb_command(["adb", "logcat", "-d", "-t", str(lines)])
    return output if success else "(Failed to capture logcat)"


# ============================================================================
# State Detection
# ============================================================================

def detect_app_state() -> AppState:
    """
    Detect current Karrot app state.

    Returns:
        AppState object with current status
    """
    timestamp = datetime.now()
    focused_app = get_focused_app()
    is_running = is_app_running(KARROT_PACKAGE)

    # Check if app is in foreground
    is_foreground = focused_app == KARROT_PACKAGE if focused_app else False

    # Detect crash indicators
    crashed = False
    if focused_app in CRASH_INDICATORS:
        crashed = True
        logging.warning(f"Crash indicator detected: {focused_app}")
    elif not is_running and not is_foreground:
        # App not running and not in foreground (unexpected termination)
        crashed = True
        logging.warning("App unexpectedly terminated")

    return AppState(
        is_running=is_running,
        is_foreground=is_foreground,
        focused_app=focused_app,
        crashed=crashed,
        timestamp=timestamp,
    )


# ============================================================================
# Crash Logging
# ============================================================================

def log_crash(state: AppState, logcat: str) -> None:
    """
    Log crash event with timestamp and logcat snippet.

    Args:
        state: AppState at time of crash
        logcat: Logcat output to save
    """
    log_path = Path(CRASH_LOG_PATH)

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"CRASH DETECTED: {state.timestamp.isoformat()}\n")
            f.write(f"Focused App: {state.focused_app}\n")
            f.write(f"Is Running: {state.is_running}\n")
            f.write(f"Is Foreground: {state.is_foreground}\n")
            f.write("-" * 80 + "\n")
            f.write("LOGCAT SNIPPET:\n")
            f.write(logcat + "\n")
            f.write("=" * 80 + "\n\n")

        logging.info(f"Crash logged to {log_path}")
    except Exception as e:
        logging.error(f"Failed to write crash log: {e}")


# ============================================================================
# Recovery Logic
# ============================================================================

def recover_app() -> bool:
    """
    Execute recovery sequence: force-stop → wait → monkey restart → wait.

    Returns:
        True if recovery successful, False otherwise
    """
    logging.info("Starting recovery sequence...")

    # Step 1: Force stop
    logging.info(f"Force stopping {KARROT_PACKAGE}...")
    if not force_stop_app(KARROT_PACKAGE):
        logging.error("Force stop failed")
        return False

    time.sleep(FORCE_STOP_WAIT)

    # Step 2: Restart with monkey
    logging.info(f"Restarting {KARROT_PACKAGE} with monkey...")
    if not start_app_with_monkey(KARROT_PACKAGE):
        logging.error("Monkey restart failed")
        return False

    # Step 3: Wait for app to fully load
    logging.info(f"Waiting {RESTART_WAIT}s for app to load...")
    time.sleep(RESTART_WAIT)

    # Step 4: Verify recovery
    state = detect_app_state()
    if state.is_foreground and not state.crashed:
        logging.info("Recovery successful!")
        return True
    else:
        logging.error(f"Recovery failed. State: foreground={state.is_foreground}, crashed={state.crashed}")
        return False


# ============================================================================
# Integration API
# ============================================================================

def check_and_recover() -> bool:
    """
    Check app health and recover if needed (integration API).

    This function is designed for integration with flow runners.

    Returns:
        True if app is healthy (no recovery needed)
        False if recovery was performed

    Example:
        from karrot_crash_monitor import check_and_recover

        # Before critical automation step
        if not check_and_recover():
            print("App was recovered, waiting before continuing...")
            time.sleep(5)
    """
    state = detect_app_state()

    if state.crashed:
        logging.warning("App crash detected, initiating recovery...")

        # Capture logcat before recovery
        logcat = capture_logcat(LOGCAT_LINES)
        log_crash(state, logcat)

        # Attempt recovery
        if recover_app():
            logging.info("Recovery completed successfully")
            return False  # Recovery was needed
        else:
            logging.error("Recovery failed")
            return False  # Recovery was needed but failed

    # App is healthy
    return True


# ============================================================================
# Daemon Mode
# ============================================================================

def run_daemon(interval: int = POLL_INTERVAL) -> None:
    """
    Run continuous monitoring in daemon mode.

    Args:
        interval: Polling interval in seconds
    """
    logging.info("Starting Karrot crash monitor daemon...")
    logging.info(f"Monitoring package: {KARROT_PACKAGE}")
    logging.info(f"Poll interval: {interval}s")
    logging.info(f"Crash log: {CRASH_LOG_PATH}")

    consecutive_failures = 0
    max_failures = 5

    try:
        while True:
            try:
                state = detect_app_state()

                if state.crashed:
                    logging.warning(f"Crash detected! Focused app: {state.focused_app}")

                    # Capture logcat
                    logcat = capture_logcat(LOGCAT_LINES)
                    log_crash(state, logcat)

                    # Attempt recovery
                    if recover_app():
                        logging.info("Recovery successful")
                        consecutive_failures = 0  # Reset failure counter
                    else:
                        logging.error("Recovery failed")
                        consecutive_failures += 1

                        if consecutive_failures >= max_failures:
                            logging.critical(
                                f"Recovery failed {max_failures} times consecutively. "
                                "Manual intervention required."
                            )
                            # Continue monitoring but log critical state
                else:
                    # App is healthy
                    if consecutive_failures > 0:
                        logging.info("App recovered and stable")
                        consecutive_failures = 0

                time.sleep(interval)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(f"Monitoring loop error: {e}")
                time.sleep(interval)

    except KeyboardInterrupt:
        logging.info("Daemon stopped by user")


# ============================================================================
# Watchdog (Self-Restart)
# ============================================================================

def run_with_watchdog() -> None:
    """
    Run daemon with watchdog that restarts on unexpected exit.
    """
    restart_count = 0
    max_restarts = 10

    logging.info("Starting watchdog mode...")

    while restart_count < max_restarts:
        try:
            run_daemon()
            break  # Normal exit
        except KeyboardInterrupt:
            logging.info("Watchdog stopped by user")
            break
        except Exception as e:
            restart_count += 1
            logging.error(f"Daemon crashed: {e}")
            logging.info(f"Restarting daemon (attempt {restart_count}/{max_restarts})...")
            time.sleep(5)  # Wait before restart

    if restart_count >= max_restarts:
        logging.critical(f"Daemon restarted {max_restarts} times. Giving up.")
        sys.exit(1)


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Karrot automation crash monitor and auto-recovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in daemon mode (foreground)
  uv run karrot_crash_monitor.py --daemon

  # Run with watchdog (auto-restart on crash)
  uv run karrot_crash_monitor.py --daemon --watchdog

  # Custom poll interval
  uv run karrot_crash_monitor.py --daemon --interval 5

  # Check once and exit
  uv run karrot_crash_monitor.py --check-once

  # Integration example (Python)
  from karrot_crash_monitor import check_and_recover

  if not check_and_recover():
      print("Recovery was performed")
        """,
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (continuous monitoring)",
    )

    parser.add_argument(
        "--watchdog",
        action="store_true",
        help="Enable watchdog (auto-restart daemon on crash)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {POLL_INTERVAL})",
    )

    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Check once and exit (for integration testing)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=CRASH_LOG_PATH,
        help=f"Crash log file path (default: {CRASH_LOG_PATH})",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Update global crash log path
    global CRASH_LOG_PATH
    CRASH_LOG_PATH = args.log_file

    # Execute mode
    if args.check_once:
        # Single check mode
        healthy = check_and_recover()
        if healthy:
            print("✓ App is healthy")
            sys.exit(0)
        else:
            print("✗ Recovery was performed")
            sys.exit(1)

    elif args.daemon:
        # Daemon mode
        if args.watchdog:
            run_with_watchdog()
        else:
            run_daemon(interval=args.interval)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
