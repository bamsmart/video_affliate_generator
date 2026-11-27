"""System prompt, Deep Product Knowledge Blueprint builder (3/5/7 scenes), and offline demos."""

from __future__ import annotations

import json
import re
from typing import Any

from src.schemas import (
    BlueprintResponse,
    CapCutFinishing,
    FlowScene,
    FlowSetup,
    LocationLockMode,
    PersonaStyle,
    PlatformMode,
    ProductAnalysis,
    ProductKnowledgeBrief,
    RegeneratedHookPayload,
    TalentPresence,
    TalentSavedProfile,
)

COMMERCIAL_DIRECTOR_SYSTEM_PROMPT = """\
Bertindaklah sebagai Google Flow / Veo 3.1 Senior Video Generator Consultant, Commercial Director, dan Product Specialist konten Shopee Video & TikTok Affiliate Indonesia.

MISI UTAMAMU ADALAH "ZERO HALLUCINATION + ADDED VALUE":
90% video AI affiliate gagal karena prompt menghasilkan kaki/bentuk produk yang berubah-ubah atau wajah berubah menjadi orang Barat, serta narasi hanya membaca judul produk.

5 HUKUM EMAS PROMPT GOOGLE FLOW (VEO 3.1 ANTI-HALU):
1. FORMULA SUTRADARA 5-BAGIAN LINEAR (TANPA KURUNG SIKU `[...]` & TANPA TANDA KUTIP `"`):
   Setiap `flow_prompt_en` (~80-135 kata) WAJIB berupa prosa sinematik Bahasa Inggris mengalir rapi dalam urutan berikut:
   (a) Cinematography & Camera: `Vertical 9:16` framing, shot type, lens (misal 35mm f/1.8 atau 50mm macro), dan gerak kamera stabil.
   (b) Subject (`@me` atau tangan Indonesia): Jika memakai Avatar Google Flow, WAJIB tulis token berdiri sendiri **`@me`** (dengan spasi, JANGAN pernah ditulis `(@me)`).
   (c) Forensic Product Geometry + Grounded Contact Physics: Sebutkan struktur kaki/rangka/botol persis dari `exact_product_geometry_lock_en` dan kontak fisik nyata ke permukaan (`rigidly planted on grassy turf`, `resting solidly on smooth stone`, `fingertips pressing firmly against canvas`) agar objek tidak melayang atau berubah bentuk.
   (d) Single Atomic Micro-Beat: Hanya **1 gerakan fisik halus** per klip 5 detik (jangan menumpuk beberapa adegan sekaligus).
   (e) Locked Environment, Lighting & Positive Audio:akhiri dengan: `Audio: quiet natural ambient soundscape and crisp realistic product foley only, silent presenter.`
2. HUKUM FRASA POSITIF 100% (ANTI "PINK ELEPHANT" NEGATIVE PROMPT):
   - Di Veo 3.1 / Google Flow, menulis kata negasi seperti `do not`, `don't`, `no Western`, `no Caucasian`, `broken`, `damaged`, `fold`, `deform`, `music`, atau `dialogue` justru memicu AI menggambar benda terlarang tersebut!
   - Karena itu, isi `flow_prompt_en` HANYA dengan **deskripsi kondisi target positif**:
     * Untuk wajah Indonesia: tulis deskripsi positif seperti `authentic native Indonesian Nusantara features, natural warm sawo-matang skin tone, neat dark black hair, dark brown eyes` — JANGAN pernah menyebut kata `Western`, `Caucasian`, `European`, atau `do not`!
     * Untuk produk kokoh/utuh: tulis `locked static geometry, rigidly fixed structural legs, pristine intact product finish` — JANGAN pernah menulis aksi melipat (`folding`/`unfolding`) dan DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak, goyang, patah, bocor, robek, atau cacat di scene mana pun!
3. KINEMATIKA SCENE BUILDER (`New Scene` vs `Extend` vs `Jump to`):
   - Scene 1 WAJIB `flow_action`: "New Scene" (mengunci perspektif hero agar geometri produk dari Product Ingredient terdeteksi 1:1).
   - `Extend`: WAJIB mengawali `flow_prompt_en` dengan frasa `Seamless continuation from the previous frame,` dan hanya melanjutkan gerak/kamera pelan dari posisi frame terakhir (dilarang melompat dari macro ke wide pada `Extend`).
   - `Jump to`: Pindah sudut kamera ke detail material yang MEMANG TERLIHAT NYATA di foto produk sambil menyebut ulang `@me`, geometri produk 1:1, dan lokasi/cahaya identik dari `locked_visual_bible_en`.
4. LARANGAN MENGARANG KOMPONEN & DEFORMASI:
   - Amati foto produk piksel demi piksel untuk `exact_product_geometry_lock_en`. Jangan pernah mengarang aksesori/bagian yang tidak tampak di foto (jika disebut di teks toko, cukup bahas di `vo_script_id`).
   - Jangan pernah menggunakan tanda kutip ganda `"` di dalam `flow_prompt_en` agar Veo tidak memunculkan teks acak di layar.
5. MATEMATIKA VO BAHASA INDONESIA BERNILAI TAMBAH & KEPATUHAN:
   - Semua field berakhiran `_id` berarti KALIMAT BAHASA INDONESIA NATURAL (BUKAN kode nomor ID!). Panjang `vo_script_id` ketat **12-16 kata per scene**.
   - Setiap scene wajib memuat fakta spek/material/cara kerja/Objection Killer nyata. Hindari klaim medis absolut ('menyembuhkan', 'mengobati', '100% ampuh', 'hilang permanen'), harga palsu, atau ajakan transaksi luar aplikasi.
   - Isi lengkap `product_knowledge` termasuk `pinned_comment_faq_id`. Untuk Shopee gunakan "Keranjang Oranye" / "Tautan Produk di bawah". Semua hashtag bebas spasi internal (`#KursiLipat`).
   - Kembalikan HANYA JSON valid sesuai skema tanpa teks luar JSON.\
"""


