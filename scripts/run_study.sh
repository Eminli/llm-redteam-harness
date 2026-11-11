#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${OPENAI_COMPATIBLE_BASE_URL:?set it (source .env)}"
: "${OPENAI_COMPATIBLE_API_KEY:?set it (source .env)}"

MODELS=( "llama3.1:8b" "qwen2.5:7b" "mistral:7b" )
SUITES=( "banking" )                  # stretch: add "workspace"
ATTACK="important_instructions"
DEFENSES=( "tool_filter" "spotlighting_with_delimiting" )   # stretch: transformers_pi_detector repeat_user_prompt
LOGROOT="runs"

bench () { python -m agentdojo.scripts.benchmark --model openai-compatible --model-id "$1" "${@:2}" --max-workers 1; }

for model in "${MODELS[@]}"; do
  tag="${model//[:\/]/_}"
  for suite in "${SUITES[@]}"; do
    echo "== $model / $suite / benign (utility baseline) =="
    bench "$model" --suite "$suite" --logdir "$LOGROOT/$tag/$suite/benign"
    echo "== $model / $suite / attack, no defense =="
    bench "$model" --suite "$suite" --attack "$ATTACK" --logdir "$LOGROOT/$tag/$suite/attack_nodef"
    for d in "${DEFENSES[@]}"; do
      echo "== $model / $suite / attack + $d =="
      bench "$model" --suite "$suite" --attack "$ATTACK" --defense "$d" --logdir "$LOGROOT/$tag/$suite/attack_$d"
    done
  done
done
echo "All cells done. Run: python scripts/analyze.py"

# FALLBACK if native tool-calling is weak for a model:
#   serve/registry via provider 'local' instead:
#   python -m agentdojo.scripts.benchmark --model local --model-id "$model" --tool-delimiter tool ...
#   (set LOCAL_LLM_PORT if not 8000)
