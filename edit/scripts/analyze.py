"""Step 1: analyse a source video so cuts and overlays can be planned.

Usage: python3 -I analyze.py SOURCE.mp4 WORK_DIR
Writes into WORK_DIR:
  vocals.wav / no_vocals.wav  Demucs split (old music removed from the voice)
  transcript.json / .txt      faster-whisper words (Malay), source time
  vad.txt                     speech regions + gaps from the ISOLATED voice
  sheets/s*.jpg               1 fps contact sheets with timestamps
  scenes.txt                  scene-change times (old transitions, flashes, cuts)
"""
import json, os, subprocess, sys, wave
import numpy as np

src, work = sys.argv[1], sys.argv[2]
os.makedirs(f"{work}/sheets", exist_ok=True)
run = lambda *a: subprocess.run(a, check=True)

# contact sheets + scene changes
run("ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
    "fps=1,scale=144:-1,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=red:box=1,tile=10x6",
    f"{work}/sheets/s%d.jpg")
sc = subprocess.run(["ffmpeg", "-i", src, "-vf", "select='gt(scene,0.25)',showinfo", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
open(f"{work}/scenes.txt", "w").write("\n".join(l.split("pts_time:")[1].split()[0] for l in sc.splitlines() if "pts_time:" in l))

# voice / music split
run("ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-ar", "44100", f"{work}/audio44.wav")
run(sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", f"{work}/sep", f"{work}/audio44.wav")
for stem in ("vocals", "no_vocals"):
    os.replace(f"{work}/sep/htdemucs/audio44/{stem}.wav", f"{work}/{stem}.wav")
run("ffmpeg", "-v", "error", "-y", "-i", f"{work}/vocals.wav", "-ac", "1", "-ar", "16000", f"{work}/voc16.wav")

wf = wave.open(f"{work}/voc16.wav")
a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768

from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions

ts = get_speech_timestamps(a, VadOptions(threshold=0.45, min_silence_duration_ms=120, speech_pad_ms=40, min_speech_duration_ms=80))
prev, lines = 0.0, []
for t in ts:
    s, e = t["start"] / 16000, t["end"] / 16000
    lines.append(f"gap {s - prev:5.2f} | speech {s:7.2f}-{e:7.2f}")
    prev = e
open(f"{work}/vad.txt", "w").write("\n".join(lines))

m = WhisperModel("small", device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, language="ms", word_timestamps=True)
out, txt = [], []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text,
                "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]})
    txt.append(f"{s.start:7.2f}-{s.end:7.2f} {s.text}")
json.dump(out, open(f"{work}/transcript.json", "w"), ensure_ascii=False, indent=1)
open(f"{work}/transcript.txt", "w").write("\n".join(txt))
print("done:", work)
