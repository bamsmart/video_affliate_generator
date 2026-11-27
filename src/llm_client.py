"""OpenRouter multimodal/text client with server-side fallback, retry, and JSON healing."""

from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path
from typing import Any, Type, TypeVar

from openai import OpenAI
from PIL import Image
from pydantic import BaseModel

from src.config import redact_secrets

T = TypeVar("T", bound=BaseModel)


class LLMClientError(RuntimeError):
    """Raised when OpenRouter call or JSON schema parsing fails after retries."""


def image_bytes_to_data_url(img_bytes: bytes, max_dim: int = 1280) -> str:
    """Downscale image bytes safely and return a base64 JPEG data URL."""
    with Image.open(io.BytesIO(img_bytes)) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        if max(w, h) > max_dim:
            scale = max_dim / float(max(w, h))
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            rgb = rgb.resize(new_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=88, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def image_path_to_data_url(path: str | Path, max_dim: int = 1280) -> str:
    """Read an image file and return a base64 JPEG data URL."""
    return image_bytes_to_data_url(Path(path).read_bytes(), max_dim=max_dim)


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract a JSON object from raw LLM text (handles fences and surrounding prose)."""
    if not raw_text or not raw_text.strip():
        raise ValueError("Respons LLM kosong.")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Strip markdown fences like ```json ... ```
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Brace-balanced scan for the first complete JSON object
    start_idx = cleaned.find("{")
    if start_idx == -1:
        raise ValueError("Tidak ditemukan objek JSON ('{...}') di respons model.")

    depth = 0
    in_string = False
    escape = False
    for idx in range(start_idx, len(cleaned)):
        ch = cleaned[idx]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start_idx : idx + 1]
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                    break

    raise ValueError("Gagal mengekstrak JSON valid dari respons model.")


class OpenRouterClient:
    """Resilient OpenRouter wrapper supporting server-side & client-side model fallback."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_sec: float = 90.0,
        max_retries: int = 2,
        client: Any | None = None,
    ) -> None:
        if not api_key and client is None:
            raise LLMClientError("OPENROUTER_API_KEY belum diisi.")
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.client = client or OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_sec,
            default_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Video Affiliate AI Generator",
            },
        )

    def _call_once(
        self,
        messages: list[dict[str, Any]],
        model: str,
        fallback_models: list[str] | None,
        use_json_format: bool,
    ) -> tuple[str, str]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
        }
        if fallback_models:
            kwargs["extra_body"] = {"models": fallback_models}
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        actual_model = getattr(resp, "model", None) or model
        return content, str(actual_model)

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        primary_model: str,
        fallback_models: list[str] | None,
        pydantic_model: Type[T],
    ) -> tuple[T, str]:
        """Execute chat completion and validate JSON against a Pydantic model."""
        candidates = [primary_model] + [m for m in (fallback_models or []) if m != primary_model]
        last_error: Exception | None = None

        for idx, current_model in enumerate(candidates):
            remaining_fallbacks = [m for m in candidates if m != current_model]
            use_json_format = True

            for attempt in range(self.max_retries + 1):
                try:
                    raw_text, actual_model = self._call_once(
                        messages=messages,
                        model=current_model,
                        fallback_models=remaining_fallbacks if idx == 0 else None,
                        use_json_format=use_json_format,
                    )
                    data = extract_json_object(raw_text)
                    validated = pydantic_model.model_validate(data)
                    return validated, actual_model
                except Exception as exc:
                    last_error = exc
                    err_str = str(exc).lower()
                    # Some :free providers reject response_format with HTTP 400
                    if use_json_format and (
                        "response_format" in err_str
                        or "json_object" in err_str
                        or "400" in err_str
                    ):
                        use_json_format = False
                        continue

                    if attempt < self.max_retries:
                        time.sleep(1.5 * (attempt + 1))

        safe_msg = redact_secrets(str(last_error or "Unknown OpenRouter error"), [self.api_key])
        raise LLMClientError(f"Gagal memanggil OpenRouter setelah fallback/retry: {safe_msg}")


