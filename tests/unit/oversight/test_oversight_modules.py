"""
Tests for oversight modules (human review + notifications).

Combined tests for efficiency.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from kosmos.oversight.human_review import (
    HumanReviewWorkflow, ApprovalMode, AuditEntry
)
from kosmos.oversight.notifications import (
    NotificationManager, NotificationLevel, NotificationChannel
)
from kosmos.models.safety import ApprovalRequest, ApprovalStatus, RiskLevel


# ========== Human Review Workflow Tests ==========

class TestHumanReviewInit:
    """Tests for HumanReviewWorkflow initialization."""

    def test_init_default_settings(self):
        """Test initialization with defaults."""
        workflow = HumanReviewWorkflow()

        assert workflow.mode == ApprovalMode.BLOCKING
        assert workflow.auto_approve_low_risk is True
        assert len(workflow.pending_requests) == 0

    def test_init_custom_settings(self):
        """Test initialization with custom settings."""
        callback = Mock()
        workflow = HumanReviewWorkflow(
            mode=ApprovalMode.QUEUE,
            auto_approve_low_risk=False,
            notification_callback=callback
        )

        assert workflow.mode == ApprovalMode.QUEUE
        assert workflow.auto_approve_low_risk is False
        assert workflow.notification_callback == callback


class TestApprovalModes:
    """Tests for different approval modes."""

    def test_disabled_mode_auto_approves(self):
        """Test that disabled mode auto-approves all requests."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.DISABLED)

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.HIGH,  # Even high risk
            reason_for_approval="Testing"
        )

        result = workflow.request_approval(request)

        assert result.status == ApprovalStatus.APPROVED

    def test_automatic_mode_approves_low_risk(self):
        """Test that automatic mode approves low risk."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.AUTOMATIC)

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.LOW,
            reason_for_approval="Testing"
        )

        result = workflow.request_approval(request)

        assert result.status == ApprovalStatus.APPROVED
        assert result.approved_by == "automatic"

    def test_queue_mode_adds_to_pending(self):
        """Test that queue mode adds request to pending."""
        workflow = HumanReviewWorkflow(
            mode=ApprovalMode.QUEUE,
            auto_approve_low_risk=False  # Don't auto-approve
        )

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.MEDIUM,
            reason_for_approval="Testing"
        )

        result = workflow.request_approval(request)

        assert result.status == ApprovalStatus.PENDING
        assert "test_123" in workflow.pending_requests
        assert workflow.get_pending_count() == 1


class TestPendingRequestProcessing:
    """Tests for processing pending requests in queue mode."""

    @patch('builtins.input', side_effect=['yes'])
    def test_process_pending_approves_request(self, mock_input):
        """Test processing pending request with approval."""
        workflow = HumanReviewWorkflow(
            mode=ApprovalMode.QUEUE,
            auto_approve_low_risk=False
        )

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.MEDIUM,
            reason_for_approval="Testing"
        )

        workflow.request_approval(request)
        processed = workflow.process_pending_requests()

        assert len(processed) == 1
        assert processed[0].status == ApprovalStatus.APPROVED
        assert workflow.get_pending_count() == 0

    @patch('builtins.input', side_effect=['no', 'User rejected'])
    def test_process_pending_rejects_request(self, mock_input):
        """Test processing pending request with rejection."""
        workflow = HumanReviewWorkflow(
            mode=ApprovalMode.QUEUE,
            auto_approve_low_risk=False
        )

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.MEDIUM,
            reason_for_approval="Testing"
        )

        workflow.request_approval(request)
        processed = workflow.process_pending_requests()

        assert len(processed) == 1
        assert processed[0].status == ApprovalStatus.REJECTED


class TestOverrideCapability:
    """Tests for approval decision override."""

    def test_override_approved_to_rejected(self):
        """Test overriding approved decision to rejected."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.AUTOMATIC)

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test op",
            risk_level=RiskLevel.LOW,
            reason_for_approval="Testing"
        )

        # Auto-approve
        workflow.request_approval(request)
        assert request.status == ApprovalStatus.APPROVED

        # Override to rejected
        workflow.override_decision(
            "test_123",
            user="admin",
            new_status=ApprovalStatus.REJECTED,
            reason="Security concern"
        )

        assert request.status == ApprovalStatus.REJECTED
        assert request.rejection_reason == "Security concern"

    def test_override_raises_on_missing_request(self):
        """Test that override raises error for missing request."""
        workflow = HumanReviewWorkflow()

        with pytest.raises(ValueError, match="not found"):
            workflow.override_decision(
                "nonexistent",
                user="admin",
                new_status=ApprovalStatus.REJECTED,
                reason="Test"
            )


