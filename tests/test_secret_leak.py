"""Tests for secret leak prevention."""

from agentdoctor.core.redaction import redact_secret


class TestSecretLeakPrevention:
    """Critical security tests: ensure secrets NEVER leak to output."""

    def test_no_leak_in_env_var(self):
        """Secret in environment variable should be redacted."""
        text = "OPENAI_API_KEY = sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in result

    def test_no_leak_in_error_message(self):
        """Secret in error message should be redacted."""
        text = "Error: invalid key sk-ant-abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "sk-ant-abcdefghijklmnopqrstuvwxyz" not in result

    def test_no_leak_in_subprocess_stdout(self):
        """Secret in subprocess output should be redacted."""
        text = "Output: token=ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "ghp_abcdefghijklmnopqrstuvwxyz" not in result

    def test_no_leak_in_url(self):
        """Credentials in URL should be redacted."""
        text = "https://user:password123@example.com/api"
        result = redact_secret(text)
        assert "password123" not in result

    def test_no_leak_in_json_config(self):
        """Secret in JSON should be redacted."""
        text = '{"api_key": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"}'
        result = redact_secret(text)
        assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in result

    def test_no_leak_in_bearer_token(self):
        """Bearer token should be redacted."""
        text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "abcdefghijklmnopqrstuvwxyz" not in result

    def test_no_leak_in_aws_key(self):
        """AWS access key should be redacted."""
        text = "AWS_ACCESS_KEY_ID = AKIAIOSFODNN7EXAMPLE"
        result = redact_secret(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_no_leak_in_password_field(self):
        """Password should be redacted."""
        text = 'password = "my_super_secret_password_123"'
        result = redact_secret(text)
        assert "my_super_secret_password" not in result

    def test_no_leak_in_github_pat(self):
        """GitHub PAT should be redacted."""
        text = "GITHUB_TOKEN = github_pat_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "github_pat_abcdefghijklmnopqrstuvwxyz" not in result

    def test_normal_text_unchanged(self):
        """Normal text should not be modified."""
        text = "Python 3.12.0 is installed"
        result = redact_secret(text)
        assert result == text

    def test_short_tokens_not_flagged(self):
        """Short tokens should not be flagged as secrets."""
        text = "key = abc"
        result = redact_secret(text)
        assert result == text
