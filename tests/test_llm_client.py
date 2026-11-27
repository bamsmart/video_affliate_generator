"""Unit tests for Gemini primary + OpenRouter fallback client, diagnostics, JSON extraction, and redaction."""

from types import SimpleNamespace

from src.config import format_env_as_streamlit_toml, get_secret_or_env, redact_secrets
from src.llm_client import GeminiClient, HybridLLMRouter, OpenRouterClient, extract_json_object
from src.prompts import build_offline_demo_blueprint
from src.schemas import BlueprintResponse, TalentSavedProfile


def test_format_env_as_streamlit_toml_and_nested_secrets(monkeypatch):
    toml_str = format_env_as_streamlit_toml(
        {
            "GEMINI_API_KEY": "AIzaSyTest123",
            "OPENROUTER_API_KEY": '"sk-or-v1-abc"',
            "APP_PIN": "9988",
        }
    )
    assert 'GEMINI_API_KEY = "AIzaSyTest123"' in toml_str
    assert 'OPENROUTER_API_KEY = "sk-or-v1-abc"' in toml_str
    assert 'GEMINI_MODEL = "gemini-2.5-flash"' in toml_str
    assert 'APP_PIN = "9988"' in toml_str

    import streamlit as st

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("src.config.load_dotenv", lambda override=False: False)
    monkeypatch.setattr(
        st,
        "secrets",
        SimpleNamespace(to_dict=lambda: {"secrets": {"gemini_api_key": '"AIzaNestedKey999"'}}),
    )
    assert get_secret_or_env("GEMINI_API_KEY") == "AIzaNestedKey999"


def test_extract_json_handles_fences_and_prose():
    raw = 'Berikut hasilnya:\n```json\n{"a": 1, "b": {"c": "ok"}}\n```\nSemoga membantu.'
    parsed = extract_json_object(raw)
    assert parsed == {"a": 1, "b": {"c": "ok"}}


def test_redact_secrets_masks_openrouter_and_gemini_keys():
    msg = (
        "Error with AIzaSyDummyTestKey1234567890abcdefg and "
        "sk-or-v1-secret12345678 and Bearer mytoken99999"
    )
    cleaned = redact_secrets(msg, ["sk-or-v1-secret12345678"])
    assert "AIzaSyDummy" not in cleaned
    assert "secret12345678" not in cleaned
    assert "mytoken99999" not in cleaned
    assert "[REDACTED]" in cleaned


def test_openrouter_fallback_downgrades_response_format_on_400():
    demo_json = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3).model_dump_json()
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if "response_format" in kwargs:
                raise RuntimeError("Error code: 400 - response_format is not supported by provider")
            return SimpleNamespace(
                model="google/gemma-3-27b-it:free",
                choices=[SimpleNamespace(message=SimpleNamespace(content=demo_json))],
            )

    fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    client = OpenRouterClient(api_key="sk-or-v1-dummy1234", max_retries=1, client=fake_openai)
    res, used_model = client.chat_json(
        messages=[{"role": "user", "content": "hi"}],
        primary_model="google/gemma-3-27b-it:free",
        fallback_models=["qwen/qwen2.5-vl-72b-instruct:free", "openrouter/free"],
        pydantic_model=BlueprintResponse,
    )
    assert isinstance(res, BlueprintResponse)
    assert used_model == "google/gemma-3-27b-instruct:free" or "gemma-3-27b-it:free" in used_model
    assert calls[0]["extra_body"] == {
        "models": ["qwen/qwen2.5-vl-72b-instruct:free", "openrouter/free"]
    }
    assert "response_format" not in calls[1]


def test_hybrid_router_uses_gemini_first_without_calling_openrouter():
    demo_json = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3).model_dump_json()
    or_called = False

    class FakeGemCompletions:
        def create(self, **kwargs):
            assert "extra_body" not in kwargs
            return SimpleNamespace(
                model="gemini-2.5-flash",
                choices=[SimpleNamespace(message=SimpleNamespace(content=demo_json))],
            )

    class FakeOrCompletions:
        def create(self, **kwargs):
            nonlocal or_called
            or_called = True
            raise AssertionError("OpenRouter should not be called when Gemini succeeds")

    gem = GeminiClient(
        api_key="AIzaSyDummyTestKey1234567890abcdefg",
        max_retries=0,
        client=SimpleNamespace(chat=SimpleNamespace(completions=FakeGemCompletions())),
    )
    orr = OpenRouterClient(
        api_key="sk-or-v1-dummy1234",
        max_retries=0,
        client=SimpleNamespace(chat=SimpleNamespace(completions=FakeOrCompletions())),
    )
    router = HybridLLMRouter(gemini_client=gem, openrouter_client=orr)
    res, used_model = router.chat_json(
        messages=[{"role": "user", "content": "hi"}],
        pydantic_model=BlueprintResponse,
    )
    assert isinstance(res, BlueprintResponse)
    assert or_called is False
    assert used_model == "gemini:gemini-2.5-flash"
    assert router.last_fallback_reason == ""


def test_hybrid_router_falls_back_to_openrouter_on_gemini_429_and_records_reason():
    demo_json = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3).model_dump_json()

    class FailingGemCompletions:
        def create(self, **kwargs):
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

    class WorkingOrCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                model="google/gemma-3-27b-it:free",
                choices=[SimpleNamespace(message=SimpleNamespace(content=demo_json))],
            )

    gem = GeminiClient(
        api_key="AIzaSyDummyTestKey1234567890abcdefg",
        max_retries=0,
        client=SimpleNamespace(chat=SimpleNamespace(completions=FailingGemCompletions())),
    )
    orr = OpenRouterClient(
        api_key="sk-or-v1-dummy1234",
        max_retries=0,
        client=SimpleNamespace(chat=SimpleNamespace(completions=WorkingOrCompletions())),
    )
    router = HybridLLMRouter(gemini_client=gem, openrouter_client=orr)
    res, used_model = router.chat_json(
        messages=[{"role": "user", "content": "hi"}],
        pydantic_model=BlueprintResponse,
        gemini_fallbacks=["gemini-2.5-flash-lite"],
        openrouter_fallbacks=["qwen/qwen2.5-vl-72b-instruct:free"],
    )
    assert isinstance(res, BlueprintResponse)
    assert "openrouter:" in used_model
    assert "fallback" in used_model
    assert "429" in router.last_fallback_reason
