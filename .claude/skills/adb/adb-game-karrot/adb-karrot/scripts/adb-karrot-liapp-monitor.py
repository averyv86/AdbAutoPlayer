# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pure-python-adb>=0.3.0",
# ]
# ///
"""
ADB Karrot LIAPP Monitor - Real-time Logcat Monitoring

This script monitors Android logcat for LIAPP security detection keywords
and provides callbacks on detection for Karrot application automation.

Features:
- Monitor for keywords: LIAPP, security, tamper, integrity, root, magisk
- Callback on detection with configurable actions
- Threading for background monitoring
- Alert/abort options
- Pattern-based detection with severity levels

Usage:
    uv run adb-karrot-liapp-monitor.py
    uv run adb-karrot-liapp-monitor.py --device 127.0.0.1:5555
    uv run adb-karrot-liapp-monitor.py --action alert --timeout 60
    uv run adb-karrot-liapp-monitor.py --keywords LIAPP root magisk --verbose
"""

import argparse
import re
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from queue import Empty, Queue
from typing import Callable, Optional


# Detection keywords with severity levels
class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DetectionPattern:
    """Pattern for detection with severity level."""
    pattern: str
    severity: Severity
    description: str


# Default detection patterns for LIAPP
DEFAULT_PATTERNS = [
    DetectionPattern(r"LIAPP", Severity.CRITICAL, "LIAPP security library detected"),
    DetectionPattern(r"liapp", Severity.CRITICAL, "LIAPP security library detected (lowercase)"),
    DetectionPattern(r"security.*check", Severity.HIGH, "Security check detected"),
    DetectionPattern(r"tamper.*detect", Severity.CRITICAL, "Tampering detection"),
    DetectionPattern(r"integrity.*fail", Severity.CRITICAL, "Integrity check failed"),
    DetectionPattern(r"integrity.*check", Severity.HIGH, "Integrity check running"),
    DetectionPattern(r"root.*detect", Severity.HIGH, "Root detection"),
    DetectionPattern(r"su.*binary", Severity.HIGH, "SU binary check"),
    DetectionPattern(r"magisk", Severity.HIGH, "Magisk detection"),
    DetectionPattern(r"frida", Severity.CRITICAL, "Frida detection"),
    DetectionPattern(r"xposed", Severity.HIGH, "Xposed detection"),
    DetectionPattern(r"hook.*detect", Severity.CRITICAL, "Hook detection"),
    DetectionPattern(r"debug.*detect", Severity.MEDIUM, "Debug detection"),
    DetectionPattern(r"emulator.*detect", Severity.MEDIUM, "Emulator detection"),
    DetectionPattern(r"anti.*debug", Severity.HIGH, "Anti-debug mechanism"),
    DetectionPattern(r"signature.*verify", Severity.MEDIUM, "Signature verification"),
    DetectionPattern(r"apk.*modif", Severity.CRITICAL, "APK modification detected"),
]

# Default configuration
DEFAULT_DEVICE = "127.0.0.1:5555"
DEFAULT_TIMEOUT = 0  # 0 = infinite


@dataclass
class Detection:
    """Represents a single detection event."""
    timestamp: datetime
    pattern: DetectionPattern
    log_line: str
    matched_text: str


