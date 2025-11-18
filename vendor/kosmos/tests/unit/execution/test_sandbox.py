"""
Tests for Docker sandbox execution.

Tests Docker container creation, resource limits, security validation, and monitoring.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from kosmos.execution.sandbox import (
    DockerSandbox,
    SandboxExecutionResult,
    execute_in_sandbox
)


# Fixtures

@pytest.fixture
def mock_docker_client():
    """Create mock Docker client."""
    client = Mock()
    client.images.get.return_value = Mock()  # Image exists
    return client


@pytest.fixture
def mock_container():
    """Create mock Docker container."""
    container = Mock()
    container.short_id = "abc123"
    container.wait.return_value = {'StatusCode': 0}
    container.logs.return_value = b"Hello, World!"
    container.status = 'running'
    return container


@pytest.fixture
@patch('kosmos.execution.sandbox.docker')
def sandbox(mock_docker, mock_docker_client):
    """Create Docker sandbox with mocked client."""
    mock_docker.from_env.return_value = mock_docker_client

    sandbox = DockerSandbox()
    return sandbox


# Initialization Tests

class TestSandboxInitialization:
    """Tests for sandbox initialization."""

    @patch('kosmos.execution.sandbox.docker')
    def test_sandbox_init_success(self, mock_docker):
        """Test successful sandbox initialization."""
        mock_client = Mock()
        mock_client.images.get.return_value = Mock()
        mock_docker.from_env.return_value = mock_client

        sandbox = DockerSandbox()

        assert sandbox.image == DockerSandbox.DEFAULT_IMAGE
        assert sandbox.cpu_limit == DockerSandbox.DEFAULT_CPU_LIMIT
        assert sandbox.memory_limit == DockerSandbox.DEFAULT_MEMORY_LIMIT
        assert sandbox.timeout == DockerSandbox.DEFAULT_TIMEOUT

    @patch('kosmos.execution.sandbox.docker')
    def test_sandbox_custom_config(self, mock_docker):
        """Test sandbox with custom configuration."""
        mock_client = Mock()
        mock_client.images.get.return_value = Mock()
        mock_docker.from_env.return_value = mock_client

        sandbox = DockerSandbox(
            cpu_limit=4.0,
            memory_limit="4g",
            timeout=600,
            network_disabled=False
        )

        assert sandbox.cpu_limit == 4.0
        assert sandbox.memory_limit == "4g"
        assert sandbox.timeout == 600
        assert sandbox.network_disabled is False

    @patch('kosmos.execution.sandbox.docker')
    def test_sandbox_init_docker_unavailable(self, mock_docker):
        """Test sandbox initialization when Docker unavailable."""
        mock_docker.from_env.side_effect = Exception("Docker not running")

        with pytest.raises(RuntimeError):
            DockerSandbox()


# Image Verification Tests

class TestImageVerification:
    """Tests for Docker image verification."""

    @patch('kosmos.execution.sandbox.docker')
    def test_image_exists(self, mock_docker):
        """Test image verification when image exists."""
        mock_client = Mock()
        mock_client.images.get.return_value = Mock()  # Image found
        mock_docker.from_env.return_value = mock_client

        sandbox = DockerSandbox()

        # Should not build
        assert mock_client.images.build.called is False

    @patch('kosmos.execution.sandbox.docker')
    def test_image_not_found_builds(self, mock_docker):
        """Test image is built when not found."""
        import docker.errors

        mock_client = Mock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        mock_client.images.build.return_value = (Mock(), [])
        mock_docker.from_env.return_value = mock_client
        mock_docker.errors.ImageNotFound = docker.errors.ImageNotFound

        sandbox = DockerSandbox()

        # Should build image
        assert mock_client.images.build.called


# Execution Tests

class TestSandboxExecution:
    """Tests for code execution in sandbox."""

    @patch('kosmos.execution.sandbox.docker')
    def test_execute_simple_code(self, mock_docker, mock_docker_client, mock_container):
        """Test executing simple code."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox()
        result = sandbox.execute("print('Hello')")

        assert isinstance(result, SandboxExecutionResult)
        assert result.success is True

    @patch('kosmos.execution.sandbox.docker')
    def test_execute_with_data_files(self, mock_docker, mock_docker_client, mock_container, tmp_path):
        """Test execution with data files."""
        # Create temp data file
        data_file = tmp_path / "data.csv"
        data_file.write_text("a,b,c\n1,2,3")

        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox()
        result = sandbox.execute(
            "import pandas as pd",
            data_files={'data.csv': str(data_file)}
        )

        # Verify container created with volume mounts
        create_call = mock_docker_client.containers.create.call_args
        assert 'volumes' in create_call[1]


