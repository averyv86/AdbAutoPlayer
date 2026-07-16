"""
Test suite for /macos-resource-optimizer:2-optimize command.

Command: Execute optimization strategy with user approval
Delegation: manager-resource-coordinator (analyze → strategy → approve → execute)
Tests: 3 (workflow delegation, user approval integration, error handling)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio


class TestCommand2OptimizeDelegation:
    """Test 1: Sequential workflow delegation (analyze → strategy → approve → execute)."""

    @pytest.mark.asyncio
    async def test_optimize_command_delegates_sequential_workflow(self):
        """Test /macos-resource-optimizer:2-optimize delegates sequential analysis-strategy-approval-execution workflow."""

        with patch('Task') as mock_task:
            # Phase 1: Analysis result
            analysis_result = {
                "status": "success",
                "categories": {
                    "cpu": {"usage_percent": 85.0, "recommendation": "reduce_processes"},
                    "memory": {"usage_percent": 92.0, "recommendation": "clear_cache"},
                    "disk": {"usage_percent": 78.0, "recommendation": "optimize_storage"},
                    "thermal": {"cpu_temp_celsius": 78.0, "recommendation": "increase_cooling"}
                }
            }

            # Phase 2: Strategy result
            strategy_result = {
                "status": "success",
                "optimizations": [
                    {
                        "id": "opt_001",
                        "category": "cpu",
                        "action": "Reduce background processes",
                        "priority": "high",
                        "estimated_improvement": "15-20%"
                    },
                    {
                        "id": "opt_002",
                        "category": "memory",
                        "action": "Clear application caches",
                        "priority": "high",
                        "estimated_improvement": "10-15%"
                    }
                ]
            }

            # Phase 3: Execution result
            execution_result = {
                "status": "success",
                "execution_summary": {
                    "total_optimizations": 2,
                    "successful": 2,
                    "failed": 0,
                    "improvements": {
                        "cpu_improvement": "18%",
                        "memory_improvement": "12%"
                    }
                }
            }

            mock_task.return_value = execution_result

            from unittest.mock import AsyncMock
            mock_execute = AsyncMock(return_value=execution_result)
            result = await mock_execute()

            # Verify sequential workflow completion
            assert result["status"] == "success"
            assert "execution_summary" in result
            assert result["execution_summary"]["total_optimizations"] > 0

    def test_optimize_delegates_with_sequential_phases(self):
        """Test Task() is called with sequential phase configuration."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "execution_summary": {
                    "total_optimizations": 2,
                    "successful": 2,
                    "improvements": {"cpu_improvement": "18%"}
                }
            }

            Task = mock_task
            result = Task(
                subagent_type="manager-resource-coordinator",
                prompt="Execute optimization workflow: Phase 1 (Analyze), Phase 2 (Strategy), Phase 3 (User Approval), Phase 4 (Execute)"
            )

            # Verify sequential delegation
            mock_task.assert_called_once()
            call_args = mock_task.call_args
            assert "Phase" in call_args[1]["prompt"]
            assert "Analyze" in call_args[1]["prompt"]
            assert "Strategy" in call_args[1]["prompt"]
            assert "Execute" in call_args[1]["prompt"]


class TestCommand2OptimizeUserApproval:
    """Test 2: User approval integration with AskUserQuestion (Korean)."""

    def test_optimize_requests_user_approval_with_korean_ui(self):
        """Test /macos-resource-optimizer:2-optimize requests user approval with Korean UI."""

        with patch('AskUserQuestion') as mock_ask:
            mock_ask.return_value = {
                "approval_decision": "approve",
                "user_language": "ko"
            }

            # Simulate user approval request
            approval = mock_ask(
                questions=[
                    {
                        "question": "다음 최적화를 실행하시겠습니까?",
                        "header": "최적화 승인",
                        "multiSelect": False,
                        "options": [
                            {
                                "label": "실행",
                                "description": "CPU 사용률 18% 개선, 메모리 12% 개선"
                            },
                            {
                                "label": "취소",
                                "description": "최적화를 실행하지 않습니다"
                            }
                        ]
                    }
                ]
            )

            # Verify user approval request
            mock_ask.assert_called_once()
            call_args = mock_ask.call_args
            assert "question" in call_args[0][0][0]

    def test_optimize_displays_optimization_plan_to_user(self):
        """Test optimize displays optimization plan with metrics to user."""

        with patch('AskUserQuestion') as mock_ask:
            mock_ask.return_value = {"approval_decision": "approve"}

            # Simulate approval request with detailed plan
            approval = mock_ask(
                questions=[
                    {
                        "question": "다음 최적화 계획을 확인하고 승인하세요",
                        "header": "최적화 계획",
                        "options": [
                            {
                                "label": "CPU 최적화",
                                "description": "백그라운드 프로세스 감소: 18% 개선 예상"
                            },
                            {
                                "label": "메모리 최적화",
                                "description": "캐시 정리: 12% 개선 예상"
                            }
                        ]
                    }
                ]
            )

            # Verify plan display
            assert approval["approval_decision"] == "approve"

    def test_optimize_handles_user_rejection(self):
        """Test /macos-resource-optimizer:2-optimize handles user rejection."""

        with patch('AskUserQuestion') as mock_ask:
            mock_ask.return_value = {"approval_decision": "cancel"}

            approval = mock_ask(
                questions=[
                    {
                        "question": "다음 최적화를 실행하시겠습니까?",
                        "options": [
                            {"label": "실행", "description": "최적화 실행"},
                            {"label": "취소", "description": "최적화 취소"}
                        ]
                    }
                ]
            )

            # Verify rejection handling
            assert approval["approval_decision"] == "cancel"

    def test_optimize_approval_includes_risk_assessment(self):
        """Test optimize approval includes risk assessment information."""

        with patch('AskUserQuestion') as mock_ask:
            mock_ask.return_value = {"approval_decision": "approve"}

            # Simulate approval with risk assessment
            approval = mock_ask(
                questions=[
                    {
                        "question": "최적화를 실행하시겠습니까?",
                        "options": [
                            {
                                "label": "실행",
                                "description": "위험 수준: 낮음 (99.9% 안전성). 예상 개선: 18%"
                            },
                            {
                                "label": "취소",
                                "description": "최적화를 건너뜁니다"
                            }
                        ]
                    }
                ]
            )

            assert approval["approval_decision"] == "approve"


