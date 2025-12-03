"""Guitar Girl Checkpoint Integration.

Provides checkpoint save/load/recovery for Guitar Girl automation.
Saves game state (progress, level, skill status) and automation context.

Features:
- Save game state to checkpoints
- Load from checkpoints for recovery
- Checkpoint lifecycle management
- Integration with timing and detection systems
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from time import time

try:
    import yaml
except ImportError:
    logging.warning("PyYAML not available. Checkpoint saving will be limited.")
    yaml = None


@dataclass
class GameState:
    """State snapshot for Guitar Girl."""
    timestamp: float
    level: int = 0
    score: int = 0
    big_notes: int = 0
    small_notes: int = 0
    last_tap_time: float = 0.0
    tap_history_size: int = 0
    songs_completed: int = 0


class GuitarGirlCheckpointIntegration:
    """Mixin for adding checkpoint functionality to Guitar Girl.

    Usage:
        class GuitarGirlEnhanced(GuitarGirl, GuitarGirlCheckpointIntegration):
            def __init__(self):
                GuitarGirl.__init__(self)
                self._init_checkpoint_system()
    """

    def __init__(self):
        """Initialize checkpoint system."""
        self.checkpoint_manager = None
        self.checkpoint_enabled = False
        self.checkpoint_dir = Path.home() / ".guitar_girl_checkpoints"
        self.last_checkpoint_time = 0.0
        self.checkpoint_stats = {
            "total_checkpoints": 0,
            "saved_checkpoints": 0,
            "loaded_checkpoints": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }
        self._state_history: List[GameState] = []

    def _init_checkpoint_system(self, checkpoint_dir: Optional[str] = None) -> bool:
        """Initialize checkpoint system.

        Args:
            checkpoint_dir: Custom checkpoint directory path

        Returns:
            True if initialized successfully
        """
        try:
            if checkpoint_dir:
                self.checkpoint_dir = Path(checkpoint_dir)

            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            self.checkpoint_enabled = True
            logging.info(f"✅ Checkpoint system initialized at {self.checkpoint_dir}")
            return True
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize checkpoint system: {e}")
            self.checkpoint_enabled = False
            return False

    def save_checkpoint(
        self,
        checkpoint_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save current game state to checkpoint.

        Args:
            checkpoint_id: Unique checkpoint identifier
            description: Optional description of checkpoint
            metadata: Optional additional metadata

        Returns:
            True if saved successfully
        """
        if not self.checkpoint_enabled:
            return False

        try:
            # Gather current state
            state = GameState(
                timestamp=time(),
                level=getattr(self, '_current_level', 0),
                score=getattr(self, '_current_score', 0),
                big_notes=getattr(self, 'note_detection_stats', {}).get('big_notes', 0),
                small_notes=getattr(self, 'note_detection_stats', {}).get('small_notes', 0),
                last_tap_time=getattr(self, 'last_tap_time', 0.0),
                tap_history_size=len(getattr(self, 'tap_history', [])),
                songs_completed=getattr(self, '_songs_completed', 0),
            )

            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "state": asdict(state),
                "metadata": metadata or {},
                "device_info": {
                    "device": getattr(self, '_device_id', "unknown"),
                    "resolution": str(getattr(self, 'base_resolution', "unknown")),
                },
                "note_stats": getattr(self, 'note_detection_stats', {}),
                "timing_stats": {
                    "last_tap_time": getattr(self, 'last_tap_time', 0.0),
                    "tap_history_size": len(getattr(self, 'tap_history', [])),
                },
            }

            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.yaml"

            if yaml:
                with open(checkpoint_file, 'w') as f:
                    yaml.dump(checkpoint_data, f)
            else:
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)

            self._state_history.append(state)
            self.checkpoint_stats["saved_checkpoints"] += 1
            self.last_checkpoint_time = time()

            logging.info(f"✅ Checkpoint saved: {checkpoint_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
            return False

    def load_checkpoint(self, checkpoint_id: str) -> bool:
        """Load game state from checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier to load

        Returns:
            True if loaded successfully
        """
        if not self.checkpoint_enabled:
            return False

        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.yaml"

            if not checkpoint_file.exists():
                checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

            if not checkpoint_file.exists():
                logging.warning(f"Checkpoint not found: {checkpoint_id}")
                return False

            with open(checkpoint_file, 'r') as f:
                if checkpoint_file.suffix == '.yaml':
                    checkpoint_data = yaml.safe_load(f) if yaml else None
                else:
                    checkpoint_data = json.load(f)

            if not checkpoint_data:
                return False

            # Restore state
            state = checkpoint_data.get('state', {})
            self._current_level = state.get('level', 0)
            self._current_score = state.get('score', 0)
            self._songs_completed = state.get('songs_completed', 0)

            # Restore note statistics
            note_stats = checkpoint_data.get('note_stats', {})
            if hasattr(self, 'note_detection_stats'):
                self.note_detection_stats.update(note_stats)

            self.checkpoint_stats["loaded_checkpoints"] += 1
            logging.info(f"✅ Checkpoint loaded: {checkpoint_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to load checkpoint: {e}")
            return False

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints.

        Returns:
            List of checkpoint information dictionaries
        """
        if not self.checkpoint_enabled:
            return []

        try:
            checkpoints = []
            for checkpoint_file in self.checkpoint_dir.glob("*.yaml"):
                try:
                    with open(checkpoint_file, 'r') as f:
                        data = yaml.safe_load(f) if yaml else None
                    if data:
                        checkpoints.append({
                            "id": data.get('checkpoint_id', checkpoint_file.stem),
                            "created_at": data.get('created_at'),
                            "description": data.get('description', ''),
                            "level": data.get('state', {}).get('level', 0),
                        })
                except Exception as e:
                    logging.warning(f"Failed to read checkpoint {checkpoint_file}: {e}")
                    continue

            return sorted(checkpoints, key=lambda x: x.get('created_at', ''), reverse=True)

        except Exception as e:
            logging.error(f"Failed to list checkpoints: {e}")
            return []

    def cleanup_old_checkpoints(self, keep_count: int = 5) -> int:
        """Clean up old checkpoints, keeping only recent ones.

        Args:
            keep_count: Number of recent checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        if not self.checkpoint_enabled:
            return 0

        try:
            checkpoints = self.list_checkpoints()
            if len(checkpoints) <= keep_count:
                return 0

            to_delete = checkpoints[keep_count:]
            deleted_count = 0

            for checkpoint in to_delete:
                checkpoint_file = self.checkpoint_dir / f"{checkpoint['id']}.yaml"
                try:
                    checkpoint_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"Failed to delete checkpoint: {e}")

            logging.info(f"✅ Cleaned up {deleted_count} old checkpoints")
            return deleted_count

        except Exception as e:
            logging.error(f"Failed to cleanup checkpoints: {e}")
            return 0

    def error_recovery_with_checkpoint(self, error_msg: str) -> bool:
        """Attempt recovery from last checkpoint.

        Args:
            error_msg: Description of error that triggered recovery

        Returns:
            True if recovery successful
        """
        if not self.checkpoint_enabled:
            logging.warning("Checkpoint system not enabled")
            return False

        try:
            checkpoints = self.list_checkpoints()
            if not checkpoints:
                logging.warning("No checkpoints available for recovery")
                return False

            # Load most recent checkpoint
            latest_checkpoint = checkpoints[0]
            logging.info(f"Attempting recovery from checkpoint: {latest_checkpoint['id']}")

            self.checkpoint_stats["recovery_attempts"] += 1

            if self.load_checkpoint(latest_checkpoint['id']):
                self.checkpoint_stats["successful_recoveries"] += 1
                logging.info("✅ Recovery successful")
                return True
            else:
                logging.error("Recovery failed")
                return False

        except Exception as e:
            logging.error(f"Error recovery failed: {e}")
            return False

    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics.

        Returns:
            Dictionary with checkpoint statistics
        """
        return {
            "checkpoint_enabled": self.checkpoint_enabled,
            "checkpoint_dir": str(self.checkpoint_dir),
            "total_checkpoints": len(self.list_checkpoints()),
            "saved_checkpoints": self.checkpoint_stats["saved_checkpoints"],
            "loaded_checkpoints": self.checkpoint_stats["loaded_checkpoints"],
            "recovery_attempts": self.checkpoint_stats["recovery_attempts"],
            "successful_recoveries": self.checkpoint_stats["successful_recoveries"],
            "recovery_success_rate": (
                self.checkpoint_stats["successful_recoveries"] /
                max(1, self.checkpoint_stats["recovery_attempts"]) * 100
            ),
            "state_history_size": len(self._state_history),
        }

    def report_checkpoint_stats(self) -> None:
        """Log checkpoint statistics to console."""
        stats = self.get_checkpoint_stats()
        logging.info("=" * 60)
        logging.info("Checkpoint Statistics:")
        logging.info(f"  Enabled: {stats['checkpoint_enabled']}")
        logging.info(f"  Total Checkpoints: {stats['total_checkpoints']}")
        logging.info(f"  Saved: {stats['saved_checkpoints']}")
        logging.info(f"  Loaded: {stats['loaded_checkpoints']}")
        logging.info(f"  Recovery Attempts: {stats['recovery_attempts']}")
        logging.info(f"  Successful Recoveries: {stats['successful_recoveries']}")
        logging.info(f"  Success Rate: {stats['recovery_success_rate']:.1f}%")
        logging.info("=" * 60)
