#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[1/4] Python venv"
python3 -m venv .venv
source .venv/bin/activate
echo "[2/4] Install AgentDojo + analysis deps"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
python -c "import importlib.metadata as m; print('agentdojo', m.version('agentdojo'))"
echo "[3/4] Check Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  echo "  Ollama not found. Install from https://ollama.com then re-run." >&2; exit 1
fi
ollama --version
echo "[4/4] Pull models (sequential; ~13 GB total)"
for m in llama3.1:8b qwen2.5:7b mistral:7b; do echo "  pulling $m"; ollama pull "$m"; done
echo "Done. Next: cp .env.example .env && bash scripts/smoke_test.sh"
