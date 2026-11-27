"""Shopee & TikTok affiliate AI video director — Mobile-First & Streamlit Cloud Ready Studio."""

from __future__ import annotations

import hmac
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
from src.talent_store import load_talent_profile, save_talent_profile
from src.voiceover import synthesize_vo_mp3

MAX_UPLOAD_IMAGES = 4
MAX_IMAGE_BYTES = 10 * 1024 * 1024

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
                "GitHub tidak membawa file `.env` demi keamanan. Tempelkan API key Anda satu kali di **share.streamlit.io -> Settings -> Secrets**.",
                title="API key belum terdeteksi",
                icon=":material/warning:",
            )
            with st.expander("Cara aktifkan API key permanen", icon=":material/help:"):
                st.markdown(
                    "1. Ambil gratis **Gemini key** di [Google AI Studio](https://aistudio.google.com/apikey) "
                    "dan **OpenRouter key** di [OpenRouter Keys](https://openrouter.ai/keys).\n"
                    "2. Buka dashboard [Streamlit Cloud](https://share.streamlit.io) -> klik `⋮` pada app -> **Settings** -> **Secrets**.\n"
                    "3. Tempelkan dengan tanda kutip:\n"
                    '```toml\nGEMINI_API_KEY = "AIza..."\nOPENROUTER_API_KEY = "sk-or-v1-..."\n```\n'
                    "4. Klik **Save** (tersimpan otomatis selamanya setiap `git push`)."
                )
    elif not active_or_key:
        st.warning(
            "Isi OPENROUTER_API_KEY di Streamlit Cloud (Settings -> Secrets) atau `.env` lokal.",
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

# ── Mobile-First Single-Column Input Card ────────────────────────────────────
with st.container(border=True):
    st.subheader("Buat blueprint produk baru")

    product_files = st.file_uploader(
        "Upload foto produk utuh / screenshot halaman produk dari HP",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="product_uploader",
    )
    valid_uploads: list[tuple[str, bytes]] = []
    if product_files:
        if len(product_files) > MAX_UPLOAD_IMAGES:
            st.warning(
                f"Maksimal {MAX_UPLOAD_IMAGES} gambar produk yang diproses sekaligus.",
                title="Batas jumlah gambar",
                icon=":material/photo_library:",
            )
        for pf in product_files[:MAX_UPLOAD_IMAGES]:
            data = pf.getvalue()
            if len(data) > MAX_IMAGE_BYTES:
                st.warning(
                    f"File `{pf.name}` melebihi 10 MB dan dilewati.",
                    title="Ukuran file terlalu besar",
                    icon=":material/warning:",
                )
                continue
            valid_uploads.append((pf.name, data))

        if valid_uploads:
            prev_cols = st.columns(min(3, len(valid_uploads)))
            for idx, (_, img_data) in enumerate(valid_uploads[:3]):
                try:
                    prev_cols[idx].image(
                        img_data,
                        width=110,
                        alt=f"Gambar produk unggahan {idx + 1}",
                    )
                except Exception:
                    prev_cols[idx].caption("Pratinjau tidak tersedia")

    presence_options = [tp.value for tp in TalentPresence]
    quick_presence_val = st.segmented_control(
        "Subjek / Avatar Google Flow (khas Indonesia)",
        options=presence_options,
        default=current_profile.talent_presence.value,
        required=True,
        wrap=True,
        key="quick_presence_select",
    )

    avatar_tag_val = current_profile.avatar_flow_tag or "@me"
    if quick_presence_val != TalentPresence.FACELESS_BROLL.value:
        avatar_tag_val = st.text_input(
            "Tag Avatar Google Flow (default @me) & ciri tambahan (opsional)",
            value=current_profile.avatar_flow_tag or "@me",
            placeholder="@me (bisa tambah ciri seperti: @me, berkacamata, kaos hitam)",
            key="input_avatar_flow_tag",
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

    with st.expander("Pengaturan lanjutan gaya bicara VO & lokasi (opsional)", icon=":material/tune:"):
        persona_options = [p.value for p in PersonaStyle]
        selected_persona_val = st.segmented_control(
            "Gaya bicara naskah VO",
            options=persona_options,
            default=current_profile.persona.value,
            required=True,
            wrap=True,
            key="persona_select",
        )
        t_notes = st.text_input(
            "Detail outfit konsisten di semua scene (opsional)",
            value=current_profile.visual_notes,
            placeholder="Contoh: Kemeja kasual warna earth-tone rapi",
            key="input_talent_notes",
        )
        loc_options = [m.value for m in LocationLockMode]
        selected_loc_mode = st.segmented_control(
            "Lokasi di Visual Bible",
            options=loc_options,
            default=current_profile.location_mode.value,
            required=True,
            wrap=True,
            key="location_mode_select",
        )
        custom_loc_val = current_profile.custom_location
        if selected_loc_mode == LocationLockMode.LOCKED_CUSTOM.value:
            custom_loc_val = st.text_input(
                "Deskripsi lokasi tetap",
                value=current_profile.custom_location,
                placeholder="Contoh: Teras rumah Indonesia sore hari yang hangat",
                key="input_custom_location",
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

# Sync live character & avatar settings directly so user never forgets a separate Save button
live_profile = current_profile.model_copy(
    update={
        "talent_presence": TalentPresence(
            quick_presence_val or TalentPresence.AVATAR_MALE_ID.value
        ),
        "talent_name": quick_presence_val or current_profile.talent_name,
        "avatar_flow_tag": (
            (avatar_tag_val.strip() or "@me")
            if quick_presence_val != TalentPresence.FACELESS_BROLL.value
            else ""
        ),
        "persona": PersonaStyle(selected_persona_val or PersonaStyle.SANTAI.value),
        "visual_notes": t_notes.strip(),
        "location_mode": LocationLockMode(
            selected_loc_mode or LocationLockMode.AUTO_CONTEXTUAL.value
        ),
        "custom_location": custom_loc_val.strip(),
    }
)
st.session_state["talent_profile"] = live_profile

if generate_clicked:
    raw_images = [img_data for _, img_data in valid_uploads]
    has_any_text = bool(extra_note.strip() or product_url.strip() or raw_specs_text.strip())
    if not raw_images and not has_any_text and engine_mode != "offline_demo":
        st.warning(
            "Pilih minimal 1 gambar produk dari galeri HP terlebih dahulu (atau isi link/spesifikasi).",
            title="Input produk belum ada",
            icon=":material/upload_file:",
        )
    else:
        with st.spinner("Mengunci anatomi produk 1:1, identitas Avatar Indonesia & menyusun blueprint..."):
            try:
                saved_prof = save_talent_profile(live_profile, profile_dir)
                st.session_state["talent_profile"] = saved_prof
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
        st.subheader("Step 1 — Setup Google Flow (Ingredients anti-halu)")
        st.markdown(
            f":green-badge[:material/aspect_ratio: Rasio {fs.aspect_ratio}] "
            ":orange-badge[:material/view_in_ar: Kunci Geometri Produk 1:1] "
            ":blue-badge[:material/face: Kunci Avatar Indonesia]"
        )
        st.info(
            "Standar **Google Flow / Veo 3.1 Anti-Halu**:\n"
            "1. **Foto Produk Utuh:** Pastikan foto di **Ingredients** menampilkan **ujung kaki/bagian bawah produk secara penuh** (tidak terpotong).\n"
            "2. **Avatar `@me` & Ingredient Aktif:** Setiap prompt otomatis memanggil **`@me`** dengan deskripsi positif Nusantara dan mengunci geometri produk 1:1. Pastikan Foto Produk Bersih tetap aktif di **New Scene** maupun **Jump to**.\n"
            "3. **Hemat Kredit:** Uji alur & kaki produk dulu di mode **Veo Fast / Lite** sebelum render final dengan **Veo Quality**.",
            title="Panduan Google Flow Video Consultant",
            icon=":material/verified:",
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
                width=200,
                caption="Cek gambar ini: pastikan kaki/ujung bawah produk terlihat UTUH",
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
            with st.expander("Kaki/bawah produk terpotong? Atur batas crop di sini", icon=":material/crop:"):
                top_crop = st.slider(
                    "Potong bar atas (%)",
                    min_value=0,
                    max_value=30,
                    value=8,
                    key="slider_crop_top",
                )
                bot_crop = st.slider(
                    "Potong bar bawah (% — geser ke 0% jika foto bukan screenshot)",
                    min_value=0,
                    max_value=50,
                    value=24,
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

        with st.expander("Lihat kunci geometri produk & visual bible (otomatis masuk ke tiap scene)", icon=":material/lock:"):
            st.markdown("**Exact Product Geometry Lock:**")
            st.code(fs.exact_product_geometry_lock_en, language="text")
            st.markdown("**Locked Visual Bible:**")
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
