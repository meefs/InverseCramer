"""Programmatic grading of the painters-order skill runs. Writes grading.json per run."""
import json, re, subprocess, sys
from pathlib import Path

IT = Path(sys.argv[1])
SKILL_SHA = Path(sys.argv[2])
SKILL_DIR = Path(sys.argv[3])


def skill_unchanged():
    now = subprocess.run(f"cd {SKILL_DIR.parent} && find painters-order -type f -not -path '*/__pycache__/*' -exec sha256sum {{}} \; | sort -k2",
                         shell=True, capture_output=True, text=True).stdout
    return now == SKILL_SHA.read_text(), f"{len(now.splitlines())} files hashed, identical to before the runs" if now == SKILL_SHA.read_text() else "skill files changed"


def probe(f):
    if not f.exists():
        return None, None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(f)],
                         capture_output=True, text=True).stdout
    j = json.loads(out)
    return float(j["format"]["duration"]), [s["codec_type"] for s in j["streams"]]


def cents_in(text):
    return [float(m.replace("−", "-").replace("+", "")) for m in re.findall(r"([+−-]?\d+(?:\.\d+)?)\s*cents", text)]


def grade(run, checks):
    exp = []
    for text, (ok, ev) in checks:
        exp.append(dict(text=text, passed=bool(ok), evidence=ev))
    n = sum(e["passed"] for e in exp)
    out = dict(expectations=exp, summary=dict(passed=n, failed=len(exp) - n, total=len(exp), pass_rate=round(n / len(exp), 3)))
    (run / "grading.json").write_text(json.dumps(out, indent=2))
    print(run.parent.name, f"{n}/{len(exp)}")
    for e in exp:
        print("   ", "PASS" if e["passed"] else "FAIL", e["text"], "|", e["evidence"][:110])


unch = skill_unchanged()

# 1 short walk
o = IT / "short-walk-retitle/with_skill/outputs"
meta = json.loads((IT / "short-walk-retitle/eval_metadata.json").read_text())["assertions"]
dur, streams = probe(o / "film.mp4")
sc = json.loads((o / "score.json").read_text())
resp = (o / "response.md").read_text()
organ = (o / "web/organ_data.js").read_text() if (o / "web/organ_data.js").exists() else ""
cs = cents_in(resp)
grade(o.parent, [
    (meta[0], (dur and 25 <= dur <= 45, f"film.mp4 duration {dur:.1f} s" if dur else "no film.mp4")),
    (meta[1], ("Short Walk" in organ, "organ_data.js title: " + (re.search(r'"title":"([^"]*)"', organ).group(1) if '"title"' in organ else "none"))),
    (meta[2], (sc["cycles"] < 6, f"cycles = {sc['cycles']}")),
    (meta[3], (any(abs(c - sc["drift_cents"]) < 1 for c in cs), f"reply cents {cs}; score.json {sc['drift_cents']:.2f}")),
    (meta[4], (re.search(r"odd harmonic|clarinet", resp, re.I) is not None, "found" if re.search(r"odd harmonic|clarinet", resp, re.I) else "not mentioned")),
    (meta[5], ((o / "web/index.html").exists() and bool(organ), "web/index.html + organ_data.js present")),
    (meta[6], unch),
])

# 2 p3 hex
o = IT / "p3-hex-browser-organ/with_skill/outputs"
meta = json.loads((IT / "p3-hex-browser-organ/eval_metadata.json").read_text())["assertions"]
an = (o / "analysis.txt").read_text()
resp = (o / "response.md").read_text()
dur, streams = probe(o / "film.mp4")
three = "class 2:" in an and "class 3:" not in an and "angle 60.0" in an
grade(o.parent, [
    (meta[0], (three, re.search(r"lattice:.*", an).group(0))),
    (meta[1], (re.search(r"shar|reuse", resp, re.I) is not None, re.search(r"[^.]*(?:shar|reuse)[^.]*\.", resp, re.I).group(0).strip()[:160] if re.search(r"shar|reuse", resp, re.I) else "not explained")),
    (meta[2], (re.search(r"only odd", resp, re.I) is None, "reply says: " + (re.search(r"[^.]*odd[^.]*\.", resp, re.I).group(0).strip()[:140] if re.search(r"odd", resp, re.I) else "no harmonic claim"))),
    (meta[3], ((o / "web/index.html").exists() and re.search(r"click|Space", resp) is not None, "web/ present; reply explains clicking and Space")),
    (meta[4], (streams and "audio" in streams, f"streams {streams}, {dur:.1f} s" if dur else "no film")),
    (meta[5], unch),
])

# 3 upward drift
o = IT / "upward-drift-variation/with_skill/outputs"
meta = json.loads((IT / "upward-drift-variation/eval_metadata.json").read_text())["assertions"]
sc = json.loads((o / "score.json").read_text())
an = (o / "analysis.txt").read_text()
resp = (o / "response.md").read_text()
dur, streams = probe(o / "film.mp4")
off = re.search(r"class 1:.*offset \[([^\]]*)\]", an)
cs = cents_in(resp)
grade(o.parent, [
    (meta[0], (sc["drift_cents"] > 0, f"drift_cents = {sc['drift_cents']:+.2f}")),
    (meta[1], ((o / "code").is_dir() and unch[0], f"outputs/code/ present: {(o / 'code').is_dir()}; {unch[1]}")),
    (meta[2], (streams and "audio" in streams, f"streams {streams}, {dur:.1f} s" if dur else "no film")),
    (meta[3], (any(abs(c - sc["drift_cents"]) < 1 for c in cs), f"reply cents {cs}; score.json {sc['drift_cents']:+.2f}")),
    (meta[4], (off is not None and "class 2:" not in an and any(abs(float(v)) > 1 for v in off.group(1).split()), f"class 1 offset [{off.group(1) if off else '?'}]")),
])
