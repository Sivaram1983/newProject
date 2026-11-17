# Edit Style Breakdown: the "Velocity / Beat-Sync Anime Edit"

Both reference videos are the same genre: **CapCut-style anime "cool edits" of a single hero character** (Tanjiro, Demon Slayer). 720×1280, 9:16. Shot strips: `ref_A_shots.png`, `ref_B_shots.png`.

| | Ref A (`Klickpin…mp4`) | Ref B (`tanjiro-cool-edit`) |
|---|---|---|
| Length | 14.3 s (13.3 s of content + 1 s black) | 8.06 s (7.6 s of content + 0.4 s black) |
| FPS | 30 | 25 |
| Music tempo | ~112 BPM (beat every 0.535 s) | ~117 BPM (beat every 0.51 s) |
| Shots | ~24 | 14 |
| Letterbox | Yes: black bar 40 px top + 40 px bottom after the drop | No |
| Extra layer | Text/article hook with glitches | None, pure footage |

---

## 1. Story structure: Calm, then Breath, then DROP, then Rage, then Black

Both edits follow the same three-act structure, set by the music:

```
[ HOOK / CALM ]  ->  [ BREATH (hold) ]  ->  [ DROP ]  ->  [ RAGE MONTAGE, 1 cut per beat ]  ->  [ HARD CUT TO BLACK ]
   soft faces         eyes closed,          zoom-blur      fire, blood, screaming,              0.4 to 1 s silence
   cool colors        slow push-in          whip into      sword swings, glowing eyes
   1 cut / beat       ~1 s, music dips      fire mask      warm reds and oranges
```

* **Ref B:** Calm 0 to 2.6 s (Nezuko smile, then Tanjiro's innocent faces in blue, orange and white). The breath is 2.6 to 3.56 s: eyes-closed bamboo shot held for 2 beats while the music dips (RMS 0.09). **The drop lands at 3.6 s** on the fire-mask shot (loudness doubles). Rage runs from 3.6 to 7.56 s, and black follows at 7.6 s.
* **Ref A:** The hook runs 0 to 3.1 s, alternating article screenshots ("tatakae" highlighted) with a dark desaturated Tanjiro look-back. Then 0.3 s of pure black (3.1 to 3.37 s) as a silence gap. Next comes a blue double-exposure, then the eyes-closed bamboo breath (3.87 to 4.5 s). **The drop is at 4.6 s** on the fire mask. Rage runs from 4.6 to 13.3 s, and black follows from 13.3 to 14.3 s.
* **Loop trick (Ref A):** the rage section is **one 7-shot sequence played twice** (mask, sword grip, flame slash, scream, fire profile, swing, glowing face, then repeat). This doubles the length with half the clips, and viewers barely notice.
* The end is a hard cut to black on the last beat, with no fade. This makes Shorts auto-loop feel seamless and boosts rewatches.

## 2. Cutting rhythm

* **Every cut lands exactly on a beat.** Shot length is 1 beat (~0.5 s). In Ref A, the detected beats (0.72, 1.30, 2.39, 4.60, 5.13, 5.67, 6.20, 6.76…) match the cut times within 1 to 2 frames.
* The **only shot held longer** is the "breath" shot before the drop (2 beats). That contrast is what makes the drop hit.
* The transition's peak blur frame sits *on* the beat, so the new shot is sharp ~1 to 2 frames after the beat.

## 3. Transitions (decoded frame by frame)

| Name | Where | Frames | What happens |
|---|---|---|---|
| **Zoom-in blur ("pull in")** | Ref B, every cut | 2 to 3 | The outgoing shot scales up ~110 to 130% with heavy radial/gaussian blur. The incoming shot lands sharp. |
| **Directional whip blur** | Ref B (4.0, 4.64, 5.56, 6.16, 7.2 s) | 1 to 2 | A single frame of horizontal/diagonal motion-smeared color, then cut. |
| **Halftone smear** | Ref A, every rage cut | 2 to 3 | Outgoing frame defocuses, then 1 frame of blur with a **comic halftone dot screen**, then the incoming shot enters with directional motion blur that eases to sharp. |
| **Glitch / pixel-sort** | Ref A hook (0.7, 1.8, 2.6 to 3.0 s) | 2 to 4 | Pixel-sort streaks, RGB channel split, block glitches, and color inversion (the yellow highlight flips to **blue**). |
| **Black gap** | Ref A 3.1 to 3.37 s | 8 | Full black and near-silence right before the build. Creates tension. |

## 4. In-shot motion

* **Constant slow push-in** (scale 100 to ~108% over the shot), so no frame is ever static. Ref B's Nezuko opener zooms visibly from 0.08 to 0.48 s.
* **Impact shake / punch-zoom** on the first 2 to 3 frames after a cut in the rage section.
* Clips are often **speed-ramped**: the action plays fast, then slows at the peak pose (sword swing, scream).

## 5. Color and texture

* **Calm section:** clean, bright, slightly cool (cyan or teal backgrounds), soft. Ref A instead uses **desaturated B&W with red accents** for menace.
* **Rage section:** high contrast, crushed blacks, **saturated red, orange and yellow**, with a blue background for contrast (Ref A swing shot).
* **Over-sharpened "HD/4K enhance" look:** strong unsharp mask with visible line-art edges.
* **Glow/bloom** on fire and **bokeh ember particles** (Ref A shots 15 and 16).
* **Halftone dot overlay** on transitions (Ref A). **Chromatic aberration** on the glitch frames.

## 6. Text layer (Ref A only): the hook

* Screenshots of an **article/web page**, zoomed on the keyword **"tatakae"** with a yellow marker highlight.
* Each card does a quick zoom-out from extreme blur to sharp, with bottom lines blurred (depth-of-field look).
* Glitch hits flip the highlight to blue/inverted, add RGB split, and drop small pixel blocks.
* The hook works because the viewer reads one word and gets curious, which stops the scroll in under 1 second.

## 7. Audio

* Phonk/trap-style track with a clear **quiet build, then a drop**. Ref A also has bass hits (strong onsets at 9.22, 9.75, 11.52 s) that the edit punctuates with extra-strong flashes.
* Loudness is flat and loud after the drop (RMS ~0.44 in Ref A), so the music is mastered hot.
* No voiceover and no on-screen captions except the hook text.

## 8. Why these go viral (recipe)

1. **The first 0.5 s is a striking face/eyes close-up or a curiosity-text hook.** There is no intro.
2. The **calm-to-rage contrast** gives an emotional arc in under 15 s.
3. **Beat-perfect cuts** give viewers a "satisfying" feeling that drives replays.
4. **Short (8 to 15 s) with a hard cut to black** makes the loop seamless, which pushes watch time above 100%.
5. **One character, one color story:** cool or desaturated first, then fire red and orange.

---

## Repro spec (what I'll use for your edit)

* 1080×1920 @ 30 fps, music 110 to 120 BPM, total 10 to 15 s.
* 0 to ~3 s hook/calm (4 to 6 shots, 1 per beat). Then a 1 to 2 beat breath hold with slow push-in. Optionally a 0.25 s black gap.
* Drop on a zoom-blur whip into the most intense shot.
* Rage montage: 1 shot per beat, halftone or motion-blur transitions centered on the beat, punch-zoom and shake on impact, glow and embers, high-contrast warm grade. Optionally loop the sequence ×2.
* End on a hard cut to black for 0.4 to 1 s.