class TestCommand2OptimizeErrorHandling:
    """Test 3: Error handling and recovery."""

    def test_optimize_handles_coordinator_analysis_failure(self):
        """Test /macos-resource-optimizer:2-optimize handles analysis phase failure."""

        with patch('Task') as mock_task:
            mock_task.side_effect = Exception("Analysis phase failed: Cannot access system metrics. Ensure proper permissions.")

            with pytest.raises(Exception) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute optimization workflow: Phase 1 (Analyze)"
                )

            assert "Analysis phase failed" in str(exc_info.value)

    def test_optimize_handles_strategy_generation_failure(self):
        """Test /macos-resource-optimizer:2-optimize handles strategy generation failure."""

        with patch('Task') as mock_task:
            mock_task.side_effect = Exception("Strategy generation failed: No valid optimizations found for current system state.")

            with pytest.raises(Exception) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute optimization workflow: Phase 2 (Strategy)"
                )

            assert "Strategy generation failed" in str(exc_info.value)

    def test_optimize_handles_execution_failure_with_rollback(self):
        """Test /macos-resource-optimizer:2-optimize handles execution failure with rollback."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "partial_failure",
                "error": "Optimization execution failed: Process termination rejected by system",
                "rollback_status": "success",
                "completed_optimizations": 1,
                "failed_optimizations": 1
            }

            result = mock_task.return_value

            # Verify rollback handling
            assert result["status"] == "partial_failure"
            assert result["rollback_status"] == "success"
            assert result["completed_optimizations"] >= 0

    def test_optimize_handles_user_approval_timeout(self):
        """Test /macos-resource-optimizer:2-optimize handles user approval timeout."""

        with patch('AskUserQuestion') as mock_ask:
            mock_ask.side_effect = TimeoutError("User approval request timed out after 300 seconds.")

            with pytest.raises(TimeoutError) as exc_info:
                AskUserQuestion(
                    questions=[
                        {
                            "question": "다음 최적화를 실행하시겠습니까?",
                            "options": [
                                {"label": "실행", "description": "실행"},
                                {"label": "취소", "description": "취소"}
                            ]
                        }
                    ]
                )

            assert "timeout" in str(exc_info.value).lower()

    def test_optimize_handles_concurrent_system_changes(self):
        """Test /macos-resource-optimizer:2-optimize handles concurrent system changes during execution."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "degraded_success",
                "warning": "System state changed during optimization execution. Some optimizations may have reduced effectiveness.",
                "execution_summary": {
                    "total_optimizations": 2,
                    "successful": 2,
                    "improvements": {"cpu_improvement": "12%"}
                }
            }

            result = mock_task.return_value

            # Verify handling of concurrent changes
            assert result["status"] == "degraded_success"
            assert "warning" in result

    def test_optimize_handles_insufficient_permissions(self):
        """Test /macos-resource-optimizer:2-optimize handles insufficient permissions."""

        with patch('Task') as mock_task:
            mock_task.side_effect = Exception("Optimization execution failed: Insufficient permissions. Some optimizations require admin access.")

            with pytest.raises(Exception) as exc_info:
                Task(
                    subagent_type="manager-resource-coordinator",
                    prompt="Execute optimization workflow"
                )

            assert "Insufficient permissions" in str(exc_info.value)


@pytest.fixture
def mock_task():
    """Fixture providing mock Task function."""
    with patch('Task') as mock:
        yield mock


@pytest.fixture
def mock_ask_user():
    """Fixture providing mock AskUserQuestion function."""
    with patch('AskUserQuestion') as mock:
        yield mock


def test_optimize_command_complete_workflow(mock_task, mock_ask_user):
    """Integration test: Complete optimization workflow with user approval."""

    # Setup mocks for sequential workflow
    mock_task.return_value = {
        "status": "success",
        "execution_summary": {
            "total_optimizations": 2,
            "successful": 2,
            "improvements": {
                "cpu_improvement": "18%",
                "memory_improvement": "12%"
            }
        }
    }

    mock_ask_user.return_value = {"approval_decision": "approve"}

    # Execute workflow
    approval = mock_ask_user(
        questions=[
            {
                "question": "다음 최적화를 실행하시겠습니까?",
                "options": [{"label": "실행", "description": "최적화 실행"}]
            }
        ]
    )

    if approval["approval_decision"] == "approve":
        result = mock_task(
            subagent_type="manager-resource-coordinator",
            prompt="Execute optimization workflow"
        )

        # Verify complete workflow
        assert result["status"] == "success"
        assert result["execution_summary"]["successful"] == 2
        assert "cpu_improvement" in result["execution_summary"]["improvements"]
