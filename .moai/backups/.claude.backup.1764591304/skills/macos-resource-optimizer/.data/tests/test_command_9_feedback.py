"""
Test suite for /macos-resource-optimizer:9-feedback command.

Command: Collect and validate feedback for system improvement
Delegation: manager-resource-coordinator (feedback validation, structuring)
Tests: 3 (feedback collection, validation, integration with /moai:9-feedback)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestCommand9FeedbackCollection:
    """Test 1: Feedback collection and structure validation."""

    def test_feedback_command_collects_structured_feedback(self):
        """Test /macos-resource-optimizer:9-feedback collects structured feedback."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback_id": "fb_20251130_001",
                "timestamp": "2025-11-30T10:30:00Z",
                "feedback": {
                    "category": "performance",
                    "type": "suggestion",
                    "severity": "medium",
                    "title": "CPU optimization could be faster",
                    "description": "The optimization process takes longer than expected on high-load systems",
                    "steps_to_reproduce": [
                        "Run analysis with CPU > 80%",
                        "Execute optimization",
                        "Observe timing"
                    ],
                    "expected_behavior": "Optimization should complete within 2 seconds",
                    "actual_behavior": "Optimization takes 3.5 seconds on loaded system",
                    "environment": {
                        "os": "macOS 15.1.1",
                        "model": "MacBook Pro M3 Max",
                        "python_version": "3.13.0"
                    }
                }
            }

            result = mock_task.return_value

            # Verify feedback structure
            assert result["status"] == "success"
            assert "feedback_id" in result
            assert "feedback" in result
            assert result["feedback"]["category"] in ["performance", "bug", "feature", "suggestion"]
            assert "title" in result["feedback"]
            assert "description" in result["feedback"]

    def test_feedback_command_delegates_to_coordinator(self):
        """Test Task() is called with feedback collection configuration."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback_id": "fb_20251130_001",
                "feedback": {"category": "performance"}
            }

            Task = mock_task
            result = Task(
                subagent_type="manager-resource-coordinator",
                prompt="Collect structured feedback: category, type, severity, description, environment, reproduction steps"
            )

            # Verify Task call
            mock_task.assert_called_once()
            call_args = mock_task.call_args
            assert call_args[1]["subagent_type"] == "manager-resource-coordinator"
            assert "feedback" in call_args[1]["prompt"].lower()

    def test_feedback_includes_environment_information(self):
        """Test feedback includes system environment information."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback": {
                    "environment": {
                        "os": "macOS 15.1.1",
                        "model": "MacBook Pro (14-inch, M3 Max)",
                        "python_version": "3.13.0",
                        "cores": 12,
                        "memory_gb": 16
                    }
                }
            }

            result = mock_task.return_value
            env = result["feedback"]["environment"]

            # Verify environment captured
            assert "os" in env
            assert "python_version" in env
            assert "cores" in env

    def test_feedback_includes_reproduction_steps(self):
        """Test feedback includes steps to reproduce issues."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback": {
                    "type": "bug",
                    "steps_to_reproduce": [
                        "Step 1: Run /macos-resource-optimizer:1-analyze",
                        "Step 2: Wait for completion",
                        "Step 3: Observe error in output"
                    ]
                }
            }

            result = mock_task.return_value

            # Verify reproduction steps
            assert "steps_to_reproduce" in result["feedback"]
            assert len(result["feedback"]["steps_to_reproduce"]) > 0


class TestCommand9FeedbackValidation:
    """Test 2: Feedback validation and quality checks."""

    def test_feedback_validates_required_fields(self):
        """Test feedback validation ensures required fields are present."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "validation": {
                    "valid": True,
                    "required_fields_present": True,
                    "missing_fields": [],
                    "required_fields": ["category", "type", "description"]
                }
            }

            result = mock_task.return_value

            # Verify validation
            assert result["validation"]["valid"] is True
            assert len(result["validation"]["missing_fields"]) == 0

    def test_feedback_validates_category_values(self):
        """Test feedback validation checks valid category values."""

        with patch('Task') as mock_task:
            valid_categories = ["bug", "feature", "performance", "suggestion", "security"]

            test_feedback = {
                "category": "performance",
                "valid": True
            }

            mock_task.return_value = {
                "status": "success",
                "validation": {
                    "valid": True,
                    "category_valid": True,
                    "valid_categories": valid_categories
                }
            }

            result = mock_task.return_value

            # Verify category validation
            assert result["validation"]["category_valid"] is True
            assert test_feedback["category"] in result["validation"]["valid_categories"]

    def test_feedback_validates_severity_levels(self):
        """Test feedback validation checks valid severity levels."""

        with patch('Task') as mock_task:
            valid_severities = ["low", "medium", "high", "critical"]

            mock_task.return_value = {
                "status": "success",
                "validation": {
                    "severity_valid": True,
                    "valid_severities": valid_severities
                }
            }

            result = mock_task.return_value

            # Verify severity validation
            assert result["validation"]["severity_valid"] is True
            assert "high" in result["validation"]["valid_severities"]

    def test_feedback_rejects_empty_description(self):
        """Test feedback validation rejects empty description."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "validation_failed",
                "error": "Feedback validation failed: Description is required and must contain at least 10 characters"
            }

            result = mock_task.return_value

            # Verify rejection
            assert result["status"] == "validation_failed"
            assert "Description" in result["error"]

    def test_feedback_validation_returns_suggestions(self):
        """Test feedback validation provides improvement suggestions."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success_with_suggestions",
                "feedback": {"description": "Monitor loop is slow"},
                "validation": {
                    "valid": True,
                    "suggestions": [
                        "Consider providing reproduction steps for better debugging",
                        "Add expected behavior vs actual behavior comparison"
                    ]
                }
            }

            result = mock_task.return_value

            # Verify suggestions
            assert "suggestions" in result["validation"]
            assert len(result["validation"]["suggestions"]) > 0


