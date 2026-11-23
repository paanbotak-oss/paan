"""Cut list for the knee video: removes dead pauses and broken transitions.

Writes project/assets/base.mp4 (1080x1920, silent), project/assets/voice.wav
(isolated vocals, same cuts) and project/assets/edl.json (segment map).
Usage: python3 cut.py SOURCE.mp4 VOCALS.wav PROJECT_ASSETS_DIR
"""
import json, subprocess, sys

# (source_start, source_end) kept, in order
KEEP = [
    (0.00, 3.22),     # hook
    (3.47, 17.21),    # cause #1 gout   (cut old flash transition)
    (17.50, 34.66),   # cause #2 osteoarthritis (cut black frame)
    (35.05, 40.56),   # "macam mana nak periksa"
    (42.58, 66.88),   # physical exam (cut 2s walking to bed)
    (67.20, 86.11),   # young patients / ligament
    (86.50, 87.95),
    (88.05, 89.55),   # ultrasound probe b-roll (silent voice)
    (91.78, 98.15),   # ultrasound screen
    (98.92, 100.20),
    (100.51, 102.05),
    (103.15, 103.47),
    (104.08, 105.12),
    (107.75, 112.25), # clinic outro card
]

def main(src, voc, out):
    vf, af, n = [], [], len(KEEP)
    for i, (s, e) in enumerate(KEEP):
        vf.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        af.append(f"[1:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e-s-0.012:.3f}:d=0.012[a{i}]")
    fc = ";".join(vf + af)
    fc += ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,scale=1080:1920:flags=lanczos,fps=30,format=yuv420p[vo]"
    fc += ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ao]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", voc, "-filter_complex", fc,
                    "-map", "[vo]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "15", "-an", f"{out}/base.mp4",
                    "-map", "[ao]", "-ar", "48000", "-ac", "2", f"{out}/voice.wav"], check=True)
    edl, t = [], 0.0
    for s, e in KEEP:
        edl.append({"src": [s, e], "out": [round(t, 3), round(t + e - s, 3)]})
        t += e - s
    json.dump({"duration": round(t, 3), "segments": edl}, open(f"{out}/edl.json", "w"), indent=1)
    print("duration", round(t, 3))

if __name__ == "__main__":
    main(*sys.argv[1:4])
