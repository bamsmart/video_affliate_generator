"""Shopee & TikTok affiliate AI video director — Mobile-First & Streamlit Cloud Ready Studio."""

from __future__ import annotations

import hmac
import re
from pathlib import Path

import streamlit as st

from src.blueprint_engine import count_words
from src.compliance import audit_blueprint, sanitize_blueprint
from src.config import (
    get_app_pin,
    get_gemini_api_key,
    get_openrouter_api_key,
    load_config,
    redact_secrets,
)
from src.exporter import save_blueprint_artifacts
from src.history_store import list_saved_blueprints
from src.image_prep import save_clean_ingredient_image
from src.schemas import (
    LocationLockMode,
    PersonaStyle,
    PlatformMode,
    SavedBlueprintRecord,
    TalentPresence,
    TalentSavedProfile,
)
from src.service import generate_blueprint_service, regenerate_hook_service
from src.talent_store import (
    load_preset_collection,
    load_talent_profile,
    save_talent_profile,
    set_active_preset,
)
from src.voiceover import synthesize_vo_mp3

# Mobile-first centered layout works cleanly on smartphone screens AND desktop browsers
st.set_page_config(
    page_title="Affiliate AI Video Director",
    page_icon=":material/movie_edit:",
    layout="centered",
)

cfg = load_config()
profile_dir = Path(cfg.get("paths", {}).get("profile_dir", "profile"))
projects_base_dir = Path(cfg.get("paths", {}).get("projects_dir", "projects"))

# ── Optional Cloud PIN Protection Gate ────────────────────────────────────────
required_pin = get_app_pin()
if "pin_unlocked" not in st.session_state:
    st.session_state["pin_unlocked"] = False

if required_pin and not st.session_state["pin_unlocked"]:
    st.title("Affiliate AI video director")
    with st.container(border=True):
        st.subheader("Masukkan PIN akses")
        st.caption("Proteksi aktif agar kuota API Anda aman saat aplikasi dibuka dari cloud.")
        entered_pin = st.text_input(
            "PIN aplikasi",
            type="password",
            placeholder="Masukkan PIN...",
            key="input_app_pin",
        )
        if st.button(
            "Buka aplikasi",
            type="primary",
            icon=":material/lock_open:",
            width="stretch",
            key="btn_unlock_pin",
        ):
            if hmac.compare_digest(entered_pin.strip(), required_pin):
                st.session_state["pin_unlocked"] = True
                st.rerun()
            else:
                st.error("PIN tidak sesuai.", title="Akses ditolak", icon=":material/lock:")
    st.stop()

# ── Initialize Session State ──────────────────────────────────────────────────
if "talent_profile" not in st.session_state:
    st.session_state["talent_profile"] = load_talent_profile(profile_dir)
if "record" not in st.session_state:
    st.session_state["record"] = None
if "compliance_report" not in st.session_state:
    st.session_state["compliance_report"] = None
if "project_dir" not in st.session_state:
    st.session_state["project_dir"] = None
if "artifacts" not in st.session_state:
    st.session_state["artifacts"] = {}
if "knowledge_warnings" not in st.session_state:
    st.session_state["knowledge_warnings"] = []
if "variation_counter" not in st.session_state:
    st.session_state["variation_counter"] = 0
if "previous_hooks" not in st.session_state:
    st.session_state["previous_hooks"] = []
if "cached_product_images" not in st.session_state:
    st.session_state["cached_product_images"] = []
if "generated_vo_mp3" not in st.session_state:
    st.session_state["generated_vo_mp3"] = None
if "generated_vo_srt" not in st.session_state:
    st.session_state["generated_vo_srt"] = None

preset_collection = load_preset_collection(profile_dir)
current_profile: TalentSavedProfile = st.session_state["talent_profile"]

