import sys, numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.manual_seed(7)
p = AutoProcessor.from_pretrained("facebook/musicgen-small")
m = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
prompt = "warm upbeat modern lofi hip hop background music for a friendly health talk show, soft electric piano chords, plucky synth, gentle kick and snare, positive, 95 bpm, no vocals"
inp = p(text=[prompt], padding=True, return_tensors="pt")
with torch.no_grad():
    a = m.generate(**inp, do_sample=True, guidance_scale=3.0, max_new_tokens=1500)
sr = m.config.audio_encoder.sampling_rate
sf.write(sys.argv[1], a[0, 0].numpy(), sr)
print("ok", sr, a.shape)
