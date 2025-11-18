"""
Tests for code safety validator.

Tests code validation, ethical guidelines, and approval gate logic.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from kosmos.safety.code_validator import CodeValidator
from kosmos.models.safety import (
    SafetyReport, ViolationType, RiskLevel, EthicalGuideline,
    ApprovalRequest, ApprovalStatus
)


class TestCodeValidatorInitialization:
    """Tests for CodeValidator initialization."""

    def test_init_default_settings(self):
        """Test initialization with default settings."""
        validator = CodeValidator()

        assert validator.allow_file_read is True
        assert validator.allow_file_write is False
        assert validator.allow_network is False
        assert len(validator.ethical_guidelines) > 0

    def test_init_custom_permissions(self):
        """Test initialization with custom permission settings."""
        validator = CodeValidator(
            allow_file_read=False,
            allow_file_write=True,
            allow_network=True
        )

        assert validator.allow_file_read is False
        assert validator.allow_file_write is True
        assert validator.allow_network is True

    def test_init_loads_default_ethical_guidelines(self):
        """Test that default ethical guidelines are loaded."""
        validator = CodeValidator()

        guidelines = validator.ethical_guidelines
        assert len(guidelines) >= 4  # At least no_harm, privacy, consent, animal

        # Check for specific guidelines
        guideline_ids = [g.guideline_id for g in guidelines]
        assert "no_harm" in guideline_ids
        assert "privacy" in guideline_ids

    def test_init_with_custom_guidelines_file(self, tmp_path):
        """Test loading ethical guidelines from file."""
        guidelines_file = tmp_path / "guidelines.json"
        guidelines_file.write_text(json.dumps({
            "guidelines": [
                {
                    "guideline_id": "custom_1",
                    "category": "test",
                    "description": "Test guideline",
                    "required": True,
                    "validation_method": "keyword",
                    "keywords": ["test_keyword"],
                    "severity_if_violated": "high"
                }
            ]
        }))

        validator = CodeValidator(ethical_guidelines_path=str(guidelines_file))

        assert len(validator.ethical_guidelines) == 1
        assert validator.ethical_guidelines[0].guideline_id == "custom_1"

    def test_init_with_nonexistent_guidelines_file(self):
        """Test that nonexistent file falls back to defaults."""
        validator = CodeValidator(ethical_guidelines_path="/nonexistent/path.json")

        # Should use defaults
        assert len(validator.ethical_guidelines) > 0


class TestSyntaxValidation:
    """Tests for syntax validation."""

    def test_valid_syntax_passes(self):
        """Test that valid syntax passes."""
        validator = CodeValidator()
        code = """
import numpy as np
x = np.array([1, 2, 3])
y = x + 1
"""
        report = validator.validate(code)

        assert report.passed
        assert len(report.violations) == 0
        assert RiskLevel.LOW == report.risk_level

    def test_syntax_error_detected(self):
        """Test that syntax errors are detected."""
        validator = CodeValidator()
        code = "if True"  # Missing colon

        report = validator.validate(code)

        assert not report.passed
        assert len(report.violations) > 0
        assert any(v.type == ViolationType.DANGEROUS_CODE for v in report.violations)
        assert any("syntax" in v.message.lower() for v in report.violations)


class TestDangerousImportsDetection:
    """Tests for dangerous module import detection."""

    def test_os_import_blocked(self):
        """Test that os module import is blocked."""
        validator = CodeValidator()
        code = "import os"

        report = validator.validate(code)

        assert not report.passed
        os_violations = [v for v in report.violations if 'os' in v.message]
        assert len(os_violations) > 0
        assert os_violations[0].severity == RiskLevel.CRITICAL

    def test_subprocess_import_blocked(self):
        """Test that subprocess import is blocked."""
        validator = CodeValidator()
        code = "import subprocess"

        report = validator.validate(code)

        assert not report.passed
        assert any('subprocess' in v.message for v in report.violations)

    def test_from_import_blocked(self):
        """Test that 'from X import Y' dangerous imports are blocked."""
        validator = CodeValidator()
        code = "from os import path"

        report = validator.validate(code)

        assert not report.passed
        assert any('os' in v.message for v in report.violations)

    def test_safe_imports_allowed(self):
        """Test that safe imports are allowed."""
        validator = CodeValidator()
        code = """
