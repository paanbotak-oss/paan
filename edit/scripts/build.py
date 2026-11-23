"""Builds PROJECT/index.html (HyperFrames composition) from a video plan.

Usage: python3 build.py PLAN.json PROJECT_DIR
All times in the plan are OUTPUT seconds (after the cuts made by cut.py).
See .claude/skills/edit-video-perbualan/SKILL.md for the plan format.
"""
import html, json, sys

PLAN = json.load(open(sys.argv[1]))
PROJECT = sys.argv[2] if len(sys.argv) > 2 else "project"
DUR = json.load(open(f"{PROJECT}/assets/edl.json"))["duration"]
CHAPTERS = PLAN.get("chapters", [])
KEYWORDS = PLAN.get("keywords", [])
CHECKLIST = PLAN.get("checklist")
CARDS = PLAN.get("cards", [])
FLASHES = PLAN.get("flashes", [])
CAM = PLAN.get("cam", [])
SHAKES = PLAN.get("shakes", [])
SFX = PLAN.get("sfx", [])
SFX_LEN = {"whoosh": 0.6, "whoosh_long": 1.0, "pop": 0.2, "impact": 1.25, "riser": 1.05,
           "tick": 0.1, "ding": 1.45, "crunch": 0.5, "stinger": 0.45}

esc = html.escape


def layers3d(text, depth, cls="t3d"):
    """Real extruded 3D text: stacked copies along Z inside a preserve-3d box."""
    out = [f'<span class="{cls}-side" data-layout-ignore style="transform:translateZ({-i * 2.2:.1f}px);'
           f'opacity:{1 - i / (depth * 1.6):.3f}">{esc(text)}</span>' for i in range(depth, 0, -1)]
    out.append(f'<span class="{cls}-face">{esc(text)}</span>')
    return "".join(out)


