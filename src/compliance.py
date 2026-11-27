"""Shopee Video & TikTok Shop Indonesia Compliance Policy Gate & Platform Normalizer."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas import BlueprintResponse, PlatformMode


class ComplianceIssue(BaseModel):
    category: str
    severity: Literal["WARNING", "BLOCKED"]
    matched_phrase: str
    field_name: str = "text"
    suggestion: str


class ComplianceReport(BaseModel):
    status: Literal["SAFE", "WARNING", "BLOCKED"]
    issues: list[ComplianceIssue] = Field(default_factory=list)
    rewritten_text: str = ""


BANNED_RULES: list[tuple[str, Literal["WARNING", "BLOCKED"], str, str]] = [
    (
        "medical_absolute",
        "BLOCKED",
        r"\bmenyembuhkan\b",
        "Ganti dengan klaim lembut seperti 'membantu merawat'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bmengobati\b",
        "Ganti dengan 'membantu menjaga kondisi'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bsembuh\s+total\b",
        "Hindari janji kesembuhan mutlak; gunakan 'terasa lebih nyaman'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bmencegah\s+penyakit\b",
        "Ganti dengan 'mendukung perawatan harian'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\b100%\s*ampuh\b",
        "Ganti dengan 'banyak disukai pengguna'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bhilang\s+permanen\b",
        "Ganti dengan 'tampak lebih terawat'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bputih\s+dalam\s+\d+\s*(hari|menit|detik|jam)\b",
        "Ganti dengan 'kulit tampak lebih cerah terawat dengan pemakaian rutin'.",
    ),
    (
        "medical_absolute",
        "BLOCKED",
        r"\bgaransi\s+100%\b",
        "Hindari jaminan 100%; sebutkan sesuai deskripsi resmi toko.",
    ),
    (
        "medical_absolute",
        "WARNING",
        r"\bteruji\s+klinis\b",
        "Pastikan klaim 'teruji klinis' benar-benar tercantum di kemasan/izin edar resmi.",
    ),
    (
        "deceptive_pricing",
        "BLOCKED",
        r"\btermurah\s+se-?indonesia\b",
        "Ganti dengan 'harga lagi promo menarik'.",
    ),
    (
        "deceptive_pricing",
        "WARNING",
        r"\bharga\s+pabrik\b",
        "Gunakan 'harga spesial promo' kecuali memang official store pabrikan.",
    ),
    (
        "deceptive_pricing",
        "BLOCKED",
        r"\bpasti\s+gratis\b",
        "Jelaskan syarat promo secara jujur atau gunakan 'cek voucher gratis ongkir'.",
    ),
    (
        "deceptive_pricing",
        "WARNING",
        r"\bwajib\s+beli\b",
        "Ganti dengan ajakan natural seperti 'patut banget dicoba'.",
    ),
    (
        "off_platform_redirect",
        "BLOCKED",
        r"\bbeli\s+(di|via|lewat)\s+(wa|whatsapp|dm|ig|instagram)\b",
        "Arahkan checkout lewat Keranjang / Tautan Produk resmi.",
    ),
    (
        "off_platform_redirect",
        "BLOCKED",
        r"\bhubungi\s+wa\b",
        "Dilarang mengarahkan transaksi ke luar platform; arahkan ke Keranjang.",
    ),
    (
        "off_platform_redirect",
        "BLOCKED",
        r"\bklik\s+link\s+bio\s+wa\b",
        "Gunakan CTA Tautan Produk di video.",
    ),
    (
        "off_platform_redirect",
        "BLOCKED",
        r"\btransfer\s+langsung\b",
        "Transaksi affiliate wajib di dalam aplikasi resmi.",
    ),
    (
        "fictional_crisis_manipulation",
        "BLOCKED",
        r"\bkasihan\s+banget\s+toko\s+ini\s+mau\s+bangkrut\b",
        "Platform melarang narasi krisis fiktif untuk memancing pembelian.",
    ),
    (
        "fictional_crisis_manipulation",
        "BLOCKED",
        r"\btolong\s+bantu\s+beli\s+biar\s+tidak\s+tutup\b",
        "Fokus pada manfaat nyata produk, bukan cerita krisis buatan.",
    ),
]


SAFE_REWRITES: list[tuple[str, str]] = [
    (r"\bmenyembuhkan\b", "membantu merawat"),
    (r"\bmengobati\b", "membantu menjaga"),
    (r"\bsembuh\s+total\b", "terasa lebih nyaman"),
    (r"\bmencegah\s+penyakit\b", "mendukung perawatan harian"),
    (r"\b100%\s*ampuh\b", "banyak disukai pengguna"),
    (r"\bhilang\s+permanen\b", "tampak lebih terawat"),
    (r"\bputih\s+dalam\s+\d+\s*(hari|menit|detik|jam)\b", "tampak lebih cerah terawat"),
    (r"\bgaransi\s+100%\b", "kualitas terjamin sesuai deskripsi toko"),
    (r"\bteruji\s+klinis\b", "diformulasikan khusus"),
    (r"\btermurah\s+se-?indonesia\b", "harga lagi promo menarik"),
    (r"\bharga\s+pabrik\b", "harga promo spesial"),
    (r"\bpasti\s+gratis\b", "bisa pakai voucher gratis ongkir"),
    (r"\bwajib\s+beli\b", "patut banget dicoba"),
    (r"\bbeli\s+(di|via|lewat)\s+(wa|whatsapp|dm|ig|instagram)\b", "cek di Keranjang"),
    (r"\bhubungi\s+wa\b", "cek Keranjang"),
    (r"\bklik\s+link\s+bio\s+wa\b", "klik Tautan Produk di bawah"),
    (r"\btransfer\s+langsung\b", "checkout langsung di keranjang"),
    (r"\bkasihan\s+banget\s+toko\s+ini\s+mau\s+bangkrut\b", "produk ini lagi banyak dicari"),
    (r"\btolong\s+bantu\s+beli\s+biar\s+tidak\s+tutup\b", "langsung cek detail produknya di keranjang"),
]


def normalize_platform_terms(text: str, platform_mode: PlatformMode = PlatformMode.SHOPEE) -> str:
    """Prevent TikTok 'Keranjang Kuning' bleeding into Shopee scripts and vice versa."""
    if not text:
        return text
    if platform_mode == PlatformMode.SHOPEE:
        return re.sub(r"\bkeranjang\s+kuning\b", "Keranjang Oranye", text, flags=re.IGNORECASE)
    if platform_mode == PlatformMode.TIKTOK:
        return re.sub(r"\bkeranjang\s+oranye\b", "Keranjang Kuning", text, flags=re.IGNORECASE)
    # BOTH: use platform-neutral 'keranjang di bawah' inside shared VO
    return re.sub(
        r"\bkeranjang\s+(kuning|oranye)\b",
        "keranjang di bawah",
        text,
        flags=re.IGNORECASE,
    )


def normalize_hashtags_in_caption(caption: str) -> str:
    """Ensure hashtags have no spaces inside tags (e.g. '#kursi lipat' -> '#kursilipat' when written as tag)."""
    if not caption:
        return caption
    # Collapse spaces immediately following a hashtag word when separated before another hashtag or end
    # Specifically fix patterns like `#kursi lipat #outdoor` -> `#kursilipat #outdoor`
    fixed = re.sub(
        r"#([A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)(?=\s*#|\s*$)",
        r"#\1\2",
        caption,
    )
    return fixed.strip()


def sanitize_text(text: str) -> tuple[str, list[ComplianceIssue]]:
    """Scan text for banned phrases and return a soft-claim sanitized version + issues."""
    issues: list[ComplianceIssue] = []
    for category, severity, pattern, suggestion in BANNED_RULES:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            issues.append(
                ComplianceIssue(
                    category=category,
                    severity=severity,
                    matched_phrase=match.group(0),
                    suggestion=suggestion,
                )
            )

    rewritten = text
    for pattern, replacement in SAFE_REWRITES:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    return rewritten, issues


def audit_text(
    text: str,
    is_sensitive_category: bool = False,
    field_name: str = "text",
) -> ComplianceReport:
    """Audit a single text string against Shopee Video & TikTok Shop rules."""
    rewritten, raw_issues = sanitize_text(text)
    issues = [issue.model_copy(update={"field_name": field_name}) for issue in raw_issues]

    status: Literal["SAFE", "WARNING", "BLOCKED"] = "SAFE"
    if any(i.severity == "BLOCKED" for i in issues):
        status = "BLOCKED"
    elif any(i.severity == "WARNING" for i in issues):
        status = "WARNING"

    return ComplianceReport(status=status, issues=issues, rewritten_text=rewritten)


def audit_blueprint(bp: BlueprintResponse) -> ComplianceReport:
    """Audit all Indonesian copy in a BlueprintResponse."""
    all_issues: list[ComplianceIssue] = []
    is_sensitive = bp.product_analysis.is_sensitive_category

    for scene in bp.scenes:
        vo_rep = audit_text(
            scene.vo_script_id,
            is_sensitive_category=is_sensitive,
            field_name=f"Scene {scene.scene_number} VO",
        )
        all_issues.extend(vo_rep.issues)

        ost_rep = audit_text(
            scene.on_screen_text_id,
            is_sensitive_category=is_sensitive,
            field_name=f"Scene {scene.scene_number} Headline",
        )
        all_issues.extend(ost_rep.issues)

    cap_rep = audit_text(
        bp.capcut_finishing.shopee_caption_and_hashtags,
        is_sensitive_category=is_sensitive,
        field_name="Caption Shopee",
    )
    all_issues.extend(cap_rep.issues)

    if bp.capcut_finishing.tiktok_caption_and_hashtags.strip():
        tt_rep = audit_text(
            bp.capcut_finishing.tiktok_caption_and_hashtags,
            is_sensitive_category=is_sensitive,
            field_name="Caption TikTok",
        )
        all_issues.extend(tt_rep.issues)

    if bp.product_knowledge.pinned_comment_faq_id.strip():
        pin_rep = audit_text(
            bp.product_knowledge.pinned_comment_faq_id,
            is_sensitive_category=is_sensitive,
            field_name="Pinned Comment FAQ",
        )
        all_issues.extend(pin_rep.issues)

    status: Literal["SAFE", "WARNING", "BLOCKED"] = "SAFE"
    if any(i.severity == "BLOCKED" for i in all_issues):
        status = "BLOCKED"
    elif any(i.severity == "WARNING" for i in all_issues):
        status = "WARNING"

    return ComplianceReport(status=status, issues=all_issues, rewritten_text="")


def sanitize_blueprint(bp: BlueprintResponse) -> BlueprintResponse:
    """Return a copy of BlueprintResponse with all VO, headlines, and captions sanitized."""
    clean_scenes = []
    for scene in bp.scenes:
        vo_clean, _ = sanitize_text(scene.vo_script_id)
        ost_clean, _ = sanitize_text(scene.on_screen_text_id)
        clean_scenes.append(
            scene.model_copy(
                update={
                    "vo_script_id": vo_clean,
                    "on_screen_text_id": ost_clean,
                }
            )
        )

    full_vo_clean = " ".join(s.vo_script_id.strip() for s in clean_scenes)
    caption_clean, _ = sanitize_text(bp.capcut_finishing.shopee_caption_and_hashtags)
    tt_clean, _ = sanitize_text(bp.capcut_finishing.tiktok_caption_and_hashtags)
    pin_clean, _ = sanitize_text(bp.product_knowledge.pinned_comment_faq_id)
    clean_finishing = bp.capcut_finishing.model_copy(
        update={
            "full_vo_script_id": full_vo_clean,
            "shopee_caption_and_hashtags": normalize_hashtags_in_caption(caption_clean),
            "tiktok_caption_and_hashtags": normalize_hashtags_in_caption(tt_clean),
        }
    )
    clean_knowledge = bp.product_knowledge.model_copy(
        update={"pinned_comment_faq_id": pin_clean}
    )
    return bp.model_copy(
        update={
            "product_knowledge": clean_knowledge,
            "scenes": clean_scenes,
            "capcut_finishing": clean_finishing,
        }
    )
