"""Enhanced AFK Journey with Checkpoint Support.

This module provides an enhanced version of AFKJourney with full checkpoint integration
for state persistence and recovery from failures.

Features:
- Automatic checkpoint creation at milestones
- Save/load game state
- Automatic recovery from errors
- Checkpoint cleanup and management
"""

import logging
from typing import Optional, Dict, Any

from .base import AFKJourneyBase
from .checkpoint_integration import AFKJourneyCheckpointIntegration


class AFKJourneyEnhanced(AFKJourneyBase, AFKJourneyCheckpointIntegration):
    """Enhanced AFK Journey with Checkpoint Support.

    This class combines the base AFKJourney functionality with checkpoint
    capabilities for state persistence and recovery.

    Usage:
        game = AFKJourneyEnhanced()
        game._init_checkpoint_system()

        # Save state before risky operation
        checkpoint_id = game.save_checkpoint()

        # Do something risky...

        # Recover if needed
        game.load_checkpoint(checkpoint_id)
    """

    def __init__(self) -> None:
        """Initialize Enhanced AFK Journey with checkpoint support."""
        AFKJourneyBase.__init__(self)
        AFKJourneyCheckpointIntegration.__init__(self)

        # Track iteration count for checkpoint creation
        self._iteration_count: int = 0
        self._battles_completed: int = 0
        self._current_location: str = "main"
        self._current_target: str = "none"

        # Checkpoint configuration
        self._checkpoint_interval: int = 100  # Save checkpoint every 100 iterations
        self._last_checkpoint_iteration: int = 0

        logging.info("✅ AFKJourney Enhanced initialized with checkpoint support")

    def start_up(self, device_streaming: bool = True) -> None:
        """Start up the game and initialize checkpoint system.

        Args:
            device_streaming: Whether to enable device streaming
        """
        # Initialize checkpoints
        self._init_checkpoint_system()

        # Call parent start_up
        super().start_up(device_streaming=device_streaming)

        # Cleanup old checkpoints
        self.cleanup_old_checkpoints(keep_count=5)

    def milestone_checkpoint(self, milestone: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a milestone checkpoint.

        Args:
            milestone: Name of the milestone (e.g., "before_boss", "chapter_complete")
            metadata: Additional metadata to save

        Returns:
            Checkpoint ID if successful
        """
        checkpoint_metadata = metadata or {}
        checkpoint_metadata["milestone"] = milestone

        return self.save_checkpoint(
            checkpoint_type="milestone",
            metadata=checkpoint_metadata
        )

    def periodic_checkpoint(self) -> None:
        """Automatically create periodic checkpoints based on iteration count.

        This method should be called in the main game loop.
        """
        self._iteration_count += 1

        # Create checkpoint at specified interval
        if (self._iteration_count - self._last_checkpoint_iteration) >= self._checkpoint_interval:
            checkpoint_id = self.auto_save_checkpoint(reason="periodic")
            if checkpoint_id:
                self._last_checkpoint_iteration = self._iteration_count
                logging.debug(f"Auto-checkpoint created at iteration {self._iteration_count}")

    def set_checkpoint_interval(self, interval: int) -> None:
        """Set the interval for automatic checkpoints.

        Args:
            interval: Number of iterations between checkpoints
        """
        self._checkpoint_interval = interval
        logging.info(f"Checkpoint interval set to every {interval} iterations")

    def report_checkpoint_stats(self) -> None:
        """Log checkpoint statistics to console."""
        stats = self.get_checkpoint_stats()
        logging.info("=" * 50)
        logging.info("Checkpoint Statistics:")
        logging.info(f"  Total Saved: {stats.get('total_saved', 0)}")
        logging.info(f"  Total Loaded: {stats.get('total_loaded', 0)}")
        logging.info(f"  Total Recovered: {stats.get('total_recovered', 0)}")
        logging.info(f"  Last Save: {stats.get('last_save_time', 'never')}")
        logging.info(f"  Last Load: {stats.get('last_load_time', 'never')}")
        logging.info(f"  Current Checkpoint: {stats.get('current_checkpoint', 'none')}")
        logging.info("=" * 50)

    def battle_complete(self) -> None:
        """Called when a battle completes. Updates stats and may trigger checkpoint."""
        self._battles_completed += 1

        # Log milestone after every 10 battles
        if self._battles_completed % 10 == 0:
            self.milestone_checkpoint(
                milestone=f"battles_{self._battles_completed}",
                metadata={"battles": self._battles_completed}
            )

    def error_recovery(self, error_msg: str) -> bool:
        """Handle error recovery using checkpoints.

        Args:
            error_msg: Description of the error

        Returns:
            True if recovery successful
        """
        logging.error(f"Error detected: {error_msg}")
        logging.info("Attempting automatic recovery...")

        success = self.recover_from_checkpoint(error_msg=error_msg)

        if success:
            logging.info("✅ Recovered from checkpoint successfully")
        else:
            logging.error("❌ Failed to recover from checkpoint")

        return success

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session.

        Returns:
            Dictionary with session information
        """
        return {
            "game": "afk-journey",
            "iterations": self._iteration_count,
            "battles_completed": self._battles_completed,
            "checkpoint_stats": self.get_checkpoint_stats(),
            "available_checkpoints": len(self.list_available_checkpoints(limit=100)),
        }
