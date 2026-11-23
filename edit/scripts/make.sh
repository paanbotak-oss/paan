#!/usr/bin/env bash
# Steps 2-4: cut, audio, build, check, render.  Run from edit/:
#   scripts/make.sh videos/<name> SOURCE.mp4 WORK_DIR
# WORK_DIR is the folder analyze.py wrote (needs vocals.wav).
set -euo pipefail
VID=$1; SRC=$2; WORK=$3
PLAN=$VID/plan.json; A=project/assets
export HF_HUB_DISABLE_XET=1
python3 -I scripts/cut.py "$PLAN" "$SRC" "$WORK/vocals.wav" $A
DUR=$(python3 -I -c "import json;print(json.load(open('$A/edl.json'))['duration'])")
[ -f "$WORK/music48.wav" ] || { python3 -I scripts/musicgen.py "$WORK/music_raw.wav" && \
  ffmpeg -v error -y -i "$WORK/music_raw.wav" -ar 48000 -ac 2 "$WORK/music48.wav"; }
python3 -I scripts/music_bed.py "$WORK/music48.wav" $A/voice.wav "$DUR" $A/music_bed.wav && rm -f $A/music_bed.wav.loop.wav
[ -f $A/sfx/whoosh.wav ] || python3 -I scripts/sfx.py $A/sfx
python3 -I scripts/build.py "$PLAN" project
(cd project && npx hyperframes check)
NAME=$(basename "$VID"); mkdir -p output
(cd project && npx hyperframes render -o "$WORK/master.mp4" -q delivery -w 4)
ffmpeg -v error -y -i "$WORK/master.mp4" -c:v libx264 -preset slow -crf 20 -maxrate 14M -bufsize 28M \
  -pix_fmt yuv420p -movflags +faststart -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -ar 48000 \
  "output/$NAME.mp4"
echo "OK -> output/$NAME.mp4"
