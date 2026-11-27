"""System prompt, Deep Product Knowledge Blueprint builder (3/5/7 scenes), and offline demos."""

from __future__ import annotations

import json
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
Bertindaklah sebagai Senior Commercial Video Director, Product Specialist, dan AI Prompt Engineer spesialis konten Shopee Video & TikTok Affiliate Indonesia untuk Google Flow dan CapCut.

MISI UTAMAMU ADALAH "ADDED VALUE & DEEP PRODUCT KNOWLEDGE":
90% affiliator lain gagal konversi karena cuma membaca judul barang secara dangkal ("barang ini bagus dan murah, yuk beli").
Video kita WAJIB menang bersaing dengan memberikan **nilai tambah edukatif yang tajam, spesifik, dan menjawab keraguan pembeli**:
- Bedah detail material, bahan aktif/komposisi, ketebalan/kapasitas/mekanisme kerja nyata, tips pakai pro, dan *Objection Killer* (menjawab keraguan terbesar calon pembeli sebelum checkout).
- Jangan mengarang angka palsu yang tidak masuk akal: gunakan fakta dari gambar/screenshot, data website/spesifikasi toko yang dilampirkan, serta pengetahuan teknis standar kategori produk secara akurat & jujur.

ATURAN TEKNIS WAJIB:
1. VISUAL BIBLE KONTEKSTUAL: Buat SATU definisi konsisten untuk lokasi (sesuaikan dengan kategori produk jika mode lokasi otomatis — misal taman/teras sore untuk kursi camping outdoor, dapur bersih untuk alat masak, meja rias terang untuk skincare), pencahayaan, color grading, gaya kamera, dan gaya subjek. SUNTIKKAN elemen visual bible ini ke dalam SETIAP prompt scene.
2. CONTINUITY BRIDGING & TOMBOL GOOGLE FLOW SPESIFIK:
   - Scene 1 WAJIB memakai `flow_action`: "New Scene".
   - Scene 2 dan seterusnya pilih secara spesifik antara:
     * "Extend": kamera melanjutkan gerakan langsung dari frame terakhir klip sebelumnya tanpa cut sudut kamera.
     * "Jump to": berpindah sudut kamera (misal cut ke macro close-up jahitan/tekstur/material produk untuk membuktikan Product Knowledge!) dengan objek & lokasi yang sama.
3. AKURASI PRODUK & BRAND SAFETY (ANTI-PRODUK RUSAK):
   - Pertahankan 100% bentuk, warna, logo, dan kemasan asli produk dari referensi Ingredients.
   - DILARANG KERAS memvisualisasikan produk yang sedang dipromosikan dalam keadaan rusak, goyang, patah, bocor, robek, atau gagal pada adegan Problem!
