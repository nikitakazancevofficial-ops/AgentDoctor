"""Tests for redaction module."""

from agentdoctor.core.redaction import mask_token, redact_dict, redact_secret, redact_url


class TestRedactSecret:
    def test_empty_string(self):
        assert redact_secret("") == ""

    def test_none_input(self):
        assert redact_secret(None) == ""

    def test_no_secrets(self):
        text = "This is a normal text with no secrets"
        assert redact_secret(text) == text

    def test_redact_sk_pro_prefix(self):
        text = "key=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCDEF"
        result = redact_secret(text)
        assert "abcdefghijklmnopqrstuvwxyz" not in result
        assert "sk-proj-[REDACTED]" in result

    def test_redact_sk_ant_prefix(self):
        text = "key=sk-ant-abcdefghijklmnopqrstuvwxyz1234567890ABCDEF"
        result = redact_secret(text)
        assert "sk-ant-[REDACTED]" in result

    def test_redact_sk_prefix(self):
        text = "key=sk-abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "sk-[REDACTED]" in result

    def test_redact_ghp_token(self):
        text = "token=ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "ghp_[REDACTED]" in result

    def test_redact_ghs_token(self):
        text = "token=ghs_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "ghs_[REDACTED]" in result

    def test_redact_github_pat(self):
        text = "token=github_pat_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "github_pat_[REDACTED]" in result

    def test_redact_aws_key(self):
        text = "key=AKIAIOSFODNN7EXAMPLE"
        result = redact_secret(text)
        assert "AKIA-[REDACTED]" in result

    def test_redact_bearer_token(self):
        text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secret(text)
        assert "abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED]" in result

    def test_redact_password_field(self):
        text = 'password = "super_secret_password_123"'
        result = redact_secret(text)
        assert "super_secret_password" not in result
        assert "[REDACTED]" in result

    def test_redact_secret_field(self):
        text = 'secret = "my_secret_value"'
        result = redact_secret(text)
        assert "my_secret_value" not in result

    def test_redact_api_key_field(self):
        text = 'api_key = "my_api_key_value_12345"'
        result = redact_secret(text)
        assert "my_api_key_value" not in result

    def test_redact_url_credentials(self):
        text = "https://user:password123@example.com/path"
        result = redact_secret(text)
        assert "password123" not in result
        assert "[REDACTED]:[REDACTED]@" in result

    def test_redact_private_key_header(self):
        text = "-----BEGIN RSA PRIVATE KEY-----"
        result = redact_secret(text)
        assert result == text  # A header alone is not a private-key block.

    def test_redact_entire_private_key_block(self):
        body = "A" * 64
        text = f"-----BEGIN PRIVATE KEY-----\n{body}\n-----END PRIVATE KEY-----"
        result = redact_secret(text)
        assert body not in result
        assert result == "[REDACTED PRIVATE KEY]"


class TestRedactDict:
    def test_simple_dict(self):
        d = {"key": "value", "secret": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"}
        result = redact_dict(d)
        assert result["key"] == "value"
        assert "abcdefghijklmnopqrstuvwxyz" not in result["secret"]

    def test_nested_dict(self):
        d = {"level1": {"level2": {"api_key": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"}}}
        result = redact_dict(d)
        assert "abcdefghijklmnopqrstuvwxyz" not in result["level1"]["level2"]["api_key"]

    def test_list_values(self):
        d = {"keys": ["sk-proj-abcdefghijklmnopqrstuvwxyz1234567890", "sk-ant-abcdefghijklmnopqrstuvwxyz1234567890"]}
        result = redact_dict(d)
        for item in result["keys"]:
            assert "abcdefghijklmnopqrstuvwxyz" not in item

    def test_nested_collections_and_sensitive_key(self):
        result = redact_dict({"servers": [{"token": "unpatterned-secret"}], "pair": ({"password": "value"},)})
        assert result["servers"][0]["token"] == "[REDACTED]"
        assert result["pair"][0]["password"] == "[REDACTED]"


class TestRedactURL:
    def test_redact_url_credentials(self):
        url = "https://user:password@example.com/path"
        result = redact_url(url)
        assert "password" not in result
        assert "[REDACTED]:[REDACTED]@" in result

    def test_url_no_credentials(self):
        url = "https://example.com/path"
        assert redact_url(url) == url


class TestMaskToken:
    def test_mask_token_visible(self):
        result = mask_token("sk-proj-abcdefghijklmnopqrstuvwxyz", 4)
        assert result.startswith("sk-p")
        assert "..." in result

    def test_mask_token_short(self):
        result = mask_token("abc", 4)
        assert result == "[REDACTED]"

    def test_mask_token_none(self):
        assert mask_token(None) == "NOT SET"

    def test_mask_token_empty(self):
        assert mask_token("") == "NOT SET"