class LIAPPMonitor:
    """Monitor for LIAPP security detection in Android logcat."""

    def __init__(
        self,
        device_serial: str = DEFAULT_DEVICE,
        patterns: Optional[list] = None,
        on_detection: Optional[Callable] = None,
        verbose: bool = False,
    ):
        self.device_serial = device_serial
        self.patterns = patterns or DEFAULT_PATTERNS
        self.on_detection = on_detection
        self.verbose = verbose

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._process: Optional[subprocess.Popen] = None
        self._detections: list = []
        self._detection_queue: Queue = Queue()
        self._lock = threading.Lock()

        # Compile regex patterns for efficiency
        self._compiled_patterns = [
            (re.compile(p.pattern, re.IGNORECASE), p)
            for p in self.patterns
        ]

    def add_pattern(self, pattern: str, severity: Severity, description: str) -> None:
        """Add a custom detection pattern."""
        new_pattern = DetectionPattern(pattern, severity, description)
        self.patterns.append(new_pattern)
        self._compiled_patterns.append(
            (re.compile(pattern, re.IGNORECASE), new_pattern)
        )

    def start(self) -> bool:
        """Start monitoring in a background thread."""
        if self._running:
            print("Monitor is already running")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        if self.verbose:
            print(f"Started monitoring device: {self.device_serial}")
            print(f"Watching for {len(self.patterns)} patterns")

        return True

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                self._process.kill()
            self._process = None

        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

        if self.verbose:
            print("Monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        try:
            # Start logcat process
            cmd = ["adb", "-s", self.device_serial, "logcat", "-v", "time"]
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            while self._running and self._process.poll() is None:
                line = self._process.stdout.readline()
                if line:
                    self._process_line(line.strip())

        except Exception as e:
            if self.verbose:
                print(f"Monitor error: {e}")
        finally:
            self._running = False

    def _process_line(self, line: str) -> None:
        """Process a single logcat line."""
        for compiled_regex, pattern in self._compiled_patterns:
            match = compiled_regex.search(line)
            if match:
                detection = Detection(
                    timestamp=datetime.now(),
                    pattern=pattern,
                    log_line=line,
                    matched_text=match.group(0),
                )

                with self._lock:
                    self._detections.append(detection)

                self._detection_queue.put(detection)

                if self.on_detection:
                    try:
                        self.on_detection(detection)
                    except Exception as e:
                        if self.verbose:
                            print(f"Callback error: {e}")

                # Only match first pattern per line
                break

    def get_detections(self) -> list:
        """Get all recorded detections."""
        with self._lock:
            return list(self._detections)

    def wait_for_detection(self, timeout: Optional[float] = None) -> Optional[Detection]:
        """Wait for a detection event."""
        try:
            return self._detection_queue.get(timeout=timeout)
        except Empty:
            return None

    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    def clear_detections(self) -> None:
        """Clear recorded detections."""
        with self._lock:
            self._detections.clear()

        # Clear queue
        while not self._detection_queue.empty():
            try:
                self._detection_queue.get_nowait()
            except Empty:
                break


def default_alert_callback(detection: Detection) -> None:
    """Default callback that prints an alert."""
    severity_colors = {
        Severity.LOW: "\033[94m",      # Blue
        Severity.MEDIUM: "\033[93m",   # Yellow
        Severity.HIGH: "\033[91m",     # Red
        Severity.CRITICAL: "\033[95m", # Magenta
    }
    reset = "\033[0m"
    color = severity_colors.get(detection.pattern.severity, "")

    print(f"\n{color}[DETECTION - {detection.pattern.severity.value}]{reset}")
    print(f"  Time: {detection.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"  Pattern: {detection.pattern.description}")
    print(f"  Matched: {detection.matched_text}")
    print(f"  Log: {detection.log_line[:100]}...")


def abort_callback(detection: Detection) -> None:
    """Callback that aborts on critical detection."""
    if detection.pattern.severity == Severity.CRITICAL:
        print(f"\n\033[91m[ABORT] Critical detection: {detection.pattern.description}\033[0m")
        print("Aborting due to critical security detection...")
        # Signal main thread to stop
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ADB Karrot LIAPP Monitor - Real-time logcat monitoring for security detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Default monitored keywords:
  LIAPP, security, tamper, integrity, root, magisk, frida, xposed,
  hook, debug, emulator, signature, apk

Examples:
  %(prog)s
  %(prog)s --device 127.0.0.1:5555 --verbose
  %(prog)s --action abort --timeout 300
  %(prog)s --keywords LIAPP root magisk --severity HIGH
        """
    )

    parser.add_argument(
        "--device", "-d",
        default=DEFAULT_DEVICE,
        help=f"Device serial (default: {DEFAULT_DEVICE})"
    )

    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        help="Custom keywords to monitor (adds to default patterns)"
    )

    parser.add_argument(
        "--action", "-a",
        choices=["alert", "abort", "silent"],
        default="alert",
        help="Action on detection (default: alert)"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Monitoring timeout in seconds (default: {DEFAULT_TIMEOUT}, 0=infinite)"
    )

    parser.add_argument(
        "--severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default="MEDIUM",
        help="Minimum severity level for custom keywords (default: MEDIUM)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print verbose output"
    )

    parser.add_argument(
        "--list-patterns",
        action="store_true",
        help="List all detection patterns and exit"
    )

    parser.add_argument(
        "--clear-logcat",
        action="store_true",
        help="Clear logcat before starting"
    )

    return parser.parse_args()


def clear_logcat(device_serial: str) -> None:
    """Clear logcat buffer."""
    try:
        subprocess.run(
            ["adb", "-s", device_serial, "logcat", "-c"],
            check=True,
            capture_output=True,
        )
        print("Logcat buffer cleared")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to clear logcat: {e}")


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # List patterns mode
    if args.list_patterns:
        print("Default detection patterns:")
        for p in DEFAULT_PATTERNS:
            print(f"  [{p.severity.value:8}] {p.pattern}: {p.description}")
        return 0

    # Clear logcat if requested
    if args.clear_logcat:
        clear_logcat(args.device)

    # Determine callback
    if args.action == "alert":
        callback = default_alert_callback
    elif args.action == "abort":
        callback = abort_callback
    else:
        callback = None

    # Create monitor
    monitor = LIAPPMonitor(
        device_serial=args.device,
        on_detection=callback,
        verbose=args.verbose,
    )

    # Add custom keywords if specified
    if args.keywords:
        severity = Severity[args.severity]
        for keyword in args.keywords:
            monitor.add_pattern(
                keyword,
                severity,
                f"Custom keyword: {keyword}",
            )
            if args.verbose:
                print(f"Added custom pattern: {keyword} ({severity.value})")

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived shutdown signal...")
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start monitoring
    print(f"Starting LIAPP monitor on device: {args.device}")
    print(f"Monitoring for {len(monitor.patterns)} patterns")
    print(f"Action on detection: {args.action}")
    if args.timeout > 0:
        print(f"Timeout: {args.timeout} seconds")
    print("Press Ctrl+C to stop...\n")

    if not monitor.start():
        return 1

    try:
        start_time = time.time()

        while monitor.is_running():
            # Check timeout
            if args.timeout > 0:
                elapsed = time.time() - start_time
                if elapsed >= args.timeout:
                    print(f"\nTimeout reached ({args.timeout}s)")
                    break

            # Sleep briefly to avoid busy waiting
            time.sleep(0.1)

    except SystemExit:
        # Raised by abort callback
        monitor.stop()
        return 1
    finally:
        monitor.stop()

    # Print summary
    detections = monitor.get_detections()
    print(f"\n--- Monitoring Summary ---")
    print(f"Total detections: {len(detections)}")

    if detections:
        print("\nDetection breakdown by severity:")
        severity_counts = {}
        for d in detections:
            sev = d.pattern.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        for sev, count in sorted(severity_counts.items()):
            print(f"  {sev}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
