"""Core engine enforcing 1:1 Product Geometry Lock, Indonesian Google Flow Avatar Lock, and Platform Safety."""

from __future__ import annotations

import re

from src.compliance import normalize_hashtags_in_caption, normalize_platform_terms
from src.schemas import (
    BlueprintResponse,
    FlowScene,
    PlatformMode,
    RegeneratedHookPayload,
    TalentPresence,
    TalentSavedProfile,
)

FOLEY_AUDIO_SUFFIX = (
    "Audio: subtle realistic room ambience and natural product foley only, "
    "no background music, no spoken dialogue."
)

# Mechanical deformation actions that cause Google Flow / Veo to hallucinate wrong legs, hinges, or shapes
_DEFORMATION_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bunfolding\b", re.IGNORECASE), "presenting the already-open intact"),
    (re.compile(r"\bunfolds\b", re.IGNORECASE), "presents the already-open intact"),
    (re.compile(r"\bunfold\b", re.IGNORECASE), "present the intact"),
    (re.compile(r"\bfolding\s+up\b", re.IGNORECASE), "steadily holding the intact"),
    (re.compile(r"\bfolding\b", re.IGNORECASE), "steadily showcasing the intact"),
    (re.compile(r"\bfolds\s+up\b", re.IGNORECASE), "steadily holds the intact"),
    (re.compile(r"\bfolded\s+up\b", re.IGNORECASE), "upright intact"),
    (re.compile(r"\bfolded\b", re.IGNORECASE), "upright intact"),
    (re.compile(r"\bcollapsing\b", re.IGNORECASE), "keeping steady the intact"),
    (re.compile(r"\bcollapsed\b", re.IGNORECASE), "upright intact"),
    (re.compile(r"\bdisassembling\b", re.IGNORECASE), "inspecting"),
    (re.compile(r"\bassembling\b", re.IGNORECASE), "showcasing"),
    (re.compile(r"\bmorphing\b", re.IGNORECASE), "maintaining exact shape"),
]


def count_words(text: str) -> int:
    """Count spoken words in an Indonesian VO or headline string."""
    tokens = [t for t in re.split(r"\s+", text.strip()) if re.search(r"\w", t)]
    return len(tokens)


def _trim_headline_words(text: str, max_words: int = 5) -> str:
    words = [w for w in text.strip().split() if w]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])


def sanitize_product_deformation_terms(prompt_en: str) -> str:
    """Remove folding/unfolding/collapsing verbs that make Google Flow invent wrong product legs/parts."""
    cleaned = prompt_en
    # Protect our own negative guard clause if already present
    guard_marker = "do NOT redesign legs, do NOT invent unseen parts, and do NOT fold or deform"
    has_guard = guard_marker.lower() in cleaned.lower()
    if has_guard:
        idx = cleaned.lower().find("[strict product lock")
        if idx != -1:
            end_idx = cleaned.find("]", idx)
            if end_idx != -1:
                prefix = cleaned[:idx]
                lock_part = cleaned[idx : end_idx + 1]
                suffix = cleaned[end_idx + 1 :]
                return (
                    _apply_deformation_regex(prefix)
                    + lock_part
                    + _apply_deformation_regex(suffix)
                )
    return _apply_deformation_regex(cleaned)


def _apply_deformation_regex(segment: str) -> str:
    out = segment
    for pattern, repl in _DEFORMATION_REPLACEMENTS:
        out = pattern.sub(repl, out)
    # Remove positive Western model descriptors if accidentally generated outside "NO Western/Caucasian"
    out = re.sub(r"\b(blonde-haired|blue-eyed)\b", "dark-haired Indonesian", out, flags=re.IGNORECASE)
    out = re.sub(
        r"(?<!no\s)(?<!not\s)\b(caucasian|european)\s+(man|woman|creator|person|talent|model)\b",
        r"authentic native Indonesian \2",
        out,
        flags=re.IGNORECASE,
    )
    return out


def _parse_avatar_handle_and_traits(raw_tag: str) -> tuple[str, str]:
    """Extract standalone Google Flow handle (default `@me`) and optional extra traits."""
    raw = (raw_tag or "").strip()
    if not raw:
        return "@me", ""
    m = re.search(r"@[A-Za-z0-9_]+", raw)
    if m:
        handle = m.group(0)
        remainder = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        remainder = re.sub(r"^[,;\s]+|[,;\s]+$", "", remainder)
        remainder = re.sub(r"\s+", " ", remainder)
        return handle, remainder
    return "@me", raw


