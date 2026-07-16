"""Multi-Game Workflow Orchestrator.

Coordinates automation across multiple games (Guitar Girl, AFKJourney) with:
- Sequential and parallel game switching
- Checkpoint-based state management
- Cross-game error recovery
- Unified performance monitoring
- Session recording and analysis

This module executes TOON-defined workflows from multi-game-automation.toon.yaml
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
from time import time, sleep
from enum import Enum


class GameType(Enum):
    """Supported game types."""
    GUITAR_GIRL = "guitar_girl"
    AFK_JOURNEY = "afk_journey"


class WorkflowPhase(Enum):
    """Workflow execution phases."""
    INITIALIZE = "initialize"
    EXECUTE = "execute"
    MONITOR = "monitor"
    COMPLETE = "complete"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    phase: WorkflowPhase = WorkflowPhase.INITIALIZE
    total_iterations: int = 0
    completed_iterations: int = 0
    errors: int = 0
    checkpoints_saved: int = 0
    sessions_recorded: int = 0
    total_duration: float = 0.0


class MultiGameOrchestrator:
    """Orchestrates multi-game automation workflows.

    Usage:
        orchestrator = MultiGameOrchestrator()
        orchestrator.load_workflow_definitions("multi-game-automation.toon.yaml")
        orchestrator.execute_workflow("multi_game_daily_routine")
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.current_game: Optional[GameType] = None
        self.active_workflows: Dict[str, WorkflowMetrics] = {}
        self.workflow_definitions: Dict[str, Dict[str, Any]] = {}
        self.game_instances: Dict[str, Any] = {}
        self.is_running: bool = False

        logging.info("✅ Multi-Game Orchestrator initialized")

    def load_workflow_definitions(self, workflow_file: str) -> bool:
        """Load TOON workflow definitions from file.

        Args:
            workflow_file: Path to TOON workflow file

        Returns:
            True if loaded successfully
        """
        try:
            workflow_path = Path(workflow_file)
            if not workflow_path.exists():
                logging.error(f"Workflow file not found: {workflow_file}")
                return False

            with open(workflow_path, 'r') as f:
                data = yaml.safe_load(f)

            if 'workflows' not in data:
                logging.error("No 'workflows' section in workflow file")
                return False

            self.workflow_definitions = data['workflows']
            logging.info(f"✅ Loaded {len(self.workflow_definitions)} workflow definitions")
            return True

        except Exception as e:
            logging.error(f"Failed to load workflow definitions: {e}")
            return False

    def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow by ID.

        Args:
            workflow_id: ID of workflow to execute
            parameters: Optional runtime parameters

        Returns:
            Execution result with metrics
        """
        if workflow_id not in self.workflow_definitions:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}"
            }

        workflow = self.workflow_definitions[workflow_id]
        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            start_time=time()
        )

        self.active_workflows[workflow_id] = metrics

        try:
            logging.info(f"▶️ Starting workflow: {workflow['name']}")
            self.is_running = True

            # Execute workflow phases
            if 'stages' in workflow:
                self._execute_stages(workflow['stages'], metrics)

            if 'phases' in workflow:
                self._execute_phases(workflow['phases'], metrics)

            if 'workflow' in workflow:
                self._execute_workflow_steps(workflow['workflow']['steps'], metrics)

            metrics.end_time = time()
            metrics.phase = WorkflowPhase.COMPLETE
            metrics.total_duration = metrics.end_time - metrics.start_time

            logging.info(f"✅ Workflow completed: {workflow['name']}")
            return {
                "success": True,
                "workflow_id": workflow_id,
                "metrics": {
                    "duration": metrics.total_duration,
                    "iterations": metrics.completed_iterations,
                    "errors": metrics.errors,
                    "checkpoints": metrics.checkpoints_saved,
                    "sessions": metrics.sessions_recorded,
                }
            }

        except Exception as e:
            logging.error(f"Workflow failed: {e}")
            metrics.phase = WorkflowPhase.ERROR_RECOVERY
            metrics.errors += 1
            return {
                "success": False,
                "error": str(e),
                "metrics": {
                    "iterations": metrics.completed_iterations,
                    "errors": metrics.errors,
                }
            }

        finally:
            self.is_running = False

    def switch_game(self, game: str) -> bool:
        """Switch to a different game.

        Args:
            game: Game identifier ("guitar_girl" or "afk_journey")

        Returns:
            True if successful
        """
        try:
            game_type = GameType(game)
            self.current_game = game_type
            logging.info(f"🎮 Switched to game: {game}")
            return True
        except ValueError:
            logging.error(f"Unknown game: {game}")
            return False

    def get_current_game(self) -> Optional[str]:
        """Get currently active game.

        Returns:
            Game identifier or None
        """
        return self.current_game.value if self.current_game else None

    def save_checkpoint(
        self,
        checkpoint_id: str,
        description: str = "",
        game: Optional[str] = None
    ) -> bool:
        """Save checkpoint for specified game.

        Args:
            checkpoint_id: Checkpoint identifier
            description: Optional description
            game: Optional game (uses current if not specified)

        Returns:
            True if successful
        """
        target_game = game or self.get_current_game()
        if not target_game:
            logging.error("No game selected for checkpoint")
            return False

        try:
            game_instance = self.game_instances.get(target_game)
            if game_instance and hasattr(game_instance, 'save_checkpoint'):
                success = game_instance.save_checkpoint(checkpoint_id, description)
                if success:
                    if target_game in self.active_workflows:
                        for metrics in self.active_workflows.values():
                            metrics.checkpoints_saved += 1
                    logging.info(f"✅ Checkpoint saved: {checkpoint_id}")
                return success

            logging.warning(f"Game instance not ready: {target_game}")
            return False

        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
            return False

    def load_checkpoint(self, checkpoint_id: str, game: Optional[str] = None) -> bool:
        """Load checkpoint for specified game.

        Args:
            checkpoint_id: Checkpoint identifier to load
            game: Optional game (uses current if not specified)

        Returns:
            True if successful
        """
        target_game = game or self.get_current_game()
        if not target_game:
            logging.error("No game selected for checkpoint loading")
            return False

        try:
            game_instance = self.game_instances.get(target_game)
            if game_instance and hasattr(game_instance, 'load_checkpoint'):
                success = game_instance.load_checkpoint(checkpoint_id)
                if success:
                    logging.info(f"✅ Checkpoint loaded: {checkpoint_id}")
                return success

            logging.warning(f"Game instance not ready: {target_game}")
            return False

        except Exception as e:
            logging.error(f"Failed to load checkpoint: {e}")
            return False

    def record_session(self, game: Optional[str] = None) -> bool:
        """Start recording session for specified game.

        Args:
            game: Optional game (uses current if not specified)

        Returns:
            True if successful
        """
        target_game = game or self.get_current_game()
        if not target_game:
            logging.error("No game selected for recording")
            return False

        try:
            game_instance = self.game_instances.get(target_game)
            if game_instance and hasattr(game_instance, 'start_recording'):
                success = game_instance.start_recording()
                if success:
                    logging.info(f"🎬 Recording started: {target_game}")
                return success

            logging.warning(f"Game instance not ready: {target_game}")
            return False

        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            return False

    def save_session(
        self,
        session_path: str,
        game: Optional[str] = None
    ) -> bool:
        """Save recorded session for specified game.

        Args:
            session_path: Path to save session file
            game: Optional game (uses current if not specified)

        Returns:
            True if successful
        """
        target_game = game or self.get_current_game()
        if not target_game:
            logging.error("No game selected for session saving")
            return False

        try:
            game_instance = self.game_instances.get(target_game)
            if game_instance and hasattr(game_instance, 'save_recording'):
                success = game_instance.save_recording(session_path)
                if success:
                    if target_game in self.active_workflows:
                        for metrics in self.active_workflows.values():
                            metrics.sessions_recorded += 1
                    logging.info(f"✅ Session saved: {session_path}")
                return success

            logging.warning(f"Game instance not ready: {target_game}")
            return False

        except Exception as e:
            logging.error(f"Failed to save session: {e}")
            return False

    def get_workflow_metrics(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Metrics dictionary or None
        """
        if workflow_id not in self.active_workflows:
            return None

        metrics = self.active_workflows[workflow_id]
        return {
            "workflow_id": metrics.workflow_id,
            "phase": metrics.phase.value,
            "start_time": metrics.start_time,
            "end_time": metrics.end_time,
            "total_duration": metrics.total_duration,
            "iterations": metrics.completed_iterations,
            "errors": metrics.errors,
            "checkpoints_saved": metrics.checkpoints_saved,
            "sessions_recorded": metrics.sessions_recorded,
        }

    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows.

        Returns:
            List of workflow information dictionaries
        """
        workflows = []
        for workflow_id, workflow in self.workflow_definitions.items():
            workflows.append({
                "id": workflow_id,
                "name": workflow.get('name', 'Unknown'),
                "description": workflow.get('description', ''),
                "games": workflow.get('games', workflow.get('game', '')),
                "duration_estimate": workflow.get('duration_estimate', 'Unknown'),
            })
        return workflows

    def _execute_stages(
        self,
        stages: Dict[str, Any],
        metrics: WorkflowMetrics
    ) -> None:
        """Execute workflow stages.

        Args:
            stages: Stages to execute
            metrics: Metrics object to update
        """
        for stage_name, stage_tasks in stages.items():
            logging.info(f"📋 Executing stage: {stage_name}")
            metrics.phase = WorkflowPhase.EXECUTE

            if isinstance(stage_tasks, list):
                for task in stage_tasks:
                    self._execute_task(task, metrics)

    def _execute_phases(
        self,
        phases: Dict[str, Any],
        metrics: WorkflowMetrics
    ) -> None:
        """Execute workflow phases in order.

        Args:
            phases: Phases to execute
            metrics: Metrics object to update
        """
        # Sort phases by order if available
        sorted_phases = sorted(
            phases.items(),
            key=lambda x: x[1].get('order', 0)
        )

        for phase_name, phase_config in sorted_phases:
            logging.info(f"🔹 Executing phase: {phase_name}")
            metrics.phase = WorkflowPhase.EXECUTE

            if 'steps' in phase_config:
                for step in phase_config['steps']:
                    self._execute_task(step, metrics)

    def _execute_workflow_steps(
        self,
        steps: List[Dict[str, Any]],
        metrics: WorkflowMetrics
    ) -> None:
        """Execute workflow steps.

        Args:
            steps: Steps to execute
            metrics: Metrics object to update
        """
        for step in steps:
            self._execute_task(step, metrics)

    def _execute_task(
        self,
        task: Dict[str, Any],
        metrics: WorkflowMetrics
    ) -> None:
        """Execute a single task.

        Args:
            task: Task configuration to execute
            metrics: Metrics object to update
        """
        task_type = task.get('task', 'unknown')
        params = task.get('params', {})

        try:
            if task_type == 'switch_game':
                self.switch_game(params.get('game', ''))

            elif task_type == 'record_checkpoint':
                self.save_checkpoint(
                    params.get('checkpoint_id', ''),
                    params.get('description', '')
                )

            elif task_type == 'save_checkpoint':
                self.save_checkpoint(
                    params.get('checkpoint_id', ''),
                    params.get('description', '')
                )

            elif task_type == 'save_session':
                self.save_session(params.get('recording_path', ''))

            elif task_type == 'loop':
                iterations = params.get('iterations', 100)
                for i in range(iterations):
                    metrics.completed_iterations += 1
                    if (i + 1) % 100 == 0:
                        logging.debug(f"  Iteration {i + 1}/{iterations}")

            elif task_type == 'wait':
                duration = params.get('duration', 1.0)
                sleep(duration)

            logging.debug(f"  ✓ Task completed: {task_type}")

        except Exception as e:
            metrics.errors += 1
            logging.error(f"Task failed ({task_type}): {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate execution report.

        Returns:
            Report dictionary with all metrics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "active_workflows": list(self.active_workflows.keys()),
            "current_game": self.get_current_game(),
            "metrics": {
                workflow_id: self.get_workflow_metrics(workflow_id)
                for workflow_id in self.active_workflows.keys()
            },
            "summary": {
                "total_workflows_executed": len(self.active_workflows),
                "total_iterations": sum(
                    m.completed_iterations
                    for m in self.active_workflows.values()
                ),
                "total_errors": sum(
                    m.errors for m in self.active_workflows.values()
                ),
                "total_checkpoints": sum(
                    m.checkpoints_saved
                    for m in self.active_workflows.values()
                ),
            }
        }
