# Affiliate AI Video Director — Google Flow Playbook (Anti-Halu & Added-Value)

Standar resmi gabungan dua skill workspace ([affiliate-ai-video-director](../.agents/skills/affiliate-ai-video-director/SKILL.md) dan [ugc-director-prompt-studio](../.agents/skills/ugc-director-prompt-studio/SKILL.md)) yang tertanam langsung di aplikasi untuk **Laptop Studio (2-Kolom)** maupun **Mobile HP (1-Kolom)**.

---

## 1. Mode Default (Tercepat — 1× Copy-Paste `15 Detik Utuh` dengan Suara & Avatar)

1. **Siapkan 2 Foto Utama:**
   - **Foto Produk (`@ProductAuthority`):** Bisa upload 1 foto utuh **atau 2–4 foto multi-sudut** (depan, serong 45°, samping, belakang) yang otomatis digabung aplikasi menjadi **1 lembar *Product Turnaround Sheet*** di Slot 1 sehingga AI memahami bentuk 3D produk tanpa menghabiskan slot Avatar!
   - **Foto Avatar Anda (`avatar_photo.jpg` / `@me`):** Upload **1 kali saja** di aplikasi (tersimpan otomatis) agar wajah presenter Indonesia konsisten di Slot 2.
2. **Pilih Durasi Klip di Aplikasi:**
   - **`15 detik utuh` (Default):** Menggabungkan naskah Hook → Solusi Produk → Before vs After + CTA menjadi satu kalimat kontinu dengan instruksi `"no looping"`, sehingga saat Google Flow diset ke **15s** Avatar bicara penuh 15 detik tanpa mengulang.
   - **`8 detik`:** Mengeluarkan prompt khusus Adegan 1 untuk klip pendek 5–8 detik per adegan Veo.
3. **Menyambung ke Adegan Berikutnya Langsung di Google Flow (Agar Produk Tetap Konsisten):**
   - Gunakan tombol **`Extend`** di akhir klip Scene 1, **ATAU** jeda (*Pause*) klip Scene 1 di frame terakhir → arahkan kursor lalu klik **`Save frame`** bawaan Google Flow → pasang sebagai **`Start frame`** Scene 2.
3. **Eksekusi di Google Flow (`Videos 9:16`):**
   - Unggah Foto Produk + Foto Avatar di menu **`+`**, **1× Copy-Paste** kotak prompt utama, atur durasi **15s**, lalu klik **Generate** → video langsung keluar dengan wajah Avatar, gerak bibir sinkron, dan suara Bahasa Indonesia.

---

## 2. Dua Lapisan Storyboard (Kompetitif + Anti-Halu)

| Lapisan Storyboard | Status | Tugas Utama |
| :--- | :--- | :--- |
| **Storyboard Narasi** | **Selalu Aktif** (termasuk 15s 1× Copy-Paste) | Menggerakkan naskah dengan alur **Sentuh Emosi & Painful Nyata → Apa yang Di-Solve → Before vs After yang Aman → Objection Killer → CTA** agar jauh lebih meyakinkan daripada affiliator yang hanya membaca judul produk. |
| **Storyboard Visual Grid** (`Nano Banana` → `Auto-Split ZIP` → `Frames to Video`) | **Opsional di Mode Pro** | Untuk produk berbentuk rumit (kursi lipat, tas multi-saku, gadget) atau video panjang banyak sudut agar siluet, kaki, dan logo terkunci ~95%+ sebelum dianimasikan. |

---

## 3. Aturan Emas Formula Anti-Halu (`<= 35` Kata Visual)

```text
[Gerak Kamera Sinematografi] + [Tag Ingredients: @ProductAuthority (+ @me Indonesian presenter)] + [Cahaya Singkat] + [No text overlays, no additional logos, no readable screens.]
```

- **Tag Langsung, Jangan Deskripsikan Ulang:** Panggil `@ProductAuthority` dan `@me` berdiri sendiri (dipisah spasi, bukan `(@me)`). Dilarang menulis ulang warna botol, tutup, kaki kursi, atau teks logo.
- **Hindari Kata Kerja Pemicu Halusinasi:** Dilarang `walks toward`, `picks up`, `opens the door`, `folding`, `unfolding`, `collapsing`, `morphing`.
- **Dilarang Menampakkan Produk Rusak:** Jangan pernah memvisualisasikan produk yang dipromosikan dalam keadaan patah, bocor, robek, atau goyang — bangun kontras *Before vs After* secara aman dan jujur.
- **Tanpa Kurung Siku & Kutip Ganda:** Bebas `[...]` dan `"` agar model tidak merender teks liar ke dalam frame.
- **Kepatuhan Audio & Platform:** Gunakan akhiran `No text overlays, no additional logos, no readable screens.`, patuhi CTA platform (`Keranjang Oranye` / `Keranjang Kuning` / `cek keranjang di bawah`), dan aktifkan label **"Konten Buatan AI"** saat unggah.