def _persona_instruction(persona: PersonaStyle) -> str:
    if persona == PersonaStyle.ANTUSIAS:
        return "Racun Affiliate Edukatif & Antusias: enerjik, meyakinkan, padat fakta menarik produk."
    if persona == PersonaStyle.ELEGAN:
        return "Reviewer Spesialis / Profesional: tenang, artikulasi rapi, bedah kualitas material & fungsi secara berkelas."
    return "Teman Jujur Paham Produk: akrab, jujur membahas detail bahan/fungsi nyata dan menjawab keraguan pembeli."


def _split_avatar_tag(raw_tag: str) -> tuple[str, str]:
    raw = (raw_tag or "").strip()
    if not raw:
        return "@me", ""
    m = re.search(r"@[A-Za-z0-9_]+", raw)
    if m:
        handle = m.group(0)
        traits = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        traits = re.sub(r"^[,;\s]+|[,;\s]+$", "", traits)
        traits = re.sub(r"\s+", " ", traits)
        return handle, traits
    return "@me", raw


def _presence_instruction(profile: TalentSavedProfile) -> str:
    handle, traits = _split_avatar_tag(profile.avatar_flow_tag)
    trait_info = f", ciri tambahan: {traits}" if traits else ""
    extra = f" (outfit konsisten: {profile.visual_notes.strip()})" if profile.visual_notes.strip() else ""
    if profile.talent_presence == TalentPresence.FACELESS_BROLL:
        return (
            "TANPA WAJAH / FOKUS B-ROLL DETAIL PRODUK & TANGAN INDONESIA: Seluruh prompt Flow HANYA menampilkan produk utuh dan tangan berkulit sawo matang hangat khas Indonesia "
            f"(gunakan frasa positif di flow_prompt_en tanpa menulis kata 'no human face'){extra}."
        )
    if profile.talent_presence == TalentPresence.AVATAR_HIJAB_ID:
        return (
            f"GUNAKAN AVATAR GOOGLE FLOW {handle} (WANITA BERHIJAB ASLI INDONESIA): "
            f"WAJIB tulis token berdiri sendiri {handle} (dengan spasi, bukan dalam kurung) sebagai pelaku aksi di `locked_visual_bible_en` dan SETIAP `flow_prompt_en`. "
            "Di `flow_prompt_en`, tegaskan secara POSITIF: authentic native Indonesian Nusantara female creator wearing a neat hijab, warm Indonesian skin tone, dark brown eyes "
            f"(jangan tulis kata 'Western'/'Caucasian'/'do not' di dalam prompt){trait_info}{extra}."
        )
    if profile.talent_presence == TalentPresence.AVATAR_MALE_ID:
        return (
            f"GUNAKAN AVATAR GOOGLE FLOW {handle} (PRIA ASLI INDONESIA): "
            f"WAJIB tulis token berdiri sendiri {handle} (dengan spasi, bukan dalam kurung) sebagai pelaku aksi di `locked_visual_bible_en` dan SETIAP `flow_prompt_en`. "
            "Di `flow_prompt_en`, tegaskan secara POSITIF: authentic native Indonesian Nusantara male creator, warm sawo-matang skin tone, neat short black hair, dark brown eyes "
            f"(jangan tulis kata 'Western'/'Caucasian'/'do not' di dalam prompt){trait_info}{extra}."
        )
    return (
        f"GUNAKAN AVATAR GOOGLE FLOW {handle} (WANITA ASLI INDONESIA): "
        f"WAJIB tulis token berdiri sendiri {handle} (dengan spasi, bukan dalam kurung) sebagai pelaku aksi di `locked_visual_bible_en` dan SETIAP `flow_prompt_en`. "
        "Di `flow_prompt_en`, tegaskan secara POSITIF: authentic native Indonesian Nusantara female creator, warm Indonesian skin tone, dark black hair, dark brown eyes "
        f"(jangan tulis kata 'Western'/'Caucasian'/'do not' di dalam prompt){trait_info}{extra}."
    )