# ── Sidebar: Global Settings + Project History Loader ─────────────────────────
with st.sidebar:
    st.subheader("Pengaturan mesin AI")

    mode_labels = {
        "gemini_then_openrouter": "Gemini utama -> fallback OpenRouter",
        "free_router": "OpenRouter gratis (model besar)",
        "budget_pro": "OpenRouter pro (cepat)",
        "offline_demo": "Mode demo offline (tanpa API key)",
    }
    engine_mode = st.selectbox(
        "Mode koneksi AI",
        options=list(mode_labels.keys()),
        format_func=lambda k: mode_labels[k],
        index=0,
        key="engine_mode",
    )

    with st.expander("Atur API key manual (opsional)", icon=":material/key:"):
        override_gemini = st.text_input(
            "Gemini API key",
            type="password",
            placeholder="AIza...",
            key="override_gemini",
        )
        override_or = st.text_input(
            "OpenRouter API key",
            type="password",
            placeholder="sk-or-v1-...",
            key="override_or",
        )

    active_gemini_key = get_gemini_api_key(override_gemini)
    active_or_key = get_openrouter_api_key(override_or)

    if engine_mode == "offline_demo":
        st.info(
            "Berjalan tanpa kuota API menggunakan contoh blueprint komersial.",
            title="Mode demo aktif",
            icon=":material/science:",
        )
    elif engine_mode == "gemini_then_openrouter":
        gem_stat = "aktif" if active_gemini_key else "belum diisi"
        or_stat = "aktif" if active_or_key else "belum diisi"
        st.caption(f"Gemini utama: **{gem_stat}** · Fallback OpenRouter: **{or_stat}**")
        if not active_gemini_key and not active_or_key:
            st.warning(
                "Isi GEMINI_API_KEY atau OPENROUTER_API_KEY di Secrets / .env.",
                title="API key belum terdeteksi",
                icon=":material/warning:",
            )
    elif not active_or_key:
        st.warning(
            "Isi OPENROUTER_API_KEY di Secrets / .env terlebih dahulu.",
            title="API key belum terdeteksi",
            icon=":material/warning:",
        )

    st.divider()
    auto_web_enrich = st.toggle(
        "Riset otomatis pengetahuan produk dari web",
        value=True,
        key="toggle_auto_web_enrich",
    )
    tts_voices = cfg.get("tts", {}).get("voices", ["id-ID-GadisNeural", "id-ID-ArdiNeural"])
    selected_tts_voice = st.selectbox(
        "Suara TTS bantuan CapCut",
        options=tts_voices,
        key="selected_tts_voice",
    )

    saved_history = list_saved_blueprints(projects_base_dir)
    if saved_history:
        st.divider()
        st.subheader("Riwayat blueprint")
        history_options = list(range(len(saved_history)))
        selected_hist_idx = st.selectbox(
            "Pilih produk tersimpan",
            options=history_options,
            format_func=lambda idx: (
                f"{saved_history[idx][1].blueprint.product_analysis.product_name[:32]} "
                f"({saved_history[idx][1].created_at[5:16].replace('T', ' ')})"
            ),
            key="history_select_idx",
        )
        if st.button(
            "Buka riwayat terpilih",
            icon=":material/history:",
            width="stretch",
            key="btn_load_history",
        ):
            hist_dir, hist_rec = saved_history[selected_hist_idx]
            hist_comp = audit_blueprint(hist_rec.blueprint)
            hist_arts = save_blueprint_artifacts(hist_rec, hist_comp, hist_dir)
            st.session_state["record"] = hist_rec
            st.session_state["compliance_report"] = hist_comp
            st.session_state["project_dir"] = str(hist_dir)
            st.session_state["artifacts"] = {k: str(v) for k, v in hist_arts.items()}
            st.session_state["previous_hooks"] = list(hist_rec.previous_hooks)
            st.session_state["knowledge_warnings"] = []
            st.session_state["generated_vo_mp3"] = None
            st.session_state["generated_vo_srt"] = None
            st.rerun()

    st.divider()
    if st.button(
        "Mulai produk baru",
        icon=":material/restart_alt:",
        width="stretch",
        key="btn_reset_project",
    ):
        st.session_state["record"] = None
        st.session_state["compliance_report"] = None
        st.session_state["project_dir"] = None
        st.session_state["artifacts"] = {}
        st.session_state["knowledge_warnings"] = []
        st.session_state["variation_counter"] = 0
        st.session_state["previous_hooks"] = []
        st.session_state["cached_product_images"] = []
        st.session_state["generated_vo_mp3"] = None
        st.session_state["generated_vo_srt"] = None
        st.rerun()

