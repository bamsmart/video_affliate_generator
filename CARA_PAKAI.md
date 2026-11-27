# 📖 Cara Pakai & Deploy Gratis ke HP (Mobile-First)

Aplikasi ini sudah dirancang **Mobile-First** supaya Anda bisa mengerjakan semuanya **100% langsung dari Handphone** (ambil screenshot Shopee di HP → buka aplikasi di HP → *copy* prompt ke Google Flow HP → *finishing* di CapCut HP) tanpa perlu menyalakan laptop!

---

## ☁️ Bagian A — Deploy Gratis ke Cloud (Bisa Dipakai di HP Kapan Saja, Laptop Mati!)

Menggunakan **Streamlit Community Cloud** (**100% Gratis, tanpa kartu kredit, mendukung GitHub Private Repo**):

### Langkah 1: Upload Kode ke GitHub Private Repository
Buka Terminal di folder proyek ini, lalu jalankan:

```bash
cd /Users/bambangtryono/PycharmProjects/video_affliate_generator
git init
git add .
git commit -m "Initial cloud-ready mobile studio"
```
> **Aman:** File `.gitignore` sudah memastikan `.env`, `.venv/`, `projects/`, dan `profile/` **TIDAK** akan ikut ter-upload ke GitHub.

Buat **New Repository** di GitHub Anda (pilih **Private**), lalu hubungkan dan push:
```bash
git branch -M main
git remote add origin https://github.com/USERNAME_ANDA/NAMA_REPO_ANDA.git
git push -u origin main
```

### Langkah 2: Deploy di Streamlit Community Cloud (1 Menit)
1. Buka [share.streamlit.io](https://share.streamlit.io) dan login dengan akun **GitHub** Anda.
2. Klik **"Create app"** → pilih repository yang baru Anda buat:
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Sebelum klik Deploy, buka **"Advanced settings..."**:
   - **Python version:** `3.12`
   - Pada kotak **Secrets**, tempel isi berikut (sesuaikan dengan API key Anda):
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     OPENROUTER_API_KEY = "sk-or-v1-..."

     # Opsional: isi angka PIN agar hanya Anda yang bisa memakai aplikasi ini
     APP_PIN = "123456"
     ```
4. Klik **"Deploy!"**. Tunggu ~1 menit sampai aplikasi menyala.

### Langkah 3: Jadikan Ikon Aplikasi di Layar Utama HP
1. Buka link aplikasi Anda (`https://nama-app.streamlit.app`) di browser HP:
   - **Android (Chrome):** Ketuk titik tiga pojok kanan atas → **"Tambahkan ke layar utama / Install app"**.
   - **iPhone (Safari):** Ketuk tombol **Share** di bawah → **"Add to Home Screen"**.
2. Selesai! Sekarang aplikasinya muncul seperti aplikasi asli di HP Anda.

---

## 📶 Bagian B — Alternatif Buka di HP Lewat Wi-Fi Rumah (Tanpa Deploy Cloud)

Jika sedang di rumah dengan Wi-Fi yang sama antara Mac dan HP:
```bash
cd /Users/bambangtryono/PycharmProjects/video_affliate_generator
.venv/bin/streamlit run app.py --server.address 0.0.0.0
```
Terminal akan menampilkan baris **`Network URL: http://192.168.x.x:8501`** — cukup ketik alamat tersebut di browser HP Anda!

---

## 📱 Bagian C — Alur Kerja Praktis 100% di Handphone

1. **Di Aplikasi Shopee / TikTok HP:** Screenshot halaman produk yang mau dipromosikan.
2. **Di Web App Kita (di HP):**
   - Ketuk **"Upload screenshot halaman produk dari galeri HP"** lalu pilih screenshot tadi.
   - Pilih durasi (`15 detik`, `25-30 detik`, atau `40-45 detik deep`).
   - *(Opsional)* Buka menu **Tambah detail spek / link website produk** untuk tempel deskripsi spesifikasi toko agar ulasan makin dalam.
   - Ketuk **"Generate blueprint & product knowledge"**.
3. **Di Kartu Step 1:** Ketuk **"Simpan foto produk bersih ke HP"** (`ingredient_produk_bersih.jpg` sudah bersih dari bar UI Shopee).
4. **Di Google Flow (Browser HP):**
   - Upload foto produk bersih tadi ke **Ingredients** (rasio `9:16`).
   - Kembali ke tab aplikasi kita, ketuk ikon **Copy** di pojok kanan kotak `Prompt Google Flow` tiap scene → *Paste* ke Google Flow sesuai petunjuk tombol **`New Scene`**, **`Extend`**, atau **`Jump to`** → simpan klip videonya ke galeri HP.
5. **Di CapCut HP & Upload:**
   - Masukkan klip hasil Flow + rekaman wajah/suara Anda di CapCut (atau ketuk **"Buat audio MP3 + SRT sinkron otomatis"** di aplikasi untuk simpan `vo_capcut.mp3` & `vo_capcut.srt` gratis ke HP).
   - Upload ke Shopee Video / TikTok, salin **Caption & Hashtag**, tempel **Pinned comment FAQ** di komentar pertama, pasang keranjang produk, dan **nyalakan toggle Label "Konten Buatan AI"**.
