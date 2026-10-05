# Test results (iteration 1, 2026-10-05)

## Fresh-agent runs (with skill)
Three agents with no prior context each got the skill and one request (see `evals.json`), and were graded by
`grade.py`.

| Test | Checks | Time | Tokens |
|---|---|---|---|
| Shorter piece, retitled "Short Walk" (tessellation 15) | 7/7 | 14.0 min | 73k |
| 3-rotation hex tiling plus a browser instrument | 6/6 | 19.0 min | 72k |
| Make the chords drift upward (2-class offset tiling) | 5/5 | 19.2 min | 94k |

Most of the time is spent rendering: three jobs shared 4 cores, with 2 shards each.

Findings that changed the skill:
- The upward-drift run had to edit code in three places. It is now built in as `PO_DIRECTION=up`, with a closer
  opening voicing so no voice sags in the first round, and direction-aware wording on the end card and the organ.
- Python wrote `__pycache__` into the skill folder. `run.sh` now sets `PYTHONDONTWRITEBYTECODE=1`, so an installed
  (possibly read-only) skill folder stays untouched.
- Regression: the default settings still reproduce the original Painter's Order soundtrack byte for byte.

There is no without-skill baseline, by choice: without the skill, the task means rebuilding the whole pipeline from
scratch.

## Triggering (`trigger_eval.json`: 10 should-trigger, 10 near-misses)
Each query was given to `claude -p` once, and the check was whether the first action was to load this skill.
- Original description: 19/20. The one miss was the "vectorscope / XY oscilloscope video" request.
- After adding XY-mode/vectorscope wording: that query triggers 3/3, and its near-miss (an mp3 oscilloscope
  visualizer) correctly stays off 3/3.
- The skill-creator's automatic optimizer (`run_loop`) scored every positive at 0% in this container, even
  explicit "make another painters order". That is a detection problem in the harness, not in the description, so
  its rewritten description was not adopted.
