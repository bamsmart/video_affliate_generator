🌐 [English](USER_GUIDE.md) | **Bahasa Indonesia** · 🏠 [Kembali ke README](../README.id.md)

# Panduan Operasional Komersial (SOP Produksi 100% dari HP)

Selamat datang di **Affiliate AI Video Director** — alur produksi konten **Shopee Video & TikTok Shop Affiliate** berstandar komersial dengan pola kerja **App → Google Flow → CapCut**.

Aplikasi ini dirancang **Mobile-First** agar Anda bisa meriset produk, menyalin prompt **anti-halu**, merender klip di **Google Flow** dengan wajah asli Avatar **`@me`** Anda, hingga upload langsung dari **Handphone** tanpa perlu menyalakan laptop setiap hari.

---

## Prasyarat Sebelum Mulai

1. **Smartphone (Android / iPhone)** dengan aplikasi **Shopee / TikTok**, browser untuk **Google Flow**, dan aplikasi **CapCut**.
2. **Avatar Pribadi di Google Flow** yang sudah dibuat satu kali (dipanggil otomatis dengan mengetik **`@me`**).
3. **API Key AI Gratis** (minimal salah satu, sangat disarankan keduanya agar ada cadangan otomatis):
   - **Gemini API Key (Utama — Gratis):** https://aistudio.google.com/apikey
   - **OpenRouter API Key (Cadangan Otomatis — Gratis):** https://openrouter.ai/keys *(memakai model `:free` tanpa wajib deposit)*.

---

## 1. Setup Awal (Cukup 1 Kali Selamanya)

### 1.1 Deploy Gratis ke Streamlit Community Cloud
Jalankan aplikasi kapan saja dari HP tanpa membuat laptop bekerja atau nge-hang:

1. **Upload Kode ke GitHub Private Repository:**
   ```bash
   cd path/to/video_affliate_generator
   git init
   git add .
   git commit -m "Initial commercial affiliate studio"
   git branch -M main
   git remote add origin https://github.com/USERNAME_ANDA/NAMA_REPO_ANDA.git
   git push -u origin main
   ```
   > **Keamanan Terjaga:** File [`.gitignore`](../.gitignore) otomatis memblokir `.env`, `.streamlit/secrets.toml`, `.venv/`, `projects/`, dan `profile/` agar API key serta hasil kerja lokal Anda **tidak pernah ikut ter-upload ke GitHub**.