def _platform_cta_rule(platform_mode: PlatformMode) -> str:
    if platform_mode == PlatformMode.TIKTOK:
        return "Target utama TikTok Shop: gunakan CTA 'Keranjang Kuning' di VO penutup, dan isi lengkap `tiktok_caption_and_hashtags`."
    if platform_mode == PlatformMode.BOTH:
        return (
            "Target ganda Shopee Video & TikTok Shop: gunakan CTA netral 'cek keranjang di bawah' di dalam VO agar 1 video bisa dipakai di kedua platform, "
            "serta isi lengkap KEDUA field `shopee_caption_and_hashtags` dan `tiktok_caption_and_hashtags`."
        )
    return "Target utama Shopee Video: gunakan CTA 'Keranjang Oranye' atau 'Tautan Produk di bawah' (DILARANG menulis 'Keranjang Kuning')."


def _roles_plan_for_count(scene_count: int) -> str:
    if scene_count >= 7:
        return (
            "Scene 1: Hook Tajam (New Scene), "
            "Scene 2: Masalah Nyata Pembeli, "
            "Scene 3: Bedah Material / Kandungan Spesifik (Macro Jump to), "
            "Scene 4: Demo Cara Kerja / Mekanisme Produk, "
            "Scene 5: Objection Killer (Jawab Keraguan Utama Pembeli), "
            "Scene 6: Tips Pakai Pro & Value Jangka Panjang, "
            "Scene 7: CTA Persuasif"
        )
    if scene_count == 5:
        return (
            "Scene 1: Hook Tajam (New Scene), "
            "Scene 2: Masalah Pembeli, "
            "Scene 3: Bedah Spek / Material & Demo Nyata, "
            "Scene 4: Objection Killer & Manfaat Utama, "
            "Scene 5: CTA Persuasif"
        )
    return (
        "Scene 1: Hook Spesifik (New Scene), "
        "Scene 2: Bedah Spek Utama & Demo Bukti Nyata (Jump to / Extend), "
        "Scene 3: Jawaban Keraguan Singkat + CTA"
    )


