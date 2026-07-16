#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.39.0", "Pillow>=10.0.0"]
# ///
"""
Karrot Unified Automation - Integration Layer for AI Vision + Smart Detection

This script ties together the AI vision and adaptive detection systems to provide
a complete automation solution for the Karrot app.

Components:
- karrot_ai_vision.py: Claude Vision-based semantic understanding
- karrot_smart_detector.py: Multi-layer detection with exponential backoff

Features:
- Unified KarrotAutomation class
- State machine for navigation
- Workflow execution engine
- Error recovery with Play Store/permission handling
- Human-like delays and variance
- JSON logging for debugging

Target Device: BlueStacks Air (1440x2560)
User Settings: Neighborhood=서초동, Phone=01039705176, Country=Korea

Usage:
    uv run karrot_unified_automation.py --tap "Get Started button"
    uv run karrot_unified_automation.py --navigate home
    uv run karrot_unified_automation.py --workflow login
    uv run karrot_unified_automation.py --launch
    uv run karrot_unified_automation.py --status
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Import from karrot_ai_vision
try:
    from karrot_ai_vision import (
        ErrorInfo,
        GameState,
        KarrotAIVision,
        Point,
        ScreenAnalysis,
        capture_screenshot as vision_capture_screenshot,
    )
except ImportError:
    print("[ERROR] Could not import karrot_ai_vision.py")
    print("Make sure karrot_ai_vision.py is in the same directory")
    sys.exit(1)

# Import from karrot_smart_detector
try:
    from karrot_smart_detector import (
        DetectionResult,
        SmartDetector,
    )
except ImportError:
    print("[ERROR] Could not import karrot_smart_detector.py")
    print("Make sure karrot_smart_detector.py is in the same directory")
    sys.exit(1)


# Configuration
SCREEN_RESOLUTION = (1440, 2560)  # BlueStacks Air
DEVICE = "127.0.0.1:5555"
KARROT_PACKAGE = "com.towneers.www"
SCREENSHOT_PATH = "/tmp/karrot_screen.png"
LOG_PATH = "/tmp/karrot-automation-log.json"

# User settings
USER_SETTINGS = {
    "neighborhood": "서초동",
    "phone": "01039705176",
    "country": "Korea",
}

# Timing configuration
HUMAN_DELAY_MIN = 0.5
HUMAN_DELAY_MAX = 1.5
ACTION_DELAY_MIN = 0.3
ACTION_DELAY_MAX = 0.8
NAVIGATION_TIMEOUT = 30.0
ERROR_RECOVERY_TIMEOUT = 10.0


class ActionType(Enum):
    """Available automation actions"""
    TAP = "tap"
    SWIPE = "swipe"
    INPUT_TEXT = "input_text"
    KEYEVENT = "keyevent"
    WAIT = "wait"
    BACK = "back"
    HOME = "home"


@dataclass
class Action:
    """Single automation action"""
    action_type: ActionType
    target: Optional[str] = None  # Element description or coordinates
    text: Optional[str] = None  # For input_text
    direction: Optional[str] = None  # For swipe: up, down, left, right
    duration_sec: Optional[float] = None  # For wait
    x: Optional[int] = None  # For direct tap
    y: Optional[int] = None  # For direct tap


@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    name: str
    action: Action
    expected_state: Optional[GameState] = None
    retry_count: int = 3
    optional: bool = False  # If True, failure won't stop workflow


@dataclass
class AutomationResult:
    """Result of an automation action"""
    success: bool
    action: str
    timestamp: str
    elapsed_sec: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AutomationLogger:
    """JSON logger for automation events"""

    def __init__(self, log_path: str = LOG_PATH):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.events: list[dict] = []

    def log(self, event_type: str, data: dict) -> None:
        """Log an event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        self.events.append(event)

        # Append to file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def get_recent(self, n: int = 10) -> list[dict]:
        """Get recent events"""
        return self.events[-n:]


