"""AFK Journey Action Recording Integration.

Provides action recording and playback for AFKJourney automation.
Records game actions for debugging, analysis, and replay.

Features:
- Record game actions (taps, swipes, detections, checkpoints)
- Playback recorded actions with timing preservation
- Action filtering and analysis
- Integration with checkpoint and YOLO systems
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any, List, Iterator
from dataclasses import dataclass
from time import time
from datetime import datetime

# Import ActionRecorder and ActionPlayer from Phase 10
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent / ".claude" / "skills" / "moai-domain-adb" / "scripts"))
    from adb_action_recorder import (
        ActionRecorder,
        ActionPlayer,
        ActionRecording,
        AutomationAction,
        ActionType,
    )
except ImportError:
    logging.warning("Could not import action recorder from Phase 10. Recording features disabled.")
    ActionRecorder = None
    ActionPlayer = None
    ActionRecording = None
    AutomationAction = None
    ActionType = None


@dataclass
class ActionStatistics:
    """Statistics for recorded actions."""
    total_actions: int = 0
    taps: int = 0
    swipes: int = 0
    waits: int = 0
    detections: int = 0
    checkpoints: int = 0
    total_duration: float = 0.0
    avg_action_time: float = 0.0


class AFKJourneyActionIntegration:
    """Mixin for adding action recording to AFKJourney.

    Usage:
        class AFKJourneyWithRecording(AFKJourneyBase, AFKJourneyActionIntegration):
            def __init__(self):
                super().__init__()
                self._init_action_system()
    """

    def __init__(self):
        """Initialize action recording system."""
        self.action_recorder: Optional[ActionRecorder] = None
        self.action_player: Optional[ActionPlayer] = None
        self.recording_enabled: bool = False
        self.playback_mode: bool = False
        self.action_stats = ActionStatistics()
        self._action_history: List[AutomationAction] = []
        self._max_history: int = 1000

    def _init_action_system(self, game: str = "afk-journey", device: str = "emulator-5554") -> bool:
        """Initialize action recording system.

        Args:
            game: Game identifier
            device: Device identifier

        Returns:
            True if initialized successfully
        """
        if not ActionRecorder or not ActionPlayer:
            logging.warning("⚠️ Action recorder not available. Recording disabled.")
            self.recording_enabled = False
            return False

        try:
            self.action_recorder = ActionRecorder(game=game, device=device)
            self.action_player = ActionPlayer()
            self.recording_enabled = True
            logging.info(f"✅ Action recording system initialized for {game}")
            return True
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize action recording: {e}")
            self.recording_enabled = False
            return False

    def start_recording(self) -> bool:
        """Start recording actions.

        Returns:
            True if recording started successfully
        """
        if not self.action_recorder:
            logging.warning("Action recorder not initialized")
            return False

        try:
            success = self.action_recorder.start_recording()
            if success:
                logging.info("✅ Action recording started")
            return success
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> Optional[ActionRecording]:
        """Stop recording and return the recording.

        Returns:
            ActionRecording object if successful, None otherwise
        """
        if not self.action_recorder:
            return None

        try:
            recording = self.action_recorder.stop_recording()
            if recording:
                # Update statistics
                self._update_action_stats(recording)
                logging.info(f"✅ Recording stopped: {len(recording.actions)} actions")
            return recording
        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")
            return None

    def record_tap(self, x: int, y: int, duration: float = 0.1) -> bool:
        """Record a tap action.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Tap duration in seconds

        Returns:
            True if recorded successfully
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            success = self.action_recorder.record_tap(x, y, duration)
            if success:
                self.action_stats.taps += 1
            return success
        except Exception as e:
            logging.warning(f"Failed to record tap: {e}")
            return False

    def record_swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: float = 0.5
    ) -> bool:
        """Record a swipe action.

        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration: Swipe duration in seconds

        Returns:
            True if recorded successfully
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            success = self.action_recorder.record_swipe(x1, y1, x2, y2, duration)
            if success:
                self.action_stats.swipes += 1
            return success
        except Exception as e:
            logging.warning(f"Failed to record swipe: {e}")
            return False

    def record_wait(self, duration: float, condition: Optional[str] = None) -> bool:
        """Record a wait action.

        Args:
            duration: Wait duration in seconds
            condition: Optional condition description

        Returns:
            True if recorded successfully
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            success = self.action_recorder.record_wait(duration, condition)
            if success:
                self.action_stats.waits += 1
            return success
        except Exception as e:
            logging.warning(f"Failed to record wait: {e}")
            return False

    def record_detection(
        self,
        detection_type: str,  # "template" or "yolo"
        class_name: str,
        confidence: float,
        location: Optional[List[int]] = None
    ) -> bool:
        """Record a detection action.

        Args:
            detection_type: "template" or "yolo"
            class_name: Detected class name
            confidence: Detection confidence
            location: Optional detection location [x, y, w, h]

        Returns:
            True if recorded successfully
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            success = self.action_recorder.record_action(
                f"{detection_type}_detect",
                {
                    "class_name": class_name,
                    "confidence": confidence,
                    "location": location,
                }
            )
            if success:
                self.action_stats.detections += 1
            return success
        except Exception as e:
            logging.warning(f"Failed to record detection: {e}")
            return False

    def record_checkpoint(self, checkpoint_id: str, description: str = "") -> bool:
        """Record a checkpoint action.

        Args:
            checkpoint_id: Checkpoint identifier
            description: Optional description

        Returns:
            True if recorded successfully
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            success = self.action_recorder.record_checkpoint(checkpoint_id, description)
            if success:
                self.action_stats.checkpoints += 1
            return success
        except Exception as e:
            logging.warning(f"Failed to record checkpoint: {e}")
            return False

    def save_recording(self, output_path: str) -> bool:
        """Save recording to file.

        Args:
            output_path: Path to save recording (YAML format)

        Returns:
            True if saved successfully
        """
        if not self.action_recorder:
            return False

        try:
            success = self.action_recorder.save_recording(output_path)
            if success:
                logging.info(f"✅ Recording saved to {output_path}")
            return success
        except Exception as e:
            logging.error(f"Failed to save recording: {e}")
            return False

    def load_recording(self, recording_path: str) -> bool:
        """Load recording from file.

        Args:
            recording_path: Path to recording file (YAML format)

        Returns:
            True if loaded successfully
        """
        if not self.action_player:
            return False

        try:
            success = self.action_player.load_recording(recording_path)
            if success:
                logging.info(f"✅ Recording loaded from {recording_path}")
                if self.action_player.recording:
                    self._update_action_stats(self.action_player.recording)
            return success
        except Exception as e:
            logging.error(f"Failed to load recording: {e}")
            return False

    def playback_recording(self, device: Optional[str] = None) -> Dict[str, Any]:
        """Playback loaded recording.

        Args:
            device: Optional device identifier

        Returns:
            Playback result with statistics
        """
        if not self.action_player or not self.action_player.recording:
            return {"success": False, "error": "No recording loaded"}

        try:
            logging.info("▶️ Starting playback...")
            result = self.action_player.play(device=device)
            logging.info(f"✅ Playback complete: {result['executed']}/{result['total_actions']} actions")
            return result
        except Exception as e:
            logging.error(f"Playback failed: {e}")
            return {"success": False, "error": str(e)}

    def playback_step_by_step(self, device: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Playback recording with step-by-step control.

        Args:
            device: Optional device identifier

        Yields:
            Step results
        """
        if not self.action_player or not self.action_player.recording:
            yield {"error": "No recording loaded"}
            return

        try:
            for step_result in self.action_player.play_step_by_step(device=device):
                yield step_result
        except Exception as e:
            yield {"error": str(e)}

    def get_action_stats(self) -> Dict[str, Any]:
        """Get action statistics.

        Returns:
            Dictionary with action statistics
        """
        return {
            "total_actions": self.action_stats.total_actions,
            "taps": self.action_stats.taps,
            "swipes": self.action_stats.swipes,
            "waits": self.action_stats.waits,
            "detections": self.action_stats.detections,
            "checkpoints": self.action_stats.checkpoints,
            "total_duration": round(self.action_stats.total_duration, 2),
            "avg_action_time": round(self.action_stats.avg_action_time, 3),
        }

    def report_action_stats(self) -> None:
        """Log action statistics to console."""
        stats = self.get_action_stats()
        logging.info("=" * 60)
        logging.info("Action Recording Statistics:")
        logging.info(f"  Total Actions: {stats['total_actions']}")
        logging.info(f"  Taps: {stats['taps']}")
        logging.info(f"  Swipes: {stats['swipes']}")
        logging.info(f"  Waits: {stats['waits']}")
        logging.info(f"  Detections: {stats['detections']}")
        logging.info(f"  Checkpoints: {stats['checkpoints']}")
        logging.info(f"  Total Duration: {stats['total_duration']:.2f}s")
        logging.info(f"  Avg Action Time: {stats['avg_action_time']*1000:.1f}ms")
        logging.info("=" * 60)

    def filter_actions(
        self,
        action_types: Optional[List[str]] = None,
        min_timestamp: Optional[float] = None,
        max_timestamp: Optional[float] = None,
    ) -> List[AutomationAction]:
        """Filter actions by type and timestamp.

        Args:
            action_types: Optional list of action types to include
            min_timestamp: Optional minimum timestamp
            max_timestamp: Optional maximum timestamp

        Returns:
            Filtered list of actions
        """
        if not self.action_player or not self.action_player.recording:
            return []

        actions = self.action_player.recording.actions
        filtered = actions

        if action_types:
            filtered = [a for a in filtered if a.action_type in action_types]

        if min_timestamp is not None:
            filtered = [a for a in filtered if a.timestamp >= min_timestamp]

        if max_timestamp is not None:
            filtered = [a for a in filtered if a.timestamp <= max_timestamp]

        return filtered

    def get_recording_duration(self) -> Optional[float]:
        """Get total duration of loaded recording.

        Returns:
            Duration in seconds, or None if no recording loaded
        """
        if not self.action_player or not self.action_player.recording:
            return None

        return self.action_player.recording.metadata.duration

    def reset_action_stats(self) -> None:
        """Reset action statistics."""
        self.action_stats = ActionStatistics()

    def _update_action_stats(self, recording: ActionRecording) -> None:
        """Update statistics from recording.

        Args:
            recording: ActionRecording to analyze
        """
        self.action_stats.total_actions = len(recording.actions)
        self.action_stats.total_duration = recording.metadata.duration

        # Count action types
        for action in recording.actions:
            if action.action_type == "tap":
                self.action_stats.taps += 1
            elif action.action_type == "swipe":
                self.action_stats.swipes += 1
            elif action.action_type == "wait":
                self.action_stats.waits += 1
            elif action.action_type in ["template_detect", "yolo_detect"]:
                self.action_stats.detections += 1
            elif action.action_type == "checkpoint":
                self.action_stats.checkpoints += 1

        # Calculate average action time
        if self.action_stats.total_actions > 0:
            self.action_stats.avg_action_time = (
                self.action_stats.total_duration / self.action_stats.total_actions
            )
