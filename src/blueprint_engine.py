"""Core engine enforcing Veo 3.1 / Google Flow 5-Law Anti-Hallucination & Positive Director Framing."""

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
    "Audio: quiet natural ambient soundscape and crisp realistic product foley only, "
    "silent presenter."
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

# "Pink Elephant" negative triggers in Veo 3.1 text prompts that must be stripped or converted positive
_NEGATIVE_TRIGGER_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?:strictly\s+)?no\s+(?:western|caucasian|european)"
            r"(?:\s*(?:,|and|or)\s*(?:no\s+)?(?:western|caucasian|european))*\s*(?:facial\s+)?features?",
            re.IGNORECASE,
        ),
        "authentic native Indonesian Nusantara features",
    ),
    (
        re.compile(
            r"\b(?:keep\s+exact\s+leg/frame/body\s+geometry[^;\n]*;\s*)?"
            r"do\s+not\s+(?:redesign|invent|fold|deform|distort|alter|change)[^.;!\n]*[.;!]?",
            re.IGNORECASE,
        ),
        "",
    ),
    (re.compile(r"\b(?:do\s+not|don't)\b", re.IGNORECASE), ""),
    (re.compile(r"\b(?:never\s+shown\s+damaged\s+or\s+broken|never\s+damaged|no\s+damage\s+to\s+product)\b", re.IGNORECASE), "pristine intact finish"),
    (re.compile(r"\bwithout\s+wobbling\b", re.IGNORECASE), "with rock-solid stability"),
    (re.compile(r"\bwithout\s+altering\s+([^.;!\n]+)", re.IGNORECASE), r"preserving original \1"),
    (re.compile(r"\bwithout\s+any\s+invented\s+or\s+altered\s+parts\b", re.IGNORECASE), "maintaining locked static geometry"),
    (re.compile(r"\bwithout\s+(?:any\s+)?sticky\s+film(?:\s+or\s+pilling)?\b", re.IGNORECASE), "with a smooth matte finish"),
    (re.compile(r"\bzero\s+sticky\s+film(?:\s+or\s+pilling)?\b", re.IGNORECASE), "smooth matte-hydrated skin sheen"),
    (re.compile(r"\bno\s+human\s+face(?:\s+in\s+frame)?\b", re.IGNORECASE), "clean framing solely on product and hands"),
    (re.compile(r"\b(?:strictly\s+)?faceless\s+product\s+b-roll\b", re.IGNORECASE), "macro hands-only product B-roll"),
    (re.compile(r"\bno\s+background\s+music\b", re.IGNORECASE), "quiet natural ambient soundscape"),
    (re.compile(r"\bno\s+spoken\s+dialogue\b", re.IGNORECASE), "silent presenter"),
    (re.compile(r"\b(blonde-haired|blue-eyed)\b", re.IGNORECASE), "dark-haired Indonesian"),
    (re.compile(r"\b(caucasian|western|european)\s+(man|woman|creator|person|talent|model|features)\b", re.IGNORECASE), r"authentic native Indonesian \2"),
    (re.compile(r"\b(caucasian|western|european)\b", re.IGNORECASE), "Indonesian"),
]

_BRACKET_PREFIX_RE = re.compile(
    r"\[\s*(?:Visual Bible|STRICT PRODUCT LOCK[^:\]]*|INDONESIAN AVATAR LOCK|SUBJECT LOCK)\s*:?\s*",
    re.IGNORECASE,
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


def sanitize_product_deformation_terms(prompt_en: str) -> str:
    """Strip meta-brackets, quotation marks, deformation verbs, and Veo Pink-Elephant negative triggers."""
    out = (prompt_en or "").replace('"', "")
    out = _BRACKET_PREFIX_RE.sub("", out)
    out = out.replace("[", "").replace("]", "")

    for pattern, repl in _DEFORMATION_REPLACEMENTS:
        out = pattern.sub(repl, out)
    for pattern, repl in _NEGATIVE_TRIGGER_REPLACEMENTS:
        out = pattern.sub(repl, out)

    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r",\s*,+", ", ", out)
    out = re.sub(r"\.\s*\.+", ".", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()


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
        r"\b(?:creator|talent)\s+(stands|sits|holds|points|shows|lifts|presses|touches|rests|gestures|walks|smiles|speaks|looks|dispenses|releases)\b",
        rf"{handle} \1",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:a|the)\s+(?:(?:indonesian)\s+)?(?:man|woman)\s+(stands|sits|holds|points|shows|lifts|presses|touches|rests|gestures|walks|smiles|looks|dispenses|releases)\b",
        rf"{handle} \1",
        out,
        flags=re.IGNORECASE,
    )
    # Never leave the handle wrapped inside parentheses like (@me)
    out = re.sub(rf"\(\s*{re.escape(handle)}\s*\)", f" {handle} ", out)
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out


