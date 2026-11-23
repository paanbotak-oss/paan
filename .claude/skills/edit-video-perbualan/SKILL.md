---
name: edit-video-perbualan
description: Edit a talking-head / conversation video (doctor Q&A, explainer, podcast clip) in the user's house style with HyperFrames — cut dead pauses and broken bits, add conversation-series motion, extruded 3D keywords, 3D cards and cube, chapter flip-sign, synthesized sound effects and a ducked music bed. Use whenever the user sends a video (Google Drive link, file) and asks to "edit video", "buang jeda", "letak motion", "3D", "sound effect", "music", or says "edit macam biasa / cara sama".
---

# Edit video perbualan (house style)

The user (Malay speaker, writes casual Malay) wants most videos edited exactly like
`edit/videos/lutut-bengkak` (Mega Care Clinic knee video). Reply in casual Malay.
Reference result: `edit/output/lutut-bengkak-final.mp4`; its plan: `edit/videos/lutut-bengkak/plan.json`.

## Toolkit (all in `edit/`)
| file | job |
|---|---|
| `scripts/analyze.py SRC WORK` | contact sheets, scene changes, Demucs voice split, VAD gaps, Malay transcript |
| `videos/<name>/plan.json` | **the only per-video file**: cuts + every overlay/SFX time |
| `scripts/make.sh videos/<name> SRC WORK` | cut → music bed → build → `hyperframes check` → render → `output/<name>.mp4` |
| `scripts/cut.py`, `build.py`, `sfx.py`, `music_bed.py`, `musicgen.py` | the steps make.sh runs |
| `project/` | the HyperFrames project (index.html is generated — edit plan/build.py, not index.html) |

## Setup (fresh container)
- Network hosts needed (environment "paan" already has them): `drive.google.com`,
  `drive.usercontent.google.com`, `huggingface.co`, `us.aws.cdn.hf.co`, `dl.fbaipublicfiles.com`.
  If a host is refused, propose it with update_environment.
- `cd edit && npm install` (hyperframes + gsap pinned), `pip install faster-whisper demucs soundfile torch transformers`.
- Always `export HF_HUB_DISABLE_XET=1` (Xet host is blocked). Run Python with `-I`.
- Drive download: `curl -sSL -o source.mp4 "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`
  into its own scratchpad folder.

## Workflow
1. **Download + analyze**: `python3 -I scripts/analyze.py source.mp4 $WORK`. Read every contact sheet
   (`$WORK/sheets/`), `vad.txt`, `transcript.txt`, `scenes.txt`. For each suspicious moment make a
   10 fps sheet (`ffmpeg -ss T -t 2 ... fps=10,tile=10x5`) and look.
2. **Decide cuts (`keep`, source seconds)**. Remove: dead gaps ≥ ~0.35 s (from VAD on the *isolated
   voice* — the original mix usually has loud TikTok music so energy-based silence detection fails),
   walking/setup with no speech, blurry/black/flash frames, stuck frames, long static outro (keep ~4.5 s).
   **Never cut mid-word.** If a broken old transition sits under speech, keep the audio and *cover the
   video* with a 3D card or white flash instead (L-cut style).
3. **Map to output time** (edl.json after a first `cut.py` run, or compute offsets) and write `plan.json`.
4. **Run** `scripts/make.sh videos/<name> source.mp4 $WORK`; it must end with `Check passed`.
5. **Look**: `cd project && npx hyperframes snapshot --at t1,t2,...` at every card/keyword and read the
   contact sheets before rendering/delivering. After render, make a 1/4 fps sheet of the final MP4 and look.
6. **Deliver**: SendUserFile the `output/<name>.mp4`; list what was cut (with times) and what was added;
   say you can't hear audio so they should check music/SFX levels. Commit + push scripts, plan and the
   final MP4 (< 100 MB). Never commit `project/assets/base.mp4`, `voice.wav`, `music_bed.wav` (gitignored).

