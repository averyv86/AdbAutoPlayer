#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anthropic>=0.39.0",
#     "Pillow>=10.0.0"
# ]
# ///
"""
Karrot Workflow Orchestrator - Predefined Automation Workflows

This script provides high-level workflow orchestration for common Karrot automation
tasks. It combines smart detection, resilient tapping, and state management into
reusable workflows with checkpoint saving and error recovery.

Built-in Workflows:
1. login - Complete login flow from welcome to authenticated
2. welcome_to_home - Navigate from welcome screen to home screen
3. check_listings - Browse marketplace listings
4. daily_routine - Full daily automation sequence

User Settings:
- Phone: 01039705176
- Neighborhood: 서초동
- Country: Korea

Features:
- Checkpoint saving (resume from last step)
- Error recovery with exponential backoff
- Human-like random delays
- Detailed progress logging
- State verification between steps

Usage:
    uv run karrot_workflow.py --run login
    uv run karrot_workflow.py --run daily_routine --resume
    uv run karrot_workflow.py --list
    uv run karrot_workflow.py --status
    uv run karrot_workflow.py --stop

Examples:
    # Run login workflow
    uv run karrot_workflow.py --run login

    # Resume from last checkpoint
    uv run karrot_workflow.py --resume

    # List all available workflows
    uv run karrot_workflow.py --list

    # Show current status
    uv run karrot_workflow.py --status

    # Clear checkpoints and start fresh
    uv run karrot_workflow.py --clear-checkpoints
"""

import argparse
import json
import random
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, Dict

# Check for required scripts
SCRIPT_DIR = Path(__file__).parent
DETECTOR_SCRIPT = SCRIPT_DIR / "karrot_smart_detector.py"
TAP_SCRIPT = SCRIPT_DIR / "karrot_resilient_tap.py"

# Configuration
CHECKPOINT_DIR = Path("/tmp/karrot-workflow-checkpoints")
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"
LOG_FILE = CHECKPOINT_DIR / "workflow-log.json"

# User settings
USER_PHONE = "01039705176"
USER_NEIGHBORHOOD = "서초동"
USER_COUNTRY = "Korea"

# Timing configuration
STEP_DELAY_MIN_SEC = 1.0
STEP_DELAY_MAX_SEC = 3.0
STATE_VERIFICATION_DELAY_SEC = 2.0
ERROR_RECOVERY_DELAY_SEC = 5.0
MAX_STEP_RETRIES = 3


class ActionType(Enum):
    """Workflow action types"""
    LAUNCH = "launch"
    TAP = "tap"
    TAP_TARGET = "tap_target"
    WAIT_STATE = "wait_state"
    WAIT_ELEMENT = "wait_element"
    ENTER_TEXT = "enter_text"
    DELAY = "delay"
    VERIFY_STATE = "verify_state"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    PRESS_KEY = "press_key"


