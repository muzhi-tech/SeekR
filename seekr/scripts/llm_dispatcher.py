"""SeekR LLM Dispatcher — routes calls to Gemini / Claude / OpenAI-compatible APIs.

Reads config.yaml for provider keys and dispatch settings.
Falls back to references/llm_defaults.json when config.yaml is absent.
All HTTP calls use stdlib urllib.request — zero external dependencies.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"
_DEFAULTS_PATH = _PROJECT_ROOT / "seekr" / "references" / "llm_defaults.json"

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_CLAUDE_BASE = "https://api.anthropic.com"
_OPENAI_BASE = "https://api.openai.com/v1"

_VALID_PROVIDERS = {"gemini", "claude", "openai_compatible"}
_VALID_MODES = {"prompt", "article"}


# ---------------------------------------------------------------------------
# Minimal YAML parser (handles 2-level nested dicts, string/int/float only)
# ---------------------------------------------------------------------------

def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a simple YAML file into a nested dict.

    Supports:
    - top-level keys
    - up to 3 levels of nested dicts (indented with spaces)
    - string, int, float, and quoted string values
    - comments (lines starting with #) and blank lines
    """
    result: Dict[str, Any] = {}
    # Stack tracks current nested path: [("providers",), ("providers", "gemini")]
    path: list = []

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blanks and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Determine nesting depth by leading spaces
        depth = 0
        for ch in line:
            if ch == " ":
                depth += 1
            else:
                break
        indent = depth // 2  # number of 2-space indent levels

        # Parse the key-value pair
        key, value = _parse_kv(stripped)
        if key is None:
            continue

        # Adjust path to current depth
        path = path[:indent]

        # Navigate to parent dict
        parent = result
        for pkey in path:
            if pkey not in parent or not isinstance(parent[pkey], dict):
                parent[pkey] = {}
            parent = parent[pkey]

        if value is None:
            # New nesting level
            parent.setdefault(key, {})
            path.append(key)
        else:
            parent[key] = value

    return result


