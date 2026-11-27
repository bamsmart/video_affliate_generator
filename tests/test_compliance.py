"""Tests for Shopee Video & TikTok Shop compliance policy gate & platform normalizers."""

from src.compliance import (
    audit_blueprint,
    audit_text,
    normalize_hashtags_in_caption,
    normalize_platform_terms,
    sanitize_blueprint,
    sanitize_text,
)
from src.prompts import build_offline_demo_blueprint
from src.schemas import PlatformMode, TalentSavedProfile


def test_detects_medical_pricing_and_offplatform_claims():
    bad_text = (
        "Serum ini 100% ampuh menyembuhkan jerawat dan putih dalam 3 hari! "
        "Harga termurah se-Indonesia, beli di WA sekarang ya!"
    )
    report = audit_text(bad_text, is_sensitive_category=True)
    assert report.status == "BLOCKED"
    categories = {issue.category for issue in report.issues}
    assert "medical_absolute" in categories
    assert "deceptive_pricing" in categories
    assert "off_platform_redirect" in categories


def test_sanitize_text_converts_to_safe():
    bad_text = "Produk ini menyembuhkan kulit kusam dan termurah se-Indonesia, wajib beli!"
    rewritten, issues = sanitize_text(bad_text)
    assert len(issues) >= 2
    after_report = audit_text(rewritten)
    assert after_report.status == "SAFE"
    assert "membantu merawat" in rewritten.lower()


def test_platform_terms_and_hashtag_normalizers():
    leaked = "Yuk langsung cek Keranjang Kuning sekarang sebelum habis!"
    assert "Keranjang Oranye" in normalize_platform_terms(leaked, PlatformMode.SHOPEE)
    assert "keranjang di bawah" in normalize_platform_terms(leaked, PlatformMode.BOTH)

    dirty_cap = "Kursi outdoor kokoh! #TrailTop #kursi lipat #camping gear"
    clean_cap = normalize_hashtags_in_caption(dirty_cap)
    assert "#kursilipat" in clean_cap
    assert "#campinggear" in clean_cap


def test_offline_demo_blueprint_passes_compliance():
    bp = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3)
    rep = audit_blueprint(bp)
    assert rep.status == "SAFE"


def test_sanitize_blueprint_cleans_scenes_and_captions():
    bp = build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3)
    bp.scenes[0].vo_script_id = "Dijamin menyembuhkan masalah kulit dan 100% ampuh!"
    bp.capcut_finishing.shopee_caption_and_hashtags = "Termurah se-Indonesia beli di WA sekarang #kursi lipat"
    assert audit_blueprint(bp).status == "BLOCKED"

    clean_bp = sanitize_blueprint(bp)
    assert audit_blueprint(clean_bp).status == "SAFE"
    assert clean_bp.scenes[0].vo_script_id in clean_bp.capcut_finishing.full_vo_script_id
    assert "#kursilipat" in clean_bp.capcut_finishing.shopee_caption_and_hashtags
