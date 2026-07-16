#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "uiautomator2>=3.0.0",
# ]
# ///

"""
ADB Check Karrot Detection - Monitor Play Integrity API detection

Checks if Karrot app detects emulator/spoofed environment by monitoring logcat
for Play Integrity API errors and device detection indicators. Key error codes:
  - Error -18: CLIENT_TRANSIENT_ERROR (device integrity check failed - detected as emulator)
  - Error -1: UNKNOWN_ERROR (possible device check)
  - Error 0: SUCCESS (device passed integrity check)

Usage:
    uv run adb-karrot-check-detection.py --device 127.0.0.1:5555
    uv run adb-karrot-check-detection.py --device 127.0.0.1:5555 --launch
    uv run adb-karrot-check-detection.py --device 127.0.0.1:5555 --detailed

Examples:
    # Quick detection check from logcat
    uv run adb-karrot-check-detection.py --device 127.0.0.1:5555

    # Launch app and monitor detection
    uv run adb-karrot-check-detection.py \\
        --device 127.0.0.1:5555 \\
        --launch \\
        --detailed

    # Check specifically for PlayIntegrity errors
    uv run adb-karrot-check-detection.py \\
        --device 127.0.0.1:5555 \\
        --launch \\
        --timeout 30

Exit Codes:
    0 - Success (app did NOT detect emulator)
    1 - Warning (detection result unclear)
    2 - Error (app DETECTED emulator/spoofed)
    3 - Critical (device not found or logcat error)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
import re
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List
import click

# ========== SECTION 3: CONSTANTS ==========
KARROT_PACKAGE = "kr.co.flo.karrot"
ADB_COMMAND = "adb"
PLAYINTEGRITY_ERROR_18 = "-18"  # CLIENT_TRANSIENT_ERROR
PLAYINTEGRITY_SUCCESS = "0"     # Passed integrity check
DETECTION_KEYWORDS = [
    "PlayIntegrity",
    "integrity error",
    "error-18",
    "CLIENT_TRANSIENT_ERROR",
    "deviceIntegrity",
    "serverIntegrity",
    "com.google.android.gms.integrity",
    "emulator",
    "spoofed",
    "failed integrity check",
    "Device not supported",
    "PlayIntegrityFix",
    "integrity check failed",
    "ro.boot.serialno",
    "ro.serialno",
]

# Enhanced error patterns for better detection
ERROR_PATTERNS = {
    "integrity_failed": {
        "patterns": [
            r"integrity.*fail",
            r"integrity.*error",
            r"check.*failed",
            r"device.*not.*supported"
        ],
        "severity": "critical"
    },
    "emulator_detected": {
        "patterns": [
            r"emulator",
            r"virtual",
            r"qemu",
            r"goldfish"
        ],
        "severity": "critical"
    },
    "spoofed_device": {
        "patterns": [
            r"spoof",
            r"fake.*device",
            r"detected.*spoof"
        ],
        "severity": "critical"
    },
    "playintegrity_error": {
        "patterns": [
            r"error[:\s-]*(\-?18)",
            r"CLIENT_TRANSIENT_ERROR",
            r"playintegrity.*error"
        ],
        "severity": "critical"
    }
}
LOGCAT_TIMEOUT = 60

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class LogcatEntry:
    """Single logcat entry with relevance information."""
    timestamp: str
    level: str
    tag: str
    message: str
    relevant: bool = False
    error_code: Optional[int] = None
    contains_detection: bool = False

@dataclass
class DetectionCheckResult:
    """Result of detection check operation."""
    device_id: str
    detection_found: bool = False
    is_emulator_detected: bool = False
    playintegrity_errors: List[str] = field(default_factory=list)
    detection_logs: List[str] = field(default_factory=list)
    app_launched: bool = False
    detailed_logcat: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 6: HELPER FUNCTIONS ==========
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        devices = []
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id, state = line.split('\t')
                if state == 'device':
                    devices.append(device_id)
        return devices
    except Exception:
        return []

def select_device(device_arg: Optional[str] = None) -> tuple[str, bool]:
    """Select target device or use default."""
    if device_arg:
        return device_arg, True

    devices = get_adb_devices()
    if not devices:
        return None, False
    if len(devices) == 1:
        return devices[0], True
    return devices[0], True

def clear_logcat(device_id: str) -> bool:
    """Clear device logcat to start fresh."""
    try:
        subprocess.run(
            [ADB_COMMAND, "-s", device_id, "logcat", "-c"],
            capture_output=True,
            timeout=5
        )
        return True
    except:
        return False

def launch_karrot_for_detection(device_id: str) -> bool:
    """Launch Karrot app for detection checking."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-karrot/scripts/adb-karrot-launch.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--timeout", "15"],
            capture_output=True,
            text=True,
            timeout=25
        )
        return result.returncode == 0
    except Exception:
        return False

