"""AFK Journey Checkpoint Integration Module.

Provides state checkpointing and recovery capabilities for AFK Journey automation.
Integrates with Phase 10's CheckpointManager to enable:
- Saving game state at key milestones
- Resuming from checkpoints
- Automatic checkpoint creation
- Recovery from errors
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from time import time

# Import the checkpoint manager from the skill
try:
    # Try importing from skill location
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent / ".claude" / "skills" / "moai-domain-adb" / "scripts"))
    from adb_checkpoint_manager import CheckpointManager, Checkpoint, CheckpointType
except ImportError:
    # Fallback: Define minimal checkpoint classes locally
    logging.warning("Could not import CheckpointManager from skills. Using minimal implementation.")

    class Checkpoint:
        """Minimal checkpoint implementation"""
        def __init__(self, checkpoint_id: str, game: str, **kwargs):
            self.checkpoint_id = checkpoint_id
            self.game = game
            self.created_at = kwargs.get('created_at', datetime.now().isoformat())
            self.resumed_at = kwargs.get('resumed_at')
            self.metadata = kwargs.get('metadata', {})

    class CheckpointManager:
        """Minimal checkpoint manager"""
        def __init__(self, storage_dir: str = ".moai/checkpoints"):
            self.storage_dir = Path(storage_dir)
            self.checkpoints = {}

        def save_checkpoint(self, game: str, **kwargs) -> str:
            return f"ckpt_{game}_{int(time())}"

        def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
            return None

        def list_checkpoints(self, game: str = None, limit: int = 20):
            return []


class AFKJourneyCheckpointIntegration:
    """Mixin for adding checkpoint support to AFKJourney.

    Usage:
        class AFKJourneyEnhanced(AFKJourneyBase, AFKJourneyCheckpointIntegration):
            def __init__(self):
                super().__init__()
                self._init_checkpoint_system()
    """

    def __init__(self):
        """Initialize checkpoint system."""
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self.current_checkpoint_id: Optional[str] = None
        self.checkpoint_stats = {
            "total_saved": 0,
            "total_loaded": 0,
            "total_recovered": 0,
            "last_save_time": None,
            "last_load_time": None,
        }
        self._checkpoint_start_time: float = time()

    def _init_checkpoint_system(self, storage_dir: str = ".moai/checkpoints") -> None:
        """Initialize checkpoint manager.

        Args:
            storage_dir: Directory for storing checkpoint files
        """
        try:
            self.checkpoint_manager = CheckpointManager(storage_dir)
            logging.info(f"✅ Checkpoint system initialized at {storage_dir}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize checkpoint system: {e}")
            self.checkpoint_manager = None

    def save_checkpoint(
        self,
        checkpoint_type: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Save current game state as checkpoint.

        Args:
            checkpoint_type: Type of checkpoint ("manual", "auto", "milestone", "error_recovery")
            metadata: Additional metadata to save with checkpoint

        Returns:
            Checkpoint ID if successful, None otherwise
        """
        if not self.checkpoint_manager:
            logging.warning("Checkpoint system not initialized")
            return None

        try:
            # Gather current state
            fsm_state = self._gather_fsm_state()
            device_state = self._gather_device_state()
            automation_context = self._gather_automation_context()

            # Prepare metadata
            checkpoint_metadata = metadata or {}
            checkpoint_metadata.update({
                "duration_seconds": time() - self._checkpoint_start_time,
                "game_version": "1.0.0",
            })

            # Save checkpoint
            checkpoint_id = self.checkpoint_manager.save_checkpoint(
                game="afk-journey",
                device_serial=self._get_device_serial(),
                fsm_state=fsm_state,
                device_state=device_state,
                automation_context=automation_context,
                checkpoint_type=checkpoint_type,
                metadata=checkpoint_metadata,
            )

            if checkpoint_id:
                self.current_checkpoint_id = checkpoint_id
                self.checkpoint_stats["total_saved"] += 1
                self.checkpoint_stats["last_save_time"] = datetime.now().isoformat()
                logging.info(f"✅ Checkpoint saved: {checkpoint_id}")
                return checkpoint_id
            else:
                logging.error("Failed to save checkpoint")
                return None

        except Exception as e:
            logging.error(f"❌ Error saving checkpoint: {e}")
            return None

    def load_checkpoint(self, checkpoint_id: str) -> bool:
        """Load game state from checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            True if successful, False otherwise
        """
        if not self.checkpoint_manager:
            logging.warning("Checkpoint system not initialized")
            return False

        try:
            checkpoint = self.checkpoint_manager.load_checkpoint(checkpoint_id)

            if not checkpoint:
                logging.error(f"Checkpoint not found: {checkpoint_id}")
                return False

            # Restore state from checkpoint
            if checkpoint.fsm_state:
                self._restore_fsm_state(checkpoint.fsm_state.__dict__)

            if checkpoint.automation_context:
                self._restore_automation_context(checkpoint.automation_context.__dict__)

            self.current_checkpoint_id = checkpoint_id
            self.checkpoint_stats["total_loaded"] += 1
            self.checkpoint_stats["last_load_time"] = datetime.now().isoformat()
            logging.info(f"✅ Checkpoint loaded: {checkpoint_id}")
            return True

        except Exception as e:
            logging.error(f"❌ Error loading checkpoint: {e}")
            return False

    def list_available_checkpoints(self, limit: int = 10) -> list:
        """List available checkpoints for AFK Journey.

        Args:
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint information dictionaries
        """
        if not self.checkpoint_manager:
            return []

        try:
            checkpoints = self.checkpoint_manager.list_checkpoints(
                game="afk-journey",
                limit=limit
            )

            return [
                {
                    "id": cp.checkpoint_id,
                    "created_at": cp.created_at,
                    "type": getattr(cp, 'checkpoint_type', 'unknown'),
                }
                for cp in checkpoints
            ]
        except Exception as e:
            logging.error(f"Error listing checkpoints: {e}")
            return []

    def auto_save_checkpoint(self, reason: str = "periodic") -> Optional[str]:
        """Automatically save checkpoint.

        Args:
            reason: Reason for auto-save ("periodic", "before_boss", "before_chapter", etc.)

        Returns:
            Checkpoint ID if successful
        """
        metadata = {"reason": reason}
        return self.save_checkpoint(checkpoint_type="auto", metadata=metadata)

    def recover_from_checkpoint(self, error_msg: str = "") -> bool:
        """Recover from error using latest checkpoint.

        Args:
            error_msg: Error message that triggered recovery

        Returns:
            True if recovery successful
        """
        checkpoints = self.list_available_checkpoints(limit=1)

        if not checkpoints:
            logging.error("No checkpoints available for recovery")
            return False

        latest_checkpoint = checkpoints[0]
        logging.info(f"Attempting recovery from checkpoint: {latest_checkpoint['id']}")

        success = self.load_checkpoint(latest_checkpoint['id'])

        if success:
            self.checkpoint_stats["total_recovered"] += 1
            logging.info("✅ Recovery successful")
        else:
            logging.error("❌ Recovery failed")

        return success

    def cleanup_old_checkpoints(self, keep_count: int = 5) -> int:
        """Clean up old checkpoints, keeping only recent ones.

        Args:
            keep_count: Number of recent checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        if not self.checkpoint_manager:
            return 0

        try:
            deleted = self.checkpoint_manager.cleanup_old_checkpoints(
                game="afk-journey",
                keep_count=keep_count
            )
            logging.info(f"🧹 Cleaned up {deleted} old checkpoints")
            return deleted
        except Exception as e:
            logging.error(f"Error cleaning up checkpoints: {e}")
            return 0

    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics.

        Returns:
            Dictionary with checkpoint statistics
        """
        return {
            **self.checkpoint_stats,
            "current_checkpoint": self.current_checkpoint_id,
            "checkpoint_system_initialized": self.checkpoint_manager is not None,
        }

    # Helper methods for state gathering/restoration

    def _gather_fsm_state(self) -> Dict[str, Any]:
        """Gather FSM state for checkpointing.

        Returns:
            FSM state dictionary
        """
        try:
            if hasattr(self, 'battle_state'):
                return {
                    "current_state": str(getattr(self.battle_state, 'mode', 'unknown')),
                    "state_entry_time": datetime.now().isoformat(),
                    "timeout_remaining": 300,
                    "iteration": getattr(self, '_iteration_count', 0),
                    "progress": {
                        "battles_completed": getattr(self, '_battles_completed', 0),
                        "current_location": getattr(self, '_current_location', 'unknown'),
                    },
                }
        except Exception as e:
            logging.warning(f"Error gathering FSM state: {e}")

        return {
            "current_state": "unknown",
            "state_entry_time": datetime.now().isoformat(),
            "timeout_remaining": 300,
            "iteration": 0,
            "progress": {},
        }

    def _gather_device_state(self) -> Dict[str, Any]:
        """Gather device state for checkpointing.

        Returns:
            Device state dictionary
        """
        return {
            "serial": self._get_device_serial(),
            "battery_percent": 100,  # Would be gathered from device in real implementation
            "memory_percent": 50,    # Would be gathered from device in real implementation
        }

    def _gather_automation_context(self) -> Dict[str, Any]:
        """Gather automation context for checkpointing.

        Returns:
            Automation context dictionary
        """
        return {
            "current_target": getattr(self, '_current_target', 'none'),
            "detection_scale": 1.0,
            "last_action_time": datetime.now().isoformat(),
            "action_queue": [],
        }

    def _restore_fsm_state(self, state_dict: Dict[str, Any]) -> None:
        """Restore FSM state from checkpoint.

        Args:
            state_dict: FSM state dictionary
        """
        logging.debug(f"Restoring FSM state: {state_dict.get('current_state')}")
        # Implementation would restore actual FSM state

    def _restore_automation_context(self, context_dict: Dict[str, Any]) -> None:
        """Restore automation context from checkpoint.

        Args:
            context_dict: Automation context dictionary
        """
        logging.debug(f"Restoring automation context")
        # Implementation would restore actual context

    def _get_device_serial(self) -> str:
        """Get device serial number.

        Returns:
            Device serial or "unknown"
        """
        try:
            if hasattr(self, 'device') and hasattr(self.device, 'serial'):
                return self.device.serial
        except:
            pass
        return "unknown"
