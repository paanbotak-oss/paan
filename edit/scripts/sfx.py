"""Synthesises the sound effects used in the edit (no external samples).
Usage: python3 sfx.py OUT_DIR"""
import sys, numpy as np, wave
SR = 48000
rng = np.random.default_rng(42)

def save(name, x, out):
    x = np.asarray(x, np.float32)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(f"{out}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def t(d): return np.arange(int(SR * d)) / SR

def bandsweep(noise, f0, f1, q=2.0):
    """Time-varying 2-pole resonant band-pass over noise (state-variable filter)."""
    n = len(noise); f = np.geomspace(f0, f1, n)
    low = band = 0.0; y = np.zeros(n)
    for i in range(n):
        F = 2 * np.sin(np.pi * f[i] / SR)
        high = noise[i] - low - band / q
        band += F * high; low += F * band; y[i] = band
    return y

def env(n, a, r, shape=2.0):
    e = np.ones(n); A = max(1, int(a * n)); R = max(1, int(r * n))
    e[:A] = np.linspace(0, 1, A) ** shape; e[-R:] = np.linspace(1, 0, R) ** shape
    return e

def whoosh(d=0.55, f0=300, f1=4000):
    x = bandsweep(rng.standard_normal(int(SR * d)), f0, f1, 1.6) * env(int(SR * d), 0.55, 0.45, 1.6)
    pan = np.linspace(-0.6, 0.6, len(x))
    return np.stack([x * (1 - pan) / 2 * 2, x * (1 + pan) / 2 * 2], 1)

def pop():
    tt = t(0.14); f = 1100 * np.exp(-tt * 28) + 280
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)

def impact():
    tt = t(1.2); f = 95 * np.exp(-tt * 6) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.5)
    click = rng.standard_normal(len(tt)) * np.exp(-tt * 60) * 0.5
    tail = bandsweep(rng.standard_normal(len(tt)), 2500, 400, 0.8) * np.exp(-tt * 5) * 0.25
    return np.tanh((boom + click + tail) * 1.6)

def riser(d=1.0):
    tt = t(d); f = np.geomspace(200, 2400, len(tt))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    nz = bandsweep(rng.standard_normal(len(tt)), 400, 7000, 1.2)
    return (tone + nz) * np.linspace(0, 1, len(tt)) ** 2.2 * env(len(tt), 0.02, 0.04)

def tick():
    tt = t(0.06)
    return (np.sin(2 * np.pi * 2200 * tt) * 0.6 + rng.standard_normal(len(tt)) * 0.4) * np.exp(-tt * 120)

def ding():
    tt = t(1.4)
    return sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, a, k in
               [(1318.5, 1, 3), (1975.5, 0.5, 4.5), (2637, 0.25, 6), (659.3, 0.35, 2.5)])

def crunch():
    out = np.zeros(int(SR * 0.45))
    for st in (0.0, 0.2):
        tt = t(0.12); b = bandsweep(rng.standard_normal(len(tt)), 900, 500, 0.9) * np.exp(-tt * 35)
        i = int(st * SR); out[i:i + len(b)] += b
    return out

def stinger():
    w = whoosh(0.4, 600, 9000)
    tt = t(0.4); hit = rng.standard_normal(len(tt)) * np.exp(-((tt - 0.2) * 25) ** 2) * 0.8
    return w + np.stack([hit, hit], 1)

if __name__ == "__main__":
    out = sys.argv[1]
    save("whoosh", whoosh(), out); save("whoosh_long", whoosh(0.9, 200, 3000), out)
    save("pop", pop(), out); save("impact", impact(), out); save("riser", riser(), out)
    save("tick", tick(), out); save("ding", ding(), out); save("crunch", crunch(), out)
    save("stinger", stinger(), out)
    print("ok")
