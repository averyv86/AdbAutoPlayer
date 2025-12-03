#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///

"""
Karrot App Automation Loop Runner

Automated loop runner that:
- Loads TOON configuration (states + named steps)
- Detects current screen state
- Executes appropriate workflow steps
- Handles crashes with exponential backoff
- Saves progress to JSON

Package: com.towneers.www
Activity: .launcher.LauncherActivity
Resolution: 1440x2560
Phone: 01039705176
Neighborhood: 서초동
"""

import argparse
import json
import subprocess
import sys
import time
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# === Configuration ===
PACKAGE_NAME = "com.towneers.www"
ACTIVITY_NAME = f"{PACKAGE_NAME}/.launcher.LauncherActivity"
RESOLUTION = (1440, 2560)
PHONE_NUMBER = "01039705176"
NEIGHBORHOOD = "서초동"

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
STATES_CONFIG = CONFIG_DIR / "karrot_states.toon"
STEPS_CONFIG = CONFIG_DIR / "karrot_named_steps.toon"
PROGRESS_FILE = Path("/tmp/karrot-workflow-progress.json")
LOG_FILE = Path("/tmp/karrot-loop-log.json")

# Crash handling config
MAX_CRASH_ATTEMPTS = 10
CRASH_TIMEOUT = 30.0  # 30 seconds total
BACKOFF_BASE = 0.5  # Start with 0.5s


# === Data Classes ===
@dataclass
class TapCoordinate:
    """Single tap coordinate."""
    x: int
    y: int


@dataclass
class ScreenState:
    """Screen state configuration from TOON."""
    name: str
    package: str
    activity: Optional[str] = None
    indicators: Optional[List[str]] = None  # OCR text indicators
    coordinates: Optional[Dict[str, TapCoordinate]] = None


@dataclass
class NamedStep:
    """Named workflow step from TOON."""
    name: str
    actions: List[Dict[str, Any]]
    next_state: Optional[str] = None


@dataclass
class WorkflowProgress:
    """Workflow execution progress."""
    current_state: str
    last_step: str
    timestamp: str
    loop_count: int
    errors: List[str]


