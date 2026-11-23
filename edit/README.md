# Edit video: Lutut Bengkak (HyperFrames)

Output: `output/lutut-bengkak-edit.mp4` (1080x1920, ~1:41, asal 1:55).

## Apa yang dibuat
- **Buang jeda & bahagian tak perlu** (`scripts/cut.py`): frame kabur/flash, frame hitam,
  transition TikTok lama yang rosak, jalan ke katil, ultrasound tersangkut, jeda antara ayat.
- **Suara diasingkan** dari muzik TikTok lama (Demucs) supaya muzik baru tak bertembung.
- **Motion untuk siri perbualan**: zoom jump-cut berselang, punch-in pada perkataan penting,
  shake pada impact, drift perlahan, progress bar, papan bab 3D yang flip.
- **3D**: keyword teks 3D extruded (LUTUT BENGKAK?, GOUT, OSTEOARTHRITIS, KRUK-KRAK!, INJURI,
  KOYAK!...), kiub 3D berputar PUNCA #1 → #2, kad penuh 3D dengan lantai grid, checklist 3D.
- **Sound effect** (whoosh, pop, impact, riser, crunch, ding — `scripts/sfx.py`) dan
  **muzik latar** (MusicGen) dengan auto-ducking bila doktor bercakap (`scripts/music_bed.py`).

## Ubah & render semula
Masa semua grafik/SFX ada dalam `scripts/build.py` (saat output).
```bash
python3 scripts/build.py project          # jana project/index.html
cd project && npx hyperframes check
npx hyperframes render -o ../output/lutut-bengkak-edit.mp4 -q delivery
```