import numpy as np
import pandas as pd
from scipy import stats
"""
        report = validator.validate(code)

        # Should pass (no dangerous imports)
        import_violations = [
            v for v in report.violations
            if v.type == ViolationType.DANGEROUS_CODE
        ]
        assert len(import_violations) == 0

    def test_multiple_dangerous_imports(self):
        """Test detection of multiple dangerous imports."""
        validator = CodeValidator()
        code = """
import os
import subprocess
import socket
"""
        report = validator.validate(code)

        assert not report.passed
        assert len(report.violations) >= 3


class TestDangerousPatternsDetection:
    """Tests for dangerous code pattern detection."""

    def test_eval_blocked(self):
        """Test that eval() is blocked."""
        validator = CodeValidator()
        code = "result = eval('1 + 1')"

        report = validator.validate(code)

        assert not report.passed
        assert any('eval' in v.message.lower() for v in report.violations)

    def test_exec_blocked(self):
        """Test that exec() is blocked."""
        validator = CodeValidator()
        code = "exec('print(1)')"

        report = validator.validate(code)

        assert not report.passed
        assert any('exec' in v.message.lower() for v in report.violations)

    def test_file_read_allowed_when_permitted(self):
        """Test that file read is allowed when permitted."""
        validator = CodeValidator(allow_file_read=True)
        code = "with open('data.txt', 'r') as f: data = f.read()"

        report = validator.validate(code)

        # Should pass but with warning
        assert report.passed
        assert len(report.warnings) > 0

    def test_file_write_blocked_by_default(self):
        """Test that file write is blocked by default."""
        validator = CodeValidator(allow_file_read=True, allow_file_write=False)
        code = "with open('output.txt', 'w') as f: f.write('test')"

        report = validator.validate(code)

        assert not report.passed
        assert any(
            v.type == ViolationType.FILE_SYSTEM_ACCESS
            for v in report.violations
        )

    def test_file_write_allowed_when_permitted(self):
        """Test that file write is allowed when permitted."""
        validator = CodeValidator(allow_file_write=True)
        code = "with open('output.txt', 'w') as f: f.write('test')"

        report = validator.validate(code)

        # Should have warning but pass
        assert report.passed or len(report.warnings) > 0

    def test_compile_blocked(self):
        """Test that compile() is blocked."""
        validator = CodeValidator()
        code = "code_obj = compile('x = 1', 'string', 'exec')"

        report = validator.validate(code)

        assert not report.passed
        assert any('compile' in v.message.lower() for v in report.violations)


class TestNetworkOperationsDetection:
    """Tests for network operation detection."""

    def test_network_operations_generate_warnings(self):
        """Test that network operations generate warnings."""
        validator = CodeValidator(allow_network=False)
        code = """
import requests
response = requests.get('http://example.com')
"""
        report = validator.validate(code)

        # Should have violations for dangerous import and warnings for network
        assert not report.passed  # Due to requests import
        assert len(report.warnings) > 0

    def test_network_keywords_detected(self):
        """Test that network keywords are detected in code."""
        validator = CodeValidator(allow_network=False)
        code = "# This code uses HTTP API calls"

        report = validator.validate(code)

        assert len(report.warnings) > 0
        assert any('http' in w.lower() for w in report.warnings)


class TestEthicalGuidelinesValidation:
    """Tests for ethical guidelines validation."""

    def test_harm_keyword_triggers_violation(self):
        """Test that harm-related keywords trigger violations."""
        validator = CodeValidator()
        code = "# This experiment could cause harm to participants"

        report = validator.validate(code)

        # Should detect ethical violation
        ethical_violations = [
            v for v in report.violations
            if v.type == ViolationType.ETHICAL_VIOLATION
        ]
        assert len(ethical_violations) > 0
        assert ethical_violations[0].severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_pii_keyword_triggers_violation(self):
        """Test that PII keywords trigger violations."""
        validator = CodeValidator()
        context = {"description": "Collect email and SSN from users"}

        report = validator.validate("import pandas", context=context)

        ethical_violations = [
            v for v in report.violations
            if v.type == ViolationType.ETHICAL_VIOLATION
        ]
        assert len(ethical_violations) > 0

    def test_human_subjects_keyword_triggers_violation(self):
        """Test that human subjects keywords trigger violations."""
        validator = CodeValidator()
        code = "# Experiment on human subjects without consent"

        report = validator.validate(code)

        ethical_violations = [
            v for v in report.violations
            if v.type == ViolationType.ETHICAL_VIOLATION
        ]
        assert len(ethical_violations) > 0

    def test_safe_code_without_ethical_issues(self):
        """Test that safe code without ethical issues passes."""
        validator = CodeValidator()
        code = """
