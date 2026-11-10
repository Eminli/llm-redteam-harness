# llm-redteam-harness

A small, reproducible harness for red-teaming large language models with
[Microsoft PyRIT](https://github.com/microsoft/PyRIT). It runs single-turn and
multi-turn attacks, converter chains, and indirect prompt injection against a
**local, self-hosted model**, and scores the results automatically so findings
are reproducible rather than judged by eye.

Built to exercise the techniques that matter for AI red teaming — prompt
injection, converter-based input obfuscation, multi-turn escalation, and
agent/tool trust boundaries — and to turn each finding into a defender takeaway.

## Threat model

Each run is framed with the ontology Microsoft's AI Red Team uses:

- **Actor** — who is attacking (external user, a poisoned document, a tool response)
- **TTPs** — the technique (injection, obfuscation, multi-turn escalation)
- **Weakness** — what it exploits (no data/instruction separation, pre-decode filtering)
- **Impact** — what it achieves (instruction override, refusal bypass)

## Scope and safety

- Everything targets a **local model you run yourself** (Ollama / LM Studio). No
  third-party product or hosted API is attacked.
- Objectives are **benign canaries** (e.g. "append a fixed token"), chosen to
  measure whether a control holds, not to elicit harmful content.
- Each finding ends in a mitigation. This is security engineering for defenders.

## Setup

Requires Python 3.10-3.13.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then edit to point at your local model
```

Start a local model, e.g. with Ollama:

```bash
ollama pull llama3.2
# OpenAI-compatible endpoint: http://localhost:11434/v1/chat/completions
```

## Run

```bash
python harness/single_turn.py      # baseline: target reachable, scoring works
python harness/converters.py       # does Base64 obfuscation change the outcome?
python harness/indirect_inject.py  # instruction hidden in a "document"
python harness/multi_turn.py        # Crescendo-style escalation (needs a 2nd local model)
python harness/scoring.py          # automated refusal scoring
```

## What's inside

| File | What it demonstrates |
|------|----------------------|
| `harness/single_turn.py` | `PromptSendingAttack` against a local target |
| `harness/converters.py` | Converter chains (Base64) and outcome deltas |
| `harness/multi_turn.py` | Multi-turn / Crescendo escalation with an adversarial model |
| `harness/indirect_inject.py` | Indirect prompt injection via attacker-controlled data |
| `harness/scoring.py` | Automated scoring (`SubStringScorer`, self-ask refusal) |
| `findings/results.md` | Results table + defender notes |

## Findings

See [findings/results.md](findings/results.md). Summary of defender takeaways:

- **Filter after decoding, not before.** If a Base64 (or similar) converter flips a
  refusal into compliance, input filtering runs only on the raw string.
- **Separate the data plane from the instruction plane.** Indirect injection
  succeeds because the model treats document/tool content as instructions. For
  agents, treat every tool and document result as untrusted input.
- **Score the whole conversation, not each turn.** Multi-turn escalation defeats
  per-turn checks; evaluate the full transcript against the objective.
- **Red teaming is continuous.** Mitigations reduce risk but don't eliminate it;
  rerun the harness as a regression suite after each change.

## References

- [PyRIT](https://github.com/microsoft/PyRIT) and [docs](https://microsoft.github.io/PyRIT/)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [MITRE ATLAS](https://atlas.mitre.org/)
- Microsoft, [Lessons from Red Teaming 100 Generative AI Products](https://arxiv.org/abs/2501.07238)
- Greshake et al., [Not what you've signed up for: indirect prompt injection](https://arxiv.org/abs/2302.12173)
