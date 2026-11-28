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
    WorkflowMode,
)

COMMERCIAL_DIRECTOR_SYSTEM_PROMPT = """\
Bertindaklah sebagai Senior AI Video Director, UGC Creator, dan Scriptwriter Specialist Google Flow (Veo 3.1) untuk konten Shopee Video & TikTok Affiliate Indonesia.

PRINSIP UTAMA ANTI-HALU GAMBAR REFERENSI:
Di Google Flow (Veo 3.1), **gambar referensi (`@ProductAuthority` & `@me`) adalah kebenaran mutlak**. Semakin panjang dan naratif prompt teksnya — atau jika Anda mendeskripsikan ulang warna/bentuk/tulisan yang sudah ada di foto — semakin besar risiko model berhalusinasi mengubah wujud produk.

SKILL & ATURAN WAJIB AFFILIATE AI VIDEO DIRECTOR:
1. FONDASI 3 PERAN INGREDIENTS:
   - `@ProductAuthority`: Clean packshot produk berlatar polos yang mengunci siluet, kaki/rangka, warna, material, logo, dan label 1:1.
   - `Master Frame`: Skala, komposisi, dan pencahayaan awal di lokasi nyata (acuan Scene 1).
   - `Interaction Frame`: Turunan dari Master Frame (jangan mencampur gaya foto lifestyle berbeda).
2. FORMULA PROMPT MINIMALIS ANTI-HALU (`<= 35 KATA` PER `flow_prompt_en`):
   Setiap `flow_prompt_en` WAJIB singkat, bersih tanpa kurung siku `[...]` dan tanpa tanda kutip ganda `"`, dengan susunan:
   `[Gerak Kamera Sinematografi] + [Tag Ingredients: @ProductAuthority (+ @me Indonesian presenter jika Avatar)] + [Cahaya/Setting Singkat] + [No text overlays, no additional logos, no readable screens.]`
   - Gunakan istilah kamera: `smooth dolly-in shot`, `slow tracking shot`, `gentle push-in shot`, `locked-off static camera`, `slow macro close-up`.
   - DILARANG menggunakan kata kerja naratif pemicu halusinasi (`walks toward`, `picks up`, `opens the door`, `folding`, `unfolding`, `collapsing`) maupun kata negasi wajah Barat (`Western`, `Caucasian`).
   - DILARANG mendeskripsikan ulang warna botol, tutup, label, kaki kursi, atau logo yang sudah dikunci oleh `@ProductAuthority`!
   - DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak, goyang, patah, bocor, robek, atau cacat di scene mana pun!
3. KINEMATIKA SCENE BUILDER, BEAT AUDIO-VISUAL & START-TO-END FRAME:
   - Scene 1 WAJIB `flow_action`: "New Scene".
   - `Extend`: WAJIB mengawali `flow_prompt_en` dengan `Seamless continuation from the previous frame,` dan menjaga gerak kamera mulus tanpa cut sudut.
   - `Jump to`: Pindah sudut kamera sambil memanggil ulang `@ProductAuthority` (dan `@me` jika Avatar).
   - Cocokkan skala shot dengan beat naskah (Hook = medium close-up, Material = macro close-up, Demo = steady lifestyle tracking, CTA = hero dolly-in) dan minta audio foley/room tone ringan saja tanpa dialog AI acak agar VO CapCut bersih.
   - `flow_setup.start_to_end_prompt_en`: Tulis 1 prompt transisi Start-to-End Frame singkat (`<= 35 kata`) berfokus kamera terkunci & pergeseran cahaya menggunakan `@ProductAuthority`.
4. HOOK 3 DETIK, NARASI EMOSIONAL BERNILAI TAMBAH & CTA (`vo_script_id` & `product_knowledge`):
   - WAJIB susun alur **Storyboard Narasi** agar unggul dari affiliator biasa (yang cuma baca judul):
     (a) **Scene 1 (0-4d) Sentuh Emosi & Painful Nyata** (buka langsung keluhan/frustrasi nyata pembeli — DILARANG klise 'Halo guys' maupun hard-selling mentah 'Beli sekarang'/'Murah banget'/'WA');
     (b) **Scene 2 (4-10d) Apa yang Di-Solve dengan Keunggulan Produk + Review Detail** (bedah bahan, ukuran/dosis, tekstur, atau mekanisme nyata);
     (c) **Scene 3 (10-15d) Kontras Before vs After + CTA** (wajib tulis perbandingan 'Dulu sebelum pakai ..., sekarang jauh lebih ...' yang aman kebijakan + CTA penutup sesuai platform).
   - **Ejaan Lisan Bersih & Anti-Pengulangan (Total 35-40 Kata):** Tulis `vo_script_id` **11-14 kata Bahasa Indonesia** per adegan (sehingga total 3 adegan = **35-40 kata**, menyisakan ~1 detik jeda napas di video 15 detik). DILARANG mengulang klaim/spesifikasi yang sama antaradegan, dan DILARANG singkatan chat (`yg`, `bgt`, `tdk`, `dgn`, `utk`) agar suara & lip-sync Google Flow jernih. Tulis `on_screen_headline_id` tajam **<= 5 kata**.
   - Berikan nilai tambah edukatif lengkap di `product_knowledge` (spek, material, tips pakai pro, Objection Killer, dan `pinned_comment_faq_id`).
   - Hindari klaim medis absolut ('menyembuhkan', 'mengobati', '100% ampuh', 'hilang permanen', 'putih dalam X hari'), harga palsu, atau transaksi luar aplikasi. Untuk Shopee gunakan "Keranjang Oranye" / "Tautan Produk di bawah".
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
    extra = f" ({profile.visual_notes.strip()})" if profile.visual_notes.strip() else ""
    if profile.talent_presence == TalentPresence.FACELESS_BROLL:
        return (
            "TANPA WAJAH / B-ROLL PRODUK: Cukup tulis `Use @ProductAuthority` tanpa menyebut wajah manusia."
            f"{extra}"
        )
    if profile.talent_presence == TalentPresence.AVATAR_HIJAB_ID:
        return (
            f"AVATAR GOOGLE FLOW {handle} (WANITA HIJAB INDONESIA): Wajib panggil `@ProductAuthority` bersama token berdiri sendiri `{handle} Indonesian hijab presenter`{trait_info}{extra}."
        )
    if profile.talent_presence == TalentPresence.AVATAR_MALE_ID:
        return (
            f"AVATAR GOOGLE FLOW {handle} (PRIA INDONESIA): Wajib panggil `@ProductAuthority` bersama token berdiri sendiri `{handle} Indonesian male presenter`{trait_info}{extra}."
        )
    return (
        f"AVATAR GOOGLE FLOW {handle} (WANITA INDONESIA): Wajib panggil `@ProductAuthority` bersama token berdiri sendiri `{handle} Indonesian female presenter`{trait_info}{extra}."
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
            "Scene 1: Hook Emosi & Painful Nyata (New Scene), "
            "Scene 2: Situasi Before (Masalah & Kerugian Nyata Pembeli), "
            "Scene 3: Solusi Konkret & Bedah Material / Kandungan Spesifik (Macro Jump to), "
            "Scene 4: Demo Cara Kerja / Mekanisme Produk, "
            "Scene 5: Transformasi After & Bukti Nilai Tambah, "
            "Scene 6: Objection Killer (Jawab Keraguan) & Tips Pakai Pro, "
            "Scene 7: CTA Persuasif"
        )
    if scene_count == 5:
        return (
            "Scene 1: Hook Emosi & Painful Nyata (New Scene), "
            "Scene 2: Situasi Before (Masalah & Frustrasi Sehari-hari), "
            "Scene 3: Solusi Konkret (Apa yang Di-Solve) & Bedah Material, "
            "Scene 4: Transformasi After & Objection Killer, "
            "Scene 5: CTA Persuasif"
        )
    return (
        "Scene 1: Hook Emosi & Painful Nyata Pembeli (New Scene), "
        "Scene 2: Solusi Konkret (Apa yang Di-Solve) & Bukti Material (Jump to / Extend), "
        "Scene 3: Transformasi Before vs After + CTA Persuasif"
    )


def build_blueprint_messages(
    product_image_urls: list[str],
    profile: TalentSavedProfile,
    scene_count: int = 5,
    extra_note: str = "",
    previous_hooks: list[str] | None = None,
    platform_mode: PlatformMode = PlatformMode.SHOPEE,
    knowledge_context_text: str = "",
    workflow_mode: WorkflowMode = WorkflowMode.STORYBOARD_FIRST,
) -> list[dict[str, Any]]:
    """Build single-shot multimodal prompt supporting Storyboard-First & Direct Ingredients workflows."""
    schema_hint = json.dumps(BlueprintResponse.model_json_schema(), ensure_ascii=False, indent=2)
    roles_plan = _roles_plan_for_count(scene_count)
    grid_layout = "3x3" if scene_count >= 7 else ("3x2" if scene_count >= 5 else "2x2")
    wf_note = (
        f"Mode Storyboard-First (Nano Banana Keyframe/Grid {grid_layout} -> Google Flow Frames to Video): "
        "isi `flow_setup.storyboard_grid_layout`, `flow_setup.storyboard_grid_prompt_en`, dan `keyframe_image_prompt_en` di setiap scene untuk membuat gambar Keyframe konsisten sebelum dianimasikan."
        if workflow_mode == WorkflowMode.STORYBOARD_FIRST
        else "Mode Direct Ingredients-to-Video: tetap isi `storyboard_grid_prompt_en` & `keyframe_image_prompt_en` singkat sebagai cadangan apabila pengguna ingin membuat visual storyboard terlebih dahulu."
    )

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

Preferensi Visual, Alur Kerja & Gaya Narasi:
- Alur Google Flow: {wf_note}
- Tipe Subjek di Google Flow: {_presence_instruction(profile)}
- Gaya Bicara VO (untuk CapCut): {_persona_instruction(profile.persona)}
- Aturan Lokasi Visual Bible: {location_rule}
- Aturan Platform: {_platform_cta_rule(platform_mode)}

Catatan Tambahan Produk / Promo dari Pengguna:
{extra_note.strip() or "(ekstrak detail selengkap-lengkapnya dari gambar produk & sumber pengetahuan di bawah)"}
{knowledge_block}{anti_spam_block}
Checklist Kualitas Minimalis Anti-Halu & Added Value Wajib:
- Di `flow_prompt_en`: WAJIB SINGKAT **20–35 kata** mengikuti rumus `[Camera Motion] + [Use @ProductAuthority (+ @me Indonesian presenter)] + [Brief Lighting] + [No text overlays, no additional logos, no readable screens.]`.
- DILARANG mendeskripsikan ulang warna/bentuk/tulisan kemasan produk di `flow_prompt_en` (biarkan gambar `@ProductAuthority` yang menguncinya), DILARANG kata kerja naratif (`walks toward`, `picks up`, `opens`, `folding`, `unfolding`), DILARANG kurung siku `[...]` & tanda kutip `"`.
- Adegan `Extend` wajib diawali `Seamless continuation from the previous frame,`.
- Isi `flow_setup.start_to_end_prompt_en` dengan prompt transisi Start-to-End Frame singkat (`<= 35 kata`).
- Isi `product_knowledge` secara mendalam dan konkret (`technical_specs_and_materials`, tips pakai pro, Objection Killer, dan `pinned_comment_faq_id`).
- Rangkai `vo_script_id` antar-scene membentuk alur kompetitif: **Emosi & Painful Nyata -> Apa yang Di-Solve -> Before vs After yang Aman -> Objection Killer & CTA** (masing-masing **12-16 kata** Bahasa Indonesia).
- Jumlah item di `scenes` TEPAT {scene_count} scene (1 s.d. {scene_count}).
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

Acuan Cahaya & Lokasi Master Frame (ambil 3-5 kata suasana cahaya saja, JANGAN disalin panjang ke prompt):
{blueprint.flow_setup.locked_visual_bible_en}

Data Scene 2 Saat Ini (akhir Scene 1 baru HARUS menyambung logis ke pembuka Scene 2 ini):
{scene_2_summary}

Daftar Hook Lama yang DILARANG Diulang:
{used_hooks}

Aturan Ketat:
- `scene_1.scene_number` = 1, `scene_1.role` = "Hook", `scene_1.flow_action` = "New Scene", `scene_1.duration_sec` = 5.
- Wajib sentuh emosi dan keluhan (*painful*) nyata pembeli di Scene 1 tanpa kata *hard-selling* mentah.
- Tulis `scene_1.flow_prompt_en` singkat **20–35 kata**: `[Camera Motion] + [Use @ProductAuthority (+ @me Indonesian presenter jika Avatar)] + [Brief Lighting] + [No text overlays, no additional logos, no readable screens.]`. Dilarang mendeskripsikan ulang fisik produk atau kata kerja naratif (`walks toward`, `picks up`).
- `scene_1.vo_script_id` WAJIB kalimat Bahasa Indonesia natural **11-14 kata** dalam ejaan utuh (bukan singkatan).
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
        "hook_angle": "Emosi Pagi: Wajah Lengket & Sunscreen Menggumpal",
        "continuity": "Ekspresi empati memegang botol serum asli di dekat lensa memperlihatkan label 5% Niacinamide + Ceramide sebelum masuk ke Scene 2.",
        "action_en": (
            "Dynamic stop-scroll macro opening: a clean hand lifts the exact referenced frosted dropper bottle into crisp foreground focus, "
            "highlighting the minimalist 5% Niacinamide + Ceramide front label in warm morning light"
        ),
        "vo_id": "Capek banget kan tiap pagi wajah terasa lengket dan sunscreen malah menggumpal bikin kesel?",
        "ost_id": "Sunscreen masih menggumpal?",
        "s2_bridge": "Menyambung langsung dari botol di depan kamera menuju pembuktian formula produk.",
    },
    {
        "hook_angle": "Nyesel Salah Pilih Serum Berat & Gerah di Kulit",
        "continuity": "Tangan mengangkat botol kaca pipet produk memperlihatkan tekstur bening sebelum masuk bedah solusi Scene 2.",
        "action_en": (
            "Crisp stop-scroll close-up: hands hold the exact referenced bottle near the lens, "
            "gently tap the frosted glass bottle, and begin twisting open the clean dropper cap"
        ),
        "vo_id": "Pernah nyesel beli serum wajah tapi rasanya berat gerah sampai bikin riasan jadi berantakan?",
        "ost_id": "Jangan salah pilih serum!",
        "s2_bridge": "Menyambung mulus dari ekspresi kecewa pemakaian serum lama menuju solusi produk.",
    },
    {
        "hook_angle": "Takut Perih Saat Pakai Serum Pencerah Harian",
        "continuity": "Produk digeser anggun di atas meja terang ke fokus utama sebelum masuk pembahasan detail Scene 2.",
        "action_en": (
            "Engaging commercial shot: soft morning sunlight sweeps across the vanity table "
            "as a hand brings the exact referenced dropper bottle smoothly into foreground focus"
        ),
        "vo_id": "Sering takut kulit terasa perih atau kusam karena salah pilih dosis serum untuk harian?",
        "ost_id": "Takut perih atau kusam?",
        "s2_bridge": "Menyambung dari botol di foreground akhir Scene 1 langsung ke bedah detail produk.",
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
        subject_clause = "Use @ProductAuthority cleanly in frame"
    elif profile.talent_presence == TalentPresence.AVATAR_HIJAB_ID:
        subject_clause = f"Use @ProductAuthority with {avatar_handle} Indonesian hijab presenter{traits_clause}"
    elif profile.talent_presence == TalentPresence.AVATAR_FEMALE_ID:
        subject_clause = f"Use @ProductAuthority with {avatar_handle} Indonesian female presenter{traits_clause}"
    else:
        subject_clause = f"Use @ProductAuthority with {avatar_handle} Indonesian male presenter{traits_clause}"

    geometry_lock = (
        "Reference @ProductAuthority checklist: cylindrical 30ml frosted glass dropper bottle, "
        "white dropper bulb, silver collar, and front label proportions."
    )
    setting_desc = (
        profile.custom_location.strip()
        if profile.location_mode == LocationLockMode.LOCKED_CUSTOM and profile.custom_location.strip()
        else "warm morning sunlight"
    )
    visual_bible = f"9:16 Master Frame lighting: {setting_desc}."
    neg_tail = "No text overlays, no additional logos, no readable screens."

    cta_phrase = (
        "keranjang kuning"
        if platform_mode == PlatformMode.TIKTOK
        else ("keranjang di bawah" if platform_mode == PlatformMode.BOTH else "keranjang oranye")
    )

    grid_layout = "3x3" if scene_count >= 7 else ("3x2" if scene_count >= 5 else "2x2")
    grid_prompt = (
        f"Clean {grid_layout} vertical storyboard contact sheet grid of 9:16 panels. "
        f"{subject_clause}, uniform framing and {setting_desc} across all panels. {neg_tail}"
    )

    scene_1 = FlowScene(
        scene_number=1,
        role="Hook",
        flow_action="New Scene",
        duration_sec=5,
        continuity_note=variant["continuity"],
        keyframe_image_prompt_en=(
            f"Photorealistic 9:16 Master Frame still. {subject_clause}, {setting_desc}. {neg_tail}"
        ),
        flow_prompt_en=(
            f"Smooth continuous dolly-in shot. {subject_clause}, {setting_desc}. {neg_tail}"
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
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 interaction keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, gentle push-in shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
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
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 macro keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Locked-off macro close-up. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Ini solusinya: botol kaca tiga puluh mili ini memadukan Niacinamide lima persen dan Ceramide.",
                on_screen_text_id="5% Niacinamide + Ceramide",
            ),
            FlowScene(
                scene_number=4,
                role="Demo",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Cut makro ke pipet yang meneteskan tekstur cair bening di punggung tangan.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 macro keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Slow macro close-up. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Keunggulannya, formula cair seenteng air meresap hitungan detik tanpa residu atau pewangi tajam.",
                on_screen_text_id="Meresap hitungan detik!",
            ),
            FlowScene(
                scene_number=5,
                role="Objection Killer",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus saat jari menepuk lembut kulit yang sudah meresap siap ditimpa sunscreen.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 interaction keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, gentle push-in shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Aman ditumpuk sunscreen pagi maupun pelembap malam tanpa bikin riasan menggumpal sama sekali.",
                on_screen_text_id="Aman ditumpuk sunscreen!",
            ),
            FlowScene(
                scene_number=6,
                role="Benefit",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Kamera bergerak lembut menampilkan kontras before after kulit tampak lembap sehat dan botol utuh.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 interaction keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, slow tracking shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Dulu sebelum rutin pakai terasa kusam, sekarang dua tetes harian bikin kulit nyaman lembap.",
                on_screen_text_id="Before After terasa nyaman!",
            ),
            FlowScene(
                scene_number=7,
                role="CTA",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke hero shot penutup botol berdiri tegak dengan gestur ajakan ke tautan produk bawah.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 closing hero keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Locked-off static hero shot. {subject_clause}, {setting_desc}. {neg_tail}"
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
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 interaction keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, gentle push-in shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Serum yang terlalu kental sering bikin wajah gerah dan sunscreen jadi gampang menggumpal.",
                on_screen_text_id="Sunscreen sering menggumpal?",
            ),
            FlowScene(
                scene_number=3,
                role="Bedah Spek & Demo",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke sudut close-up makro tangan meneteskan tekstur cair dari botol kaca 30ml.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 macro keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Locked-off macro close-up. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Ini solusinya: formula cair Niacinamide lima persen dan Ceramide meresap dalam hitungan detik.",
                on_screen_text_id="5% Niacinamide + Ceramide",
            ),
            FlowScene(
                scene_number=4,
                role="Objection Killer",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus dari kulit yang lembap halus siap ditimpa sunscreen tanpa lengket.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 interaction keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, slow tracking shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Dulu sebelum rutin pakai terasa kusam berat, sekarang lebih nyaman aman dilayer sunscreen pagi.",
                on_screen_text_id="Before After nyaman dilayer!",
            ),
            FlowScene(
                scene_number=5,
                role="CTA",
                flow_action="Jump to",
                duration_sec=5,
                continuity_note="Pindah ke hero shot produk berdiri rapi di atas meja terang dengan gestur ajakan cek tautan produk bawah.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 closing hero keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Locked-off static hero shot. {subject_clause}, {setting_desc}. {neg_tail}"
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
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 macro keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Locked-off macro close-up. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id="Ini solusinya: formula cair Niacinamide lima persen plus Ceramide meresap hitungan detik tanpa residu.",
                on_screen_text_id="5% Niacinamide + Ceramide",
            ),
            FlowScene(
                scene_number=3,
                role="CTA",
                flow_action="Extend",
                duration_sec=5,
                continuity_note="Melanjutkan mulus saat tangan meletakkan botol utuh di meja terang dan menunjuk ke arah tautan produk bawah.",
                keyframe_image_prompt_en=(
                    f"Photorealistic 9:16 closing hero keyframe from Master Frame. {subject_clause}, {setting_desc}. {neg_tail}"
                ),
                flow_prompt_en=(
                    f"Seamless continuation from the previous frame, gentle pull-back shot. "
                    f"{subject_clause}, {setting_desc}. {neg_tail}"
                ),
                vo_script_id=f"Dulu sebelum pakai wajah terasa berat kusam, sekarang jauh lebih nyaman ringan; cek {cta_phrase}!",
                on_screen_text_id="Before After + Cek bawah!",
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
            storyboard_grid_layout=grid_layout,
            storyboard_grid_prompt_en=grid_prompt,
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
    """Return a distinct minimalist anti-halu Scene 1 Hook payload for Offline Demo Mode."""
    variant = _DEMO_HOOK_VARIANTS[variation_index % len(_DEMO_HOOK_VARIANTS)]
    new_s1 = FlowScene(
        scene_number=1,
        role="Hook",
        flow_action="New Scene",
        duration_sec=5,
        continuity_note=variant["continuity"],
        flow_prompt_en=(
            "Slow tracking shot on 9:16 vertical frame. Use @ProductAuthority in warm morning light. "
            "No text overlays, no additional logos, no readable screens."
        ),
        vo_script_id=variant["vo_id"],
        on_screen_text_id=variant["ost_id"],
    )
    return RegeneratedHookPayload(
        hook_angle=variant["hook_angle"],
        scene_1=new_s1,
        scene_2_continuity_note=variant["s2_bridge"],
    )
