"""Tests for Commercial-Grade Mechanisms, Lightweight Presets, Screenshot Cropper, SRT, & History."""

import io
from pathlib import Path

from PIL import Image

from src.blueprint_engine import (
    apply_regenerated_hook,
    count_words,
    enforce_commercial_mechanisms,
)
from src.history_store import append_product_hook, list_saved_blueprints, load_product_hooks
from src.image_prep import is_mobile_screenshot, prepare_clean_product_ingredient
from src.prompts import (
    COMMERCIAL_DIRECTOR_SYSTEM_PROMPT,
    build_offline_demo_blueprint,
    build_offline_demo_regenerated_hook,
)
from src.schemas import PersonaStyle, PlatformMode, TalentPresence, TalentSavedProfile
from src.srt_export import build_srt_from_blueprint
from src.talent_store import (
    load_preset_collection,
    load_talent_profile,
    save_talent_profile,
    set_active_preset,
)


def test_text_only_talent_presets_and_legacy_migration(tmp_path: Path):
    prof_dir = tmp_path / "profile"
    col = load_preset_collection(prof_dir)
    assert len(col.presets) >= 4
    default_prof = load_talent_profile(prof_dir)
    assert default_prof.is_faceless is False  # Default is Avatar Google Flow Saya (Pria Indonesia)
    assert default_prof.talent_presence == TalentPresence.AVATAR_MALE_ID
    assert default_prof.avatar_flow_tag == "@me"

    # Legacy preset file on disk missing avatar_flow_tag gets normalized to "@me"
    legacy_dir = tmp_path / "legacy_profile"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "talent_presets.json").write_text(
        '{"active_preset_id":"avatar_pria_id","presets":[{"preset_id":"avatar_pria_id","talent_name":"Pria","talent_presence":"Pria","avatar_flow_tag":""}]}',
        encoding="utf-8",
    )
    migrated_col = load_preset_collection(legacy_dir)
    assert migrated_col.presets[0].avatar_flow_tag == "@me"

    prof = TalentSavedProfile(
        preset_id="hijab_preset",
        talent_name="Hijab Antusias",
        talent_presence=TalentPresence.AVATAR_HIJAB_ID,
        persona=PersonaStyle.ANTUSIAS,
        avatar_flow_tag="@hijab_saya",
        visual_notes="Pashmina krem kasual",
    )
    save_talent_profile(prof, prof_dir)
    active = load_talent_profile(prof_dir)
    assert active.talent_name == "Hijab Antusias"
    assert active.avatar_flow_tag == "@hijab_saya"
    assert active.is_faceless is False

    switched = set_active_preset("broll_produk", prof_dir)
    assert switched.is_faceless is True

    # Legacy dicts migrate cleanly
    migrated = TalentSavedProfile.model_validate({"talent_name": "Old", "is_faceless": True})
    assert migrated.talent_presence == TalentPresence.FACELESS_BROLL
    migrated_male = TalentSavedProfile.model_validate({"talent_name": "OldMale", "talent_presence": "Pria"})
    assert migrated_male.talent_presence == TalentPresence.AVATAR_MALE_ID


def test_smart_shopee_screenshot_cropper():
    # Ultra-tall 20:9 phone screenshot (540x1200 -> H/W = 2.22 >= 1.92) is safely trimmed
    tall_buf = io.BytesIO()
    Image.new("RGB", (540, 1200), (240, 240, 240)).save(tall_buf, format="PNG")
    assert is_mobile_screenshot(tall_buf.getvalue()) is True
    cropped_bytes, was_cropped = prepare_clean_product_ingredient(tall_buf.getvalue())
    assert was_cropped is True
    with Image.open(io.BytesIO(cropped_bytes)) as out_im:
        assert out_im.height < 1200

    # Standard 9:16 portrait product photo (720x1280 -> H/W = 1.77 < 1.92) is NOT cropped so chair legs stay intact!
    portrait_buf = io.BytesIO()
    Image.new("RGB", (720, 1280), (200, 210, 220)).save(portrait_buf, format="PNG")
    assert is_mobile_screenshot(portrait_buf.getvalue()) is False
    _, portrait_cropped = prepare_clean_product_ingredient(portrait_buf.getvalue())
    assert portrait_cropped is False


def test_anti_hallucination_product_leg_lock_and_indonesian_avatar_lock():
    # 1. Default @me avatar mention with generic creator phrases rewritten & idempotent on re-run
    avatar_prof = TalentSavedProfile(
        talent_presence=TalentPresence.AVATAR_MALE_ID,
        avatar_flow_tag="",
        visual_notes="Kaos polos hitam rapi",
    )
    raw = build_offline_demo_blueprint(avatar_prof, scene_count=3)
    raw.flow_setup.exact_product_geometry_lock_en = (
        "Beige TrailTop bucket chair with tan-painted cross-brace tubular legs, "
        "vertical rear support posts, and black plastic foot caps."
    )
    raw.scenes[0].flow_prompt_en = (
        "A Caucasian man is unfolding the beige TrailTop chair on the grass."
    )
    raw.scenes[1].flow_prompt_en = (
        "Medium shot as the creator stands beside the chair and talent points at the seat."
    )
    raw.scenes[2].flow_prompt_en = (
        "Wide shot next to the folded chair on the lawn."
    )

    enforced = enforce_commercial_mechanisms(
        raw,
        is_faceless=False,
        platform_mode=PlatformMode.SHOPEE,
        profile=avatar_prof,
    )
    # Re-applying (as happens during regenerate_hook) must stay clean & idempotent
    enforced_twice = enforce_commercial_mechanisms(
        enforced,
        is_faceless=False,
        platform_mode=PlatformMode.SHOPEE,
        profile=avatar_prof,
    )

    assert enforced_twice == enforced

    for s in enforced_twice.scenes:
        p = s.flow_prompt_en
        low = p.lower()
        # 1. Zero meta-brackets and zero quotation marks
        assert "[" not in p and "]" not in p
        assert '"' not in p
        # 2. Zero Veo Pink-Elephant negative triggers
        for forbidden in ("do not", "don't", "caucasian", "western", "european", "background music", "spoken dialogue"):
            assert forbidden not in low
        # 3. Exact product geometry & positive static lock in EVERY scene
        assert "tan-painted cross-brace tubular legs" in p
        assert "locked static geometry" in low
        # 4. Folding / unfolding deformations are sanitized out
        assert "unfolding" not in low
        assert "folded" not in low
        # 5. Google Flow @me Avatar + Positive Native Indonesian identity
        assert " @me " in p
        assert "(@me)" not in p
        assert "authentic native indonesian man" in low
        # 6. Scene Builder kinematics & Positive Audio Cue
        assert "quiet natural ambient soundscape" in low
        assert "silent presenter" in low
        if s.flow_action == "Extend":
            assert p.startswith("Seamless continuation from the previous frame,")

    assert "@me stands beside" in enforced_twice.scenes[1].flow_prompt_en
    assert "@me points at" in enforced_twice.scenes[1].flow_prompt_en

    # 2. Tag with extra traits: "@me, berkacamata, kaos hitam"
    traits_prof = TalentSavedProfile(
        talent_presence=TalentPresence.AVATAR_MALE_ID,
        avatar_flow_tag="@me, berkacamata, kaos hitam",
    )
    raw_traits = build_offline_demo_blueprint(traits_prof, scene_count=3)
    enforced_traits = enforce_commercial_mechanisms(
        raw_traits,
        is_faceless=False,
        platform_mode=PlatformMode.SHOPEE,
        profile=traits_prof,
    )
    for s in enforced_traits.scenes:
        p = s.flow_prompt_en
        assert " @me " in p
        assert "(@me)" not in p
        assert "berkacamata, kaos hitam" in p


def test_enforces_visual_bible_specific_flow_actions_and_platform_terms():
    assert "DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT

    raw = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=5)
    raw.scenes[0].flow_action = "WrongAction"
    raw.scenes[1].flow_action = "Extend / Jump to"
    raw.scenes[1].flow_prompt_en = '[Visual Bible: Studio] Continuous push-in on "bottle" with no background music.'
    raw.scenes[2].flow_action = "Extend / Jump to"
    raw.scenes[2].flow_prompt_en = "Macro close-up droplet dispensing onto hand."
    raw.scenes[4].vo_script_id = "Mumpung promo masih ada, langsung klik Keranjang Kuning sebelum kehabisan stok!"

    enforced = enforce_commercial_mechanisms(
        raw,
        is_faceless=True,
        platform_mode=PlatformMode.SHOPEE,
    )
    assert enforced.scenes[0].flow_action == "New Scene"
    assert enforced.scenes[1].flow_action == "Extend"
    assert enforced.scenes[1].flow_prompt_en.startswith("Seamless continuation from the previous frame,")
    assert enforced.scenes[2].flow_action == "Jump to"
    assert "Keranjang Oranye" in enforced.scenes[4].vo_script_id

    for s in enforced.scenes:
        low = s.flow_prompt_en.lower()
        assert "9:16" in low
        assert "[" not in s.flow_prompt_en and "]" not in s.flow_prompt_en
        assert '"' not in s.flow_prompt_en
        assert "background music" not in low
        assert "quiet natural ambient soundscape" in low
        assert "silent presenter" in low
        wc = count_words(s.vo_script_id)
        assert 10 <= wc <= 18


def test_srt_builder_and_persistent_hook_history(tmp_path: Path):
    bp = enforce_commercial_mechanisms(build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3))
    srt_text = build_srt_from_blueprint(bp, max_words_per_cue=4)
    assert "00:00:00,000 -->" in srt_text
    assert "1\n" in srt_text

    proj_dir = tmp_path / "projects"
    hooks1 = append_product_hook("TrailTop Kursi Lipat Outdoor 150kg", "Hook pertama unik", proj_dir)
    hooks2 = append_product_hook("TrailTop Kursi Lipat Outdoor Promo", "Hook kedua berbeda", proj_dir)
    assert len(hooks1) == 1
    assert len(hooks2) == 2
    loaded = load_product_hooks("TrailTop Kursi Lipat Outdoor", proj_dir)
    assert "Hook pertama unik" in loaded and "Hook kedua berbeda" in loaded
    assert list_saved_blueprints(proj_dir) == []


def test_regenerate_hook_changes_scene_1_and_updates_full_vo():
    bp = enforce_commercial_mechanisms(
        build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3, variation_index=0)
    )
    old_hook = bp.scenes[0].vo_script_id
    regen_payload = build_offline_demo_regenerated_hook(bp, variation_index=1)
    updated = apply_regenerated_hook(bp, regen_payload, is_faceless=True)

    assert updated.scenes[0].vo_script_id != old_hook
    assert updated.scenes[0].flow_action == "New Scene"
    assert updated.scenes[0].vo_script_id in updated.capcut_finishing.full_vo_script_id
    assert old_hook not in updated.capcut_finishing.full_vo_script_id
