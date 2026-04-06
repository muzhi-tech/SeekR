"""Unit tests for seekr.scripts.llm_dispatcher."""

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

from seekr.scripts.models import LLMResult
from seekr.scripts.llm_dispatcher import (
    _call_claude,
    _call_gemini,
    _call_openai_compatible,
    _parse_simple_yaml,
    LLMDispatcher,
)


# ---------------------------------------------------------------------------
# YAML Parser Tests
# ---------------------------------------------------------------------------

class TestParseSimpleYaml(unittest.TestCase):

    def test_flat_key_value(self):
        yaml = 'timeout: 120\n'
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["timeout"], 120)

    def test_nested_dict(self):
        yaml = "dispatch:\n  timeout: 60\n  provider: gemini\n"
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["dispatch"]["timeout"], 60)
        self.assertEqual(result["dispatch"]["provider"], "gemini")

    def test_quoted_string(self):
        yaml = 'model: "deepseek-chat"\n'
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["model"], "deepseek-chat")

    def test_comment_lines_skipped(self):
        yaml = "# this is a comment\nkey: value\n"
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["key"], "value")

    def test_inline_comment(self):
        yaml = "timeout: 120  # seconds\n"
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["timeout"], 120)

    def test_empty_value_means_nested(self):
        yaml = "providers:\n  gemini:\n    api_key: abc\n"
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["providers"]["gemini"]["api_key"], "abc")

    def test_two_level_nested(self):
        yaml = "providers:\n  gemini:\n    api_key: test123\n    model: gemini-2.0-flash\n"
        result = _parse_simple_yaml(yaml)
        self.assertEqual(result["providers"]["gemini"]["api_key"], "test123")
        self.assertEqual(result["providers"]["gemini"]["model"], "gemini-2.0-flash")

    def test_float_value(self):
        yaml = "temperature: 0.7\n"
        result = _parse_simple_yaml(yaml)
        self.assertAlmostEqual(result["temperature"], 0.7)


# ---------------------------------------------------------------------------
# Config Loading Tests
# ---------------------------------------------------------------------------

class TestConfigLoading(unittest.TestCase):

    def test_loads_defaults_when_no_config_file(self):
        d = LLMDispatcher(config_path="/nonexistent/config.yaml")
        self.assertIn("prompt", d.dispatch_settings)
        self.assertIn("article", d.dispatch_settings)

    def test_defaults_have_correct_providers(self):
        d = LLMDispatcher(config_path="/nonexistent/config.yaml")
        self.assertEqual(d.dispatch_settings["prompt"]["provider"], "gemini")
        self.assertEqual(d.dispatch_settings["article"]["provider"], "claude")


# ---------------------------------------------------------------------------
# Provider Selection Tests
# ---------------------------------------------------------------------------

class TestProviderSelection(unittest.TestCase):

    def setUp(self):
        self.d = LLMDispatcher(config_path="/nonexistent/config.yaml")

    def test_prompt_mode_selects_gemini(self):
        self.assertEqual(
            self.d.dispatch_settings["prompt"]["provider"], "gemini"
        )

    def test_article_mode_selects_claude(self):
        self.assertEqual(
            self.d.dispatch_settings["article"]["provider"], "claude"
        )


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestValidation(unittest.TestCase):

    def setUp(self):
        self.d = LLMDispatcher(config_path="/nonexistent/config.yaml")

    def test_missing_api_key_returns_error(self):
        result = self.d.prompt_generate("hello")
        self.assertIsNotNone(result.error)
        self.assertIn("api_key", result.error.lower() + "API key")

    def test_unknown_mode_returns_error(self):
        result = self.d.dispatch("hello", mode="unknown")
        self.assertIsNotNone(result.error)
        self.assertIn("Unknown mode", result.error)

    def test_unknown_provider_returns_error(self):
        result = self.d.dispatch("hello", mode="prompt", provider="fake_provider")
        self.assertIsNotNone(result.error)
        self.assertIn("Unknown provider", result.error)

    def test_openai_compatible_requires_api_base(self):
        d = LLMDispatcher(config_path="/nonexistent/config.yaml")
        # Override providers with no api_base
        d._config["providers"]["openai_compatible"] = {"api_key": "test-key"}
        result = d.dispatch("hello", mode="prompt", provider="openai_compatible")
        self.assertIsNotNone(result.error)
        self.assertIn("api_base", result.error)


# ---------------------------------------------------------------------------
# Request Format Tests (mock HTTP)
# ---------------------------------------------------------------------------

class TestGeminiRequestFormat(unittest.TestCase):

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_gemini_url_and_body(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}],
            "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2},
        }).encode()
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        cfg = {"api_key": "test-key", "model": "gemini-2.0-flash"}
        dispatch_cfg = {"temperature": 0.5, "max_tokens": 1024}
        result = _call_gemini("Hi", "You are helpful", cfg, dispatch_cfg, 30, "prompt")

        self.assertIsNone(result.error)
        self.assertEqual(result.text, "Hello!")
        self.assertEqual(result.provider, "gemini")
        self.assertEqual(result.input_tokens, 5)

        # Verify URL
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertIn("generativelanguage.googleapis.com", req.full_url)
        self.assertIn("gemini-2.0-flash", req.full_url)
        self.assertIn("key=test-key", req.full_url)


