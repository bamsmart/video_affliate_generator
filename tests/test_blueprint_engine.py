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
    assert load_talent_profile(prof_dir).is_faceless is True  # Default is Fokus Produk / B-Roll

    prof = TalentSavedProfile(
        preset_id="hijab_preset",
        talent_name="Hijab Antusias",
        talent_presence=TalentPresence.FEMALE_HIJAB,
        persona=PersonaStyle.ANTUSIAS,
        visual_notes="Pashmina krem kasual",
    )
    save_talent_profile(prof, prof_dir)
    active = load_talent_profile(prof_dir)
    assert active.talent_name == "Hijab Antusias"
    assert active.is_faceless is False

    switched = set_active_preset("broll_produk", prof_dir)
    assert switched.is_faceless is True

    # Legacy dict with is_faceless=True migrates cleanly without photo_paths
    migrated = TalentSavedProfile.model_validate({"talent_name": "Old", "is_faceless": True})
    assert migrated.talent_presence == TalentPresence.FACELESS_BROLL


def test_smart_shopee_screenshot_cropper():
    tall_buf = io.BytesIO()
    Image.new("RGB", (540, 1200), (240, 240, 240)).save(tall_buf, format="PNG")
    assert is_mobile_screenshot(tall_buf.getvalue()) is True
    cropped_bytes, was_cropped = prepare_clean_product_ingredient(tall_buf.getvalue())
    assert was_cropped is True
    with Image.open(io.BytesIO(cropped_bytes)) as out_im:
        assert out_im.height < 1200

    sq_buf = io.BytesIO()
    Image.new("RGB", (800, 800), (200, 210, 220)).save(sq_buf, format="PNG")
    assert is_mobile_screenshot(sq_buf.getvalue()) is False
    _, sq_cropped = prepare_clean_product_ingredient(sq_buf.getvalue())
    assert sq_cropped is False


def test_enforces_visual_bible_specific_flow_actions_and_platform_terms():
    assert "DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT

    raw = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=5)
    raw.scenes[0].flow_action = "WrongAction"
    raw.scenes[1].flow_action = "Extend / Jump to"
    raw.scenes[1].flow_prompt_en = "Continuous push-in on hand holding bottle."
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
    assert enforced.scenes[2].flow_action == "Jump to"
    assert "Keranjang Oranye" in enforced.scenes[4].vo_script_id

    bible_prefix = enforced.flow_setup.locked_visual_bible_en[:40]
    for s in enforced.scenes:
        assert bible_prefix in s.flow_prompt_en
        assert "no background music" in s.flow_prompt_en.lower()
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
