"""Configuration loader supporting both local .env and Streamlit Cloud st.secrets."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and environment variables from .env."""
    load_dotenv(override=False)
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with cfg_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def _clean_secret_value(raw: Any) -> str:
    """Normalize secret strings and strip accidental extra wrapping quotes."""
    if raw is None:
        return ""
    text = str(raw).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    return text


def get_secret_or_env(key: str, default: str = "") -> str:
    """Read a setting from environment/.env first, falling back safely to st.secrets on Cloud."""
    load_dotenv(override=False)
    env_val = _clean_secret_value(os.getenv(key, ""))
    if env_val:
        return env_val

    # Case-insensitive env check
    target_lower = key.lower()
    for env_k, env_v in os.environ.items():
        if env_k.lower() == target_lower:
            cleaned = _clean_secret_value(env_v)
            if cleaned:
                return cleaned

    try:
        import streamlit as st

        secrets_dict = st.secrets.to_dict() if hasattr(st.secrets, "to_dict") else dict(st.secrets)
        # 1. Exact top-level lookup
        if key in secrets_dict:
            cleaned = _clean_secret_value(secrets_dict[key])
            if cleaned:
                return cleaned
        # 2. Case-insensitive top-level or nested TOML section lookup ([secrets], [default], etc.)
        for k, v in secrets_dict.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if str(sub_k).lower() == target_lower:
                        cleaned = _clean_secret_value(sub_v)
                        if cleaned:
                            return cleaned
            elif str(k).lower() == target_lower:
                cleaned = _clean_secret_value(v)
                if cleaned:
                    return cleaned
    except Exception:
        pass

    return default


def format_env_as_streamlit_toml(values: dict[str, str]) -> str:
    """Format key-value pairs into valid Streamlit Cloud Secrets TOML."""
    ordered_keys = ["GEMINI_API_KEY", "GEMINI_MODEL", "OPENROUTER_API_KEY", "APP_PIN"]
    lines = ["# Tempelkan (Paste) seluruh isi ini ke Streamlit Cloud -> Settings -> Secrets"]
    for k in ordered_keys:
        val = _clean_secret_value(values.get(k, ""))
        if k == "GEMINI_MODEL" and not val:
            val = "gemini-2.5-flash"
        if val:
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{k} = "{escaped}"')
    return "\n".join(lines) + "\n"


def get_gemini_api_key(override_key: str | None = None) -> str:
    """Return the Gemini API key from override, .env, or Streamlit Cloud secrets."""
    if override_key and override_key.strip():
        return override_key.strip()
    return get_secret_or_env("GEMINI_API_KEY")


def get_gemini_model_override() -> str:
    """Return optional GEMINI_MODEL override from .env or Streamlit Cloud secrets."""
    return get_secret_or_env("GEMINI_MODEL")


def get_openrouter_api_key(override_key: str | None = None) -> str:
    """Return the OpenRouter API key from override, .env, or Streamlit Cloud secrets."""
    if override_key and override_key.strip():
        return override_key.strip()
    return get_secret_or_env("OPENROUTER_API_KEY")


def get_app_pin() -> str:
    """Return optional APP_PIN passcode configured in .env or Streamlit Cloud secrets."""
    return get_secret_or_env("APP_PIN")


def redact_secrets(text: str, extra_secrets: list[str] | None = None) -> str:
    """Mask API keys, PINs, and bearer tokens from text before logging or displaying."""
    if not text:
        return text

    redacted = text
    candidates: list[str] = []
    for key_name in ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "APP_PIN"):
        val = get_secret_or_env(key_name)
        if val:
            candidates.append(val)
    if extra_secrets:
        candidates.extend([s.strip() for s in extra_secrets if s and s.strip()])

    for secret in candidates:
        if len(secret) >= 6:
            redacted = redacted.replace(secret, "[REDACTED]")

    redacted = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", redacted)
    redacted = re.sub(r"sk-or-v1-[A-Za-z0-9_-]{8,}", "[REDACTED]", redacted)
    redacted = re.sub(r"(Bearer\s+)[A-Za-z0-9._-]{8,}", r"\1[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted
