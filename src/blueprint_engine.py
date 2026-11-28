"""Core engine enforcing Storyboard-First, Minimalist Anti-Halu Google Flow / Veo 3.1 Prompts & 3-Role Ingredients."""

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

NEGATIVE_CONSTRAINT_SUFFIX = "No text overlays, no additional logos, no readable screens."
MAX_CORE_PROMPT_WORDS = 26
MAX_GRID_CORE_WORDS = 36

_PRODUCT_REDESCRIPTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "product-part-redescription",
        re.compile(
            r"\b(?:red|blue|green|black|white|beige|khaki|tan|brown|silver|gold|frosted|matte|amber|clear|transparent)\s+"
            r"(?:bottle|chair|cap|legs?|frame|label|logo|fabric|canvas|glass|box|packaging|tube|zipper|pocket|handle|headrest|dropper)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "material-part-redescription",
        re.compile(
            r"\b(?:steel|metal|alumin(?:i)?um|wooden|plastic|tubular|rubber)\s+"
            r"(?:legs?|frame|cap|feet|posts?|bulb|collar)\b",
            re.IGNORECASE,
        ),
    ),
    ("structural-redescription", re.compile(r"\b(?:x-frame|foam\s+headrest)\b", re.IGNORECASE)),
    ("text-logo-redescription", re.compile(r"\bprinted\s+(?:logo|label|text|wordmark)\b", re.IGNORECASE)),
]

_NARRATIVE_ACTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "narrative-verb",
        re.compile(
            r"\b(?:walks?\s+toward|walking\s+toward|picks?\s+up|picking\s+up|"
            r"opens?(?:\s+the\s+(?:door|cap|pocket))?|opening(?:\s+the\s+(?:door|cap|pocket))?|"
            r"grabs?|unpacks?|twists?|rotates?|bends?|sits?\s+down|stands?\s+up)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "deformation-verb",
        re.compile(
            r"\b(?:folds?|folding|folded|unfolds?|unfolding|collaps(?:es?|ing|ed)|"
            r"assembl(?:es?|ing)|disassembl(?:es?|ing)|morph(?:s|ing))\b",
            re.IGNORECASE,
        ),
    ),
]

_WESTERN_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(blonde-haired|blue-eyed)\b", re.IGNORECASE), "dark-haired Indonesian"),
    (
        re.compile(
            r"\b(caucasian|western|european)\s+(man|woman|creator|person|talent|model|presenter|features)\b",
            re.IGNORECASE,
        ),
        r"Indonesian \2",
    ),
    (re.compile(r"\b(caucasian|western|european)\b", re.IGNORECASE), "Indonesian"),
]

_BRACKET_PREFIX_RE = re.compile(
    r"\[\s*(?:Visual Bible|STRICT PRODUCT LOCK[^:\]]*|INDONESIAN AVATAR LOCK|SUBJECT LOCK)\s*:?\s*",
    re.IGNORECASE,
)


def count_words(text: str) -> int:
    """Count words (including @mentions) in a script or Flow prompt."""
    tokens = [t for t in re.split(r"\s+", text.strip()) if re.search(r"\w", t)]
    return len(tokens)


def _trim_headline_words(text: str, max_words: int = 5) -> str:
    words = [w for w in text.strip().split() if w]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])


def detect_flow_prompt_hallucination_risks(text: str) -> list[str]:
    """Inspect a Google Flow prompt for SKILL.md anti-patterns (re-descriptions, narrative/deformation verbs)."""
    found: list[str] = []
    for label, pattern in (*_PRODUCT_REDESCRIPTION_PATTERNS, *_NARRATIVE_ACTION_PATTERNS):
        if pattern.search(text):
            found.append(label)
    return found