# ── Main Header (Mobile-Friendly Compact) ────────────────────────────────────
st.title("Affiliate AI video director")
st.caption(
    "Buka langsung di HP -> Upload screenshot produk -> Salin prompt ke Google Flow & finishing di CapCut"
)

# ── Preferensi Karakter & Gaya Narasi (Terlipat Rapi) ─────────────────────────
with st.expander(
    f"Gaya aktif: {current_profile.talent_presence.value} · {current_profile.persona.value}",
    expanded=False,
    icon=":material/tune:",
):
    preset_ids = [p.preset_id for p in preset_collection.presets] + ["__new__"]
    preset_names_map = {p.preset_id: p.talent_name for p in preset_collection.presets}
    preset_names_map["__new__"] = "+ Simpan sebagai preset baru"

    current_idx = (
        preset_ids.index(current_profile.preset_id)
        if current_profile.preset_id in preset_ids
        else 0
    )
    chosen_preset_id = st.selectbox(
        "Preset cepat",
        options=preset_ids,
        index=current_idx,
        format_func=lambda pid: preset_names_map.get(pid, pid),
        key="select_talent_preset",
    )

    if chosen_preset_id != "__new__" and chosen_preset_id != current_profile.preset_id:
        switched = set_active_preset(chosen_preset_id, profile_dir)
        st.session_state["talent_profile"] = switched
        st.rerun()

    editing_profile = (
        TalentSavedProfile(
            preset_id="custom_talent",
            talent_name="Preset Baru",
        )
        if chosen_preset_id == "__new__"
        else current_profile
    )

    presence_options = [tp.value for tp in TalentPresence]
    selected_presence_val = st.segmented_control(
        "Tipe subjek di video Google Flow",
        options=presence_options,
        default=editing_profile.talent_presence.value,
        required=True,
        wrap=True,
        key="presence_select",
    )
    persona_options = [p.value for p in PersonaStyle]
    selected_persona_val = st.segmented_control(
        "Gaya bicara naskah VO",
        options=persona_options,
        default=editing_profile.persona.value,
        required=True,
        wrap=True,
        key="persona_select",
    )
    t_name = st.text_input(
        "Nama preset",
        value=editing_profile.talent_name,
        key="input_talent_name",
    )
    t_notes = st.text_input(
        "Detail outfit / gaya visual singkat (opsional)",
        value=editing_profile.visual_notes,
        placeholder="Contoh: Kemeja linen warna netral rapi",
        key="input_talent_notes",
    )
    loc_options = [m.value for m in LocationLockMode]
    selected_loc_mode = st.segmented_control(
        "Lokasi di Visual Bible",
        options=loc_options,
        default=editing_profile.location_mode.value,
        required=True,
        wrap=True,
        key="location_mode_select",
    )
    custom_loc_val = editing_profile.custom_location
    if selected_loc_mode == LocationLockMode.LOCKED_CUSTOM.value:
        custom_loc_val = st.text_input(
            "Deskripsi lokasi tetap",
            value=editing_profile.custom_location,
            placeholder="Contoh: Ruang tamu minimalis hangat cahaya pagi",
            key="input_custom_location",
        )

    if st.button(
        "Simpan preferensi",
        type="primary",
        icon=":material/save:",
        width="stretch",
        key="btn_save_talent",
    ):
        target_pid = (
            re.sub(r"[^a-z0-9]+", "_", t_name.lower()).strip("_") or "custom_talent"
            if chosen_preset_id == "__new__"
            else editing_profile.preset_id
        )
        new_prof = editing_profile.model_copy(
            update={
                "preset_id": target_pid,
                "talent_name": t_name.strip() or "Preset Utama",
                "talent_presence": TalentPresence(
                    selected_presence_val or TalentPresence.FACELESS_BROLL.value
                ),
                "persona": PersonaStyle(selected_persona_val or PersonaStyle.SANTAI.value),
                "visual_notes": t_notes.strip(),
                "location_mode": LocationLockMode(
                    selected_loc_mode or LocationLockMode.AUTO_CONTEXTUAL.value
                ),
                "custom_location": custom_loc_val.strip(),
            }
        )
        saved_prof = save_talent_profile(new_prof, profile_dir)
        st.session_state["talent_profile"] = saved_prof
        st.toast(f"Preferensi '{saved_prof.talent_name}' diaktifkan.")
        st.rerun()

