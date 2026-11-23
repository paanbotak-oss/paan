"""Loops the generated music to the film length with crossfades, then ducks it
under the voice (sidechain) and fades the tail.  Usage:
python3 music_bed.py MUSIC_48K.wav VOICE.wav DURATION OUT.wav"""
import subprocess, sys, wave, numpy as np
src, voice, dur, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
w = wave.open(src); sr = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, ch) / 32768
x = x[: int(sr * 28.0)]                      # drop MusicGen's fading last bar
xf = int(sr * 2.0); fade = np.linspace(0, 1, xf)[:, None]
need = int(sr * (dur + 1)); y = x.copy()
while len(y) < need:
    y = np.concatenate([y[:-xf], y[-xf:] * (1 - fade) + x[:xf] * fade, x[xf:]])
y = y[:need]
tmp = out + ".loop.wav"
with wave.open(tmp, "wb") as o:
    o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
fc = ("[0:a]loudnorm=I=-20:TP=-2:LRA=11,aformat=channel_layouts=stereo[m];"
      "[1:a]aformat=channel_layouts=stereo,asplit=2[sc][vx];[vx]anullsink;"
      "[m][sc]sidechaincompress=threshold=0.02:ratio=2:attack=60:release=700:makeup=1[d];"
      f"[d]volume=1.85,afade=t=in:d=0.4,afade=t=out:st={dur-2.2}:d=2.2,atrim=0:{dur}[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", voice, "-filter_complex", fc, "-map", "[o]",
                "-ar", "48000", out], check=True)
print("ok")
