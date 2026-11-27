"""Tests for blueprint Markdown, JSON, and CapCut SRT exporter."""

from pathlib import Path

from src.blueprint_engine import enforce_commercial_mechanisms
from src.compliance import audit_blueprint
from src.exporter import save_blueprint_artifacts
from src.history_store import list_saved_blueprints
from src.prompts import build_offline_demo_blueprint
from src.schemas import SavedBlueprintRecord, TalentSavedProfile


def test_save_blueprint_artifacts_creates_md_json_srt_and_loads_in_history(tmp_path: Path):
    proj_dir = tmp_path / "projects" / "serum_01"
    bp = enforce_commercial_mechanisms(build_offline_demo_blueprint(TalentSavedProfile(), scene_count=3))
    record = SavedBlueprintRecord(
        project_id="serum_01",
        created_at="2026-11-27T16:30:00",
        duration_preset="15 detik (3 scene)",
        persona="Review Jujur Santai",
        model_used="offline-demo",
        blueprint=bp,
    )
    comp = audit_blueprint(bp)
    arts = save_blueprint_artifacts(record, comp, proj_dir)

    assert arts["blueprint_json"].is_file()
    assert arts["blueprint_md"].is_file()
    assert arts["capcut_srt"].is_file()

    md_text = arts["blueprint_md"].read_text(encoding="utf-8")
    assert "Step 1: Setup Google Flow (Ingredients)" in md_text
    assert "New Scene" in md_text
    assert "Konten Buatan AI" in md_text

    srt_text = arts["capcut_srt"].read_text(encoding="utf-8")
    assert "00:00:00,000 -->" in srt_text

    saved_list = list_saved_blueprints(tmp_path / "projects")
    assert len(saved_list) == 1
    assert saved_list[0][1].project_id == "serum_01"