## plan.json format (output seconds unless noted)
```jsonc
{
 "keep": [[0.0, 3.22], [3.47, 17.21]],            // SOURCE seconds, in order
 "outro_start": 96.3,                             // top gradient stops here (clinic outro card)
 "chapters": [[0.35, 12.95, "SOAL JAWAB", "LUTUT BENGKAK"]],   // 3D flip sign, top: kicker + title
 "keywords": [[14.6, 16.45, ["GOUT"], "impact", 180]],          // style pop|impact|crunch, size px (auto-shrunk)
 "checklist": [41.35, 44.4, [[41.35, "1", "FIZIKAL"], [42.4, "2", "ULTRASOUND"]]],   // or null
 "cards": [[33.05, 36.3, "SOALAN", ["MACAM MANA", "NAK PERIKSA?"], "Gout atau Osteoarthritis?", "title"],
           [16.55, 17.55, "PUNCA #1|PUNCA #2", ["GOUT", "OSTEO-", "ARTHRITIS"], "", "cube"]],
 "flashes": [[2.9, 3.36]],                        // white stinger over a 0.2–0.5 s bad bit
 "cam": [[0, 1.22, "set"], [0.05, 1.04, "intro"], [12.99, 1.14, "set"], [14.6, 1.22, "punch"], [15.9, 1.1, "ease"]],
 "shakes": [14.6],
 "sfx": [[14.58, "impact", 0.5]]                  // whoosh whoosh_long pop impact riser tick ding crunch stinger
}
```

## House style rules
- **Canvas** 1080×1920, 30 fps. Brand: navy `#071a33`, teal `#19c3b1`, gold `#ffd23f`, Inter Display Black.
- **Burned-in captions sit at the bottom (≈78–86 % height)** and the clinic logo top-left — put all
  graphics in the top band: chapter sign y≈196 px, 3D keywords y≈330–750 px. Keep text inside the TikTok
  safe area (build.py auto-fits width to ~760 px).
- **Conversation motion**: every jump cut alternates zoom (1.00 ↔ 1.10–1.15, hard `set`); `punch` (to
  ~1.2) + `shakes` + `impact` SFX on the key medical term; slow drift between keys; intro zoom-out from
  1.22; progress bar on top; 0.6 s fade to black at the end.
- **3D**: extruded keywords (16 stacked layers) that fly in and slowly rotate; full-screen cards with
  perspective grid floor that flip up and away; cube rotating between two items (e.g. PUNCA #1 → #2);
  checklist items that flip in. One keyword roughly every 5–15 s — key terms only, 1–2 words per line.
- **Cards**: start ~0.1–0.2 s *before* the bad footage, end after it; hold ≥ 0.8 s; use them for section
  questions ("MACAM MANA NAK PERIKSA?", "SIAPA LAGI?", "LANGKAH 2").
- **Sound**: voice = Demucs vocals (old music dropped). Music = MusicGen lofi bed looped, sidechain-ducked:
  ≈ −27 LUFS under speech, ≈ −16 LUFS in gaps. SFX 0.3–0.55 volume: whoosh on cards/scene changes,
  pop on keywords, impact on punch words, tick on chapter flips, riser before a big card, ding on outro.
  Final master loudnorm −14 LUFS / −1.5 dBTP.

## Gotchas already solved
- `<video>` must not be inside a timed element: `#cam` wrapper has no `data-start`.
- `.card-flip` must be `transform-style: flat` or rotated 3D titles get clipped by the card background.
- Extrusion layers carry `data-layout-ignore` (otherwise `text_occluded` errors); cube faces too.
- faster-whisper + this PyAV: pass raw float samples, not a file path (`metadata_errors` TypeError).
- Whisper segment times drift ±0.5 s — use burned captions + VAD for timing, whisper for words.
- Render master is ~150 MB: re-encode (make.sh does) before committing/sending.