def build_blueprint_messages(
    product_image_urls: list[str],
    profile: TalentSavedProfile,
    scene_count: int = 5,
    extra_note: str = "",
    previous_hooks: list[str] | None = None,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    knowledge_context_text: str = "",
) -> list[dict[str, Any]]:
    """Build single-shot multimodal prompt enriched with website/store Product Knowledge."""
    schema_hint = json.dumps(BlueprintResponse.model_json_schema(), ensure_ascii=False, indent=2)
    roles_plan = _roles_plan_for_count(scene_count)

    anti_spam_block = ""
    if previous_hooks:
        joined = "\n".join(f"- {h}" for h in previous_hooks[-8:])
        anti_spam_block = (
            "\nANTI-SPAM / ANTI-DUPLIKAT LINTAS SESI: Produk ini sudah pernah dibuatkan video. "
            "WAJIB buat Hook Scene 1, sudut bedah produk, dan kalimat narasi yang BERBEDA TOTAL dari daftar hook lama berikut:\n"
            f"{joined}\n"
        )

    knowledge_block = ""
    if knowledge_context_text.strip():
        knowledge_block = (
            "\nSUMBER PENGETAHUAN PRODUK TAMBAHAN (WEBSITE / SPESIFIKASI TOKO / RISET WEB):\n"
            f"{knowledge_context_text.strip()}\n"
            "Gunakan fakta teknis, bahan, ukuran, cara pakai, dan detail di atas secara maksimal sebagai ADDED VALUE di dalam `product_knowledge` dan `vo_script_id` setiap scene!\n"
        )

    if (
        profile.location_mode == LocationLockMode.LOCKED_CUSTOM
        and profile.custom_location.strip()
    ):
        location_rule = f"KUNCI LOKASI TETAP di Visual Bible: {profile.custom_location.strip()}"
    else:
        location_rule = (
            "PILIH 1 LOKASI OTOMATIS PALING KONTEKSTUAL sesuai kategori produk "
            "(contoh: halaman rumput / teras outdoor sore hari untuk produk camping/outdoor, meja rias cerah untuk skincare, dapur minimalis untuk alat masak) "
            "dan kunci 1 lokasi tersebut untuk SELURUH scene dari awal sampai akhir!"
        )

    user_prompt = f"""
Analisis produk secara mendalam dari gambar yang dilampirkan beserta data referensi tambahan, lalu buat Blueprint Produksi Bernilai Tambah Tinggi ({scene_count} Scene: {roles_plan}) rasio 9:16 untuk alur Google Flow -> CapCut.

Preferensi Visual & Gaya Narasi:
- Tipe Subjek di Google Flow: {_presence_instruction(profile)}
- Gaya Bicara VO (untuk CapCut): {_persona_instruction(profile.persona)}
- Aturan Lokasi Visual Bible: {location_rule}
- Aturan Platform: {_platform_cta_rule(platform_mode)}

Catatan Tambahan Produk / Promo dari Pengguna:
{extra_note.strip() or "(ekstrak detail selengkap-lengkapnya dari gambar produk & sumber pengetahuan di bawah)"}
{knowledge_block}{anti_spam_block}
Checklist Kualitas, Anti-Halu Produk & Identitas Avatar Indonesia Wajib:
- Isi `flow_setup.exact_product_geometry_lock_en` dengan deskripsi geometri fisik PERSIS yang terlihat di foto produk (struktur & jumlah kaki/rangka/botol, warna material, sambungan, permukaan, posisi & isi logo) memakai kalimat positif tanpa kata kutip ganda `"`.
- Di `flow_prompt_en`: susun prosa sinematik Bahasa Inggris 5-bagian (~80-135 kata), TANPA kurung siku `[...]`, TANPA tanda kutip `"`, dan TANPA kata negasi (`do not`, `no Western`, `no Caucasian`, `broken`, `damaged`, `fold`, `music`, `dialogue`).
- Setiap `flow_prompt_en` WAJIB: (1) satu aksi mikro 5 detik + kontak permukaan fisik yang mantap, (2) awali adegan `Extend` dengan `Seamless continuation from the previous frame,`, (3) jika memakai Avatar wajib menulis token berdiri sendiri `@me` disertai deskripsi positif Nusantara Indonesia.
- Isi `product_knowledge` secara mendalam dan konkret (bedah material/kandungan, tips pakai pro, profil pembeli ideal, jawaban keraguan utama pembeli, pembeda dari kompetitor, dan `pinned_comment_faq_id` siap tempel di kolom komentar).
- Jumlah item di `scenes` TEPAT {scene_count} scene (1 s.d. {scene_count}).
- Setiap `vo_script_id` WAJIB **12-16 kata** Bahasa Indonesia natural yang menyebut detail nyata produk (bukan pujian umum kosong!).
- JANGAN PERNAH menggambarkan produk referensi dalam keadaan rusak/goyang/cacat di scene mana pun.
- Semua hashtag bebas spasi internal (`#KursiLipat #ShopeeVideo`).

Kembalikan HANYA JSON valid sesuai skema berikut:
{schema_hint}
""".strip()

    content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
    for url in product_image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})

    return [
        {"role": "system", "content": COMMERCIAL_DIRECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def build_regenerate_hook_messages(
    blueprint: BlueprintResponse,
    profile: TalentSavedProfile,
    previous_hooks: list[str],
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
) -> list[dict[str, Any]]:
    """Build focused prompt to regenerate Scene 1 Hook using a fresh Product Knowledge angle."""
    schema_hint = json.dumps(RegeneratedHookPayload.model_json_schema(), ensure_ascii=False, indent=2)
    scene_2_summary = (
        blueprint.scenes[1].model_dump_json(indent=2)
        if len(blueprint.scenes) >= 2
        else "{}"
    )
    used_hooks = "\n".join(f"- {h}" for h in previous_hooks[-10:]) or f"- {blueprint.scenes[0].vo_script_id}"
    specs_summary = "; ".join(blueprint.product_knowledge.technical_specs_and_materials)

    prompt = f"""
Buat ulang HANYA Scene 1 (Hook) dengan sudut pandang edukatif / rasa penasaran berbasis Product Knowledge baru agar menjadi variasi video baru (anti-spam), TANPA mengubah lokasi di Visual Bible dan tetap menyambung mulus ke Scene 2!

Produk: {blueprint.product_analysis.product_name} ({blueprint.product_analysis.category})
Fakta Teknis & Material Produk: {specs_summary or ", ".join(blueprint.product_analysis.usp)}
Keraguan Utama Pembeli: {blueprint.product_knowledge.top_buyer_objection_and_answer}
Tipe Subjek: {_presence_instruction(profile)}
Gaya Bicara VO: {_persona_instruction(profile.persona)}
Aturan Platform: {_platform_cta_rule(platform_mode)}

Locked Visual Bible (WAJIB disertakan penuh di dalam `scene_1.flow_prompt_en`):
{blueprint.flow_setup.locked_visual_bible_en}

Data Scene 2 Saat Ini (akhir Scene 1 baru HARUS menyambung logis ke pembuka Scene 2 ini):
{scene_2_summary}

Daftar Hook Lama yang DILARANG Diulang:
{used_hooks}

Aturan Ketat:
- `scene_1.scene_number` = 1, `scene_1.role` = "Hook", `scene_1.flow_action` = "New Scene", `scene_1.duration_sec` = 5.
- Tulis `scene_1.flow_prompt_en` dalam Bahasa Inggris prosa 5-bagian (~80-135 kata), TANPA kurung siku `[...]`, TANPA tanda kutip `"`, dan HANYA kalimat positif (tanpa kata `do not`, `no`, `Western`, `Caucasian`, `fold`, `broken`, `music`).
- Jika memakai Avatar, wajib tulis token berdiri sendiri `@me` (dengan spasi) sebagai subjek pelaku dengan ciri positif asli Nusantara Indonesia.
- `scene_1.vo_script_id` WAJIB kalimat Bahasa Indonesia natural **12-16 kata** yang punya nilai tambah informasi (bukan kode ID).
- `scene_1.on_screen_text_id` maksimal **5 kata**.

Kembalikan HANYA JSON valid sesuai skema berikut:
{schema_hint}
""".strip()

    return [
        {"role": "system", "content": COMMERCIAL_DIRECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


_DEMO_HOOK_VARIANTS: list[dict[str, str]] = [
    {
        "hook_angle": "Bedah Alasan Niacinamide 5% Nggak Bikin Perih",
        "continuity": "Tangan mengangkat botol serum asli ke arah lensa kamera memperlihatkan label 5% Niacinamide + Ceramide sebelum masuk ke Scene 2.",
        "action_en": (
            "Dynamic stop-scroll macro opening: a clean hand lifts the exact referenced frosted dropper bottle into crisp foreground focus, "
            "highlighting the minimalist 5% Niacinamide + Ceramide front label in warm morning light"
        ),
        "vo_id": "Banyak yang belum tahu kenapa konsentrasi Niacinamide lima persen paling pas dipakai harian!",
        "ost_id": "Kenapa Niacinamide 5% pas?",
        "s2_bridge": "Menyambung langsung dari botol di depan kamera menuju adegan berikutnya.",
    },
    {
        "hook_angle": "Tes Tekstur Water-Base Bebas Pilling Sunscreen",
        "continuity": "Tangan mengetuk pelan botol kaca pipet produk lalu memutar tutupnya untuk menyambung ke tetesan tekstur di Scene 2.",
        "action_en": (
            "Crisp stop-scroll close-up: hands hold the exact referenced bottle near the lens, "
            "gently tap the frosted glass bottle, and begin twisting open the clean dropper cap"
        ),
        "vo_id": "Sering ngalamin sunscreen menggumpal pagi hari gara-gara salah pilih tekstur dasar serum wajah?",
        "ost_id": "Sunscreen sering menggumpal?",
        "s2_bridge": "Menyambung mulus dari gerakan tangan membuka tutup pipet menuju adegan berikutnya.",
    },
    {
        "hook_angle": "Kombinasi Niacinamide + Ceramide untuk Skin Barrier",
        "continuity": "Produk digeser anggun di atas meja terang ke fokus utama sebelum masuk ke pembahasan detail Scene 2.",
        "action_en": (
            "Engaging commercial shot: soft morning sunlight sweeps across the vanity table "
            "as a hand brings the exact referenced dropper bottle smoothly into foreground focus"
        ),
        "vo_id": "Jangan cuma lihat persentase tinggi, cek dulu ada pendamping Ceramide di botolnya nggak!",
        "ost_id": "Cek kandungan pendampingnya!",
        "s2_bridge": "Menyambung dari posisi botol di foreground akhir Scene 1 langsung ke adegan berikutnya.",
    },
]


def build_offline_demo_blueprint(
    profile: TalentSavedProfile,
    scene_count: int = 5,
    extra_note: str = "",
    variation_index: int = 0,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
) -> BlueprintResponse:
    """Deterministic commercial-grade demo blueprint with Deep Product Knowledge (supports 3, 5, or 7 scenes)."""
    variant = _DEMO_HOOK_VARIANTS[variation_index % len(_DEMO_HOOK_VARIANTS)]
    custom_note = extra_note.strip()
    prod_name = (
        custom_note[:55]
        if custom_note and len(custom_note.split()) <= 6
        else "LumiGlass Niacinamide 5% + Ceramide NP Serum 30ml"
    )
    promo_info = custom_note if custom_note else "Harga promo etalase + voucher gratis ongkir"

    avatar_handle, avatar_traits = _split_avatar_tag(profile.avatar_flow_tag)
    traits_clause = f", {avatar_traits}" if avatar_traits else ""
    if profile.talent_presence == TalentPresence.FACELESS_BROLL:
        subject_desc = (
            "clean well-groomed warm medium-tan Indonesian hands only in frame, "
            "keeping visual focus solely on the pristine bottle and smooth skin"
        )
        actor_ref = "clean warm medium-tan Indonesian hands"
    elif profile.talent_presence == TalentPresence.AVATAR_HIJAB_ID:
        subject_desc = (
            f"{avatar_handle}, an authentic native Indonesian female creator with Nusantara Southeast Asian facial features, "
            f"warm Indonesian skin tone, dark brown eyes, neat cream pashmina hijab, and casual linen top{traits_clause}, "
            f"preserving the exact 1:1 facial identity of {avatar_handle}"
        )
        actor_ref = f"{avatar_handle}"
    elif profile.talent_presence == TalentPresence.AVATAR_MALE_ID:
        subject_desc = (
            f"{avatar_handle}, an authentic native Indonesian male creator with Nusantara Southeast Asian facial features, "
            f"warm sawo-matang Indonesian skin tone, neat short black hair, dark brown eyes, and casual olive linen shirt{traits_clause}, "
            f"preserving the exact 1:1 facial identity of {avatar_handle}"
        )
        actor_ref = f"{avatar_handle}"
    else:
        subject_desc = (
            f"{avatar_handle}, an authentic native Indonesian female creator with Nusantara Southeast Asian facial features, "
            f"warm Indonesian skin tone, natural dark black hair, dark brown eyes, and neat cream linen casual shirt{traits_clause}, "
            f"preserving the exact 1:1 facial identity of {avatar_handle}"
        )
        actor_ref = f"{avatar_handle}"

    geometry_lock = (
        "Exact cylindrical 30ml frosted matte glass dropper bottle with white rubber bulb, "
        "silver collar ring, and clean black front label showing 5% Niacinamide and Ceramide, "
        "maintaining locked static geometry and original bottle proportions"
    )
    setting_desc = (
        profile.custom_location.strip()
        if profile.location_mode == LocationLockMode.LOCKED_CUSTOM and profile.custom_location.strip()
        else "sunlit minimalist Indonesian room with soft morning window light"
    )
    visual_bible = (
        f"Vertical 9:16 commercial video shot on 35mm f/1.8 lens in a {setting_desc}, "
        f"clean neutral warm beige-white color grading, featuring {subject_desc}, "
        f"with {geometry_lock.lower()}"
    )
    audio_cue = "Audio: quiet natural ambient soundscape and crisp realistic product foley only, silent presenter."

    cta_phrase = (
        "keranjang kuning"
        if platform_mode == PlatformMode.TIKTOK
        else ("keranjang di bawah" if platform_mode == PlatformMode.BOTH else "keranjang oranye")
    )

    scene_1 = FlowScene(
        scene_number=1,
        role="Hook",
        flow_action="New Scene",
        duration_sec=5,
        continuity_note=variant["continuity"],
        flow_prompt_en=(
            f"Vertical 9:16 commercial frame, 35mm f/1.8 macro shot. {subject_desc}. "
            f"{geometry_lock}. {variant['action_en']} inside the {setting_desc}. "
            f"{audio_cue}"
        ),
        vo_script_id=variant["vo_id"],
        on_screen_text_id=variant["ost_id"],
    )

    if scene_count >= 7:
        scenes = [
            scene_1,
            FlowScene(
                scene_number=2,
                role="Problem",
                flow_action="Extend",
                duration_sec=5,
                continuity_note=variant["s2_bridge"],
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame, gentle slow push-in. "
                    f"{subject_desc}. {geometry_lock}. {actor_ref} holds the pristine referenced bottle steadily against the bright morning air of the {setting_desc}. "
                    f"{audio_cue}"
                ),
                vo_script_id="Dosis terlalu tinggi kadang bikin kulit kaget, sedangkan gel kental bikin gerah seharian.",
                on_screen_text_id="Takut perih atau lengket?",
            ),
            FlowScene(
                scene_number=3,
                role="Bedah Spek",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke sudut makro botol kaca frosted 30ml dan pipet kaca higienis.",
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, 50mm macro close-up shot. {subject_desc}. "
                    f"{geometry_lock}, resting solidly with firm contact on sunlit travertine stone inside the {setting_desc}. "
                    f"Soft golden light sweeps gently over the frosted bottle shoulder. {audio_cue}"
                ),
                vo_script_id="Di botol kaca tiga puluh mili ini, Niacinamide lima persen dipadukan langsung sama Ceramide.",
                on_screen_text_id="5% Niacinamide + Ceramide",
            ),
            FlowScene(
                scene_number=4,
                role="Demo",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Cut makro ke pipet yang meneteskan tekstur cair bening di punggung tangan.",
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, extreme macro close-up shot. {subject_desc}. "
                    f"{geometry_lock}. {actor_ref} releases two crystal-clear water-light drops onto skin inside the {setting_desc}, "
                    f"absorbing evenly into a fresh satin surface. {audio_cue}"
                ),
                vo_script_id="Basisnya cair seenteng air tanpa pewangi tambahan, jadi meresap hitungan detik tanpa residu.",
                on_screen_text_id="Water-base tanpa lengket",
            ),
            FlowScene(
                scene_number=5,
                role="Objection Killer",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus saat jari menepuk lembut kulit yang sudah meresap siap ditimpa sunscreen.",
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame. {subject_desc}. "
                    f"{geometry_lock} planted solidly on the stone counter inside the {setting_desc}. "
                    f"Fingertips press gently across the smooth matte-hydrated skin surface. {audio_cue}"
                ),
                vo_script_id="Aman ditumpuk sunscreen pagi maupun moisturizer malam tanpa bikin makeup menggumpal sama sekali.",
                on_screen_text_id="Aman ditumpuk sunscreen!",
            ),
            FlowScene(
                scene_number=6,
                role="Benefit",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Kamera bergerak lembut menampilkan kilau lembap sehat dan botol produk utuh.",
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame, slow smooth arc orbit. {subject_desc}. "
                    f"{geometry_lock} beside a sunlit mirror inside the {setting_desc}, highlighting radiant healthy skin. "
                    f"{audio_cue}"
                ),
                vo_script_id="Cukup dua sampai tiga tetes rutin buat bantu merawat kulit kusam dan kelembapan.",
                on_screen_text_id="Hemat 2-3 tetes sehari",
            ),
            FlowScene(
                scene_number=7,
                role="CTA",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke hero shot penutup botol berdiri tegak dengan gestur ajakan ke tautan produk bawah.",
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, clean eye-level hero shot. {subject_desc}. "
                    f"{geometry_lock} standing upright with firm base contact on the sunlit table inside the {setting_desc}, "
                    f"as {actor_ref} gestures cleanly toward the lower screen link area. {audio_cue}"
                ),
                vo_script_id=f"Detail spek lengkapnya udah aku tulis di komentar, langsung cek {cta_phrase} sekarang ya!",
                on_screen_text_id="Cek spek & promo bawah!",
            ),
        ]
    elif scene_count == 5:
        scenes = [
            scene_1,
            FlowScene(
                scene_number=2,
                role="Problem",
                flow_action="Extend",
                duration_sec=5,
                continuity_note=variant["s2_bridge"],
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame, smooth gentle push-in. {subject_desc}. "
                    f"{geometry_lock}. {actor_ref} holds the pristine referenced bottle steadily in the bright {setting_desc}. "
                    f"{audio_cue}"
                ),
                vo_script_id="Serum yang terlalu kental sering bikin wajah gerah dan sunscreen jadi gampang menggumpal.",
                on_screen_text_id="Sunscreen sering menggumpal?",
            ),
            FlowScene(
                scene_number=3,
                role="Bedah Spek & Demo",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke sudut close-up makro tangan meneteskan tekstur water-base dari botol kaca 30ml.",
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, 50mm macro close-up cut. {subject_desc}. "
                    f"{geometry_lock}. {actor_ref} dispenses two clear watery drops onto clean skin inside the {setting_desc} "
                    f"until blended into a weightless finish. {audio_cue}"
                ),
                vo_script_id="Formula water-base ini memadukan Niacinamide lima persen dan Ceramide yang meresap hitungan detik.",
                on_screen_text_id="5% Niacinamide + Ceramide",
            ),
            FlowScene(
                scene_number=4,
                role="Objection Killer",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus dari kulit yang lembap halus siap ditimpa sunscreen tanpa lengket.",
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame. {subject_desc}. "
                    f"{geometry_lock} resting firmly in hand inside the sunlit {setting_desc} alongside fresh matte-hydrated skin sheen. "
                    f"{audio_cue}"
                ),
                vo_script_id="Tanpa pewangi menyengat dan aman dilayer sunscreen pagi buat bantu merawat kulit kusam.",
                on_screen_text_id="Aman dilayer pagi & malam",
            ),
            FlowScene(
                scene_number=5,
                role="CTA",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke hero shot produk berdiri rapi di atas meja terang dengan gestur ajakan cek tautan produk bawah.",
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, clean hero closing shot. {subject_desc}. "
                    f"{geometry_lock} planted upright on the sunlit table inside the {setting_desc}, "
                    f"as {actor_ref} gestures clearly toward the lower link area. {audio_cue}"
                ),
                vo_script_id=f"Rangkuman speknya ada di komentar pertama, yuk langsung klik {cta_phrase} mumpung promo!",
                on_screen_text_id="Cek promo sekarang!",
            ),
        ]
    else:
        scenes = [
            scene_1,
            FlowScene(
                scene_number=2,
                role="Bedah Spek & Demo",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note=variant["s2_bridge"],
                flow_prompt_en=(
                    f"Vertical 9:16 commercial frame, 50mm macro close-up shot. {subject_desc}. "
                    f"{geometry_lock}. {actor_ref} dispenses two crystal-clear watery drops onto skin inside the {setting_desc} "
                    f"while holding the front label sharp toward the lens. {audio_cue}"
                ),
                vo_script_id="Basis airnya memadukan Niacinamide lima persen dan Ceramide, meresap cepat tanpa mengganggu sunscreen.",
                on_screen_text_id="5% Niacinamide water-base",
            ),
            FlowScene(
                scene_number=3,
                role="CTA",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus saat tangan meletakkan botol utuh di meja terang dan menunjuk ke arah tautan produk bawah.",
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, vertical 9:16 commercial frame, smooth pull-back reveal. {subject_desc}. "
                    f"{geometry_lock} resting squarely on the sunlit table inside the {setting_desc} "
                    f"as {actor_ref} points gently toward the lower screen area. {audio_cue}"
                ),
                vo_script_id=f"Ukuran tiga puluh milinya awet sebulan lebih, langsung cek {cta_phrase} mumpung promo!",
                on_screen_text_id="Awet 30ml · Cek bawah!",
            ),
        ]

    full_vo = " ".join(s.vo_script_id for s in scenes)
    knowledge = ProductKnowledgeBrief(
        technical_specs_and_materials=[
            "Kandungan utama: Niacinamide 5% (sweet-spot harian minim risiko iritasi pemula) + Ceramide NP penjaga barrier",
            "Tekstur & Pelarut: Water-based ringan cepat meresap, bebas residu minyak (non-greasy)",
            "Kemasan: Botol kaca frosted 30ml (estimasi pemakaian rutin 4-6 minggu untuk 2-3 tetes/pakai)",
            "Kompatibilitas Layering: Aman dipakai pagi sebelum sunscreen maupun malam sebelum moisturizer",
        ],
        how_it_works_or_usage_tip=(
            "Gunakan 2-3 tetes pada kulit setengah lembap setelah cuci muka, tunggu 15-20 detik hingga meresap rata baru timpa sunscreen agar tidak menggumpal (pilling)."
        ),
        honest_pros_and_ideal_buyer=(
            "Paling cocok untuk pemula, pemilik kulit kombinasi-berminyak di iklim panas, atau pekerja aktif yang butuh serum pagi cepat meresap."
        ),
        top_buyer_objection_and_answer=(
            "Tanya: 'Apakah lengket kalau ditimpa sunscreen/bedak?' — Jawab: Tidak, karena basisnya cair seperti air sehingga langsung menyatu di kulit dalam hitungan detik."
        ),
        competitor_differentiator_angle=(
            "Affiliator lain hanya bilang 'serum pencerah murah', sedangkan kita membedah alasan ilmiah dosis 5% + Ceramide serta bukti anti-pilling di bawah sunscreen."
        ),
        pinned_comment_faq_id=(
            f"📌 Rangkuman Cepat {prod_name}:\n"
            "• Kandungan: 5% Niacinamide + Ceramide NP (nyaman buat harian)\n"
            "• Tekstur: Cair ringan kayak air, nggak bikin sunscreen menggumpal\n"
            "• Isi: 30ml (awet ~1-1.5 bulan pemakaian pagi/malam)\n"
            "• Cara pakai: 2-3 tetes sebelum moisturizer/sunscreen. Cek voucher promo aktif di keranjang ya!"
        ),
    )

    return BlueprintResponse(
        product_analysis=ProductAnalysis(
            product_name=prod_name,
            category="Skincare & Perawatan Wajah",
            price_or_promo=promo_info,
            usp=[
                "Dosis ideal Niacinamide 5% + Ceramide NP yang ramah dipakai tiap hari",
                "Tekstur watery cepat meresap dan anti-pilling saat ditimpa sunscreen",
                "Kemasan botol kaca pipet frosted 30ml awet 4-6 minggu",
            ],
            pain_points=[
                "Serum kental bikin wajah gerah dan membuat sunscreen menggumpal",
                "Takut iritasi kalau langsung memakai serum dosis terlalu tinggi",
            ],
            target_audience="Wanita & pria aktif usia 18-34 tahun pencari skincare harian ringan terukur",
            hook_angle=variant["hook_angle"],
            recommended_setting_id="Meja rias minimalis dekat jendela cahaya pagi",
            is_sensitive_category=True,
        ),
        product_knowledge=knowledge,
        flow_setup=FlowSetup(
            ingredients_checklist=[
                "Foto Produk Bersih (gunakan hasil crop bebas UI Shopee)"
            ],
            aspect_ratio="9:16",
            exact_product_geometry_lock_en=geometry_lock,
            locked_visual_bible_en=visual_bible,
        ),
        scenes=scenes,
        capcut_finishing=CapCutFinishing(
            full_vo_script_id=full_vo,
            bgm_vibe_suggestion="Lo-fi acoustic edukatif / clean morning routine (volume tipis 8-10% agar detail spek VO terdengar jernih)",
            pacing_tips=(
                "Gabungkan klip hasil Flow di CapCut, tambahkan wajah/suara Anda (atau import vo_capcut.mp3 + capcut_subtitles.srt gratis), "
                "dan TEMPEL teks Pinned Comment di kolom komentar pertama begitu video terbit untuk mendongkrak konversi!"
            ),
            shopee_caption_and_hashtags=(
                f"Bedah lengkap {prod_name}: kenapa dosis 5% Niacinamide + Ceramide justru paling nyaman dipakai harian tanpa bikin sunscreen menggumpal! "
                "Cek spek lengkap di komentar pertama & klik Tautan Produk di bawah buat klaim promonya ya! "
                "#RacunShopee #ShopeeVideo #ReviewJujurSkincare #SkincareEdukasi #SerumNiacinamide"
            ),
            tiktok_caption_and_hashtags=(
                f"Alasan {prod_name} nyaman dipakai pagi sebelum sunscreen tanpa rasa lengket! Bedah kandungan & tips pakainya ada di video. "
                "Cek promo aktifnya di Keranjang Kuning sekarang! "
                "#TikTokShopAffiliate #ReviewSkincareJujur #SerumNiacinamide #EdukasiSkincare #FYPIndonesia"
            ),
            compliance_reminder="Wajib aktifkan label 'Konten Buatan AI' saat upload di Shopee Video / TikTok Shop.",
        ),
    )


def build_offline_demo_regenerated_hook(
    blueprint: BlueprintResponse,
    variation_index: int = 1,
) -> RegeneratedHookPayload:
    """Return a distinct positive-framed Scene 1 Hook payload for Offline Demo Mode."""
    variant = _DEMO_HOOK_VARIANTS[variation_index % len(_DEMO_HOOK_VARIANTS)]
    bible = blueprint.flow_setup.locked_visual_bible_en
    geo = blueprint.flow_setup.exact_product_geometry_lock_en
    new_s1 = FlowScene(
        scene_number=1,
        role="Hook",
        flow_action="New Scene",
        duration_sec=5,
        continuity_note=variant["continuity"],
        flow_prompt_en=(
            f"Vertical 9:16 commercial frame, 35mm macro opening. {bible}. {geo}. "
            f"{variant['action_en']}. "
            "Audio: quiet natural ambient soundscape and crisp realistic product foley only, silent presenter."
        ),
        vo_script_id=variant["vo_id"],
        on_screen_text_id=variant["ost_id"],
    )
    return RegeneratedHookPayload(
        hook_angle=variant["hook_angle"],
        scene_1=new_s1,
        scene_2_continuity_note=variant["s2_bridge"],
    )