2. **Aktifkan Aplikasi & Secrets di Cloud:**
   - Buka [share.streamlit.io](https://share.streamlit.io) dan login dengan akun GitHub Anda.
   - Klik **Create app** → pilih repositori Anda, Branch `main`, dan Main file path `app.py`.
   - Buka **Advanced settings...** → pilih Python `3.12` → tempel Secrets TOML Anda *(di Mac, jalankan `.venv/bin/python scripts/copy_secrets_for_cloud.py` untuk menyalin `.env` ke clipboard otomatis dalam format TOML yang valid)*:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     OPENROUTER_API_KEY = "sk-or-v1-..."

     # Sangat disarankan: PIN pengaman agar kuota API Anda hanya bisa dipakai sendiri
     APP_PIN = "123456"
     ```
   - Klik **Deploy!** dan tunggu ±1 menit sampai aplikasi menyala.

3. **Pasang Sebagai Ikon Aplikasi di Layar Utama HP:**
   - Buka link aplikasi Anda (`https://nama-app.streamlit.app`) di browser HP.
   - **Android (Chrome):** Ketuk **`⋮`** → **Tambahkan ke layar utama / Install app**.
   - **iPhone (Safari):** Ketuk **Share** → **Add to Home Screen**.

### 1.2 Opsi Alternatif: Jalankan di Laptop atau via Wi-Fi Rumah
- **Di Laptop saja:**
  ```bash
  .venv/bin/streamlit run app.py
  ```
- **Di HP lewat Wi-Fi rumah yang sama (tanpa deploy Cloud):**
  ```bash
  .venv/bin/streamlit run app.py --server.address 0.0.0.0
  ```
  Buka **`Network URL`** (`http://192.168.x.x:8501`) yang muncul di browser HP Anda.

> **Cara Mematikan Server Lokal:** Tekan **`Control + C`** di terminal tempat Streamlit berjalan. Jika terminal macet atau terlanjur ditutup, jalankan `pkill -9 -f streamlit` lalu tutup tab `localhost:8501`.

---

## 2. SOP Produksi Video Harian dari HP (5 Tahap)

### Tahap 1: Siapkan Foto Utuh & Product Knowledge
1. **Ambil Foto Produk yang Utuh (Kunci Anti-Halu #1):**
   - Simpan foto produk dari galeri toko atau ambil screenshot layar produk.
   - **Aturan Emas:** Pastikan **ujung bawah produk terlihat 100% utuh** (misalnya ke-4 kaki kursi, sepatu karet alas, atau bagian bawah botol). Jika bagian bawah terpotong di foto referensi, Google Flow berisiko mengarang bentuk kaki baru.
2. *(Keunggulan Kompetitif)* **Lampirkan Spesifikasi Toko / Link Website Brand:**
   - Buka **Tambah detail spek / link website produk**, lalu tempel link website resmi atau *copy-paste* rincian bahan/ukuran/kandungan dari deskripsi toko agar naskah VO jauh lebih berbobot daripada affiliator yang hanya membaca judul barang.

### Tahap 2: Generate Blueprint Komersial di Aplikasi
1. Buka aplikasi dari Layar Utama HP (masukkan `APP_PIN` jika diaktifkan).
2. Unggah **1–4 foto produk** (maksimal 10 MB per file).
3. Pilih **Subjek / Avatar Google Flow**:
   - **`Avatar Saya (Pria / Wanita / Hijab Indonesia)`:** Tag **`@me`** sudah otomatis terisi. Anda bisa menambah ciri singkat misalnya `@me, berkacamata, kaos hitam`.
   - **`Tanpa Wajah (Fokus Produk)`:** Untuk video B-roll makro tangan khas Indonesia & detail produk tanpa wajah.
4. Pilih **Durasi & kedalaman ulasan** (`3 scene`, `5 scene`, atau `7 scene deep`) serta **Target platform CTA** (`Shopee Video`, `TikTok Shop`, atau `Shopee + TikTok`).
5. Ketuk **Generate blueprint & product knowledge**.
6. Jika muncul peringatan kuning *Peringatan kepatuhan klaim produk*, ketuk **Perbaiki klaim otomatis ke bahasa aman** sebelum lanjut.

### Tahap 3: Eksekusi Konsisten di Google Flow (Rasio `9:16`)
1. Pada kartu **Step 1 — Setup Google Flow**, periksa pratinjau **`ingredient_produk_bersih.jpg`**:
   - Foto `1:1`, `3:4`, dan `9:16` dibiarkan utuh 100%; hanya screenshot HP ekstra-panjang yang dipangkas bar atas/bawahnya secara konservatif.
   - Jika bagian bawah tampak terlalu mepet, buka **Kaki/bawah produk terpotong? Atur batas crop di sini**, geser *Potong bar bawah* ke **`0%`** → ketuk **Terapkan ulang crop**, lalu ketuk **Simpan foto produk bersih ke HP**.
2. Buka **Google Flow** di HP (rasio **`9:16`**), lalu unggah foto produk bersih tadi ke menu **Ingredients / Asset**.
3. Jalankan **Step 2 sampai Step Terakhir** secara berurutan:
   - Ketuk ikon **Copy** di pojok kanan atas kotak `Prompt Google Flow`.
   - Ikuti lencana tombol Google Flow di setiap kartu:
     - **`New Scene`** (Scene 1): Tempel prompt + pastikan **Ingredient Produk** aktif. Token **`@me`** di dalam prompt otomatis memanggil wajah asli Avatar Indonesia Anda.
     - **`Extend`**: Pilih **Extend** dari frame terakhir klip sebelumnya untuk gerak sinambung tanpa ganti sudut.
     - **`Jump to`**: Pilih **Jump to** untuk pindah sudut *close-up* material sambil tetap mengaktifkan **Ingredient Produk** agar geometri tetap 1:1.
   - Simpan semua klip video ke galeri HP.

### Tahap 4: Finishing Cepat di CapCut HP
1. Impor seluruh klip Google Flow ke proyek baru CapCut (`9:16`).
2. Tambahkan Voice Over:
   - **Paling Natural:** Rekam suara asli Anda sambil membaca **Full VO script**, atau pakai suara/avatar langsung di CapCut.
   - **Otomatis Gratis:** Di kartu Step Terakhir, ketuk **Buat audio MP3 + SRT sinkron otomatis** untuk mengunduh `vo_capcut.mp3` dan `vo_capcut.srt`, atau unduh **Download subtitle CapCut (.srt)** untuk disandingkan dengan rekaman suara sendiri.
3. Posisikan **Teks Headline** tiap scene di *safe zone* tengah-atas (bebas dari ikon status atas dan tombol keranjang/caption di sepertiga bawah layar).
4. Tambahkan BGM sesuai rekomendasi dengan volume tipis **8%–10%** agar informasi spek tetap terdengar jelas.

### Tahap 5: Upload & Optimasi Konversi
1. Upload video ke **Shopee Video** atau **TikTok Shop**, lalu tempel **Caption & Hashtag** sesuai platform dari kartu Step Terakhir.
2. Tautkan produk ke **Keranjang Oranye / Keranjang Kuning**.
3. **Kepatuhan Wajib:** Aktifkan label/toggle **"Konten Buatan AI"** saat upload.
4. **Pendongkrak Checkout:** Begitu video tayang, buka kolom komentar lalu **salin & sematkan (`Pin`) teks `Pinned comment FAQ`** sebagai komentar pertama untuk langsung menjawab keraguan pembeli.

---

## 3. Matriks Pemilihan Format & Skala Anti-Spam

| Kebutuhan Konten | Rekomendasi Durasi | Fokus Utama |
| :--- | :--- | :--- |
| **Produk impulsif / viral cepat** | `15 detik (3 scene)` | Hook cepat → Bedah 1 spek & demo → CTA singkat |
| **Produk harian & fashion** | `25-30 detik (5 scene)` | Hook → Masalah pembeli → Spek & demo → Objection Killer → CTA |
| **Produk mahal / outdoor / skincare** | `40-45 detik (7 scene deep)` | Hook → Masalah → Bedah material makro → Demo kerja → Objection Killer → Tips pakai pro → CTA |

**Produksi Variasi Tanpa Duplikat:**
- **Ketuk `Regenerate hook`:** Mengganti khusus sudut pandang **Scene 1 (Hook)** saja sambil tetap menyambung mulus ke Scene 2.
- **Ketuk `Variasi baru (anti-spam)`:** Merombak seluruh angle video sambil mengecek riwayat `hook_history.json` agar kalimat hook tidak pernah berulang.

---

## 4. Troubleshooting Cepat

| Masalah | Penyebab Umum | Solusi Cepat |
| :--- | :--- | :--- |
| **Peringatan `API key belum terdeteksi` di Cloud** | `.env` diblokir GitHub demi keamanan; Secrets Cloud belum diisi | Buka **share.streamlit.io → Settings → Secrets**, tempel key di dalam kutip `"..."`, lalu klik **Save** |
| **Bentuk kaki/rangka produk berubah di Flow** | Bagian bawah foto terpotong di Ingredients, atau Ingredient Produk tidak terpilih saat `Jump to` | Geser crop bawah ke `0%`, upload ulang foto utuh ke Ingredients, dan pastikan Ingredient Produk aktif di tiap scene |
| **Wajah berubah jadi orang Barat / tidak mirip saya** | Token `@me` tidak tertulis berdiri sendiri | Gunakan versi terbaru — **`@me`** kini otomatis ditulis berdiri sendiri disertai kunci wajah asli Nusantara |
| **Link marketplace menampilkan catatan batas bot** | Situs toko memblokir crawler otomatis / wajib login | Normal — cukup *copy-paste* rincian deskripsi toko ke kolom teks spesifikasi di aplikasi |
| **Laptop terasa berat saat menjalankan lokal** | Proses Streamlit lokal masih berjalan di belakang layar | Matikan dengan `Ctrl + C` atau `pkill -9 -f streamlit`, lalu jalankan harian via **Streamlit Cloud** |