class TestAuditTrail:
    """Tests for audit trail logging."""

    def test_audit_entry_created_on_approval_request(self):
        """Test that audit entry is created when requesting approval."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.AUTOMATIC)

        request = ApprovalRequest(
            request_id="test_123",
            operation_type="test",
            operation_description="Test",
            risk_level=RiskLevel.LOW,
            reason_for_approval="Testing"
        )

        workflow.request_approval(request)

        # Check audit trail
        trail = workflow.get_audit_trail()
        assert len(trail) > 0
        assert any(e.action == "approval_requested" for e in trail)

    def test_get_audit_trail_filtered_by_request_id(self):
        """Test getting audit trail filtered by request ID."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.AUTOMATIC)

        # Create multiple requests
        for i in range(3):
            request = ApprovalRequest(
                request_id=f"test_{i}",
                operation_type="test",
                operation_description="Test",
                risk_level=RiskLevel.LOW,
                reason_for_approval="Testing"
            )
            workflow.request_approval(request)

        # Get trail for specific request
        trail = workflow.get_audit_trail(request_id="test_1")
        assert all(e.request_id == "test_1" for e in trail)

    def test_get_approval_stats(self):
        """Test getting approval statistics."""
        workflow = HumanReviewWorkflow(mode=ApprovalMode.AUTOMATIC)

        # Create several requests
        for i in range(5):
            request = ApprovalRequest(
                request_id=f"test_{i}",
                operation_type="test",
                operation_description="Test",
                risk_level=RiskLevel.LOW,
                reason_for_approval="Testing"
            )
            workflow.request_approval(request)

        stats = workflow.get_approval_stats()

        assert stats["total_processed"] == 5
        assert stats["approved"] == 5
        assert stats["approval_rate"] == 1.0


# ========== Notification Manager Tests ==========

class TestNotificationManagerInit:
    """Tests for NotificationManager initialization."""

    def test_init_default_settings(self):
        """Test initialization with defaults."""
        manager = NotificationManager()

        assert manager.default_channel == NotificationChannel.BOTH
        assert manager.min_level == NotificationLevel.INFO
        assert len(manager.history) == 0

    def test_init_custom_settings(self):
        """Test initialization with custom settings."""
        manager = NotificationManager(
            default_channel=NotificationChannel.LOG,
            min_level=NotificationLevel.WARNING,
            use_rich_formatting=False
        )

        assert manager.default_channel == NotificationChannel.LOG
        assert manager.min_level == NotificationLevel.WARNING
        assert manager.use_rich is False


class TestNotificationSending:
    """Tests for sending notifications."""

    @patch('kosmos.oversight.notifications.logger')
    def test_notify_info_message(self, mock_logger):
        """Test sending info notification."""
        manager = NotificationManager(
            default_channel=NotificationChannel.LOG
        )

        manager.notify("Test message", level=NotificationLevel.INFO)

        # Should log and add to history
        assert len(manager.history) == 1
        assert manager.history[0].message == "Test message"
        assert manager.history[0].level == NotificationLevel.INFO

    @patch('kosmos.oversight.notifications.logger')
    def test_notify_below_min_level_ignored(self, mock_logger):
        """Test that notifications below min level are ignored."""
        manager = NotificationManager(
            min_level=NotificationLevel.WARNING
        )

        manager.notify("Debug message", level=NotificationLevel.DEBUG)
        manager.notify("Info message", level=NotificationLevel.INFO)

        # Should not be in history
        assert len(manager.history) == 0

    @patch('kosmos.oversight.notifications.logger')
    def test_convenience_methods(self, mock_logger):
        """Test convenience methods (info, warning, error, etc.)."""
        manager = NotificationManager(
            default_channel=NotificationChannel.LOG,
            min_level=NotificationLevel.DEBUG
        )

        manager.debug("Debug msg")
        manager.info("Info msg")
        manager.warning("Warning msg")
        manager.error("Error msg")
        manager.critical("Critical msg")

        assert len(manager.history) == 5
        assert manager.history[0].level == NotificationLevel.DEBUG
        assert manager.history[4].level == NotificationLevel.CRITICAL


