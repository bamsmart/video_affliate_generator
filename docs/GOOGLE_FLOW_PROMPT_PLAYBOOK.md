# Google Flow / Veo 3.1 Anti-Hallucination Prompt Playbook

Panduan standar **Google Flow Video Generator Consultant** yang tertanam otomatis di mesin generator prompt aplikasi ini agar hasil video affiliate tetap **konsisten 1:1** di setiap adegan.

---

## 5 Hukum Anti-Halu di Google Flow (Veo 3.1)

### 1. Formula Sutradara 5-Bagian (Prosa Linear, Bebas Kurung Siku)
Google Flow menghasilkan video jauh lebih stabil saat prompt ditulis sebagai prosa sinematik berurutan dibanding blok tag meta (`[Visual Bible: ...]`, `[LOCK: ...]`) yang panjang:
1. **Cinematography & Camera:** Rasio vertikal `9:16`, jenis *shot*, lensa (misal `35mm f/1.8` atau `50mm macro`), dan gerak kamera terkunci.
2. **Subject & Standalone `@me`:** Identitas `@me` berdiri sendiri (dengan spasi) dan ciri fisik positif khas Nusantara Indonesia.
3. **Forensic 1:1 Product Geometry + Grounded Contact Physics:** Rincian struktur kaki/rangka/botol nyata dari foto serta kontak mantap dengan lantai/rumput/meja agar objek tidak melayang atau berubah ukuran.
4. **One Atomic Micro-Beat (1 Aksi / 5 Detik):** Hanya satu gerakan fisik halus per klip—tidak pernah menumpuk banyak aksi atau gerakan melipat/membongkar (`folding`/`unfolding`).
5. **Locked Environment, Lighting & Positive Audio:** Lokasi & pencahayaan konsisten, diakhiri `Audio: quiet natural ambient soundscape and crisp realistic product foley only, silent presenter.`

### 2. Frasa Target Positif 100% (Hindari Jebakan "Pink Elephant")
Model video memproses seluruh token kata yang muncul di prompt. Kata negasi seperti `do not deform legs`, `no Western face`, atau `no background music` justru berisiko memunculkan objek yang dilarang.
- **Lama (berisiko):** `strictly NO Western/Caucasian, do NOT redesign legs, no background music`
- **Baru (Consultant-Grade):** `authentic native Indonesian Nusantara features, warm sawo-matang skin, neat dark black hair; locked static geometry and original proportions preserved; quiet natural ambient soundscape only, silent presenter.`

### 3. Kinematika Scene Builder (`New Scene` vs `Extend` vs `Jump to`)
- **`New Scene` (Scene 1):** Menetapkan posisi awal produk persis seperti foto Ingredient (selalu pastikan ujung bawah/kaki produk terlihat utuh di foto Ingredient).
- **`Extend`:** Wajib diawali **`Seamless continuation from the previous frame,`** agar Veo melanjutkan gerakan langsung dari frame terakhir tanpa mematahkan geometri kaki atau sudut kamera.
- **`Jump to`:** Berpindah sudut kamera (misal ke *macro* tekstur/jahitan) sambil mempertahankan Product Ingredient aktif dan mengulang deskripsi lingkungan & cahaya yang sama.

### 4. Nol Tanda Kutip Ganda (`"`) di Prompt Video
Tanda kutip di dalam prompt video dapat terbaca sebagai permintaan menempelkan teks grafis acak di layar. Mesin otomatis menghilangkan tanda kutip dari `flow_prompt_en` sementara teks headline dikerjakan bersih di **CapCut**.

### 5. Hemat Kredit Google Flow (`Fast` → `Quality`)
Gunakan **Veo Fast / Lite** terlebih dahulu untuk menguji kesinambungan gerakan dan keakuratan kaki/bodi produk pada Scene 1–N; setelah rapi di Scene Builder, render ulang klip kunci memakai **Veo Quality**.