# === TOON Configuration Loader ===
class TOONConfigLoader:
    """Loads TOON configuration files."""

    @staticmethod
    def load_states(config_path: Path) -> Dict[str, ScreenState]:
        """Load screen states from TOON config."""
        if not config_path.exists():
            raise FileNotFoundError(f"States config not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        states = {}
        for state_name, state_data in config.get('states', {}).items():
            coordinates = {}
            if 'coordinates' in state_data:
                for coord_name, coord_data in state_data['coordinates'].items():
                    coordinates[coord_name] = TapCoordinate(
                        x=coord_data['x'],
                        y=coord_data['y']
                    )

            states[state_name] = ScreenState(
                name=state_name,
                package=state_data.get('package', PACKAGE_NAME),
                activity=state_data.get('activity'),
                indicators=state_data.get('indicators'),
                coordinates=coordinates if coordinates else None
            )

        return states

    @staticmethod
    def load_steps(config_path: Path) -> Dict[str, NamedStep]:
        """Load named workflow steps from TOON config."""
        if not config_path.exists():
            raise FileNotFoundError(f"Steps config not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        steps = {}
        for step_name, step_data in config.get('named_steps', {}).items():
            steps[step_name] = NamedStep(
                name=step_name,
                actions=step_data.get('actions', []),
                next_state=step_data.get('next_state')
            )

        return steps


# === ADB Interface ===
class ADBInterface:
    """ADB command interface."""

    @staticmethod
    def run_command(command: List[str], timeout: float = 5.0) -> str:
        """Run ADB command and return output."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            log_error(f"ADB command failed: {e}")
            return ""

    @classmethod
    def get_current_activity(cls) -> Optional[str]:
        """Get current foreground activity."""
        output = cls.run_command([
            'adb', 'shell', 'dumpsys', 'activity', 'activities'
        ])

        # Parse activity from dumpsys output
        for line in output.split('\n'):
            if 'mResumedActivity' in line or 'mFocusedActivity' in line:
                # Extract package/activity
                parts = line.split()
                for part in parts:
                    if '/' in part and 'com.' in part:
                        return part.strip()

        return None

    @classmethod
    def is_app_running(cls) -> bool:
        """Check if Karrot app is running."""
        activity = cls.get_current_activity()
        return activity is not None and PACKAGE_NAME in activity

    @classmethod
    def launch_app(cls) -> bool:
        """Launch Karrot app."""
        result = cls.run_command([
            'adb', 'shell', 'am', 'start', '-n', ACTIVITY_NAME
        ])
        time.sleep(2.0)  # Wait for launch
        return "Error" not in result

    @classmethod
    def tap(cls, x: int, y: int) -> None:
        """Perform tap at coordinates."""
        cls.run_command(['adb', 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(0.5)  # Wait after tap

    @classmethod
    def input_text(cls, text: str) -> None:
        """Input text via ADB."""
        # Escape special characters
        escaped_text = text.replace(' ', '%s')
        cls.run_command(['adb', 'shell', 'input', 'text', escaped_text])
        time.sleep(0.3)

    @classmethod
    def take_screenshot(cls, output_path: Path) -> bool:
        """Take screenshot and pull to local."""
        # Screenshot to device
        cls.run_command([
            'adb', 'shell', 'screencap', '-p', '/sdcard/screen.png'
        ])

        # Pull to local
        result = cls.run_command([
            'adb', 'pull', '/sdcard/screen.png', str(output_path)
        ])

        return output_path.exists()


# === State Detector ===
class StateDetector:
    """Detects current screen state."""

    def __init__(self, states: Dict[str, ScreenState]):
        self.states = states

    def detect_state(self) -> Optional[str]:
        """Detect current screen state."""
        # Method 1: Package detection
        activity = ADBInterface.get_current_activity()
        if not activity:
            return "crashed"

        # Check against known states
        for state_name, state_config in self.states.items():
            if state_config.package in activity:
                if state_config.activity is None or state_config.activity in activity:
                    return state_name

        # Method 2: OCR fallback (placeholder - would need OCR implementation)
        # For now, return unknown if package detected but state not recognized
        if PACKAGE_NAME in activity:
            return "unknown_karrot_screen"

        return "unknown"


# === Step Executor ===
class StepExecutor:
    """Executes workflow steps."""

    def __init__(self, states: Dict[str, ScreenState], steps: Dict[str, NamedStep]):
        self.states = states
        self.steps = steps

    def execute_step(self, step_name: str) -> bool:
        """Execute a named step."""
        if step_name not in self.steps:
            log_error(f"Step not found: {step_name}")
            return False

        step = self.steps[step_name]
        log_info(f"Executing step: {step_name}")

        try:
            for action in step.actions:
                action_type = action.get('type')

                if action_type == 'tap':
                    x, y = action['x'], action['y']
                    ADBInterface.tap(x, y)
                    log_info(f"  Tap: ({x}, {y})")

                elif action_type == 'input_text':
                    text = action['text']
                    ADBInterface.input_text(text)
                    log_info(f"  Input: {text}")

                elif action_type == 'wait':
                    duration = action.get('duration', 1.0)
                    time.sleep(duration)
                    log_info(f"  Wait: {duration}s")

                elif action_type == 'tap_coordinate':
                    state_name = action['state']
                    coord_name = action['coordinate']

                    if state_name in self.states:
                        state = self.states[state_name]
                        if state.coordinates and coord_name in state.coordinates:
                            coord = state.coordinates[coord_name]
                            ADBInterface.tap(coord.x, coord.y)
                            log_info(f"  Tap coordinate: {state_name}.{coord_name}")

                else:
                    log_error(f"Unknown action type: {action_type}")

            return True

        except Exception as e:
            log_error(f"Step execution failed: {e}")
            return False


# === Crash Handler ===
class CrashHandler:
    """Handles app crashes with exponential backoff."""

    def __init__(self):
        self.attempt_count = 0
        self.total_wait_time = 0.0

    def reset(self):
        """Reset crash handling state."""
        self.attempt_count = 0
        self.total_wait_time = 0.0

    def handle_crash(self) -> bool:
        """
        Handle crash with exponential backoff.
        Returns True if recovery succeeded, False if max attempts reached.
        """
        self.attempt_count += 1

        if self.attempt_count > MAX_CRASH_ATTEMPTS:
            log_error(f"Max crash recovery attempts reached ({MAX_CRASH_ATTEMPTS})")
            return False

        if self.total_wait_time >= CRASH_TIMEOUT:
            log_error(f"Crash recovery timeout reached ({CRASH_TIMEOUT}s)")
            return False

        # Exponential backoff: 0.5 → 0.75 → 1.125 → 1.7s
        wait_time = BACKOFF_BASE * (1.5 ** (self.attempt_count - 1))

        log_info(f"Crash detected. Recovery attempt {self.attempt_count}/{MAX_CRASH_ATTEMPTS} (wait: {wait_time:.2f}s)")

        time.sleep(wait_time)
        self.total_wait_time += wait_time

        # Attempt relaunch
        if ADBInterface.launch_app():
            log_info("App relaunched successfully")
            self.reset()
            return True
        else:
            log_error("App relaunch failed")
            return False


# === Progress Manager ===
class ProgressManager:
    """Manages workflow progress persistence."""

    @staticmethod
    def save_progress(progress: WorkflowProgress):
        """Save progress to JSON file."""
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(asdict(progress), f, indent=2, ensure_ascii=False)
        except Exception as e:
            log_error(f"Failed to save progress: {e}")

    @staticmethod
    def load_progress() -> Optional[WorkflowProgress]:
        """Load progress from JSON file."""
        if not PROGRESS_FILE.exists():
            return None

        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return WorkflowProgress(**data)
        except Exception as e:
            log_error(f"Failed to load progress: {e}")
            return None


# === Logging ===
def log_info(message: str):
    """Log info message."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": "INFO",
        "message": message
    }
    print(f"[INFO] {message}")
    _append_log(log_entry)


def log_error(message: str):
    """Log error message."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": "ERROR",
        "message": message
    }
    print(f"[ERROR] {message}", file=sys.stderr)
    _append_log(log_entry)


def _append_log(log_entry: Dict[str, str]):
    """Append log entry to JSON log file."""
    try:
        logs = []
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)

        logs.append(log_entry)

        # Keep last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]

        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    except Exception:
        pass  # Silent fail for logging


# === Main Loop Runner ===
class KarrotLoopRunner:
    """Main loop runner orchestrator."""

    def __init__(self):
        log_info("Initializing Karrot Loop Runner")

        # Load configurations
        self.states = TOONConfigLoader.load_states(STATES_CONFIG)
        self.steps = TOONConfigLoader.load_steps(STEPS_CONFIG)

        log_info(f"Loaded {len(self.states)} states and {len(self.steps)} steps")

        # Initialize components
        self.detector = StateDetector(self.states)
        self.executor = StepExecutor(self.states, self.steps)
        self.crash_handler = CrashHandler()

        # Progress tracking
        self.loop_count = 0
        self.errors: List[str] = []

    def run_workflow(self, workflow_name: str, loop_until: Optional[str] = None):
        """
        Run a workflow continuously.

        Args:
            workflow_name: Name of workflow to execute
            loop_until: Optional state to loop until (stops when reached)
        """
        log_info(f"Starting workflow: {workflow_name}")
        if loop_until:
            log_info(f"Loop until state: {loop_until}")

        # Ensure app is running
        if not ADBInterface.is_app_running():
            log_info("App not running, launching...")
            if not ADBInterface.launch_app():
                log_error("Failed to launch app")
                return

        while True:
            self.loop_count += 1
            log_info(f"\n=== Loop {self.loop_count} ===")

            # Detect current state
            current_state = self.detector.detect_state()
            log_info(f"Current state: {current_state}")

            # Handle crashes
            if current_state == "crashed":
                if not self.crash_handler.handle_crash():
                    log_error("Crash recovery failed, stopping")
                    break
                continue

            # Handle unknown states
            if current_state in ["unknown", "unknown_karrot_screen"]:
                log_info("Unknown state detected, taking screenshot")
                screenshot_path = Path(f"/tmp/karrot-unknown-{int(time.time())}.png")
                ADBInterface.take_screenshot(screenshot_path)
                log_info(f"Screenshot saved: {screenshot_path}")
                time.sleep(2.0)
                continue

            # Check loop termination condition
            if loop_until and current_state == loop_until:
                log_info(f"Target state reached: {loop_until}")
                break

            # Find and execute appropriate step for current state
            step_executed = False
            for step_name, step in self.steps.items():
                if workflow_name in step_name:
                    # Execute step
                    success = self.executor.execute_step(step_name)
                    if success:
                        step_executed = True

                        # Save progress
                        progress = WorkflowProgress(
                            current_state=current_state,
                            last_step=step_name,
                            timestamp=datetime.now().isoformat(),
                            loop_count=self.loop_count,
                            errors=self.errors
                        )
                        ProgressManager.save_progress(progress)

                        # Wait for state transition
                        time.sleep(2.0)
                        break

            if not step_executed:
                log_error(f"No step found for workflow: {workflow_name} in state: {current_state}")
                time.sleep(1.0)

    def execute_single_step(self, step_name: str):
        """Execute a single named step."""
        log_info(f"Executing single step: {step_name}")

        if not ADBInterface.is_app_running():
            log_info("App not running, launching...")
            if not ADBInterface.launch_app():
                log_error("Failed to launch app")
                return

        # Detect current state
        current_state = self.detector.detect_state()
        log_info(f"Current state: {current_state}")

        # Execute step
        success = self.executor.execute_step(step_name)
        if success:
            log_info(f"Step completed: {step_name}")
        else:
            log_error(f"Step failed: {step_name}")

    def show_status(self):
        """Show current status and progress."""
        log_info("=== Karrot Loop Runner Status ===")

        # Load progress
        progress = ProgressManager.load_progress()
        if progress:
            print(f"Last State: {progress.current_state}")
            print(f"Last Step: {progress.last_step}")
            print(f"Timestamp: {progress.timestamp}")
            print(f"Loop Count: {progress.loop_count}")
            print(f"Errors: {len(progress.errors)}")
        else:
            print("No progress found")

        # Check app status
        is_running = ADBInterface.is_app_running()
        print(f"\nApp Running: {is_running}")

        if is_running:
            current_state = self.detector.detect_state()
            print(f"Current State: {current_state}")

        # Show configuration
        print(f"\nLoaded States: {len(self.states)}")
        print(f"Loaded Steps: {len(self.steps)}")

        # Show available workflows
        workflows = set()
        for step_name in self.steps.keys():
            workflow = step_name.split('_')[0] if '_' in step_name else step_name
            workflows.add(workflow)

        print(f"\nAvailable Workflows: {', '.join(workflows)}")


# === CLI ===
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Karrot App Automation Loop Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run karrot_loop_runner.py --workflow full_login
  uv run karrot_loop_runner.py --step tap_get_started
  uv run karrot_loop_runner.py --loop-until home
  uv run karrot_loop_runner.py --status
        """
    )

    parser.add_argument(
        '--workflow',
        type=str,
        help='Run workflow continuously (e.g., full_login)'
    )

    parser.add_argument(
        '--step',
        type=str,
        help='Execute single named step'
    )

    parser.add_argument(
        '--loop-until',
        type=str,
        help='Loop until reaching specified state'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status and progress'
    )

    args = parser.parse_args()

    # Initialize runner
    try:
        runner = KarrotLoopRunner()
    except Exception as e:
        log_error(f"Failed to initialize runner: {e}")
        sys.exit(1)

    # Execute command
    try:
        if args.status:
            runner.show_status()

        elif args.workflow:
            runner.run_workflow(args.workflow, loop_until=args.loop_until)

        elif args.step:
            runner.execute_single_step(args.step)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        log_info("\nStopped by user (Ctrl+C)")
        sys.exit(0)

    except Exception as e:
        log_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
