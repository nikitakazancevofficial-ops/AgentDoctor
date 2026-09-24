"""Tests for missing executable handling."""

from agentdoctor.checks.tools import _check_tool, check_tools


class TestMissingExecutable:
    def test_missing_tool_detection(self):
        found, version = _check_tool("nonexistent-tool-xyz123456")
        assert not found
        assert version == ""

    def test_tools_check_runs(self):
        results = check_tools()
        assert isinstance(results, list)
        for r in results:
            assert hasattr(r, "id")
            assert hasattr(r, "category")
            assert hasattr(r, "status")


class TestSubprocessTimeout:
    def test_command_timeout(self):
        """Test that timed-out commands are handled gracefully."""
        import sys

        from agentdoctor.core.runner import run_command_sync

        if sys.platform == "win32":
            cmd = ["ping", "-n", "100", "127.0.0.1"]
        else:
            cmd = ["sleep", "3600"]

        result = run_command_sync(cmd, timeout=0.1)
        assert result.timed_out or result.exception
