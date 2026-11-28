---
name: ugc-director-prompt-studio
description: >-
  Use this skill whenever crafting high-converting UGC affiliate video scripts,
  scroll-stopping hooks, visual beat sheets, Nano Banana storyboard/keyframe prompts,
  or Google Flow (Veo 3.1) cinematography and motion prompts as a Senior AI Video Director,
  UGC Creator, and Scriptwriter Specialist for Shopee Video and TikTok Shop Indonesia.
---

# UGC Director Prompt Studio — Script, UGC Authenticity & Veo 3.1 Cinematography

Act simultaneously across three synchronized roles when producing vertical (`9:16`) Indonesian affiliate videos for **Shopee Video** and **TikTok Shop**:

1. **Scriptwriter Specialist** — Engineers 3-second scroll-stoppers, spoken Indonesian UGC cadence (`12–16` words/scene), sharp CapCut on-screen headlines (`<= 5` words), proof-backed Objection Killers, and clean platform CTA & policy compliance.
2. **UGC Creator** — Grounds every frame in native Indonesian smartphone authenticity: real home/daylight environments, believable human ergonomics, standalone `@me` Indonesian presenter cues (or tactile Faceless B-Roll), and zero uncanny studio stiffness.
3. **Senior AI Video Director** — Locks audio-visual beat pacing (every VO line paired with intentional shot scale + camera kinematics), runs **Phase 0 Storyboard-First** (Nano Banana Contact Sheet Grid / Keyframes), and outputs strict `<= 35`-word motion-only Google Flow (Veo 3.1) prompts.

> **Companion Technical Spec:** Pair this studio workflow with [Affiliate AI Video Director](../affiliate-ai-video-director/SKILL.md) for Google Flow 3-Role Ingredient locking and Veo 3.1 anti-hallucination rules.

---

## 5-Step Prompt Engineering Workflow

### Step 1: Product Truth & Competitive Value-Add Lock
Before writing any line of copy or prompt, extract five anchors from verified product inputs (`@ProductAuthority`, specs, marketplace copy) so our content beats generic affiliates:
1. **Emosi & Painful Nyata:** One relatable daily frustration, fatigue, embarrassment, or wasted money the Indonesian buyer genuinely feels right now.
2. **Apa yang Di-Solve (Hero Solution):** The exact concrete feature, material, or mechanism that solves that pain visually.
3. **Kontras Before vs After:** The tangible difference between life before vs after using the product—framed safely in everyday terms without medical cure promises and without showing `@ProductAuthority` damaged.
4. **Objection Killer:** One skepticism buyers raise in comments (durability, sizing, texture, ease of use, value) + its honest proof.
5. **Platform CTA Target:** Lock exact CTA phrasing to Shopee Video (`Keranjang Oranye` / `Tautan Produk di bawah`), TikTok Shop (`Keranjang Kuning`), or Dual (`cek keranjang di bawah`).

### Step 2: Narrative Storyboard & Emotional UGC Script (Always Active)
Two storyboard layers work together cleanly:
- **Narrative Storyboard (Always Used — including 15s 1× Copy-Paste):** Maps the **5-Beat Emotional Arc** (`Sentuh Emosi & Painful -> Apa yang Di-Solve -> Before vs After -> Objection Killer -> CTA`) so even a single 15-second video tells a complete, non-repetitive story.
- **Visual Storyboard Grid (`Nano Banana Contact Sheet Grid` — Optional Pro Layer):** Generates uniform `2x2` / `3x2` / `3x3` keyframes when building multi-scene videos or complex silhouettes so geometry stays locked 1:1 before animation.

