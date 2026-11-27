"""Core engine enforcing Commercial-Grade Mechanisms, Specific Flow Actions, and Platform Safety."""

from __future__ import annotations

import re

from src.compliance import normalize_hashtags_in_caption, normalize_platform_terms
from src.schemas import BlueprintResponse, FlowScene, PlatformMode, RegeneratedHookPayload

FOLEY_AUDIO_SUFFIX = (
    "Audio: subtle realistic room ambience and natural product foley only, "
    "no background music, no spoken dialogue."
)


def count_words(text: str) -> int:
    """Count spoken words in an Indonesian VO or headline string."""
    tokens = [t for t in re.split(r"\s+", text.strip()) if re.search(r"\w", t)]
    return len(tokens)


def _trim_headline_words(text: str, max_words: int = 5) -> str:
    words = [w for w in text.strip().split() if w]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])


def _inject_visual_bible(prompt_en: str, visual_bible_en: str) -> str:
    clean_prompt = prompt_en.strip()
    clean_bible = visual_bible_en.strip()
    if not clean_bible:
        return clean_prompt

    bible_probe = clean_bible[:48].lower()
    if bible_probe not in clean_prompt.lower() and "[visual bible" not in clean_prompt.lower():
        clean_prompt = f"[Visual Bible: {clean_bible}] {clean_prompt}"

    if "9:16" not in clean_prompt:
        clean_prompt = f"9:16 vertical commercial frame. {clean_prompt}"

    if "no background music" not in clean_prompt.lower():
        if not clean_prompt.endswith("."):
            clean_prompt += "."
        clean_prompt = f"{clean_prompt} {FOLEY_AUDIO_SUFFIX}"

    return clean_prompt


def _normalize_flow_action(raw_action: str, scene_idx: int, prompt_en: str) -> str:
    """Normalize Google Flow Scene Builder action to 'New Scene', 'Extend', or 'Jump to'."""
    if scene_idx == 1:
        return "New Scene"

    low = raw_action.strip().lower()
    if low == "extend":
        return "Extend"
    if low in ("jump to", "jumpto", "jump"):
        return "Jump to"

    p_low = prompt_en.lower()
    if any(kw in p_low for kw in ("macro", "extreme close-up", "cut to", "hero closing", "pedestal", "podium")):
        return "Jump to"
    return "Extend"


