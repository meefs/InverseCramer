"""Concatenate the rendered segments and mux the soundtrack: <builddir>/film.mp4"""
import subprocess
import sys
from pathlib import Path

build = Path(sys.argv[1])
segs = sorted((build / "segments").glob("seg_*.mp4"))
(build / "segments.txt").write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(build / "segments.txt"),
                "-i", str(build / "score.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(build / "film.mp4")], check=True)
print(build / "film.mp4", round((build / "film.mp4").stat().st_size / 1e6, 1), "MB")
