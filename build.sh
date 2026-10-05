#!/usr/bin/env bash
# Refresh site/ from the latest renders. Usage: site/build.sh (after running both run_all.sh scripts)
set -euo pipefail
python -m painters_order.web build/painters_order/score.json site/organ_data.js
python -m flock.html build/flock && cp build/flock/flock_viewer_page.html site/flock-viewer.html
ffmpeg -loglevel error -y -i build/flock/flock.mp4 -c:v libx264 -crf 23 -preset slow -c:a copy -movflags +faststart site/media/flock.mp4
ffmpeg -loglevel error -y -i build/painters_order/painters_order.mp4 -c:v libx264 -crf 23 -preset slow -c:a copy -movflags +faststart site/media/painters-order.mp4
ffmpeg -loglevel error -y -ss 11 -i build/flock/flock.mp4 -frames:v 1 -vf scale=1280:-1 -q:v 3 site/media/flock-poster.jpg
ffmpeg -loglevel error -y -ss 54 -i build/painters_order/painters_order.mp4 -frames:v 1 -vf scale=1280:-1 -q:v 3 site/media/painters-order-poster.jpg
ffmpeg -loglevel error -y -i build/flock/flock_still.png -vf scale=1280:-1 -q:v 3 site/media/flock-still.jpg
ffmpeg -loglevel error -y -ss 54 -i build/painters_order/painters_order.mp4 -frames:v 1 -vf scale=1085:-1 -q:v 3 site/preview.jpg
