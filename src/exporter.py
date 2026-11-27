"""Blueprint artifact exporter (blueprint.json, blueprint.md, and capcut_subtitles.srt)."""

from __future__ import annotations

from pathlib import Path

from src.blueprint_engine import count_words
from src.compliance import ComplianceReport
from src.schemas import SavedBlueprintRecord
from src.srt_export import save_blueprint_srt


def render_blueprint_markdown(
    record: SavedBlueprintRecord,
    compliance_report: ComplianceReport,
) -> str:
    """Render SavedBlueprintRecord into a clean copy-ready Markdown guide with Deep Product Knowledge."""
    bp = record.blueprint
    pa = bp.product_analysis
    pk = bp.product_knowledge
    fs = bp.flow_setup
    cf = bp.capcut_finishing

    lines: list[str] = [
        f"# Blueprint Video Affiliate — {pa.product_name}",
        "",
        f"- **Project ID:** `{record.project_id}`",
        f"- **Kategori:** {pa.category} | **Lokasi Kontekstual:** {pa.recommended_setting_id}",
        f"- **Platform:** `{record.platform_mode.value}` | **Durasi:** {record.duration_preset} | **Preset:** {record.talent_preset_name}",
        f"- **Engine AI:** `{record.model_used}` | **Status Kepatuhan:** `{compliance_report.status}`",
        f"- **Hook Angle:** {pa.hook_angle}",
        f"- **Target Audiens:** {pa.target_audience}",
    ]
    if record.knowledge_sources:
        lines.append("- **Sumber Product Knowledge:** " + ", ".join(record.knowledge_sources))
    if record.fallback_reason:
        lines.append(f"- **Catatan Fallback:** {record.fallback_reason}")
    if pa.price_or_promo:
        lines.append(f"- **Harga / Promo:** {pa.price_or_promo}")
    if pa.usp:
        lines.append("- **Keunggulan Utama (USP):** " + "; ".join(pa.usp))

    lines.extend(
        [
            "",
            "---",
            "",
            "## Product Knowledge & Added Value (Pembeda dari Affiliator Lain)",
        ]
    )
    if pk.competitor_differentiator_angle:
        lines.append(f"- **Sudut Pembeda Kompetitor:** {pk.competitor_differentiator_angle}")
    if pk.technical_specs_and_materials:
        lines.append("- **Bedah Spesifikasi & Material:**")
        for spec in pk.technical_specs_and_materials:
            lines.append(f"  - {spec}")
    if pk.how_it_works_or_usage_tip:
        lines.append(f"- **Cara Kerja / Tips Pakai Pro:** {pk.how_it_works_or_usage_tip}")
    if pk.honest_pros_and_ideal_buyer:
        lines.append(f"- **Profil Pembeli Ideal:** {pk.honest_pros_and_ideal_buyer}")
    if pk.top_buyer_objection_and_answer:
        lines.append(f"- **Objection Killer (Jawaban Keraguan Pembeli):** {pk.top_buyer_objection_and_answer}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Step 1: Setup Google Flow (Ingredients)",
            f"- **Rasio Video:** `{fs.aspect_ratio}`",
            "- **Upload ke Menu Ingredients di Google Flow:**",
        ]
    )
    for item in fs.ingredients_checklist:
        lines.append(f"  - [ ] {item}")

    lines.extend(
        [
            "",
            "**Locked Visual Bible (Sudah otomatis disuntikkan ke setiap prompt scene):**",
            "```text",
            fs.locked_visual_bible_en,
            "```",
            "",
            "---",
        ]
    )

    for s in bp.scenes:
        step_num = s.scene_number + 1
        wc = count_words(s.vo_script_id)
        lines.extend(
            [
                "",
                f"## Step {step_num}: Scene {s.scene_number} ({s.role}) — {s.duration_sec}s",
                f"- **Tombol di Google Flow:** `{s.flow_action}`",
                f"- **Continuity Bridge:** {s.continuity_note}",
                "",
                "**Prompt Google Flow (EN):**",
                "```text",
                s.flow_prompt_en,
                "```",
                f"**VO Bahasa Indonesia ({wc} kata):**",
                "```text",
                s.vo_script_id,
                "```",
                f"**Headline Layar CapCut:** `{s.on_screen_text_id}`",
            ]
        )

    final_step = len(bp.scenes) + 2
    lines.extend(
        [
            "",
            "---",
            "",
            f"## Step {final_step}: Paket Finishing CapCut, Pinned Comment & Upload",
            "",
            "**Full VO Script (Siap Rekam / TTS CapCut):**",
            "```text",
            cf.full_vo_script_id,
            "```",
            f"- **Saran Vibe BGM:** {cf.bgm_vibe_suggestion}",
            f"- **Tips Pacing & Editing CapCut:** {cf.pacing_tips}",
            "",
            "**Pinned Comment FAQ (Tempel di Komentar Pertama untuk Dongkrak Konversi):**",
            "```text",
            pk.pinned_comment_faq_id,
            "```",
            "",
            "**Caption & Hashtag Shopee Video:**",
            "```text",
            cf.shopee_caption_and_hashtags,
            "```",
        ]
    )
    if cf.tiktok_caption_and_hashtags.strip():
        lines.extend(
            [
                "",
                "**Caption & Hashtag TikTok Shop:**",
                "```text",
                cf.tiktok_caption_and_hashtags,
                "```",
            ]
        )
    lines.extend(
        [
            "",
            f"> **Kepatuhan Wajib:** {cf.compliance_reminder}",
            "",
        ]
    )
    return "\n".join(lines)


def save_blueprint_artifacts(
    record: SavedBlueprintRecord,
    compliance_report: ComplianceReport,
    project_dir: Path,
) -> dict[str, Path]:
    """Save blueprint.json, blueprint.md, and capcut_subtitles.srt inside project_dir."""
    project_dir.mkdir(parents=True, exist_ok=True)
    json_path = project_dir / "blueprint.json"
    md_path = project_dir / "blueprint.md"
    srt_path = project_dir / "capcut_subtitles.srt"

    json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(
        render_blueprint_markdown(record, compliance_report),
        encoding="utf-8",
    )
    save_blueprint_srt(record.blueprint, srt_path)
    return {
        "blueprint_json": json_path,
        "blueprint_md": md_path,
        "capcut_srt": srt_path,
    }