def build_avatar_identity_lock_en(
    profile: TalentSavedProfile | None,
    is_faceless: bool,
) -> str:
    """Build clean positive Indonesian @me Avatar identity prose for Veo 3.1."""
    if is_faceless:
        return (
            "clean natural warm medium-tan Indonesian hands only in frame, "
            "keeping visual focus solely on the pristine product"
        )

    presence = profile.talent_presence if profile else TalentPresence.AVATAR_MALE_ID
    handle, extra_traits = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    outfit_raw = profile.visual_notes.strip() if profile and profile.visual_notes else ""

    if presence == TalentPresence.AVATAR_HIJAB_ID:
        person_desc = (
            "an authentic native Indonesian woman wearing a neat hijab, "
            "with Southeast Asian Nusantara facial structure, warm Indonesian skin tone, and dark brown eyes"
        )
    elif presence == TalentPresence.AVATAR_FEMALE_ID:
        person_desc = (
            "an authentic native Indonesian woman with Southeast Asian Nusantara facial structure, "
            "warm Indonesian skin tone, natural dark black hair, and dark brown eyes"
        )
    else:
        person_desc = (
            "an authentic native Indonesian man with Southeast Asian Nusantara facial structure, "
            "warm sawo-matang Indonesian skin tone, neat dark black hair, and dark brown eyes"
        )

    traits_clause = f", {extra_traits}" if extra_traits else ""
    outfit_clause = f", wearing consistent attire ({outfit_raw})" if outfit_raw else ""
    return (
        f"Featuring {handle} — {person_desc}{traits_clause}{outfit_clause}, "
        f"preserving exact 1:1 facial structure and identity of {handle}"
    )