def sanitize_product_deformation_terms(prompt_en: str) -> str:
    """Strip brackets, double quotes, and Western appearance tokens."""
    out = (prompt_en or "").replace('"', "")
    out = _BRACKET_PREFIX_RE.sub("", out)
    out = out.replace("[", "").replace("]", "")

    for pattern, repl in _WESTERN_REPLACEMENTS:
        out = pattern.sub(repl, out)

    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r",\s*,+", ", ", out)
    out = re.sub(r"\.\s*\.+", ".", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()


def _parse_avatar_handle_and_traits(raw_tag: str) -> tuple[str, str]:
    """Extract standalone Google Flow handle (default `@me`) and optional concise extra traits."""
    raw = (raw_tag or "").strip()
    if not raw:
        return "@me", ""
    m = re.search(r"@[A-Za-z0-9_]+", raw)
    if m:
        handle = m.group(0)
        remainder = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        remainder = re.sub(r"^[,;\s]+|[,;\s]+$", "", remainder)
        remainder = re.sub(r"\s+", " ", remainder)
        clipped = " ".join(remainder.split()[:4])
        return handle, clipped
    return "@me", " ".join(raw.split()[:4])


def _bind_avatar_handle_in_segment(segment: str, handle: str) -> str:
    """Replace generic creator/talent nouns with standalone `handle` and ensure space-bounded tags."""
    out = segment
    out = re.sub(
        r"\b(?:the\s+)?(?:creator|talent)'s\b",
        f"{handle}'s",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:a|an|the)\s+(?:(?:young|casual|authentic|native)\s+)*(?:indonesian\s+)?(?:(?:male|female)\s+)?(?:creator|talent|presenter|reviewer)\b",
        f"{handle} Indonesian presenter",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(?:creator|talent)\s+(stands|sits|holds|points|shows|lifts|presses|touches|rests|gestures)\b",
        rf"{handle} \1",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(rf"\(\s*{re.escape(handle)}\s*\)", f" {handle} ", out)
    out = re.sub(r"\(\s*@ProductAuthority\s*\)", " @ProductAuthority ", out, flags=re.IGNORECASE)
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out


def build_avatar_identity_lock_en(
    profile: TalentSavedProfile | None,
    is_faceless: bool,
) -> str:
    """Return a concise positive Indonesian avatar/hands phrase for minimalist Veo prompts."""
    if is_faceless:
        return "natural Indonesian hands only"

    presence = profile.talent_presence if profile else TalentPresence.AVATAR_MALE_ID
    handle, extra_traits = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    if presence == TalentPresence.AVATAR_HIJAB_ID:
        base = f"{handle} Indonesian hijab presenter"
    elif presence == TalentPresence.AVATAR_FEMALE_ID:
        base = f"{handle} Indonesian female presenter"
    else:
        base = f"{handle} Indonesian male presenter"

    if extra_traits:
        return f"{base}, {extra_traits}"
    return base


def _extract_camera_directive(text: str, flow_action: str) -> str:
    low = text.lower()
    if "extreme close-up" in low or "macro" in low:
        return "Locked-off macro close-up"
    if "dolly" in low:
        return "Smooth continuous dolly-in shot"
    if "tracking" in low or "orbit" in low or "arc" in low or "pan" in low:
        return "Slow tracking shot"
    if "pull-back" in low or "wide" in low or "zoom out" in low:
        return "Gentle pull-back shot"
    if "push-in" in low or flow_action == "Extend":
        return "Gentle push-in shot"
    return "Locked-off static camera shot"


def _extract_lighting_cue(text: str, visual_bible_en: str) -> str:
    combined = f"{text} {visual_bible_en}".lower()
    if "twilight" in combined:
        return "warm twilight light"
    if "afternoon" in combined or "golden" in combined or "grass" in combined or "outdoor" in combined:
        return "warm afternoon outdoor light"
    if "morning" in combined or "window" in combined:
        return "soft morning window light"
    if "studio" in combined or "pedestal" in combined:
        return "warm directional studio light"
    return "soft natural indoor light"


def _strip_existing_negative_tail(text: str) -> str:
    cleaned = re.sub(
        r"\s*No text overlays,\s*no additional logos,\s*no readable screens\.?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(r"\s*Audio:\s*.*$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    return cleaned.rstrip(" .")


def _resolve_grid_layout(scene_count: int) -> str:
    if scene_count >= 7:
        return "3x3"
    if scene_count >= 5:
        return "3x2"
    return "2x2"


def _compose_minimalist_flow_prompt(
    prompt_en: str,
    visual_bible_en: str,
    flow_action: str,
    avatar_handle: str,
    avatar_lock_en: str,
    is_faceless: bool,
) -> str:
    """Enforce Minimalist Anti-Halu Formula (<= 35 words, target < 30 words) deterministically & idempotently."""
    sanitized = sanitize_product_deformation_terms(prompt_en)
    core_body = _strip_existing_negative_tail(sanitized)
    if not is_faceless:
        core_body = _bind_avatar_handle_in_segment(core_body, avatar_handle)
    else:
        core_body = re.sub(r"\(\s*@ProductAuthority\s*\)", " @ProductAuthority ", core_body, flags=re.IGNORECASE)

    low_core = core_body.lower()
    has_product_tag = bool(re.search(r"(?:^|(?<=\s))@ProductAuthority(?=$|[\s.,;:!?])", core_body))
    has_avatar_tag = is_faceless or (
        bool(re.search(rf"(?:^|(?<=\s)){re.escape(avatar_handle)}(?=$|[\s'.,;:!?])", core_body))
        and "indonesian" in low_core
    )
    has_extend_lead = (
        flow_action != "Extend"
        or low_core.startswith("seamless continuation from the previous frame")
    )
    risks = detect_flow_prompt_hallucination_risks(core_body)

    if (
        has_product_tag
        and has_avatar_tag
        and has_extend_lead
        and not risks
        and count_words(core_body) <= MAX_CORE_PROMPT_WORDS
    ):
        return f"{core_body}. {NEGATIVE_CONSTRAINT_SUFFIX}"

    cam_cue = _extract_camera_directive(core_body, flow_action)
    light_cue = _extract_lighting_cue(core_body, visual_bible_en)
    avatar_part = " as the exact product" if is_faceless else f" with {avatar_lock_en}"

    if flow_action == "Extend":
        condensed_core = (
            f"Seamless continuation from the previous frame, {cam_cue[0].lower()}{cam_cue[1:]}. "
            f"Keep @ProductAuthority{avatar_part}, {light_cue}"
        )
    else:
        condensed_core = f"Use @ProductAuthority{avatar_part}. {cam_cue}, {light_cue}"

    condensed_core = re.sub(r"[ \t]{2,}", " ", condensed_core).strip(" .")
    return f"{condensed_core}. {NEGATIVE_CONSTRAINT_SUFFIX}"


def _normalize_start_to_end_prompt(raw_prompt: str, is_faceless: bool, avatar_lock_en: str) -> str:
    cleaned = _strip_existing_negative_tail(sanitize_product_deformation_terms(raw_prompt))
    if (
        "@ProductAuthority" in cleaned
        and not detect_flow_prompt_hallucination_risks(cleaned)
        and count_words(cleaned) <= MAX_CORE_PROMPT_WORDS
    ):
        return f"{cleaned}. {NEGATIVE_CONSTRAINT_SUFFIX}"

    subject_part = "@ProductAuthority" if is_faceless else f"@ProductAuthority with {avatar_lock_en}"
    return (
        f"Locked-off static camera transition using start and end frame with {subject_part}. "
        f"Seamless lighting shift to warm sunlight. {NEGATIVE_CONSTRAINT_SUFFIX}"
    )


def _normalize_storyboard_grid_prompt(
    raw_prompt: str,
    layout: str,
    is_faceless: bool,
    avatar_handle: str,
    avatar_lock_en: str,
    visual_bible_en: str,
) -> str:
    """Enforce clean Nano Banana Contact Sheet Grid prompt tagging @ProductAuthority & @me."""
    sanitized = sanitize_product_deformation_terms(raw_prompt)
    core_body = _strip_existing_negative_tail(sanitized)
    if not is_faceless:
        core_body = _bind_avatar_handle_in_segment(core_body, avatar_handle)

    has_product_tag = bool(re.search(r"(?:^|(?<=\s))@ProductAuthority(?=$|[\s.,;:!?])", core_body))
    has_avatar_tag = is_faceless or (
        bool(re.search(rf"(?:^|(?<=\s)){re.escape(avatar_handle)}(?=$|[\s'.,;:!?])", core_body))
        and "indonesian" in core_body.lower()
    )
    has_layout = layout.lower() in core_body.lower()
    if (
        has_product_tag
        and has_avatar_tag
        and has_layout
        and not detect_flow_prompt_hallucination_risks(core_body)
        and count_words(core_body) <= MAX_GRID_CORE_WORDS
    ):
        return f"{core_body}. {NEGATIVE_CONSTRAINT_SUFFIX}"

    light_cue = _extract_lighting_cue(core_body, visual_bible_en)
    avatar_part = " cleanly" if is_faceless else f" with {avatar_lock_en}"
    return (
        f"Clean {layout} vertical storyboard contact sheet grid of 9:16 panels. "
        f"Use @ProductAuthority{avatar_part}, uniform framing and {light_cue} across all panels. "
        f"{NEGATIVE_CONSTRAINT_SUFFIX}"
    )


def _normalize_keyframe_image_prompt(
    raw_prompt: str,
    flow_prompt_en: str,
    scene_idx: int,
    role: str,
    is_faceless: bool,
    avatar_handle: str,
    avatar_lock_en: str,
    visual_bible_en: str,
) -> str:
    """Enforce concise 9:16 Nano Banana keyframe prompt anchored to @ProductAuthority / Master Frame."""
    sanitized = sanitize_product_deformation_terms(raw_prompt)
    core_body = _strip_existing_negative_tail(sanitized)
    if not is_faceless:
        core_body = _bind_avatar_handle_in_segment(core_body, avatar_handle)

    has_product_tag = bool(re.search(r"(?:^|(?<=\s))@ProductAuthority(?=$|[\s.,;:!?])", core_body))
    has_avatar_tag = is_faceless or (
        bool(re.search(rf"(?:^|(?<=\s)){re.escape(avatar_handle)}(?=$|[\s'.,;:!?])", core_body))
        and "indonesian" in core_body.lower()
    )
    if (
        core_body
        and has_product_tag
        and has_avatar_tag
        and not detect_flow_prompt_hallucination_risks(core_body)
        and count_words(core_body) <= MAX_CORE_PROMPT_WORDS
    ):
        return f"{core_body}. {NEGATIVE_CONSTRAINT_SUFFIX}"

    light_cue = _extract_lighting_cue(flow_prompt_en, visual_bible_en)
    avatar_part = "" if is_faceless else f" with {avatar_lock_en}"
    role_low = role.lower()
    flow_low = flow_prompt_en.lower()

    if scene_idx == 1:
        lead = "Photorealistic 9:16 Master Frame still"
    elif "macro" in flow_low or "bedah spek" in role_low or "demo" in role_low:
        lead = "Photorealistic 9:16 macro keyframe from Master Frame"
    elif "cta" in role_low:
        lead = "Photorealistic 9:16 closing hero keyframe from Master Frame"
    else:
        lead = "Photorealistic 9:16 interaction keyframe from Master Frame"

    return f"{lead}. Use @ProductAuthority{avatar_part}, {light_cue}. {NEGATIVE_CONSTRAINT_SUFFIX}"


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


def compose_talking_voice_flow_prompt(
    minimal_prompt: str,
    vo_script_id: str,
    avatar_lock_en: str,
    is_faceless: bool,
) -> str:
    """Build ready-to-paste Google Flow prompt combining anti-halu visual lock with Indonesian spoken VO."""
    visual_core = _strip_existing_negative_tail(sanitize_product_deformation_terms(minimal_prompt))
    clean_vo = re.sub(r'["\[\]]+', "", vo_script_id or "")
    clean_vo = re.sub(r"\s+", " ", clean_vo).strip()
    if not clean_vo:
        return minimal_prompt

    if is_faceless:
        return (
            f"{visual_core}. Clear natural Indonesian voiceover explains warmly: '{clean_vo}'. "
            f"{NEGATIVE_CONSTRAINT_SUFFIX}"
        )

    return (
        f"{visual_core}. {avatar_lock_en} speaks naturally to camera with synced lip movement "
        f"in clear friendly Indonesian voice: '{clean_vo}'. {NEGATIVE_CONSTRAINT_SUFFIX}"
    )


def compose_full_15s_flow_prompt(
    bp: BlueprintResponse,
    profile: TalentSavedProfile | None = None,
    include_voice: bool = True,
) -> str:
    """Build single-clip 15-second prompt combining first-3-scene script so Google Flow does not loop."""
    effective_faceless = profile.is_faceless if profile is not None else False
    avatar_lock = build_avatar_identity_lock_en(profile=profile, is_faceless=effective_faceless)
    visual_core = _strip_existing_negative_tail(
        sanitize_product_deformation_terms(bp.scenes[0].flow_prompt_en)
    )
    combined_vo = " ".join(s.vo_script_id.strip() for s in bp.scenes[:3] if s.vo_script_id.strip())
    clean_15s_vo = re.sub(r'["\[\]]+', "", combined_vo)
    clean_15s_vo = re.sub(r"\s+", " ", clean_15s_vo).strip()

    if not include_voice or not clean_15s_vo:
        return (
            f"Single continuous 15-second vertical 9:16 video with smooth pacing and no looping. "
            f"{visual_core}. {NEGATIVE_CONSTRAINT_SUFFIX}"
        )

    if effective_faceless:
        return (
            f"Single continuous 15-second vertical 9:16 video with smooth pacing and no looping. "
            f"{visual_core}. Clear natural Indonesian voiceover speaks continuously for 15 seconds: "
            f"'{clean_15s_vo}'. {NEGATIVE_CONSTRAINT_SUFFIX}"
        )

    return (
        f"Single continuous 15-second vertical 9:16 video with smooth pacing and no looping. "
        f"{visual_core}. {avatar_lock} speaks continuously to camera with synced lip movement "
        f"in clear friendly Indonesian voice for 15 seconds: '{clean_15s_vo}'. "
        f"{NEGATIVE_CONSTRAINT_SUFFIX}"
    )


def enforce_commercial_mechanisms(
    bp: BlueprintResponse,
    is_faceless: bool = False,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    profile: TalentSavedProfile | None = None,
) -> BlueprintResponse:
    """Deterministically enforce Storyboard-First, Minimalist Anti-Halu Flow prompts, & Platform Safety."""
    effective_faceless = profile.is_faceless if profile is not None else is_faceless
    avatar_handle, _ = _parse_avatar_handle_and_traits(
        profile.avatar_flow_tag if profile else "@me"
    )
    avatar_lock = build_avatar_identity_lock_en(profile=profile, is_faceless=effective_faceless)
    bible = sanitize_product_deformation_terms(bp.flow_setup.locked_visual_bible_en.strip())
    geo_lock = sanitize_product_deformation_terms(bp.flow_setup.exact_product_geometry_lock_en.strip())
    grid_layout = _resolve_grid_layout(len(bp.scenes))
    grid_prompt = _normalize_storyboard_grid_prompt(
        raw_prompt=bp.flow_setup.storyboard_grid_prompt_en,
        layout=grid_layout,
        is_faceless=effective_faceless,
        avatar_handle=avatar_handle,
        avatar_lock_en=avatar_lock,
        visual_bible_en=bible,
    )
    s2e_prompt = _normalize_start_to_end_prompt(
        bp.flow_setup.start_to_end_prompt_en,
        is_faceless=effective_faceless,
        avatar_lock_en=avatar_lock,
    )

    if effective_faceless:
        checklist = [
            "Ingredient 1 — @ProductAuthority: Upload foto produk bersih berlatar polos (pastikan ujung kaki/alas produk utuh)",
            f"Storyboard Grid ({grid_layout}) — Generate gambar keyframe dulu di Nano Banana / Flow Image Mode lalu Auto-Split",
            "Frames to Video — Masukkan keyframe hasil Auto-Split ke Start Frame di Google Flow + tempel prompt gerak < 35 kata",
        ]
    else:
        checklist = [
            "Ingredient 1 — @ProductAuthority: Upload foto produk bersih (ujung kaki/alas utuh, latar polos)",
            f"Storyboard Grid ({grid_layout}) — Generate keyframe bersama {avatar_handle} di Nano Banana dulu sebelum render video",
            "Frames to Video — Pasang keyframe hasil Auto-Split ke Start Frame agar bentuk kaki produk & wajah tidak berubah",
        ]

    updated_setup = bp.flow_setup.model_copy(
        update={
            "aspect_ratio": "9:16",
            "ingredients_checklist": checklist,
            "exact_product_geometry_lock_en": geo_lock,
            "start_to_end_prompt_en": s2e_prompt,
            "storyboard_grid_layout": grid_layout,
            "storyboard_grid_prompt_en": grid_prompt,
            "locked_visual_bible_en": bible,
        }
    )

    fixed_scenes: list[FlowScene] = []
    for idx, scene in enumerate(bp.scenes, start=1):
        resolved_action = _normalize_flow_action(scene.flow_action, idx, scene.flow_prompt_en)
        minimal_prompt = _compose_minimalist_flow_prompt(
            prompt_en=scene.flow_prompt_en,
            visual_bible_en=bible,
            flow_action=resolved_action,
            avatar_handle=avatar_handle,
            avatar_lock_en=avatar_lock,
            is_faceless=effective_faceless,
        )
        keyframe_prompt = _normalize_keyframe_image_prompt(
            raw_prompt=scene.keyframe_image_prompt_en,
            flow_prompt_en=minimal_prompt,
            scene_idx=idx,
            role=scene.role,
            is_faceless=effective_faceless,
            avatar_handle=avatar_handle,
            avatar_lock_en=avatar_lock,
            visual_bible_en=bible,
        )

        continuity = scene.continuity_note.strip()
        if not continuity:
            if idx == 1:
                continuity = "Gunakan Master Frame + @ProductAuthority sebagai Start Frame Scene 1."
            elif resolved_action == "Jump to":
                continuity = f"Pasang Keyframe Scene {idx} ke Start Frame (atau Jump to sambil tetap memilih @ProductAuthority)."
            else:
                continuity = f"Lanjut mulus dari frame terakhir Scene {idx - 1} menggunakan Extend."

        vo_clean = normalize_platform_terms(scene.vo_script_id.strip(), platform_mode=platform_mode)
        voice_prompt = compose_talking_voice_flow_prompt(
            minimal_prompt=minimal_prompt,
            vo_script_id=vo_clean,
            avatar_lock_en=avatar_lock,
            is_faceless=effective_faceless,
        )
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
                    "keyframe_image_prompt_en": keyframe_prompt,
                    "flow_prompt_en": minimal_prompt,
                    "flow_voice_prompt_en": voice_prompt,
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
    """Replace Scene 1 with a new anti-spam Hook and re-enforce Storyboard & Minimalist Anti-Halu rules."""
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
