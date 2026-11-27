"""Cross-session anti-spam hook history & saved blueprint browser."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.schemas import SavedBlueprintRecord

HOOK_HISTORY_FILENAME = "hook_history.json"


_PROMO_NOISE = {
    "promo",
    "diskon",
    "murah",
    "gratis",
    "ongkir",
    "cod",
    "original",
    "ori",
    "official",
    "terlaris",
    "viral",
}


def _normalize_product_key(product_name: str) -> str:
    raw_tokens = re.findall(r"[a-z0-9]+", product_name.lower())
    core_tokens = [
        t
        for t in raw_tokens
        if t not in _PROMO_NOISE and not re.fullmatch(r"\d+(ml|gr|g|kg|pcs|cm|mm|l)?", t)
    ]
    chosen = core_tokens[:4] or raw_tokens[:4]
    return "_".join(chosen) or "default_product"


def load_product_hooks(product_name: str, projects_dir: str | Path = "projects") -> list[str]:
    """Load previously generated hooks for a product across past sessions."""
    hist_path = Path(projects_dir) / HOOK_HISTORY_FILENAME
    if not hist_path.is_file():
        return []
    try:
        data = json.loads(hist_path.read_text(encoding="utf-8"))
        key = _normalize_product_key(product_name)
        items = data.get(key, [])
        return [str(x) for x in items if str(x).strip()]
    except Exception:
        return []


def append_product_hook(
    product_name: str,
    hook_text: str,
    projects_dir: str | Path = "projects",
) -> list[str]:
    """Persist a newly generated hook under normalized product key (keeps last 25)."""
    p_dir = Path(projects_dir)
    p_dir.mkdir(parents=True, exist_ok=True)
    hist_path = p_dir / HOOK_HISTORY_FILENAME

    data: dict[str, list[str]] = {}
    if hist_path.is_file():
        try:
            raw = json.loads(hist_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
        except Exception:
            data = {}

    key = _normalize_product_key(product_name)
    existing = [str(x) for x in data.get(key, []) if str(x).strip()]
    clean_hook = hook_text.strip()
    if clean_hook and clean_hook not in existing:
        existing.append(clean_hook)
    data[key] = existing[-25:]
    hist_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data[key]


def list_saved_blueprints(projects_dir: str | Path = "projects") -> list[tuple[Path, SavedBlueprintRecord]]:
    """Scan projects/*/blueprint.json (newest first), skipping legacy incompatible folders."""
    p_dir = Path(projects_dir)
    if not p_dir.is_dir():
        return []

    found: list[tuple[Path, SavedBlueprintRecord]] = []
    for bp_json in sorted(p_dir.glob("*/blueprint.json"), reverse=True):
        try:
            rec = SavedBlueprintRecord.model_validate_json(bp_json.read_text(encoding="utf-8"))
            found.append((bp_json.parent, rec))
        except Exception:
            continue
    return found
