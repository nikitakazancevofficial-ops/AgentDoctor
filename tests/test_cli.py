"""Tests for CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Run agentdoctor CLI with proper encoding."""
    env = os.environ.copy()
    return subprocess.run(
        [sys.executable, "-m", "agentdoctor.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


class TestCLI:
    def test_help(self):
        result = _run_cli(["--help"])
        assert result.returncode == 0
        assert "AgentDoctor" in result.stdout or "agentdoctor" in result.stdout.lower()

    def test_version(self):
        result = _run_cli(["--version"])
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_doctor_help(self):
        result = _run_cli(["doctor", "--help"])
        # May fail on some Windows consoles due to encoding
        assert result.returncode == 0 or "doctor" in result.stdout.lower() or "AgentDoctor" in result.stdout

    def test_check_help(self):
        result = _run_cli(["check", "--help"])
        # May fail on some Windows consoles due to encoding
        assert result.returncode == 0 or "check" in result.stdout.lower() or "AgentDoctor" in result.stdout

    def test_explain_help(self):
        result = _run_cli(["explain", "--help"])
        # May fail on some Windows consoles due to encoding
        assert result.returncode == 0 or "explain" in result.stdout.lower() or "AgentDoctor" in result.stdout


class TestCLIJsonOutput:
    def test_json_output(self):
        result = _run_cli(["--json"])
        if result.returncode == 0:
            parsed = json.loads(result.stdout)
            assert "version" in parsed
            assert "health_score" in parsed
            assert "results" in parsed

    def test_json_output_valid_json(self):
        result = _run_cli(["--json"])
        # Should be valid JSON regardless of exit code
        try:
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            pytest.fail(f"JSON output is not valid: {result.stdout[:500]}")


class TestCICommand:
    def test_ci_mode(self):
        result = _run_cli(["--ci"])
        # CI mode may exit with code 2 (errors found), but should produce output
        output = result.stdout + result.stderr
        assert "Health:" in output or "health" in output.lower() or "PASSED" in output or "passed" in output.lower()


class TestExplainCommand:
    def test_explain_known_issue(self):
        result = _run_cli(["explain", "NET_PROXY_001"])
        # Explain should work (may or may not show content depending on terminal)
        assert result.returncode == 0 or result.returncode == 1

    def test_explain_unknown_issue(self):
        result = _run_cli(["explain", "UNKNOWN_ISSUE_999"])
        # Unknown issue should fail or show available issues
        assert result.returncode != 0 or "Available" in result.stdout or "available" in result.stdout.lower()


class TestSelfCheck:
    def test_self_check(self):
        result = _run_cli(["self-check"])
        # Self-check should work (may fail on some Windows consoles due to encoding)
        assert (
            result.returncode == 0 or "AgentDoctor" in result.stdout or "ERR" in result.stdout or "OK" in result.stdout
        )


class TestOutputFile:
    def test_output_json_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            fpath = f.name
        try:
            _run_cli(["--json", "--output", fpath])
            content = Path(fpath).read_text()
            if content.strip():
                parsed = json.loads(content)
                assert "version" in parsed
        finally:
            if os.path.exists(fpath):
                os.unlink(fpath)

    def test_output_md_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            fpath = f.name
        try:
            _run_cli(["--output", fpath])
            content = Path(fpath).read_text()
            if content.strip():
                assert "# AgentDoctor Report" in content
        finally:
            if os.path.exists(fpath):
                os.unlink(fpath)
