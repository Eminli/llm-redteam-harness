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
echo "[4/4] Pull models (sequential; ~13 GB total; resumes from cache on retry)"
pull_with_retry () {
  local m="$1" n=0
  until ollama pull "$m"; do
    n=$((n+1))
    if [ "$n" -ge 5 ]; then echo "  !! $m failed after 5 tries (last error above). Re-run setup.sh later." >&2; return 1; fi
    echo "  .. $m hiccup (often a 503); retry $n/5 in 30s"; sleep 30
  done
}
ok=1
for m in llama3.1:8b qwen2.5:7b mistral:7b; do echo "  pulling $m"; pull_with_retry "$m" || ok=0; done
[ "$ok" = 1 ] || { echo "Some models did not pull; fix network/registry and re-run. Others are cached." >&2; exit 1; }
echo "Done. Next: cp .env.example .env && bash scripts/smoke_test.sh"
