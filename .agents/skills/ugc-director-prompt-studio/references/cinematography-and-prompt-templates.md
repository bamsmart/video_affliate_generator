# Cinematography Grammar & Veo 3.1 Prompt Templates

Every template below enforces **Storyboard-First precision** and Google Flow's **Anti-Halu <= 35-word rule**. All Veo 3.1 prompts exclude square brackets `[...]`, double quotes `"`, re-descriptions of colors/labels already in `@ProductAuthority`, and narrative/deformation verbs.

---

## 1. Audio-Visual Beat-to-Shot Grammar

Match every scriptwriter beat to purposeful framing and camera kinematics:

| Script Beat | Primary Shot Scale | Safe Veo 3.1 Camera Move | Natural Audio / Foley Cue |
| :--- | :--- | :--- | :--- |
| **Hook (Scene 1)** | Medium Close-Up / Hero 3/4 | `Gentle push-in shot` or `Smooth dolly-in shot` | Subtle natural room tone, no spoken dialogue |
| **Relatable Problem** | Medium Environmental | `Locked-off static camera` or `Slow tracking shot` | Soft interior ambiance only |
| **Material Proof** | Tight Macro Detail | `Slow macro pan` or `Subtle macro close-up` | Crisp natural texture foley only |
| **Real-World Demo** | Medium Lifestyle (`@me` + Product) | `Steady handheld-style tracking shot` | Gentle ambient daylight room tone |
| **Objection Killer** | Clean Eye-Level Proof | `Locked-off static camera` | Clean natural room tone, silent voice track |
| **Closing CTA** | Clean Hero 3/4 | `Smooth continuous dolly-in shot` | Subtle warm ambient foley only |

---

## 2. Safe Kinematics vs. Banned Hallucination Verbs

| Use (Safe Cinematography & Presence) | Never Use (Hallucination & Deformation Triggers) |
| :--- | :--- |
| `Smooth dolly-in shot`, `Gentle push-in shot`, `Slow tracking shot`, `Locked-off static camera`, `Slow macro pan`, `Subtle orbit arc` | `walks toward`, `picks up`, `opens the door`, `opens the cap`, `grabs`, `unpacks`, `twists`, `rotates`, `bends`, `sits down`, `stands up` |
| `Product rests steadily on tabletop`, `@me Indonesian presenter beside @ProductAuthority`, `Calm confident expression` | `folds`, `unfolds`, `collapses`, `assembles`, `disassembles`, `morphs`, plus any color+part phrases like `black cap`, `white label`, `steel frame` |

---

## 3. Phase 0: Nano Banana Storyboard Grid & Keyframe Prompts (Image Mode)

Run these in Google Flow **Image Mode (Nano Banana)** with `Product Authority` attached (plus `@me` if Creator mode) before video generation.

### Contact Sheet Grid (`3x2` Creator `@me` Template)
```text
Create a clean 3x2 vertical 9:16 contact sheet grid showing 6 cohesive Indonesian UGC frames featuring @me Indonesian presenter and @ProductAuthority in one bright minimalist Indonesian living room: panel 1 medium hook, panel 2 problem setup, panel 3 tight material close-up, panel 4 natural usage pose, panel 5 proof check, panel 6 clean hero CTA. Consistent warm daylight and sharp 1:1 product fidelity. No text overlays, no borders with letters.
```

### Contact Sheet Grid (`2x2` Faceless B-Roll Template)
```text
Create a clean 2x2 vertical 9:16 contact sheet grid showing 4 cohesive aesthetic studio scenes with @ProductAuthority in bright natural Indonesian morning window light: panel 1 hero 3/4 wide, panel 2 macro texture detail, panel 3 minimalist tabletop lifestyle context, panel 4 dramatic rim-lit hero angle. Exact product fidelity across all panels. No text overlays, no watermarks.
```

### Single Keyframe Templates (`keyframe_image_prompt_en`)
- **Creator Master Frame:**
  ```text
  9:16 vertical lifestyle photograph of @me Indonesian presenter in natural morning Indonesian home daylight beside @ProductAuthority on a clean minimalist surface, medium close-up, soft natural shadows, crisp focus, authentic smartphone creator look.
  ```
- **Faceless Macro Proof Frame:**
  ```text
  9:16 vertical commercial macro photograph of @ProductAuthority resting cleanly on warm stone surface under soft directional window sunlight, shallow depth of field, crisp material texture, clean minimal styling.
  ```

---

## 4. Google Flow (Veo 3.1) Motion Prompts (`<= 35` Words — Verified Anti-Halu)

Every sample below is strictly under 35 words, free of brackets/quotes/re-descriptions, and ends with the mandatory negative constraint suffix.

### Scene 1 — `New Scene` (Creator `@me` Hook)
```text
Gentle push-in shot on 9:16 frame with @me Indonesian presenter calmly presenting @ProductAuthority in bright Indonesian living room daylight. Subtle room tone only. No text overlays, no additional logos, no readable screens.
```

### Scene 1 — `New Scene` (Faceless Hero B-Roll Hook)
```text
Smooth dolly-in shot on 9:16 frame showcasing @ProductAuthority resting cleanly on minimalist pedestal under warm morning sunlight. Subtle ambient foley only. No text overlays, no additional logos, no readable screens.
```

### Scene 2 — `Extend` (Seamless Continuation)
```text
Seamless continuation from the previous frame, gentle push-in shot keeping @me Indonesian presenter and @ProductAuthority steady in warm natural daylight. Subtle room tone only. No text overlays, no additional logos, no readable screens.
```

### Scene 3 — `Jump to` (Macro Material Proof)
```text
Slow macro pan across @ProductAuthority resting steadily on minimalist tabletop under crisp directional daylight. Soft natural texture foley only. No text overlays, no additional logos, no readable screens.
```

### Scene 4 — `Jump to` (Clean Lifestyle Demo / Proof)
```text
Slow tracking shot framing @me Indonesian presenter naturally beside @ProductAuthority in cozy sunlit Indonesian corner. Subtle ambient room tone only. No text overlays, no additional logos, no readable screens.
```

### Transition — `Start-to-End Frame` (Exact Two-Keyframe Reveal)
```text
Locked-off static camera transition using start and end frame with @ProductAuthority. Seamless lighting shift from cool twilight to warm morning sunlight. No text overlays, no additional logos, no readable screens.
```
