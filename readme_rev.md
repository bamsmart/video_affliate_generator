# 🛍️ Shopee Affiliate AI Video Generator (Commercial-Grade Hybrid System)

Dokumen ini adalah *blueprint* revisi untuk membangun aplikasi **Automated Creative Director & Prompt Engineer** menggunakan Python (di **Antigravity**) dan **Gemini Multimodal API**. 

Sistem ini dirancang khusus untuk menghasilkan video affiliate Shopee berkualitas **commercial-grade** dengan alur kerja **Hybrid (App → Google Flow → CapCut)** yang *idiot-proof* (sangat sederhana, minim interaksi, dan bisa digunakan oleh pengguna paling awam sekalipun).

---

## 📌 1. Aturan & Kepatuhan (Shopee Policy)

* **Monetisasi:** Shopee mengizinkan video affiliate buatan AI untuk dimonetisasi dan menghasilkan komisi.
* **Syarat Wajib:** Pengguna **wajib** mengaktifkan label atau mencantumkan keterangan "Konten Buatan AI" saat *upload* ke Shopee Video demi transparansi.
* **Anti-Spam:** Setiap kali *generate* ulang untuk produk yang sama, sistem harus memvariasikan *hook* dan sudut visual agar tidak terdeteksi sebagai konten duplikat (*reupload*).

---

## ⚙️ 2. Arsitektur Hybrid (Realistis & Hemat Biaya)

Alih-alih memaksakan *backend* merender video dari nol (yang mahal dan rawan halusinasi visual), tugas dibagi secara optimal sesuai keunggulan masing-masing *platform*:

1. **Aplikasi Python / Antigravity (Otak Sutradara & Prompt Engineer):**
   * Membaca *screenshot* produk secara otomatis via Multimodal LLM (Gemini).
   * Merumuskan strategi jualan, naskah VO presisi, dan rangkaian *prompt* sinematografi yang saling menyambung.
2. **Google Flow (Mesin Produksi Visual Kontinu):**
   * Mengeksekusi *prompt* menggunakan fitur **Ingredients** (foto produk & wajah talent) dan **Scene Builder / Extend** agar video menyambung mulus dari awal hingga akhir.
3. **CapCut (Finishing Commercial-Grade):**
   * Menggabungkan klip video hasil Flow, *Voice Over* (rekaman/TTS), *Auto-Caption* (di *safe zone*), BGM, dan SFX.

---

## 🎯 3. Desain UX: "Idiot-Proof" (Zero-Friction)

Pengguna tidak boleh diminta menulis *prompt*, memikirkan sudut kamera, atau mengatur teknis sinematografi.

### Fase 0: Onboarding Profil Talent (Cukup 1x di Awal)
* **Foto Talent:** Upload 1–3 foto wajah jelas (pencahayaan rata, menghadap depan) untuk referensi konsistensi visual.
* **Gaya Bicara Default:** Pilih 1 persona (misal: *Review Jujur Santai*, *Racun Shopee Antusias*, atau *Elegan/Profesional*).
* *(Opsional)* **Sampel Suara:** Disimpan jika pengguna ingin mengintegrasikan TTS / *Voice Cloning* di tahap *finishing*.

### Fase 1: Produksi Harian (1 Input + 1 Klik)
* Pengguna cukup mengunggah **1 screenshot halaman produk Shopee** (atau 1 foto asli produk).
* *(Opsional)* Pilih durasi target: `15 detik (3 Scene)` atau `25–30 detik (5 Scene)`.
* Klik tombol **"Generate Blueprint"**.

---

## 🏆 4. Empat Mekanisme Kunci *Commercial-Grade*

Agar video tidak terlihat seperti "AI murahan" (*AI slop*) dan benar-benar menghasilkan konversi, *backend* wajib menerapkan 4 aturan ini secara otomatis pada output-nya:

1. **Locked Visual Bible (Kunci Konsistensi):**
   * Sistem membuat 1 blok deskripsi visual tetap (*setting lokasi, pencahayaan, color grading, outfit talent, dan jenis lensa*) lalu **menyuntikkannya ke setiap *prompt* adegan** agar seluruh klip terlihat diambil di waktu dan tempat yang sama.
2. **Continuity Bridging (Jembatan Antar-Scene):**
   * *Ending* Scene $N$ dirancang secara eksplisit agar menyambung ke *opening* Scene $N+1$ (misal: Scene 1 berakhir dengan talent mengangkat produk ke kamera → Scene 2 dimulai dengan *close-up* produk yang dipegang tersebut). Memaksimalkan fitur *Extend / Jump to* di Google Flow.
3. **Matematika Durasi VO (Anti-Kecepetan/Kepanjangan):**
   * Panjang naskah Voice Over bahasa Indonesia dikunci ketat sekitar **12–16 kata per klip 5 detik** (atau **20–24 kata per klip 8 detik**) agar sinkronisasi di CapCut langsung pas tanpa banyak pemotongan.
4. **Panduan Ingredients Eksplisit:**
   * Output selalu diawali dengan instruksi jelas tentang foto apa saja yang harus diunggah ke menu *Ingredients* di Google Flow sebelum mulai menempelkan *prompt*.

---

## 🖥️ 5. Struktur Tampilan Output Aplikasi (Siap Copy-Paste)

Hasil *generate* ditampilkan sebagai daftar kartu (*step-by-step*) dengan tombol **1-Click Copy**:

