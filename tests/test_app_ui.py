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

    # Strictly 1 file uploader (product image only)
    assert len(at.file_uploader) == 1

    at.selectbox(key="engine_mode").select("offline_demo").run()
    assert not at.exception

    # Default avatar tag is Google Flow's native @me mention
    assert at.text_input(key="input_avatar_flow_tag").value == "@me"

    tall_img = io.BytesIO()
    Image.new("RGB", (540, 1200), (235, 225, 215)).save(tall_img, format="PNG")
    at.file_uploader(key="product_uploader").upload("shopee_screen.png", tall_img.getvalue()).run()
    at.text_area(key="input_raw_specs").set_value("5% Niacinamide + Ceramide NP, pH 5.5 water-based").run()

    at.button(key="btn_generate_blueprint").click().run()
    assert not at.exception

    record_3 = at.session_state["record"]
    assert record_3 is not None
    assert len(record_3.blueprint.scenes) == 3
    for sc in record_3.blueprint.scenes:
        p = sc.flow_prompt_en
        low = p.lower()
        assert "[" not in p and "]" not in p
        assert '"' not in p
        assert " @me " in p
        assert "(@me)" not in p
        assert "authentic native indonesian" in low
        assert "locked static geometry" in low
        assert "caucasian" not in low and "western" not in low
        assert "quiet natural ambient soundscape" in low
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
    assert len(at.file_uploader) == 1
