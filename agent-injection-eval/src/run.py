#!/usr/bin/env python3
"""
run.py — the experiment runner.

Reads a config, runs every (task x defense x attack x seed) cell against a REAL
model (Ollama), logs a transcript per episode, and writes a results JSONL plus a
machine-readable summary. Analysis is done separately by analyze.py so runs are
immutable artifacts.

Usage (on the operator's Mac, with `ollama serve` running):
    python3 src/run.py --config config/experiment.json
    python3 src/run.py --model qwen2.5:7b --seeds 20 --budget 16
    python3 src/run.py --smoke            # 1 seed, tiny, to check wiring

Nothing here needs pip: it talks to Ollama over stdlib urllib.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from targets import OllamaTarget                      # noqa: E402
from environment import default_tasks                  # noqa: E402
from defenses import get_defense                        # noqa: E402
from attacks import static_attack, adaptive_attack      # noqa: E402
from metrics import Rate, asr_at_n, headline            # noqa: E402

DEFAULT_CONFIG = {
    "model": "llama3.1:8b",
    "host": "http://localhost:11434",
    "defenses": ["none", "prompt_level", "spotlighting"],
    "seeds": 20,
    "budget": 16,
    "out_dir": "results",
}


def load_config(path):
    cfg = dict(DEFAULT_CONFIG)
    if path and os.path.exists(path):
        cfg.update(json.load(open(path)))
    return cfg


def env_factory_for(task):
    import copy
    return lambda: copy.deepcopy(task)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--model")
    ap.add_argument("--seeds", type=int)
    ap.add_argument("--budget", type=int)
    ap.add_argument("--out-dir")
    ap.add_argument("--smoke", action="store_true", help="1 seed, quick wiring check")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.model: cfg["model"] = args.model
    if args.seeds: cfg["seeds"] = args.seeds
    if args.budget: cfg["budget"] = args.budget
    if args.out_dir: cfg["out_dir"] = args.out_dir
    if args.smoke: cfg["seeds"] = 1

    os.makedirs(cfg["out_dir"], exist_ok=True)
    target = OllamaTarget(model=cfg["model"], host=cfg["host"])
    tasks = default_tasks()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(cfg["out_dir"], f"episodes-{stamp}.jsonl")
    summary = {"config": cfg, "model": target.name, "cells": []}

    print(f"[*] model={target.name} seeds={cfg['seeds']} budget={cfg['budget']}")
    print(f"[*] logging episodes -> {log_path}")
    logf = open(log_path, "w")
    spath = os.path.join(cfg["out_dir"], f"summary-{stamp}.json")
    summary["complete"] = False

    try:
        for defense_name in cfg["defenses"]:
            defense = get_defense(defense_name)
            for attack in ("static", "adaptive"):
                summary["cells"].append(
                    run_cell(target, tasks, defense, defense_name, attack, cfg, logf))
        summary["complete"] = True
    finally:
        # Always write a summary, even on Ctrl-C or an unexpected crash, so a
        # partial run is still an inspectable artifact (flagged complete=false).
        logf.close()
        summary["headline"] = build_headline(summary["cells"], cfg["defenses"])
        json.dump(summary, open(spath, "w"), indent=2)
        print(f"[+] summary -> {spath} (complete={summary['complete']})")
    print("[+] run analyze.py on the summary for tables + the static-vs-adaptive delta")


def run_cell(target, tasks, defense, defense_name, attack, cfg, logf):
    """Run every (task x seed) episode for one defense/attack cell.

    An episode that raises (e.g. an Ollama timeout) is logged with an "error"
    field and EXCLUDED from n, rather than aborting the whole run; the count is
    reported as n_errors so exclusions are visible. Episodes whose model output
    hit the token cap are scored normally by the oracle and counted in
    n_truncated (degenerate output, see PREREGISTRATION)."""
    succ = total = n_errors = n_truncated = 0
    first_idx = []
    for task in tasks:
        ef = env_factory_for(task)
        for seed in range(cfg["seeds"]):
            row = {"task": task.task_id, "defense": defense_name, "attack": attack,
                   "seed": seed}
            trunc_before = getattr(target, "truncated_calls", 0)
            try:
                if attack == "static":
                    ok, used, tr = static_attack(target, ef, defense, task.task_id, seed=seed)
                    fidx = used if ok else None
                else:
                    ok, used, fidx, tr = adaptive_attack(
                        target, ef, defense, task.task_id, budget=cfg["budget"], seed=seed)
            except Exception as e:   # noqa: BLE001 — record and keep going
                n_errors += 1
                row.update({"episode_id": f"{task.task_id}|{attack}|s{seed}",
                            "error": f"{type(e).__name__}: {e}"})
                print(f"    !! {defense_name}/{attack}/{task.task_id}/s{seed}: {row['error']}")
            else:
                total += 1
                succ += int(ok)
                first_idx.append(fidx)
                truncated = getattr(target, "truncated_calls", 0) - trunc_before
                n_truncated += int(truncated > 0)
                row.update({
                    "episode_id": getattr(tr, "episode_id", ""),
                    "success": ok, "attempts_used": used, "first_success": fidx,
                    "truncated_calls": truncated,
                    "actions": getattr(tr, "actions", []),
                    "final": getattr(tr, "final", ""),
                })
            logf.write(json.dumps(row) + "\n")
            logf.flush()
    rate = Rate(f"{defense_name}/{attack}", succ, total)
    cell = {"defense": defense_name, "attack": attack,
            "asr": rate.pct, "ci": rate.ci, "n": total,
            "n_errors": n_errors, "n_truncated": n_truncated}
    if attack == "adaptive":
        cell["asr_at_n"] = asr_at_n(first_idx, budgets=tuple(
            k for k in (1, 2, 4, 8, 16, 32) if k <= cfg["budget"]))
    print(f"    {defense_name:13s} {attack:9s} ASR={rate.pct:5.1f}% CI={rate.ci} n={total}"
          f" errors={n_errors} truncated={n_truncated}")
    return cell


def build_headline(cells, defenses):
    """Pair static vs adaptive per defense for the H1 headline; skips defenses
    whose cells are missing (partial run)."""
    heads = []
    for d in defenses:
        s = next((c for c in cells if c["defense"] == d and c["attack"] == "static"), None)
        a = next((c for c in cells if c["defense"] == d and c["attack"] == "adaptive"), None)
        if s is None or a is None:
            continue
        heads.append(headline(Rate(d, round(s["asr"] * s["n"] / 100), s["n"]),
                              Rate(d, round(a["asr"] * a["n"] / 100), a["n"])))
    return heads


if __name__ == "__main__":
    main()