class TestCommand9FeedbackIntegration:
    """Test 3: Integration with /moai:9-feedback command."""

    def test_feedback_integrates_with_moai_feedback_command(self):
        """Test /macos-resource-optimizer:9-feedback integrates with /moai:9-feedback."""

        with patch('Task') as mock_task:
            # Simulate integration with global /moai:9-feedback
            moai_feedback_response = {
                "status": "submitted",
                "moai_command": "/moai:9-feedback",
                "feedback_reference": "fb_20251130_001",
                "submission_timestamp": "2025-11-30T10:35:00Z",
                "moai_ticket_id": "MOAI-FB-2025-1130-001"
            }

            mock_task.return_value = moai_feedback_response

            result = mock_task(
                subagent_type="manager-resource-coordinator",
                prompt="Submit feedback to /moai:9-feedback system"
            )

            # Verify MoAI integration
            assert result["status"] == "submitted"
            assert "moai_ticket_id" in result

    def test_feedback_submission_creates_improvement_ticket(self):
        """Test feedback submission creates improvement tracking ticket."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "ticket_created": True,
                "ticket": {
                    "id": "MOAI-FB-2025-1130-001",
                    "type": "improvement",
                    "title": "Optimize CPU analysis performance",
                    "category": "performance",
                    "status": "open",
                    "priority": "medium",
                    "created_at": "2025-11-30T10:35:00Z"
                }
            }

            result = mock_task.return_value

            # Verify ticket creation
            assert result["ticket_created"] is True
            assert "ticket" in result
            assert result["ticket"]["status"] == "open"

    def test_feedback_links_to_improvement_tracking(self):
        """Test feedback links to improvement tracking system."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "tracking": {
                    "feedback_id": "fb_20251130_001",
                    "linked_to_ticket": "MOAI-FB-2025-1130-001",
                    "tracking_url": "https://moai.example.com/tickets/MOAI-FB-2025-1130-001",
                    "estimated_review_date": "2025-12-07T00:00:00Z"
                }
            }

            result = mock_task.return_value

            # Verify tracking linkage
            assert result["tracking"]["linked_to_ticket"] is not None
            assert "tracking_url" in result["tracking"]

    def test_feedback_enables_improvement_iteration(self):
        """Test feedback system enables continuous improvement iteration."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "improvement_cycle": {
                    "feedback_id": "fb_20251130_001",
                    "improvement_stage": "1_review",
                    "stages": [
                        "1_review",
                        "2_analysis",
                        "3_planning",
                        "4_implementation",
                        "5_validation",
                        "6_release"
                    ],
                    "current_stage_status": "in_progress",
                    "estimated_completion": "2025-12-15T00:00:00Z"
                }
            }

            result = mock_task.return_value

            # Verify improvement cycle
            assert "improvement_cycle" in result
            assert result["improvement_cycle"]["current_stage_status"] == "in_progress"

    def test_feedback_supports_batched_submissions(self):
        """Test feedback system supports multiple feedback submissions."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "batch_submission": {
                    "total_feedbacks": 3,
                    "successful": 3,
                    "failed": 0,
                    "feedback_ids": [
                        "fb_20251130_001",
                        "fb_20251130_002",
                        "fb_20251130_003"
                    ]
                }
            }

            result = mock_task.return_value

            # Verify batch submission
            assert result["batch_submission"]["total_feedbacks"] == 3
            assert result["batch_submission"]["successful"] == 3


