"""Workflow utilities and helper functions for multi-game orchestration.

Provides:
- Workflow validation and error checking
- Configuration management
- Performance profiling
- State management utilities
- Workflow composition helpers
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import time


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""

    max_retries: int = 3
    retry_delay: float = 5.0
    checkpoint_interval: int = 600  # Every 10 minutes
    enable_monitoring: bool = True
    enable_recording: bool = True
    enable_checkpoints: bool = True
    max_duration: Optional[float] = None  # None = unlimited
    error_recovery_strategy: str = "checkpoint"  # "checkpoint" or "restart"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "checkpoint_interval": self.checkpoint_interval,
            "enable_monitoring": self.enable_monitoring,
            "enable_recording": self.enable_recording,
            "enable_checkpoints": self.enable_checkpoints,
            "max_duration": self.max_duration,
            "error_recovery_strategy": self.error_recovery_strategy,
        }


class WorkflowValidator:
    """Validates workflow definitions and configurations."""

    @staticmethod
    def validate_workflow_definition(workflow: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a workflow definition.

        Args:
            workflow: Workflow definition dict

        Returns:
            (is_valid, error_message)
        """
        required_fields = ["name", "description"]

        for field in required_fields:
            if field not in workflow:
                return False, f"Missing required field: {field}"

        if not isinstance(workflow["name"], str) or not workflow["name"]:
            return False, "Name must be non-empty string"

        if not isinstance(workflow["description"], str):
            return False, "Description must be string"

        # Validate games field if present
        if "games" in workflow:
            games = workflow.get("games")
            if isinstance(games, str):
                if games not in ["guitar_girl", "afk_journey", "both"]:
                    return False, f"Invalid game: {games}"
            elif isinstance(games, list):
                for game in games:
                    if game not in ["guitar_girl", "afk_journey"]:
                        return False, f"Invalid game: {game}"
            else:
                return False, "Games must be string or list"

        # Validate stages/phases/workflow
        if "stages" not in workflow and "phases" not in workflow and "workflow" not in workflow:
            return False, "Must contain 'stages', 'phases', or 'workflow'"

        return True, None

    @staticmethod
    def validate_config(config: WorkflowConfig) -> tuple[bool, Optional[str]]:
        """
        Validate workflow configuration.

        Args:
            config: WorkflowConfig instance

        Returns:
            (is_valid, error_message)
        """
        if config.max_retries < 0:
            return False, "max_retries must be >= 0"

        if config.retry_delay < 0:
            return False, "retry_delay must be >= 0"

        if config.checkpoint_interval < 60:
            return False, "checkpoint_interval must be >= 60 seconds"

        if config.error_recovery_strategy not in ["checkpoint", "restart"]:
            return False, f"Invalid error_recovery_strategy: {config.error_recovery_strategy}"

        return True, None


class WorkflowProfiler:
    """Profiles workflow execution performance."""

    def __init__(self):
        """Initialize profiler."""
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}

    def start(self, name: str) -> None:
        """Start profiling a workflow."""
        self.start_times[name] = time.time()

    def stop(self, name: str) -> float:
        """Stop profiling and return duration."""
        if name not in self.start_times:
            logging.warning(f"Profiler: No start time for {name}")
            return 0.0

        duration = time.time() - self.start_times[name]

        if name not in self.metrics:
            self.metrics[name] = []

        self.metrics[name].append(duration)
        del self.start_times[name]

        return duration

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a workflow."""
        if name not in self.metrics or not self.metrics[name]:
            return {}

        times = self.metrics[name]
        return {
            "count": len(times),
            "total": sum(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all workflows."""
        return {name: self.get_stats(name) for name in self.metrics.keys()}


