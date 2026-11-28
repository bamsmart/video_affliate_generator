---
name: affiliate-ai-video-director
description: >-
  Use this skill whenever designing, generating, reviewing, or optimizing Google Flow
  (Veo 3.1) affiliate product video prompts, Ingredients-to-Video assets, or Start-to-End Frame
  transitions to prevent product hallucination and enforce visual consistency.
---

# Affiliate AI Video Director — Google Flow (Veo 3.1) Anti-Halu Skill

In affiliate video production, the #1 conversion killer is **product hallucination**—mutated logos, stretched silhouettes, altered legs/frames, or mismatched labels. Reference images are **absolute visual truth** (`@ProductAuthority`), while text prompts must act strictly as concise **camera, composition, and constraint directives**.

> **Creative & Scriptwriting Companion:** For 3-second scroll-stopping UGC hooks, Indonesian direct-response beat sheets, shot-by-shot cinematography grammar, and ready-to-paste Nano Banana / Veo 3.1 templates, use [UGC Director Prompt Studio](../ugc-director-prompt-studio/SKILL.md).

---

## 1. Phase 0 — Visual Storyboard-First & 3-Role Ingredients

Never jump straight from a product photo to video for complex items (folding chairs, bags, shoes, gadgets). Run **Storyboard-First** inside Google Flow's **Image Mode (Nano Banana)**:
1. **Contact Sheet Grid (`2x2`, `3x2`, `3x3`)** or **Master Frame → Derived Keyframes:** Generate static 9:16 keyframes first (cheap, fast, 95%+ shape/logo fidelity), inspect legs & logos, split grid panels via the app's **Auto-Splitter** (`keyframe_1..N.jpg` / ZIP on Laptop), then animate via **Video → Frames (`Start Frame`)**.
2. **3-Role Ingredients:**

Google Flow supports up to three reference images in **Ingredients to Video**. Assign each slot a strict visual job—never upload three mismatched lifestyle shots:

| Reference Role | Core Job | Preparation Guidelines |
| :--- | :--- | :--- |
| **`Product Authority` (`@ProductAuthority`)** | Locks exact silhouette, color, material, legs/base, logo, and label. | Use a clean, uncropped packshot on a solid white/neutral gray background with crisp typography and full bottom legs/base visible. |
| **`Master Frame`** | Locks initial scale, composition, and baseline lighting. | Product (or product + `@me` Indonesian presenter) placed naturally in the target environment. Serves as Scene 1 anchor. |
| **`Interaction Frame`** | Locks hand grip scale and usage ergonomics. | Generate directly from the `Master Frame` rather than an unrelated photo so lighting and lens geometry stay locked. |

**Avatar Mention Rule:** When featuring the user's Google Flow avatar, always place standalone `@me` (surrounded by spaces, never `(@me)`) paired with a concise Indonesian cue (e.g., `@me Indonesian presenter`)—never substitute Caucasian/Western appearance descriptors.

---

## 2. Minimalist Anti-Halu Prompt Formula (Target `< 30` Words, Cap `<= 35` Words)

The longer and more descriptive the text prompt, the more Veo 3.1 fabricates details not present in the keyframe.

```text
[Cinematography / Camera Motion] + [Tagged Ingredients: @ProductAuthority (& @me)] + [Lighting / Setting] + [Explicit Negative Constraints]
```

### Mandatory Directives
1. **Cinematography over Narrative:** Use camera kinematics (`smooth dolly-in`, `slow tracking shot`, `gentle push-in`, `locked-off static camera`, `subtle macro pan`). Never use multi-step narrative verbs (`walks toward`, `picks up`, `opens the door`, `folding`, `unfolding`).
2. **Tag, Do Not Re-Describe:** Call `@ProductAuthority` directly instead of re-writing bottle colors, shapes, caps, leg counts, or logo text inside the prompt (re-describing creates text-vs-image conflict).
3. **Scene Builder Continuity:**
   - `New Scene` (Scene 1): Locks hero framing with `@ProductAuthority`.
   - `Extend`: Start cleanly with `Seamless continuation from the previous frame` and keep the same camera family.
   - `Jump to`: Switch angle/scale while re-tagging `@ProductAuthority` (and `@me` if Avatar mode).
4. **Explicit Anti-Artifact Negative Constraints:** End every prompt cleanly with:
   `No text overlays, no additional logos, no readable screens.`

### Ready-to-Use Example (Under 30 Words)
> `Smooth, continuous dolly-in shot on 9:16 vertical frame. Use @ProductAuthority resting cleanly in morning studio light. Subtle natural foley only. No text overlays, no additional logos, no readable screens.`

---

## 3. Start-to-End Frame Transitions

Use Google Flow's **Start-to-End Frame** feature for exact reveals or position shifts where product geometry must never warp:
1. Supply **Start Frame** (product at Position X).
2. Supply **End Frame** (product at Position Y in matching setting/lighting).
3. Keep the prompt strictly focused on camera lock and ambient lighting shift:
   > `Locked-off static camera transition using start and end frame with @ProductAuthority. Seamless lighting shift from cool twilight to warm morning sunlight. No text overlays, no additional logos, no readable screens.`

---

## 4. Anti-Patterns Validation Checklist

Before finalizing or approving any Google Flow prompt, verify:
- [ ] Word count is concise (`<= 35–40 words`), zero 100+ word narrative paragraphs.
- [ ] `@ProductAuthority` is tagged cleanly (and standalone `@me` when Avatar mode is active).
- [ ] Zero physical re-descriptions of labels, logos, caps, legs, or colors that already exist in `@ProductAuthority`.
- [ ] Zero narrative hallucination verbs (`walks toward`, `picks up`, `opens the door`) or mechanical deformation verbs (`folding`, `unfolding`, `collapsing`, `morphing`).
- [ ] Zero square meta-brackets (`[...]`) and zero double quotation marks (`"`).
- [ ] Explicit end constraint present: `No text overlays, no additional logos, no readable screens.`