class TestClaudeRequestFormat(unittest.TestCase):

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_claude_headers_and_body(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [{"text": "Bonjour!"}],
            "usage": {"input_tokens": 10, "output_tokens": 3},
        }).encode()
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        cfg = {"api_key": "sk-test", "model": "claude-sonnet-4-20250514"}
        dispatch_cfg = {"temperature": 0.5, "max_tokens": 2048}
        result = _call_claude("Hi", "Be brief", cfg, dispatch_cfg, 30, "article")

        self.assertIsNone(result.error)
        self.assertEqual(result.text, "Bonjour!")
        self.assertEqual(result.provider, "claude")

        # Verify headers (urllib capitalizes first letter)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers["X-api-key"], "sk-test")
        self.assertEqual(req.headers["Anthropic-version"], "2023-06-01")


class TestOpenAIRequestFormat(unittest.TestCase):

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_openai_url_construction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hola!"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4},
        }).encode()
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        cfg = {
            "api_key": "ds-test",
            "model": "deepseek-chat",
            "api_base": "https://api.deepseek.com/v1",
        }
        dispatch_cfg = {"temperature": 0.3, "max_tokens": 512}
        result = _call_openai_compatible("Hi", "", cfg, dispatch_cfg, 30, "prompt")

        self.assertIsNone(result.error)
        self.assertEqual(result.text, "Hola!")

        req = mock_urlopen.call_args[0][0]
        self.assertIn("api.deepseek.com", req.full_url)
        self.assertIn("chat/completions", req.full_url)
        self.assertIn("Bearer ds-test", req.get_header("Authorization"))


# ---------------------------------------------------------------------------
# LLMResult Dataclass Tests
# ---------------------------------------------------------------------------

class TestLLMResult(unittest.TestCase):

    def test_create_success_result(self):
        r = LLMResult(
            provider="gemini", model="gemini-2.0-flash", mode="prompt",
            text="Hello", input_tokens=5, output_tokens=2,
            elapsed_ms=300, error=None,
        )
        self.assertEqual(r.provider, "gemini")
        self.assertIsNone(r.error)

    def test_create_error_result(self):
        r = LLMResult(
            provider="claude", model="", mode="article",
            text="", input_tokens=0, output_tokens=0,
            elapsed_ms=0, error="API key missing",
        )
        self.assertEqual(r.error, "API key missing")

    def test_frozen(self):
        r = LLMResult(
            provider="gemini", model="m", mode="prompt",
            text="", input_tokens=0, output_tokens=0,
            elapsed_ms=0, error=None,
        )
        with self.assertRaises(AttributeError):
            r.text = "modified"


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------

class TestErrorHandling(unittest.TestCase):

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_http_401_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com", code=401, msg="Unauthorized",
            hdrs=None, fp=BytesIO(b"bad key"),
        )
        cfg = {"api_key": "bad", "model": "test"}
        result = _call_gemini("hi", "", cfg, {}, 30, "prompt")
        self.assertIn("Authentication failed", result.error)

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_http_429_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com", code=429, msg="Too Many Requests",
            hdrs=None, fp=BytesIO(b"slow down"),
        )
        cfg = {"api_key": "k", "model": "test"}
        result = _call_claude("hi", "", cfg, {}, 30, "article")
        self.assertIn("Rate limited", result.error)

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_http_500_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com", code=500, msg="Internal Server Error",
            hdrs=None, fp=BytesIO(b"oops"),
        )
        cfg = {"api_key": "k", "model": "test"}
        result = _call_gemini("hi", "", cfg, {}, 30, "prompt")
        self.assertIn("server error", result.error)

    @patch("seekr.scripts.llm_dispatcher.urllib.request.urlopen")
    def test_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = ConnectionError("timeout")
        cfg = {"api_key": "k", "model": "test"}
        result = _call_claude("hi", "", cfg, {}, 30, "article")
        self.assertIn("Network error", result.error)


# ---------------------------------------------------------------------------
# Dispatcher Override Tests
# ---------------------------------------------------------------------------

class TestDispatcherOverride(unittest.TestCase):

    def setUp(self):
        self.d = LLMDispatcher(config_path="/nonexistent/config.yaml")

    def test_override_provider_via_kwarg(self):
        # Even though prompt defaults to gemini, override to openai_compatible
        # Should fail because no api_key configured, but the provider should be used
        d = LLMDispatcher(config_path="/nonexistent/config.yaml")
        d._config["providers"]["openai_compatible"] = {
            "api_key": "test-key",  # has key but no api_base
        }
        result = d.dispatch("hi", mode="prompt", provider="openai_compatible")
        # Should error about api_base, proving provider was overridden
        self.assertIn("api_base", result.error)
        self.assertEqual(result.provider, "openai_compatible")


if __name__ == "__main__":
    unittest.main()