class WorkflowStateManager:
    """Manages workflow state and persistence."""

    def __init__(self, state_dir: str = ".moai/state"):
        """Initialize state manager."""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = {}

    def save_state(self, workflow_id: str, state: Dict[str, Any]) -> bool:
        """
        Save workflow state to file.

        Args:
            workflow_id: Workflow identifier
            state: State dictionary

        Returns:
            True if successful
        """
        try:
            state_file = self.state_dir / f"{workflow_id}_state.json"
            with open(state_file, 'w') as f:
                json.dump({
                    "workflow_id": workflow_id,
                    "timestamp": datetime.now().isoformat(),
                    "state": state,
                }, f, indent=2)

            self.state[workflow_id] = state
            logging.info(f"✅ State saved for workflow: {workflow_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to save state: {e}")
            return False

    def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from file.

        Args:
            workflow_id: Workflow identifier

        Returns:
            State dictionary or None
        """
        try:
            state_file = self.state_dir / f"{workflow_id}_state.json"
            if not state_file.exists():
                return None

            with open(state_file, 'r') as f:
                data = json.load(f)

            self.state[workflow_id] = data.get("state", {})
            logging.info(f"✅ State loaded for workflow: {workflow_id}")
            return self.state[workflow_id]

        except Exception as e:
            logging.error(f"Failed to load state: {e}")
            return None

    def get_state(self, workflow_id: str) -> Dict[str, Any]:
        """Get current state for a workflow."""
        return self.state.get(workflow_id, {})

    def update_state(self, workflow_id: str, key: str, value: Any) -> None:
        """Update a state value."""
        if workflow_id not in self.state:
            self.state[workflow_id] = {}

        self.state[workflow_id][key] = value


class WorkflowComposer:
    """Composes complex workflows from simpler building blocks."""

    def __init__(self):
        """Initialize composer."""
        self.workflows: Dict[str, Dict[str, Any]] = {}

    def register_workflow(self, name: str, workflow: Dict[str, Any]) -> bool:
        """Register a workflow template."""
        try:
            is_valid, error = WorkflowValidator.validate_workflow_definition(workflow)
            if not is_valid:
                logging.error(f"Invalid workflow: {error}")
                return False

            self.workflows[name] = workflow
            logging.info(f"✅ Registered workflow: {name}")
            return True

        except Exception as e:
            logging.error(f"Failed to register workflow: {e}")
            return False

    def compose_sequential(self, name: str, workflow_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Compose a sequential workflow from multiple workflows.

        Args:
            name: Name of composed workflow
            workflow_ids: List of workflow IDs to execute in sequence

        Returns:
            Composed workflow definition or None
        """
        if not all(wf_id in self.workflows for wf_id in workflow_ids):
            logging.error("One or more workflows not found")
            return None

        composed = {
            "name": name,
            "description": f"Sequential composition of {len(workflow_ids)} workflows",
            "type": "sequential",
            "workflows": workflow_ids,
            "created_at": datetime.now().isoformat(),
        }

        return composed

    def compose_parallel(self, name: str, workflow_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Compose a parallel workflow from multiple workflows.

        Args:
            name: Name of composed workflow
            workflow_ids: List of workflow IDs to execute in parallel

        Returns:
            Composed workflow definition or None
        """
        if not all(wf_id in self.workflows for wf_id in workflow_ids):
            logging.error("One or more workflows not found")
            return None

        composed = {
            "name": name,
            "description": f"Parallel composition of {len(workflow_ids)} workflows",
            "type": "parallel",
            "workflows": workflow_ids,
            "created_at": datetime.now().isoformat(),
        }

        return composed

    def compose_conditional(
        self,
        name: str,
        condition: str,
        true_workflows: List[str],
        false_workflows: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Compose a conditional workflow.

        Args:
            name: Name of composed workflow
            condition: Condition expression
            true_workflows: Workflows to execute if condition is true
            false_workflows: Workflows to execute if condition is false

        Returns:
            Composed workflow definition or None
        """
        all_ids = true_workflows + false_workflows
        if not all(wf_id in self.workflows for wf_id in all_ids):
            logging.error("One or more workflows not found")
            return None

        composed = {
            "name": name,
            "description": f"Conditional composition",
            "type": "conditional",
            "condition": condition,
            "true_workflows": true_workflows,
            "false_workflows": false_workflows,
            "created_at": datetime.now().isoformat(),
        }

        return composed


class WorkflowRetryManager:
    """Manages retry logic for failed workflows."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 5.0):
        """Initialize retry manager."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_history: Dict[str, List[Dict[str, Any]]] = {}

    def attempt(self, workflow_id: str, func: Callable, *args, **kwargs) -> tuple[bool, Optional[Exception]]:
        """
        Attempt to execute a function with retries.

        Args:
            workflow_id: Workflow identifier
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            (success, exception)
        """
        if workflow_id not in self.retry_history:
            self.retry_history[workflow_id] = []

        last_exception = None

        for attempt_num in range(self.max_retries + 1):
            try:
                logging.info(f"🔄 Attempt {attempt_num + 1}/{self.max_retries + 1} for {workflow_id}")
                func(*args, **kwargs)

                self.retry_history[workflow_id].append({
                    "attempt": attempt_num + 1,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                })

                return True, None

            except Exception as e:
                last_exception = e
                self.retry_history[workflow_id].append({
                    "attempt": attempt_num + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                })

                if attempt_num < self.max_retries:
                    logging.warning(f"⚠️ Attempt failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

        return False, last_exception

    def get_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get retry history for a workflow."""
        return self.retry_history.get(workflow_id, [])


class WorkflowLogger:
    """Enhanced logging for workflow execution."""

    def __init__(self, log_dir: str = ".moai/logs/workflows"):
        """Initialize logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_workflow_start(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log workflow start."""
        message = f"▶️ Workflow started: {workflow_id}"
        if metadata:
            message += f" | {metadata}"

        logging.info(message)
        self._write_log_file(workflow_id, f"START | {message}")

    def log_workflow_complete(self, workflow_id: str, result: Dict[str, Any]) -> None:
        """Log workflow completion."""
        message = f"✅ Workflow completed: {workflow_id}"
        logging.info(message)
        self._write_log_file(workflow_id, f"COMPLETE | {message} | {result}")

    def log_workflow_error(self, workflow_id: str, error: Exception) -> None:
        """Log workflow error."""
        message = f"❌ Workflow error: {workflow_id} | {str(error)}"
        logging.error(message)
        self._write_log_file(workflow_id, f"ERROR | {message}")

    def log_checkpoint(self, workflow_id: str, checkpoint_id: str, description: str = "") -> None:
        """Log checkpoint."""
        message = f"📂 Checkpoint: {checkpoint_id}"
        if description:
            message += f" | {description}"

        logging.info(message)
        self._write_log_file(workflow_id, f"CHECKPOINT | {message}")

    def _write_log_file(self, workflow_id: str, message: str) -> None:
        """Write message to workflow log file."""
        try:
            log_file = self.log_dir / f"{workflow_id}.log"
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} | {message}\n")
        except Exception as e:
            logging.error(f"Failed to write log file: {e}")
