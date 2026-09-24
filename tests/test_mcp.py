"""Tests for MCP config parsing."""

from pathlib import Path
from unittest.mock import patch

import pytest

from agentdoctor.core.models import CheckStatus

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_mcp_results():
    """Import and run MCP check."""
    # We need to test the MCP parsing logic directly
    from agentdoctor.checks.mcp import _parse_mcp_config, _validate_mcp_server

    return _parse_mcp_config, _validate_mcp_server


class TestMCPConfigParsing:
    def test_valid_mcp_config(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "mcp_valid.json"
        data, error = _parse_mcp_config(config_path)
        assert error is None
        assert isinstance(data, dict)
        assert "mcpServers" in data
        assert len(data["mcpServers"]) == 4

    def test_invalid_mcp_config(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "mcp_invalid.json"
        _data, error = _parse_mcp_config(config_path)
        assert error is not None
        assert "Line" in error

    def test_invalid_json_content(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "invalid.json"
        _data, error = _parse_mcp_config(config_path)
        assert error is not None

    def test_missing_command_config(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "mcp_missing_command.json"
        data, error = _parse_mcp_config(config_path)
        assert error is None
        assert data is not None
        assert "mcpServers" in data

    def test_mcp_with_secret(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "mcp_with_secret.json"
        data, error = _parse_mcp_config(config_path)
        assert error is None
        assert data is not None
        env = data["mcpServers"]["secrets-server"]["env"]
        assert "OPENAI_API_KEY" in env
        assert "ANTHROPIC_API_KEY" in env

    def test_empty_env_config(self):
        from agentdoctor.checks.mcp import _parse_mcp_config

        config_path = FIXTURES_DIR / "mcp_empty_env.json"
        data, error = _parse_mcp_config(config_path)
        assert error is None
        assert data is not None
        assert data["mcpServers"]["empty-env"]["env"] == {}


class TestMCPValidation:
    @pytest.fixture
    def validate_func(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        return _validate_mcp_server

    def test_valid_stdio_server(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        config = {"command": "python", "args": ["server.py"]}
        with patch("agentdoctor.checks.mcp.shutil.which", return_value="/usr/bin/python"):
            results = _validate_mcp_server("test-server", config)
        assert results == []

    def test_missing_command(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        config = {"command": "nonexistent-command-xyz123", "args": ["--arg"]}
        with patch("agentdoctor.checks.mcp.shutil.which", return_value=None):
            results = _validate_mcp_server("test-server", config)
        assert len(results) == 1
        assert results[0].id == "MCP_COMMAND_001"
        assert results[0].status == CheckStatus.ERROR
        assert "not found" in results[0].summary

    def test_url_server(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        config = {"url": "http://localhost:8081/mcp", "transport": "sse"}
        results = _validate_mcp_server("test-server", config)
        assert results == []

    def test_url_with_credentials(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        config = {"url": "https://user:password123@example.com/mcp"}
        results = _validate_mcp_server("test-server", config)
        assert len(results) == 1
        assert results[0].id == "MCP_SECRET_001"
        assert results[0].status == CheckStatus.WARNING
        public_fields = " ".join([results[0].summary, results[0].details, results[0].recommendation])
        assert "password123" not in public_fields
        assert "https://[REDACTED]:[REDACTED]@example.com/mcp" in public_fields

    def test_server_with_secret_env(self):
        from agentdoctor.checks.mcp import _validate_mcp_server

        config = {
            "command": "node",
            "args": ["server.js"],
            "env": {"OPENAI_API_KEY": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890", "SAFE_VAR": "${SAFE_VAR}"},
        }
        with patch("agentdoctor.checks.mcp.shutil.which", return_value="/usr/bin/node"):
            results = _validate_mcp_server("test-server", config)
        assert len(results) == 1
        assert results[0].id == "MCP_SECRET_001"
        assert results[0].status == CheckStatus.WARNING
        assert "abcdefghijklmnopqrstuvwxyz1234567890" not in str(results[0])


class TestSecretDetection:
    def test_secret_in_env_detected(self):
        from agentdoctor.checks.secrets import _scan_dict

        data = {
            "env": {
                "OPENAI_API_KEY": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
                "SAFE_VAR": "normal_value",
                "password": "my_secret_pass",
            }
        }
        results = _scan_dict(data)
        assert results
        assert all("abcdefghijklmnopqrstuvwxyz1234567890" not in result.details for result in results)

    def test_no_false_positives(self):
        from agentdoctor.checks.secrets import _scan_dict

        data = {
            "name": "openai",
            "description": "API key for testing",
            "value": "sk-proj-abc",  # Too short to match
        }
        results = _scan_dict(data)
        assert results == []


class TestBinaryFileExclusion:
    def test_vscdb_not_parsed_as_json(self):
        """Ensure *.vscdb (SQLite) files are not analyzed as JSON MCP configs."""
        from agentdoctor.checks.mcp import _is_binary_file, _parse_mcp_config

        vscdb_path = FIXTURES_DIR / "test_state.vscdb"
        assert vscdb_path.exists(), "Fixture must exist"
        assert _is_binary_file(vscdb_path), "vscdb should be detected as binary"
        data, error = _parse_mcp_config(vscdb_path)
        assert data is None
        assert error is not None
        assert "Binary" in error

    def test_sqlite_not_parsed_as_json(self):
        """Ensure *.sqlite files are not analyzed as JSON."""
        from agentdoctor.checks.mcp import _is_binary_file

        assert _is_binary_file(FIXTURES_DIR / "anything.sqlite")
        assert _is_binary_file(FIXTURES_DIR / "anything.sqlite3")
        assert _is_binary_file(FIXTURES_DIR / "anything.db")
