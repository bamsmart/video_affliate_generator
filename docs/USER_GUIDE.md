🌐 **English** | [Bahasa Indonesia](USER_GUIDE.id.md) · 🏠 [Back to README](../README.md)

# Commercial User Guide — 100% Mobile Production Playbook

Welcome to **Affiliate AI Video Director**—a commercial-grade creative workflow engineered for **Shopee Video & TikTok Shop** affiliates using the **`App → Google Flow → CapCut`** pipeline.

The studio is built **Mobile-First**, allowing you to research products, generate anti-hallucination prompts featuring your personal **`@me`** Google Flow avatar, assemble clips in CapCut, and publish directly from your smartphone.

---

## Prerequisites

1. **Smartphone (Android or iPhone)** with **Shopee / TikTok**, mobile browser access to **Google Flow**, and **CapCut**.
2. **Personal Avatar in Google Flow** created once (invoked automatically by typing **`@me`**).
3. **Free AI API Keys** (at least one, ideally both for automatic failover):
   - **Google Gemini API Key (Primary — Free):** https://aistudio.google.com/apikey
   - **OpenRouter API Key (Automatic Fallback — Free):** https://openrouter.ai/keys *(uses `:free` models by default)*.

---

## 1. One-Time Initial Setup (5 Minutes)

### 1.1 Deploy Free to Streamlit Community Cloud
Run the studio from anywhere on your phone without keeping a laptop powered on:

1. **Push Code to a Private GitHub Repository:**
   ```bash
   cd path/to/video_affliate_generator
   git init
   git add .
   git commit -m "Initial commercial affiliate studio"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```
   > **Security Guarantee:** [`.gitignore`](../.gitignore) automatically excludes `.env`, `.streamlit/secrets.toml`, `.venv/`, `projects/`, and `profile/` so your private API keys and local workspace files are never pushed to GitHub.

2. **Deploy & Configure Cloud Secrets:**
   - Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
   - Click **Create app** → select your repository, branch `main`, and main file path `app.py`.
   - Open **Advanced settings...** → select Python `3.12` → paste your TOML secrets *(on macOS, run `.venv/bin/python scripts/copy_secrets_for_cloud.py` to convert `.env` into valid TOML and copy it directly to your clipboard)*:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     OPENROUTER_API_KEY = "sk-or-v1-..."

     # Recommended: protect your API quota behind a personal login PIN
     APP_PIN = "123456"
     ```
   - Click **Deploy!** and wait ~60 seconds.

3. **Install as a Mobile Home-Screen App:**
   - Open your `https://your-app.streamlit.app` URL on your phone.
   - **Android (Chrome):** Tap **`⋮`** → **Add to Home screen / Install app**.
   - **iPhone (Safari):** Tap **Share** → **Add to Home Screen**.

### 1.2 Local Laptop & Home Wi-Fi Alternative
- **Local laptop only:**
  ```bash
  .venv/bin/streamlit run app.py
  ```
- **Phone over the same home Wi-Fi (no Cloud deploy required):**
  ```bash
  .venv/bin/streamlit run app.py --server.address 0.0.0.0
  ```
  Open the printed **`Network URL`** (`http://192.168.x.x:8501`) in your phone browser.

> **Stopping the Local Server:** Press **`Control + C`** in the running terminal window. If the terminal froze or was closed, run `pkill -9 -f streamlit` and close any open `localhost:8501` browser tabs.

---

## 2. Daily Mobile Production SOP (5 Stages)