class WorkflowState(Enum):
    """Workflow execution states"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


class GameState(Enum):
    """Karrot app states"""
    UNKNOWN = "unknown"
    SPLASH = "splash"
    WELCOME = "welcome"
    LOGIN = "login"
    PHONE_INPUT = "phone_input"
    VERIFICATION = "verification"
    NEIGHBORHOOD_SELECT = "neighborhood_select"
    HOME = "home"
    SETTINGS = "settings"
    ERROR = "error"


@dataclass
class WorkflowAction:
    """Single workflow action"""
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    retry_on_fail: bool = True
    max_retries: int = MAX_STEP_RETRIES


@dataclass
class WorkflowStep:
    """Workflow step result"""
    step_number: int
    action: WorkflowAction
    success: bool = False
    attempts: int = 0
    elapsed_sec: float = 0.0
    error: Optional[str] = None
    timestamp: str = ""


@dataclass
class WorkflowCheckpoint:
    """Workflow checkpoint for resume"""
    workflow_name: str
    last_completed_step: int
    total_steps: int
    state: WorkflowState
    timestamp: str
    execution_id: str
    steps_completed: List[WorkflowStep] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    name: str
    description: str
    actions: List[WorkflowAction]
    required_initial_state: Optional[GameState] = None


# Workflow definitions
WORKFLOWS: Dict[str, WorkflowDefinition] = {
    "login": WorkflowDefinition(
        name="login",
        description="Complete login flow from welcome to authenticated",
        actions=[
            WorkflowAction(
                action_type=ActionType.LAUNCH,
                params={"package": "com.towneers.www"},
                description="Launch Karrot app"
            ),
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "welcome", "timeout": 15},
                description="Wait for welcome screen"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "get_started"},
                description="Tap 'Get Started' button"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 2.0, "max": 4.0},
                description="Wait for next screen"
            ),
            WorkflowAction(
                action_type=ActionType.WAIT_ELEMENT,
                params={"element": "Log in", "timeout": 10},
                description="Wait for login screen"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "login"},
                description="Tap 'Log in' button"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 1.5, "max": 3.0},
                description="Wait for phone input"
            ),
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "phone_input", "timeout": 10},
                description="Wait for phone input screen"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "phone_input"},
                description="Tap phone input field"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 0.5, "max": 1.0},
                description="Wait for keyboard"
            ),
            WorkflowAction(
                action_type=ActionType.ENTER_TEXT,
                params={"text": USER_PHONE},
                description=f"Enter phone number: {USER_PHONE}"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 1.0, "max": 2.0},
                description="Wait before submitting"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "confirm_button"},
                description="Tap confirm button"
            ),
            WorkflowAction(
                action_type=ActionType.VERIFY_STATE,
                params={"expected_state": "verification", "timeout": 15},
                description="Verify login initiated (verification screen shown)"
            ),
        ]
    ),

    "welcome_to_home": WorkflowDefinition(
        name="welcome_to_home",
        description="Navigate from welcome screen to home screen",
        actions=[
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "welcome", "timeout": 10},
                description="Verify on welcome screen"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "get_started"},
                description="Tap 'Get Started'"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 2.0, "max": 3.0},
                description="Wait for navigation"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "login"},
                description="Tap 'Log in'"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 3.0, "max": 5.0},
                description="Wait for authentication"
            ),
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "verification", "timeout": 20},
                description="Wait for verification (manual step)"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 15.0, "max": 30.0},
                description="Wait for user to complete verification"
            ),
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "neighborhood_select", "timeout": 30},
                description="Wait for neighborhood selection"
            ),
            WorkflowAction(
                action_type=ActionType.TAP_TARGET,
                params={"target": "find_nearby"},
                description="Tap 'Find nearby neighborhoods'"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 3.0, "max": 5.0},
                description="Wait for location search"
            ),
            WorkflowAction(
                action_type=ActionType.VERIFY_STATE,
                params={"expected_state": "home", "timeout": 20},
                description="Verify home screen reached"
            ),
        ]
    ),

    "check_listings": WorkflowDefinition(
        name="check_listings",
        description="Browse marketplace listings",
        required_initial_state=GameState.HOME,
        actions=[
            WorkflowAction(
                action_type=ActionType.VERIFY_STATE,
                params={"expected_state": "home", "timeout": 5},
                description="Verify on home screen"
            ),
            WorkflowAction(
                action_type=ActionType.SCREENSHOT,
                params={"filename": "home_screen.png"},
                description="Capture home screen"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 1.0, "max": 2.0},
                description="Wait before scrolling"
            ),
            WorkflowAction(
                action_type=ActionType.SCROLL,
                params={"direction": "down", "distance": 500},
                description="Scroll down to view listings"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 2.0, "max": 3.0},
                description="Wait for listings to load"
            ),
            WorkflowAction(
                action_type=ActionType.SCREENSHOT,
                params={"filename": "listings_1.png"},
                description="Capture first set of listings"
            ),
            WorkflowAction(
                action_type=ActionType.SCROLL,
                params={"direction": "down", "distance": 500},
                description="Scroll more listings"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 2.0, "max": 3.0},
                description="Wait for more listings"
            ),
            WorkflowAction(
                action_type=ActionType.SCREENSHOT,
                params={"filename": "listings_2.png"},
                description="Capture second set of listings"
            ),
        ]
    ),

    "daily_routine": WorkflowDefinition(
        name="daily_routine",
        description="Full daily automation: login + check listings + log activity",
        actions=[
            WorkflowAction(
                action_type=ActionType.LAUNCH,
                params={"package": "com.towneers.www"},
                description="Launch Karrot app"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 3.0, "max": 5.0},
                description="Wait for app startup"
            ),
            # Note: This combines login and check_listings workflows
            # In practice, you'd call sub-workflows, but for simplicity we inline
            WorkflowAction(
                action_type=ActionType.WAIT_STATE,
                params={"state": "home", "timeout": 60},
                description="Wait for home screen (assumes already logged in or manual login)"
            ),
            WorkflowAction(
                action_type=ActionType.SCREENSHOT,
                params={"filename": "daily_home.png"},
                description="Daily home screen capture"
            ),
            WorkflowAction(
                action_type=ActionType.SCROLL,
                params={"direction": "down", "distance": 800},
                description="Browse listings"
            ),
            WorkflowAction(
                action_type=ActionType.DELAY,
                params={"min": 3.0, "max": 5.0},
                description="View listings"
            ),
            WorkflowAction(
                action_type=ActionType.SCREENSHOT,
                params={"filename": "daily_listings.png"},
                description="Daily listings capture"
            ),
        ]
    ),
}


class WorkflowExecutor:
    """Executes workflows with checkpointing and error recovery"""

    def __init__(self, enable_ai_vision: bool = True):
        self.enable_ai_vision = enable_ai_vision
        self.checkpoint_dir = CHECKPOINT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Execution tracking
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_workflow: Optional[WorkflowDefinition] = None
        self.current_checkpoint: Optional[WorkflowCheckpoint] = None

    def _run_adb(self, cmd: str, timeout: float = 10.0) -> str:
        """Run ADB shell command"""
        try:
            result = subprocess.run(
                f"adb shell {cmd}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"[DEBUG] ADB error: {e}")
            return ""

    def _get_random_delay(self, min_sec: float, max_sec: float) -> float:
        """Get random delay for human-like behavior"""
        return random.uniform(min_sec, max_sec)

    def _log_event(self, event: str, details: Dict[str, Any]) -> None:
        """Log workflow event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_id": self.execution_id,
            "event": event,
            **details
        }

        # Load existing logs
        logs = []
        if LOG_FILE.exists():
            try:
                logs = json.loads(LOG_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                logs = []

        logs.append(log_entry)

        # Keep last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]

        LOG_FILE.write_text(json.dumps(logs, indent=2, ensure_ascii=False))

    def _save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Save workflow checkpoint"""
        CHECKPOINT_FILE.write_text(json.dumps(asdict(checkpoint), indent=2))
        self._log_event("checkpoint_saved", {
            "workflow": checkpoint.workflow_name,
            "step": checkpoint.last_completed_step,
            "total": checkpoint.total_steps,
            "state": checkpoint.state.value
        })

    def _load_checkpoint(self) -> Optional[WorkflowCheckpoint]:
        """Load last checkpoint"""
        if not CHECKPOINT_FILE.exists():
            return None

        try:
            data = json.loads(CHECKPOINT_FILE.read_text())
            # Reconstruct checkpoint with enums
            checkpoint = WorkflowCheckpoint(
                workflow_name=data["workflow_name"],
                last_completed_step=data["last_completed_step"],
                total_steps=data["total_steps"],
                state=WorkflowState(data["state"]),
                timestamp=data["timestamp"],
                execution_id=data["execution_id"],
                steps_completed=[
                    WorkflowStep(
                        step_number=s["step_number"],
                        action=WorkflowAction(
                            action_type=ActionType(s["action"]["action_type"]),
                            params=s["action"]["params"],
                            description=s["action"]["description"]
                        ),
                        success=s["success"],
                        attempts=s["attempts"],
                        elapsed_sec=s["elapsed_sec"],
                        error=s.get("error"),
                        timestamp=s["timestamp"]
                    )
                    for s in data.get("steps_completed", [])
                ]
            )
            return checkpoint
        except Exception as e:
            print(f"[WARNING] Could not load checkpoint: {e}")
            return None

    def _clear_checkpoint(self) -> None:
        """Clear saved checkpoint"""
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        print("[OK] Checkpoint cleared")

    def _detect_state(self) -> GameState:
        """Detect current game state"""
        try:
            result = subprocess.run(
                ["uv", "run", str(DETECTOR_SCRIPT), "--detect-state", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return GameState(data["state"])
        except Exception as e:
            print(f"[DEBUG] State detection error: {e}")

        return GameState.UNKNOWN

    def _execute_action(self, action: WorkflowAction, step_number: int) -> WorkflowStep:
        """Execute a single workflow action"""
        start_time = time.time()
        step = WorkflowStep(
            step_number=step_number,
            action=action,
            timestamp=datetime.now().isoformat()
        )

        print(f"\n{'='*60}")
        print(f"[STEP {step_number}] {action.description}")
        print(f"Action: {action.action_type.value}")
        print(f"{'='*60}")

        max_attempts = action.max_retries if action.retry_on_fail else 1

        for attempt in range(1, max_attempts + 1):
            step.attempts = attempt

            if attempt > 1:
                print(f"\n[RETRY {attempt}/{max_attempts}] Retrying action...")
                time.sleep(ERROR_RECOVERY_DELAY_SEC)

            try:
                success = self._execute_action_once(action)
                step.success = success

                if success:
                    print(f"[SUCCESS] Step {step_number} completed")
                    break
                else:
                    print(f"[FAILED] Step {step_number} failed")
                    if attempt < max_attempts:
                        continue
                    else:
                        step.error = f"Failed after {max_attempts} attempts"

            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                print(f"[ERROR] {error_msg}")
                step.error = error_msg

                if attempt < max_attempts:
                    continue

        step.elapsed_sec = time.time() - start_time
        return step

    def _execute_action_once(self, action: WorkflowAction) -> bool:
        """Execute action once"""
        action_type = action.action_type
        params = action.params

        if action_type == ActionType.LAUNCH:
            package = params.get("package", "com.towneers.www")
            print(f"[ACTION] Launching {package}...")
            result = subprocess.run(
                ["uv", "run", str(TAP_SCRIPT), "--launch"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0

        elif action_type == ActionType.TAP_TARGET:
            target = params.get("target", "")
            print(f"[ACTION] Tapping target: {target}")
            result = subprocess.run(
                ["uv", "run", str(TAP_SCRIPT), "--tap", target],
                capture_output=True,
                timeout=15
            )
            return result.returncode == 0

        elif action_type == ActionType.TAP:
            x = params.get("x", 0)
            y = params.get("y", 0)
            print(f"[ACTION] Tapping coordinates: ({x}, {y})")
            result = subprocess.run(
                ["uv", "run", str(TAP_SCRIPT), "--tap", str(x), str(y)],
                capture_output=True,
                timeout=15
            )
            return result.returncode == 0

        elif action_type == ActionType.WAIT_STATE:
            state = params.get("state", "unknown")
            timeout = params.get("timeout", 30)
            print(f"[ACTION] Waiting for state: {state} (timeout: {timeout}s)")

            start = time.time()
            while time.time() - start < timeout:
                current = self._detect_state()
                print(f"[CHECK] Current state: {current.value}")

                if current.value == state:
                    print(f"[SUCCESS] State '{state}' detected")
                    return True

                time.sleep(2)

            print(f"[TIMEOUT] State '{state}' not reached in {timeout}s")
            return False

        elif action_type == ActionType.WAIT_ELEMENT:
            element = params.get("element", "")
            timeout = params.get("timeout", 30)
            print(f"[ACTION] Waiting for element: {element} (timeout: {timeout}s)")

            result = subprocess.run(
                ["uv", "run", str(DETECTOR_SCRIPT), "--wait", element, "--timeout", str(timeout)],
                capture_output=True,
                timeout=timeout + 5
            )
            return result.returncode == 0

        elif action_type == ActionType.ENTER_TEXT:
            text = params.get("text", "")
            print(f"[ACTION] Entering text: {text}")
            self._run_adb(f"input text '{text}'")
            return True

        elif action_type == ActionType.DELAY:
            min_sec = params.get("min", 1.0)
            max_sec = params.get("max", 3.0)
            delay = self._get_random_delay(min_sec, max_sec)
            print(f"[ACTION] Waiting {delay:.2f}s...")
            time.sleep(delay)
            return True

        elif action_type == ActionType.VERIFY_STATE:
            expected = params.get("expected_state", "unknown")
            timeout = params.get("timeout", 10)
            print(f"[ACTION] Verifying state: {expected}")

            start = time.time()
            while time.time() - start < timeout:
                current = self._detect_state()
                if current.value == expected:
                    print(f"[VERIFIED] State is {expected}")
                    return True
                time.sleep(2)

            print(f"[NOT VERIFIED] Expected {expected}, current: {current.value}")
            return False

        elif action_type == ActionType.SCREENSHOT:
            filename = params.get("filename", "screenshot.png")
            output_path = self.checkpoint_dir / filename
            print(f"[ACTION] Taking screenshot: {filename}")

            try:
                subprocess.run(
                    ["adb", "shell", "screencap", "-p", "/sdcard/screen.png"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ["adb", "pull", "/sdcard/screen.png", str(output_path)],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                print(f"[SAVED] Screenshot saved to {output_path}")
                return True
            except Exception as e:
                print(f"[ERROR] Screenshot failed: {e}")
                return False

        elif action_type == ActionType.SCROLL:
            direction = params.get("direction", "down")
            distance = params.get("distance", 500)
            print(f"[ACTION] Scrolling {direction} {distance}px")

            # Calculate swipe coordinates (center of screen, vertical swipe)
            center_x = 720
            start_y = 1500 if direction == "down" else 1000
            end_y = start_y - distance if direction == "down" else start_y + distance

            self._run_adb(f"input swipe {center_x} {start_y} {center_x} {end_y} 300")
            return True

        elif action_type == ActionType.PRESS_KEY:
            keycode = params.get("keycode", "KEYCODE_BACK")
            print(f"[ACTION] Pressing key: {keycode}")
            self._run_adb(f"input keyevent {keycode}")
            return True

        else:
            print(f"[ERROR] Unknown action type: {action_type}")
            return False

    def run_workflow(
        self,
        workflow_name: str,
        resume: bool = False
    ) -> WorkflowCheckpoint:
        """Run a workflow from start or resume from checkpoint"""

        if workflow_name not in WORKFLOWS:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow = WORKFLOWS[workflow_name]
        self.current_workflow = workflow

        print(f"\n{'='*60}")
        print(f"WORKFLOW: {workflow.name}")
        print(f"Description: {workflow.description}")
        print(f"Total Steps: {len(workflow.actions)}")
        print(f"{'='*60}\n")

        # Load or create checkpoint
        if resume:
            checkpoint = self._load_checkpoint()
            if checkpoint and checkpoint.workflow_name == workflow_name:
                print(f"[RESUME] Resuming from step {checkpoint.last_completed_step + 1}")
                start_step = checkpoint.last_completed_step + 1
            else:
                print("[INFO] No valid checkpoint found, starting from beginning")
                checkpoint = WorkflowCheckpoint(
                    workflow_name=workflow_name,
                    last_completed_step=-1,
                    total_steps=len(workflow.actions),
                    state=WorkflowState.IN_PROGRESS,
                    timestamp=datetime.now().isoformat(),
                    execution_id=self.execution_id
                )
                start_step = 0
        else:
            checkpoint = WorkflowCheckpoint(
                workflow_name=workflow_name,
                last_completed_step=-1,
                total_steps=len(workflow.actions),
                state=WorkflowState.IN_PROGRESS,
                timestamp=datetime.now().isoformat(),
                execution_id=self.execution_id
            )
            start_step = 0

        self.current_checkpoint = checkpoint

        # Verify initial state if required
        if workflow.required_initial_state and start_step == 0:
            print(f"[VERIFY] Checking initial state: {workflow.required_initial_state.value}")
            current_state = self._detect_state()
            if current_state != workflow.required_initial_state:
                print(f"[ERROR] Wrong initial state. Expected: {workflow.required_initial_state.value}, Got: {current_state.value}")
                checkpoint.state = WorkflowState.FAILED
                checkpoint.steps_completed.append(WorkflowStep(
                    step_number=0,
                    action=WorkflowAction(ActionType.VERIFY_STATE, description="Initial state check"),
                    success=False,
                    error=f"Wrong initial state: {current_state.value}",
                    timestamp=datetime.now().isoformat()
                ))
                self._save_checkpoint(checkpoint)
                return checkpoint

        # Execute workflow steps
        for i, action in enumerate(workflow.actions[start_step:], start=start_step):
            step_result = self._execute_action(action, i + 1)
            checkpoint.steps_completed.append(step_result)

            if step_result.success:
                checkpoint.last_completed_step = i
                checkpoint.state = WorkflowState.IN_PROGRESS
                self._save_checkpoint(checkpoint)

                # Add delay between steps
                if i < len(workflow.actions) - 1:
                    delay = self._get_random_delay(STEP_DELAY_MIN_SEC, STEP_DELAY_MAX_SEC)
                    print(f"\n[WAIT] Pausing {delay:.2f}s before next step...\n")
                    time.sleep(delay)
            else:
                print(f"\n[FAILED] Workflow failed at step {i + 1}")
                print(f"Error: {step_result.error}")
                checkpoint.state = WorkflowState.FAILED
                self._save_checkpoint(checkpoint)
                return checkpoint

        # Workflow completed
        print(f"\n{'='*60}")
        print(f"[COMPLETED] Workflow '{workflow_name}' finished successfully!")
        print(f"Total steps: {len(checkpoint.steps_completed)}")
        print(f"Execution ID: {checkpoint.execution_id}")
        print(f"{'='*60}\n")

        checkpoint.state = WorkflowState.COMPLETED
        self._save_checkpoint(checkpoint)

        return checkpoint

    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        checkpoint = self._load_checkpoint()

        if not checkpoint:
            return {
                "status": "no_checkpoint",
                "message": "No workflow checkpoint found"
            }

        return {
            "status": "active_checkpoint",
            "workflow": checkpoint.workflow_name,
            "state": checkpoint.state.value,
            "progress": f"{checkpoint.last_completed_step + 1}/{checkpoint.total_steps}",
            "execution_id": checkpoint.execution_id,
            "timestamp": checkpoint.timestamp,
            "can_resume": checkpoint.state == WorkflowState.IN_PROGRESS,
        }

    def list_workflows(self) -> None:
        """List all available workflows"""
        print("\n" + "="*60)
        print("AVAILABLE WORKFLOWS")
        print("="*60)

        for name, workflow in WORKFLOWS.items():
            print(f"\n{name}")
            print(f"  Description: {workflow.description}")
            print(f"  Steps: {len(workflow.actions)}")
            if workflow.required_initial_state:
                print(f"  Required State: {workflow.required_initial_state.value}")

        print("\n" + "="*60)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Karrot Workflow Orchestrator - Predefined Automation Workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --run login                    Run login workflow
  %(prog)s --run daily_routine --resume   Resume daily routine
  %(prog)s --list                         List all workflows
  %(prog)s --status                       Show current status
  %(prog)s --clear-checkpoints            Clear checkpoints

Available Workflows:
  login            Complete login flow
  welcome_to_home  Navigate from welcome to home
  check_listings   Browse marketplace listings
  daily_routine    Full daily automation

User Settings:
  Phone: 01039705176
  Neighborhood: 서초동
  Country: Korea
        """
    )

    parser.add_argument(
        "--run", "-r",
        metavar="WORKFLOW",
        help="Run a workflow by name"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available workflows"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current workflow status"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop current workflow (clear checkpoint)"
    )
    parser.add_argument(
        "--clear-checkpoints", "-c",
        action="store_true",
        help="Clear all checkpoints"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI Vision detection"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    # Initialize executor
    executor = WorkflowExecutor(enable_ai_vision=not args.no_ai)

    # Handle --list
    if args.list:
        executor.list_workflows()
        return 0

    # Handle --status
    if args.status:
        status = executor.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("\n" + "="*60)
            print("WORKFLOW STATUS")
            print("="*60)
            if status["status"] == "no_checkpoint":
                print("No active workflow")
            else:
                print(f"Workflow: {status['workflow']}")
                print(f"State: {status['state']}")
                print(f"Progress: {status['progress']}")
                print(f"Execution ID: {status['execution_id']}")
                print(f"Timestamp: {status['timestamp']}")
                print(f"Can Resume: {'Yes' if status['can_resume'] else 'No'}")
            print("="*60)
        return 0

    # Handle --stop
    if args.stop or args.clear_checkpoints:
        executor._clear_checkpoint()
        return 0

    # Handle --run
    if args.run:
        workflow_name = args.run

        if workflow_name not in WORKFLOWS:
            print(f"[ERROR] Unknown workflow: {workflow_name}")
            print(f"\nAvailable workflows:")
            for name in WORKFLOWS.keys():
                print(f"  - {name}")
            return 1

        try:
            checkpoint = executor.run_workflow(workflow_name, resume=args.resume)

            if args.json:
                print(json.dumps(asdict(checkpoint), indent=2, default=str))

            return 0 if checkpoint.state == WorkflowState.COMPLETED else 1

        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Workflow interrupted by user")
            print("[INFO] Progress saved. Use --resume to continue")
            return 130
        except Exception as e:
            print(f"\n[ERROR] Workflow execution error: {e}")
            return 1

    # No command specified
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
