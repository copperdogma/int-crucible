"""
Tests for safety guardrails.

Tests emergency stop, resource limits, incident logging, and safety context.
"""

import pytest
import json
import signal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from kosmos.safety.guardrails import SafetyGuardrails
from kosmos.models.safety import (
    SafetyReport, SafetyViolation, SafetyIncident,
    ViolationType, RiskLevel, ResourceLimit, EmergencyStopStatus
)


class TestSafetyGuardrailsInitialization:
    """Tests for SafetyGuardrails initialization."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_init_default_settings(self, mock_get_config):
        """Test initialization with default settings."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        assert guardrails.code_validator is not None
        assert guardrails.incident_log_path == "safety_incidents.jsonl"
        assert guardrails.emergency_stop.is_active is False
        assert guardrails.default_resource_limits.max_memory_mb == 2048

    @patch('kosmos.safety.guardrails.get_config')
    def test_init_custom_incident_log_path(self, mock_get_config):
        """Test initialization with custom incident log path."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(
            incident_log_path="/custom/path/incidents.log",
            enable_signal_handlers=False
        )

        assert guardrails.incident_log_path == "/custom/path/incidents.log"

    @patch('kosmos.safety.guardrails.signal.signal')
    @patch('kosmos.safety.guardrails.get_config')
    def test_init_registers_signal_handlers(self, mock_get_config, mock_signal):
        """Test that signal handlers are registered."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=True)

        # Should register SIGTERM and SIGINT
        assert mock_signal.call_count >= 2

    @patch('kosmos.safety.guardrails.get_config')
    def test_init_creates_resource_limits_from_config(self, mock_get_config):
        """Test that resource limits are created from config."""
        mock_config = Mock()
        mock_config.safety.max_cpu_cores = 4.0
        mock_config.safety.max_memory_mb = 4096
        mock_config.safety.max_execution_time = 600
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        limits = guardrails.default_resource_limits
        assert limits.max_cpu_cores == 4.0
        assert limits.max_memory_mb == 4096
        assert limits.max_execution_time_seconds == 600


class TestCodeValidation:
    """Tests for code validation through guardrails."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_validate_code_passes_safe_code(self, mock_get_config):
        """Test that safe code passes validation."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        code = "x = 1 + 1"

        report = guardrails.validate_code(code)

        assert report.passed
        assert len(report.violations) == 0

    @patch('kosmos.safety.guardrails.get_config')
    def test_validate_code_blocks_dangerous_code(self, mock_get_config):
        """Test that dangerous code is blocked."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        code = "import os"

        report = guardrails.validate_code(code)

        assert not report.passed
        assert len(report.violations) > 0

    @patch('kosmos.safety.guardrails.get_config')
    def test_validate_code_logs_violations(self, mock_get_config, tmp_path):
        """Test that violations are logged as incidents."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        incident_log = tmp_path / "incidents.jsonl"
        guardrails = SafetyGuardrails(
            incident_log_path=str(incident_log),
            enable_signal_handlers=False
        )
        code = "import os"

        report = guardrails.validate_code(code)

        # Should log incident
        assert len(guardrails.incidents) > 0
        assert incident_log.exists()

    @patch('kosmos.safety.guardrails.get_config')
    def test_validate_code_raises_if_emergency_stop_active(self, mock_get_config):
        """Test that validation raises error if emergency stop is active."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        guardrails.trigger_emergency_stop(
            triggered_by="test",
            reason="Test stop"
        )

        with pytest.raises(RuntimeError, match="Emergency stop"):
            guardrails.validate_code("x = 1")

    @patch('kosmos.safety.guardrails.get_config')
    def test_validate_code_includes_context(self, mock_get_config):
        """Test that context is passed to validator."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        code = "x = 1"
        context = {"experiment_id": "exp_123"}

        report = guardrails.validate_code(code, context=context)

        assert "context" in report.metadata
        assert report.metadata["context"] == context