def _strip_audio_and_framing_prefix(body: str) -> str:
    """Remove trailing Audio cue and leading 9:16/Extend framing header for idempotent composition."""
    cleaned = re.sub(r"\s*Audio:\s*.*$", "", body, flags=re.IGNORECASE | re.DOTALL).strip()
    cleaned = re.sub(
        r"^(?:Seamless continuation from the previous frame,\s*)?(?:Vertical\s+)?9:16(?:\s+vertical)?\s+commercial\s+(?:frame|video|shot)[.,:]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^Seamless continuation from the previous frame[.,:\s]*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned


def _compose_veo_director_prompt(
    prompt_en: str,
    visual_bible_en: str,
    geometry_lock_en: str,
    avatar_lock_en: str,
    flow_action: str,
    avatar_handle: str = "@me",
    is_faceless: bool = False,
) -> str:
    """Compose clean, linear, positive-only 5-Part Veo 3.1 Director prose (100% idempotent)."""
    body = sanitize_product_deformation_terms(prompt_en)
    body = _strip_audio_and_framing_prefix(body)
    clean_geo = sanitize_product_deformation_terms(geometry_lock_en).rstrip(".")
    clean_bible = sanitize_product_deformation_terms(visual_bible_en).rstrip(".")
    clean_avatar = avatar_lock_en.rstrip(".")

    if not is_faceless:
        body = _bind_avatar_handle_in_segment(body, avatar_handle)
        if "authentic native indonesian" not in body.lower():
            body = f"{clean_avatar}. {body}" if body else f"{clean_avatar}."
        handle_pat = rf"(?:^|(?<=\s)){re.escape(avatar_handle)}(?=$|[\s'.,;:!?])"
        if not re.search(handle_pat, body):
            body = f"Featuring {avatar_handle} interacting naturally with the product. {body}"
    else:
        if "indonesian hands" not in body.lower():
            body = f"{clean_avatar}. {body}" if body else f"{clean_avatar}."

    if clean_geo:
        geo_probe = clean_geo[:35].lower()
        if geo_probe not in body.lower():
            body = (
                f"{body.rstrip('.')}. "
                f"The product maintains locked static geometry and original proportions matching the Product Ingredient 1:1: {clean_geo}."
            )
        elif "locked static geometry" not in body.lower():
            body = f"{body.rstrip('.')}. Locked static geometry and original proportions remain preserved across every frame."

    # Add lightweight environment/lighting anchor only if body has no setting/lighting cue yet
    if clean_bible and not any(
        kw in body.lower() for kw in ("sunlight", "sunlit", "morning", "window", "outdoor", "indoor", "grass", "table", "room", "stone", "lighting")
    ):
        bible_body = _strip_audio_and_framing_prefix(clean_bible).rstrip(".")
        if bible_body:
            body = f"{body.rstrip('.')}. Setting and lighting: {bible_body}."

    framing_prefix = (
        "Seamless continuation from the previous frame, vertical 9:16 commercial frame,"
        if flow_action == "Extend"
        else "Vertical 9:16 commercial frame,"
    )
    body_clean = body.lstrip(".,:; ")
    full_body = f"{framing_prefix} {body_clean}".rstrip(" .")
    full_body = re.sub(r"\.\s*\.+", ".", full_body)
    full_body = re.sub(r"[ \t]{2,}", " ", full_body).strip()
    return f"{full_body}. {FOLEY_AUDIO_SUFFIX}"


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
    """Deterministically enforce Veo 3.1 positive framing, 1:1 Product Lock, @me Lock, and Platform Safety."""
    effective_faceless = profile.is_faceless if profile is not None else is_faceless
    avatar_handle, _ = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    bible = sanitize_product_deformation_terms(bp.flow_setup.locked_visual_bible_en.strip())
    if not effective_faceless:
        bible = _bind_avatar_handle_in_segment(bible, avatar_handle)
    geo_lock = sanitize_product_deformation_terms(bp.flow_setup.exact_product_geometry_lock_en.strip())
    avatar_lock = build_avatar_identity_lock_en(profile=profile, is_faceless=effective_faceless)

    if not effective_faceless and "authentic native indonesian" not in bible.lower():
        bible = f"{bible.rstrip('.')}. {avatar_lock}."

    if effective_faceless:
        checklist = [
            "Ingredient 1 — Foto Produk Bersih (pastikan SELURUH bentuk kaki/rangka/bodi produk terlihat utuh, tidak terpotong)",
            "Saat klik New Scene maupun Jump to, pastikan Foto Produk Bersih tetap terpilih di bar prompt Google Flow agar bentuk produk tidak berubah",
        ]
    else:
        checklist = [
            "Ingredient 1 — Foto Produk Bersih (pastikan SELURUH bentuk kaki/rangka/bodi produk terlihat utuh, tidak terpotong)",
            f"Avatar Anda ({avatar_handle}) — Otomatis terpasang berdiri sendiri sebagai '{avatar_handle}' di setiap prompt",
            "Tips Google Flow: Uji dulu pakai Veo Fast/Lite untuk cek kestabilan kaki produk, lalu render final di Veo Quality; pastikan Ingredient Produk aktif saat New Scene & Jump to!",
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
        resolved_action = _normalize_flow_action(scene.flow_action, idx, scene.flow_prompt_en)
        enriched_prompt = _compose_veo_director_prompt(
            prompt_en=scene.flow_prompt_en,
            visual_bible_en=bible,
            geometry_lock_en=geo_lock,
            avatar_lock_en=avatar_lock,
            flow_action=resolved_action,
            avatar_handle=avatar_handle,
            is_faceless=effective_faceless,
        )

        continuity = scene.continuity_note.strip()
        if not continuity:
            if idx == 1:
                continuity = "Adegan pembuka: pastikan produk tampil utuh persis seperti foto Ingredients tanpa aksi melipat/mengubah rangka."
            elif resolved_action == "Jump to":
                continuity = f"Pindah sudut kamera (Jump to) ke detail yang memang terlihat di foto dengan tetap memilih Ingredients Produk dari Scene {idx - 1}."
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
    """Replace Scene 1 with a new anti-spam Hook and re-enforce Veo 3.1 Product & @me locks."""
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