class GeminiClient:
    """Google Gemini OpenAI-compatible client with fast quota-exceeded failover."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout_sec: float = 60.0,
        max_retries: int = 1,
        client: Any | None = None,
    ) -> None:
        if not api_key and client is None:
            raise LLMClientError("GEMINI_API_KEY belum diisi.")
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.client = client or OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_sec,
        )

    def _call_once(
        self,
        messages: list[dict[str, Any]],
        model: str,
        use_json_format: bool,
    ) -> tuple[str, str]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
        }
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        actual_model = getattr(resp, "model", None) or model
        return content, str(actual_model)

    @staticmethod
    def _is_quota_error(err_str: str) -> bool:
        lower = err_str.lower()
        return any(
            kw in lower
            for kw in ("429", "quota", "resource_exhausted", "exceeded", "rate limit")
        )

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        primary_model: str,
        fallback_models: list[str] | None,
        pydantic_model: Type[T],
    ) -> tuple[T, str]:
        """Call Gemini models and fail fast on quota exhaustion so router can fall back."""
        candidates = [primary_model] + [m for m in (fallback_models or []) if m != primary_model]
        last_error: Exception | None = None
        quota_error: Exception | None = None

        for current_model in candidates:
            use_json_format = True
            for attempt in range(self.max_retries + 1):
                try:
                    raw_text, actual_model = self._call_once(
                        messages=messages,
                        model=current_model,
                        use_json_format=use_json_format,
                    )
                    data = extract_json_object(raw_text)
                    validated = pydantic_model.model_validate(data)
                    return validated, actual_model
                except Exception as exc:
                    last_error = exc
                    err_str = str(exc)
                    if use_json_format and (
                        "response_format" in err_str.lower()
                        or "json_object" in err_str.lower()
                        or "400" in err_str
                    ):
                        use_json_format = False
                        continue
                    if self._is_quota_error(err_str):
                        quota_error = quota_error or exc
                        # Fail fast to next Gemini model or OpenRouter without long sleep
                        break
                    if "404" in err_str or "not found" in err_str.lower():
                        break
                    if attempt < self.max_retries:
                        time.sleep(1.0)

        chosen_err = quota_error or last_error
        safe_msg = redact_secrets(str(chosen_err or "Unknown Gemini error"), [self.api_key])
        raise LLMClientError(f"Gemini gagal / limit tercapai: {safe_msg}")


class HybridLLMRouter:
    """Routes requests to Gemini first, with automatic fallback to OpenRouter."""

    def __init__(
        self,
        gemini_client: GeminiClient | None = None,
        openrouter_client: OpenRouterClient | None = None,
    ) -> None:
        if gemini_client is None and openrouter_client is None:
            raise LLMClientError("Minimal salah satu GEMINI_API_KEY atau OPENROUTER_API_KEY harus diisi.")
        self.gemini_client = gemini_client
        self.openrouter_client = openrouter_client
        self.last_fallback_reason: str = ""

    @staticmethod
    def _summarize_gemini_error(err_msg: str) -> str:
        low = err_msg.lower()
        if any(k in low for k in ("429", "quota", "resource_exhausted", "rate limit")):
            return "Kuota/RPM Gemini sedang penuh (429)"
        if "404" in low or "not found" in low:
            return "Nama model Gemini tidak ditemukan (404)"
        if "401" in low or "403" in low or "api_key_invalid" in low or "invalid api key" in low:
            return "GEMINI_API_KEY tidak valid atau ditolak (401/403)"
        return err_msg[:140]

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        pydantic_model: Type[T],
        gemini_primary: str = "gemini-2.5-flash",
        gemini_fallbacks: list[str] | None = None,
        openrouter_primary: str = "google/gemma-3-27b-it:free",
        openrouter_fallbacks: list[str] | None = None,
    ) -> tuple[T, str]:
        """Try Gemini first; on any failure/quota limit, seamlessly fall back to OpenRouter."""
        self.last_fallback_reason = ""
        gemini_err: str | None = None

        if self.gemini_client is not None:
            try:
                res, used_model = self.gemini_client.chat_json(
                    messages=messages,
                    primary_model=gemini_primary,
                    fallback_models=gemini_fallbacks,
                    pydantic_model=pydantic_model,
                )
                return res, f"gemini:{used_model}"
            except Exception as exc:
                gemini_err = redact_secrets(str(exc), [self.gemini_client.api_key])
                self.last_fallback_reason = self._summarize_gemini_error(gemini_err)

        if self.openrouter_client is not None:
            try:
                res, used_model = self.openrouter_client.chat_json(
                    messages=messages,
                    primary_model=openrouter_primary,
                    fallback_models=openrouter_fallbacks,
                    pydantic_model=pydantic_model,
                )
                if gemini_err:
                    return res, f"openrouter:{used_model} (fallback dari Gemini)"
                return res, f"openrouter:{used_model}"
            except Exception as exc:
                or_err = redact_secrets(str(exc), [self.openrouter_client.api_key])
                if gemini_err:
                    raise LLMClientError(
                        f"Gemini gagal ({gemini_err}) dan OpenRouter fallback juga gagal ({or_err})."
                    ) from exc
                raise LLMClientError(or_err) from exc

        raise LLMClientError(gemini_err or "Tidak ada provider LLM yang aktif.")
