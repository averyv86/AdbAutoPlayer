"""Integration tests for AFK Journey Checkpoint System.

Tests cover:
- Checkpoint creation and management
- State gathering and restoration
- Error recovery
- Checkpoint cleanup
- Statistics tracking
- Integration with AFKJourneyEnhanced
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil

from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.checkpoint_integration import (
    AFKJourneyCheckpointIntegration,
)
from adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.afk_journey_enhanced import (
    AFKJourneyEnhanced,
)


class TestCheckpointIntegrationInit:
    """Test checkpoint integration initialization."""

    def test_init_checkpoint_integration(self):
        """Test initializing checkpoint integration."""
        integration = AFKJourneyCheckpointIntegration()

        assert integration.checkpoint_manager is None
        assert integration.current_checkpoint_id is None
        assert integration.checkpoint_stats["total_saved"] == 0
        assert integration.checkpoint_stats["total_loaded"] == 0
        assert integration.checkpoint_stats["total_recovered"] == 0

    def test_init_checkpoint_system_with_valid_dir(self):
        """Test initializing checkpoint system with valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = AFKJourneyCheckpointIntegration()
            integration._init_checkpoint_system(tmpdir)

            assert integration.checkpoint_manager is not None
            assert Path(tmpdir).exists()

    def test_init_checkpoint_system_creates_directory(self):
        """Test that initialization creates checkpoint directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            integration = AFKJourneyCheckpointIntegration()
            integration._init_checkpoint_system(str(checkpoint_dir))

            assert checkpoint_dir.exists()


class TestCheckpointSaveLoad:
    """Test checkpoint save and load functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyCheckpointIntegration()
        self.integration._init_checkpoint_system(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_save_checkpoint_success(self):
        """Test successful checkpoint save."""
        checkpoint_id = self.integration.save_checkpoint()

        assert checkpoint_id is not None
        assert checkpoint_id.startswith("ckpt_")
        assert self.integration.checkpoint_stats["total_saved"] == 1
        assert self.integration.checkpoint_stats["last_save_time"] is not None

    def test_save_checkpoint_with_metadata(self):
        """Test saving checkpoint with custom metadata."""
        metadata = {"battle_num": 42, "location": "arcane_labyrinth"}
        checkpoint_id = self.integration.save_checkpoint(metadata=metadata)

        assert checkpoint_id is not None
        assert self.integration.checkpoint_stats["total_saved"] == 1

    def test_save_checkpoint_different_types(self):
        """Test saving checkpoints of different types."""
        types = ["manual", "auto", "milestone", "error_recovery"]

        for checkpoint_type in types:
            checkpoint_id = self.integration.save_checkpoint(checkpoint_type=checkpoint_type)
            assert checkpoint_id is not None

        assert self.integration.checkpoint_stats["total_saved"] == 4

    def test_load_checkpoint_without_manager(self):
        """Test loading checkpoint when manager not initialized."""
        integration = AFKJourneyCheckpointIntegration()
        result = integration.load_checkpoint("some_id")

        assert result is False

    def test_save_and_load_checkpoint(self):
        """Test saving then loading checkpoint."""
        checkpoint_id = self.integration.save_checkpoint()

        assert checkpoint_id is not None

        # Load the checkpoint
        success = self.integration.load_checkpoint(checkpoint_id)

        assert success is True
        assert self.integration.checkpoint_stats["total_loaded"] == 1
        assert self.integration.current_checkpoint_id == checkpoint_id

    def test_multiple_saves_and_loads(self):
        """Test multiple save and load operations."""
        checkpoint_ids = []

        # Save multiple checkpoints
        for i in range(3):
            ckpt_id = self.integration.save_checkpoint(metadata={"iteration": i})
            checkpoint_ids.append(ckpt_id)

        assert self.integration.checkpoint_stats["total_saved"] == 3

        # Load each checkpoint
        for ckpt_id in checkpoint_ids:
            success = self.integration.load_checkpoint(ckpt_id)
            assert success is True

        assert self.integration.checkpoint_stats["total_loaded"] == 3


class TestCheckpointStateGathering:
    """Test state gathering for checkpointing."""

    def test_gather_fsm_state(self):
        """Test FSM state gathering."""
        integration = AFKJourneyCheckpointIntegration()
        integration.battle_state = Mock()
        integration.battle_state.mode = "quest"

        fsm_state = integration._gather_fsm_state()

        assert fsm_state is not None
        assert "current_state" in fsm_state
        assert "state_entry_time" in fsm_state
        assert "timeout_remaining" in fsm_state
        assert "iteration" in fsm_state
        assert "progress" in fsm_state

    def test_gather_device_state(self):
        """Test device state gathering."""
        integration = AFKJourneyCheckpointIntegration()

        device_state = integration._gather_device_state()

        assert device_state is not None
        assert "serial" in device_state
        assert "battery_percent" in device_state
        assert "memory_percent" in device_state

    def test_gather_automation_context(self):
        """Test automation context gathering."""
        integration = AFKJourneyCheckpointIntegration()

        context = integration._gather_automation_context()

        assert context is not None
        assert "current_target" in context
        assert "detection_scale" in context
        assert "last_action_time" in context
        assert "action_queue" in context


class TestCheckpointList:
    """Test listing available checkpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyCheckpointIntegration()
        self.integration._init_checkpoint_system(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_list_empty_checkpoints(self):
        """Test listing when no checkpoints exist."""
        checkpoints = self.integration.list_available_checkpoints()

        assert checkpoints == []

    def test_list_after_saving_checkpoints(self):
        """Test listing after saving checkpoints."""
        # Save multiple checkpoints
        for i in range(3):
            self.integration.save_checkpoint(metadata={"num": i})

        checkpoints = self.integration.list_available_checkpoints()

        assert len(checkpoints) == 3
        assert all("id" in cp for cp in checkpoints)
        assert all("created_at" in cp for cp in checkpoints)

    def test_list_with_limit(self):
        """Test listing with limit parameter."""
        # Save 5 checkpoints
        for i in range(5):
            self.integration.save_checkpoint()

        checkpoints = self.integration.list_available_checkpoints(limit=2)

        assert len(checkpoints) == 2


class TestCheckpointCleanup:
    """Test checkpoint cleanup functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyCheckpointIntegration()
        self.integration._init_checkpoint_system(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_cleanup_old_checkpoints(self):
        """Test cleaning up old checkpoints."""
        # Save 10 checkpoints
        for i in range(10):
            self.integration.save_checkpoint()

        # Cleanup, keeping only 3
        deleted = self.integration.cleanup_old_checkpoints(keep_count=3)

        assert deleted >= 0

    def test_cleanup_respects_keep_count(self):
        """Test cleanup respects keep_count parameter."""
        # Save 5 checkpoints
        for i in range(5):
            self.integration.save_checkpoint()

        # Cleanup, keeping only 2
        self.integration.cleanup_old_checkpoints(keep_count=2)

        remaining = self.integration.list_available_checkpoints(limit=100)
        assert len(remaining) <= 2


class TestCheckpointAutoSave:
    """Test automatic checkpoint saving."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyCheckpointIntegration()
        self.integration._init_checkpoint_system(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_auto_save_checkpoint(self):
        """Test auto-save functionality."""
        checkpoint_id = self.integration.auto_save_checkpoint(reason="periodic")

        assert checkpoint_id is not None
        assert self.integration.checkpoint_stats["total_saved"] == 1

    def test_auto_save_different_reasons(self):
        """Test auto-save with different reasons."""
        reasons = ["periodic", "before_boss", "before_chapter", "detection_failure"]

        for reason in reasons:
            checkpoint_id = self.integration.auto_save_checkpoint(reason=reason)
            assert checkpoint_id is not None

        assert self.integration.checkpoint_stats["total_saved"] == 4


class TestCheckpointRecovery:
    """Test checkpoint recovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = AFKJourneyCheckpointIntegration()
        self.integration._init_checkpoint_system(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_recover_from_checkpoint_with_no_checkpoints(self):
        """Test recovery when no checkpoints exist."""
        success = self.integration.recover_from_checkpoint("test error")

        assert success is False

    def test_recover_from_checkpoint_success(self):
        """Test successful recovery from checkpoint."""
        # Save a checkpoint first
        self.integration.save_checkpoint()

        # Attempt recovery
        success = self.integration.recover_from_checkpoint("test error")

        assert success is True
        assert self.integration.checkpoint_stats["total_recovered"] == 1

    def test_recovery_increments_counter(self):
        """Test that recovery increments counter."""
        # Save checkpoint and recover multiple times
        for i in range(3):
            self.integration.save_checkpoint()
            self.integration.recover_from_checkpoint(f"error_{i}")

        assert self.integration.checkpoint_stats["total_recovered"] >= 1


class TestCheckpointStats:
    """Test checkpoint statistics."""

    def test_get_checkpoint_stats(self):
        """Test getting checkpoint statistics."""
        integration = AFKJourneyCheckpointIntegration()

        stats = integration.get_checkpoint_stats()

        assert "total_saved" in stats
        assert "total_loaded" in stats
        assert "total_recovered" in stats
        assert "current_checkpoint" in stats
        assert "checkpoint_system_initialized" in stats

    def test_stats_updated_on_save(self):
        """Test stats are updated on save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = AFKJourneyCheckpointIntegration()
            integration._init_checkpoint_system(tmpdir)

            assert integration.checkpoint_stats["total_saved"] == 0

            integration.save_checkpoint()

            assert integration.checkpoint_stats["total_saved"] == 1
            assert integration.checkpoint_stats["last_save_time"] is not None


class TestAFKJourneyEnhanced:
    """Test AFKJourneyEnhanced class integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_init(self, mock_base_init):
        """Test AFKJourneyEnhanced initialization."""
        mock_base_init.return_value = None

        game = AFKJourneyEnhanced()

        assert hasattr(game, 'checkpoint_manager')
        assert game._iteration_count == 0
        assert game._battles_completed == 0
        assert game._checkpoint_interval == 100

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_set_checkpoint_interval(self, mock_base_init):
        """Test setting checkpoint interval."""
        mock_base_init.return_value = None

        game = AFKJourneyEnhanced()
        game.set_checkpoint_interval(50)

        assert game._checkpoint_interval == 50

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_milestone_checkpoint(self, mock_base_init):
        """Test milestone checkpoint creation."""
        mock_base_init.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            game = AFKJourneyEnhanced()
            game._init_checkpoint_system(tmpdir)

            checkpoint_id = game.milestone_checkpoint("before_boss")

            assert checkpoint_id is not None

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_periodic_checkpoint(self, mock_base_init):
        """Test periodic checkpoint creation."""
        mock_base_init.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            game = AFKJourneyEnhanced()
            game.set_checkpoint_interval(5)
            game._init_checkpoint_system(tmpdir)

            # Call periodic checkpoint 6 times to trigger one save
            for _ in range(6):
                game.periodic_checkpoint()

            assert game._iteration_count == 6
            assert game.checkpoint_stats["total_saved"] >= 1

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_battle_complete(self, mock_base_init):
        """Test battle complete tracking."""
        mock_base_init.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            game = AFKJourneyEnhanced()
            game._init_checkpoint_system(tmpdir)

            game.battle_complete()
            game.battle_complete()

            assert game._battles_completed == 2

    @patch('adbautoplayer.src_tauri.src_python.adb_auto_player.games.afk_journey.base.AFKJourneyBase.__init__')
    def test_enhanced_get_session_summary(self, mock_base_init):
        """Test getting session summary."""
        mock_base_init.return_value = None

        game = AFKJourneyEnhanced()

        summary = game.get_session_summary()

        assert summary["game"] == "afk-journey"
        assert "iterations" in summary
        assert "battles_completed" in summary
        assert "checkpoint_stats" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
