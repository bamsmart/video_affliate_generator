🌐 [English](USER_GUIDE.md) | **Bahasa Indonesia** · 🏠 [Kembali ke README](../README.id.md)

# Panduan Operasional Komersial — Studio Laptop & HP (`1× Copy-Paste`)

Selamat datang di **Affiliate AI Video Director** — studio generator konten **Shopee Video & TikTok Shop Indonesia** berpola **`App → Google Flow → CapCut`** yang dirancang sesederhana mungkin (**3 langkah, cukup `1× Copy-Paste`**).

Bisa dijalankan langsung di **Laptop (2-Kolom *default*)** maupun dari **Handphone (1-Kolom)** lewat Streamlit Community Cloud.

---

## Prasyarat Sebelum Mulai

1. **Foto Produk Utuh & 1× Foto Wajah Avatar Anda** (tersimpan otomatis di aplikasi setelah diunggah pertama kali).
2. **Akun Google Flow** (`https://labs.google/fx/tools/flow`) — bisa dibuka di browser laptop maupun HP.
3. **API Key AI Gratis** (minimal salah satu, disarankan keduanya agar ada cadangan otomatis):
   - **Gemini API Key (Utama — Gratis):** https://aistudio.google.com/apikey
   - **OpenRouter API Key (Cadangan Otomatis — Gratis):** https://openrouter.ai/keys *(memakai model `:free`)*.

---

## 1. Setup Awal (Cukup 1 Kali)

### 1.1 Deploy Gratis ke Streamlit Community Cloud (Akses dari HP)
1. **Upload Kode ke GitHub Private Repository:**
   ```bash
   cd path/to/video_affliate_generator
   git add .
   git commit -m "Update affiliate video director studio"
   git push -u origin main
   ```
   > **Keamanan Terjaga:** File [`.gitignore`](../.gitignore) otomatis memblokir `.env`, `.streamlit/secrets.toml`, `.venv/`, `projects/`, dan `profile/` (`avatar_photo.jpg`, preset) agar API key dan foto pribadi Anda **tidak pernah ikut ter-upload ke GitHub**.