def build():
    els, n = [], 0

    def clip(start, end, inner, cls="", eid=None, z=10):
        nonlocal n
        n += 1
        eid = eid or f"c{n}"
        els.append(f'<div id="{eid}" class="clip {cls}" data-start="{start:.2f}" '
                   f'data-duration="{end - start:.2f}" data-track-index="{z}" style="z-index:{z}">{inner}</div>')
        return eid

    # chapters
    chap_ids = []
    for s, e, kicker, title in CHAPTERS:
        inner = (f'<div class="chip-wrap"><div class="chip"><span class="chip-dot"></span>'
                 f'<span class="chip-k">{esc(kicker)}</span><span class="chip-t">{esc(title)}</span></div></div>')
        chap_ids.append((clip(s, e, inner, "chapter", z=20), s, e))

    # keywords
    kw_ids = []
    for s, e, lines, style, size in KEYWORDS:
        size = min(size, int(760 / (0.68 * max(len(l) for l in lines))))
        rows = "".join(f'<div class="kw-row">{layers3d(l, 16)}</div>' for l in lines)
        inner = (f'<div class="kw-stage"><div class="kw-shadow"></div>'
                 f'<div class="kw-3d" style="font-size:{size}px">{rows}</div></div>')
        kw_ids.append((clip(s, e, inner, f"kw kw-{style}", z=30), s, e, style))

    # checklist
    ck_id = None
    if CHECKLIST:
      s, e, items = CHECKLIST
      rows = "".join(f'<div class="ck-item" data-at="{t}"><span class="ck-num">{esc(num)}</span>'
                   f'<span class="ck-txt">{esc(txt)}</span></div>' for t, num, txt in items)
      ck_id = clip(s, e, f'<div class="ck-stage"><div class="ck-3d">{rows}</div></div>', "checklist", z=30)

    # cards
    card_ids = []
    for s, e, kicker, lines, sub, kind in CARDS:
        dots = "".join(f'<i style="left:{(i * 397) % 1000 / 10:.1f}%;top:{(i * 613) % 1000 / 10:.1f}%;'
                       f'animation-delay:0s;--d:{(i * 7) % 5 + 2}"></i>' for i in range(28))
        if kind == "cube":
            # cube: kicker "FRONT KICKER|BACK KICKER", lines[0] = front word, lines[1:] = back lines
            k1, k2 = (kicker.split("|") + [""])[:2]
            back = "".join(f'<div class="cf-small">{layers3d(l, 10, "c3d")}</div>' for l in lines[1:])
            body = ('<div class="cube-stage"><div class="cube">'
                    f'<div class="cube-face f-front" data-layout-ignore><span class="cf-k">{esc(k1)}</span>{layers3d(lines[0], 10, "c3d")}</div>'
                    f'<div class="cube-face f-bottom" data-layout-ignore><span class="cf-k">{esc(k2)}</span>{back}</div>'
                    '</div></div>')
        else:
            fit = min(150, int(740 / (0.68 * max(len(l) for l in lines))))
            t_rows = "".join(f'<div class="kw-row">{layers3d(l, 18)}</div>' for l in lines)
            body = (f'<div class="card-text">'
                    + (f'<div class="card-kicker">{esc(kicker)}</div>' if kicker else "")
                    + f'<div class="card-3d" style="font-size:{fit}px">{t_rows}</div>'
                    + (f'<div class="card-sub">{esc(sub)}</div>' if sub else "")
                    + '</div>')
        inner = (f'<div class="card-flip"><div class="card-bg"><div class="grid-floor"></div>'
                 f'<div class="glow"></div><div class="dots">{dots}</div></div>{body}</div>')
        card_ids.append((clip(s, e, inner, f"card card-{kind}", z=50), s, e, kind))

    flash_ids = [(clip(s, e, '<div class="flash"></div>', "flashclip", z=60), s, e) for s, e in FLASHES]

    audio = [f'<audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{DUR:.2f}" '
             f'data-volume="1" data-track-index="1"></audio>',
             f'<audio id="music" src="assets/music_bed.wav" data-start="0" data-duration="{DUR:.2f}" '
             f'data-volume="1" data-fade-out="1.5" data-track-index="2"></audio>']
    for i, (t, name, vol) in enumerate(SFX):
        audio.append(f'<audio id="sfx{i}" src="assets/sfx/{name}.wav" data-start="{t:.2f}" '
                     f'data-duration="{SFX_LEN[name]:.2f}" data-volume="{vol}" data-track-index="{3 + i % 3}"></audio>')

    timeline = {
        "dur": DUR, "cam": CAM, "shakes": SHAKES,
        "chapters": [[i, s, e] for i, s, e in chap_ids],
        "keywords": [[i, s, e, st] for i, s, e, st in kw_ids],
        "checklist": [ck_id, CHECKLIST[0], CHECKLIST[1], [t for t, _, _ in CHECKLIST[2]]] if CHECKLIST else None,
        "cards": [[i, s, e, k] for i, s, e, k in card_ids],
        "flashes": [[i, s, e] for i, s, e in flash_ids],
    }
    page = TEMPLATE.replace("{{DUR}}", f"{DUR:.2f}") \
        .replace("{{TOPFADE}}", f"{PLAN.get('outro_start', DUR):.2f}") \
        .replace("{{ELEMENTS}}", "\n      ".join(els)) \
        .replace("{{AUDIO}}", "\n      ".join(audio)) \
        .replace("{{DATA}}", json.dumps(timeline))
    open(f"{PROJECT}/index.html", "w").write(page)
    print("wrote", f"{PROJECT}/index.html", len(els), "clips", len(audio), "audio")


