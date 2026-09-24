"""Tests for command runner."""

from agentdoctor.core.runner import configure_timeout, run_command, run_command_sync


class TestRunCommandSync:
    def test_configured_timeout_caps_a_longer_check_timeout(self):
        configure_timeout(0.1)
        try:
            if __import__("sys").platform == "win32":
                cmd = ["ping", "-n", "10", "127.0.0.1"]
            else:
                cmd = ["sleep", "10"]
            result = run_command_sync(cmd, timeout=5)
            assert result.timed_out
        finally:
            configure_timeout(None)

    def test_echo_command(self):
        result = run_command_sync(["python", "-c", "print('hello')"], timeout=5)
        assert result.success
        assert "hello" in result.stdout

    def test_nonexistent_command(self):
        result = run_command_sync(["nonexistent-command-xyz123"], timeout=5)
        assert not result.success

    def test_timeout(self):
        # Use sleep with very short timeout
        if __import__("sys").platform == "win32":
            cmd = ["ping", "-n", "10", "127.0.0.1"]
        else:
            cmd = ["sleep", "10"]
        result = run_command_sync(cmd, timeout=0.1)
        assert result.timed_out

    def test_empty_command(self):
        result = run_command_sync([], timeout=5)
        assert not result.success

    def test_command_with_args(self):
        result = run_command_sync(["python", "-c", "print('test123')"], timeout=5)
        assert result.success
        assert "test123" in result.stdout

    def test_stderr_capture(self):
        result = run_command_sync(["python", "-c", "import sys; sys.stderr.write('error msg')"], timeout=5)
        assert "error msg" in result.stderr

    def test_return_code(self):
        if __import__("sys").platform == "win32":
            result = run_command_sync(["cmd", "/c", "exit", "1"], timeout=5)
        else:
            result = run_command_sync(["sh", "-c", "exit 1"], timeout=5)
        assert result.return_code == 1


class TestRunCommand:
    def test_echo_command(self):
        result = run_command(["python", "-c", "print('hello')"], timeout=5)
        assert result.success
        assert "hello" in result.stdout

    def test_nonexistent_command(self):
        result = run_command(["nonexistent-command-xyz123"], timeout=5)
        assert not result.success