def _bind_avatar_handle_in_segment(segment: str, handle: str) -> str:
    """Replace generic creator/talent nouns with standalone `handle` and ensure space-bounded `@me`."""
    out = segment
    out = re.sub(
        r"\b(?:the\s+)?(?:creator|talent)'s\b",
        f"{handle}'s",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:a|an|the)\s+(?:(?:young|casual|authentic|native)\s+)*(?:indonesian\s+)?(?:(?:male|female)\s+)?(?:creator|talent|presenter|reviewer)\b",
        handle,
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:creator|talent)\s+(stands|sits|holds|points|shows|lifts|presses|touches|rests|gestures|walks|smiles|speaks|looks)\b",
        rf"{handle} \1",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:a|the)\s+(?:(?:indonesian)\s+)?(?:man|woman)\s+(stands|sits|holds|points|shows|lifts|presses|touches|rests|gestures|walks|smiles|looks)\b",
        rf"{handle} \1",
        out,
        flags=re.IGNORECASE,
    )
    # Never leave the handle wrapped inside parentheses like (@me)
    out = re.sub(rf"\(\s*{re.escape(handle)}\s*\)", f" {handle} ", out)
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out


def _apply_to_unbracketed(text: str, transform) -> str:
    """Apply `transform` only to segments outside `[...]` lock blocks."""
    parts = re.split(r"(\[[^\]]*\])", text)
    for i in range(0, len(parts), 2):
        parts[i] = transform(parts[i])
    return "".join(parts)


def build_avatar_identity_lock_en(
    profile: TalentSavedProfile | None,
    is_faceless: bool,
) -> str:
    """Build deterministic Google Flow `@me` Avatar + Native Indonesian Identity lock."""
    if is_faceless:
        return (
            "SUBJECT LOCK: Faceless B-roll — show only natural warm medium-tan Indonesian hands "
            "interacting gently with the product; strictly NO human face in frame."
        )

    presence = profile.talent_presence if profile else TalentPresence.AVATAR_MALE_ID
    handle, extra_traits = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    outfit_raw = profile.visual_notes.strip() if profile and profile.visual_notes else ""

    if presence == TalentPresence.AVATAR_HIJAB_ID:
        person_desc = (
            "authentic native Indonesian woman wearing a neat hijab, with Southeast Asian Nusantara facial structure, "
            "natural warm Indonesian skin tone, and dark brown eyes"
        )
    elif presence == TalentPresence.AVATAR_FEMALE_ID:
        person_desc = (
            "authentic native Indonesian woman with Southeast Asian Nusantara facial structure, "
            "natural warm Indonesian skin tone, natural dark black hair, and dark brown eyes"
        )
    else:
        person_desc = (
            "authentic native Indonesian man with Southeast Asian Nusantara facial structure, "
            "natural warm sawo-matang Indonesian skin tone, neat dark black hair, and dark brown eyes"
        )

    traits_clause = f", {extra_traits}" if extra_traits else ""
    outfit_clause = f", consistent attire ({outfit_raw})" if outfit_raw else ""
    return (
        f"INDONESIAN AVATAR LOCK: Featuring {handle} — use the exact 1:1 face, facial bone structure, "
        f"glasses/hair, eyes, and identity of {handle} — {person_desc}{traits_clause}{outfit_clause}; "
        "strictly NO Western, NO Caucasian, and NO European facial features."
    )