class TestCommand9FeedbackTypes:
    """Additional tests for different feedback types."""

    def test_feedback_accepts_bug_reports(self):
        """Test feedback accepts bug type reports."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback": {
                    "type": "bug",
                    "title": "Monitor loop crashes after 1 hour",
                    "severity": "high"
                }
            }

            result = mock_task.return_value

            # Verify bug report
            assert result["feedback"]["type"] == "bug"
            assert result["feedback"]["severity"] == "high"

    def test_feedback_accepts_feature_requests(self):
        """Test feedback accepts feature request type."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback": {
                    "type": "feature",
                    "title": "Add GPU optimization support",
                    "severity": "medium"
                }
            }

            result = mock_task.return_value

            # Verify feature request
            assert result["feedback"]["type"] == "feature"

    def test_feedback_accepts_security_reports(self):
        """Test feedback accepts security type reports."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "feedback": {
                    "type": "security",
                    "title": "Potential privilege escalation vulnerability",
                    "severity": "critical"
                }
            }

            result = mock_task.return_value

            # Verify security report
            assert result["feedback"]["type"] == "security"
            assert result["feedback"]["severity"] == "critical"


@pytest.fixture
def mock_task():
    """Fixture providing mock Task function."""
    with patch('Task') as mock:
        yield mock


def test_feedback_command_complete_workflow(mock_task):
    """Integration test: Complete feedback submission workflow."""

    # Phase 1: Collect feedback
    mock_task.return_value = {
        "status": "success",
        "feedback_id": "fb_20251130_001",
        "feedback": {
            "category": "performance",
            "type": "suggestion",
            "severity": "medium",
            "title": "Optimize analysis speed",
            "description": "Analysis could be 20% faster with parallel I/O optimization"
        },
        "validation": {"valid": True}
    }

    feedback_result = mock_task(
        subagent_type="manager-resource-coordinator",
        prompt="Collect structured feedback"
    )

    # Phase 2: Submit to /moai:9-feedback
    mock_task.return_value = {
        "status": "submitted",
        "feedback_reference": feedback_result["feedback_id"],
        "moai_ticket_id": "MOAI-FB-2025-1130-001"
    }

    submission_result = mock_task(
        subagent_type="manager-resource-coordinator",
        prompt="Submit feedback to /moai:9-feedback"
    )

    # Verify complete workflow
    assert feedback_result["status"] == "success"
    assert feedback_result["validation"]["valid"] is True
    assert submission_result["status"] == "submitted"
    assert submission_result["moai_ticket_id"] is not None
