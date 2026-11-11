#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${OPENAI_COMPATIBLE_BASE_URL:?set it (source .env)}"
: "${OPENAI_COMPATIBLE_API_KEY:?set it (source .env)}"
MODEL="${1:-llama3.1:8b}"
LOG="runs/_smoke"
echo "Smoke test: $MODEL on banking, 1 user x 1 injection task, important_instructions"
python -m agentdojo.scripts.benchmark \
  --model openai-compatible --model-id "$MODEL" \
  --suite banking --attack important_instructions \
  --user-task user_task_0 --injection-task injection_task_0 \
  --logdir "$LOG" --max-workers 1 || {
    echo ">> benchmark errored. Check tool-calling / wiring (see README fallback)."; }
echo "---- result tree ----"; find "$LOG" -type f | head -40
echo "---- one result JSON (for schema) ----"
f="$(find "$LOG" -name '*.json' | head -1)"; [ -n "$f" ] && { echo "$f"; cat "$f"; }