class TestNotificationHistory:
    """Tests for notification history management."""

    @patch('kosmos.oversight.notifications.logger')
    def test_get_history_all(self, mock_logger):
        """Test getting all notification history."""
        manager = NotificationManager(default_channel=NotificationChannel.LOG)

        for i in range(10):
            manager.info(f"Message {i}")

        history = manager.get_history()

        assert len(history) == 10

    @patch('kosmos.oversight.notifications.logger')
    def test_get_history_filtered_by_level(self, mock_logger):
        """Test getting history filtered by level."""
        manager = NotificationManager(default_channel=NotificationChannel.LOG)

        manager.info("Info 1")
        manager.warning("Warning 1")
        manager.info("Info 2")
        manager.error("Error 1")

        warnings = manager.get_history(level=NotificationLevel.WARNING)

        assert len(warnings) == 1
        assert warnings[0].message == "Warning 1"

    @patch('kosmos.oversight.notifications.logger')
    def test_get_history_with_limit(self, mock_logger):
        """Test getting history with limit."""
        manager = NotificationManager(default_channel=NotificationChannel.LOG)

        for i in range(100):
            manager.info(f"Message {i}")

        history = manager.get_history(limit=10)

        assert len(history) == 10
        # Should be most recent
        assert history[-1].message == "Message 99"

    @patch('kosmos.oversight.notifications.logger')
    def test_clear_history(self, mock_logger):
        """Test clearing notification history."""
        manager = NotificationManager(default_channel=NotificationChannel.LOG)

        manager.info("Message 1")
        manager.info("Message 2")
        assert len(manager.history) == 2

        manager.clear_history()

        assert len(manager.history) == 0


class TestNotificationStats:
    """Tests for notification statistics."""

    @patch('kosmos.oversight.notifications.logger')
    def test_get_stats(self, mock_logger):
        """Test getting notification statistics."""
        manager = NotificationManager(default_channel=NotificationChannel.LOG)

        manager.info("Info 1")
        manager.info("Info 2")
        manager.warning("Warning 1")
        manager.error("Error 1")

        stats = manager.get_stats()

        assert stats["total_notifications"] == 4
        assert stats["by_level"]["info"] == 2
        assert stats["by_level"]["warning"] == 1
        assert stats["by_level"]["error"] == 1


class TestNotificationConfiguration:
    """Tests for notification configuration changes."""

    @patch('kosmos.oversight.notifications.logger')
    def test_set_min_level(self, mock_logger):
        """Test changing minimum notification level."""
        manager = NotificationManager(
            min_level=NotificationLevel.INFO,
            default_channel=NotificationChannel.LOG
        )

        manager.debug("Debug msg")  # Should be ignored
        assert len(manager.history) == 0

        manager.set_min_level(NotificationLevel.DEBUG)
        manager.debug("Debug msg 2")  # Should now be logged

        assert len(manager.history) == 1

    @patch('kosmos.oversight.notifications.logger')
    def test_set_channel(self, mock_logger):
        """Test changing notification channel."""
        manager = NotificationManager()

        assert manager.default_channel == NotificationChannel.BOTH

        manager.set_channel(NotificationChannel.LOG)

        assert manager.default_channel == NotificationChannel.LOG