TEMPLATE = r"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face { font-family: "HF Display"; src: url("assets/fonts/InterDisplay-Black.otf"); font-weight: 900; }
      @font-face { font-family: "HF Display"; src: url("assets/fonts/InterDisplay-ExtraBold.otf"); font-weight: 800; }
      @font-face { font-family: "HF Text"; src: url("assets/fonts/Inter-SemiBold.otf"); font-weight: 600; }
      :root {
        --navy: #071a33; --navy2: #0d2d55; --teal: #19c3b1; --teal-d: #0a6f6a;
        --gold: #ffd23f; --ink: #ffffff; --side: #063b4a;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden;
              font-family: "HF Display", sans-serif; color: var(--ink); background: #000; }
      .clip { position: absolute; inset: 0; pointer-events: none; }

      /* footage + camera rig */
      #cam { position: absolute; inset: 0; transform-origin: 50% 40%; will-change: transform; }
      #base { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }
      #vignette { position: absolute; inset: 0; z-index: 5;
        background: radial-gradient(ellipse 85% 70% at 50% 42%, transparent 55%, rgba(0,0,0,.42) 100%); }
      #topfade { position: absolute; left: 0; right: 0; top: 0; height: 520px; z-index: 6;
        background: linear-gradient(rgba(4,14,30,.55), rgba(4,14,30,0)); }

      /* progress */
      #progress-track { position: absolute; left: 0; right: 0; top: 0; height: 12px; z-index: 70; background: rgba(255,255,255,.18); }
      #progress { position: absolute; left: 0; top: 0; height: 12px; width: 1080px; z-index: 71; transform-origin: 0 50%;
        background: linear-gradient(90deg, var(--teal), var(--gold)); }

      /* chapter flip sign */
      .chapter { perspective: 900px; }
      .chip-wrap { position: absolute; left: 0; right: 0; top: 196px; display: flex; justify-content: center; }
      .chip { display: flex; align-items: center; gap: 18px; padding: 18px 34px 18px 26px; border-radius: 20px;
        background: linear-gradient(180deg, rgba(13,45,85,.94), rgba(7,26,51,.94));
        border: 3px solid rgba(25,195,177,.85); box-shadow: 0 18px 40px rgba(0,0,0,.35);
        transform-origin: 50% 50% -40px; backface-visibility: hidden; }
      .chip-dot { width: 18px; height: 18px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 18px var(--teal); }
      .chip-k { font: 800 30px "HF Display"; letter-spacing: .08em; color: var(--gold); }
      .chip-t { font: 900 36px "HF Display"; letter-spacing: .02em; }

      /* extruded 3D text */
      .kw-stage, .ck-stage { position: absolute; left: 0; right: 0; top: 330px; height: 420px;
        display: flex; align-items: center; justify-content: center; perspective: 1100px; }
      .kw-3d, .card-3d { position: relative; transform-style: preserve-3d; text-align: center; line-height: .98; }
      .kw-row { position: relative; display: grid; transform-style: preserve-3d; justify-items: center; }
      .kw-row > span { grid-area: 1 / 1; font-weight: 900; letter-spacing: -.02em; white-space: nowrap; }
      .t3d-side, .c3d-side { color: var(--side); -webkit-text-stroke: 2px #03222b; }
      .t3d-face { background: linear-gradient(180deg, #ffffff 30%, var(--gold) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        -webkit-text-stroke: 2px rgba(255,255,255,.35); }
      .kw-impact .t3d-face { background: linear-gradient(180deg, #fff 20%, #ffe066 60%, #ff9f1c 100%);
        -webkit-background-clip: text; background-clip: text; }
      .kw-crunch .t3d-face { background: linear-gradient(180deg, #fff 10%, #ff6b6b 100%);
        -webkit-background-clip: text; background-clip: text; }
      .kw-crunch .t3d-side { color: #4a0d0d; }
      .kw-shadow { position: absolute; width: 760px; height: 120px; top: 330px; border-radius: 50%;
        background: radial-gradient(ellipse, rgba(0,0,0,.55), transparent 70%); }

      /* checklist */
      .ck-3d { transform-style: preserve-3d; display: flex; flex-direction: column; gap: 26px; }
      .ck-item { display: flex; align-items: center; gap: 26px; padding: 22px 44px 22px 22px; border-radius: 28px;
        background: linear-gradient(180deg, rgba(13,45,85,.95), rgba(7,26,51,.95)); border: 3px solid var(--teal);
        box-shadow: 0 24px 50px rgba(0,0,0,.4); transform-origin: 0 50%; }
      .ck-num { width: 96px; height: 96px; border-radius: 22px; display: grid; place-items: center;
        background: var(--gold); color: var(--navy); font: 900 64px "HF Display"; }
      .ck-txt { font: 900 78px "HF Display"; letter-spacing: -.01em; }

      /* full-screen cards */
      .card { perspective: 1400px; }
      .card-flip { position: absolute; inset: 0; transform-style: flat; transform-origin: 50% 0%; }
      .card-bg { position: absolute; inset: 0; overflow: hidden;
        background: radial-gradient(ellipse 120% 70% at 50% 35%, #12437a 0%, var(--navy) 60%, #030b18 100%); }
      .grid-floor { position: absolute; left: -50%; right: -50%; bottom: -10%; height: 70%;
        background-image: linear-gradient(rgba(25,195,177,.55) 2px, transparent 2px),
                          linear-gradient(90deg, rgba(25,195,177,.55) 2px, transparent 2px);
        background-size: 120px 120px; transform: perspective(700px) rotateX(68deg); transform-origin: 50% 0%;
        -webkit-mask-image: linear-gradient(transparent, #000 40%); mask-image: linear-gradient(transparent, #000 40%); }
      .glow { position: absolute; width: 900px; height: 900px; left: 90px; top: 380px; border-radius: 50%;
        background: radial-gradient(circle, rgba(25,195,177,.35), transparent 65%); }
      .dots i { position: absolute; width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.55); }
      .card-text { position: absolute; left: 0; right: 0; top: 520px; display: flex; flex-direction: column;
        align-items: center; gap: 34px; perspective: 1200px; transform-style: preserve-3d; }
      .card-kicker { font: 800 46px "HF Display"; letter-spacing: .22em; color: var(--teal);
        padding: 10px 30px; border: 3px solid var(--teal); border-radius: 999px; }
      .card-3d { font-size: 150px; line-height: 1.12; }
      .card-sub { font: 600 46px "HF Text"; color: rgba(255,255,255,.88); }

      /* cube */
      .cube-stage { position: absolute; left: 0; right: 0; top: 560px; height: 600px; display: flex;
        justify-content: center; align-items: center; perspective: 1600px; }
      .cube { position: relative; width: 740px; height: 520px; transform-style: preserve-3d; }
      .cube-face { position: absolute; inset: 0; border-radius: 40px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 10px; transform-style: preserve-3d;
        background: linear-gradient(180deg, #164e8c, #0a2547); border: 4px solid var(--teal);
        box-shadow: inset 0 0 80px rgba(25,195,177,.25); backface-visibility: hidden; }
      .f-front { transform: translateZ(260px); }
      .f-bottom { transform: rotateX(-90deg) translateZ(260px); }
      .cf-k { font: 800 54px "HF Display"; letter-spacing: .16em; color: var(--gold); }
      .cube-face .kw-row, .cube-face .cf-small { font-size: 190px; }
      .cube-face .cf-small { font-size: 96px; display: grid; justify-items: center; transform-style: preserve-3d; }
      .cube-face .cf-small > span, .cube-face > span.c3d-face, .cube-face > span.c3d-side { grid-area: 1/1; }
      .f-front { display: grid; place-items: center; }
      .f-front > * { grid-area: 1 / 1; }
      .f-front .cf-k { transform: translateY(-170px); }
      .f-front .c3d-face, .f-front .c3d-side { font-size: 180px; font-weight: 900; }
      .c3d-face { color: #fff; }

      .flash { position: absolute; inset: 0; background: #fff; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{DUR}}" data-width="1080" data-height="1920">
      <div id="cam">
        <video id="base" src="assets/base.mp4" muted playsinline data-start="0" data-duration="{{DUR}}" data-track-index="0"></video>
      </div>
      <div id="vignette" class="clip" data-start="0" data-duration="{{DUR}}" data-track-index="4"></div>
      <div id="topfade" class="clip" data-start="0" data-duration="{{TOPFADE}}" data-track-index="5"></div>
      <div id="progress-track" class="clip" data-start="0" data-duration="{{DUR}}" data-track-index="70"></div>
      <div id="progress" class="clip" data-start="0" data-duration="{{DUR}}" data-track-index="71"></div>
      {{ELEMENTS}}
      {{AUDIO}}
    </div>
    <script>
      const D = {{DATA}};
      const tl = gsap.timeline({ paused: true });
      const q = (s) => document.querySelector(s);
      const qa = (s, root) => Array.from((root || document).querySelectorAll(s));

      // ---- progress bar
      tl.fromTo("#progress", { scaleX: 0 }, { scaleX: 1, duration: D.dur, ease: "none" }, 0);

      // ---- camera: hard-cut zooms, punches, slow drift between keys
      const cam = q("#cam");
      D.cam.forEach(([t, s, mode], i) => {
        const next = i + 1 < D.cam.length ? D.cam[i + 1][0] : D.dur;
        let settle = t;
        if (mode === "set") tl.set(cam, { scale: s, x: 0, y: 0 }, t);
        else if (mode === "intro") { tl.to(cam, { scale: s, duration: 0.9, ease: "expo.out" }, t); settle = t + 0.9; }
        else if (mode === "punch") { tl.to(cam, { scale: s, duration: 0.18, ease: "power3.out" }, t); settle = t + 0.18; }
        else { tl.to(cam, { scale: s, duration: 0.35, ease: "power2.inOut" }, t); settle = t + 0.35; }
        const drift = next - settle - 0.01;
        if (drift > 0.3) tl.to(cam, { scale: s + Math.min(0.03, drift * 0.006), duration: drift, ease: "none" }, settle);
      });
      // deterministic hand-held shake on impacts
      const SH = [[14, -9], [-12, 7], [9, 10], [-7, -6], [5, 4], [-3, -2], [0, 0]];
      D.shakes.forEach((t) => SH.forEach(([x, y], k) =>
        tl.to(cam, { x, y, rotation: x * 0.04, duration: 0.035, ease: "none" }, t + 0.02 + k * 0.035)));

      // ---- chapter sign: 3D flip in / out
      D.chapters.forEach(([id, s, e]) => {
        const chip = qa(".chip", q("#" + id))[0];
        tl.fromTo(chip, { rotationX: -95, opacity: 0, y: -20 },
                        { rotationX: 0, opacity: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }, s);
        tl.to(chip, { rotationY: 6, duration: Math.max(0.5, e - s - 0.8), ease: "sine.inOut" }, s + 0.5);
        tl.to(chip, { rotationX: 95, opacity: 0, duration: 0.3, ease: "power2.in" }, e - 0.3);
      });

      // ---- 3D keywords
      D.keywords.forEach(([id, s, e, style]) => {
        const el = q("#" + id), box = qa(".kw-3d", el)[0], sh = qa(".kw-shadow", el)[0];
        const d = e - s;
        if (style === "pop") {
          tl.fromTo(box, { rotationY: -80, rotationX: 25, scale: 0.35, opacity: 0, z: -500 },
                         { rotationY: -16, rotationX: 10, scale: 1, opacity: 1, z: 0, duration: 0.5, ease: "back.out(1.7)" }, s);
        } else if (style === "impact") {
          tl.fromTo(box, { scale: 2.6, rotationX: 35, rotationY: 0, opacity: 0, z: 300 },
                         { scale: 1, rotationX: 12, rotationY: -14, opacity: 1, z: 0, duration: 0.28, ease: "expo.out" }, s);
        } else {
          tl.fromTo(box, { scale: 0.2, rotationZ: -25, rotationY: 40, opacity: 0 },
                         { scale: 1, rotationZ: -6, rotationY: -12, rotationX: 10, opacity: 1, duration: 0.3, ease: "back.out(3)" }, s);
          tl.to(box, { rotationZ: 6, duration: 0.07, yoyo: true, repeat: 5, ease: "none" }, s + 0.3);
        }
        tl.fromTo(sh, { opacity: 0, scaleX: 0.4 }, { opacity: 1, scaleX: 1, duration: 0.4 }, s);
        tl.to(box, { rotationY: 16, rotationX: 4, duration: Math.max(0.4, d - 0.85), ease: "sine.inOut" }, s + 0.5);
        tl.to(box, { rotationX: -90, scale: 0.7, opacity: 0, duration: 0.3, ease: "power2.in" }, e - 0.3);
        tl.to(sh, { opacity: 0, duration: 0.3 }, e - 0.3);
      });

      // ---- checklist: items flip in like 3D cards
      if (D.checklist) (() => {
        const [id, s, e, ats] = D.checklist;
        const items = qa(".ck-item", q("#" + id)), box = qa(".ck-3d", q("#" + id))[0];
        tl.set(box, { rotationY: -18, rotationX: 8 }, s);
        items.forEach((it, k) => tl.fromTo(it, { rotationY: 95, opacity: 0, x: -60 },
          { rotationY: 0, opacity: 1, x: 0, duration: 0.45, ease: "back.out(1.5)" }, ats[k]));
        tl.to(box, { rotationY: 10, duration: e - s - 0.6, ease: "sine.inOut" }, s + 0.3);
        tl.to(items, { rotationX: -90, opacity: 0, duration: 0.3, stagger: 0.05, ease: "power2.in" }, e - 0.35);
      })();

      // ---- full-screen 3D cards
      D.cards.forEach(([id, s, e, kind]) => {
        const el = q("#" + id), flip = qa(".card-flip", el)[0], bg = qa(".card-bg", el)[0];
        const floor = qa(".grid-floor", el)[0], dots = qa(".dots i", el);
        tl.fromTo(bg, { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: 0.14, ease: "power2.out" }, s);
        tl.fromTo(floor, { backgroundPosition: "0px 0px" }, { backgroundPosition: "0px 480px", duration: e - s, ease: "none" }, s);
        dots.forEach((dt, k) => tl.fromTo(dt, { y: 40, opacity: 0 },
          { y: -160 - (k % 5) * 40, opacity: 0.9, duration: e - s, ease: "none" }, s));
        if (kind === "cube") {
          const cube = qa(".cube", el)[0];
          tl.fromTo(cube, { rotationX: 0, rotationY: -35, scale: 0.6, z: -300 },
                          { rotationY: -12, scale: 1, z: 0, duration: 0.25, ease: "expo.out" }, s);
          tl.to(cube, { rotationX: 90, rotationY: 12, duration: 0.42, ease: "power3.inOut" }, s + 0.32);
        } else {
          const box = qa(".card-3d", el)[0], kick = qa(".card-kicker", el)[0], sub = qa(".card-sub", el)[0];
          tl.fromTo(box, { rotationY: -70, rotationX: 30, scale: 0.4, z: -600, opacity: 0 },
                         { rotationY: -14, rotationX: 10, scale: 1, z: 0, opacity: 1, duration: 0.4, ease: "back.out(1.5)" }, s + 0.05);
          tl.to(box, { rotationY: 14, rotationX: 4, duration: Math.max(0.3, e - s - 0.75), ease: "sine.inOut" }, s + 0.45);
          if (kick) tl.fromTo(kick, { y: -40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }, s + 0.1);
          if (sub) tl.fromTo(sub, { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, ease: "power3.out" }, s + 0.3);
        }
        // exit: the whole card flips up and away in 3D
        tl.to(flip, { rotationX: 88, y: -200, opacity: 0, duration: 0.26, ease: "power2.in" }, e - 0.26);
      });

      // ---- white flash stingers
      D.flashes.forEach(([id, s, e]) => {
        const f = qa(".flash", q("#" + id))[0], d = e - s;
        tl.fromTo(f, { opacity: 0 }, { opacity: 1, duration: Math.min(0.08, d * 0.25), ease: "power1.in" }, s);
        tl.to(f, { opacity: 0, duration: Math.min(0.16, d * 0.4), ease: "power2.out" }, e - Math.min(0.16, d * 0.4));
      });

      // ---- ending fade
      tl.to("#cam", { opacity: 0, duration: 0.6, ease: "power1.in" }, D.dur - 0.6);

      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    build()
