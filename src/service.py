"""High-level orchestration service with Deep Product Knowledge (Website URL, Store Specs, & Web Search)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.blueprint_engine import apply_regenerated_hook, enforce_commercial_mechanisms
from src.compliance import ComplianceReport, audit_blueprint
from src.config import get_gemini_model_override
from src.exporter import save_blueprint_artifacts
from src.history_store import append_product_hook, load_product_hooks
from src.image_prep import save_clean_ingredient_image
from src.knowledge_enricher import KnowledgeContext, gather_product_knowledge_context
from src.llm_client import (
    GeminiClient,
    HybridLLMRouter,
    OpenRouterClient,
    image_bytes_to_data_url,
)
from src.prompts import (
    build_blueprint_messages,
    build_offline_demo_blueprint,
    build_offline_demo_regenerated_hook,
    build_regenerate_hook_messages,
)
from src.schemas import (
    BlueprintResponse,
    PlatformMode,
    RegeneratedHookPayload,
    SavedBlueprintRecord,
    TalentSavedProfile,
)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:36] or "produk_shopee"


def create_project_dir(cfg: dict[str, Any], product_name: str) -> Path:
    base = Path(cfg.get("paths", {}).get("projects_dir", "projects"))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    proj = base / f"{slugify(product_name)}_{ts}"
    proj.mkdir(parents=True, exist_ok=True)
    return proj


def _resolve_scene_count(duration_preset: str) -> int:
    low = duration_preset.lower()
    if "7 scene" in low:
        return 7
    if "5 scene" in low:
        return 5
    return 3


def _call_structured_llm(
    messages: list[dict[str, Any]],
    pydantic_cls: type,
    engine_mode: str,
    cfg: dict[str, Any],
    gemini_key: str,
    openrouter_key: str,
    use_vision: bool = True,
) -> tuple[Any, str, str]:
    """Return `(validated_obj, used_model_label, fallback_reason)`."""
    gem_cfg = cfg.get("gemini", {})
    or_cfg = cfg.get("openrouter", {})
    presets = or_cfg.get("presets", {})
    free_cfg = presets.get("free_router", {})
    pro_cfg = presets.get("budget_pro", {})

    if engine_mode == "gemini_then_openrouter":
        gem_client = (
            GeminiClient(
                api_key=gemini_key,
                base_url=gem_cfg.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                timeout_sec=float(gem_cfg.get("timeout_sec", 60)),
                max_retries=int(gem_cfg.get("max_retries", 1)),
            )
            if gemini_key
            else None
        )
        or_client = (
            OpenRouterClient(
                api_key=openrouter_key,
                base_url=or_cfg.get("base_url", "https://openrouter.ai/api/v1"),
                timeout_sec=float(or_cfg.get("timeout_sec", 90)),
                max_retries=int(or_cfg.get("max_retries", 2)),
            )
            if openrouter_key
            else None
        )
        router = HybridLLMRouter(gemini_client=gem_client, openrouter_client=or_client)
        model_key = "vision_model" if use_vision else "text_model"
        fb_key = "vision_fallbacks" if use_vision else "text_fallbacks"
        gem_primary = get_gemini_model_override() or gem_cfg.get(
            model_key, "gemini-2.5-flash"
        )
        res, used_m = router.chat_json(
            messages=messages,
            pydantic_model=pydantic_cls,
            gemini_primary=gem_primary,
            gemini_fallbacks=gem_cfg.get("fallback_models", []),
            openrouter_primary=free_cfg.get(model_key, "google/gemma-3-27b-it:free"),
            openrouter_fallbacks=free_cfg.get(fb_key, []),
        )
        return res, used_m, router.last_fallback_reason

    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY belum diisi (atau pilih Mode demo offline di sidebar).")

    chosen_cfg = pro_cfg if engine_mode == "budget_pro" else free_cfg
    model_key = "vision_model" if use_vision else "text_model"
    fb_key = "vision_fallbacks" if use_vision else "text_fallbacks"
    client = OpenRouterClient(
        api_key=openrouter_key,
        base_url=or_cfg.get("base_url", "https://openrouter.ai/api/v1"),
        timeout_sec=float(or_cfg.get("timeout_sec", 90)),
        max_retries=int(or_cfg.get("max_retries", 2)),
    )
    res, used_m = client.chat_json(
        messages=messages,
        primary_model=chosen_cfg.get(model_key, "google/gemma-3-27b-it:free"),
        fallback_models=chosen_cfg.get(fb_key, []),
        pydantic_model=pydantic_cls,
    )
    return res, f"openrouter:{used_m}", ""


def generate_blueprint_service(
    product_images_bytes: list[bytes],
    profile: TalentSavedProfile,
    duration_preset: str,
    extra_note: str,
    engine_mode: str,
    cfg: dict[str, Any],
    gemini_key: str,
    openrouter_key: str,
    previous_hooks: list[str],
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    product_url: str = "",
    raw_specs_text: str = "",
    auto_web_enrich: bool = True,
    variation_index: int = 0,
    existing_project_dir: Path | None = None,
) -> tuple[SavedBlueprintRecord, ComplianceReport, Path, dict[str, Path], list[str]]:
    """Run 1-click blueprint generation enriched with Website/Spec Product Knowledge."""
    scene_count = _resolve_scene_count(duration_preset)
    projects_base = Path(cfg.get("paths", {}).get("projects_dir", "projects"))

    combined_hooks = list(previous_hooks)
    if extra_note.strip():
        for h in load_product_hooks(extra_note.strip(), projects_base):
            if h not in combined_hooks:
                combined_hooks.append(h)

    k_ctx = KnowledgeContext()
    fallback_reason = ""

    if engine_mode == "offline_demo":
        if raw_specs_text.strip():
            k_ctx.sources_used.append("Deskripsi/Spesifikasi Toko")
        if product_url.strip():
            k_ctx.sources_used.append("URL Produk (Demo)")
        if product_images_bytes:
            k_ctx.sources_used.insert(0, "Analisis Gambar Produk")
        raw_bp = build_offline_demo_blueprint(
            profile=profile,
            scene_count=scene_count,
            extra_note=extra_note,
            variation_index=variation_index,
            platform_mode=platform_mode,
        )
        used_model = "offline-demo"
    else:
        k_ctx = gather_product_knowledge_context(
            product_url=product_url,
            raw_specs_text=raw_specs_text,
            auto_web_search=auto_web_enrich,
            search_hint=extra_note,
        )
        if product_images_bytes:
            k_ctx.sources_used.insert(0, "Vision Gambar Produk")

        prod_urls = [image_bytes_to_data_url(b) for b in product_images_bytes]
        messages = build_blueprint_messages(
            product_image_urls=prod_urls,
            profile=profile,
            scene_count=scene_count,
            extra_note=extra_note,
            previous_hooks=combined_hooks,
            platform_mode=platform_mode,
            knowledge_context_text=k_ctx.combined_text,
        )
        raw_bp, used_model, fallback_reason = _call_structured_llm(
            messages=messages,
            pydantic_cls=BlueprintResponse,
            engine_mode=engine_mode,
            cfg=cfg,
            gemini_key=gemini_key,
            openrouter_key=openrouter_key,
            use_vision=True,
        )

    final_bp = enforce_commercial_mechanisms(
        raw_bp,
        is_faceless=profile.is_faceless,
        platform_mode=platform_mode,
        profile=profile,
    )

    prod_name = final_bp.product_analysis.product_name
    persisted_hooks = append_product_hook(
        product_name=prod_name,
        hook_text=final_bp.scenes[0].vo_script_id,
        projects_dir=projects_base,
    )
    for h in combined_hooks:
        if h not in persisted_hooks:
            persisted_hooks.insert(0, h)

    proj_dir = existing_project_dir or create_project_dir(cfg, prod_name)

    cropped_path_str = ""
    if product_images_bytes:
        clean_img_path, _ = save_clean_ingredient_image(
            product_images_bytes[0],
            output_dir=proj_dir / "input",
        )
        cropped_path_str = str(clean_img_path)

    record = SavedBlueprintRecord(
        project_id=proj_dir.name,
        created_at=datetime.now().isoformat(timespec="seconds"),
        platform_mode=platform_mode,
        duration_preset=duration_preset,
        persona=profile.persona.value,
        talent_preset_name=profile.talent_name,
        model_used=used_model,
        fallback_reason=fallback_reason,
        knowledge_sources=k_ctx.sources_used,
        cropped_ingredient_path=cropped_path_str,
        previous_hooks=persisted_hooks,
        blueprint=final_bp,
    )
    comp_report = audit_blueprint(final_bp)
    artifacts = save_blueprint_artifacts(record, comp_report, proj_dir)
    return record, comp_report, proj_dir, artifacts, k_ctx.warnings


def regenerate_hook_service(
    record: SavedBlueprintRecord,
    profile: TalentSavedProfile,
    engine_mode: str,
    cfg: dict[str, Any],
    gemini_key: str,
    openrouter_key: str,
    variation_index: int,
    project_dir: Path,
) -> tuple[SavedBlueprintRecord, ComplianceReport, dict[str, Path]]:
    """Regenerate Scene 1 Hook only (anti-spam variation) while bridging into Scene 2."""
    projects_base = Path(cfg.get("paths", {}).get("projects_dir", "projects"))
    prod_name = record.blueprint.product_analysis.product_name

    historical_hooks = load_product_hooks(prod_name, projects_base)
    all_prev_hooks = list(dict.fromkeys([*historical_hooks, *record.previous_hooks]))

    fallback_reason = ""
    if engine_mode == "offline_demo":
        payload = build_offline_demo_regenerated_hook(
            blueprint=record.blueprint,
            variation_index=variation_index,
        )
        used_model = "offline-demo"
    else:
        messages = build_regenerate_hook_messages(
            blueprint=record.blueprint,
            profile=profile,
            previous_hooks=all_prev_hooks,
            platform_mode=record.platform_mode,
        )
        payload, used_model, fallback_reason = _call_structured_llm(
            messages=messages,
            pydantic_cls=RegeneratedHookPayload,
            engine_mode=engine_mode,
            cfg=cfg,
            gemini_key=gemini_key,
            openrouter_key=openrouter_key,
            use_vision=False,
        )

    merged_bp = apply_regenerated_hook(
        bp=record.blueprint,
        payload=payload,
        is_faceless=profile.is_faceless,
        platform_mode=record.platform_mode,
        profile=profile,
    )
    persisted_hooks = append_product_hook(
        product_name=prod_name,
        hook_text=merged_bp.scenes[0].vo_script_id,
        projects_dir=projects_base,
    )

    updated_record = record.model_copy(
        update={
            "model_used": used_model,
            "fallback_reason": fallback_reason,
            "previous_hooks": persisted_hooks,
            "blueprint": merged_bp,
        }
    )
    comp_report = audit_blueprint(merged_bp)
    artifacts = save_blueprint_artifacts(updated_record, comp_report, project_dir)
    return updated_record, comp_report, artifacts
