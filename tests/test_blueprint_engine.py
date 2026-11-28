"""Tests for Commercial-Grade Mechanisms, Lightweight Presets, Screenshot Cropper, SRT, & History."""

import io
from pathlib import Path

from PIL import Image

from src.blueprint_engine import (
    apply_regenerated_hook,
    compose_full_15s_flow_prompt,
    count_words,
    detect_flow_prompt_hallucination_risks,
    enforce_commercial_mechanisms,
)
from src.history_store import append_product_hook, list_saved_blueprints, load_product_hooks
from src.image_prep import (
    build_frames_zip,
    build_product_turnaround_sheet,
    is_mobile_screenshot,
    parse_grid_layout,
    prepare_clean_product_ingredient,
    save_product_authority_image,
    split_storyboard_grid,
)
from src.prompts import (
    COMMERCIAL_DIRECTOR_SYSTEM_PROMPT,
    build_offline_demo_blueprint,
    build_offline_demo_regenerated_hook,
)
from src.schemas import PersonaStyle, PlatformMode, TalentPresence, TalentSavedProfile
from src.srt_export import build_srt_from_blueprint
from src.talent_store import (
    delete_avatar_photo,
    get_saved_avatar_photo_path,
    load_preset_collection,
    load_talent_profile,
    save_avatar_photo,
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
    # 1. Default @me avatar mention + bloated 90-word hallucination-prone prompt condensed cleanly
    avatar_prof = TalentSavedProfile(
        talent_presence=TalentPresence.AVATAR_MALE_ID,
        avatar_flow_tag="",
        visual_notes="Kaos polos hitam rapi",
    )
    raw = build_offline_demo_blueprint(avatar_prof, scene_count=3)
    raw.scenes[0].flow_prompt_en = (
        "A Caucasian man walks toward the table, picks up a red bottle with a black cap, "
        "opens the door and is unfolding the beige TrailTop chair on the bright green grass while "
        "smiling broadly into the camera in dramatic cinematic lighting with many intricate details "
        "and long background explanations that exceed thirty words easily."
    )
    # Even a SHORT prompt (<26 words) that re-describes physical attributes or uses narrative verbs MUST be auto-condensed!
    raw.scenes[1].flow_prompt_en = (
        "Use @ProductAuthority red bottle with black cap and printed logo as @me Indonesian male presenter in morning light."
    )
    raw.scenes[2].flow_prompt_en = (
        "Wide pull-back shot as @me sits down on beige chair with tan legs."
    )

    enforced = enforce_commercial_mechanisms(
        raw,
        is_faceless=False,
        platform_mode=PlatformMode.SHOPEE,
        profile=avatar_prof,
    )
    # Re-applying (as happens during regenerate_hook) must stay clean & identical
    enforced_twice = enforce_commercial_mechanisms(
        enforced,
        is_faceless=False,
        platform_mode=PlatformMode.SHOPEE,
        profile=avatar_prof,
    )

    assert enforced_twice == enforced

    # Start-to-End Frame & Storyboard Grid prompts use @ProductAuthority & concise constraints
    s2e = enforced_twice.flow_setup.start_to_end_prompt_en
    assert "@ProductAuthority" in s2e
    assert "No text overlays, no additional logos, no readable screens." in s2e
    assert count_words(s2e) <= 35
    assert detect_flow_prompt_hallucination_risks(s2e) == []

    assert enforced_twice.flow_setup.storyboard_grid_layout == "2x2"
    grid_p = enforced_twice.flow_setup.storyboard_grid_prompt_en
    assert "2x2" in grid_p
    assert "@ProductAuthority" in grid_p
    assert " @me " in grid_p
    assert "No text overlays, no additional logos, no readable screens." in grid_p

    for s in enforced_twice.scenes:
        kp = s.keyframe_image_prompt_en
        assert "@ProductAuthority" in kp
        assert " @me " in kp
        assert "(@me)" not in kp
        assert "No text overlays, no additional logos, no readable screens." in kp
        assert count_words(kp) <= 35
        assert detect_flow_prompt_hallucination_risks(kp) == []

        p = s.flow_prompt_en
        low = p.lower()
        # 1. Strict SKILL.md word budget enforced (<= 35 words)
        assert count_words(p) <= 35
        # 2. Zero SKILL.md anti-patterns (no product re-description, no narrative/deformation verbs)
        assert detect_flow_prompt_hallucination_risks(p) == []
        # 3. Zero meta-brackets and zero quotation marks
        assert "[" not in p and "]" not in p
        assert '"' not in p
        # 4. @ProductAuthority & standalone Indonesian @me tagged cleanly
        assert "@ProductAuthority" in p
        assert " @me " in p
        assert "(@me)" not in p
        assert "indonesian" in low
        assert "caucasian" not in low
        # 5. Forbidden narrative, deformation & physical re-description terms absent
        for bad in ("walks toward", "picks up", "opens the door", "unfolding", "red bottle", "black cap", "printed logo", "tan legs"):
            assert bad not in low
        # 6. Explicit anti-artifact negative constraint present
        assert "No text overlays, no additional logos, no readable screens." in p
        # 7. Extend scenes start cleanly from previous frame
        if s.flow_action == "Extend":
            assert p.startswith("Seamless continuation from the previous frame,")

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
    assert enforce_commercial_mechanisms(
        enforced_traits, is_faceless=False, platform_mode=PlatformMode.SHOPEE, profile=traits_prof
    ) == enforced_traits
    for s in enforced_traits.scenes:
        p = s.flow_prompt_en
        assert "@ProductAuthority" in p
        assert " @me " in p
        assert "(@me)" not in p
        assert "berkacamata, kaos hitam" in p
        assert count_words(p) <= 35
        assert detect_flow_prompt_hallucination_risks(p) == []


def test_enforces_visual_bible_specific_flow_actions_and_platform_terms():
    assert "DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT

    raw = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=5)
    raw.scenes[0].flow_action = "WrongAction"
    raw.scenes[1].flow_action = "Extend / Jump to"
    raw.scenes[1].flow_prompt_en = '[Visual Bible: Studio] Slow push-in shot with @ProductAuthority.'
    raw.scenes[2].flow_action = "Extend / Jump to"
    raw.scenes[2].flow_prompt_en = "Macro close-up shot focusing on material."
    raw.scenes[4].vo_script_id = "Mumpung promo masih ada, langsung klik Keranjang Kuning sebelum kehabisan stok!"

    enforced = enforce_commercial_mechanisms(
        raw,
        is_faceless=True,
        platform_mode=PlatformMode.SHOPEE,
    )
    assert enforced.flow_setup.aspect_ratio == "9:16"
    assert enforced.scenes[0].flow_action == "New Scene"
    assert enforced.scenes[1].flow_action == "Extend"
    assert enforced.scenes[1].flow_prompt_en.startswith("Seamless continuation from the previous frame,")
    assert enforced.scenes[2].flow_action == "Jump to"
    assert "Keranjang Oranye" in enforced.scenes[4].vo_script_id

    for s in enforced.scenes:
        assert "@ProductAuthority" in s.flow_prompt_en
        assert count_words(s.flow_prompt_en) <= 35
        assert detect_flow_prompt_hallucination_risks(s.flow_prompt_en) == []
        assert "[" not in s.flow_prompt_en and "]" not in s.flow_prompt_en
        assert '"' not in s.flow_prompt_en
        assert "No text overlays, no additional logos, no readable screens." in s.flow_prompt_en
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