class TestResourceLimitEnforcement:
    """Tests for resource limit enforcement."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_enforce_uses_defaults_when_none_requested(self, mock_get_config):
        """Test that defaults are used when no limits requested."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        enforced = guardrails.enforce_resource_limits()

        assert enforced.max_memory_mb == 2048
        assert enforced.max_execution_time_seconds == 300

    @patch('kosmos.safety.guardrails.get_config')
    def test_enforce_caps_excessive_requests(self, mock_get_config):
        """Test that excessive requests are capped to defaults."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        requested = ResourceLimit(
            max_memory_mb=8192,  # Exceeds default
            max_execution_time_seconds=1000  # Exceeds default
        )

        enforced = guardrails.enforce_resource_limits(requested)

        assert enforced.max_memory_mb == 2048  # Capped
        assert enforced.max_execution_time_seconds == 300  # Capped

    @patch('kosmos.safety.guardrails.get_config')
    def test_enforce_allows_within_limits_requests(self, mock_get_config):
        """Test that requests within limits are allowed."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        requested = ResourceLimit(
            max_memory_mb=1024,  # Within default
            max_execution_time_seconds=100  # Within default
        )

        enforced = guardrails.enforce_resource_limits(requested)

        assert enforced.max_memory_mb == 1024
        assert enforced.max_execution_time_seconds == 100

    @patch('kosmos.safety.guardrails.get_config')
    def test_enforce_blocks_dangerous_permissions(self, mock_get_config):
        """Test that dangerous permissions are blocked."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        requested = ResourceLimit(
            allow_network_access=True,
            allow_file_write=True,
            allow_subprocess=True
        )

        enforced = guardrails.enforce_resource_limits(requested)

        # Should all be False (blocked)
        assert enforced.allow_network_access is False
        assert enforced.allow_file_write is False
        assert enforced.allow_subprocess is False


class TestEmergencyStopMechanism:
    """Tests for emergency stop mechanism."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_trigger_emergency_stop(self, mock_get_config):
        """Test triggering emergency stop."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        guardrails.trigger_emergency_stop(
            triggered_by="user",
            reason="Manual stop requested"
        )

        assert guardrails.emergency_stop.is_active is True
        assert guardrails.emergency_stop.triggered_by == "user"
        assert guardrails.emergency_stop.reason == "Manual stop requested"

    @patch('kosmos.safety.guardrails.get_config')
    def test_trigger_creates_flag_file(self, mock_get_config, tmp_path):
        """Test that triggering creates stop flag file."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            guardrails = SafetyGuardrails(enable_signal_handlers=False)
            guardrails.trigger_emergency_stop(
                triggered_by="test",
                reason="Test"
            )

            flag_file = Path(".kosmos_emergency_stop")
            assert flag_file.exists()

            # Check content
            content = json.loads(flag_file.read_text())
            assert content["triggered_by"] == "test"
            assert content["reason"] == "Test"

        finally:
            os.chdir(original_cwd)

    @patch('kosmos.safety.guardrails.get_config')
    def test_trigger_logs_incident(self, mock_get_config):
        """Test that triggering logs an incident."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        guardrails.trigger_emergency_stop(
            triggered_by="test",
            reason="Test stop"
        )

        # Should log incident
        assert len(guardrails.incidents) > 0
        assert "emergency_stop" in guardrails.incidents[-1].incident_id

    @patch('kosmos.safety.guardrails.get_config')
    def test_is_emergency_stop_active(self, mock_get_config):
        """Test checking if emergency stop is active."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        assert guardrails.is_emergency_stop_active() is False

        guardrails.trigger_emergency_stop(
            triggered_by="test",
            reason="Test"
        )

        assert guardrails.is_emergency_stop_active() is True

    @patch('kosmos.safety.guardrails.get_config')
    def test_check_emergency_stop_raises_if_active(self, mock_get_config):
        """Test that check raises error if stop is active."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        guardrails.trigger_emergency_stop(
            triggered_by="test",
            reason="Test stop"
        )

        with pytest.raises(RuntimeError, match="Emergency stop active"):
            guardrails.check_emergency_stop()

    @patch('kosmos.safety.guardrails.get_config')
    def test_reset_emergency_stop(self, mock_get_config, tmp_path):
        """Test resetting emergency stop."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            guardrails = SafetyGuardrails(enable_signal_handlers=False)
            guardrails.trigger_emergency_stop(
                triggered_by="test",
                reason="Test"
            )

            assert guardrails.is_emergency_stop_active() is True

            guardrails.reset_emergency_stop()

            assert guardrails.is_emergency_stop_active() is False
            assert not Path(".kosmos_emergency_stop").exists()

        finally:
            os.chdir(original_cwd)

    @patch('kosmos.safety.guardrails.get_config')
    def test_detects_flag_file(self, mock_get_config, tmp_path):
        """Test that flag file is detected."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            guardrails = SafetyGuardrails(enable_signal_handlers=False)

            # Create flag file manually
            flag_file = Path(".kosmos_emergency_stop")
            flag_file.write_text('{"reason": "test"}')

            # Check should detect it
            with pytest.raises(RuntimeError, match="Emergency stop"):
                guardrails.check_emergency_stop()

        finally:
            os.chdir(original_cwd)


class TestSafetyContext:
    """Tests for safety context manager."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_context_checks_before_and_after(self, mock_get_config):
        """Test that context checks emergency stop before and after."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        executed = False
        with guardrails.safety_context():
            executed = True

        assert executed

    @patch('kosmos.safety.guardrails.get_config')
    def test_context_raises_if_stop_active_before(self, mock_get_config):
        """Test that context raises if stop active before execution."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)
        guardrails.trigger_emergency_stop(
            triggered_by="test",
            reason="Test"
        )

        with pytest.raises(RuntimeError, match="Emergency stop"):
            with guardrails.safety_context():
                pass

    @patch('kosmos.safety.guardrails.get_config')
    def test_context_propagates_other_exceptions(self, mock_get_config):
        """Test that context propagates non-stop exceptions."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        with pytest.raises(ValueError, match="test error"):
            with guardrails.safety_context():
                raise ValueError("test error")


class TestIncidentLogging:
    """Tests for safety incident logging."""

    @patch('kosmos.safety.guardrails.get_config')
    def test_log_incident_to_memory(self, mock_get_config):
        """Test that incidents are logged to memory."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        incident = SafetyIncident(
            incident_id="test_123",
            violation=SafetyViolation(
                type=ViolationType.DANGEROUS_CODE,
                severity=RiskLevel.HIGH,
                message="Test violation"
            ),
            action_taken="Blocked"
        )

        guardrails._log_incident(incident)

        assert len(guardrails.incidents) == 1
        assert guardrails.incidents[0].incident_id == "test_123"

    @patch('kosmos.safety.guardrails.get_config')
    def test_log_incident_to_file(self, mock_get_config, tmp_path):
        """Test that incidents are logged to file."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        incident_log = tmp_path / "incidents.jsonl"
        guardrails = SafetyGuardrails(
            incident_log_path=str(incident_log),
            enable_signal_handlers=False
        )

        incident = SafetyIncident(
            incident_id="test_123",
            violation=SafetyViolation(
                type=ViolationType.DANGEROUS_CODE,
                severity=RiskLevel.HIGH,
                message="Test violation"
            ),
            action_taken="Blocked"
        )

        guardrails._log_incident(incident)

        # Check file exists
        assert incident_log.exists()

        # Check content (JSONL format)
        lines = incident_log.read_text().strip().split('\n')
        assert len(lines) == 1

        logged_data = json.loads(lines[0])
        assert logged_data["incident_id"] == "test_123"

    @patch('kosmos.safety.guardrails.get_config')
    def test_get_recent_incidents(self, mock_get_config):
        """Test retrieving recent incidents."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        # Add multiple incidents
        for i in range(15):
            incident = SafetyIncident(
                incident_id=f"incident_{i}",
                violation=SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.LOW,
                    message=f"Incident {i}"
                ),
                action_taken="Blocked"
            )
            guardrails._log_incident(incident)

        # Get recent (default limit 10)
        recent = guardrails.get_recent_incidents(limit=10)

        assert len(recent) == 10
        assert recent[-1].incident_id == "incident_14"  # Most recent

    @patch('kosmos.safety.guardrails.get_config')
    def test_get_recent_incidents_filtered_by_severity(self, mock_get_config):
        """Test retrieving incidents filtered by severity."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        # Add incidents with different severities
        for severity in [RiskLevel.LOW, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            incident = SafetyIncident(
                incident_id=f"incident_{severity.value}",
                violation=SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=severity,
                    message="Test"
                ),
                action_taken="Blocked"
            )
            guardrails._log_incident(incident)

        # Get only high severity
        high_incidents = guardrails.get_recent_incidents(severity=RiskLevel.HIGH)

        assert len(high_incidents) == 1
        assert high_incidents[0].violation.severity == RiskLevel.HIGH

    @patch('kosmos.safety.guardrails.get_config')
    def test_get_incident_summary(self, mock_get_config):
        """Test getting incident summary statistics."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        # Add various incidents
        guardrails._log_incident(SafetyIncident(
            incident_id="inc_1",
            violation=SafetyViolation(
                type=ViolationType.DANGEROUS_CODE,
                severity=RiskLevel.HIGH,
                message="Test"
            ),
            action_taken="Blocked",
            resolved=False
        ))
        guardrails._log_incident(SafetyIncident(
            incident_id="inc_2",
            violation=SafetyViolation(
                type=ViolationType.ETHICAL_VIOLATION,
                severity=RiskLevel.CRITICAL,
                message="Test"
            ),
            action_taken="Blocked",
            resolved=True
        ))

        summary = guardrails.get_incident_summary()

        assert summary["total_incidents"] == 2
        assert summary["by_type"]["dangerous_code"] == 1
        assert summary["by_type"]["ethical_violation"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["critical"] == 1
        assert summary["unresolved"] == 1

    @patch('kosmos.safety.guardrails.get_config')
    def test_get_incident_summary_empty(self, mock_get_config):
        """Test incident summary with no incidents."""
        mock_config = Mock()
        mock_config.safety.max_memory_mb = 2048
        mock_config.safety.max_execution_time = 300
        mock_get_config.return_value = mock_config

        guardrails = SafetyGuardrails(enable_signal_handlers=False)

        summary = guardrails.get_incident_summary()

        assert summary["total_incidents"] == 0
        assert summary["by_type"] == {}
        assert summary["by_severity"] == {}
        assert summary["unresolved"] == 0
