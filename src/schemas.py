"""Pydantic v2 schemas with Deep Product Knowledge (Added Value) for Competitive Affiliate Reviews."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PersonaStyle(str, Enum):
    SANTAI = "Review Jujur Santai"
    ANTUSIAS = "Racun Shopee Antusias"
    ELEGAN = "Elegan / Profesional"


class TalentPresence(str, Enum):
    AVATAR_MALE_ID = "Avatar Saya (Pria Indonesia)"
    AVATAR_FEMALE_ID = "Avatar Saya (Wanita Indonesia)"
    AVATAR_HIJAB_ID = "Avatar Saya (Hijab Indonesia)"
    FACELESS_BROLL = "Tanpa Wajah (Fokus Produk)"

    # Backward-compatible Python aliases
    MALE = "Avatar Saya (Pria Indonesia)"
    FEMALE = "Avatar Saya (Wanita Indonesia)"
    FEMALE_HIJAB = "Avatar Saya (Hijab Indonesia)"


_LEGACY_PRESENCE_MAP: dict[str, str] = {
    "Pria": TalentPresence.AVATAR_MALE_ID.value,
    "Wanita": TalentPresence.AVATAR_FEMALE_ID.value,
    "Wanita Berhijab": TalentPresence.AVATAR_HIJAB_ID.value,
    "Tanpa Wajah (Fokus Produk)": TalentPresence.FACELESS_BROLL.value,
}


class LocationLockMode(str, Enum):
    AUTO_CONTEXTUAL = "Otomatis sesuai produk"
    LOCKED_CUSTOM = "Kunci lokasi tetap"


class PlatformMode(str, Enum):
    SHOPEE = "shopee"
    TIKTOK = "tiktok"
    BOTH = "both"


class WorkflowMode(str, Enum):
    STORYBOARD_FIRST = "storyboard_first"
    DIRECT_INGREDIENTS = "direct_ingredients"


class TalentSavedProfile(BaseModel):
    """Lightweight text-only Google Flow Avatar & speaking style preset (zero photo/voice upload in app)."""

    preset_id: str = Field(default="avatar_pria_id")
    talent_name: str = Field(default="Avatar Google Flow Saya (Pria Indonesia)")
    talent_presence: TalentPresence = Field(default=TalentPresence.AVATAR_MALE_ID)
    persona: PersonaStyle = Field(default=PersonaStyle.SANTAI)
    avatar_flow_tag: str = Field(
        default="@me",
        description="Tag avatar Google Flow (default '@me', bisa ditambah ciri singkat seperti '@me, berkacamata, kaos hitam').",
    )
    visual_notes: str = Field(
        default="",
        description="Catatan singkat outfit/tampilan konsisten (contoh: kemeja kasual rapi warna earth-tone).",
    )
    location_mode: LocationLockMode = Field(default=LocationLockMode.AUTO_CONTEXTUAL)
    custom_location: str = Field(
        default="",
        description="Lokasi tetap jika location_mode = Kunci lokasi tetap.",
    )
    updated_at: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_tp = data.get("talent_presence")
            if raw_tp in _LEGACY_PRESENCE_MAP:
                data = {**data, "talent_presence": _LEGACY_PRESENCE_MAP[raw_tp]}
            elif "talent_presence" not in data:
                if data.get("is_faceless") is True:
                    data = {**data, "talent_presence": TalentPresence.FACELESS_BROLL.value}
                elif data.get("is_faceless") is False:
                    data = {**data, "talent_presence": TalentPresence.AVATAR_FEMALE_ID.value}
        return data

    @property
    def is_faceless(self) -> bool:
        return self.talent_presence == TalentPresence.FACELESS_BROLL


class TalentPresetCollection(BaseModel):
    active_preset_id: str = Field(default="avatar_pria_id")
    presets: list[TalentSavedProfile] = Field(default_factory=list)


class ProductAnalysis(BaseModel):
    product_name: str = Field(
        ...,
        min_length=1,
        description="Nama lengkap produk dan varian utama dalam Bahasa Indonesia.",
    )
    category: str = Field(
        default="Umum",
        description="Kategori produk (contoh: Skincare, Peralatan Rumah, Kursi Outdoor, Fashion).",
    )
    price_or_promo: str = Field(
        default="",
        description="Informasi harga atau promo yang terlihat di gambar/catatan (kosongkan jika tidak ada).",
    )
    usp: list[str] = Field(
        default_factory=list,
        description="Daftar 3-4 keunggulan utama (Unique Selling Points) produk dalam Bahasa Indonesia.",
    )
    pain_points: list[str] = Field(
        default_factory=list,
        description="Daftar 2-3 masalah nyata calon pembeli yang diselesaikan produk ini.",
    )
    target_audience: str = Field(
        ...,
        min_length=1,
        description="Deskripsi spesifik target pembeli produk di Indonesia.",
    )
    hook_angle: str = Field(
        ...,
        min_length=1,
        description="Nama sudut pandang (angle) hook yang dipilih untuk menghentikan scroll.",
    )
    recommended_setting_id: str = Field(
        default="Ruang dalam rumah yang terang dan rapi",
        description="1 lokasi syuting paling masuk akal sesuai kategori produk.",
    )
    is_sensitive_category: bool = Field(
        default=False,
        description="True jika produk termasuk skincare, kosmetik, suplemen, obat, atau makanan/minuman kesehatan.",
    )


class ProductKnowledgeBrief(BaseModel):
    """Deep Product Knowledge & Added Value weapon to beat generic surface-level affiliates."""

    technical_specs_and_materials: list[str] = Field(
        default_factory=list,
        description=(
            "Daftar 3-5 fakta teknis mendalam: bahan/material spesifik, kandungan aktif/komposisi, "
            "dimensi/kapasitas/daya tahan, atau mekanisme konstruksi nyata (bukan kata sifat kosong)."
        ),
    )
    how_it_works_or_usage_tip: str = Field(
        default="",
        description=(
            "Penjelasan Bahasa Indonesia tentang cara kerja produk atau tips pemakaian pro/kombinasi "
            "yang jarang dibahas affiliator biasa."
        ),
    )
    honest_pros_and_ideal_buyer: str = Field(
        default="",
        description="Ulasan jujur kenapa produk ini layak dibeli dan paling cocok untuk profil pembeli seperti apa.",
    )
    top_buyer_objection_and_answer: str = Field(
        default="",
        description=(
            "Objection Killer: 1 keraguan/pertanyaan terbesar calon pembeli di kolom komentar beserta jawaban faktual yang menenangkan."
        ),
    )
    competitor_differentiator_angle: str = Field(
        default="",
        description="Nilai tambah utama ulasan video ini dibanding kompetitor affiliator lain yang hanya baca judul produk.",
    )
    pinned_comment_faq_id: str = Field(
        default="",
        description=(
            "Teks komentar pertama (Pinned Comment) Bahasa Indonesia siap copy-paste berisi ringkasan spek penting & jawaban FAQ "
            "untuk mendongkrak konversi di Shopee Video / TikTok."
        ),
    )


class FlowSetup(BaseModel):
    ingredients_checklist: list[str] = Field(
        default_factory=list,
        description="Daftar foto referensi yang diunggah ke menu Ingredients di Google Flow.",
    )
    aspect_ratio: str = Field(
        default="9:16",
        description="Rasio aspek video vertikal, selalu '9:16'.",
    )
    exact_product_geometry_lock_en: str = Field(
        default=(
            "Reference @ProductAuthority checklist: exact silhouette, structural proportions, surface color, and original branding."
        ),
        min_length=1,
        description=(
            "Ringkasan internal Product Authority untuk checklist pengguna (TIDAK disalin ke dalam `flow_prompt_en` "
            "agar prompt Google Flow tidak mendeskripsikan ulang detail fisik yang sudah dikunci oleh gambar `@ProductAuthority`)."
        ),
    )
    start_to_end_prompt_en: str = Field(
        default=(
            "Locked-off static camera transition using start and end frame with @ProductAuthority. "
            "Seamless lighting shift from cool shade to warm sunlight. "
            "No text overlays, no additional logos, no readable screens."
        ),
        min_length=1,
        description=(
            "Prompt singkat (<= 35 kata) siap tempel ke fitur Start-to-End Frame Google Flow yang hanya mengarahkan "
            "gerak kamera + transisi cahaya memakai @ProductAuthority + batasan negatif eksplisit."
        ),
    )
    storyboard_grid_layout: str = Field(
        default="2x2",
        description="Tata letak Contact Sheet Grid untuk Nano Banana / Google Flow Image Mode ('2x2', '3x2', atau '3x3').",
    )
    storyboard_grid_prompt_en: str = Field(
        default=(
            "Clean 2x2 vertical storyboard contact sheet grid on 9:16 panels. "
            "Use @ProductAuthority cleanly with uniform lighting and framing across all panels. "
            "No text overlays, no additional logos, no readable screens."
        ),
        min_length=1,
        description=(
            "1 prompt Contact Sheet Grid Bahasa Inggris siap tempel ke Nano Banana / Google Flow Image Mode "
            "untuk menghasilkan beberapa panel keyframe seragam dalam satu kanvas sebelum dipotong menjadi Start Frames."
        ),
    )
    locked_visual_bible_en: str = Field(
        ...,
        min_length=1,
        description=(
            "Arahan singkat konsistensi lokasi, pencahayaan, dan rasio 9:16 sebagai acuan Master Frame "
            "(tanpa mendeskripsikan ulang wujud fisik produk dari @ProductAuthority)."
        ),
    )


class FlowScene(BaseModel):
    scene_number: int = Field(..., ge=1, description="Nomor urut adegan dimulai dari 1.")
    role: str = Field(
        ...,
        min_length=1,
        description="Peran adegan: 'Hook', 'Problem', 'Bedah Spek', 'Demo', 'Objection Killer', 'Benefit', atau 'CTA'.",
    )
    flow_action: str = Field(
        default="New Scene",
        description=(
            "Tombol aksi di Google Flow Scene Builder: 'New Scene' (wajib untuk Scene 1), "
            "'Extend' (lanjut mulus dari frame terakhir tanpa cut kamera), atau "
            "'Jump to' (pindah sudut kamera dengan objek & Master Frame tetap)."
        ),
    )
    duration_sec: int = Field(
        default=5,
        ge=4,
        le=8,
        description="Durasi klip dalam detik (standar 5 detik).",
    )
    continuity_note: str = Field(
        ...,
        min_length=1,
        description="Penjelasan Bahasa Indonesia bagaimana aksi awal/akhir adegan ini menyambung dengan adegan sebelah.",
    )
    keyframe_image_prompt_en: str = Field(
        default="",
        description=(
            "Prompt gambar statis 9:16 untuk Nano Banana / Flow Image Mode (<= 35 kata) untuk membuat keyframe "
            "adegan ini dari @ProductAuthority (& @me jika mode Avatar) sebelum dianimasikan di Frames to Video."
        ),
    )
    flow_prompt_en: str = Field(
        ...,
        min_length=1,
        description=(
            "Prompt Google Flow minimalis anti-halu (WAJIB singkat 20-35 kata) dengan rumus: "
            "[Camera/Motion] + [Use @ProductAuthority (+ @me Indonesian presenter jika mode Avatar)] + [Brief Lighting/Environment] + "
            "[No text overlays, no additional logos, no readable screens.]. "
            "DILARANG mendeskripsikan ulang bentuk/warna/label produk, dilarang kata kerja naratif (walks toward, picks up, opens, fold/unfold), "
            "tanpa kurung siku `[...]`, dan tanpa tanda kutip ganda."
        ),
    )
    flow_voice_prompt_en: str = Field(
        default="",
        description=(
            "Prompt Google Flow siap tempel (default) yang menggabungkan kunci visual anti-halu "
            "dengan arahan suara Bahasa Indonesia natural & lip-sync untuk mengucapkan `vo_script_id`."
        ),
    )
    vo_script_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Kalimat penuh naskah Voice Over Bahasa Indonesia yang luwes, edukatif, dan bernilai tambah tinggi "
            "(WAJIB 12-16 kata untuk klip 5 detik, sebut detail spek/manfaat nyata, BUKAN klaim kosong & BUKAN kode ID!)."
        ),
    )
    on_screen_text_id: str = Field(
        ...,
        min_length=1,
        description="Teks headline singkat Bahasa Indonesia maksimal 5 kata untuk overlay teks di CapCut (BUKAN kode ID).",
    )


class CapCutFinishing(BaseModel):
    full_vo_script_id: str = Field(
        ...,
        min_length=1,
        description="Gabungan utuh seluruh kalimat vo_script_id dari Scene 1 sampai akhir dalam Bahasa Indonesia.",
    )
    bgm_vibe_suggestion: str = Field(
        ...,
        min_length=1,
        description="Rekomendasi jenis musik latar (BGM) dan level volume di CapCut.",
    )
    pacing_tips: str = Field(
        ...,
        min_length=1,
        description="Tips editing praktis di CapCut (pemotongan jeda, posisi teks safe-zone, dan SFX).",
    )
    shopee_caption_and_hashtags: str = Field(
        ...,
        min_length=1,
        description="Caption edukatif & persuasif untuk Shopee Video beserta 4-6 hashtag relevan tanpa spasi di dalam hashtag.",
    )
    tiktok_caption_and_hashtags: str = Field(
        default="",
        description="Caption edukatif & persuasif alternatif untuk TikTok Shop beserta 4-6 hashtag relevan tanpa spasi.",
    )
    compliance_reminder: str = Field(
        default="Wajib aktifkan label 'Konten Buatan AI' saat upload di Shopee Video.",
        description="Pengingat kepatuhan aktivasi label Konten Buatan AI.",
    )


class BlueprintResponse(BaseModel):
    """Structured commercial blueprint with Deep Product Knowledge Added Value."""

    product_analysis: ProductAnalysis
    product_knowledge: ProductKnowledgeBrief = Field(default_factory=ProductKnowledgeBrief)
    flow_setup: FlowSetup
    scenes: list[FlowScene] = Field(..., min_length=1)
    capcut_finishing: CapCutFinishing


class RegeneratedHookPayload(BaseModel):
    """Focused JSON output for regenerating Scene 1 Hook variation (anti-spam)."""

    hook_angle: str = Field(
        ...,
        min_length=1,
        description="Nama sudut pandang (angle) hook baru yang berbeda dari sebelumnya.",
    )
    scene_1: FlowScene
    scene_2_continuity_note: str = Field(
        ...,
        min_length=1,
        description="Penjelasan Bahasa Indonesia bagaimana Scene 2 menyambung mulus dari akhir Scene 1 yang baru.",
    )


class SavedBlueprintRecord(BaseModel):
    project_id: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    platform_mode: PlatformMode = Field(default=PlatformMode.SHOPEE)
    workflow_mode: WorkflowMode = Field(default=WorkflowMode.STORYBOARD_FIRST)
    duration_preset: str = Field(default="25-30 detik (5 scene)")
    persona: str = Field(default=PersonaStyle.SANTAI.value)
    talent_preset_name: str = Field(default="Fokus Produk / B-Roll (Wajah & Suara di CapCut)")
    model_used: str = Field(default="gemini:gemini-2.5-flash")
    fallback_reason: str = Field(default="")
    knowledge_sources: list[str] = Field(default_factory=list)
    cropped_ingredient_path: str = Field(default="")
    previous_hooks: list[str] = Field(default_factory=list)
    blueprint: BlueprintResponse