# ── Mobile-First Single-Column Input Card ────────────────────────────────────
with st.container(border=True):
    st.subheader("Buat blueprint produk baru")

    product_files = st.file_uploader(
        "Upload screenshot halaman produk dari galeri HP",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="product_uploader",
    )
    if product_files:
        prev_cols = st.columns(min(3, len(product_files)))
        for idx, pf in enumerate(product_files[:3]):
            prev_cols[idx].image(
                pf.getvalue(),
                width=110,
                alt=f"Gambar produk unggahan {idx + 1}",
            )

    duration_preset = st.segmented_control(
        "Durasi & kedalaman ulasan",
        options=[
            "15 detik (3 scene)",
            "25-30 detik (5 scene)",
            "40-45 detik (7 scene deep)",
        ],
        default="15 detik (3 scene)",
        required=True,
        wrap=True,
        key="duration_preset",
    )

    platform_labels = {
        PlatformMode.SHOPEE.value: "Shopee Video",
        PlatformMode.TIKTOK.value: "TikTok Shop",
        PlatformMode.BOTH.value: "Shopee + TikTok",
    }
    selected_platform_str = st.segmented_control(
        "Target platform CTA",
        options=list(platform_labels.keys()),
        format_func=lambda k: platform_labels[k],
        default=PlatformMode.SHOPEE.value,
        required=True,
        wrap=True,
        key="platform_mode_select",
    )

    with st.expander("Tambah detail spek / link website produk (opsional — hasil lebih dalam)", icon=":material/fact_check:"):
        product_url = st.text_input(
            "Link website resmi brand / artikel review produk",
            placeholder="https://...",
            key="input_product_url",
        )
        extra_note = st.text_input(
            "Nama merek / promo fokus singkat",
            placeholder="Contoh: TrailTop Kursi Lipat 150kg bonus tas",
            key="extra_note",
        )
        raw_specs_text = st.text_area(
            "Copy-paste spesifikasi lengkap dari deskripsi toko",
            placeholder="Tempel rincian bahan / ukuran / komposisi dari toko agar ulasan makin tajam...",
            height=100,
            key="input_raw_specs",
        )

    generate_clicked = st.button(
        "Generate blueprint & product knowledge",
        type="primary",
        icon=":material/auto_awesome:",
        width="stretch",
        key="btn_generate_blueprint",
    )

active_platform_mode = PlatformMode(selected_platform_str or PlatformMode.SHOPEE.value)

if generate_clicked:
    raw_images = [f.getvalue() for f in (product_files or [])]
    has_any_text = bool(extra_note.strip() or product_url.strip() or raw_specs_text.strip())
    if not raw_images and not has_any_text and engine_mode != "offline_demo":
        st.warning(
            "Pilih minimal 1 gambar produk dari galeri HP terlebih dahulu (atau isi link/spesifikasi).",
            title="Input produk belum ada",
            icon=":material/upload_file:",
        )
    else:
        with st.spinner("Mengumpulkan product knowledge mendalam & merancang blueprint..."):
            try:
                st.session_state["cached_product_images"] = raw_images
                st.session_state["generated_vo_mp3"] = None
                st.session_state["generated_vo_srt"] = None
                record, comp_rep, proj_dir, arts, k_warns = generate_blueprint_service(
                    product_images_bytes=raw_images,
                    profile=st.session_state["talent_profile"],
                    duration_preset=duration_preset or "15 detik (3 scene)",
                    extra_note=extra_note,
                    engine_mode=engine_mode,
                    cfg=cfg,
                    gemini_key=active_gemini_key,
                    openrouter_key=active_or_key,
                    previous_hooks=st.session_state["previous_hooks"],
                    platform_mode=active_platform_mode,
                    product_url=product_url,
                    raw_specs_text=raw_specs_text,
                    auto_web_enrich=auto_web_enrich,
                    variation_index=st.session_state["variation_counter"],
                )
                st.session_state["record"] = record
                st.session_state["compliance_report"] = comp_rep
                st.session_state["project_dir"] = str(proj_dir)
                st.session_state["artifacts"] = {k: str(v) for k, v in arts.items()}
                st.session_state["knowledge_warnings"] = k_warns
                st.session_state["previous_hooks"] = list(record.previous_hooks)
                st.session_state["variation_counter"] += 1
                st.toast(f"Blueprint siap ({record.model_used})")
            except Exception as exc:
                safe_err = redact_secrets(str(exc), [active_gemini_key, active_or_key])
                st.error(safe_err, title="Gagal membuat blueprint", icon=":material/error:")