def _inject_visual_bible_and_locks(
    prompt_en: str,
    visual_bible_en: str,
    geometry_lock_en: str,
    avatar_lock_en: str,
    avatar_handle: str = "@me",
    is_faceless: bool = False,
) -> str:
    clean_prompt = sanitize_product_deformation_terms(prompt_en.strip())
    clean_bible = sanitize_product_deformation_terms(visual_bible_en.strip())
    clean_geo = geometry_lock_en.strip()

    if not is_faceless:
        clean_prompt = _apply_to_unbracketed(
            clean_prompt,
            lambda seg: _bind_avatar_handle_in_segment(seg, avatar_handle),
        )
        # Ensure standalone avatar handle appears in the visible action text outside lock blocks
        unbracketed_text = " ".join(re.split(r"\[[^\]]*\]", clean_prompt)[0::2])
        handle_pattern = rf"(?:^|(?<=\s)){re.escape(avatar_handle)}(?=$|[\s'.,;:!?])"
        if not re.search(handle_pattern, unbracketed_text):
            parts = re.split(r"(\[[^\]]*\])", clean_prompt)
            for idx in range(len(parts) - 1, -1, -2):
                stripped = parts[idx].strip()
                if stripped and not re.fullmatch(r"9:16 vertical commercial frame\.?", stripped, re.IGNORECASE):
                    parts[idx] = f" Featuring {avatar_handle} interacting naturally with the product: {stripped}"
                    break
            else:
                parts.append(f" Featuring {avatar_handle} interacting naturally with the product.")
            clean_prompt = "".join(parts)

    blocks: list[str] = []
    if "9:16" not in clean_prompt:
        blocks.append("9:16 vertical commercial frame.")

    if clean_bible:
        bible_probe = clean_bible[:42].lower()
        if bible_probe not in clean_prompt.lower() and "[visual bible" not in clean_prompt.lower():
            blocks.append(f"[Visual Bible: {clean_bible}]")

    if clean_geo and "[strict product lock" not in clean_prompt.lower():
        blocks.append(
            f"[STRICT PRODUCT LOCK — MATCH UPLOADED PRODUCT INGREDIENT 1:1: {clean_geo} "
            "Keep exact leg/frame/body geometry, joint structure, proportions, colors, and logo identical to the Product Ingredient photo; "
            "do NOT redesign legs, do NOT invent unseen parts, and do NOT fold or deform the product.]"
        )

    if avatar_lock_en and "indonesian avatar lock:" not in clean_prompt.lower() and "subject lock:" not in clean_prompt.lower():
        blocks.append(f"[{avatar_lock_en}]")

    blocks.append(clean_prompt)
    combined = re.sub(r"[ \t]{2,}", " ", " ".join(b for b in blocks if b)).strip()

    if "no background music" not in combined.lower():
        if not combined.endswith("."):
            combined += "."
        combined = f"{combined} {FOLEY_AUDIO_SUFFIX}"

    return combined


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
    is_faceless: bool = False,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    profile: TalentSavedProfile | None = None,
) -> BlueprintResponse:
    """Deterministically enforce 1:1 Product Geometry Lock, Indonesian Avatar Lock, and Platform Safety."""
    effective_faceless = profile.is_faceless if profile is not None else is_faceless
    avatar_handle, _ = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    bible = sanitize_product_deformation_terms(bp.flow_setup.locked_visual_bible_en.strip())
    if not effective_faceless:
        bible = _apply_to_unbracketed(
            bible,
            lambda seg: _bind_avatar_handle_in_segment(seg, avatar_handle),
        )
    geo_lock = bp.flow_setup.exact_product_geometry_lock_en.strip()
    avatar_lock = build_avatar_identity_lock_en(profile=profile, is_faceless=effective_faceless)

    if not effective_faceless and "no western" not in bible.lower():
        bible = f"{bible} [{avatar_lock}]"

    if effective_faceless:
        checklist = [
            "Ingredient 1 — Foto Produk Bersih (pastikan SELURUH bentuk kaki/rangka/bodi produk terlihat utuh, tidak terpotong)",
            "Saat klik New Scene maupun Jump to, pastikan Foto Produk Bersih tetap terpilih di bar prompt Google Flow agar bentuk produk tidak berubah",
        ]
    else:
        checklist = [
            "Ingredient 1 — Foto Produk Bersih (pastikan SELURUH bentuk kaki/rangka/bodi produk terlihat utuh, tidak terpotong)",
            f"Avatar Anda ({avatar_handle}) — Sudah otomatis tertulis sebagai '{avatar_handle}' di setiap prompt! Cukup tempel prompt ke Google Flow (atau pilih Avatar Anda dari asset menu jika perlu)",
            "PENTING: Pastikan Foto Produk tetap aktif di Ingredients/Asset setiap kali klik New Scene maupun Jump to agar kaki/bentuk produk tidak berubah!",
        ]

    updated_setup = bp.flow_setup.model_copy(
        update={
            "aspect_ratio": "9:16",
            "ingredients_checklist": checklist,
            "exact_product_geometry_lock_en": geo_lock,
            "locked_visual_bible_en": bible,
        }
    )

    fixed_scenes: list[FlowScene] = []
    for idx, scene in enumerate(bp.scenes, start=1):
        enriched_prompt = _inject_visual_bible_and_locks(
            prompt_en=scene.flow_prompt_en,
            visual_bible_en=bible,
            geometry_lock_en=geo_lock,
            avatar_lock_en=avatar_lock,
            avatar_handle=avatar_handle,
            is_faceless=effective_faceless,
        )
        resolved_action = _normalize_flow_action(scene.flow_action, idx, enriched_prompt)

        continuity = scene.continuity_note.strip()
        if not continuity:
            if idx == 1:
                continuity = "Adegan pembuka: pastikan produk tampil utuh persis seperti foto Ingredients tanpa aksi melipat/mengubah rangka."
            elif resolved_action == "Jump to":
                continuity = f"Pindah sudut kamera (Jump to) ke detail yang memang terlihat di foto dengan tetap memilih Ingredients Produk + Avatar dari Scene {idx - 1}."
            else:
                continuity = f"Melanjutkan gerakan mulus dari frame terakhir Scene {idx - 1} menggunakan tombol Extend."

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
    is_faceless: bool = False,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    profile: TalentSavedProfile | None = None,
) -> BlueprintResponse:
    """Replace Scene 1 with a new anti-spam Hook and re-enforce Product & Avatar locks."""
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
        profile=profile,
    )