2. **Isi Secrets di [share.streamlit.io](https://share.streamlit.io):**
   - Pilih repo Anda, branch `main`, main file `app.py`, dan Python `3.12`.
   - Buka **Settings → Secrets**, tempel format TOML *(di Mac, jalankan `.venv/bin/python scripts/copy_secrets_for_cloud.py`)*:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     OPENROUTER_API_KEY = "sk-or-v1-..."
     APP_PIN = "123456"
     ```
3. **Buka di HP:** Tambahkan URL aplikasi ke Layar Utama HP, lalu di sidebar → **Pengaturan aplikasi & koneksi AI** ubah **Tata letak layar** ke **Mobile / HP (1-Kolom)** bila perlu.

### 1.2 Menjalankan di Laptop (Default)
```bash
.venv/bin/streamlit run app.py
```
Untuk mematikan server lokal, tekan **`Control + C`** di terminal (atau jalankan `pkill -9 -f streamlit` jika masih ada proses tersisa).

---

## 2. SOP Produksi Harian (3 Langkah Anti-Bingung)

### Tahap 1: Upload Foto Produk & Foto Avatar (10 Detik)
1. **Upload Foto Produk** (`Foto produk` — unggah 1 foto utuh **atau 2–4 foto multi-sudut** [depan, serong 45°, samping, belakang] agar otomatis digabung jadi **1 lembar *Product Turnaround Sheet*** di Slot 1, maks `10 MB`/file). Pastikan **ujung kaki/alas bawah produk terlihat utuh 100%**.
2. **Upload Foto Avatar Anda** (`Foto avatar Anda`) **1 kali saja** — foto tersimpan otomatis untuk Slot 2 pada pemakaian berikutnya.
3. *(Opsional)* Buka **Pengaturan tambahan (opsional — boleh langsung lewati)** jika ingin mengganti durasi/gaya bicara, memilih `Shopee Video` / `TikTok Shop` / `Shopee + TikTok`, atau menempel link & deskripsi toko.
4. Klik **`Buat prompt Google Flow`**.

### Tahap 2: Eksekusi di Google Flow (`1× Copy-Paste`, Default `15 Detik Utuh`)
1. Pada kartu hasil **Siap pakai! 3 langkah di Google Flow**, periksa pilihan durasi:
   - **`15 detik utuh` (Default):** Memuat naskah lengkap (*Emosi & Painful → Solusi Produk → Before vs After + CTA*) dengan arahan `"no looping"` agar saat Google Flow diset **15s** Avatar berbicara penuh tanpa mengulang.
   - **`8 detik`:** Dipakai bila ingin membuat klip pendek 5–8 detik per adegan di Veo.
2. Klik **`Download foto produk (.jpg)`** (atau **`Download Turnaround Sheet produk (.jpg)`** bila mengunggah 2–4 sudut) dan download **`avatar_photo.jpg`** bila belum ada di galeri/folder Google Flow.
3. Klik **`Buka Google Flow`** → buat *project* baru → pilih **Videos (`9:16`)** → atur durasi **`15s`** (atau `5-8s`) → klik **`+`** lalu unggah **Foto Produk / Turnaround Sheet + Foto Avatar** tadi.
4. Klik ikon **Copy** di kotak **`Prompt Google Flow — Suara, Script & Avatar`** → **Paste** → **Generate**. Video langsung keluar lengkap dengan wajah Avatar, gerak bibir sinkron, dan suara Bahasa Indonesia yang menjelaskan produk!

> **Ingin lanjut ke Scene 2 tanpa produk berubah bentuk?** Di Google Flow, klik **`Extend`** di akhir klip 1, **ATAU** jeda (*Pause*) video Scene 1 di frame terakhir → arahkan kursor dan klik **`Save frame`** → pakai gambar itu sebagai **`Start frame`** Scene 2. Buka juga **Mode pro** di bawah untuk **Storyboard Grid (`Nano Banana`)**, **Potong Otomatis (`keyframes.zip`)**, **Slider Crop**, dan **Product Knowledge**.

### Tahap 3: Cadangan Audio MP3 / Finishing CapCut (Opsional)
- **Secara Default:** Suara penjelasan produk sudah langsung keluar otomatis dari Google Flow lewat kotak `1× Copy-Paste`.
- **Cadangan Dubbing CapCut:** Tepat di bawah kotak prompt, tersedia teks **Script suara (VO)** dan tombol **`Buat audio MP3 + SRT sinkron suara Indonesia`** (`vo_capcut.mp3` + `.srt`) bila Anda ingin mengganti atau merapikan suara serta *auto-caption* di CapCut.

### Tahap 4: Upload & Optimasi Konversi
1. Salin **Caption & Hashtag** serta **Pinned Comment FAQ** dari lipatan **Caption Shopee/TikTok, Pinned Comment FAQ & tips CapCut**.
2. Tautkan produk ke **Keranjang Oranye** (Shopee Video) atau **Keranjang Kuning** (TikTok Shop).
3. **Kepatuhan Wajib:** Aktifkan label/toggle **"Konten Buatan AI"** sebelum *publish*, lalu **Pin** teks FAQ di komentar pertama.

---

## 3. Alur Narasi Kompetitif & Matriks Format

Setiap skrip yang dihasilkan mengikuti **Storyboard Narasi Emosional** (`ugc-director-prompt-studio`) agar jauh lebih menjual daripada affiliator yang hanya membaca judul barang:
**Sentuh Emosi & Painful Nyata → Apa yang Di-Solve → Before vs After yang Aman → Objection Killer → CTA Platform**.

| Kebutuhan Konten | Pengaturan Disarankan | Fokus Utama |
| :--- | :--- | :--- |
| **Video cepat 15 detik sekali jadi** | `15 detik utuh` + `3 scene` *(Default)* | Hook Emosi & Painful → Apa yang Di-Solve → Before vs After + CTA dalam 1 klip penuh 15s |
| **Ulasan multi-klip harian** | `8 detik` + `5 scene` | Hook Emosi → Situasi Before → Solusi & Material → Transformasi After & Objection Killer → CTA |
| **Produk mahal / kompleks** | `8 detik` + `7 scene deep` + Mode Pro Grid | Grid Storyboard Nano Banana → Auto-Split → 7 adegan pembuktian detail |

---

## 4. Troubleshooting Cepat

| Masalah | Penyebab Umum | Solusi Cepat |
| :--- | :--- | :--- |
| **Video mengulang di durasi 15 detik** | Menggunakan prompt singkat 1 adegan saat Flow diset 15s | Pastikan tombol **`15 detik utuh` (Default)** aktif di aplikasi agar naskah penuh 3 adegan terpakai dari detik ke-1 sampai ke-15 |
| **Peringatan `API key belum terdeteksi` di Cloud** | `.env` diblokir GitHub demi keamanan; Secrets belum diisi | Buka **share.streamlit.io → Settings → Secrets**, tempel key dalam tanda kutip `"..."`, klik **Save** |
| **Bentuk kaki/rangka produk berubah di Flow** | Bagian bawah foto produk terpotong, atau butuh penguncian gambar awal | Unggah foto produk utuh dari atas sampai ujung kaki (atau atur slider crop bawah di Mode Pro ke `0%`), lalu gunakan **Mode Pro → Storyboard Grid + Auto-Split** |
| **Wajah tidak sesuai / suara tidak sinkron** | Foto Avatar belum ikut diunggah di menu `+` Google Flow | Pastikan **Foto Produk** dan **Foto Avatar (`avatar_photo.jpg`)** sama-sama dimasukkan ke `+` Google Flow sebelum klik Generate |