### Stage 1: Prepare Complete Product References
1. **Capture an Uncropped Product Image (Anti-Hallucination Rule #1):**
   - Save the product gallery photo or take a clean mobile screenshot.
   - **Golden Rule:** Ensure the **entire bottom of the product (e.g., all chair legs, rubber feet, or bottle base)** is clearly visible and uncropped. Cropped legs cause Google Flow to hallucinate mismatched structures.
2. *(Recommended Competitive Edge)* **Gather Store Specs or Official Brand URLs:**
   - Expand **Tambah detail spek / link website produk** and paste the brand URL or copy-pasted marketplace specifications (materials, load ratings, ingredients, dimensions). This gives your voiceover factual depth that outperforms generic affiliate videos.

### Stage 2: Generate the Commercial Blueprint
1. Open your studio app from your phone home screen (enter `APP_PIN` if enabled).
2. Upload **1–4 product images** (up to 10 MB each).
3. Select **Subjek / Avatar Google Flow**:
   - **`Avatar Saya (Pria / Wanita / Hijab Indonesia)`:** **`@me`** is pre-filled automatically. Optionally add brief traits such as `@me, berkacamata, kaos hitam`.
   - **`Tanpa Wajah (Fokus Produk)`:** Generates macro B-roll showing Indonesian hands and product craftsmanship without faces.
4. Pick your **duration preset** (`3`, `5`, or `7 scene deep`) and **target CTA platform** (`Shopee Video`, `TikTok Shop`, or `Shopee + TikTok`).
5. Tap **Generate blueprint & product knowledge**.
6. If any compliance warning appears, tap **Perbaiki klaim otomatis ke bahasa aman** before proceeding.

### Stage 3: Execute in Google Flow (`9:16`)
1. On **Step 1 — Setup Google Flow**, inspect the preview of **`ingredient_produk_bersih.jpg`**:
   - Standard `1:1`, `3:4`, and `9:16` photos are kept intact; ultra-tall phone screenshots are conservatively trimmed.
   - If the lower edges look close, open **Kaki/bawah produk terpotong? Atur batas crop di sini**, set *Potong bar bawah* to **`0%`**, tap **Terapkan ulang crop**, and tap **Simpan foto produk bersih ke HP**.
2. Open **Google Flow** on your phone (`9:16` aspect ratio) and attach the clean product photo under **Ingredients / Asset**.
3. Run **Step 2 through Step N+1** sequentially:
   - Tap the **Copy** icon on each `Prompt Google Flow` box.
   - Match the Google Flow Scene Builder action badge:
     - **`New Scene`** (Scene 1): Paste prompt while ensuring your **Product Ingredient** is selected. Standalone **`@me`** in the prompt automatically invokes your personal Indonesian avatar.
     - **`Extend`**: Extend smoothly from the previous clip's final frame with zero camera cut.
     - **`Jump to`**: Cut to a material/feature angle while keeping your **Product Ingredient** active so geometry stays locked 1:1.
   - Save every generated clip to your phone gallery.

### Stage 4: Mobile Finishing in CapCut
1. Import all Google Flow clips into a new **`9:16`** CapCut timeline.
2. Add Indonesian Voiceover:
   - **Best Authenticity:** Record your own voice reading **Full VO script**, or use your CapCut avatar/voice.
   - **Zero-Effort Automated Option:** Under the final step card, tap **Buat audio MP3 + SRT sinkron otomatis** to download `vo_capcut.mp3` and `vo_capcut.srt`, or download **`Download subtitle CapCut (.srt)`** to pair with manual recording.
3. Place scene **On-Screen Headlines** in the upper-middle safe zone (clear of top status chrome and bottom basket/caption overlays).
4. Add subtle BGM at **8%–10% volume** so product knowledge details remain crisp.

### Stage 5: Publish & Maximize Conversion
1. Upload to **Shopee Video** or **TikTok Shop** with the generated platform **Caption & Hashtags**.
2. Attach the product to **Keranjang Oranye / Keranjang Kuning**.
3. **Mandatory Platform Compliance:** Enable the **"AI-generated content / Konten Buatan AI"** toggle before publishing.
4. **Conversion Multiplier:** Immediately paste and **Pin** the generated **`Pinned comment FAQ`** as your first comment to answer buyer objections on the spot.

---

## 3. Format Matrix & Anti-Spam Scaling

| Content Goal | Recommended Duration | Structure Highlights |
| :--- | :--- | :--- |
| **Impulse & fast trend buys** | `15 detik (3 scene)` | Sharp Hook → Core Spec + Demo → Fast CTA |
| **Daily lifestyle & fashion** | `25-30 detik (5 scene)` | Hook → Pain Point → Spec & Demo → Objection Killer → CTA |
| **High-ticket, outdoor gear, or skincare** | `40-45 detik (7 scene deep)` | Hook → Problem → Macro Material Audit → Mechanism Demo → Objection Killer → Pro Tip & Value → CTA |

**Scaling Without Duplicate Flags:**
- **Tap `Regenerate hook`:** Swaps only **Scene 1** while seamlessly bridging into Scene 2—ideal for A/B testing scroll-stop hooks.
- **Tap `Variasi baru (anti-spam)`:** Rebuilds the full angle while cross-checking persistent `hook_history.json` so hooks never repeat prior uploads.

---

## 4. Quick Troubleshooting

| Symptom | Root Cause | Resolution |
| :--- | :--- | :--- |
| **`API key belum terdeteksi` on Cloud** | `.env` is intentionally excluded from Git; Cloud Secrets not configured yet | Open **share.streamlit.io → Settings → Secrets**, paste keys inside `"..."` quotes, and click **Save** |
| **Product legs or frame mutated in Flow** | Lower edge cropped in Ingredient photo, or Product Ingredient unselected on `Jump to` | Reset bottom crop slider to `0%`, re-upload uncropped product photo, and keep Product Ingredient active on every scene |
| **Generated person looks Western or wrong** | Flow avatar mention missing `@me` or wrapped in parentheses | Use current app build—every prompt enforces standalone **`@me`** plus Nusantara facial identity locks |
| **Store URL shows bot-restriction note** | E-commerce site blocks automated crawlers or requires login | Expected behavior—copy-paste the store specs directly into the app's specification text box |
| **Local laptop slows down or hangs** | Background Streamlit sessions left running | Stop with `Ctrl + C` or `pkill -9 -f streamlit`, and run daily workflows on **Streamlit Cloud** instead |