# ── Step-by-Step Output Cards (Mobile-Friendly Vertical Stream) ──────────────
record_obj: SavedBlueprintRecord | None = st.session_state.get("record")
comp_obj = st.session_state.get("compliance_report")

if record_obj is not None and comp_obj is not None:
    bp = record_obj.blueprint
    pa = bp.product_analysis
    pk = bp.product_knowledge
    fs = bp.flow_setup
    cf = bp.capcut_finishing

    st.divider()

    for kw in st.session_state.get("knowledge_warnings", []):
        st.info(kw, title="Catatan pengambilan link", icon=":material/info:")

    # Summary & Anti-Spam Toolbar
    with st.container(border=True):
        st.subheader(pa.product_name)
        hook_hist_count = len(record_obj.previous_hooks)
        src_label = ", ".join(record_obj.knowledge_sources) if record_obj.knowledge_sources else "AI Product Specialist"
        st.markdown(
            f":orange-badge[:material/lightbulb: Hook: {pa.hook_angle}] "
            f":green-badge[:material/location_on: {pa.recommended_setting_id}] "
            f":violet-badge[:material/psychology: {src_label}] "
            f":blue-badge[:material/shield: {hook_hist_count} hook] "
            f":gray-badge[:material/memory: {record_obj.model_used}]"
        )
        if record_obj.fallback_reason:
            st.caption(
                f"Info koneksi AI: {record_obj.fallback_reason} -> otomatis dialihkan ke OpenRouter."
            )
        if pa.usp:
            st.caption("Keunggulan utama: " + " · ".join(pa.usp))

        with st.container(horizontal=True):
            regen_hook_clicked = st.button(
                "Regenerate hook",
                icon=":material/refresh:",
                width="stretch",
                key="btn_regenerate_hook",
            )
            regen_all_clicked = st.button(
                "Variasi baru (anti-spam)",
                icon=":material/shuffle:",
                width="stretch",
                key="btn_regenerate_all",
            )

    if regen_hook_clicked:
        with st.spinner("Meracik variasi Hook Scene 1 baru..."):
            try:
                proj_dir = Path(st.session_state["project_dir"])
                new_rec, new_comp, new_arts = regenerate_hook_service(
                    record=record_obj,
                    profile=st.session_state["talent_profile"],
                    engine_mode=engine_mode,
                    cfg=cfg,
                    gemini_key=active_gemini_key,
                    openrouter_key=active_or_key,
                    variation_index=st.session_state["variation_counter"],
                    project_dir=proj_dir,
                )
                st.session_state["record"] = new_rec
                st.session_state["compliance_report"] = new_comp
                st.session_state["artifacts"] = {k: str(v) for k, v in new_arts.items()}
                st.session_state["previous_hooks"] = list(new_rec.previous_hooks)
                st.session_state["variation_counter"] += 1
                st.session_state["generated_vo_mp3"] = None
                st.session_state["generated_vo_srt"] = None
                st.rerun()
            except Exception as exc:
                safe_err = redact_secrets(str(exc), [active_gemini_key, active_or_key])
                st.error(safe_err, title="Gagal me-regenerate hook", icon=":material/error:")

    if regen_all_clicked:
        with st.spinner("Membuat variasi blueprint baru..."):
            try:
                proj_dir = Path(st.session_state["project_dir"])
                new_rec, new_comp, _, new_arts, k_warns = generate_blueprint_service(
                    product_images_bytes=st.session_state.get("cached_product_images", []),
                    profile=st.session_state["talent_profile"],
                    duration_preset=duration_preset or record_obj.duration_preset,
                    extra_note=extra_note,
                    engine_mode=engine_mode,
                    cfg=cfg,
                    gemini_key=active_gemini_key,
                    openrouter_key=active_or_key,
                    previous_hooks=st.session_state["previous_hooks"],
                    platform_mode=active_platform_mode,
                    product_url=product_url,
                    raw_specs_text=raw_specs_text,
                    auto_web_enrich=auto_web_enrich,
                    variation_index=st.session_state["variation_counter"],
                    existing_project_dir=proj_dir,
                )
                st.session_state["record"] = new_rec
                st.session_state["compliance_report"] = new_comp
                st.session_state["artifacts"] = {k: str(v) for k, v in new_arts.items()}
                st.session_state["knowledge_warnings"] = k_warns
                st.session_state["previous_hooks"] = list(new_rec.previous_hooks)
                st.session_state["variation_counter"] += 1
                st.session_state["generated_vo_mp3"] = None
                st.session_state["generated_vo_srt"] = None
                st.rerun()
            except Exception as exc:
                safe_err = redact_secrets(str(exc), [active_gemini_key, active_or_key])
                st.error(safe_err, title="Gagal membuat variasi baru", icon=":material/error:")

    if comp_obj.status != "SAFE":
        issue_lines = "\n".join(
            f"- **{iss.field_name}**: `{iss.matched_phrase}` — {iss.suggestion}"
            for iss in comp_obj.issues
        )
        st.warning(
            f"Ditemukan kalimat berisiko pelanggaran kebijakan platform:\n{issue_lines}",
            title="Peringatan kepatuhan klaim produk",
            icon=":material/policy:",
        )
        if st.button(
            "Perbaiki klaim otomatis ke bahasa aman",
            icon=":material/auto_fix_high:",
            width="stretch",
            key="btn_sanitize",
        ):
            clean_bp = sanitize_blueprint(bp)
            clean_rec = record_obj.model_copy(update={"blueprint": clean_bp})
            clean_comp = audit_blueprint(clean_bp)
            proj_dir = Path(st.session_state["project_dir"])
            new_arts = save_blueprint_artifacts(clean_rec, clean_comp, proj_dir)
            st.session_state["record"] = clean_rec
            st.session_state["compliance_report"] = clean_comp
            st.session_state["artifacts"] = {k: str(v) for k, v in new_arts.items()}
            st.session_state["generated_vo_mp3"] = None
            st.session_state["generated_vo_srt"] = None
            st.rerun()

    # ── ADDED VALUE CARD: Deep Product Knowledge ─────────────────────────────
    with st.container(border=True):
        st.subheader("Product knowledge & nilai tambah")
        if pk.competitor_differentiator_angle:
            st.success(
                pk.competitor_differentiator_angle,
                title="Pembeda ulasan kita vs affiliator lain",
                icon=":material/workspace_premium:",
            )

        st.markdown("**Bedah spesifikasi teknis & material:**")
        for spec_item in pk.technical_specs_and_materials:
            st.markdown(f"- {spec_item}")
        if pk.how_it_works_or_usage_tip:
            st.markdown(f"**Tips pakai / mekanisme kerja:** {pk.how_it_works_or_usage_tip}")
        if pk.top_buyer_objection_and_answer:
            st.info(
                pk.top_buyer_objection_and_answer,
                title="Objection killer (jawab keraguan utama pembeli)",
                icon=":material/quiz:",
            )
        if pk.honest_pros_and_ideal_buyer:
            st.caption(f"**Paling cocok untuk:** {pk.honest_pros_and_ideal_buyer}")

    # ── STEP 1 CARD: Setup Google Flow ───────────────────────────────────────
    with st.container(border=True):
        st.subheader("Step 1 — Setup Google Flow (Ingredients)")
        st.markdown(
            f":green-badge[:material/aspect_ratio: Rasio {fs.aspect_ratio}] "
            ":blue-badge[:material/collections: Simpan & upload foto bersih ke Flow]"
        )
        for item in fs.ingredients_checklist:
            st.markdown(f"- {item}")

        cropped_path = (
            Path(record_obj.cropped_ingredient_path)
            if record_obj.cropped_ingredient_path
            else None
        )
        has_raw_upload = len(st.session_state.get("cached_product_images", [])) > 0

        if cropped_path and cropped_path.is_file():
            crop_bytes = cropped_path.read_bytes()
            st.image(
                crop_bytes,
                width=180,
                caption="Foto produk bersih (bebas bar UI Shopee)",
                alt="Foto produk bersih hasil crop",
            )
            st.download_button(
                "Simpan foto produk bersih ke HP",
                data=crop_bytes,
                file_name=cropped_path.name,
                mime="image/jpeg",
                icon=":material/download:",
                width="stretch",
                key="btn_dl_ing_clean",
            )

        if has_raw_upload:
            with st.expander("Atur ulang batas potong screenshot (opsional)", icon=":material/crop:"):
                top_crop = st.slider(
                    "Potong bar atas (%)",
                    min_value=0,
                    max_value=30,
                    value=11,
                    key="slider_crop_top",
                )
                bot_crop = st.slider(
                    "Potong bar bawah (%)",
                    min_value=0,
                    max_value=50,
                    value=34,
                    key="slider_crop_bot",
                )
                if st.button(
                    "Terapkan ulang crop",
                    icon=":material/crop_free:",
                    width="stretch",
                    key="btn_recrop",
                ):
                    proj_dir = Path(st.session_state["project_dir"])
                    new_crop_p, _ = save_clean_ingredient_image(
                        st.session_state["cached_product_images"][0],
                        output_dir=proj_dir / "input",
                        top_crop_pct=top_crop / 100.0,
                        bottom_crop_pct=bot_crop / 100.0,
                    )
                    record_obj = record_obj.model_copy(update={"cropped_ingredient_path": str(new_crop_p)})
                    st.session_state["record"] = record_obj
                    st.rerun()

        with st.expander("Lihat locked visual bible (otomatis masuk ke tiap scene)", icon=":material/lock:"):
            st.code(fs.locked_visual_bible_en, language="text")

    # ── STEP 2..N+1 CARDS: Per-Scene Google Flow Prompts (Thumb-Friendly) ────
    flow_action_guides = {
        "New Scene": (
            "green",
            "add_circle",
            "Mulai adegan pertama di Google Flow dengan foto produk di Ingredients.",
        ),
        "Extend": (
            "blue",
            "trending_flat",
            "Pilih Extend di Scene Builder untuk lanjut mulus dari frame terakhir.",
        ),
        "Jump to": (
            "violet",
            "switch_video",
            "Pilih Jump to di Scene Builder untuk pindah ke sudut kamera close-up.",
        ),
    }

    for scene in bp.scenes:
        step_idx = scene.scene_number + 1
        wc = count_words(scene.vo_script_id)
        b_col, b_icon, action_help = flow_action_guides.get(
            scene.flow_action,
            ("violet", "call_split", "Lanjutkan di Scene Builder Google Flow."),
        )
        wc_color = "green" if 10 <= wc <= 18 else "orange"

        with st.container(border=True):
            st.subheader(f"Step {step_idx} — Scene {scene.scene_number} ({scene.role})")
            st.markdown(
                f":{b_col}-badge[:material/{b_icon}: {scene.flow_action}] "
                f":gray-badge[:material/timer: {scene.duration_sec}d] "
                f":{wc_color}-badge[:material/record_voice_over: {wc} kata]"
            )
            st.caption(f"{action_help} · **Sambungan:** {scene.continuity_note}")

            st.markdown("**Prompt Google Flow (ketuk ikon copy di kanan atas kotak):**")
            st.code(scene.flow_prompt_en, language="text")

            st.markdown("**Naskah VO Bahasa Indonesia:**")
            st.code(scene.vo_script_id, language="text")
            st.caption(f"Teks headline layar CapCut: **{scene.on_screen_text_id}**")

    # ── FINAL STEP CARD: Paket Finishing CapCut, Pinned Comment & Upload ─────
    final_step_num = len(bp.scenes) + 2
    arts = st.session_state.get("artifacts", {})
    default_srt_path = Path(arts.get("capcut_srt", "")) if arts.get("capcut_srt") else None

    with st.container(border=True):
        st.subheader(f"Step {final_step_num} — Finishing CapCut & upload")

        st.markdown("**1. Full VO script (gabungan utuh):**")
        st.code(cf.full_vo_script_id, language="text")

        if default_srt_path and default_srt_path.is_file():
            st.download_button(
                "Download subtitle CapCut (.srt)",
                data=default_srt_path.read_bytes(),
                file_name="capcut_subtitles.srt",
                mime="text/plain",
                icon=":material/subtitles:",
                width="stretch",
                key="btn_dl_default_srt",
            )

        if st.button(
            "Buat audio MP3 + SRT sinkron otomatis (opsional)",
            icon=":material/graphic_eq:",
            width="stretch",
            key="btn_tts_mp3",
        ):
            with st.spinner("Menghasilkan vo_capcut.mp3 & subtitle SRT sinkron per kata..."):
                try:
                    proj_dir = Path(st.session_state["project_dir"])
                    mp3_out = proj_dir / "vo_capcut.mp3"
                    srt_out = proj_dir / "vo_capcut.srt"
                    synthesize_vo_mp3(
                        text=cf.full_vo_script_id,
                        output_mp3=mp3_out,
                        voice=selected_tts_voice,
                        rate=str(cfg.get("tts", {}).get("default_rate", "+6%")),
                        output_srt=srt_out,
                    )
                    st.session_state["generated_vo_mp3"] = str(mp3_out)
                    st.session_state["generated_vo_srt"] = str(srt_out)
                except Exception as exc:
                    st.error(str(exc), title="Gagal membuat audio MP3", icon=":material/error:")

        mp3_saved = st.session_state.get("generated_vo_mp3")
        srt_saved = st.session_state.get("generated_vo_srt")
        if mp3_saved and Path(mp3_saved).is_file():
            mp3_bytes = Path(mp3_saved).read_bytes()
            st.audio(mp3_bytes, format="audio/mp3")
            st.download_button(
                "Simpan vo_capcut.mp3 ke HP",
                data=mp3_bytes,
                file_name="vo_capcut.mp3",
                mime="audio/mp3",
                icon=":material/download:",
                width="stretch",
                key="btn_dl_vo_mp3",
            )
            if srt_saved and Path(srt_saved).is_file():
                st.download_button(
                    "Simpan vo_capcut.srt (sinkron suara)",
                    data=Path(srt_saved).read_bytes(),
                    file_name="vo_capcut.srt",
                    mime="text/plain",
                    icon=":material/closed_caption:",
                    width="stretch",
                    key="btn_dl_vo_srt",
                )

        st.markdown("**2. Pinned comment FAQ (salin & tempel di komentar pertama video):**")
        st.code(pk.pinned_comment_faq_id, language="text")

        st.markdown("**3. Saran BGM & tips CapCut:**")
        st.info(
            f"**BGM:** {cf.bgm_vibe_suggestion}\n\n**Tips CapCut:** {cf.pacing_tips}",
            icon=":material/content_cut:",
        )

        if record_obj.platform_mode in (PlatformMode.SHOPEE, PlatformMode.BOTH):
            st.markdown("**4. Caption & hashtag Shopee Video:**")
            st.code(cf.shopee_caption_and_hashtags, language="text")

        if record_obj.platform_mode in (PlatformMode.TIKTOK, PlatformMode.BOTH) and cf.tiktok_caption_and_hashtags.strip():
            st.markdown("**Caption & hashtag TikTok Shop:**")
            st.code(cf.tiktok_caption_and_hashtags, language="text")

        st.warning(
            cf.compliance_reminder,
            title="Syarat wajib kepatuhan platform",
            icon=":material/verified_user:",
        )

        if arts:
            with st.container(horizontal=True):
                md_file = Path(arts.get("blueprint_md", ""))
                js_file = Path(arts.get("blueprint_json", ""))
                if md_file.is_file():
                    st.download_button(
                        "Simpan .md",
                        data=md_file.read_bytes(),
                        file_name=md_file.name,
                        icon=":material/description:",
                        width="stretch",
                        key="btn_dl_md",
                    )
                if js_file.is_file():
                    st.download_button(
                        "Simpan .json",
                        data=js_file.read_bytes(),
                        file_name=js_file.name,
                        icon=":material/data_object:",
                        width="stretch",
                        key="btn_dl_json",
                    )
