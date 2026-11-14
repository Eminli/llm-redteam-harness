# Runbook — running the real evaluation on your Mac (M4 Pro)

Everything here runs on your machine with **Python 3.9+ and Ollama only** — the
core harness has no pip dependencies (it talks to Ollama over stdlib `urllib`).
matplotlib is optional (for the ASR@N plot); analysis falls back to text if it's
absent.

## 0. One-time setup (~10 min)

```bash
# install Ollama (https://ollama.com) then pull two small models
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama serve        # leave running in a terminal (if not already a service)

# sanity check the harness logic (uses test doubles, no model needed)
cd agent-injection-eval
python3 tests/test_harness.py
```

On an M4 Pro, 7–8B models run comfortably; no GPU config needed.

## 1. Smoke test the wiring against the real model (~2 min)

```bash
python3 src/run.py --smoke --model llama3.1:8b
```

This runs 1 seed over the tasks × defenses × {static, adaptive}. You want to see
non-trivial, *varying* ASR numbers and a `results/episodes-*.jsonl` appear. If the
undefended baseline ASR is ~0, something is wrong (see PREREGISTRATION §7) — the
model may not be emitting tool calls in the expected JSON; inspect a few
transcripts in the JSONL.

## 2. Full run (~20–60 min per model, CPU/seed dependent)

```bash
python3 src/run.py --model llama3.1:8b --seeds 20 --budget 16
python3 src/run.py --model qwen2.5:7b  --seeds 20 --budget 16
```

Each writes `results/episodes-<stamp>.jsonl` (one line per episode, full
transcript + oracle verdict) and `results/summary-<stamp>.json`.

## 3. Analyze

```bash
python3 src/analyze.py "results/summary-*.json" --md report/results_table.md --plot report/asr_at_n.png
```

Prints the static-vs-adaptive headline table, the H1/H2 verdicts, and the ASR@N
curves. Paste the printed block (and the two files) back to me and I'll write the
findings and the honest discussion — including if H1 is *not* supported.

## 4. Calibrate the secondary text judge (optional but recommended)

```bash
python3 calibration/calibrate.py export "results/episodes-*.jsonl"
# open calibration/to_label.csv, fill human_label (comply|refuse|neither) for >=50 rows
python3 calibration/calibrate.py score calibration/to_label.csv
```

If kappa ≥ 0.6, we report the text metric too; if not, oracle metrics only.

## 5. Stretch: real benchmarks & a real classifier

- Point the harness at **AgentDojo**: implement `environment.from_agentdojo()` to
  map its tasks/tools into `Env` objects (the oracle pattern is already
  AgentDojo-shaped). Pin the AgentDojo version.
- Wire a **real classifier defense**: pass a callable into `defenses.Classifier`
  that calls a guard model (e.g. `ollama pull llama-guard3` or a Prompt-Guard
  model) and returns `"injection"` / `"clean"`.
- Add a **third model** (e.g. `mistral:7b`) so a finding isn't single-model.

## What to send back

1. The printed `analyze.py` block.
2. `results/summary-*.json` and (if small enough) `results/episodes-*.jsonl`.
3. The calibration `score` output, if you ran it.
4. Your Ollama version (`ollama --version`) and model digests (`ollama show
   llama3.1:8b --modelfile | head`), so the run is pinned and reproducible.