def enforce_commercial_mechanisms(
    bp: BlueprintResponse,
    is_faceless: bool = True,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
) -> BlueprintResponse:
    """Deterministically enforce Commercial-Grade rules on a BlueprintResponse."""
    bible = bp.flow_setup.locked_visual_bible_en.strip()

    if is_faceless:
        checklist = [
            "Foto Produk Bersih (unduh dari hasil crop bebas UI Shopee di bawah)",
            "Cukup foto produk saja — wajah/talking-head & pengisian suara diatur di CapCut",
        ]
    else:
        checklist = [
            "Foto Produk Bersih (unduh dari hasil crop bebas UI Shopee di bawah)",
            "Foto Wajah Talent (unggah langsung ke menu Ingredients Google Flow jika ingin wajah konsisten di Flow)",
        ]

    updated_setup = bp.flow_setup.model_copy(
        update={
            "aspect_ratio": "9:16",
            "ingredients_checklist": checklist,
        }
    )

    fixed_scenes: list[FlowScene] = []
    for idx, scene in enumerate(bp.scenes, start=1):
        enriched_prompt = _inject_visual_bible(scene.flow_prompt_en, bible)
        resolved_action = _normalize_flow_action(scene.flow_action, idx, enriched_prompt)

        continuity = scene.continuity_note.strip()
        if not continuity:
            if idx == 1:
                continuity = "Adegan pembuka: pastikan produk dari Ingredients tampil utuh sebelum akhir klip."
            elif resolved_action == "Jump to":
                continuity = f"Pindah sudut kamera (Jump to) ke detail produk dengan tetap mengunci lokasi & objek dari Scene {idx - 1}."
            else:
                continuity = f"Melanjutkan gerakan langsung dari frame terakhir Scene {idx - 1} menggunakan tombol Extend."

        vo_clean = normalize_platform_terms(scene.vo_script_id.strip(), platform_mode=platform_mode)
        headline_clean = _trim_headline_words(
            normalize_platform_terms(scene.on_screen_text_id, platform_mode=platform_mode),
            max_words=5,
        )

        fixed_scenes.append(
            scene.model_copy(
                update={
                    "scene_number": idx,
                    "flow_action": resolved_action,
                    "continuity_note": continuity,
                    "flow_prompt_en": enriched_prompt,
                    "vo_script_id": vo_clean,
                    "on_screen_text_id": headline_clean,
                }
            )
        )

    full_vo = " ".join(s.vo_script_id for s in fixed_scenes)
    shopee_cap = normalize_hashtags_in_caption(
        normalize_platform_terms(
            bp.capcut_finishing.shopee_caption_and_hashtags,
            platform_mode=PlatformMode.SHOPEE,
        )
    )
    tiktok_raw = bp.capcut_finishing.tiktok_caption_and_hashtags.strip()
    if not tiktok_raw:
        tiktok_raw = re.sub(
            r"#Shopee\w*",
            "#TikTokShopAffiliate",
            shopee_cap,
            flags=re.IGNORECASE,
        )
    tiktok_cap = normalize_hashtags_in_caption(
        normalize_platform_terms(tiktok_raw, platform_mode=PlatformMode.TIKTOK)
    )

    reminder = bp.capcut_finishing.compliance_reminder.strip()
    if "ai" not in reminder.lower():
        reminder = "Wajib aktifkan label 'Konten Buatan AI' saat upload di Shopee Video / TikTok Shop."

    updated_finishing = bp.capcut_finishing.model_copy(
        update={
            "full_vo_script_id": full_vo,
            "shopee_caption_and_hashtags": shopee_cap,
            "tiktok_caption_and_hashtags": tiktok_cap,
            "compliance_reminder": reminder,
        }
    )

    pk = bp.product_knowledge
    specs = [s.strip() for s in pk.technical_specs_and_materials if s.strip()]
    if not specs and bp.product_analysis.usp:
        specs = list(bp.product_analysis.usp)

    pinned_faq = normalize_platform_terms(pk.pinned_comment_faq_id.strip(), platform_mode=platform_mode)
    if not pinned_faq:
        bullet_lines = "\n".join(f"• {item}" for item in specs[:4])
        pinned_faq = (
            f"📌 Ringkasan Spek {bp.product_analysis.product_name}:\n"
            f"{bullet_lines}\n"
            "Yuk cek stok & voucher promonya langsung di keranjang!"
        )

    updated_knowledge = pk.model_copy(
        update={
            "technical_specs_and_materials": specs,
            "pinned_comment_faq_id": pinned_faq,
        }
    )

    return bp.model_copy(
        update={
            "product_knowledge": updated_knowledge,
            "flow_setup": updated_setup,
            "scenes": fixed_scenes,
            "capcut_finishing": updated_finishing,
        }
    )


def apply_regenerated_hook(
    bp: BlueprintResponse,
    payload: RegeneratedHookPayload,
    is_faceless: bool = True,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
) -> BlueprintResponse:
    """Replace Scene 1 with a new anti-spam Hook and update Scene 2 bridge + Full VO."""
    new_scenes = list(bp.scenes)
    new_scenes[0] = payload.scene_1.model_copy(
        update={
            "scene_number": 1,
            "role": "Hook",
            "flow_action": "New Scene",
        }
    )
    if len(new_scenes) >= 2 and payload.scene_2_continuity_note.strip():
        new_scenes[1] = new_scenes[1].model_copy(
            update={"continuity_note": payload.scene_2_continuity_note.strip()}
        )

    updated_analysis = bp.product_analysis.model_copy(
        update={"hook_angle": payload.hook_angle.strip()}
    )
    merged = bp.model_copy(
        update={
            "product_analysis": updated_analysis,
            "scenes": new_scenes,
        }
    )
    return enforce_commercial_mechanisms(
        merged,
        is_faceless=is_faceless,
        platform_mode=platform_mode,
    )