4. BAHASA PROMPT FLOW: Semua `flow_prompt_en` WAJIB dalam Bahasa Inggris sinematis yang menonjolkan detail fisik/kualitas material produk secara visual, dan diakhiri kalimat: "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
5. MATEMATIKA VO BAHASA INDONESIA BERNILAI TAMBAH: Semua field berakhiran `_id` berarti KALIMAT BAHASA INDONESIA NATURAL (BUKAN kode nomor ID!). Kunci panjang `vo_script_id` ketat di **12-16 kata per scene** (untuk klip 5 detik). DILARANG menulis kalimat basa-basi kosong — setiap scene wajib memuat fakta spek/material/cara kerja/jawaban keraguan pembeli! Hindari klaim medis absolut ('menyembuhkan', 'mengobati', '100% ampuh', 'hilang permanen'), harga palsu ('termurah se-Indonesia'), atau ajakan transaksi luar aplikasi ('beli di WA').
6. PRODUCT KNOWLEDGE BRIEF & PINNED COMMENT: Isi lengkap objek `product_knowledge`, termasuk `pinned_comment_faq_id` (komentar sematan siap copy-paste yang merangkum spek penting & jawaban pertanyaan umum pembeli).
7. TERMINOLOGI PLATFORM: Untuk Shopee gunakan istilah "Keranjang Oranye" atau "Tautan Produk di bawah" (jangan sebut Keranjang Kuning di naskah Shopee). Semua hashtag bebas spasi internal (`#KursiLipat`).
8. OUTPUT FORMAT: Kembalikan HANYA dalam format JSON valid sesuai skema yang ditentukan tanpa teks tambahan di luar JSON.\
"""


def _persona_instruction(persona: PersonaStyle) -> str:
    if persona == PersonaStyle.ANTUSIAS:
        return "Racun Affiliate Edukatif & Antusias: enerjik, meyakinkan, padat fakta menarik produk."
    if persona == PersonaStyle.ELEGAN:
        return "Reviewer Spesialis / Profesional: tenang, artikulasi rapi, bedah kualitas material & fungsi secara berkelas."
    return "Teman Jujur Paham Produk: akrab, jujur membahas detail bahan/fungsi nyata dan menjawab keraguan pembeli."


def _presence_instruction(profile: TalentSavedProfile) -> str:
    extra = f" ({profile.visual_notes.strip()})" if profile.visual_notes.strip() else ""
    if profile.talent_presence == TalentPresence.FACELESS_BROLL:
        return (
            "TANPA WAJAH / FOKUS B-ROLL DETAIL PRODUK & TANGAN: Seluruh klip Google Flow HANYA menampilkan detail makro material produk dan interaksi tangan rapi "
            f"tanpa pernah menampilkan wajah manusia{extra} (wajah/avatar & suara diatur di CapCut)."
        )
    if profile.talent_presence == TalentPresence.FEMALE_HIJAB:
        return f"Ada Talent di Flow: satu kreator wanita Indonesia berhijab rapi konsisten di semua scene{extra}."
    if profile.talent_presence == TalentPresence.MALE:
        return f"Ada Talent di Flow: satu kreator pria Indonesia berpenampilan kasual rapi konsisten di semua scene{extra}."
    return f"Ada Talent di Flow: satu kreator wanita Indonesia berpenampilan kasual rapi konsisten di semua scene{extra}."


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
Checklist Kualitas & Added Value Wajib:
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
- Jangan pernah menampilkan produk dalam kondisi rusak/cacat.
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

    if profile.talent_presence == TalentPresence.FACELESS_BROLL:
        subject_desc = "clean well-groomed hands only (strictly faceless product B-roll, no human face in frame)"
    elif profile.talent_presence == TalentPresence.FEMALE_HIJAB:
        subject_desc = "consistent young Indonesian female creator wearing a neat cream pashmina hijab and casual linen top"
    elif profile.talent_presence == TalentPresence.MALE:
        subject_desc = "consistent young Indonesian male creator wearing a neat casual olive linen shirt"
    else:
        subject_desc = "consistent young Indonesian female creator wearing a neat cream linen casual shirt"

    setting_desc = (
        profile.custom_location.strip()
        if profile.location_mode == LocationLockMode.LOCKED_CUSTOM and profile.custom_location.strip()
        else "sunlit minimalist Indonesian vanity table with soft morning window light"
    )
    visual_bible = (
        f"9:16 vertical commercial video shot on 35mm f/1.8 lens in a {setting_desc}, "
        f"clean neutral warm beige-white color grading, featuring {subject_desc}, "
        f"keeping the exact product bottle geometry, frosted glass texture, and printed label strictly identical to the uploaded Ingredients reference."
    )

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
            f"[Visual Bible: {visual_bible}] {variant['action_en']}. "
            "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Continuous smooth camera push-in contrasting humid tropical morning air "
                    "while holding the pristine intact referenced serum bottle steadily in hand. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Macro close-up cut highlighting the frosted UV-diffusing glass bottle and precision glass dropper "
                    "of the exact referenced product resting on sunlit travertine stone. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Extreme macro close-up of two crystal-clear water-light serum drops releasing from the referenced pipette "
                    "onto clean skin and spreading into a weightless invisible finish. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Smooth continuation as fingertips lightly tap the matte-hydrated skin surface "
                    "showing zero sticky film or pilling while the intact bottle sits cleanly nearby. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Gentle arc shot around the referenced bottle beside a sunlit mirror, "
                    "emphasizing clean daily skincare simplicity and healthy hydrated skin sheen. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Clean hero closing shot as the exact referenced serum bottle stands upright in crisp focus "
                    "while a hand gestures gently toward the lower shopping link safe zone. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Continuous smooth camera push-in contrasting humid tropical morning air "
                    "before focusing cleanly on the pristine intact referenced serum bottle held steadily in hand. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Macro close-up cut onto the hand holding the exact referenced 30ml frosted bottle, "
                    "dispensing two clear watery serum drops onto skin and blending smoothly into a weightless finish. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Smooth continuation showing refreshed matte-hydrated skin sheen "
                    "while holding the intact referenced bottle steadily in soft morning window light. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Clean hero closing shot as the exact referenced serum bottle stands upright on the sunlit table "
                    "in crisp focus while a hand gestures gently toward the lower shopping link safe zone. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Macro close-up shot on the referenced bottle held cleanly in hand, "
                    "dispensing two crystal-clear watery drops onto skin and blending effortlessly to show a non-sticky finish while keeping the label sharp. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
                    f"[Visual Bible: {visual_bible}] Smooth pull-back as the exact referenced bottle rests steadily in crisp focus on the sunlit table "
                    "with a gentle hand gesture pointing downward toward the product link area and clean upper/lower safe zones. "
                    "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
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
    """Return a distinct Scene 1 Hook payload for Offline Demo Mode."""
    variant = _DEMO_HOOK_VARIANTS[variation_index % len(_DEMO_HOOK_VARIANTS)]
    bible = blueprint.flow_setup.locked_visual_bible_en
    new_s1 = FlowScene(
        scene_number=1,
        role="Hook",
        flow_action="New Scene",
        duration_sec=5,
        continuity_note=variant["continuity"],
        flow_prompt_en=(
            f"[Visual Bible: {bible}] {variant['action_en']}. "
            "Audio: subtle realistic room ambience and natural product foley only, no background music, no spoken dialogue."
        ),
        vo_script_id=variant["vo_id"],
        on_screen_text_id=variant["ost_id"],
    )
    return RegeneratedHookPayload(
        hook_angle=variant["hook_angle"],
        scene_1=new_s1,
        scene_2_continuity_note=variant["s2_bridge"],
    )
