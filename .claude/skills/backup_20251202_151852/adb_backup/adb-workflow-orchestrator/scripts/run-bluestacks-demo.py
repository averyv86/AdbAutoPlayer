#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "colorama>=0.4.6",
# ]
# ///

"""
Bluestacks Demonstration Launcher

Orchestrates comprehensive ADB workflow demonstrations on Bluestacks emulator.
Provides visual presentation, progress tracking, and detailed reporting.

Features:
- Device connection management
- Timestamped output directories
- Colored progress indicators
- Comprehensive error handling
- Summary statistics and reporting
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

import click
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


# ============================================================================
# SECTION 4: Constants & Configuration
# ============================================================================

DEFAULT_DEVICE = "127.0.0.1:5555"
DEMO_NAME = "ADB Workflow Orchestrator"
DEMO_VERSION = "1.0.0"
OUTPUT_BASE = Path("/tmp")

# Unicode box drawing characters
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"
BOX_TOP_LEFT = "┌"
BOX_TOP_RIGHT = "┐"
BOX_BOTTOM_LEFT = "└"
BOX_BOTTOM_RIGHT = "┘"

# Progress indicators
PROGRESS_PENDING = "⋯"
PROGRESS_RUNNING = "⟳"
PROGRESS_SUCCESS = "✓"
PROGRESS_FAILURE = "✗"


# ============================================================================
# SECTION 5: Project Root Auto-Detection
# ============================================================================

def find_project_root(start_path: Path = Path.cwd()) -> Path:
    """Find project root by looking for marker files."""
    current = start_path
    markers = [".git", "pyproject.toml", ".claude", ".moai"]

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent

    # Fallback to current working directory
    return Path.cwd()


# ============================================================================
# SECTION 6: Data Models
# ============================================================================

@dataclass
class DemoConfig:
    """Configuration for demonstration run."""
    device: str
    output_dir: Path
    verbose: bool
    no_display: bool
    project_root: Path
    start_time: datetime

@dataclass
class PhaseResult:
    """Result from a single workflow phase."""
    phase_name: str
    status: str  # "pending", "running", "success", "failure"
    duration: float = 0.0
    error_message: Optional[str] = None
    output_files: List[Path] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []


# ============================================================================
# SECTION 7: Core Business Logic
# ============================================================================

def create_output_dir(base_dir: str = "/tmp") -> Path:
    """Create timestamped output directory for demonstration."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(base_dir) / f"bluestacks-demo-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def validate_device_connection(device: str) -> bool:
    """Validate that device is connected and accessible."""
    try:
        result = subprocess.run(
            ["adb", "-s", device, "shell", "echo", "test"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_adb_availability() -> bool:
    """Check if ADB is installed and available."""
    try:
        subprocess.run(["adb", "version"], capture_output=True, timeout=5)
        return True
    except FileNotFoundError:
        return False


def run_workflow(
    device: str,
    output_dir: Path,
    verbose: bool = False,
    project_root: Optional[Path] = None
) -> Tuple[bool, List[PhaseResult]]:
    """Execute the ADB workflow demonstration."""
    if project_root is None:
        project_root = find_project_root()

    results = []

    # Phase 1: Device Info Collection
    phase1 = PhaseResult(phase_name="Device Information Collection", status="running")
    start = time.time()
    try:
        cmd = ["adb", "-s", device, "shell", "getprop", "ro.build.version.release"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            phase1.status = "success"
            log_file = output_dir / "device-info.log"
            log_file.write_text(f"Device: {device}\nAndroid Version: {result.stdout.strip()}\n")
            phase1.output_files = [log_file]
        else:
            phase1.status = "failure"
            phase1.error_message = f"Failed to get device info: {result.stderr}"
    except subprocess.TimeoutExpired:
        phase1.status = "failure"
        phase1.error_message = "Command timeout"
    except Exception as e:
        phase1.status = "failure"
        phase1.error_message = str(e)
    finally:
        phase1.duration = time.time() - start

    results.append(phase1)

    # Phase 2: Screenshot Capture
    phase2 = PhaseResult(phase_name="Screenshot Capture", status="running")
    start = time.time()
    try:
        screenshot_path = output_dir / "screenshot.png"
        cmd = ["adb", "-s", device, "shell", "screencap", "-p", "/sdcard/screenshot.png"]
        result = subprocess.run(cmd, capture_output=True, timeout=10)

        if result.returncode == 0:
            cmd_pull = ["adb", "-s", device, "pull", "/sdcard/screenshot.png", str(screenshot_path)]
            pull_result = subprocess.run(cmd_pull, capture_output=True, timeout=10)

            if pull_result.returncode == 0:
                phase2.status = "success"
                phase2.output_files = [screenshot_path]
            else:
                phase2.status = "failure"
                phase2.error_message = "Failed to pull screenshot"
        else:
            phase2.status = "failure"
            phase2.error_message = "Failed to capture screenshot"
    except subprocess.TimeoutExpired:
        phase2.status = "failure"
        phase2.error_message = "Command timeout"
    except Exception as e:
        phase2.status = "failure"
        phase2.error_message = str(e)
    finally:
        phase2.duration = time.time() - start

    results.append(phase2)

    # Phase 3: System Information
    phase3 = PhaseResult(phase_name="System Information", status="running")
    start = time.time()
    try:
        cmd = ["adb", "-s", device, "shell", "dumpsys", "meminfo"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            phase3.status = "success"
            log_file = output_dir / "system-info.log"
            log_file.write_text(result.stdout)
            phase3.output_files = [log_file]
        else:
            phase3.status = "failure"
            phase3.error_message = "Failed to collect system info"
    except subprocess.TimeoutExpired:
        phase3.status = "failure"
        phase3.error_message = "Command timeout"
    except Exception as e:
        phase3.status = "failure"
        phase3.error_message = str(e)
    finally:
        phase3.duration = time.time() - start

    results.append(phase3)

    # Overall success if at least 2 phases succeeded
    overall_success = sum(1 for r in results if r.status == "success") >= 2

    return overall_success, results


# ============================================================================
# SECTION 8: Output Formatters
# ============================================================================

def display_header(device: str, output_dir: Path) -> None:
    """Display formatted demonstration header."""
    width = 70

    # Top border
    click.echo(f"{Fore.CYAN}{BOX_TOP_LEFT}{BOX_HORIZONTAL * (width - 2)}{BOX_TOP_RIGHT}{Style.RESET_ALL}")

    # Title
    title = f" {DEMO_NAME} v{DEMO_VERSION} "
    padding = width - len(title) - 2
    left_pad = padding // 2
    right_pad = padding - left_pad
    click.echo(f"{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}{Fore.BRIGHT_CYAN}{' ' * left_pad}{title}{' ' * right_pad}{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}")

    # Divider
    click.echo(f"{Fore.CYAN}{BOX_VERTICAL}{BOX_HORIZONTAL * (width - 2)}{BOX_VERTICAL}{Style.RESET_ALL}")

    # Device info
    device_line = f" Device: {device}"
    click.echo(f"{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}{device_line:<{width - 2}}{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}")

    # Output directory
    output_line = f" Output: {output_dir.name}"
    click.echo(f"{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}{output_line:<{width - 2}}{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}")

    # Start time
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_line = f" Start Time: {start_time}"
    click.echo(f"{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}{time_line:<{width - 2}}{Fore.CYAN}{BOX_VERTICAL}{Style.RESET_ALL}")

    # Bottom border
    click.echo(f"{Fore.CYAN}{BOX_BOTTOM_LEFT}{BOX_HORIZONTAL * (width - 2)}{BOX_BOTTOM_RIGHT}{Style.RESET_ALL}")
    click.echo()


def display_device_status(device: str, connected: bool) -> None:
    """Display device connection status."""
    status_icon = f"{Fore.GREEN}{PROGRESS_SUCCESS}{Style.RESET_ALL}" if connected else f"{Fore.RED}{PROGRESS_FAILURE}{Style.RESET_ALL}"
    status_text = f"{Fore.GREEN}Connected{Style.RESET_ALL}" if connected else f"{Fore.RED}Disconnected{Style.RESET_ALL}"

    click.echo(f"{status_icon} Device Status: {status_text}")
    click.echo()


def display_phase_progress(phases: List[PhaseResult]) -> None:
    """Display phase progress with status indicators."""
    click.echo(f"{Fore.BRIGHT_CYAN}Workflow Phases:{Style.RESET_ALL}")

    for phase in phases:
        if phase.status == "success":
            icon = f"{Fore.GREEN}{PROGRESS_SUCCESS}{Style.RESET_ALL}"
            status_color = Fore.GREEN
        elif phase.status == "failure":
            icon = f"{Fore.RED}{PROGRESS_FAILURE}{Style.RESET_ALL}"
            status_color = Fore.RED
        else:
            icon = f"{Fore.YELLOW}{PROGRESS_RUNNING}{Style.RESET_ALL}"
            status_color = Fore.YELLOW

        duration_str = f"{phase.duration:.2f}s" if phase.duration > 0 else "pending"
        status_display = phase.status.upper()

        click.echo(
            f"  {icon} {phase.phase_name:<40} "
            f"{status_color}{status_display:<8}{Style.RESET_ALL} ({duration_str})"
        )

        if phase.error_message:
            click.echo(f"     {Fore.RED}Error: {phase.error_message}{Style.RESET_ALL}")

        for output_file in phase.output_files:
            click.echo(f"     {Fore.CYAN}├─ {output_file.name}{Style.RESET_ALL}")


def display_summary(
    phases: List[PhaseResult],
    output_dir: Path,
    total_duration: float,
    success: bool
) -> None:
    """Display execution summary and statistics."""
    click.echo()
    click.echo(f"{Fore.BRIGHT_CYAN}Summary Statistics:{Style.RESET_ALL}")

    total_phases = len(phases)
    successful_phases = sum(1 for p in phases if p.status == "success")
    failed_phases = sum(1 for p in phases if p.status == "failure")
    total_phase_duration = sum(p.duration for p in phases)

    # Overall result
    result_icon = f"{Fore.GREEN}{PROGRESS_SUCCESS}{Style.RESET_ALL}" if success else f"{Fore.RED}{PROGRESS_FAILURE}{Style.RESET_ALL}"
    result_text = f"{Fore.GREEN}PASSED{Style.RESET_ALL}" if success else f"{Fore.RED}FAILED{Style.RESET_ALL}"
    click.echo(f"{result_icon} Overall Result: {result_text}")

    # Statistics
    click.echo(f"  Total Phases: {total_phases}")
    click.echo(f"  {Fore.GREEN}Successful: {successful_phases}{Style.RESET_ALL}")
    click.echo(f"  {Fore.RED}Failed: {failed_phases}{Style.RESET_ALL}")
    click.echo(f"  Success Rate: {(successful_phases/total_phases*100):.1f}%")
    click.echo()

    # Timing
    click.echo(f"{Fore.BRIGHT_CYAN}Execution Time:{Style.RESET_ALL}")
    click.echo(f"  Phase Execution: {total_phase_duration:.2f}s")
    click.echo(f"  Total Time: {total_duration:.2f}s")
    click.echo()

    # Output files
    click.echo(f"{Fore.BRIGHT_CYAN}Output Directory:{Style.RESET_ALL}")
    click.echo(f"  {Fore.CYAN}{output_dir}{Style.RESET_ALL}")
    click.echo()

    # Generated files
    if output_dir.exists():
        files = list(output_dir.glob("*"))
        if files:
            click.echo(f"{Fore.BRIGHT_CYAN}Generated Files:{Style.RESET_ALL}")
            for file in sorted(files):
                size_kb = file.stat().st_size / 1024 if file.is_file() else 0
                if file.is_file():
                    click.echo(f"  {Fore.CYAN}├─ {file.name}{Style.RESET_ALL} ({size_kb:.1f} KB)")


# ============================================================================
# SECTION 9: CLI Interface + Entry Point
# ============================================================================

@click.command()
@click.option(
    "--device",
    default=DEFAULT_DEVICE,
    help=f"Device ID (default: {DEFAULT_DEVICE})"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default=None,
    help="Output directory (auto-generated if not specified)"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--no-display",
    is_flag=True,
    help="Skip image display"
)
def main(device: str, output_dir: Optional[str], verbose: bool, no_display: bool) -> int:
    """
    Bluestacks Demonstration Launcher

    Orchestrates comprehensive ADB workflow demonstrations on Bluestacks emulator.
    Provides visual presentation, progress tracking, and detailed reporting.
    """
    run_start = time.time()

    try:
        # Setup
        if output_dir:
            demo_output = Path(output_dir)
            demo_output.mkdir(parents=True, exist_ok=True)
        else:
            demo_output = create_output_dir(str(OUTPUT_BASE))

        project_root = find_project_root()

        # Create configuration
        config = DemoConfig(
            device=device,
            output_dir=demo_output,
            verbose=verbose,
            no_display=no_display,
            project_root=project_root,
            start_time=datetime.now()
        )

        # Display header
        display_header(config.device, config.output_dir)

        # Check ADB availability
        if not check_adb_availability():
            click.echo(f"{Fore.RED}Error: ADB is not installed or not in PATH{Style.RESET_ALL}")
            click.echo("Please install Android SDK Platform Tools and add 'adb' to your PATH")
            return 1

        # Check device connection
        if verbose:
            click.echo(f"{Fore.YELLOW}Checking device connection...{Style.RESET_ALL}")

        connected = validate_device_connection(config.device)
        display_device_status(config.device, connected)

        if not connected:
            click.echo(
                f"{Fore.RED}Error: Cannot connect to device {config.device}{Style.RESET_ALL}\n"
                f"Make sure:\n"
                f"  1. Bluestacks is running\n"
                f"  2. Device ID is correct\n"
                f"  3. ADB daemon is accessible"
            )
            return 1

        # Run workflow
        if verbose:
            click.echo(f"{Fore.YELLOW}Starting workflow execution...{Style.RESET_ALL}\n")

        success, phases = run_workflow(
            device=config.device,
            output_dir=config.output_dir,
            verbose=config.verbose,
            project_root=config.project_root
        )

        # Display results
        display_phase_progress(phases)

        run_end = time.time()
        total_duration = run_end - run_start

        display_summary(phases, config.output_dir, total_duration, success)

        # Save execution report
        report_data = {
            "timestamp": config.start_time.isoformat(),
            "device": config.device,
            "success": success,
            "duration_seconds": total_duration,
            "phases": [
                {
                    "name": p.phase_name,
                    "status": p.status,
                    "duration": p.duration,
                    "error": p.error_message,
                    "output_files": [str(f) for f in p.output_files]
                }
                for p in phases
            ]
        }

        report_file = config.output_dir / "execution-report.json"
        report_file.write_text(json.dumps(report_data, indent=2))

        if verbose:
            click.echo(f"{Fore.CYAN}Execution report saved: {report_file}{Style.RESET_ALL}")

        return 0 if success else 1

    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}Demonstration interrupted by user{Style.RESET_ALL}")
        return 130
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
