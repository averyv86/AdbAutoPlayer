"""AFK Journey with YOLO Detection and Checkpoint Support.

This module provides a fully enhanced AFK Journey implementation with:
- YOLO-based fast object detection
- Automatic checkpointing and recovery
- Hybrid detection (YOLO + template fallback)
- Confidence threshold tuning
"""

import logging
from typing import Optional, List, Dict, Any

from .base import AFKJourneyBase
from .checkpoint_integration import AFKJourneyCheckpointIntegration
from .yolo_integration import AFKJourneyYOLOIntegration, DetectionResult


class AFKJourneyYOLOEnhanced(AFKJourneyBase, AFKJourneyCheckpointIntegration, AFKJourneyYOLOIntegration):
    """Fully enhanced AFK Journey with YOLO detection and checkpoints.

    This class combines:
    - Base AFK Journey functionality
    - Checkpoint save/load/recovery
    - YOLO-based fast detection with template fallback

    Usage:
        game = AFKJourneyYOLOEnhanced()
        game.start_up(device_streaming=True)

        # YOLO detection
        result = game.detect_hero()

        # Automatic checkpoints
        game.periodic_checkpoint()

        # Error recovery
        game.error_recovery("detection_timeout")
    """

    def __init__(self) -> None:
        """Initialize enhanced AFK Journey with YOLO and checkpoints."""
        AFKJourneyBase.__init__(self)
        AFKJourneyCheckpointIntegration.__init__(self)
        AFKJourneyYOLOIntegration.__init__(self)

        # Track detection history for analysis
        self._last_detections: List[DetectionResult] = []
        self._max_detection_history: int = 50

        logging.info("✅ AFKJourney YOLO Enhanced initialized with checkpoints + YOLO")

    def start_up(self, device_streaming: bool = True, yolo_model: str = "yolov8n.pt") -> bool:
        """Start up the game with checkpoints and YOLO.

        Args:
            device_streaming: Whether to enable device streaming
            yolo_model: Path to YOLO model

        Returns:
            True if startup successful
        """
        try:
            # Initialize checkpoints
            self._init_checkpoint_system()
            logging.info("✅ Checkpoint system initialized")

            # Initialize YOLO
            self._init_yolo_system(yolo_model)
            logging.info(f"✅ YOLO system initialized: {self.yolo_enabled}")

            # Call parent start_up
            super().start_up(device_streaming=device_streaming)

            # Cleanup old checkpoints
            self.cleanup_old_checkpoints(keep_count=5)
            logging.info("✅ Old checkpoints cleaned up")

            return True

        except Exception as e:
            logging.error(f"❌ Startup failed: {e}")
            return False

    def detect_hero(self, use_yolo: bool = True) -> Optional[DetectionResult]:
        """Detect hero using YOLO with template fallback.

        Args:
            use_yolo: Whether to use YOLO detection

        Returns:
            DetectionResult if found, None otherwise
        """
        # Get current screen capture (would be implemented in base class)
        screen_path = self._get_current_screen()
        if not screen_path:
            return None

        result = self.detect_object(
            screen_path,
            "hero",
            use_yolo=use_yolo,
            use_template_fallback=True
        )

        if result:
            self._add_to_detection_history(result)
            logging.debug(f"✅ Hero detected via {result.method}")
        return result

    def detect_enemy(self, use_yolo: bool = True) -> Optional[DetectionResult]:
        """Detect enemy using YOLO with template fallback.

        Args:
            use_yolo: Whether to use YOLO detection

        Returns:
            DetectionResult if found, None otherwise
        """
        screen_path = self._get_current_screen()
        if not screen_path:
            return None

        result = self.detect_object(
            screen_path,
            "enemy",
            use_yolo=use_yolo,
            use_template_fallback=True
        )

        if result:
            self._add_to_detection_history(result)
        return result

    def detect_battle_button(self, use_yolo: bool = True) -> Optional[DetectionResult]:
        """Detect battle button using YOLO with template fallback.

        Args:
            use_yolo: Whether to use YOLO detection

        Returns:
            DetectionResult if found, None otherwise
        """
        screen_path = self._get_current_screen()
        if not screen_path:
            return None

        result = self.detect_object(
            screen_path,
            "battle_button",
            use_yolo=use_yolo,
            use_template_fallback=True
        )

        if result:
            self._add_to_detection_history(result)
        return result

    def detect_item(self, use_yolo: bool = True) -> Optional[DetectionResult]:
        """Detect item using YOLO with template fallback.

        Args:
            use_yolo: Whether to use YOLO detection

        Returns:
            DetectionResult if found, None otherwise
        """
        screen_path = self._get_current_screen()
        if not screen_path:
            return None

        result = self.detect_object(
            screen_path,
            "item",
            use_yolo=use_yolo,
            use_template_fallback=True
        )

        if result:
            self._add_to_detection_history(result)
        return result

    def detect_all_objects(self, use_yolo: bool = True) -> List[DetectionResult]:
        """Detect all objects in current screen.

        Args:
            use_yolo: Whether to use YOLO detection

        Returns:
            List of DetectionResult objects
        """
        screen_path = self._get_current_screen()
        if not screen_path:
            return []

        class_names = ["hero", "enemy", "battle_button", "item", "altar", "text"]
        results = self.detect_multiple_objects(
            screen_path,
            class_names,
            use_yolo=use_yolo,
            use_template_fallback=True
        )

        for result in results:
            self._add_to_detection_history(result)

        return results

    def _add_to_detection_history(self, result: DetectionResult) -> None:
        """Add detection to history for analysis.

        Args:
            result: DetectionResult to add
        """
        self._last_detections.append(result)
        if len(self._last_detections) > self._max_detection_history:
            self._last_detections.pop(0)

    def get_detection_history(self, limit: Optional[int] = None) -> List[DetectionResult]:
        """Get detection history.

        Args:
            limit: Maximum number of recent detections to return

        Returns:
            List of DetectionResult objects
        """
        if limit:
            return self._last_detections[-limit:]
        return self._last_detections.copy()

    def get_detection_success_rate(self, class_name: Optional[str] = None) -> float:
        """Get success rate for detections.

        Args:
            class_name: If specified, get success rate for that class only

        Returns:
            Success rate (0.0 - 1.0)
        """
        if not self._last_detections:
            return 0.0

        if class_name:
            relevant = [d for d in self._last_detections if d.class_name == class_name]
            if not relevant:
                return 0.0
            return sum(1 for d in relevant if d.detected) / len(relevant)
        else:
            return sum(1 for d in self._last_detections if d.detected) / len(self._last_detections)

    def optimize_confidence_thresholds(self) -> Dict[str, float]:
        """Analyze detection history and suggest optimized confidence thresholds.

        Returns:
            Dictionary with suggested confidence values per class
        """
        if not self._last_detections:
            logging.warning("No detection history available")
            return {}

        class_data: Dict[str, List[float]] = {}
        for detection in self._last_detections:
            if detection.detected:
                if detection.class_name not in class_data:
                    class_data[detection.class_name] = []
                class_data[detection.class_name].append(detection.confidence)

        optimized = {}
        for class_name, confidences in class_data.items():
            if confidences:
                # Suggest threshold at 90th percentile of successful detections
                sorted_conf = sorted(confidences)
                idx = max(0, int(len(sorted_conf) * 0.1))
                optimized[class_name] = round(sorted_conf[idx], 2)

        return optimized

    def report_performance(self) -> None:
        """Log comprehensive performance report."""
        logging.info("=" * 70)
        logging.info("AFK Journey YOLO Enhanced - Performance Report")
        logging.info("=" * 70)

        # Detection stats
        self.report_detection_stats()

        # Checkpoint stats
        self.report_checkpoint_stats()

        # Detection history analysis
        if self._last_detections:
            logging.info("-" * 70)
            logging.info("Detection History Analysis:")
            class_counts = {}
            for detection in self._last_detections:
                if detection.class_name not in class_counts:
                    class_counts[detection.class_name] = {"total": 0, "successful": 0}
                class_counts[detection.class_name]["total"] += 1
                if detection.detected:
                    class_counts[detection.class_name]["successful"] += 1

            for class_name, counts in class_counts.items():
                success_rate = counts["successful"] / counts["total"] if counts["total"] > 0 else 0
                logging.info(f"  {class_name}: {counts['successful']}/{counts['total']} ({success_rate:.1%})")

        logging.info("=" * 70)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get complete session summary with YOLO stats.

        Returns:
            Dictionary with session information
        """
        checkpoint_summary = super().get_session_summary()
        detection_stats = self.get_detection_stats()

        return {
            **checkpoint_summary,
            "yolo_stats": {
                "enabled": detection_stats["yolo_enabled"],
                "success_rate": detection_stats["success_rate"],
                "total_detections": detection_stats["total_detections"],
                "avg_speed_ms": detection_stats["avg_total_speed_ms"],
            },
        }

    def _get_current_screen(self) -> Optional[str]:
        """Get current screen capture path.

        Returns:
            Path to current screen image, or None
        """
        try:
            # This would be implemented in the base class
            # For now, return None as placeholder
            if hasattr(self, 'device') and hasattr(self.device, 'take_screenshot'):
                return self.device.take_screenshot()
            return None
        except Exception as e:
            logging.warning(f"Could not capture screen: {e}")
            return None

    def error_recovery_with_yolo(self, error_msg: str) -> bool:
        """Enhanced error recovery using YOLO detection for validation.

        Args:
            error_msg: Description of error

        Returns:
            True if recovery successful
        """
        logging.error(f"Error detected: {error_msg}")
        logging.info("Attempting recovery with YOLO validation...")

        # Recover from checkpoint
        success = self.recover_from_checkpoint(error_msg=error_msg)

        if success:
            # Validate recovery with YOLO detection
            screen = self._get_current_screen()
            if screen:
                detections = self.detect_all_objects(use_yolo=True)
                if detections:
                    logging.info(f"✅ Recovery successful. Detected {len(detections)} objects.")
                    return True

        logging.error("❌ Recovery failed")
        return False
