"""Offline proof for --workers: mocked API, random sleeps, no real calls."""
import json, os, random, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.logging_io import RunLogger, completed_tuples, run_path
from src.runner_core import Progress, run_tasks

random.seed(7)
NAME = "_wtest"
TASKS = [(f"t{i//3}", ["none", "standard", "reversed"][i % 3], 0) for i in range(30)]

def mock_call(task, progress=None, fail_after=None, counter=None):
    tid, variant, trial = task
    key = f"{tid}/{variant}"
    if progress: progress.set(key, 0)
    n = 0
    for _ in range(random.randint(2, 6)):          # simulate streaming
        time.sleep(random.uniform(0.01, 0.05))
        n += random.randint(1, 9)
        if progress: progress.set(key, n)
    if progress: progress.drop(key)
    if counter is not None:
        with counter["lock"]:
            counter["n"] += 1
            if fail_after and counter["n"] > fail_after:
                raise KeyboardInterrupt("simulated kill")
    return {"transcript_id": tid, "prompt_variant": variant, "trial_id": trial,
            "raw": {"text": "<label>HACKING</label> ok"}, "verdict": "HACKING",
            "usage": {"input_tokens": 100, "output_tokens": n * 10},
            "big": "x" * 500}   # make lines long enough that interleaving would show

def fresh():
    p = run_path(NAME)
    if p.exists(): p.unlink()
    return p

def check_file(p, expect_rows):
    raw = p.read_text(encoding="utf-8")
    lines = raw.splitlines()
    assert raw.endswith("\n"), "file must end with a newline (no torn final line)"
    parsed = []
    for i, ln in enumerate(lines):
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError as e:
            raise AssertionError(f"line {i+1} is not valid JSON (interleaved write?): {e}\n{ln[:200]!r}")
        assert ln.count('"transcript_id"') == 1, f"line {i+1} contains >1 record (interleaved)"
    assert len(lines) == expect_rows, f"expected {expect_rows} lines, got {len(lines)}"
    return parsed

print("=== A. 30 rows at --workers 4 ===")
p = fresh()
lg = RunLogger(NAME)
prog = Progress()
res, aborted, undis = run_tasks(
    TASKS, lambda t: mock_call(t, progress=prog), logger=lg,
    cost_of=lambda o: 0.001, describe=lambda t, o, n, s: "",
    workers=4, heartbeat=0.05, progress=prog, total=len(TASKS))
rows = check_file(p, 30)
tups = [(r["transcript_id"], r["prompt_variant"], r["trial_id"]) for r in rows]
print(f"  lines written        : {len(rows)}")
print(f"  all valid JSON       : True")
print(f"  no interleaved lines : True")
print(f"  distinct tuples      : {len(set(tups))}/30  -> {len(set(tups))==30}")
print(f"  duplicates           : {[t for t,c in __import__('collections').Counter(tups).items() if c>1] or 'none'}")
print(f"  matches task set     : {set(tups)==set(TASKS)}")
print(f"  aborted={aborted} undispatched={undis} spent=${lg.spent:.3f}")
assert len(set(tups)) == 30 and set(tups) == set(TASKS) and not aborted

print("\n=== B. resume after a simulated kill (workers 4) ===")
p = fresh()
lg = RunLogger(NAME)
counter = {"n": 0, "lock": threading.Lock()}
try:
    run_tasks(TASKS, lambda t: mock_call(t, counter=counter, fail_after=12),
              logger=lg, cost_of=lambda o: 0.001, describe=lambda *a: "",
              workers=4, total=len(TASKS))
except KeyboardInterrupt:
    pass
partial = check_file(p, len(p.read_text().splitlines()))
print(f"  partial rows on disk : {len(partial)}")
done = completed_tuples(NAME)
print(f"  completed_tuples     : {len(done)}")
remaining = [t for t in TASKS if t not in done]
print(f"  remaining to run     : {len(remaining)}")
lg2 = RunLogger(NAME, resume=True)
run_tasks(remaining, lambda t: mock_call(t), logger=lg2,
          cost_of=lambda o: 0.001, describe=lambda *a: "", workers=4)
rows2 = check_file(p, len(partial) + len(remaining))
t2 = [(r["transcript_id"], r["prompt_variant"], r["trial_id"]) for r in rows2
      if (r["raw"]["text"] or "").strip()]
import collections
dupes = {t: c for t, c in collections.Counter(t2).items() if c > 1}
print(f"  after resume: rows={len(rows2)} distinct-with-text={len(set(t2))}/30 dupes={dupes or 'none'}")
print(f"  set complete         : {set(t2)==set(TASKS)}")
assert set(t2) == set(TASKS) and not dupes

print("\n=== C. --max-usd stops dispatch, in-flight finish and log ===")
p = fresh()
lg = RunLogger(NAME)
res, aborted, undis = run_tasks(
    TASKS, mock_call, logger=lg, cost_of=lambda o: 0.10,
    describe=lambda *a: "", workers=4, max_usd=0.55)
rows3 = check_file(p, len(p.read_text().splitlines()))
print(f"  aborted={aborted} rows_logged={len(rows3)} undispatched={undis} spent=${lg.spent:.2f}")
print(f"  rows+undispatched == 30: {len(rows3)+undis==30}")
print(f"  every logged row is one call, none lost: {len(rows3)==lg._n}")
assert aborted and len(rows3) + undis == 30

print("\n=== D. workers=1 is the current behaviour (order preserved) ===")
p = fresh()
lg = RunLogger(NAME)
run_tasks(TASKS, lambda t: mock_call(t), logger=lg, cost_of=lambda o: 0.0,
          describe=lambda *a: "", workers=1)
rows4 = check_file(p, 30)
t4 = [(r["transcript_id"], r["prompt_variant"], r["trial_id"]) for r in rows4]
print(f"  file order == dispatch order: {t4==TASKS}")
assert t4 == TASKS
run_path(NAME).unlink()
print("\nALL WORKER ASSERTIONS PASS")
