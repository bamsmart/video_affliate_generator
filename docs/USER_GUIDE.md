🌐 **English** | [Bahasa Indonesia](USER_GUIDE.id.md) · 🏠 [Back to README](../README.md)

# Commercial User Guide — Laptop Studio & Mobile Playbook (`1× Copy-Paste`)

Welcome to **Affiliate AI Video Director**—a streamlined **3-step, `1× Copy-Paste`** affiliate video studio engineered for **Shopee Video & TikTok Shop Indonesia** (`App → Google Flow → CapCut`).

Run it in **Laptop Studio (`2-Column` default)** locally or toggle **Mobile / HP (`1-Column`)** from the sidebar when deployed on Streamlit Community Cloud.

---

## Prerequisites

1. **Product Photos & One-Time Personal Avatar Photo** (saved automatically in the app once uploaded).
2. **Google Flow Account** (`https://labs.google/fx/tools/flow`) — also works seamlessly on smartphone browsers.
3. **Free AI API Keys** (at least one, ideally both for automatic failover):
   - **Google Gemini API Key (Primary — Free):** https://aistudio.google.com/apikey
   - **OpenRouter API Key (Automatic Fallback — Free):** https://openrouter.ai/keys *(uses `:free` models by default)*.

---

## 1. Initial Setup (Once Only)

### 1.1 Deploy Free to Streamlit Community Cloud (Mobile & Anywhere Access)
1. **Push Code to a Private GitHub Repository:**
   ```bash
   cd path/to/video_affliate_generator
   git add .
   git commit -m "Update affiliate video director studio"
   git push -u origin main
   ```
   > **Security Guarantee:** [`.gitignore`](../.gitignore) automatically excludes `.env`, `.streamlit/secrets.toml`, `.venv/`, `projects/`, and `profile/` (`avatar_photo.jpg`, presets) so your private keys and personal photos never leave your local workspace.
