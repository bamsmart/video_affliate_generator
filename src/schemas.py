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
    FACELESS_BROLL = "Tanpa Wajah (Fokus Produk)"
    FEMALE = "Wanita"
    FEMALE_HIJAB = "Wanita Berhijab"
    MALE = "Pria"


class LocationLockMode(str, Enum):
    AUTO_CONTEXTUAL = "Otomatis sesuai produk"
    LOCKED_CUSTOM = "Kunci lokasi tetap"


class PlatformMode(str, Enum):
    SHOPEE = "shopee"
    TIKTOK = "tiktok"
    BOTH = "both"


class TalentSavedProfile(BaseModel):
    """Lightweight text-only character & speaking style preset (zero photo/voice upload needed)."""

    preset_id: str = Field(default="broll_produk")
    talent_name: str = Field(default="Fokus Produk / B-Roll (Wajah & Suara di CapCut)")
    talent_presence: TalentPresence = Field(default=TalentPresence.FACELESS_BROLL)
    persona: PersonaStyle = Field(default=PersonaStyle.SANTAI)
    visual_notes: str = Field(
        default="",
        description="Catatan singkat outfit/tampilan opsional (contoh: lengan kemeja linen krem).",
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
        if isinstance(data, dict) and "talent_presence" not in data:
            if data.get("is_faceless") is True:
                data = {**data, "talent_presence": TalentPresence.FACELESS_BROLL.value}
            elif data.get("is_faceless") is False:
                data = {**data, "talent_presence": TalentPresence.FEMALE.value}
        return data

    @property
    def is_faceless(self) -> bool:
        return self.talent_presence == TalentPresence.FACELESS_BROLL


class TalentPresetCollection(BaseModel):
    active_preset_id: str = Field(default="broll_produk")
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
    locked_visual_bible_en: str = Field(
        ...,
        min_length=1,
        description=(
            "Satu paragraf Bahasa Inggris yang mengunci 1 lokasi konsisten, pencahayaan, color grading, "
            "lensa kamera, gaya visual subjek, dan kemiripan 100% bentuk produk terhadap Ingredients."
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
            "'Jump to' (pindah sudut kamera/close-up dengan objek & lokasi tetap)."
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
    flow_prompt_en: str = Field(
        ...,
        min_length=1,
        description=(
            "Prompt visual lengkap dalam Bahasa Inggris siap copy-paste ke Google Flow. "
            "WAJIB memuat elemen Locked Visual Bible, detail fisik/material spesifik produk, pergerakan kamera, "
            "produk tetap identik dengan Ingredients (JANGAN pernah digambarkan rusak/gagal), serta arahan foley tanpa musik/dialog."
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
    duration_preset: str = Field(default="25-30 detik (5 scene)")
    persona: str = Field(default=PersonaStyle.SANTAI.value)
    talent_preset_name: str = Field(default="Fokus Produk / B-Roll (Wajah & Suara di CapCut)")
    model_used: str = Field(default="gemini:gemini-2.5-flash")
    fallback_reason: str = Field(default="")
    knowledge_sources: list[str] = Field(default_factory=list)
    cropped_ingredient_path: str = Field(default="")
    previous_hooks: list[str] = Field(default_factory=list)
    blueprint: BlueprintResponse