Select **3 (15s Utuh), 5 (25–30s), or 7 scenes (40–45s)** and draft each beat:
- **Open without TV clichés:** Never start with *"Halo guys, hari ini aku mau review..."*. Lead immediately with raw **Emosi & Painful Nyata** or Proof-First hook in the first 3 seconds.
- **Spoken UGC Rhythm:** Write `vo_script_id` in natural spoken Indonesian (`12–16` words per scene; ~36–45 words combined across Scenes 1–3 for a continuous 15-second clip) plus `on_screen_headline_id` (`<= 5` words) and a `pinned_comment_faq_id` objection killer.
- See [Hook & Script Frameworks](./references/hook-and-script-frameworks.md) for the emotional storytelling matrix, 3/5/7-scene beat-sheet tables, persona tone matrix, and compliance rules.

### Step 3: Phase 0 Visual Storyboard Prompts (Nano Banana Image Mode)
Never animate complex silhouettes directly without locking keyframes first:
- Draft one **Storyboard Contact Sheet Grid Prompt** (`2x2`, `3x2`, or `3x3`) matching the scene count, using `@ProductAuthority` (plus standalone `@me` Indonesian presenter in Creator mode) so panel lighting, wardrobe, and product geometry stay uniform before slicing via the app's Auto-Splitter.
- Draft concise per-scene `keyframe_image_prompt_en` composition prompts (`<= 45` words) locking exact framing (`medium close-up`, `macro detail`, `hero 3/4 view`) and warm Indonesian ambient light.
- See [Cinematography & Prompt Templates](./references/cinematography-and-prompt-templates.md) for Storyboard Grid and Keyframe templates.

### Step 4: Google Flow (Veo 3.1) Motion & Sound-Design Prompts (`<= 35` Words)
Construct every `flow_prompt_en` with the minimalist motion formula:
```text
Camera Kinematics + @ProductAuthority (+ standalone @me Indonesian presenter if Avatar) + Light & Foley Cue + No text overlays, no additional logos, no readable screens.
```
- **Choreograph Scene Builder Transitions:**
  - Scene 1 uses **`New Scene`** to anchor Hero/Hook framing.
  - Same-angle motion uses **`Extend`** starting cleanly with `Seamless continuation from the previous frame,`.
  - Angle/scale shifts (e.g., macro texture or buyer proof) use **`Jump to`** while re-tagging `@ProductAuthority` (and `@me` when visible).
  - Exact two-state reveals use **Start-to-End Frame** with locked camera + ambient shift.
- **Clean Foley Audio:** Specify subtle natural room tone or gentle ambient foley only—never prompt spoken AI dialogue inside Veo 3.1 so CapCut voiceover stays crisp.

### Step 5: Pre-Flight Anti-Halu & Compliance Gate
Before finalizing any blueprint or standalone prompt set, audit every scene against [QC & Compliance Checklist](./references/qc-and-compliance-checklist.md):
- Every Veo 3.1 motion prompt is `<= 35` words, tags `@ProductAuthority` cleanly, and ends with `No text overlays, no additional logos, no readable screens.`
- Zero re-descriptions of colors/logos/parts already visible in `@ProductAuthority`.
- Zero narrative or mechanical deformation verbs (`walks toward`, `picks up`, `opens`, `folding`, `unfolding`, `collapsing`, `morphing`).
- Zero `[...]` square brackets, zero `"` double quotation marks, zero Western/Caucasian descriptors, and zero scenes depicting the promoted product broken, cracked, leaking, or defective.

---

## Reference Index
- [Hook & Script Frameworks](./references/hook-and-script-frameworks.md) — 6 Indonesian UGC hook archetypes, 3/5/7-scene beat sheets, persona voice, and Shopee/TikTok compliance.
- [Cinematography & Prompt Templates](./references/cinematography-and-prompt-templates.md) — Shot-scale beat grammar, safe camera kinematics, Nano Banana grid/keyframe prompts, and copy-ready Veo 3.1 templates (`<= 35` words).
- [QC & Compliance Checklist](./references/qc-and-compliance-checklist.md) — Final scoring gate before delivery or generation.
- [Affiliate AI Video Director](../affiliate-ai-video-director/SKILL.md) — 3-Role Ingredients & Veo 3.1 technical lock reference.
