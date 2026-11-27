"""Configuration loader supporting both local .env and Streamlit Cloud st.secrets."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


def resolve_binary(name: str) -> str:
    """Resolve an executable binary from .venv/bin, current Python bin, or system PATH."""
    venv_candidate = REPO_ROOT / ".venv" / "bin" / name
    if venv_candidate.is_file() and os.access(venv_candidate, os.X_OK):
        return str(venv_candidate)

    exe_candidate = Path(sys.executable).parent / name
    if exe_candidate.is_file() and os.access(exe_candidate, os.X_OK):
        return str(exe_candidate)

    which_path = shutil.which(name)
    if which_path:
        return which_path

    return name


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and environment variables from .env."""
    load_dotenv(override=False)
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with cfg_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def get_secret_or_env(key: str, default: str = "") -> str:
    """Read a setting from environment/.env first, falling back safely to st.secrets on Cloud."""
    load_dotenv(override=False)
    env_val = os.getenv(key, "").strip()
    if env_val:
        return env_val

    try:
        import streamlit as st

        val = st.secrets.get(key, "")
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        pass

    return default


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