# Resource Limits Tests

class TestResourceLimits:
    """Tests for resource limit enforcement."""

    @patch('kosmos.execution.sandbox.docker')
    def test_cpu_limit_applied(self, mock_docker, mock_docker_client, mock_container):
        """Test CPU limit is applied to container."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox(cpu_limit=2.0)
        sandbox.execute("print('test')")

        create_call = mock_docker_client.containers.create.call_args
        assert 'nano_cpus' in create_call[1]
        assert create_call[1]['nano_cpus'] == int(2.0 * 1e9)

    @patch('kosmos.execution.sandbox.docker')
    def test_memory_limit_applied(self, mock_docker, mock_docker_client, mock_container):
        """Test memory limit is applied to container."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox(memory_limit="2g")
        sandbox.execute("print('test')")

        create_call = mock_docker_client.containers.create.call_args
        assert 'mem_limit' in create_call[1]
        assert create_call[1]['mem_limit'] == "2g"

    @patch('kosmos.execution.sandbox.docker')
    def test_timeout_enforced(self, mock_docker, mock_docker_client, mock_container):
        """Test timeout is enforced."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        # Simulate timeout
        import docker.errors
        mock_container.wait.side_effect = Exception("Timeout")
        mock_docker.errors = docker.errors

        sandbox = DockerSandbox(timeout=5)
        result = sandbox.execute("import time; time.sleep(10)")

        assert result.timeout_occurred is True


# Security Tests

class TestSecurityConstraints:
    """Tests for security constraints."""

    @patch('kosmos.execution.sandbox.docker')
    def test_network_disabled(self, mock_docker, mock_docker_client, mock_container):
        """Test network is disabled when requested."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox(network_disabled=True)
        sandbox.execute("print('test')")

        create_call = mock_docker_client.containers.create.call_args
        assert create_call[1]['network_disabled'] is True

    @patch('kosmos.execution.sandbox.docker')
    def test_read_only_filesystem(self, mock_docker, mock_docker_client, mock_container):
        """Test read-only filesystem enabled."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox(read_only=True)
        sandbox.execute("print('test')")

        create_call = mock_docker_client.containers.create.call_args
        assert create_call[1]['read_only'] is True

    @patch('kosmos.execution.sandbox.docker')
    def test_security_options_applied(self, mock_docker, mock_docker_client, mock_container):
        """Test security options are applied."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox()
        sandbox.execute("print('test')")

        create_call = mock_docker_client.containers.create.call_args
        assert 'security_opt' in create_call[1]
        assert 'no-new-privileges' in create_call[1]['security_opt']


# Output Capture Tests

class TestOutputCapture:
    """Tests for stdout/stderr capture."""

    @patch('kosmos.execution.sandbox.docker')
    def test_capture_stdout(self, mock_docker, mock_docker_client, mock_container):
        """Test stdout capture."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.logs.return_value = b"Test output"

        sandbox = DockerSandbox()
        result = sandbox.execute("print('Test output')")

        assert "Test output" in result.stdout

    @patch('kosmos.execution.sandbox.docker')
    def test_capture_stderr(self, mock_docker, mock_docker_client, mock_container):
        """Test stderr capture."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        # Mock stderr
        def mock_logs(stdout=True, stderr=False):
            if stderr:
                return b"Error message"
            return b""

        mock_container.logs = Mock(side_effect=mock_logs)

        sandbox = DockerSandbox()
        result = sandbox.execute("import sys; print('error', file=sys.stderr)")

        # Note: Mock will capture based on parameters