def capture_logcat(device_id: str, timeout: float = 10) -> List[str]:
    """Capture recent logcat lines from device."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "logcat", "-d"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.split('\n') if result.returncode == 0 else []
    except Exception:
        return []


def check_semantic_detection(device_id: str) -> tuple[bool, List[str]]:
    """
    Check for error dialogs using semantic UI detection via uiautomator2.

    Returns:
        Tuple of (is_detected, error_messages)
    """
    try:
        import uiautomator2 as u2
        device = u2.connect(device_id)

        errors_found = []

        # Common error dialog patterns
        error_patterns = [
            "오류",  # Error (Korean)
            "error",
            "failed",
            "not supported",
            "device not compatible",
            "integrity check failed",
            "playintegrity"
        ]

        # Check for error dialogs
        for pattern in error_patterns:
            selector = device(text=pattern)
            if selector.wait(timeout=2):
                errors_found.append(f"Found error dialog: {pattern}")

        # Check for accessibility tree errors
        try:
            dump = device.dump_hierarchy()
            if dump and "error" in dump.lower():
                errors_found.append("Error detected in accessibility tree")
        except Exception:
            pass

        return len(errors_found) > 0, errors_found

    except Exception as e:
        return False, [f"Semantic detection unavailable: {str(e)}"]

def parse_logcat_lines(logcat_output: List[str]) -> List[LogcatEntry]:
    """Parse logcat lines and extract relevant entries."""
    entries = []
    for line in logcat_output:
        if not line.strip():
            continue

        entry = LogcatEntry(
            timestamp="",
            level="",
            tag="",
            message=line.strip()
        )

        # Check relevance
        for keyword in DETECTION_KEYWORDS:
            if keyword.lower() in line.lower():
                entry.relevant = True
                entry.contains_detection = True
                break

        # Try to extract error code
        error_match = re.search(r'error[:\s-]*(-?\d+)', line, re.IGNORECASE)
        if error_match:
            try:
                entry.error_code = int(error_match.group(1))
            except:
                pass

        if entry.relevant or entry.error_code is not None:
            entries.append(entry)

    return entries

def check_for_detection_in_logs(logcat_entries: List[LogcatEntry]) -> tuple[bool, List[str]]:
    """Check if device/emulator detection is evident in logs."""
    is_detected = False
    error_messages = []
    detection_categories = set()

    for entry in logcat_entries:
        # Check for specific error codes
        if entry.error_code == -18:  # CLIENT_TRANSIENT_ERROR
            is_detected = True
            error_messages.append(f"Error -18 (CLIENT_TRANSIENT_ERROR): {entry.message}")
            detection_categories.add("playintegrity_error")

        # Check against enhanced error patterns
        for error_type, error_config in ERROR_PATTERNS.items():
            for pattern in error_config["patterns"]:
                if re.search(pattern, entry.message, re.IGNORECASE):
                    is_detected = True
                    error_messages.append(f"[{error_type}] {entry.message}")
                    detection_categories.add(error_type)
                    break

        # Additional keyword-based detection
        if entry.contains_detection:
            error_messages.append(f"[detection_keyword] {entry.message}")

    # Categorize detection results
    detection_summary = list(detection_categories) if detection_categories else []

    return is_detected, error_messages, detection_summary

# ========== SECTION 7: CORE LOGIC ==========
def check_detection(device_id: str, launch: bool = False,
                   detailed: bool = False, timeout: float = LOGCAT_TIMEOUT) -> DetectionCheckResult:
    """Check if Karrot detects emulator/spoofed environment."""
    start_time = time.time()
    result = DetectionCheckResult(
        device_id=device_id,
        timestamp=start_time
    )

    # Step 1: Clear logcat for clean slate
    clear_logcat(device_id)
    time.sleep(0.5)

    # Step 2: Optionally launch app
    if launch:
        result.app_launched = launch_karrot_for_detection(device_id)
        if not result.app_launched:
            result.error = "Failed to launch Karrot app"
            result.exit_code = 3
            result.duration = time.time() - start_time
            return result

        time.sleep(3)  # Wait for app to perform checks

    # Step 3: Capture logcat
    logcat_lines = capture_logcat(device_id, timeout=timeout)

    if not logcat_lines:
        result.error = "Failed to capture logcat"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    # Step 4: Parse logcat
    logcat_entries = parse_logcat_lines(logcat_lines)

    # Step 5: Check for detection indicators
    result.detection_found = len(logcat_entries) > 0
    is_detected, error_messages, detection_categories = check_for_detection_in_logs(logcat_entries)
    result.is_emulator_detected = is_detected
    result.detection_logs = error_messages[:10]  # Limit to first 10

    # Extract any PlayIntegrity errors found
    result.playintegrity_errors = [
        msg for msg in error_messages
        if "error" in msg.lower() and ("playintegrity" in msg.lower() or "integrity" in msg.lower())
    ]

    # Step 6: Check for semantic detection (UI-based errors)
    if detailed or launch:
        semantic_detected, semantic_errors = check_semantic_detection(device_id)
        if semantic_detected:
            is_detected = True
            result.detection_logs.extend(semantic_errors[:5])

    # Determine exit code
    if is_detected:
        result.exit_code = 2  # Error: emulator detected
    elif result.detection_found and detailed:
        result.exit_code = 1  # Warning: detection indicators found
    else:
        result.exit_code = 0  # Success: no detection found

    result.duration = time.time() - start_time
    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: DetectionCheckResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.is_emulator_detected:
        lines.append(f"❌ EMULATOR DETECTED on {result.device_id}")
    elif result.detection_found:
        lines.append(f"⚠️  Detection indicators found on {result.device_id}")
    else:
        lines.append(f"✅ No emulator detection on {result.device_id}")

    lines.append(f"  App Launched: {'✅ Yes' if result.app_launched else '❌ No'}")
    lines.append(f"  Detection Found: {'✅ Yes' if result.detection_found else '❌ No'}")
    lines.append(f"  Emulator Detected: {'✅ Yes' if result.is_emulator_detected else '❌ No'}")

    if result.playintegrity_errors:
        lines.append(f"\n  PlayIntegrity Errors ({len(result.playintegrity_errors)}):")
        for err in result.playintegrity_errors[:3]:
            lines.append(f"    • {err[:100]}...")

    if result.detection_logs:
        lines.append(f"\n  Detection Logs ({len(result.detection_logs)}):")
        for log in result.detection_logs[:5]:
            lines.append(f"    • {log[:100]}...")

    lines.append(f"\n  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: DetectionCheckResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    help='Target device ID'
)
@click.option(
    '--launch',
    is_flag=True,
    help='Launch Karrot app before checking (recommended for active detection)'
)
@click.option(
    '--detailed',
    is_flag=True,
    help='Show detailed detection indicators'
)
@click.option(
    '--timeout',
    type=float,
    default=LOGCAT_TIMEOUT,
    help='Max seconds to wait for logcat (default: 60)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], launch: bool, detailed: bool, timeout: float,
        output_json: bool) -> None:
    """
    Check if Karrot detects emulator/spoofed environment.

    Monitors logcat for Play Integrity API errors and device detection indicators.
    Use --launch to launch the app during detection check.

    Examples:
        uv run adb-karrot-check-detection.py --device 127.0.0.1:5555
        uv run adb-karrot-check-detection.py --device 127.0.0.1:5555 --launch
        uv run adb-karrot-check-detection.py --device 127.0.0.1:5555 --launch --detailed
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = DetectionCheckResult(
            device_id="unknown",
            error="No connected ADB devices found",
            exit_code=3
        )
        if output_json:
            click.echo(format_json_output(error_result), err=True)
        else:
            click.echo(f"❌ Error: No connected ADB devices", err=True)
        sys.exit(3)

    # Check detection
    result = check_detection(selected_device, launch=launch, detailed=detailed, timeout=timeout)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
