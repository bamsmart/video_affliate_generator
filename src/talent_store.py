"""Lightweight text-only preference store for Visual Character & Speaking Persona (zero media upload)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from src.schemas import (
    LocationLockMode,
    PersonaStyle,
    TalentPresence,
    TalentPresetCollection,
    TalentSavedProfile,
)

LEGACY_PROFILE_FILENAME = "talent_profile.json"
PRESETS_FILENAME = "talent_presets.json"


def _default_presets() -> list[TalentSavedProfile]:
    return [
        TalentSavedProfile(
            preset_id="avatar_pria_id",
            talent_name="Avatar Google Flow Saya (Pria Indonesia)",
            talent_presence=TalentPresence.AVATAR_MALE_ID,
            persona=PersonaStyle.SANTAI,
            avatar_flow_tag="@me",
            visual_notes="Pria asli Indonesia rapi dengan kemeja kasual / kaos polos warna netral",
            location_mode=LocationLockMode.AUTO_CONTEXTUAL,
        ),
        TalentSavedProfile(
            preset_id="avatar_wanita_id",
            talent_name="Avatar Google Flow Saya (Wanita Indonesia)",
            talent_presence=TalentPresence.AVATAR_FEMALE_ID,
            persona=PersonaStyle.SANTAI,
            avatar_flow_tag="@me",
            visual_notes="Wanita asli Indonesia rapi dengan outfit kasual warna earth-tone",
            location_mode=LocationLockMode.AUTO_CONTEXTUAL,
        ),
        TalentSavedProfile(
            preset_id="avatar_hijab_id",
            talent_name="Avatar Google Flow Saya (Hijab Indonesia)",
            talent_presence=TalentPresence.AVATAR_HIJAB_ID,
            persona=PersonaStyle.ANTUSIAS,
            avatar_flow_tag="@me",
            visual_notes="Wanita asli Indonesia berhijab pashmina rapi warna earth-tone",
            location_mode=LocationLockMode.AUTO_CONTEXTUAL,
        ),
        TalentSavedProfile(
            preset_id="broll_produk",
            talent_name="Tanpa Wajah / Fokus Produk Saja",
            talent_presence=TalentPresence.FACELESS_BROLL,
            persona=PersonaStyle.SANTAI,
            avatar_flow_tag="",
            visual_notes="Fokus produk tajam dan interaksi tangan berkulit khas Indonesia tanpa menampilkan wajah",
            location_mode=LocationLockMode.AUTO_CONTEXTUAL,
        ),
    ]


def load_preset_collection(profile_dir: str | Path = "profile") -> TalentPresetCollection:
    """Load all saved presets, falling back cleanly to ready-to-use built-in presets."""
    p_dir = Path(profile_dir)
    presets_path = p_dir / PRESETS_FILENAME
    if presets_path.is_file():
        try:
            col = TalentPresetCollection.model_validate_json(
                presets_path.read_text(encoding="utf-8")
            )
            if col.presets:
                normalized_presets = [
                    p.model_copy(update={"avatar_flow_tag": "@me"})
                    if (not p.is_faceless and not p.avatar_flow_tag.strip())
                    else p
                    for p in col.presets
                ]
                active = col.active_preset_id
                if not any(p.preset_id == active for p in normalized_presets):
                    active = normalized_presets[0].preset_id
                return TalentPresetCollection(active_preset_id=active, presets=normalized_presets)
        except Exception:
            pass

    defaults = _default_presets()
    return TalentPresetCollection(active_preset_id=defaults[0].preset_id, presets=defaults)


def save_preset_collection(
    collection: TalentPresetCollection,
    profile_dir: str | Path = "profile",
) -> TalentPresetCollection:
    p_dir = Path(profile_dir)
    p_dir.mkdir(parents=True, exist_ok=True)
    presets_path = p_dir / PRESETS_FILENAME
    presets_path.write_text(collection.model_dump_json(indent=2), encoding="utf-8")
    return collection


def load_talent_profile(profile_dir: str | Path = "profile") -> TalentSavedProfile:
    """Return the currently active TalentSavedProfile."""
    col = load_preset_collection(profile_dir)
    for p in col.presets:
        if p.preset_id == col.active_preset_id:
            return p
    return col.presets[0]


def save_talent_profile(
    profile: TalentSavedProfile,
    profile_dir: str | Path = "profile",
) -> TalentSavedProfile:
    """Upsert `profile` inside the preset collection and set it as active."""
    col = load_preset_collection(profile_dir)
    preset_id = (
        profile.preset_id
        or re.sub(r"[^a-z0-9]+", "_", profile.talent_name.lower()).strip("_")
        or "custom_talent"
    )
    updated = profile.model_copy(
        update={
            "preset_id": preset_id,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    new_list: list[TalentSavedProfile] = []
    replaced = False
    for existing in col.presets:
        if existing.preset_id == preset_id:
            new_list.append(updated)
            replaced = True
        else:
            new_list.append(existing)
    if not replaced:
        new_list.append(updated)

    save_preset_collection(
        TalentPresetCollection(active_preset_id=preset_id, presets=new_list),
        profile_dir,
    )
    return updated


def set_active_preset(
    preset_id: str,
    profile_dir: str | Path = "profile",
) -> TalentSavedProfile:
    col = load_preset_collection(profile_dir)
    if any(p.preset_id == preset_id for p in col.presets):
        col = col.model_copy(update={"active_preset_id": preset_id})
        save_preset_collection(col, profile_dir)
    return load_talent_profile(profile_dir)