| Tahap | Isi Kartu di Aplikasi | Aksi Pengguna |
| :--- | :--- | :--- |
| **Step 1: Setup Flow** | Checklist foto yang diunggah ke menu *Ingredients* (Foto Produk + Foto Talent). | Upload ke Google Flow |
| **Step 2: Scene 1 (Hook)** | **Prompt Flow (EN)** `[Copy]` + **Aksi Flow:** `New Scene` + **VO (ID)** (12–15 kata). | Paste di Flow |
| **Step 3: Scene 2 (Demo)** | **Prompt Flow (EN)** `[Copy]` + **Aksi Flow:** `Extend / Jump to` + **VO (ID)** (12–15 kata). | Paste di Flow |
| **Step 4: Scene 3 (CTA)** | **Prompt Flow (EN)** `[Copy]` + **Aksi Flow:** `Extend / Jump to` + **VO (ID)** (10–14 kata). | Paste di Flow |
| **Step 5: Paket CapCut** | **Full VO Script** `[Copy]`, **Saran Vibe BGM**, **Caption & Hashtag Shopee** `[Copy]`, dan pengingat **Label AI**. | Finishing di CapCut & Upload |

---

## 🤖 6. System Prompt (Siap Pakai untuk Gemini API)

Gunakan *system prompt* ini di *backend* aplikasi Antigravity untuk memproses *screenshot* produk dan mengembalikan format JSON yang terstruktur:

```text
Bertindaklah sebagai Senior Commercial Video Director dan AI Prompt Engineer spesialis konten Shopee Affiliate untuk Google Flow dan CapCut.

Tugasmu adalah menganalisis gambar/screenshot produk yang diberikan pengguna untuk mengekstrak nama produk, harga/promo (jika ada), keunggulan utama (USP), dan masalah pembeli (pain points).

Berdasarkan analisis tersebut dan profil talent yang diberikan, buatlah blueprint produksi video pendek (rasio 9:16) yang siap dieksekusi di Google Flow secara berkesinambungan (seamless continuity) dan di-finishing di CapCut.

ATURAN WAJIB:
1. VISUAL BIBLE: Buat satu definisi konsisten untuk lokasi, pencahayaan, color grading, gaya kamera, dan pakaian talent. SUNTIKKAN elemen visual bible ini ke dalam SETIAP prompt scene agar hasil video di Google Flow konsisten.
2. CONTINUITY BRIDGING: Pastikan aksi penutup di Scene N menyambung secara logis ke aksi pembuka di Scene N+1 (dirancang untuk fitur Extend / Scene Builder di Google Flow).
3. AKURASI PRODUK: Instruksikan kamera dan aksi untuk mempertahankan bentuk/kemasan asli produk dari referensi Ingredients tanpa mengubah teks atau desain produk.
4. BAHASA PROMPT: Semua prompt visual untuk Google Flow WAJIB dalam Bahasa Inggris yang deskriptif, sinematis, dan fokus pada pergerakan kamera serta aksi nyata.
5. MATEMATIKA VO: Naskah Voice Over WAJIB menggunakan Bahasa Indonesia yang luwes, natural, persuasif ala reviewer Shopee (bukan bahasa kaku/robot). Kunci durasi ketat di 12-16 kata per scene (asumsi klip 5-6 detik).
6. HOOK 3 DETIK: Scene 1 wajib memiliki visual kontras/dinamis dan kalimat hook yang langsung menghentikan scroll.
7. OUTPUT FORMAT: Kembalikan HANYA dalam format JSON valid sesuai skema yang ditentukan tanpa teks tambahan di luar JSON.
```

---

## 📐 7. Skema Output JSON (Untuk Parsing di Python)

Gunakan skema ini (via `response_schema` / Structured Outputs di Gemini API) agar UI aplikasi selalu stabil:

```json
{
  "product_analysis": {
    "product_name": "string",
    "usp": ["string"],
    "target_audience": "string",
    "hook_angle": "string"
  },
  "flow_setup": {
    "ingredients_checklist": [
      "Foto Produk (dari screenshot/foto bersih)",
      "Foto Wajah Talent (dari profil tersimpan)"
    ],
    "aspect_ratio": "9:16",
    "locked_visual_bible_en": "string (deskripsi konsisten lokasi, lighting, outfit, color grading)"
  },
  "scenes": [
    {
      "scene_number": 1,
      "role": "Hook | Problem | Demo | CTA",
      "flow_action": "New Scene | Extend / Jump to",
      "duration_sec": 5,
      "continuity_note": "string (penjelasan sambungan dari scene sebelumnya)",
      "flow_prompt_en": "string (prompt lengkap siap copy-paste ke Google Flow, sudah termasuk Visual Bible)",
      "vo_script_id": "string (12-16 kata bahasa Indonesia natural)",
      "on_screen_text_id": "string (teks singkat max 5 kata untuk headline CapCut)"
    }
  ],
  "capcut_finishing": {
    "full_vo_script_id": "string (gabungan seluruh VO siap rekam/TTS)",
    "bgm_vibe_suggestion": "string",
    "pacing_tips": "string",
    "shopee_caption_and_hashtags": "string",
    "compliance_reminder": "Wajib aktifkan label 'Konten Buatan AI' saat upload di Shopee Video."
  }
}
```

---

## 🚀 8. Roadmap Implementasi di Antigravity

* [ ] **Setup State Profil Talent:** Simpan preferensi persona & foto referensi talent secara lokal/database agar cukup diisi 1x.
* [ ] **Build Upload UI:** Halaman utama super minimalis (1 *dropzone* untuk *screenshot* produk + 1 tombol *Generate*).
* [ ] **Integrasi Gemini API (Multimodal + Structured Output):** Kirim *screenshot* + `System Prompt` + `JSON Schema`.
* [ ] **Render Step-by-Step Cards:** Tampilkan hasil JSON menjadi kartu berurutan dengan tombol *1-Click Copy* per *scene* dan paket CapCut.
* [ ] **Fitur "Regenerate Hook":** Tambahkan tombol khusus untuk mengulang *angle* Scene 1 saja jika pengguna ingin variasi video untuk produk yang sama.