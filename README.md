# Indirect prompt injection & defense transfer on small open-weight agents

A small, pre-registered red-team study: does indirect prompt injection succeed against
7-8B open-weight models driving a tool-using agent, and do AgentDojo's defenses reduce it
in the same rank order they do for frontier models? Built on
[AgentDojo](https://github.com/ethz-spylab/agentdojo); success is a **deterministic
sandbox oracle**, not an LLM judge.

Design and success criteria are frozen up front in **[PREREGISTRATION.md](PREREGISTRATION.md)**.

## Why it's credible
- One falsifiable question, committed before running (no cherry-picking).
- Deterministic ground truth (sandbox state), so no judge-reliability caveat.
- Calibrated against a published AgentDojo number before any new number is trusted.
- Wilson CIs on every rate; McNemar's paired test for each defense delta.

## Requirements (runs on your machine, not in CI)
- macOS/Linux host with ~16 GB+ RAM (models run one at a time).
- [Ollama](https://ollama.com) for local inference.
- Python 3.10+.

## Setup
```bash
cd llm-redteam-harness
bash scripts/setup.sh          # venv, deps, pull the 3 models
cp .env.example .env           # already points at local Ollama
```

## Smoke test first (confirms the Ollama tool-calling wiring)
```bash
source .venv/bin/activate && set -a && . ./.env && set +a
bash scripts/smoke_test.sh     # 1 user task x 1 injection task on banking
```
It prints the run-log tree and one result JSON. If the agent never calls tools, your model's
native tool-calling over Ollama is weak: switch provider to `local` with `--tool-delimiter`
(see the note in `scripts/run_study.sh`) and re-smoke.

## Run the study
```bash
source .venv/bin/activate && set -a && . ./.env && set +a
bash scripts/run_study.sh      # benign + attack + 2 defenses, 3 models, banking
```
Resumable: AgentDojo skips tasks already logged. Add `workspace` (stretch) by editing
`SUITES` in the script. Full `banking` set across all cells is a few hours on a Mac.

## Analyze
After runs finish, `scripts/analyze.py` reads `runs/` and emits the ASR table with Wilson
CIs, the McNemar defense deltas, and the calibration row into `findings/`. (Written against
the real result schema once the smoke test produces one.)

## Optional calibration (pre-reg Section 9)
Reproduce the published gpt-4o number to validate the harness (needs `OPENAI_API_KEY`):
```bash
python -m agentdojo.scripts.benchmark --model gpt-4o-2024-05-13 \
  --suite banking --attack important_instructions --logdir runs/_calibration
```

## Scope
Sandbox + self-hosted models only; benign simulated actions, never harmful text; standard
academic benchmark; defender-oriented; no third-party production systems. See
PREREGISTRATION.md Section 12.
