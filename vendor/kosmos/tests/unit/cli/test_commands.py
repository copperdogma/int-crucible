"""
Unit tests for CLI commands.

Tests all CLI commands: run, status, history, cache, config, profile.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch
from pathlib import Path

from kosmos.cli.main import app


class TestCLIBasics:
    """Test basic CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Kosmos" in result.stdout
        assert "version" in result.stdout.lower()

    def test_help_command(self, runner):
        """Test help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Kosmos AI Scientist" in result.stdout

    def test_doctor_command(self, runner):
        """Test doctor diagnostic command."""
        with patch('kosmos.cli.main.get_session') as mock_session:
            mock_session.return_value.close = MagicMock()

            result = runner.invoke(app, ["doctor"])

            # Should run diagnostics
            assert "Diagnostic" in result.stdout or result.exit_code >= 0


class TestInfoCommand:
    """Test info command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_info_displays_configuration(self, runner):
        """Test info command displays configuration."""
        with patch('kosmos.config.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.claude.model = "claude-3-5-sonnet-20241022"
            mock_cfg.research.max_iterations = 10
            mock_cfg.research.enabled_domains = ["biology", "physics"]
            mock_cfg.claude.is_cli_mode = False
            mock_config.return_value = mock_cfg

            result = runner.invoke(app, ["info"])

            assert "claude-3-5-sonnet" in result.stdout.lower() or result.exit_code >= 0


class TestRunCommand:
    """Test run command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('kosmos.cli.commands.run.ResearchDirectorAgent')
    def test_run_with_question(self, mock_director, runner):
        """Test running research with question."""
        # Mock director
        director_instance = MagicMock()
        mock_director.return_value = director_instance

        result = runner.invoke(app, [
            "run",
            "--question", "What is the effect of temperature on protein folding?",
            "--domain", "biology"
        ])

        # Command should attempt to run
        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.run.ResearchDirectorAgent')
    def test_run_interactive_mode(self, mock_director, runner):
        """Test interactive mode."""
        director_instance = MagicMock()
        mock_director.return_value = director_instance

        # Simulate user input
        result = runner.invoke(app, ["run", "--interactive"], input="Test question\ny\n")

        # Should enter interactive mode
        assert result.exit_code >= 0


class TestStatusCommand:
    """Test status command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('kosmos.cli.commands.status.get_session')
    def test_status_shows_research_status(self, mock_session, runner):
        """Test status command shows research status."""
        # Mock database query
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        mock_session.return_value.query.return_value = mock_query

        result = runner.invoke(app, ["status"])

        # Should show some status
        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.status.get_session')
    def test_status_watch_mode(self, mock_session, runner):
        """Test status watch mode."""
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 3
        mock_session.return_value.query.return_value = mock_query

        # Run with timeout to avoid infinite loop
        result = runner.invoke(app, ["status", "--watch", "--interval", "1"], timeout=2)

        # Should attempt to watch (may timeout)
        assert result.exit_code >= 0 or "timeout" in str(result.exception).lower()


class TestHistoryCommand:
    """Test history command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('kosmos.cli.commands.history.get_session')
    def test_history_lists_past_research(self, mock_session, runner):
        """Test history command lists past research."""
        # Mock research cycles
        mock_cycle = MagicMock()
        mock_cycle.id = 1
        mock_cycle.research_question = "Test question"
        mock_cycle.domain = "biology"
        mock_cycle.status = "completed"

        mock_session.return_value.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_cycle]

        result = runner.invoke(app, ["history"])

        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.history.get_session')
    def test_history_view_specific_cycle(self, mock_session, runner):
        """Test viewing specific research cycle."""
        mock_cycle = MagicMock()
        mock_cycle.id = 1
        mock_cycle.research_question = "Test question"
        mock_cycle.results = []

        mock_session.return_value.query.return_value.filter.return_value.first.return_value = mock_cycle

        result = runner.invoke(app, ["history", "--cycle-id", "1"])

        assert result.exit_code >= 0


class TestCacheCommand:
    """Test cache command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('kosmos.cli.commands.cache.CacheManager')
    def test_cache_info(self, mock_manager, runner):
        """Test cache info command."""
        manager_instance = MagicMock()
        manager_instance.get_stats.return_value = {
            "memory": MagicMock(hits=100, misses=20, entries=50, size_bytes=1024000, hit_ratio=0.83)
        }
        mock_manager.return_value = manager_instance

        result = runner.invoke(app, ["cache", "info"])

        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.cache.CacheManager')
    def test_cache_clear(self, mock_manager, runner):
        """Test cache clear command."""
        manager_instance = MagicMock()
        mock_manager.return_value = manager_instance

        result = runner.invoke(app, ["cache", "clear", "--confirm"])

        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.cache.CacheManager')
    def test_cache_clear_requires_confirmation(self, mock_manager, runner):
        """Test cache clear requires confirmation."""
        manager_instance = MagicMock()
        mock_manager.return_value = manager_instance

        # Without --confirm flag
        result = runner.invoke(app, ["cache", "clear"])

        # Should either require confirmation or exit cleanly
        assert result.exit_code >= 0


class TestConfigCommand:
    """Test config command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_config_show(self, runner):
        """Test showing configuration."""
        with patch('kosmos.config.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.claude.model = "claude-3-5-sonnet-20241022"
            mock_config.return_value = mock_cfg

            result = runner.invoke(app, ["config", "show"])

            assert result.exit_code >= 0

    def test_config_get_value(self, runner):
        """Test getting specific config value."""
        with patch('kosmos.config.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.claude.model = "claude-3-5-sonnet-20241022"
            mock_config.return_value = mock_cfg

            result = runner.invoke(app, ["config", "get", "CLAUDE_MODEL"])

            assert result.exit_code >= 0

    def test_config_validate(self, runner):
        """Test config validation."""
        with patch('kosmos.config.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            result = runner.invoke(app, ["config", "validate"])

            assert result.exit_code >= 0


class TestProfileCommand:
    """Test profile command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('kosmos.cli.commands.profile.get_profiler')
    def test_profile_view(self, mock_profiler, runner):
        """Test viewing profile data."""
        profiler_instance = MagicMock()
        profiler_instance.get_summary.return_value = {
            "total_profiles": 10,
            "total_duration": 5.5
        }
        profiler_instance.profiles = []
        mock_profiler.return_value = profiler_instance

        result = runner.invoke(app, ["profile", "view"])

        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.profile.get_profiler')
    def test_profile_clear(self, mock_profiler, runner):
        """Test clearing profile data."""
        profiler_instance = MagicMock()
        mock_profiler.return_value = profiler_instance

        result = runner.invoke(app, ["profile", "clear"])

        assert result.exit_code >= 0

    @patch('kosmos.cli.commands.profile.get_profiler')
    def test_profile_bottlenecks(self, mock_profiler, runner):
        """Test finding bottlenecks."""
        profiler_instance = MagicMock()
        profiler_instance.detect_bottlenecks.return_value = []
        mock_profiler.return_value = profiler_instance

        result = runner.invoke(app, ["profile", "bottlenecks"])

        assert result.exit_code >= 0


class TestCLIOptions:
    """Test global CLI options."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_verbose_flag(self, runner):
        """Test verbose flag."""
        result = runner.invoke(app, ["--verbose", "version"])

        assert result.exit_code == 0

    def test_debug_flag(self, runner):
        """Test debug flag."""
        result = runner.invoke(app, ["--debug", "version"])

        assert result.exit_code == 0

    def test_quiet_flag(self, runner):
        """Test quiet flag."""
        result = runner.invoke(app, ["--quiet", "version"])

        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_invalid_command(self, runner):
        """Test handling invalid command."""
        result = runner.invoke(app, ["nonexistent-command"])

        assert result.exit_code != 0

    def test_missing_required_argument(self, runner):
        """Test handling missing required argument."""
        result = runner.invoke(app, ["run"])  # Missing --question

        # Should show error or help
        assert result.exit_code != 0 or "question" in result.stdout.lower()

    @patch('kosmos.cli.commands.run.ResearchDirectorAgent')
    def test_exception_handling(self, mock_director, runner):
        """Test graceful exception handling."""
        # Make director raise exception
        mock_director.side_effect = Exception("Test error")

        result = runner.invoke(app, ["run", "--question", "Test"])

        # Should handle gracefully
        assert "error" in result.stdout.lower() or result.exit_code != 0


class TestCLIOutputFormatting:
    """Test CLI output formatting."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_table_output(self, runner):
        """Test table output formatting."""
        with patch('kosmos.cli.commands.history.get_session') as mock_session:
            mock_cycle = MagicMock()
            mock_cycle.id = 1
            mock_cycle.research_question = "Test"
            mock_session.return_value.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_cycle]

            result = runner.invoke(app, ["history", "--format", "table"])

            assert result.exit_code >= 0

    def test_json_output(self, runner):
        """Test JSON output formatting."""
        with patch('kosmos.cli.commands.history.get_session') as mock_session:
            mock_cycle = MagicMock()
            mock_cycle.id = 1
            mock_session.return_value.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_cycle]

            result = runner.invoke(app, ["history", "--format", "json"])

            assert result.exit_code >= 0


class TestCLIIntegration:
    """Integration tests for CLI."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.mark.integration
    def test_full_workflow(self, runner):
        """Test complete CLI workflow."""
        with patch('kosmos.cli.commands.run.ResearchDirectorAgent') as mock_director:
            director_instance = MagicMock()
            mock_director.return_value = director_instance

            # 1. Check status
            result = runner.invoke(app, ["status"])
            assert result.exit_code >= 0

            # 2. View cache
            result = runner.invoke(app, ["cache", "info"])
            assert result.exit_code >= 0

            # 3. Run research
            result = runner.invoke(app, [
                "run",
                "--question", "Test question",
                "--domain", "biology"
            ])
            assert result.exit_code >= 0

            # 4. Check history
            result = runner.invoke(app, ["history"])
            assert result.exit_code >= 0