def test_split_storyboard_grid_and_zip_export():
    import zipfile

    assert parse_grid_layout("3x2") == (3, 2)
    assert parse_grid_layout("invalid") == (2, 2)

    # Create a 400x400 2x2 grid image with distinct colored quadrants
    grid_img = Image.new("RGB", (400, 400))
    colors = [
        ((220, 40, 40), (0, 0, 200, 200)),     # Top-left: Red
        ((40, 200, 40), (200, 0, 400, 200)),   # Top-right: Green
        ((40, 40, 220), (0, 200, 200, 400)),   # Bottom-left: Blue
        ((220, 200, 40), (200, 200, 400, 400)), # Bottom-right: Yellow
    ]
    for col, box in colors:
        grid_img.paste(Image.new("RGB", (200, 200), col), box[:2])

    buf = io.BytesIO()
    grid_img.save(buf, format="PNG")
    frames = split_storyboard_grid(buf.getvalue(), cols=2, rows=2, trim_margin_pct=0.02)
    assert len(frames) == 4

    # Check center pixel dominant channel matches reading order (R, G, B)
    centers = []
    for f_bytes in frames:
        with Image.open(io.BytesIO(f_bytes)) as im:
            centers.append(im.getpixel((im.width // 2, im.height // 2)))
    assert centers[0][0] > 180 and centers[0][1] < 80  # Red
    assert centers[1][1] > 170 and centers[1][0] < 80  # Green
    assert centers[2][2] > 180 and centers[2][0] < 80  # Blue

    zip_bytes = build_frames_zip(frames, prefix="keyframe")
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        assert zf.namelist() == [
            "keyframe_1.jpg",
            "keyframe_2.jpg",
            "keyframe_3.jpg",
            "keyframe_4.jpg",
        ]


def test_ugc_director_prompt_studio_skill_and_system_prompt():
    import re

    skill_root = Path(".agents/skills/ugc-director-prompt-studio")
    skill_md = skill_root / "SKILL.md"
    assert skill_md.exists()
    skill_text = skill_md.read_text(encoding="utf-8")
    assert skill_text.startswith("---\nname: ugc-director-prompt-studio\ndescription:")

    ref_files = [
        skill_root / "references/hook-and-script-frameworks.md",
        skill_root / "references/cinematography-and-prompt-templates.md",
        skill_root / "references/qc-and-compliance-checklist.md",
    ]
    for ref in ref_files:
        assert ref.exists() and len(ref.read_text(encoding="utf-8").strip()) > 200

    # Verify every sample Veo 3.1 motion prompt under Section 4 enforces <= 35 words & zero anti-halu triggers
    templates_text = ref_files[1].read_text(encoding="utf-8")
    veo_section = templates_text.split("## 4. Google Flow (Veo 3.1) Motion Prompts")[1]
    veo_blocks = re.findall(r"```text\n(.*?)\n```", veo_section, flags=re.DOTALL)
    assert len(veo_blocks) == 6
    for prompt in veo_blocks:
        clean_prompt = prompt.strip()
        assert count_words(clean_prompt) <= 35, clean_prompt
        assert detect_flow_prompt_hallucination_risks(clean_prompt) == [], clean_prompt
        assert "@ProductAuthority" in clean_prompt
        assert "[" not in clean_prompt and "]" not in clean_prompt and '"' not in clean_prompt
        assert clean_prompt.endswith("No text overlays, no additional logos, no readable screens.")

    assert "Senior AI Video Director" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT
    assert "UGC Creator" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT
    assert "Scriptwriter Specialist" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT
    assert "Before vs After" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT
    assert "Painful" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT
    assert "Before vs After" in skill_text and "Painful" in skill_text
    frameworks_text = ref_files[0].read_text(encoding="utf-8")
    assert "Before vs After" in frameworks_text and "Painful" in frameworks_text
    assert "DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak" in COMMERCIAL_DIRECTOR_SYSTEM_PROMPT


def test_avatar_photo_persistence_and_talking_voice_prompt(tmp_path: Path):
    prof_dir = tmp_path / "profile"
    assert get_saved_avatar_photo_path(prof_dir) is None

    png_buf = io.BytesIO()
    Image.new("RGB", (320, 480), (210, 180, 150)).save(png_buf, format="PNG")
    saved_path = save_avatar_photo(png_buf.getvalue(), prof_dir)
    assert saved_path.is_file()
    assert get_saved_avatar_photo_path(prof_dir) == saved_path

    prof = TalentSavedProfile()
    bp = enforce_commercial_mechanisms(
        build_offline_demo_blueprint(prof, scene_count=3, variation_index=0),
        is_faceless=False,
        profile=prof,
    )
    for sc in bp.scenes:
        vp = sc.flow_voice_prompt_en
        assert "@ProductAuthority" in vp
        assert " @me " in vp
        assert "indonesian voice" in vp.lower()
        assert sc.vo_script_id in vp
        assert "[" not in vp and "]" not in vp and '"' not in vp
        assert vp.endswith("No text overlays, no additional logos, no readable screens.")

    regen_payload = build_offline_demo_regenerated_hook(bp, variation_index=2)
    updated = apply_regenerated_hook(bp, regen_payload, is_faceless=False, profile=prof)
    assert updated.scenes[0].vo_script_id in updated.scenes[0].flow_voice_prompt_en

    full_15s = compose_full_15s_flow_prompt(bp, profile=prof, include_voice=True)
    assert "15-second" in full_15s and "no looping" in full_15s
    assert "@ProductAuthority" in full_15s and " @me " in full_15s
    assert "indonesian voice" in full_15s.lower()
    assert all(sc.vo_script_id in full_15s for sc in bp.scenes[:3])
    assert "[" not in full_15s and "]" not in full_15s and '"' not in full_15s

    delete_avatar_photo(prof_dir)
    assert get_saved_avatar_photo_path(prof_dir) is None


def test_auto_product_turnaround_sheet_multi_angles(tmp_path: Path):
    def _make_angle(rgb_color: tuple[int, int, int], size: tuple[int, int] = (400, 500)) -> bytes:
        b = io.BytesIO()
        Image.new("RGB", size, rgb_color).save(b, format="PNG")
        return b.getvalue()

    # 1 image -> single clean portrait JPEG
    one_bytes, _ = build_product_turnaround_sheet([_make_angle((200, 80, 80))])
    with Image.open(io.BytesIO(one_bytes)) as im1:
        assert im1.height > im1.width

    # 2 images -> 2x1 horizontal Turnaround Sheet
    two_bytes, _ = build_product_turnaround_sheet(
        [_make_angle((200, 80, 80)), _make_angle((80, 200, 80))]
    )
    with Image.open(io.BytesIO(two_bytes)) as im2:
        assert im2.width > im2.height
        assert im2.getpixel((5, 5))[0] > 235  # Neutral light-gray background

    # 3 images -> 3x1 wide Turnaround Sheet
    three_bytes, _ = build_product_turnaround_sheet(
        [_make_angle((200, 80, 80)), _make_angle((80, 200, 80)), _make_angle((80, 80, 200))]
    )
    with Image.open(io.BytesIO(three_bytes)) as im3:
        assert im3.width >= 2.5 * im3.height

    # 4 images -> 2x2 square Turnaround Sheet saved to disk
    saved_path, _ = save_product_authority_image(
        [
            _make_angle((200, 80, 80)),
            _make_angle((80, 200, 80)),
            _make_angle((80, 80, 200)),
            _make_angle((200, 200, 80)),
        ],
        output_dir=tmp_path / "input",
    )
    assert saved_path.is_file()
    with Image.open(saved_path) as im4:
        assert im4.width == im4.height



