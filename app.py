"""Affiliate AI Video Director — Dual Laptop-First & Cloud-Mobile 1x Copy-Paste Studio for Google Flow & CapCut."""

from __future__ import annotations

from contextlib import nullcontext
import hmac
from pathlib import Path

import streamlit as st

from src.blueprint_engine import (
    audit_commercial_story_pillars,
    compose_full_15s_flow_prompt,
    count_words,
)
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
from src.image_prep import (
    build_frames_zip,
    parse_grid_layout,
    save_product_authority_image,
    split_storyboard_grid,
)
from src.schemas import (
    LocationLockMode,
    PersonaStyle,
    PlatformMode,
    SavedBlueprintRecord,
    TalentPresence,
    TalentSavedProfile,
    WorkflowMode,
)
from src.service import generate_blueprint_service, regenerate_hook_service
from src.talent_store import (
    delete_avatar_photo,
    get_saved_avatar_photo_path,
    load_talent_profile,
    save_avatar_photo,
    save_talent_profile,
)
from src.voiceover import synthesize_vo_mp3

MAX_UPLOAD_IMAGES = 4
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# Wide layout gives Laptop Studio a 2-column cockpit while Mobile mode/phones stack cleanly
st.set_page_config(
    page_title="Affiliate AI Studio",
    page_icon=":material/movie_edit:",
    layout="wide",
    initial_sidebar_state="collapsed",
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

# ── Sidebar: Simple Top Actions + Collapsed Technical Settings ───────────────
with st.sidebar:
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

    saved_history = list_saved_blueprints(projects_base_dir)
    if saved_history:
        st.divider()
        st.subheader("Riwayat produk")
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
    with st.expander("Pengaturan aplikasi & koneksi AI (opsional)", icon=":material/settings:"):
        device_labels = {
            "laptop": "Laptop (2-Kolom)",
            "mobile": "Mobile / HP (1-Kolom)",
        }
        device_mode = st.segmented_control(
            "Tata letak layar",
            options=list(device_labels.keys()),
            format_func=lambda k: device_labels[k],
            default="laptop",
            required=True,
            wrap=True,
            key="device_mode_select",
        )

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

        override_gemini = st.text_input(
            "Gemini API key (opsional)",
            type="password",
            placeholder="AIza...",
            key="override_gemini",
        )
        override_or = st.text_input(
            "OpenRouter API key (opsional)",
            type="password",
            placeholder="sk-or-v1-...",
            key="override_or",
        )

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

    is_laptop_mode = (device_mode or "laptop") == "laptop"
    active_gemini_key = get_gemini_api_key(override_gemini)
    active_or_key = get_openrouter_api_key(override_or)

    if engine_mode == "offline_demo":
        st.info(
            "Berjalan tanpa kuota API menggunakan contoh blueprint komersial.",
            title="Mode demo aktif",
            icon=":material/science:",
        )
    elif engine_mode == "gemini_then_openrouter" and not active_gemini_key and not active_or_key:
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
    elif engine_mode in ("free_router", "budget_pro") and not active_or_key:
        st.warning(
            "Isi OPENROUTER_API_KEY di Streamlit Cloud (Settings -> Secrets) atau `.env` lokal.",
            title="API key belum terdeteksi",
            icon=":material/warning:",
        )

# ── Main Header (Apple-Clean 3-Step Intro) ──────────────────────────────────
st.title("Affiliate AI Studio")
st.caption(
    "Upload foto produk -> Klik 1 tombol -> Copy-Paste 1 prompt komersial siap pakai ke Google Flow."
)

# ── Streamlined Input Card (2 Uploaders -> Primary Button -> Collapsed Options) ──
with st.container(border=True):
    if is_laptop_mode:
        up_left, up_right = st.columns([1.15, 1.0], gap="medium")
    else:
        up_left = nullcontext()
        up_right = nullcontext()

    with up_left:
        product_files = st.file_uploader(
            "Foto produk (1 foto, atau 2–4 sudut depan/samping/belakang)",
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
                prev_cols = st.columns(min(4, len(valid_uploads)))
                for idx, (_, img_data) in enumerate(valid_uploads[:4]):
                    try:
                        prev_cols[idx].image(
                            img_data,
                            width=88,
                            alt=f"Gambar produk unggahan {idx + 1}",
                        )
                    except Exception:
                        prev_cols[idx].caption("Pratinjau tidak tersedia")
                if len(valid_uploads) >= 2:
                    st.caption(
                        f"{len(valid_uploads)} sudut digabung otomatis jadi 1 lembar **ProductAuthority.jpg**."
                    )

    with up_right:
        st.session_state.setdefault("saved_avatar_upload_sig", None)
        avatar_upload = st.file_uploader(
            "Foto wajah / Avatar (upload 1x saja, tersimpan otomatis)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
            key="avatar_photo_uploader",
        )
        if avatar_upload is not None:
            av_bytes = avatar_upload.getvalue()
            if len(av_bytes) > MAX_IMAGE_BYTES:
                st.warning(
                    "Foto avatar melebihi 10 MB dan dilewati.",
                    title="Ukuran foto terlalu besar",
                    icon=":material/warning:",
                )
            else:
                av_sig = f"{avatar_upload.name}:{len(av_bytes)}"
                if av_sig != st.session_state.get("saved_avatar_upload_sig"):
                    save_avatar_photo(av_bytes, profile_dir)
                    st.session_state["saved_avatar_upload_sig"] = av_sig

        saved_avatar_path = get_saved_avatar_photo_path(profile_dir)
        if saved_avatar_path is not None:
            st.image(
                saved_avatar_path.read_bytes(),
                width=88,
                caption="Avatar aktif",
                alt="Foto avatar tersimpan",
            )
            if st.button(
                "Hapus foto avatar",
                icon=":material/delete:",
                key="btn_delete_avatar_photo",
            ):
                delete_avatar_photo(profile_dir)
                st.rerun()

    generate_clicked = st.button(
        "Buat Prompt Siap Pakai",
        type="primary",
        icon=":material/auto_awesome:",
        width="stretch",
        key="btn_generate_blueprint",
    )

    with st.expander("Opsi lanjutan (opsional)", icon=":material/tune:"):
        if is_laptop_mode:
            opt_left, opt_right = st.columns([1.0, 1.0], gap="medium")
        else:
            opt_left = nullcontext()
            opt_right = nullcontext()

        with opt_left:
            presence_options = [tp.value for tp in TalentPresence]
            quick_presence_val = st.segmented_control(
                "Model / presenter video",
                options=presence_options,
                default=current_profile.talent_presence.value,
                required=True,
                wrap=True,
                key="quick_presence_select",
            )
            avatar_tag_val = current_profile.avatar_flow_tag or "@me"
            if quick_presence_val != TalentPresence.FACELESS_BROLL.value:
                avatar_tag_val = st.text_input(
                    "Tag Avatar Google Flow (default @me)",
                    value=current_profile.avatar_flow_tag or "@me",
                    placeholder="@me (bisa tambah ciri: @me, berkacamata)",
                    key="input_avatar_flow_tag",
                )

            duration_preset = st.segmented_control(
                "Durasi video",
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

        with opt_right:
            include_native_voice = st.toggle(
                "Sertakan suara & script Indonesia otomatis di prompt Google Flow",
                value=True,
                key="toggle_native_voice_default",
            )
            workflow_labels = {
                WorkflowMode.STORYBOARD_FIRST.value: "Storyboard-First (Frames to Video — Anti-Halu)",
                WorkflowMode.DIRECT_INGREDIENTS.value: "Direct Ingredients-to-Video (Cepat)",
            }
            selected_workflow_str = st.segmented_control(
                "Mode alur Google Flow",
                options=list(workflow_labels.keys()),
                format_func=lambda k: workflow_labels[k],
                default=WorkflowMode.STORYBOARD_FIRST.value,
                required=True,
                wrap=True,
                key="workflow_mode_select",
            )

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
                "Detail outfit konsisten di semua scene",
                value=current_profile.visual_notes,
                placeholder="Contoh: Kemeja kasual earth-tone rapi",
                key="input_talent_notes",
            )
            loc_options = [m.value for m in LocationLockMode]
            selected_loc_mode = st.segmented_control(
                "Lokasi latar belakang",
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

            product_url = st.text_input(
                "Link website resmi / halaman produk",
                placeholder="https://...",
                key="input_product_url",
            )
            extra_note = st.text_input(
                "Nama merek / catatan promo singkat",
                placeholder="Contoh: TrailTop Kursi Lipat 150kg",
                key="extra_note",
            )
            raw_specs_text = st.text_area(
                "Copy-paste deskripsi produk dari toko",
                placeholder="Tempel rincian bahan / ukuran agar ulasan makin tepat...",
                height=90,
                key="input_raw_specs",
            )

active_platform_mode = PlatformMode(selected_platform_str or PlatformMode.SHOPEE.value)
active_workflow_mode = WorkflowMode(selected_workflow_str or WorkflowMode.STORYBOARD_FIRST.value)

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
            "Pilih minimal 1 gambar produk terlebih dahulu (atau isi link/deskripsi di Pengaturan tambahan).",
            title="Foto produk belum diunggah",
            icon=":material/upload_file:",
        )
    else:
        with st.spinner("Menyiapkan foto produk bersih & 1x prompt anti-halu Google Flow..."):
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
                    workflow_mode=active_workflow_mode,
                )
                st.session_state["record"] = record
                st.session_state["compliance_report"] = comp_rep
                st.session_state["project_dir"] = str(proj_dir)
                st.session_state["artifacts"] = {k: str(v) for k, v in arts.items()}
                st.session_state["knowledge_warnings"] = k_warns
                st.session_state["previous_hooks"] = list(record.previous_hooks)
                st.session_state["variation_counter"] += 1
                st.toast(f"Prompt siap pakai ({record.model_used})")
            except Exception as exc:
                safe_err = redact_secrets(str(exc), [active_gemini_key, active_or_key])
                st.error(safe_err, title="Gagal membuat prompt", icon=":material/error:")

# ── Foolproof Output: 1x Copy-Paste Card + 3 Optional Collapsed Expanders ────
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

    hero_scene = bp.scenes[0]
    cropped_path = (
        Path(record_obj.cropped_ingredient_path)
        if record_obj.cropped_ingredient_path
        else None
    )
    saved_avatar_out = get_saved_avatar_photo_path(profile_dir)
    has_raw_upload = len(st.session_state.get("cached_product_images", [])) > 0
    arts = st.session_state.get("artifacts", {})
    default_srt_path = Path(arts.get("capcut_srt", "")) if arts.get("capcut_srt") else None

    # ── MAIN RESULT CARD: 1 Copy-Paste Box + Clean Actions ──────────────────
    with st.container(border=True):
        st.subheader(f"Siap pakai — {pa.product_name}")
        pillars = audit_commercial_story_pillars(bp)
        p_emosi = "✓" if pillars["emotion_pain"] else "•"
        p_solusi = "✓" if (pillars["solution_usp"] and pillars["detail_review"]) else "•"
        p_ba = "✓" if pillars["before_after"] else "•"
        p_cta = "✓" if pillars["cta"] else "•"
        st.caption(
            f"Alur komersial: Emosi & Painful {p_emosi} · Solusi & Review Detail {p_solusi} · "
            f"Before & After {p_ba} · CTA {p_cta}"
        )

        clip_dur_labels = {
            "15s": "15 detik utuh (1x jadi, tanpa mengulang)",
            "8s": "8 detik (per adegan)",
        }
        selected_clip_dur = st.segmented_control(
            "Durasi klip di Google Flow",
            options=list(clip_dur_labels.keys()),
            format_func=lambda k: clip_dur_labels[k],
            default="15s",
            required=True,
            wrap=True,
            key="clip_duration_select",
        )
        is_15s_clip = (selected_clip_dur or "15s") == "15s"
        hero_prompt = (
            compose_full_15s_flow_prompt(bp, profile=live_profile, include_voice=include_native_voice)
            if is_15s_clip
            else (
                hero_scene.flow_voice_prompt_en
                if (include_native_voice and hero_scene.flow_voice_prompt_en)
                else hero_scene.flow_prompt_en
            )
        )

        if is_laptop_mode:
            assets_col, prompt_col = st.columns([1.0, 1.5], gap="medium")
        else:
            assets_col = nullcontext()
            prompt_col = nullcontext()

        with assets_col:
            if cropped_path and cropped_path.is_file():
                crop_bytes = cropped_path.read_bytes()
                is_multi_angle = len(st.session_state.get("cached_product_images", [])) >= 2
                prod_dl_label = (
                    "1. Download ProductAuthority.jpg (Multi-Sudut)"
                    if is_multi_angle
                    else "1. Download ProductAuthority.jpg"
                )
                st.image(
                    crop_bytes,
                    width=130,
                    alt="Foto produk bersih ProductAuthority siap upload ke Google Flow",
                )
                st.download_button(
                    prod_dl_label,
                    data=crop_bytes,
                    file_name="ProductAuthority.jpg",
                    mime="image/jpeg",
                    icon=":material/download:",
                    width="stretch",
                    key="btn_dl_ing_clean",
                )

            if saved_avatar_out is not None:
                avatar_bytes = saved_avatar_out.read_bytes()
                st.image(
                    avatar_bytes,
                    width=110,
                    alt="Foto avatar siap upload ke Google Flow",
                )
                st.download_button(
                    "Download avatar_photo.jpg",
                    data=avatar_bytes,
                    file_name="avatar_photo.jpg",
                    mime="image/jpeg",
                    icon=":material/face:",
                    width="stretch",
                    key="btn_dl_avatar_photo",
                )
            elif not live_profile.is_faceless:
                st.caption("Belum ada foto wajah? Upload di kotak **Foto wajah / Avatar** di atas.")

            st.link_button(
                "2. Buka Google Flow",
                "https://labs.google/fx/tools/flow",
                type="primary",
                icon=":material/open_in_new:",
                width="stretch",
            )

        with prompt_col:
            dur_step_hint = "atur durasi **15s**" if is_15s_clip else "atur durasi **5-8s**"
            st.markdown(
                f"""
1. **Download foto** di samping (`ProductAuthority.jpg` & `avatar_photo.jpg`).
2. Klik **2. Buka Google Flow** -> **New project** -> **Videos (9:16)** -> {dur_step_hint} -> klik **`+`** lalu upload fotonya.
3. **Copy kotak di bawah -> Paste ke Google Flow -> klik Generate.**
""".strip()
            )
            st.code(hero_prompt, language="text", wrap_lines=True)
            st.caption(
                "Tips: jika `@ProductAuthority` belum jadi tag biru di Google Flow, hapus kata itu lalu ketik **`@`** dan pilih **`ProductAuthority.jpg`**."
            )

            with st.container(horizontal=True):
                regen_hook_clicked = st.button(
                    "Ganti Hook",
                    icon=":material/refresh:",
                    width="stretch",
                    key="btn_regenerate_hook",
                )
                regen_all_clicked = st.button(
                    "Buat Ulang",
                    icon=":material/shuffle:",
                    width="stretch",
                    key="btn_regenerate_all",
                )

    if regen_hook_clicked:
        with st.spinner("Meracik variasi hook pembuka baru..."):
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
        with st.spinner("Membuat variasi prompt baru..."):
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
                    workflow_mode=active_workflow_mode,
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

    # ── SINGLE COLLAPSED EXTRAS EXPANDER (Voice/MP3/Caption, Adegan 2..N, Pro) ──
    with st.expander(
        "Alat tambahan: Audio MP3, Caption, Adegan 2–N & Mode Pro (opsional)",
        icon=":material/widgets:",
    ):
        tab_vo, tab_scenes, tab_pro = st.tabs(["Suara & Caption", "Adegan 2–N", "Mode Pro"])

        with tab_vo:
            st.markdown("**Naskah suara (VO) penjelasan produk:**")
            st.code(cf.full_vo_script_id, language="text", wrap_lines=True)

            if st.button(
                "Buat audio MP3 + SRT sinkron suara Indonesia",
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
                    "Download vo_capcut.mp3",
                    data=mp3_bytes,
                    file_name="vo_capcut.mp3",
                    mime="audio/mp3",
                    icon=":material/download:",
                    width="stretch",
                    key="btn_dl_vo_mp3",
                )
                if srt_saved and Path(srt_saved).is_file():
                    st.download_button(
                        "Download vo_capcut.srt (sinkron suara)",
                        data=Path(srt_saved).read_bytes(),
                        file_name="vo_capcut.srt",
                        mime="text/plain",
                        icon=":material/closed_caption:",
                        width="stretch",
                        key="btn_dl_vo_srt",
                    )

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

            if record_obj.platform_mode in (PlatformMode.SHOPEE, PlatformMode.BOTH):
                st.markdown("**Caption & hashtag Shopee Video:**")
                st.code(cf.shopee_caption_and_hashtags, language="text", wrap_lines=True)

            if record_obj.platform_mode in (PlatformMode.TIKTOK, PlatformMode.BOTH) and cf.tiktok_caption_and_hashtags.strip():
                st.markdown("**Caption & hashtag TikTok Shop:**")
                st.code(cf.tiktok_caption_and_hashtags, language="text", wrap_lines=True)

            st.markdown("**Pinned comment FAQ (salin & tempel di komentar pertama video):**")
            st.code(pk.pinned_comment_faq_id, language="text", wrap_lines=True)

            st.info(
                f"**BGM:** {cf.bgm_vibe_suggestion}\n\n**Tips CapCut:** {cf.pacing_tips}",
                title="Saran BGM & editing CapCut",
                icon=":material/content_cut:",
            )
            st.warning(
                cf.compliance_reminder,
                title="Syarat wajib kepatuhan platform",
                icon=":material/verified_user:",
            )

        with tab_scenes:
            if len(bp.scenes) <= 1:
                st.caption("Blueprint saat ini hanya memiliki 1 adegan.")
            else:
                st.info(
                    "Bisa langsung di Google Flow tanpa extract video manual:\n"
                    "- **Cara 1 (`Extend`):** Klik tombol **Extend** pada akhir klip Scene 1.\n"
                    "- **Cara 2 (`Save frame` -> `Start frame`):** Jeda (*Pause*) video Scene 1 di frame terakhir -> "
                    "arahkan kursor dan klik **`Save frame`** -> jadikan gambar tersebut **`Start frame`** Scene 2 agar bentuk produk & wajah tetap 100% konsisten.",
                    title="Tips menyambung scene langsung di Google Flow",
                    icon=":material/photo_camera:",
                )
                for scene in bp.scenes[1:]:
                    scene_prompt = (
                        scene.flow_voice_prompt_en
                        if (include_native_voice and scene.flow_voice_prompt_en)
                        else scene.flow_prompt_en
                    )
                    if scene.flow_action == "Extend":
                        plain_guide = "Di Google Flow, klik tombol **Extend** pada klip sebelumnya, lalu **Paste** prompt ini:"
                    else:
                        plain_guide = "Di Google Flow, klik tombol **Jump to** (atau pasang `Save frame` klip 1 ke **Start frame** + **ProductAuthority.jpg**), lalu **Paste** prompt ini:"
                    st.markdown(f"**Adegan {scene.scene_number} ({scene.role})** — {plain_guide}")
                    st.code(scene_prompt, language="text", wrap_lines=True)
                    st.caption(f"Naskah VO adegan {scene.scene_number}: {scene.vo_script_id}")

        with tab_pro:
            if has_raw_upload:
                st.markdown("**Atur ulang batas crop foto produk (jika ujung bawah masih terpotong):**")
                top_crop = st.slider(
                    "Potong bar atas (%)",
                    min_value=0,
                    max_value=30,
                    value=8,
                    key="slider_crop_top",
                )
                bot_crop = st.slider(
                    "Potong bar bawah (% — 0% jika bukan screenshot)",
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
                    new_crop_p, _ = save_product_authority_image(
                        st.session_state["cached_product_images"][:4],
                        output_dir=proj_dir / "input",
                        top_crop_pct=top_crop / 100.0,
                        bottom_crop_pct=bot_crop / 100.0,
                    )
                    record_obj = record_obj.model_copy(update={"cropped_ingredient_path": str(new_crop_p)})
                    st.session_state["record"] = record_obj
                    st.rerun()

            st.markdown(f"**Prompt Contact Sheet Grid Storyboard ({fs.storyboard_grid_layout} — Nano Banana / Flow Image Mode):**")
            st.code(fs.storyboard_grid_prompt_en, language="text", wrap_lines=True)

            st.markdown("**Prompt Gambar Keyframe per Adegan (Nano Banana):**")
            for scene in bp.scenes:
                if scene.keyframe_image_prompt_en:
                    st.caption(f"Adegan {scene.scene_number} ({scene.role})")
                    st.code(scene.keyframe_image_prompt_en, language="text", wrap_lines=True)

            st.markdown("**Prompt Start-to-End Frame (transisi antar posisi anti-ubah bentuk):**")
            st.code(fs.start_to_end_prompt_en, language="text", wrap_lines=True)

            st.divider()
            st.markdown("**Potong Otomatis Gambar Grid Storyboard -> Keyframe 1..N:**")
            grid_options = ["2x2", "3x2", "2x3", "3x3"]
            default_grid_idx = (
                grid_options.index(fs.storyboard_grid_layout)
                if fs.storyboard_grid_layout in grid_options
                else 0
            )
            chosen_grid = st.selectbox(
                "Tata letak panel grid",
                options=grid_options,
                index=default_grid_idx,
                key="select_grid_split_layout",
            )
            trim_pct = st.slider(
                "Buang garis pembatas panel (%)",
                min_value=0.0,
                max_value=5.0,
                value=1.5,
                step=0.5,
                key="slider_grid_trim_pct",
            )
            grid_upload = st.file_uploader(
                "Upload gambar Contact Sheet Grid hasil Nano Banana",
                type=["png", "jpg", "jpeg", "webp"],
                key="grid_splitter_uploader",
            )
            if grid_upload is not None:
                try:
                    cols_n, rows_n = parse_grid_layout(chosen_grid)
                    split_imgs = split_storyboard_grid(
                        grid_upload.getvalue(),
                        cols=cols_n,
                        rows=rows_n,
                        trim_margin_pct=trim_pct / 100.0,
                    )
                    zip_bytes = build_frames_zip(split_imgs, prefix="keyframe")
                    st.download_button(
                        f"Download semua {len(split_imgs)} keyframe (.zip)",
                        data=zip_bytes,
                        file_name=f"{record_obj.project_id}_keyframes.zip",
                        mime="application/zip",
                        type="primary",
                        icon=":material/folder_zip:",
                        width="stretch",
                        key="btn_dl_keyframes_zip",
                    )
                    g_cols = st.columns(min(cols_n, 3))
                    for f_idx, f_bytes in enumerate(split_imgs, start=1):
                        c_slot = g_cols[(f_idx - 1) % len(g_cols)]
                        c_slot.image(
                            f_bytes,
                            width=120,
                            caption=f"Keyframe {f_idx}",
                            alt=f"Keyframe {f_idx} hasil split grid",
                        )
                        c_slot.download_button(
                            f"Frame {f_idx}",
                            data=f_bytes,
                            file_name=f"keyframe_{f_idx}.jpg",
                            mime="image/jpeg",
                            width="stretch",
                            key=f"btn_dl_split_frame_{f_idx}",
                        )
                except Exception as exc:
                    st.error(str(exc), title="Gagal memotong grid", icon=":material/error:")

            st.divider()
            st.markdown("**Detail Product Knowledge & Nilai Tambah:**")
            if pk.competitor_differentiator_angle:
                st.success(
                    pk.competitor_differentiator_angle,
                    title="Pembeda ulasan",
                    icon=":material/workspace_premium:",
                )
            for spec_item in pk.technical_specs_and_materials:
                st.markdown(f"- {spec_item}")
            if pk.how_it_works_or_usage_tip:
                st.markdown(f"**Tips pakai / mekanisme kerja:** {pk.how_it_works_or_usage_tip}")
            if pk.top_buyer_objection_and_answer:
                st.info(
                    pk.top_buyer_objection_and_answer,
                    title="Objection killer",
                    icon=":material/quiz:",
                )
            if pk.honest_pros_and_ideal_buyer:
                st.caption(f"**Paling cocok untuk:** {pk.honest_pros_and_ideal_buyer}")

            st.markdown("**Checklist Internal @ProductAuthority & Visual Bible:**")
            st.code(fs.exact_product_geometry_lock_en, language="text", wrap_lines=True)
            st.code(fs.locked_visual_bible_en, language="text", wrap_lines=True)

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