import numpy as np
data = np.random.randn(100, 10)
mean = np.mean(data, axis=0)
"""
        report = validator.validate(code)

        ethical_violations = [
            v for v in report.violations
            if v.type == ViolationType.ETHICAL_VIOLATION
        ]
        assert len(ethical_violations) == 0

    def test_context_checked_for_ethical_issues(self):
        """Test that context is checked for ethical issues."""
        validator = CodeValidator()
        code = "x = 1"  # Innocent code
        context = {"hypothesis": "Testing weapon effectiveness on animals"}

        report = validator.validate(code, context=context)

        # Should detect ethical violations in context
        ethical_violations = [
            v for v in report.violations
            if v.type == ViolationType.ETHICAL_VIOLATION
        ]
        assert len(ethical_violations) > 0


class TestRiskAssessment:
    """Tests for risk level assessment."""

    def test_no_violations_is_low_risk(self):
        """Test that no violations result in low risk."""
        validator = CodeValidator()
        code = "x = 1 + 1"

        report = validator.validate(code)

        assert report.risk_level == RiskLevel.LOW

    def test_critical_violation_is_critical_risk(self):
        """Test that critical violations result in critical risk."""
        validator = CodeValidator()
        code = "import os"

        report = validator.validate(code)

        assert report.risk_level == RiskLevel.CRITICAL

    def test_high_severity_violation_is_high_risk(self):
        """Test that high severity violations result in high risk."""
        validator = CodeValidator(allow_file_read=False)
        code = "with open('file.txt', 'r') as f: pass"

        report = validator.validate(code)

        assert report.risk_level == RiskLevel.HIGH

    def test_risk_is_highest_severity(self):
        """Test that risk level is the highest severity violation."""
        validator = CodeValidator()
        code = """