class KarrotAutomation:
    """Unified automation system for Karrot app"""

    def __init__(
        self,
        device: str = DEVICE,
        anthropic_api_key: str = "",
        enable_ai_vision: bool = True,
    ):
        self.device = device
        self.vision = KarrotAIVision(api_key=anthropic_api_key) if enable_ai_vision else None
        self.detector = SmartDetector(
            anthropic_api_key=anthropic_api_key,
            enable_ai_vision=enable_ai_vision
        )
        self.logger = AutomationLogger()
        self.current_state = GameState.UNKNOWN
        self.enable_ai_vision = enable_ai_vision

        # Statistics
        self.stats = {
            "actions_executed": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "errors_recovered": 0,
            "workflows_completed": 0,
        }

    def _run_adb(self, cmd: str, timeout: float = 5.0) -> tuple[bool, str]:
        """Run ADB command and return success status and output"""
        try:
            full_cmd = f"adb -s {self.device} {cmd}"
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            output = result.stdout.strip()
            return success, output
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            return False, str(e)

    def _human_delay(self, min_sec: float = HUMAN_DELAY_MIN, max_sec: float = HUMAN_DELAY_MAX) -> None:
        """Add human-like random delay"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _action_delay(self) -> None:
        """Short delay between actions"""
        delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
        time.sleep(delay)

    def capture_screenshot(self) -> bool:
        """Capture screenshot from device"""
        try:
            vision_capture_screenshot(SCREENSHOT_PATH)
            return Path(SCREENSHOT_PATH).exists()
        except Exception as e:
            self.logger.log("error", {"message": f"Screenshot failed: {e}"})
            return False

    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates"""
        success, output = self._run_adb(f"shell input tap {x} {y}")
        self._action_delay()

        self.logger.log("tap", {
            "x": x,
            "y": y,
            "success": success,
            "output": output
        })

        return success

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Swipe from (x1, y1) to (x2, y2)"""
        success, output = self._run_adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration_ms}")
        self._human_delay()

        self.logger.log("swipe", {
            "from": {"x": x1, "y": y1},
            "to": {"x": x2, "y": y2},
            "duration_ms": duration_ms,
            "success": success
        })

        return success

    def swipe_direction(self, direction: str) -> bool:
        """Swipe in a direction"""
        w, h = SCREEN_RESOLUTION
        center_x, center_y = w // 2, h // 2
        offset = 500

        directions = {
            "up": (center_x, center_y + offset, center_x, center_y - offset),
            "down": (center_x, center_y - offset, center_x, center_y + offset),
            "left": (center_x + offset, center_y, center_x - offset, center_y),
            "right": (center_x - offset, center_y, center_x + offset, center_y),
        }

        if direction not in directions:
            return False

        x1, y1, x2, y2 = directions[direction]
        return self.swipe(x1, y1, x2, y2)

    def input_text(self, text: str) -> bool:
        """Input text via ADB"""
        # Escape spaces and special characters
        escaped = text.replace(" ", "%s")
        success, output = self._run_adb(f"shell input text '{escaped}'")
        self._action_delay()

        self.logger.log("input_text", {
            "text": text,
            "success": success
        })

        return success

    def keyevent(self, keycode: int) -> bool:
        """Send keyevent"""
        success, output = self._run_adb(f"shell input keyevent {keycode}")
        self._action_delay()

        self.logger.log("keyevent", {
            "keycode": keycode,
            "success": success
        })

        return success

    def back(self) -> bool:
        """Press back button"""
        return self.keyevent(4)

    def home(self) -> bool:
        """Press home button"""
        return self.keyevent(3)

    def launch_app(self) -> bool:
        """Launch Karrot app"""
        success, output = self._run_adb(
            f"shell am start -n {KARROT_PACKAGE}/.activities.MainActivity"
        )

        self.logger.log("launch_app", {
            "package": KARROT_PACKAGE,
            "success": success
        })

        if success:
            self._human_delay(2.0, 3.0)  # Wait for app to start

        return success

    def tap_element(self, description: str, timeout: float = 10.0) -> bool:
        """
        Find element by description and tap it.
        Uses smart detector with fallback to AI vision.
        """
        start_time = time.time()

        print(f"\n[TAP] Finding '{description}'...")
        result = self.detector.wait_for_element(description, timeout=timeout)

        if result.found and result.point:
            print(f"[TAP] Tapping at ({result.point.x}, {result.point.y})")
            success = self.tap(result.point.x, result.point.y)

            self.stats["actions_executed"] += 1
            if success:
                self.stats["successful_actions"] += 1
            else:
                self.stats["failed_actions"] += 1

            self.logger.log("tap_element", {
                "description": description,
                "x": result.point.x,
                "y": result.point.y,
                "method": result.method.value,
                "success": success,
                "elapsed_sec": time.time() - start_time,
            })

            return success

        print(f"[FAILED] Could not find '{description}'")
        self.stats["actions_executed"] += 1
        self.stats["failed_actions"] += 1

        self.logger.log("tap_element_failed", {
            "description": description,
            "reason": "not_found",
            "elapsed_sec": time.time() - start_time,
        })

        return False

    def get_current_state(self) -> GameState:
        """Get current game state"""
        state = self.detector.detect_game_state()
        self.current_state = state

        self.logger.log("state_detected", {
            "state": state.value
        })

        return state

    def wait_for_state(self, target_state: GameState, timeout: float = NAVIGATION_TIMEOUT) -> bool:
        """Wait for specific game state"""
        start_time = time.time()

        print(f"\n[WAIT] Waiting for state: {target_state.value}")

        while time.time() - start_time < timeout:
            current = self.get_current_state()

            if current == target_state:
                print(f"[SUCCESS] Reached state: {target_state.value}")
                return True

            self._human_delay(1.0, 2.0)

        print(f"[TIMEOUT] Could not reach state: {target_state.value}")
        return False

    def handle_error(self, error_info: Optional[ErrorInfo] = None) -> bool:
        """
        Auto-recover from errors.
        Returns True if recovered, False otherwise.
        """
        if not error_info and self.vision:
            # Detect error
            self.capture_screenshot()
            error_info = self.vision.detect_error(SCREENSHOT_PATH)

        if not error_info:
            return False

        print(f"\n[ERROR] Detected: {error_info.error_type}")
        print(f"[RECOVERY] Action: {error_info.recovery_action}")

        recovery_map = {
            "tap_ok": lambda: self.tap_element("OK", timeout=5.0),
            "tap_cancel": lambda: self.tap_element("Cancel", timeout=5.0),
            "navigate_back": lambda: self.back(),
            "restart_app": lambda: self.launch_app(),
            "close_popup": lambda: self.tap_element("Close", timeout=5.0) or self.back(),
        }

        recovery_func = recovery_map.get(error_info.recovery_action)
        if recovery_func:
            success = recovery_func()
            if success:
                self.stats["errors_recovered"] += 1
                self.logger.log("error_recovered", {
                    "error_type": error_info.error_type,
                    "recovery_action": error_info.recovery_action,
                })
            return success

        return False

    def navigate_to(self, target_state: GameState, timeout: float = NAVIGATION_TIMEOUT) -> bool:
        """
        Auto-navigate to target state using state machine.
        """
        start_time = time.time()
        max_attempts = 10
        attempt = 0

        print(f"\n{'='*50}")
        print(f"[NAVIGATE] Target: {target_state.value}")
        print(f"{'='*50}")

        while attempt < max_attempts and time.time() - start_time < timeout:
            attempt += 1
            current = self.get_current_state()

            print(f"\n[NAVIGATE] Attempt {attempt}: Current={current.value}, Target={target_state.value}")

            # Check if we've reached the target
            if current == target_state:
                print(f"[SUCCESS] Reached {target_state.value}")
                return True

            # Check for errors
            if self.vision:
                error = self.vision.detect_error(SCREENSHOT_PATH)
                if error:
                    self.handle_error(error)
                    continue

            # State-specific navigation logic
            success = self._navigate_step(current, target_state)
            if not success:
                print(f"[WARN] Navigation step failed")

            self._human_delay(1.0, 2.0)

        print(f"[FAILED] Could not reach {target_state.value} in {attempt} attempts")
        return False

    def _navigate_step(self, current: GameState, target: GameState) -> bool:
        """Execute one navigation step"""

        # Navigation rules
        if current == GameState.PLAY_STORE:
            # Close Play Store
            return self.back()

        if current == GameState.PERMISSION_DIALOG:
            # Allow permission
            return self.tap_element("Allow", timeout=5.0)

        if current == GameState.WELCOME and target == GameState.LOGIN:
            return self.tap_element("Get Started", timeout=5.0)

        if current == GameState.LOGIN and target == GameState.PHONE_INPUT:
            return self.tap_element("Log in", timeout=5.0)

        if current == GameState.PHONE_INPUT and target == GameState.VERIFICATION:
            # Input phone number
            if self.tap_element("phone input", timeout=5.0):
                self.input_text(USER_SETTINGS["phone"])
                return self.tap_element("Next", timeout=5.0)
            return False

        if current == GameState.VERIFICATION and target == GameState.NEIGHBORHOOD_SELECT:
            # Verification code must be entered manually
            print("[MANUAL] Please enter verification code manually")
            return self.wait_for_state(GameState.NEIGHBORHOOD_SELECT, timeout=60.0)

        if current == GameState.NEIGHBORHOOD_SELECT and target == GameState.HOME:
            # Select neighborhood
            if self.tap_element("search", timeout=5.0):
                self.input_text(USER_SETTINGS["neighborhood"])
                self._human_delay()
                return self.tap_element(USER_SETTINGS["neighborhood"], timeout=5.0)
            return False

        # Default: try to move forward
        return self.tap_element("Next", timeout=5.0) or self.tap_element("Continue", timeout=5.0)

    def execute_workflow(self, workflow: list[WorkflowStep]) -> AutomationResult:
        """
        Execute a sequence of workflow steps.
        Returns overall result.
        """
        start_time = time.time()
        total_steps = len(workflow)
        completed_steps = 0

        print(f"\n{'='*50}")
        print(f"[WORKFLOW] Starting {total_steps} steps")
        print(f"{'='*50}")

        for i, step in enumerate(workflow, 1):
            print(f"\n[STEP {i}/{total_steps}] {step.name}")

            # Execute action
            success = self._execute_action(step.action)

            if success:
                completed_steps += 1
                print(f"[OK] Step {i} completed")

                # Check expected state if specified
                if step.expected_state:
                    if not self.wait_for_state(step.expected_state, timeout=10.0):
                        if not step.optional:
                            print(f"[FAILED] Expected state not reached: {step.expected_state.value}")
                            break
            else:
                print(f"[FAILED] Step {i} failed")
                if not step.optional:
                    # Try error recovery
                    if not self.handle_error():
                        break

            self._human_delay()

        elapsed = time.time() - start_time
        success = completed_steps == total_steps

        if success:
            self.stats["workflows_completed"] += 1

        result = AutomationResult(
            success=success,
            action=f"workflow_{total_steps}_steps",
            timestamp=datetime.now().isoformat(),
            elapsed_sec=elapsed,
            metadata={
                "total_steps": total_steps,
                "completed_steps": completed_steps,
            }
        )

        self.logger.log("workflow_completed", asdict(result))

        return result

    def _execute_action(self, action: Action) -> bool:
        """Execute a single action"""

        if action.action_type == ActionType.TAP:
            if action.x is not None and action.y is not None:
                return self.tap(action.x, action.y)
            elif action.target:
                return self.tap_element(action.target)
            return False

        if action.action_type == ActionType.SWIPE:
            if action.direction:
                return self.swipe_direction(action.direction)
            return False

        if action.action_type == ActionType.INPUT_TEXT:
            if action.text:
                return self.input_text(action.text)
            return False

        if action.action_type == ActionType.KEYEVENT:
            if action.x is not None:  # Use x as keycode
                return self.keyevent(action.x)
            return False

        if action.action_type == ActionType.WAIT:
            if action.duration_sec:
                time.sleep(action.duration_sec)
                return True
            return False

        if action.action_type == ActionType.BACK:
            return self.back()

        if action.action_type == ActionType.HOME:
            return self.home()

        return False

    def get_stats(self) -> dict:
        """Get automation statistics"""
        return {
            **self.stats,
            "current_state": self.current_state.value,
            "detector_stats": self.detector.get_stats(),
            "recent_logs": self.logger.get_recent(5),
        }


# Predefined workflows
WORKFLOWS = {
    "login": [
        WorkflowStep(
            name="Launch app",
            action=Action(action_type=ActionType.WAIT, duration_sec=2.0),
            expected_state=None,
            optional=False,
        ),
        WorkflowStep(
            name="Tap Get Started",
            action=Action(action_type=ActionType.TAP, target="Get Started"),
            expected_state=GameState.LOGIN,
            optional=False,
        ),
        WorkflowStep(
            name="Tap Log in",
            action=Action(action_type=ActionType.TAP, target="Log in"),
            expected_state=GameState.PHONE_INPUT,
            optional=False,
        ),
        WorkflowStep(
            name="Enter phone number",
            action=Action(action_type=ActionType.TAP, target="phone input"),
            expected_state=None,
            optional=False,
        ),
        WorkflowStep(
            name="Input phone",
            action=Action(action_type=ActionType.INPUT_TEXT, text=USER_SETTINGS["phone"]),
            expected_state=None,
            optional=False,
        ),
        WorkflowStep(
            name="Tap Next",
            action=Action(action_type=ActionType.TAP, target="Next"),
            expected_state=GameState.VERIFICATION,
            optional=False,
        ),
    ],
}


def print_status(automation: KarrotAutomation) -> None:
    """Print automation status"""
    stats = automation.get_stats()
    state = automation.get_current_state()

    print("\n" + "="*50)
    print("KARROT AUTOMATION STATUS")
    print("="*50)
    print(f"Current State: {state.value}")
    print(f"AI Vision: {'Enabled' if automation.enable_ai_vision else 'Disabled'}")
    print(f"\nAutomation Statistics:")
    print(f"  Actions Executed: {stats['actions_executed']}")
    print(f"  Successful: {stats['successful_actions']}")
    print(f"  Failed: {stats['failed_actions']}")
    print(f"  Errors Recovered: {stats['errors_recovered']}")
    print(f"  Workflows Completed: {stats['workflows_completed']}")

    detector_stats = stats.get("detector_stats", {})
    if detector_stats:
        print(f"\nDetector Statistics:")
        print(f"  Total Detections: {detector_stats.get('total_detections', 0)}")
        print(f"  Cache Hits: {detector_stats.get('cache_hits', 0)}")
        print(f"  Timeouts: {detector_stats.get('timeouts', 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Karrot Unified Automation - AI Vision + Smart Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tap "Get Started button"          Find and tap element
  %(prog)s --navigate home                     Navigate to home screen
  %(prog)s --workflow login                    Execute login workflow
  %(prog)s --launch                            Launch Karrot app
  %(prog)s --status                            Show automation status

Available workflows:
  login - Complete login flow with phone number

User settings:
  Neighborhood: 서초동
  Phone: 01039705176
  Country: Korea
        """
    )

    parser.add_argument(
        "--tap", "-t",
        metavar="DESCRIPTION",
        help="Find and tap element by description"
    )
    parser.add_argument(
        "--navigate", "-n",
        metavar="STATE",
        help="Navigate to target state (welcome, login, home, etc.)"
    )
    parser.add_argument(
        "--workflow", "-w",
        metavar="NAME",
        help="Execute predefined workflow (login)"
    )
    parser.add_argument(
        "--launch", "-l",
        action="store_true",
        help="Launch Karrot app"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show automation status"
    )
    parser.add_argument(
        "--device", "-d",
        default=DEVICE,
        help=f"ADB device (default: {DEVICE})"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI Vision (faster but less accurate)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    # Check for ANTHROPIC_API_KEY if AI is enabled
    if not args.no_ai and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARN] ANTHROPIC_API_KEY not set. Running with --no-ai")
        args.no_ai = True

    # Initialize automation
    try:
        automation = KarrotAutomation(
            device=args.device,
            enable_ai_vision=not args.no_ai
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize automation: {e}")
        return 1

    # Handle --launch
    if args.launch:
        print("[LAUNCH] Starting Karrot app...")
        success = automation.launch_app()
        if success:
            print("[OK] App launched")
            return 0
        else:
            print("[FAILED] Could not launch app")
            return 1

    # Handle --status
    if args.status:
        if args.json:
            print(json.dumps(automation.get_stats(), indent=2, default=str))
        else:
            print_status(automation)
        return 0

    # Handle --tap
    if args.tap:
        print(f"[TAP] Finding and tapping '{args.tap}'...")
        success = automation.tap_element(args.tap)

        if args.json:
            print(json.dumps({"success": success}, indent=2))
        else:
            if success:
                print(f"[OK] Successfully tapped '{args.tap}'")
            else:
                print(f"[FAILED] Could not tap '{args.tap}'")

        return 0 if success else 1

    # Handle --navigate
    if args.navigate:
        try:
            target_state = GameState(args.navigate.lower())
        except ValueError:
            print(f"[ERROR] Invalid state: {args.navigate}")
            print(f"Available states: {', '.join(s.value for s in GameState)}")
            return 1

        print(f"[NAVIGATE] Navigating to {target_state.value}...")
        success = automation.navigate_to(target_state)

        if args.json:
            print(json.dumps({"success": success}, indent=2))
        else:
            if success:
                print(f"[OK] Successfully navigated to {target_state.value}")
            else:
                print(f"[FAILED] Could not reach {target_state.value}")

        return 0 if success else 1

    # Handle --workflow
    if args.workflow:
        if args.workflow not in WORKFLOWS:
            print(f"[ERROR] Unknown workflow: {args.workflow}")
            print(f"Available workflows: {', '.join(WORKFLOWS.keys())}")
            return 1

        workflow = WORKFLOWS[args.workflow]
        print(f"[WORKFLOW] Executing '{args.workflow}' ({len(workflow)} steps)...")

        result = automation.execute_workflow(workflow)

        if args.json:
            print(json.dumps(asdict(result), indent=2))
        else:
            if result.success:
                print(f"\n[OK] Workflow '{args.workflow}' completed successfully")
                print(f"  Time: {result.elapsed_sec:.1f}s")
            else:
                print(f"\n[FAILED] Workflow '{args.workflow}' failed")
                print(f"  Completed: {result.metadata['completed_steps']}/{result.metadata['total_steps']} steps")

        return 0 if result.success else 1

    # No command specified
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