def _parse_kv(pair: str) -> tuple:
    """Parse 'key: value' into (key, parsed_value)."""
    colon = pair.find(":")
    if colon == -1:
        return None, None
    key = pair[:colon].strip()
    raw = pair[colon + 1:].strip()

    if not raw:
        return key, None

    # Strip inline comments
    if raw.startswith('"'):
        end = raw.find('"', 1)
        if end != -1:
            raw = raw[1:end]
        return key, raw

    # Strip trailing comment
    if "#" in raw:
        raw = raw[:raw.index("#")].strip()

    if not raw:
        return key, None

    # Try numeric
    try:
        return key, int(raw)
    except ValueError:
        pass
    try:
        return key, float(raw)
    except ValueError:
        pass

    return key, raw


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_defaults() -> Dict[str, Any]:
    """Load default dispatch config from references/llm_defaults.json."""
    with open(_DEFAULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load merged config: defaults <- config.yaml overrides.

    Returns the defaults if config.yaml is missing.
    """
    defaults = _load_defaults()

    path = Path(config_path) if config_path else _CONFIG_PATH
    if not path.exists():
        return {
            "providers": {},
            "dispatch": defaults["dispatch_modes"],
            "timeout": defaults.get("timeout", 120),
        }

    with open(path, "r", encoding="utf-8") as f:
        user_config = _parse_simple_yaml(f.read())

    # Merge dispatch settings: user config overrides defaults
    dispatch = dict(defaults["dispatch_modes"])
    if "dispatch" in user_config:
        user_dispatch = user_config["dispatch"]
        # Top-level timeout
        if "timeout" in user_dispatch:
            dispatch["timeout"] = user_dispatch.pop("timeout")
        # Mode overrides
        for mode_key in ("prompt", "article"):
            if mode_key in user_dispatch:
                if isinstance(user_dispatch[mode_key], dict):
                    dispatch.setdefault(mode_key, {}).update(user_dispatch[mode_key])

    return {
        "providers": user_config.get("providers", {}),
        "dispatch": dispatch,
        "timeout": dispatch.pop("timeout", defaults.get("timeout", 120)),
    }


# ---------------------------------------------------------------------------
# Provider call functions
# ---------------------------------------------------------------------------

def _make_error_result(provider: str, model: str, mode: str,
                       elapsed_ms: int, message: str):
    """Build an LLMResult for error cases."""
    from seekr.scripts.models import LLMResult
    return LLMResult(
        provider=provider,
        model=model,
        mode=mode,
        text="",
        input_tokens=0,
        output_tokens=0,
        elapsed_ms=elapsed_ms,
        error=message,
    )


def _call_gemini(prompt: str, system: str, provider_cfg: Dict[str, Any],
                 dispatch_cfg: Dict[str, Any], timeout: int,
                 mode: str) -> "LLMResult":
    """Call Google Gemini REST API."""
    from seekr.scripts.models import LLMResult

    api_key = provider_cfg.get("api_key", "")
    model = provider_cfg.get("model", "gemini-2.0-flash")
    api_base = provider_cfg.get("api_base", "") or _GEMINI_BASE

    if not api_key:
        return _make_error_result(
            "gemini", model, mode, 0,
            f"API key for 'gemini' is empty. Set providers.gemini.api_key in config.yaml.",
        )

    url = f"{api_base.rstrip('/')}/models/{model}:generateContent?key={api_key}"

    body: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": dispatch_cfg.get("temperature", 0.7),
            "maxOutputTokens": dispatch_cfg.get("max_tokens", 4096),
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    req_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_data, method="POST",
        headers={"Content-Type": "application/json"},
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        elapsed = int((time.monotonic() - start) * 1000)

        text = resp_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = resp_data.get("usageMetadata", {})
        return LLMResult(
            provider="gemini", model=model, mode=mode, text=text,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            elapsed_ms=elapsed, error=None,
        )
    except urllib.error.HTTPError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        msg = _http_error_message("gemini", e)
        return _make_error_result("gemini", model, mode, elapsed, msg)
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return _make_error_result("gemini", model, mode, elapsed, f"Network error calling gemini: {e}")


def _call_claude(prompt: str, system: str, provider_cfg: Dict[str, Any],
                 dispatch_cfg: Dict[str, Any], timeout: int,
                 mode: str) -> "LLMResult":
    """Call Anthropic Claude REST API."""
    from seekr.scripts.models import LLMResult

    api_key = provider_cfg.get("api_key", "")
    model = provider_cfg.get("model", "claude-sonnet-4-20250514")
    api_base = provider_cfg.get("api_base", "") or _CLAUDE_BASE

    if not api_key:
        return _make_error_result(
            "claude", model, mode, 0,
            f"API key for 'claude' is empty. Set providers.claude.api_key in config.yaml.",
        )

    url = f"{api_base.rstrip('/')}/v1/messages"

    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": dispatch_cfg.get("max_tokens", 8192),
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    temperature = dispatch_cfg.get("temperature")
    if temperature is not None:
        body["temperature"] = temperature

    req_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_data, method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        elapsed = int((time.monotonic() - start) * 1000)

        text = resp_data.get("content", [{}])[0].get("text", "")
        usage = resp_data.get("usage", {})
        return LLMResult(
            provider="claude", model=model, mode=mode, text=text,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            elapsed_ms=elapsed, error=None,
        )
    except urllib.error.HTTPError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        msg = _http_error_message("claude", e)
        return _make_error_result("claude", model, mode, elapsed, msg)
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return _make_error_result("claude", model, mode, elapsed, f"Network error calling claude: {e}")


def _call_openai_compatible(prompt: str, system: str, provider_cfg: Dict[str, Any],
                            dispatch_cfg: Dict[str, Any], timeout: int,
                            mode: str) -> "LLMResult":
    """Call OpenAI-compatible API (DeepSeek, Ollama, etc.)."""
    from seekr.scripts.models import LLMResult

    api_key = provider_cfg.get("api_key", "")
    model = provider_cfg.get("model", "deepseek-chat")
    api_base = provider_cfg.get("api_base", "")

    if not api_key:
        return _make_error_result(
            "openai_compatible", model, mode, 0,
            f"API key for 'openai_compatible' is empty. Set providers.openai_compatible.api_key in config.yaml.",
        )
    if not api_base:
        return _make_error_result(
            "openai_compatible", model, mode, 0,
            "Provider 'openai_compatible' requires 'api_base' in config.yaml.",
        )

    url = f"{api_base.rstrip('/')}/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": dispatch_cfg.get("max_tokens", 4096),
    }
    temperature = dispatch_cfg.get("temperature")
    if temperature is not None:
        body["temperature"] = temperature

    req_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_data, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        elapsed = int((time.monotonic() - start) * 1000)

        text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = resp_data.get("usage", {})
        return LLMResult(
            provider="openai_compatible", model=model, mode=mode, text=text,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            elapsed_ms=elapsed, error=None,
        )
    except urllib.error.HTTPError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        msg = _http_error_message("openai_compatible", e)
        return _make_error_result("openai_compatible", model, mode, elapsed, msg)
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return _make_error_result("openai_compatible", model, mode, elapsed, f"Network error calling openai_compatible: {e}")


def _http_error_message(provider: str, err: urllib.error.HTTPError) -> str:
    """Map HTTP error codes to user-friendly messages."""
    status = err.code
    if status in (401, 403):
        return f"Authentication failed for {provider}. Check your API key."
    if status == 429:
        return f"Rate limited by {provider}. Retry after a moment."
    if status >= 500:
        return f"Provider {provider} returned server error {status}. Retry later."
    try:
        body = err.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return f"Provider {provider} returned HTTP {status}: {body[:200]}"


# ---------------------------------------------------------------------------
# Dispatcher class
# ---------------------------------------------------------------------------

_PROVIDER_FN = {
    "gemini": _call_gemini,
    "claude": _call_claude,
    "openai_compatible": _call_openai_compatible,
}


class LLMDispatcher:
    """Route LLM calls to the correct provider based on dispatch mode."""

    def __init__(self, config_path: Optional[str] = None):
        self._config = _load_config(config_path)

    @property
    def providers(self) -> Dict[str, Any]:
        return self._config.get("providers", {})

    @property
    def dispatch_settings(self) -> Dict[str, Any]:
        return self._config.get("dispatch", {})

    @property
    def timeout(self) -> int:
        return self._config.get("timeout", 120)

    def dispatch(self, prompt: str, mode: str = "prompt",
                 system: str = "", **overrides) -> "LLMResult":
        """Main entry point. Selects provider by mode and calls it.

        Args:
            prompt: User message / task prompt.
            mode: "prompt" for brief generation, "article" for full article.
            system: System prompt (optional).
            **overrides: Override provider, model, temperature, max_tokens.

        Returns:
            LLMResult with generated text or error.
        """
        if mode not in _VALID_MODES:
            from seekr.scripts.models import LLMResult
            return LLMResult(
                provider="", model="", mode=mode, text="",
                input_tokens=0, output_tokens=0, elapsed_ms=0,
                error=f"Unknown mode '{mode}'. Must be one of: {', '.join(_VALID_MODES)}.",
            )

        # Resolve dispatch config for this mode
        mode_cfg = dict(self.dispatch_settings.get(mode, {}))
        mode_cfg.update(overrides)

        provider_name = mode_cfg.get("provider", "gemini")
        if provider_name not in _VALID_PROVIDERS:
            from seekr.scripts.models import LLMResult
            return LLMResult(
                provider=provider_name, model="", mode=mode, text="",
                input_tokens=0, output_tokens=0, elapsed_ms=0,
                error=f"Unknown provider '{provider_name}'. Must be one of: {', '.join(_VALID_PROVIDERS)}.",
            )

        # Allow model override via config or kwarg
        provider_cfg = dict(self.providers.get(provider_name, {}))
        if "model" in mode_cfg:
            provider_cfg["model"] = mode_cfg.pop("model")

        call_fn = _PROVIDER_FN[provider_name]
        return call_fn(prompt, system, provider_cfg, mode_cfg, self.timeout, mode)

    def prompt_generate(self, prompt: str, system: str = "", **kw) -> "LLMResult":
        """Generate a prompt / brief / outline (default: Gemini)."""
        return self.dispatch(prompt, mode="prompt", system=system, **kw)

    def article_generate(self, prompt: str, system: str = "", **kw) -> "LLMResult":
        """Generate a full GEO article (default: Claude)."""
        return self.dispatch(prompt, mode="article", system=system, **kw)


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(_PROJECT_ROOT))

    d = LLMDispatcher()
    print("Loaded config:")
    print(f"  Providers configured: {list(d.providers.keys())}")
    print(f"  Dispatch prompt  -> {d.dispatch_settings.get('prompt', {})}")
    print(f"  Dispatch article -> {d.dispatch_settings.get('article', {})}")
    print(f"  Timeout: {d.timeout}s")
    print()

    # Quick smoke test (will return error if no keys configured)
    print("--- Prompt mode (Gemini default) ---")
    r = d.prompt_generate("Say hello in one sentence.")
    print(f"  provider={r.provider}  model={r.model}  error={r.error}")
    if r.text:
        print(f"  text={r.text[:200]}")

    print()
    print("--- Article mode (Claude default) ---")
    r = d.article_generate("Write one sentence about SEO.")
    print(f"  provider={r.provider}  model={r.model}  error={r.error}")
    if r.text:
        print(f"  text={r.text[:200]}")