# Cause harm  # High severity
import os     # Critical severity
"""
        report = validator.validate(code)

        # Should be critical (highest)
        assert report.risk_level == RiskLevel.CRITICAL


class TestApprovalRequirements:
    """Tests for approval requirement logic."""

    @patch('kosmos.safety.code_validator.get_config')
    def test_requires_approval_when_configured(self, mock_get_config):
        """Test that approval is required when configured."""
        mock_config = Mock()
        mock_config.safety.require_human_approval = True
        mock_get_config.return_value = mock_config

        validator = CodeValidator()
        report = SafetyReport(
            passed=True,
            risk_level=RiskLevel.LOW,
            violations=[],
            warnings=[]
        )

        assert validator.requires_approval(report) is True

    @patch('kosmos.safety.code_validator.get_config')
    def test_requires_approval_for_high_risk(self, mock_get_config):
        """Test that approval is required for high risk."""
        mock_config = Mock()
        mock_config.safety.require_human_approval = False
        mock_get_config.return_value = mock_config

        validator = CodeValidator()
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.HIGH,
            violations=[]
        )

        assert validator.requires_approval(report) is True

    @patch('kosmos.safety.code_validator.get_config')
    def test_requires_approval_for_critical_violations(self, mock_get_config):
        """Test that approval is required for critical violations."""
        mock_config = Mock()
        mock_config.safety.require_human_approval = False
        mock_get_config.return_value = mock_config

        validator = CodeValidator()
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.CRITICAL,
            violations=[],
        )

        assert validator.requires_approval(report) is True

    @patch('kosmos.safety.code_validator.get_config')
    def test_requires_approval_for_ethical_violations(self, mock_get_config):
        """Test that approval is required for ethical violations."""
        from kosmos.models.safety import SafetyViolation

        mock_config = Mock()
        mock_config.safety.require_human_approval = False
        mock_get_config.return_value = mock_config

        validator = CodeValidator()
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.MEDIUM,
            violations=[
                SafetyViolation(
                    type=ViolationType.ETHICAL_VIOLATION,
                    severity=RiskLevel.HIGH,
                    message="Ethical issue detected"
                )
            ]
        )

        assert validator.requires_approval(report) is True

    @patch('kosmos.safety.code_validator.get_config')
    def test_no_approval_needed_for_safe_code(self, mock_get_config):
        """Test that approval is not required for safe code."""
        mock_config = Mock()
        mock_config.safety.require_human_approval = False
        mock_get_config.return_value = mock_config

        validator = CodeValidator()
        report = SafetyReport(
            passed=True,
            risk_level=RiskLevel.LOW,
            violations=[]
        )

        assert validator.requires_approval(report) is False


class TestApprovalRequestCreation:
    """Tests for approval request creation."""

    def test_creates_approval_request_with_details(self):
        """Test that approval request is created with correct details."""
        from kosmos.models.safety import SafetyViolation

        validator = CodeValidator()
        code = "import os"
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.CRITICAL,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.CRITICAL,
                    message="Dangerous import: os"
                )
            ]
        )

        request = validator.create_approval_request(code, report)

        assert request.operation_type == "code_execution"
        assert request.risk_level == RiskLevel.CRITICAL
        assert request.status == ApprovalStatus.PENDING
        assert "Dangerous import" in request.operation_description
        assert code[:500] in request.context["code"]

    def test_approval_request_includes_context(self):
        """Test that approval request includes provided context."""
        from kosmos.models.safety import SafetyViolation

        validator = CodeValidator()
        code = "import os"
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.HIGH,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.HIGH,
                    message="Issue"
                )
            ]
        )
        context = {"experiment_id": "exp_123", "hypothesis": "Test hypothesis"}

        request = validator.create_approval_request(code, report, context)

        assert request.context["experiment_id"] == "exp_123"
        assert request.context["hypothesis"] == "Test hypothesis"

    def test_approval_request_has_unique_id(self):
        """Test that approval requests have unique IDs."""
        from kosmos.models.safety import SafetyViolation

        validator = CodeValidator()
        code = "x = 1"
        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.LOW,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.LOW,
                    message="Issue"
                )
            ]
        )

        request1 = validator.create_approval_request(code, report)
        request2 = validator.create_approval_request(code, report)

        assert request1.request_id != request2.request_id
        assert request1.request_id.startswith("approval_")


class TestSafetyReportMethods:
    """Tests for SafetyReport helper methods."""

    def test_has_violations(self):
        """Test has_violations method."""
        from kosmos.models.safety import SafetyViolation

        report_with = SafetyReport(
            passed=False,
            risk_level=RiskLevel.HIGH,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.HIGH,
                    message="Issue"
                )
            ]
        )
        report_without = SafetyReport(
            passed=True,
            risk_level=RiskLevel.LOW,
            violations=[]
        )

        assert report_with.has_violations() is True
        assert report_without.has_violations() is False

    def test_has_critical_violations(self):
        """Test has_critical_violations method."""
        from kosmos.models.safety import SafetyViolation

        report_critical = SafetyReport(
            passed=False,
            risk_level=RiskLevel.CRITICAL,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.CRITICAL,
                    message="Critical issue"
                )
            ]
        )
        report_low = SafetyReport(
            passed=False,
            risk_level=RiskLevel.LOW,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.LOW,
                    message="Minor issue"
                )
            ]
        )

        assert report_critical.has_critical_violations() is True
        assert report_low.has_critical_violations() is False

    def test_get_violations_by_type(self):
        """Test get_violations_by_type method."""
        from kosmos.models.safety import SafetyViolation

        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.HIGH,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.HIGH,
                    message="Code issue"
                ),
                SafetyViolation(
                    type=ViolationType.ETHICAL_VIOLATION,
                    severity=RiskLevel.HIGH,
                    message="Ethical issue"
                ),
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.MEDIUM,
                    message="Another code issue"
                )
            ]
        )

        code_violations = report.get_violations_by_type(ViolationType.DANGEROUS_CODE)
        ethical_violations = report.get_violations_by_type(ViolationType.ETHICAL_VIOLATION)

        assert len(code_violations) == 2
        assert len(ethical_violations) == 1

    def test_summary_passed(self):
        """Test summary for passed report."""
        report = SafetyReport(
            passed=True,
            risk_level=RiskLevel.LOW,
            violations=[]
        )

        summary = report.summary()

        assert "✓" in summary or "passed" in summary.lower()
        assert "low" in summary.lower()

    def test_summary_failed(self):
        """Test summary for failed report."""
        from kosmos.models.safety import SafetyViolation

        report = SafetyReport(
            passed=False,
            risk_level=RiskLevel.HIGH,
            violations=[
                SafetyViolation(
                    type=ViolationType.DANGEROUS_CODE,
                    severity=RiskLevel.HIGH,
                    message="Issue"
                )
            ],
            warnings=["Warning 1"]
        )

        summary = report.summary()

        assert "✗" in summary or "failed" in summary.lower()
        assert "1 violations" in summary.lower() or "1 violation" in summary.lower()
        assert "1 warnings" in summary.lower() or "1 warning" in summary.lower()
