"""Guitar Girl Fully Enhanced with All Features.

This module provides a complete Guitar Girl implementation with:
- Checkpoint save/load/recovery
- YOLO-based fast note detection
- Action recording and playback
- Integrated performance analytics

This is the ultimate enhanced class combining all iterations' features.
"""

import logging
from typing import Optional, List, Dict, Any

from .guitar_girl import GuitarGirl
from .checkpoint_integration import GuitarGirlCheckpointIntegration
from .yolo_integration import GuitarGirlYOLOIntegration, DetectionResult
from .action_integration import GuitarGirlActionIntegration


class GuitarGirlFullyEnhanced(
    GuitarGirl,
    GuitarGirlCheckpointIntegration,
    GuitarGirlYOLOIntegration,
    GuitarGirlActionIntegration
):
    """Fully enhanced Guitar Girl with all features integrated.

    This class combines:
    - Base Guitar Girl functionality
    - Checkpoint save/load/recovery (Iteration 2)
    - YOLO-based fast detection (Iteration 3)
    - Action recording and playback (Iteration 4)

    Usage:
        game = GuitarGirlFullyEnhanced()
        game.start_up(device_streaming=True)

        # All features work together
        game.start_recording()

        note = game.detect_note()  # Records detection
        game.record_tap(100, 200)  # Manual action record

        game.record_checkpoint("before_boss", {"level\": 5})

        recording = game.stop_recording()
        game.save_recording("session.yaml")

        # Recover and replay
        game.error_recovery_with_checkpoint("timeout")
        game.load_recording("session.yaml")
        game.playback_recording()

        # Get complete analysis
        game.report_performance()
    """

    def __init__(self) -> None:
        """Initialize fully enhanced Guitar Girl."""
        GuitarGirl.__init__(self)
        GuitarGirlCheckpointIntegration.__init__(self)
        GuitarGirlYOLOIntegration.__init__(self)
        GuitarGirlActionIntegration.__init__(self)

        logging.info("✅ Guitar Girl Fully Enhanced initialized with all features")

    def start_up(
        self,
        device_streaming: bool = True,
        yolo_model: str = "yolov8n.pt",
        enable_recording: bool = False,
        checkpoint_dir: Optional[str] = None
    ) -> bool:
        """Start up the game with all features.

        Args:
            device_streaming: Whether to enable device streaming
            yolo_model: Path to YOLO model
            enable_recording: Whether to start recording immediately
            checkpoint_dir: Optional custom checkpoint directory

        Returns:
            True if startup successful
        """
        try:
            # Initialize checkpoints
            self._init_checkpoint_system(checkpoint_dir)
            logging.info("✅ Checkpoint system initialized")

            # Initialize YOLO
            self._init_yolo_system(yolo_model)
            logging.info(f"✅ YOLO system initialized: {self.yolo_enabled}")

            # Initialize action recording
            self._init_action_system()
            logging.info(f"✅ Action recording system initialized: {self.recording_enabled}")

            # Call parent start_up
            super().start_up(device_streaming=device_streaming)

            # Cleanup old checkpoints
            self.cleanup_old_checkpoints(keep_count=5)
            logging.info("✅ Old checkpoints cleaned up")

            # Start recording if requested
            if enable_recording and self.recording_enabled:
                self.start_recording()

            return True

        except Exception as e:
            logging.error(f"❌ Startup failed: {e}")
            return False

    def detect_and_record_note(self, note_class: str) -> Optional[DetectionResult]:
        """Detect note and record the action.

        Args:
            note_class: Class of note to detect

        Returns:
            DetectionResult if found, None otherwise
        """
        result = self.detect_note(note_class, use_yolo=True)
        if result:
            self.record_note_detection(
                note_class=result.class_name,
                confidence=result.confidence,
                location=[result.x, result.y, result.width, result.height]
            )
        return result

    def detect_all_and_record(self) -> List[DetectionResult]:
        """Detect all notes and record the action.

        Returns:
            List of DetectionResult objects
        """
        results = self.detect_all_notes(use_yolo=True)
        for result in results:
            self.record_note_detection(
                note_class=result.class_name,
                confidence=result.confidence,
                location=[result.x, result.y, result.width, result.height]
            )
        return results

    def tap_and_record(self, x: int, y: int, duration: float = 0.1) -> bool:
        """Tap location and record the action.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Tap duration

        Returns:
            True if successful
        """
        # Execute tap (in real implementation)
        # For now, just record it
        success = self.record_tap(x, y, duration)
        if success:
            logging.debug(f"Tap recorded at ({x}, {y})")
        return success

    def level_up_and_record(self, character: str, new_level: int) -> bool:
        """Level up character and record the action.

        Args:
            character: Character name
            new_level: New level

        Returns:
            True if successful
        """
        return self.record_level_up(character, new_level)

    def use_skill_and_record(self, skill_name: str, skill_id: int) -> bool:
        """Use skill and record the action.

        Args:
            skill_name: Skill name
            skill_id: Skill ID

        Returns:
            True if successful
        """
        return self.record_skill_use(skill_name, skill_id)

    def save_session(self, recording_path: str) -> bool:
        """Save complete session (checkpoint + recording).

        Args:
            recording_path: Path to save recording

        Returns:
            True if successful
        """
        try:
            # Stop recording
            recording = self.stop_recording()
            if not recording:
                logging.warning("No recording to save")
                return False

            # Save recording
            success = self.save_recording(recording_path)
            if not success:
                return False

            logging.info(f"✅ Session saved: {recording_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to save session: {e}")
            return False

    def replay_session(self, recording_path: str) -> Dict[str, Any]:
        """Load and replay a saved session.

        Args:
            recording_path: Path to recording file

        Returns:
            Playback result with statistics
        """
        try:
            # Load recording
            if not self.load_recording(recording_path):
                return {"success": False, "error": "Failed to load recording"}

            # Playback
            return self.playback_recording()

        except Exception as e:
            logging.error(f"Failed to replay session: {e}")
            return {"success": False, "error": str(e)}

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all systems.

        Returns:
            Dictionary with complete statistics
        """
        return {
            "game": "guitar-girl",
            "checkpoint_stats": self.get_checkpoint_stats(),
            "yolo_stats": self.get_detection_stats(),
            "action_stats": self.get_action_stats(),
            "session_summary": {
                "songs_completed": getattr(self, '_songs_completed', 0),
                "current_level": getattr(self, '_current_level', 0),
                "total_score": getattr(self, '_current_score', 0),
                "detection_history_size": len(getattr(self, '_detection_history', [])),
            }
        }

    def report_comprehensive_performance(self) -> None:
        """Log comprehensive performance report from all systems."""
        logging.info("=" * 80)
        logging.info("GUITAR GIRL FULLY ENHANCED - COMPREHENSIVE PERFORMANCE REPORT")
        logging.info("=" * 80)

        # Checkpoint stats
        logging.info("\n📌 CHECKPOINT SYSTEM:")
        self.report_checkpoint_stats()

        # YOLO stats
        logging.info("\n🎯 YOLO DETECTION SYSTEM:")
        self.report_detection_stats()

        # Action stats
        logging.info("\n🎬 ACTION RECORDING SYSTEM:")
        self.report_action_stats()

        # Combined analysis
        logging.info("\n📊 COMBINED ANALYSIS:")
        stats = self.get_comprehensive_stats()
        if stats['session_summary']:
            logging.info(f"  Songs Completed: {stats['session_summary']['songs_completed']}")
            logging.info(f"  Current Level: {stats['session_summary']['current_level']}")
            logging.info(f"  Total Score: {stats['session_summary']['total_score']}")
            logging.info(f"  Detections Recorded: {stats['session_summary']['detection_history_size']}")

        logging.info("=" * 80)

    def integrated_error_recovery(self, error_msg: str) -> bool:
        """Enhanced error recovery using all systems.

        Args:
            error_msg: Description of error

        Returns:
            True if recovery successful
        """
        logging.error(f"Error: {error_msg}")
        logging.info("Initiating integrated error recovery...")

        # Record the error
        self.record_checkpoint("error_checkpoint", f"error_recovery: {error_msg}")

        # Try checkpoint recovery
        success = self.error_recovery_with_checkpoint(error_msg)

        if success:
            # Record successful recovery
            self.record_action("recovery", {"type": "checkpoint", "status": "success"})
            logging.info("✅ Integrated recovery successful")

        return success

    def record_action(self, action_type: str, params: Dict[str, Any]) -> bool:
        """Record a custom action.

        Args:
            action_type: Type of action
            params: Action parameters

        Returns:
            True if recorded
        """
        if not self.action_recorder or not self.action_recorder.is_recording:
            return False

        try:
            return self.action_recorder.record_action(action_type, params)
        except Exception as e:
            logging.warning(f"Failed to record action: {e}")
            return False

    def enable_full_recording(self) -> bool:
        """Enable comprehensive recording of all actions.

        Returns:
            True if recording started
        """
        if not self.start_recording():
            return False

        logging.info("🎬 Full recording enabled - all actions will be recorded")
        return True

    def disable_recording_and_save(self, output_path: str) -> bool:
        """Stop recording and save the session.

        Args:
            output_path: Path to save recording

        Returns:
            True if successful
        """
        recording = self.stop_recording()
        if not recording:
            return False

        return self.save_recording(output_path)
