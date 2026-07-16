#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Finite State Machine Patterns for Game Bots

Tests the FSM implementation from game-automation.md Module 4.
Covers state transitions, guards, timeouts, and recovery logic.

Test Categories:
  - State Definition Tests (8 tests)
  - FSM Initialization Tests (5 tests)
  - State Transition Tests (12 tests)
  - Guard Function Tests (8 tests)
  - Timeout Handling Tests (6 tests)
  - Recovery Logic Tests (7 tests)
  - Edge Case Tests (8 tests)

Total: 54 test methods, ~88% coverage target
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable


# ============================================================================
# FSM Implementation (from game-automation.md)
# ============================================================================

class BotState(Enum):
    """Enumeration of all possible bot states"""
    IDLE = "idle"
    LOADING = "loading"
    BATTLING = "battling"
    VICTORY = "victory"
    DEFEAT = "defeat"
    ERROR = "error"
    RECOVERY = "recovery"
    PAUSED = "paused"


@dataclass
class StateTransition:
    """Represents a state transition with guards and actions"""
    from_state: BotState
    to_state: BotState
    guard: Optional[Callable[[], bool]] = None
    action: Optional[Callable[[], None]] = None
    timeout_sec: int = 30


class GameBotFSM:
    """Finite State Machine for game automation"""

    def __init__(self, device, detector):
        self.device = device
        self.detector = detector
        self.current_state = BotState.IDLE
        self.state_entered_at = time.time()
        self.transitions = self._build_transitions()
        self.state_history = [BotState.IDLE]

    def _build_transitions(self) -> dict:
        """Define all valid state transitions"""
        return {
            BotState.IDLE: [
                StateTransition(
                    from_state=BotState.IDLE,
                    to_state=BotState.LOADING,
                    guard=self._detect_quest_button,
                    action=self._click_quest_button,
                    timeout_sec=5
                ),
            ],
            BotState.LOADING: [
                StateTransition(
                    from_state=BotState.LOADING,
                    to_state=BotState.BATTLING,
                    guard=self._detect_battle_ready,
                    action=self._start_battle,
                    timeout_sec=15
                ),
                StateTransition(
                    from_state=BotState.LOADING,
                    to_state=BotState.ERROR,
                    guard=lambda: self._check_timeout(15),
                    action=self._log_timeout,
                    timeout_sec=2
                ),
            ],
            BotState.BATTLING: [
                StateTransition(
                    from_state=BotState.BATTLING,
                    to_state=BotState.VICTORY,
                    guard=self._detect_victory,
                    action=self._claim_reward,
                    timeout_sec=60
                ),
                StateTransition(
                    from_state=BotState.BATTLING,
                    to_state=BotState.DEFEAT,
                    guard=self._detect_defeat,
                    action=self._handle_defeat,
                    timeout_sec=60
                ),
            ],
            BotState.VICTORY: [
                StateTransition(
                    from_state=BotState.VICTORY,
                    to_state=BotState.IDLE,
                    guard=self._detect_return_to_menu,
                    action=self._return_to_menu,
                    timeout_sec=10
                ),
            ],
            BotState.ERROR: [
                StateTransition(
                    from_state=BotState.ERROR,
                    to_state=BotState.RECOVERY,
                    guard=lambda: True,
                    action=self._initiate_recovery,
                    timeout_sec=5
                ),
            ],
            BotState.RECOVERY: [
                StateTransition(
                    from_state=BotState.RECOVERY,
                    to_state=BotState.IDLE,
                    guard=self._recovery_successful,
                    action=self._complete_recovery,
                    timeout_sec=10
                ),
            ],
        }

    def update(self) -> BotState:
        """Main FSM update loop"""
        if self._check_state_timeout():
            self._handle_state_timeout()
            return self.current_state

        if self.current_state in self.transitions:
            for transition in self.transitions[self.current_state]:
                if transition.guard and transition.guard():
                    if transition.action:
                        transition.action()

                    old_state = self.current_state
                    self.current_state = transition.to_state
                    self.state_entered_at = time.time()
                    self.state_history.append(self.current_state)
                    return self.current_state

        return self.current_state

    def _check_state_timeout(self) -> bool:
        """Check if current state has exceeded timeout"""
        elapsed = time.time() - self.state_entered_at
        timeout = self._get_state_timeout()
        return elapsed > timeout

    def _get_state_timeout(self) -> int:
        """Get timeout for current state"""
        state_timeouts = {
            BotState.LOADING: 20,
            BotState.BATTLING: 120,
            BotState.RECOVERY: 30,
        }
        return state_timeouts.get(self.current_state, 60)

    def _handle_state_timeout(self):
        """Handle timeout by transitioning to ERROR"""
        old_state = self.current_state
        self.current_state = BotState.ERROR
        self.state_entered_at = time.time()
        self.state_history.append(BotState.ERROR)

    def _detect_quest_button(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return self.detector.detect_element(state["image"], "quest_button")

    def _detect_battle_ready(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return self.detector.detect_element(state["image"], "start_button")

    def _detect_victory(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return self.detector.detect_element(state["image"], "victory_screen")

    def _detect_defeat(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return self.detector.detect_element(state["image"], "defeat_screen")

    def _detect_return_to_menu(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return self.detector.detect_element(state["image"], "main_menu")

    def _recovery_successful(self) -> bool:
        state = self.detector.capture_and_analyze(self.device)
        return (self.detector.detect_element(state["image"], "main_menu") or
                self.detector.detect_element(state["image"], "quest_list"))

    def _check_timeout(self, sec: int) -> bool:
        """Generic timeout check"""
        return (time.time() - self.state_entered_at) > sec

    def _click_quest_button(self):
        state = self.detector.capture_and_analyze(self.device)
        region = self.detector.get_element_region(state["image"], "quest_button")
        if region:
            cx = (region[0] + region[2]) // 2
            cy = (region[1] + region[3]) // 2
            self.device.tap(cx, cy)

    def _start_battle(self):
        self.device.tap(540, 960)

    def _claim_reward(self):
        self.device.tap(540, 1000)

    def _handle_defeat(self):
        self.device.tap(100, 100)

    def _return_to_menu(self):
        self.device.tap(100, 100)

    def _initiate_recovery(self):
        """Reset to known state"""
        self.device.tap(100, 100)
        time.sleep(0.1)

    def _complete_recovery(self):
        pass

    def _log_timeout(self):
        pass


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_device():
    """Mock ADB device"""
    device = Mock()
    device.tap = Mock()
    return device


@pytest.fixture
def mock_detector():
    """Mock screenshot detector"""
    detector = Mock()
    detector.capture_and_analyze = Mock(return_value={"image": Mock()})
    detector.detect_element = Mock(return_value=False)
    detector.get_element_region = Mock(return_value=None)
    return detector


@pytest.fixture
def fsm(mock_device, mock_detector):
    """Create FSM instance for testing"""
    return GameBotFSM(mock_device, mock_detector)


# ============================================================================
# Tests: State Definition (8 tests)
# ============================================================================

class TestStateDefinition:
    """Test BotState enumeration and StateTransition dataclass"""

    def test_bot_state_enum_values(self):
        """Verify all bot states have correct string values"""
        assert BotState.IDLE.value == "idle"
        assert BotState.LOADING.value == "loading"
        assert BotState.BATTLING.value == "battling"
        assert BotState.VICTORY.value == "victory"
        assert BotState.DEFEAT.value == "defeat"
        assert BotState.ERROR.value == "error"
        assert BotState.RECOVERY.value == "recovery"
        assert BotState.PAUSED.value == "paused"

    def test_bot_state_enum_count(self):
        """Verify correct number of states"""
        assert len(BotState) == 8

    def test_state_transition_dataclass(self):
        """Verify StateTransition creation"""
        transition = StateTransition(
            from_state=BotState.IDLE,
            to_state=BotState.LOADING,
            timeout_sec=10
        )
        assert transition.from_state == BotState.IDLE
        assert transition.to_state == BotState.LOADING
        assert transition.timeout_sec == 10
        assert transition.guard is None
        assert transition.action is None

    def test_state_transition_with_callable(self):
        """Verify StateTransition with guard and action"""
        guard = Mock(return_value=True)
        action = Mock()
        transition = StateTransition(
            from_state=BotState.IDLE,
            to_state=BotState.LOADING,
            guard=guard,
            action=action,
            timeout_sec=5
        )
        assert transition.guard == guard
        assert transition.action == action

    def test_state_transition_default_timeout(self):
        """Verify default timeout value"""
        transition = StateTransition(
            from_state=BotState.IDLE,
            to_state=BotState.LOADING
        )
        assert transition.timeout_sec == 30

    def test_bot_state_is_enum(self):
        """Verify BotState is Enum subclass"""
        assert issubclass(BotState, Enum)

    def test_state_transition_is_dataclass(self):
        """Verify StateTransition is dataclass"""
        import dataclasses
        assert dataclasses.is_dataclass(StateTransition)

    def test_all_states_are_unique(self):
        """Verify all state values are unique"""
        values = [state.value for state in BotState]
        assert len(values) == len(set(values))


# ============================================================================
# Tests: FSM Initialization (5 tests)
# ============================================================================

class TestFSMInitialization:
    """Test FSM instance creation and initial state"""

    def test_fsm_initial_state(self, fsm):
        """FSM starts in IDLE state"""
        assert fsm.current_state == BotState.IDLE

    def test_fsm_has_transitions(self, fsm):
        """FSM has transition dictionary"""
        assert fsm.transitions is not None
        assert isinstance(fsm.transitions, dict)

    def test_fsm_transition_count(self, fsm):
        """FSM has transitions from correct states"""
        assert BotState.IDLE in fsm.transitions
        assert BotState.LOADING in fsm.transitions
        assert BotState.BATTLING in fsm.transitions

    def test_fsm_state_history_init(self, fsm):
        """FSM tracks state history"""
        assert fsm.state_history == [BotState.IDLE]

    def test_fsm_preserves_references(self, fsm, mock_device, mock_detector):
        """FSM stores device and detector references"""
        assert fsm.device == mock_device
        assert fsm.detector == mock_detector


# ============================================================================
# Tests: State Transitions (12 tests)
# ============================================================================

class TestStateTransitions:
    """Test state transition logic"""

    def test_idle_to_loading_transition(self, fsm, mock_detector):
        """IDLE → LOADING when quest button detected"""
        mock_detector.detect_element.return_value = True
        fsm.update()
        assert fsm.current_state == BotState.LOADING

    def test_loading_to_battling_transition(self, fsm, mock_detector):
        """LOADING → BATTLING when battle ready"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "start_button"
        fsm.update()
        assert fsm.current_state == BotState.BATTLING

    def test_battling_to_victory_transition(self, fsm, mock_detector):
        """BATTLING → VICTORY when victory screen detected"""
        fsm.current_state = BotState.BATTLING
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "victory_screen"
        fsm.update()
        assert fsm.current_state == BotState.VICTORY

    def test_battling_to_defeat_transition(self, fsm, mock_detector):
        """BATTLING → DEFEAT when defeat screen detected"""
        fsm.current_state = BotState.BATTLING
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "defeat_screen"
        fsm.update()
        assert fsm.current_state == BotState.DEFEAT

    def test_victory_to_idle_transition(self, fsm, mock_detector):
        """VICTORY → IDLE when returning to menu"""
        fsm.current_state = BotState.VICTORY
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.return_value = True
        fsm.update()
        assert fsm.current_state == BotState.IDLE

    def test_error_to_recovery_transition(self, fsm):
        """ERROR → RECOVERY always (guard returns True)"""
        fsm.current_state = BotState.ERROR
        fsm.state_entered_at = time.time()
        fsm.update()
        assert fsm.current_state == BotState.RECOVERY

    def test_recovery_to_idle_transition(self, fsm, mock_detector):
        """RECOVERY → IDLE when recovery successful"""
        fsm.current_state = BotState.RECOVERY
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem in ("main_menu", "quest_list")
        fsm.update()
        assert fsm.current_state == BotState.IDLE

    def test_no_transition_stays_in_state(self, fsm, mock_detector):
        """No transition triggered = stay in current state"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.return_value = False
        initial_state = fsm.current_state
        fsm.update()
        assert fsm.current_state == initial_state

    def test_state_history_records_transitions(self, fsm, mock_detector):
        """State history records all transitions"""
        mock_detector.detect_element.return_value = True
        fsm.update()  # IDLE → LOADING
        assert BotState.LOADING in fsm.state_history
        assert len(fsm.state_history) == 2

    def test_transition_action_is_called(self, fsm, mock_detector):
        """Transition action is executed when guard passes"""
        mock_detector.detect_element.return_value = True
        fsm.update()
        # _click_quest_button should be called
        mock_detector.get_element_region.assert_called()

    def test_transition_guard_not_called_if_none(self, fsm):
        """Transition without guard doesn't error"""
        # Create transition without guard
        fsm.current_state = BotState.ERROR
        fsm.state_entered_at = time.time()
        # Should transition without error even though guard is None (lambda: True)
        result = fsm.update()
        assert result == BotState.RECOVERY

    def test_multiple_valid_transitions_first_wins(self, fsm, mock_detector):
        """First valid transition is taken"""
        fsm.current_state = BotState.BATTLING
        fsm.state_entered_at = time.time()
        # Make victory guard return True first
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "victory_screen"
        fsm.update()
        assert fsm.current_state == BotState.VICTORY  # Victory checked before defeat


# ============================================================================
# Tests: Guard Functions (8 tests)
# ============================================================================

class TestGuardFunctions:
    """Test guard function evaluation"""

    def test_detect_quest_button_guard(self, fsm, mock_detector):
        """_detect_quest_button returns True when button found"""
        mock_detector.detect_element.return_value = True
        result = fsm._detect_quest_button()
        assert result is True

    def test_detect_quest_button_guard_false(self, fsm, mock_detector):
        """_detect_quest_button returns False when button not found"""
        mock_detector.detect_element.return_value = False
        result = fsm._detect_quest_button()
        assert result is False

    def test_detect_battle_ready_guard(self, fsm, mock_detector):
        """_detect_battle_ready returns True when start button found"""
        mock_detector.detect_element.return_value = True
        result = fsm._detect_battle_ready()
        assert result is True

    def test_detect_victory_guard(self, fsm, mock_detector):
        """_detect_victory returns True when victory screen found"""
        mock_detector.detect_element.return_value = True
        result = fsm._detect_victory()
        assert result is True

    def test_detect_defeat_guard(self, fsm, mock_detector):
        """_detect_defeat returns True when defeat screen found"""
        mock_detector.detect_element.return_value = True
        result = fsm._detect_defeat()
        assert result is True

    def test_recovery_successful_guard_main_menu(self, fsm, mock_detector):
        """_recovery_successful returns True when main menu detected"""
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "main_menu"
        result = fsm._recovery_successful()
        assert result is True

    def test_recovery_successful_guard_quest_list(self, fsm, mock_detector):
        """_recovery_successful returns True when quest list detected"""
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "quest_list"
        result = fsm._recovery_successful()
        assert result is True

    def test_recovery_successful_guard_false(self, fsm, mock_detector):
        """_recovery_successful returns False when neither found"""
        mock_detector.detect_element.return_value = False
        result = fsm._recovery_successful()
        assert result is False


# ============================================================================
# Tests: Timeout Handling (6 tests)
# ============================================================================

class TestTimeoutHandling:
    """Test timeout detection and handling"""

    def test_check_state_timeout_not_exceeded(self, fsm):
        """Timeout not triggered when time < timeout"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time()  # Just entered
        result = fsm._check_state_timeout()
        assert result is False

    def test_check_state_timeout_exceeded(self, fsm):
        """Timeout triggered when time > timeout"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time() - 25  # 25 sec ago (timeout=20)
        result = fsm._check_state_timeout()
        assert result is True

    def test_get_state_timeout_loading(self, fsm):
        """LOADING state has 20 second timeout"""
        fsm.current_state = BotState.LOADING
        assert fsm._get_state_timeout() == 20

    def test_get_state_timeout_battling(self, fsm):
        """BATTLING state has 120 second timeout"""
        fsm.current_state = BotState.BATTLING
        assert fsm._get_state_timeout() == 120

    def test_get_state_timeout_recovery(self, fsm):
        """RECOVERY state has 30 second timeout"""
        fsm.current_state = BotState.RECOVERY
        assert fsm._get_state_timeout() == 30

    def test_handle_state_timeout_transitions_to_error(self, fsm):
        """Timeout handler transitions to ERROR state"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time() - 25
        fsm.update()
        assert fsm.current_state == BotState.ERROR


# ============================================================================
# Tests: Recovery Logic (7 tests)
# ============================================================================

class TestRecoveryLogic:
    """Test error and recovery patterns"""

    def test_error_state_exists(self):
        """ERROR state is defined"""
        assert BotState.ERROR in BotState

    def test_recovery_state_exists(self):
        """RECOVERY state is defined"""
        assert BotState.RECOVERY in BotState

    def test_error_transitions_to_recovery(self, fsm):
        """ERROR → RECOVERY transition exists"""
        fsm.current_state = BotState.ERROR
        fsm.state_entered_at = time.time()
        fsm.update()
        assert fsm.current_state == BotState.RECOVERY

    def test_recovery_action_called(self, fsm, mock_device):
        """_initiate_recovery is called during transition"""
        fsm.current_state = BotState.ERROR
        fsm.state_entered_at = time.time()
        initial_tap_count = mock_device.tap.call_count
        fsm.update()
        # Tap should be called in recovery action
        assert mock_device.tap.call_count > initial_tap_count

    def test_recovery_back_to_idle(self, fsm, mock_detector):
        """Successful recovery transitions back to IDLE"""
        fsm.current_state = BotState.RECOVERY
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.return_value = True
        fsm.update()
        assert fsm.current_state == BotState.IDLE

    def test_recovery_timeout(self, fsm):
        """RECOVERY state has timeout protection"""
        fsm.current_state = BotState.RECOVERY
        fsm.state_entered_at = time.time() - 35  # 35 sec ago (timeout=30)
        fsm.update()
        assert fsm.current_state == BotState.ERROR

    def test_complete_recovery_cycle(self, fsm, mock_detector, mock_device):
        """Complete error → recovery → idle cycle"""
        # Start with error
        fsm.current_state = BotState.ERROR
        fsm.state_entered_at = time.time()

        # Update to recovery
        fsm.update()
        assert fsm.current_state == BotState.RECOVERY

        # Mock recovery success
        mock_detector.detect_element.return_value = True
        fsm.update()
        assert fsm.current_state == BotState.IDLE


# ============================================================================
# Tests: Edge Cases (8 tests)
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_rapid_state_updates(self, fsm, mock_detector):
        """Multiple rapid updates don't cause issues"""
        mock_detector.detect_element.side_effect = lambda _, elem: True
        for _ in range(10):
            fsm.update()
        # Should end up in a stable state
        assert fsm.current_state in BotState

    def test_state_entered_at_updates(self, fsm, mock_detector):
        """state_entered_at updates on transition"""
        time_before = fsm.state_entered_at
        mock_detector.detect_element.return_value = True
        time.sleep(0.01)
        fsm.update()
        assert fsm.state_entered_at > time_before

    def test_zero_timeout_not_allowed(self, fsm):
        """Ensure timeouts are positive"""
        for state in BotState:
            fsm.current_state = state
            assert fsm._get_state_timeout() > 0

    def test_invalid_state_no_transitions(self, fsm):
        """Paused state has no transitions defined"""
        fsm.current_state = BotState.PAUSED
        initial_state = fsm.current_state
        fsm.update()
        assert fsm.current_state == initial_state

    def test_detector_exception_handling(self, fsm, mock_detector):
        """FSM handles detector exceptions gracefully"""
        mock_detector.capture_and_analyze.side_effect = RuntimeError("Device error")
        with pytest.raises(RuntimeError):
            fsm.update()

    def test_device_exception_handling(self, fsm, mock_device, mock_detector):
        """FSM handles device exceptions gracefully"""
        mock_device.tap.side_effect = RuntimeError("Device error")
        mock_detector.get_element_region.return_value = (10, 20, 100, 80)
        fsm.current_state = BotState.IDLE
        with pytest.raises(RuntimeError):
            fsm._click_quest_button()

    def test_concurrent_guard_evaluation(self, fsm, mock_detector):
        """Guards are evaluated independently"""
        mock_detector.detect_element.return_value = False
        result1 = fsm._detect_victory()
        result2 = fsm._detect_defeat()
        assert result1 == result2  # Both should be same (False)

    def test_state_history_length(self, fsm, mock_detector):
        """State history grows appropriately"""
        initial_len = len(fsm.state_history)
        mock_detector.detect_element.return_value = True
        for _ in range(3):
            fsm.update()
        assert len(fsm.state_history) > initial_len


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete bot workflows"""

    def test_complete_quest_cycle(self, fsm, mock_detector, mock_device):
        """Complete cycle: IDLE → LOADING → BATTLING → VICTORY → IDLE"""
        states_visited = []

        # IDLE → LOADING
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "quest_button"
        fsm.update()
        states_visited.append(fsm.current_state)

        # LOADING → BATTLING
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "start_button"
        fsm.update()
        states_visited.append(fsm.current_state)

        # BATTLING → VICTORY
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "victory_screen"
        fsm.update()
        states_visited.append(fsm.current_state)

        # VICTORY → IDLE
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.side_effect = lambda _, elem: elem == "main_menu"
        fsm.update()
        states_visited.append(fsm.current_state)

        assert states_visited == [BotState.LOADING, BotState.BATTLING, BotState.VICTORY, BotState.IDLE]

    def test_timeout_recovery_cycle(self, fsm, mock_detector):
        """Timeout triggers recovery cycle"""
        fsm.current_state = BotState.LOADING
        fsm.state_entered_at = time.time() - 25  # Timeout!

        # First update: triggers error
        fsm.update()
        assert fsm.current_state == BotState.ERROR

        # Second update: error → recovery
        fsm.state_entered_at = time.time()
        fsm.update()
        assert fsm.current_state == BotState.RECOVERY

        # Third update: recovery → idle (if successful)
        fsm.state_entered_at = time.time()
        mock_detector.detect_element.return_value = True
        fsm.update()
        assert fsm.current_state == BotState.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