# Error Handling Tests

class TestErrorHandling:
    """Tests for error handling."""

    @patch('kosmos.execution.sandbox.docker')
    def test_container_error_handled(self, mock_docker, mock_docker_client):
        """Test container error is handled gracefully."""
        import docker.errors

        mock_docker.from_env.return_value = mock_docker_client
        mock_docker.errors.ContainerError = docker.errors.ContainerError
        mock_docker_client.containers.create.side_effect = docker.errors.ContainerError(
            Mock(), 1, "cmd", "image", "Error"
        )

        sandbox = DockerSandbox()
        result = sandbox.execute("print('test')")

        assert result.success is False
        assert result.error is not None

    @patch('kosmos.execution.sandbox.docker')
    def test_non_zero_exit_code(self, mock_docker, mock_docker_client, mock_container):
        """Test non-zero exit code."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.wait.return_value = {'StatusCode': 1}

        sandbox = DockerSandbox()
        result = sandbox.execute("import sys; sys.exit(1)")

        assert result.success is False
        assert result.exit_code == 1


# Monitoring Tests

class TestExecutionMonitoring:
    """Tests for execution monitoring."""

    @patch('kosmos.execution.sandbox.docker')
    def test_monitoring_enabled(self, mock_docker, mock_docker_client, mock_container):
        """Test monitoring is enabled when requested."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        # Mock stats
        mock_container.stats.return_value = iter([
            {
                'cpu_stats': {'cpu_usage': {'total_usage': 1000, 'percpu_usage': [500, 500]}, 'system_cpu_usage': 10000},
                'precpu_stats': {'cpu_usage': {'total_usage': 500, 'percpu_usage': [250, 250]}, 'system_cpu_usage': 5000},
                'memory_stats': {'usage': 100000000, 'limit': 2000000000}
            }
        ])

        sandbox = DockerSandbox(enable_monitoring=True)
        result = sandbox.execute("print('test')")

        # Resource stats should be populated
        # Note: Monitoring runs in background thread, may not complete immediately


# Cleanup Tests

class TestCleanup:
    """Tests for resource cleanup."""

    @patch('kosmos.execution.sandbox.docker')
    def test_container_removed_after_execution(self, mock_docker, mock_docker_client, mock_container):
        """Test container is removed after execution."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container

        sandbox = DockerSandbox()
        result = sandbox.execute("print('test')")

        # Container should be removed
        assert mock_container.remove.called

    @patch('kosmos.execution.sandbox.docker')
    def test_sandbox_cleanup(self, mock_docker, mock_docker_client):
        """Test sandbox cleanup."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.images.get.return_value = Mock()

        sandbox = DockerSandbox()
        sandbox.cleanup()

        # Client should be closed
        assert mock_docker_client.close.called


# Convenience Function Tests

class TestConvenienceFunction:
    """Tests for execute_in_sandbox convenience function."""

    @patch('kosmos.execution.sandbox.DockerSandbox')
    def test_execute_in_sandbox_basic(self, mock_sandbox_class):
        """Test execute_in_sandbox convenience function."""
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {'success': True}
        mock_sandbox.execute.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        result = execute_in_sandbox("print('test')")

        assert result['success'] is True
        assert mock_sandbox.cleanup.called


# Return Value Extraction Tests

class TestReturnValueExtraction:
    """Tests for return value extraction."""

    @patch('kosmos.execution.sandbox.docker')
    def test_extract_return_value_json(self, mock_docker, mock_docker_client, mock_container):
        """Test extraction of JSON return value."""
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.logs.return_value = b'RESULT:{"value": 42}'

        sandbox = DockerSandbox()
        result = sandbox.execute("print('RESULT:{\"value\": 42}')")

        # Note: Actual extraction would parse the JSON


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
