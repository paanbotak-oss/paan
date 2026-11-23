"""Cuts the source video + isolated vocals using plan["keep"] (source-time ranges).

Writes PROJECT/assets/base.mp4 (1080x1920, silent), voice.wav (same cuts) and
edl.json (source -> output map).
Usage: python3 cut.py PLAN.json SOURCE.mp4 VOCALS.wav PROJECT_ASSETS_DIR
"""
import json, subprocess, sys


def main(plan, src, voc, out):
    keep = json.load(open(plan))["keep"]
    vf, af, n = [], [], len(keep)
    for i, (s, e) in enumerate(keep):
        vf.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        af.append(f"[1:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e-s-0.012:.3f}:d=0.012[a{i}]")
    fc = ";".join(vf + af)
    # scale+pad keeps any aspect ratio inside a 1080x1920 vertical frame
    fc += (";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
           "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,format=yuv420p[vo]")
    fc += ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ao]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", voc, "-filter_complex", fc,
                    "-map", "[vo]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "15", "-an", f"{out}/base.mp4",
                    "-map", "[ao]", "-ar", "48000", "-ac", "2", f"{out}/voice.wav"], check=True)
    edl, t = [], 0.0
    for s, e in keep:
        edl.append({"src": [s, e], "out": [round(t, 3), round(t + e - s, 3)]})
        t += e - s
    json.dump({"duration": round(t, 3), "segments": edl}, open(f"{out}/edl.json", "w"), indent=1)
    print("duration", round(t, 3))


if __name__ == "__main__":
    main(*sys.argv[1:5])