2. **Configure Secrets at [share.streamlit.io](https://share.streamlit.io):**
   - Select your repo, branch `main`, main file `app.py`, and Python `3.12`.
   - Under **Settings → Secrets**, paste TOML *(on macOS, run `.venv/bin/python scripts/copy_secrets_for_cloud.py` to copy `.env` as TOML)*:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     OPENROUTER_API_KEY = "sk-or-v1-..."
     APP_PIN = "123456"
     ```
3. **Install as a Mobile Shortcut (Optional):** Add your deployed app URL to Android/iOS Home Screen and switch **Tata letak layar** in sidebar settings to **Mobile / HP (1-Kolom)**.

### 1.2 Run Locally on Laptop (Default)
```bash
.venv/bin/streamlit run app.py
```
Stop anytime with **`Control + C`** (or `pkill -9 -f streamlit` if a background session remains).

---

## 2. Daily Production SOP (3 Foolproof Steps)

### Stage 1: Upload Product + Avatar Photo (10 Seconds)
1. **Upload Product Photo(s)** (`Foto produk` — upload 1 uncropped photo **or 2–4 angles** [front, 3/4, side, back] to auto-stitch into a single **Product Turnaround Sheet** for Slot 1, up to 10 MB each). Ensure **bottom legs/base are completely visible**.
2. **Upload Your Avatar Photo (`Foto avatar Anda`)** once: it stays saved automatically for Slot 2 across all future products.
3. *(Optional)* Open **Pengaturan tambahan (opsional — boleh langsung lewati)** to customize persona, `3`/`5`/`7` scene depth, target platform (`Shopee Video`, `TikTok Shop`, `Shopee + TikTok`), or paste store specs / product URL for deeper facts.
4. Click **`Buat prompt Google Flow`**.

### Stage 2: Execute in Google Flow (`1× Copy-Paste`, Default `15s` Talking Avatar)
1. In **Siap pakai! 3 langkah di Google Flow**, verify the selected duration:
   - **`15 detik utuh` (Default):** Speaks the full emotional story (*Hook → Solution → Before vs After + CTA*) smoothly across **15 seconds with zero looping**.
   - **`8 detik`:** Use when generating shorter **5–8s** single-scene Veo clips.
2. Click **`Download foto produk (.jpg)`** (or **`Download Turnaround Sheet produk (.jpg)`** when using 2–4 angles) and download your **`avatar_photo.jpg`** if needed.
3. Click **`Buka Google Flow`** → create a new project → select **Videos (`9:16`)** → set duration to **`15s`** (or `5-8s`) → tap **`+`** and attach both **Product Photo / Turnaround Sheet + Avatar Photo**.
4. Click the **Copy** icon on **`Prompt Google Flow — Suara, Script & Avatar`** → **Paste** → **Generate**. Google Flow generates the video complete with your Avatar face, lip-sync, and Indonesian spoken voiceover!

> **Continuing to Scene 2 without Product Drift:** Inside Google Flow, either click **`Extend`** at the end of Clip 1, OR **Pause** Clip 1 at its final frame → hover and click **`Save frame`** → set that saved frame as your **`Start frame`** for Scene 2. Also explore **Mode pro** below for **Storyboard Contact Sheet Grid (`Nano Banana`)**, **Auto-Splitter (`keyframes.zip`)**, manual **Crop Sliders**, and **Deep Product Knowledge**.

### Stage 3: Voice Backup & CapCut Finishing (Optional)
- **Built-in Default:** Google Flow already includes Indonesian voiceover directly from your single prompt.
- **CapCut Audio Backup:** Right below the prompt box, your full **Script suara (VO)** is visible along with **`Buat audio MP3 + SRT sinkron suara Indonesia`** (`vo_capcut.mp3` + `.srt`) in case you want clean CapCut dubbing/subtitles.

### Stage 4: Publish & Maximize Conversion
1. Copy platform **Caption & Hashtags** and **Pinned Comment FAQ** from the **Caption Shopee/TikTok, Pinned Comment FAQ & tips CapCut** expander.
2. Attach **Keranjang Oranye** (Shopee) or **Keranjang Kuning** (TikTok).
3. **Mandatory Compliance:** Enable the **"Konten Buatan AI / AI-generated content"** toggle when publishing, then **Pin** the generated FAQ as your first comment.

---

## 3. Competitive Narrative Arc & Format Matrix

Every generated script follows the **Emotional Value-Add Storyboard** (`ugc-director-prompt-studio`) so your review beats generic affiliate titles:
**Touch Emotion & Real Pain (`Painful Nyata`) → What It Solves (`Apa yang Di-Solve`) → Safe `Before vs After` → `Objection Killer` → Platform CTA**.

| Content Goal | App Setting | Structure Highlights |
| :--- | :--- | :--- |
| **Fast 15s single-clip conversion** | `15 detik utuh` + `3 scene` *(Default)* | Hook Emosi & Painful → Apa yang Di-Solve → Before vs After + CTA in one 15s pass |
| **Multi-clip lifestyle review** | `8 detik` + `5 scene` | Emotional Hook → Before Context → Material Solution → After & Objection Killer → CTA |
| **Deep high-ticket breakdown** | `8 detik` + `7 scene deep` + Pro Grid | Full multi-angle Storyboard Grid → Auto-Split → 7-scene macro & ergonomic proof |

---

## 4. Quick Troubleshooting

| Symptom | Root Cause | Resolution |
| :--- | :--- | :--- |
| **Video repeats/loops at 15 seconds in Flow** | Using a short single-scene prompt with Flow set to `15s` | Keep **`15 detik utuh` (Default)** selected in the app so the full 3-scene script fills all 15 seconds continuously |
| **`API key belum terdeteksi` on Cloud** | `.env` is gitignored; Cloud Secrets not set yet | Open **share.streamlit.io → Settings → Secrets**, paste keys in `"..."` quotes, and click **Save** |
| **Product legs/base mutated in Flow** | Lower edge missing from uploaded photo, or using `Direct` on complex shapes | Re-upload uncropped product photo (or set bottom crop slider to `0%`), or run **Mode Pro → Storyboard Grid + Auto-Split** |
| **Avatar looks wrong or not synced** | Avatar photo not attached in Google Flow `+` Ingredients | Attach both **Foto Produk** and **Foto Avatar (`avatar_photo.jpg`)** inside Google Flow before generating |
