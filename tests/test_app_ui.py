"""Headless UI behavior tests using st.testing.v1.AppTest (Mobile-First + Cloud PIN Gate + Deep Review)."""

import io
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_has_only_product_uploader_and_supports_deep_7_scene_product_knowledge(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APP_PIN", raising=False)
    at = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not at.exception

    # Strictly 2 uploaders initially (product image + persistent avatar photo; grid splitter appears after generation)
    assert len(at.file_uploader) == 2
    assert at.get_by_key("device_mode_select").value == "laptop"
    assert at.get_by_key("workflow_mode_select").value == "storyboard_first"
    assert at.toggle(key="toggle_native_voice_default").value is True

    # Switching between Laptop & Mobile layout modes works cleanly without widget collisions
    at.get_by_key("device_mode_select").set_value("mobile").run()
    assert not at.exception
    at.get_by_key("device_mode_select").set_value("laptop").run()
    assert not at.exception

    at.selectbox(key="engine_mode").select("offline_demo").run()
    assert not at.exception

    # Default avatar tag is Google Flow's native @me mention
    assert at.text_input(key="input_avatar_flow_tag").value == "@me"

    tall_img = io.BytesIO()
    Image.new("RGB", (540, 1200), (235, 225, 215)).save(tall_img, format="PNG")
    avatar_img = io.BytesIO()
    Image.new("RGB", (300, 400), (200, 170, 140)).save(avatar_img, format="PNG")

    at.file_uploader(key="product_uploader").upload("shopee_screen.png", tall_img.getvalue()).run()
    at.file_uploader(key="avatar_photo_uploader").upload("avatar_saya.png", avatar_img.getvalue()).run()
    assert (tmp_path / "profile" / "avatar_photo.jpg").is_file()

    at.text_area(key="input_raw_specs").set_value("5% Niacinamide + Ceramide NP, pH 5.5 water-based").run()

    at.button(key="btn_generate_blueprint").click().run()
    assert not at.exception

    record_3 = at.session_state["record"]
    assert record_3 is not None
    # Default clip duration is 15s full script (no looping)
    assert at.get_by_key("clip_duration_select").value == "15s"
    rendered_codes = [c.value for c in at.code]
    assert any(
        "15-second" in code
        and "no looping" in code
        and all(sc.vo_script_id in code for sc in record_3.blueprint.scenes[:3])
        for code in rendered_codes
    )

    # Switching clip duration to 8s shows single-scene talking prompt
    at.get_by_key("clip_duration_select").set_value("8s").run()
    assert not at.exception
    rendered_8s = [c.value for c in at.code]
    voice_prompt = record_3.blueprint.scenes[0].flow_voice_prompt_en
    assert voice_prompt in rendered_8s
    assert record_3.blueprint.scenes[0].vo_script_id in voice_prompt
    assert "@ProductAuthority" in voice_prompt and " @me " in voice_prompt
    assert "indonesian voice" in voice_prompt.lower()
    assert record_3.workflow_mode.value == "storyboard_first"
    assert record_3.blueprint.flow_setup.storyboard_grid_layout == "2x2"
    assert "@ProductAuthority" in record_3.blueprint.flow_setup.storyboard_grid_prompt_en
    assert len(record_3.blueprint.scenes) == 3
    for sc in record_3.blueprint.scenes:
        assert "@ProductAuthority" in sc.keyframe_image_prompt_en
        assert " @me " in sc.keyframe_image_prompt_en
        assert len(sc.keyframe_image_prompt_en.split()) <= 35
        p = sc.flow_prompt_en
        low = p.lower()
        assert "[" not in p and "]" not in p
        assert '"' not in p
        assert "@ProductAuthority" in p
        assert " @me " in p
        assert "(@me)" not in p
        assert "indonesian" in low
        assert "No text overlays, no additional logos, no readable screens." in p
        assert len(p.split()) <= 35
        if sc.flow_action == "Extend":
            assert p.startswith("Seamless continuation from the previous frame,")
    assert len(record_3.blueprint.product_knowledge.technical_specs_and_materials) >= 3
    assert "📌" in record_3.blueprint.product_knowledge.pinned_comment_faq_id
    assert "Deskripsi/Spesifikasi Toko" in record_3.knowledge_sources
    assert Path(record_3.cropped_ingredient_path).is_file()
    assert Path(at.session_state["artifacts"]["capcut_srt"]).is_file()

    # Regenerate Hook
    first_hook_vo = record_3.blueprint.scenes[0].vo_script_id
    at.button(key="btn_regenerate_hook").click().run()
    assert not at.exception
    assert at.session_state["record"].blueprint.scenes[0].vo_script_id != first_hook_vo

    # Test 40-45 detik (7 scene deep review) + TikTok Shop CTA
    at.get_by_key("duration_preset").set_value("40-45 detik (7 scene deep)").run()
    at.get_by_key("platform_mode_select").set_value("tiktok").run()
    at.button(key="btn_generate_blueprint").click().run()
    assert not at.exception

    record_7 = at.session_state["record"]
    assert len(record_7.blueprint.scenes) == 7
    roles = [s.role for s in record_7.blueprint.scenes]
    assert "Bedah Spek" in roles
    assert "Objection Killer" in roles
    assert "keranjang kuning" in record_7.blueprint.scenes[-1].vo_script_id.lower()


def test_cloud_pin_gate_blocks_until_correct_pin(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_PIN", "998877")

    at = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not at.exception
    # Main uploader must NOT render while locked behind PIN
    assert len(at.file_uploader) == 0

    # Wrong PIN shows error and keeps app locked
    at.text_input(key="input_app_pin").set_value("000000").run()
    at.button(key="btn_unlock_pin").click().run()
    assert len(at.error) == 1
    assert len(at.file_uploader) == 0

    # Correct PIN unlocks main app
    at.text_input(key="input_app_pin").set_value("998877").run()
    at.button(key="btn_unlock_pin").click().run()
    assert not at.exception
    assert len(at.file_uploader) == 2
