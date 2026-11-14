# Findings — Adaptive attacks vs. prompt-injection defenses for tool-using agents

*Status: scaffold. The `[FILL]` blanks are completed from a real run's
`analyze.py` output; do not write numbers that aren't in a logged summary.*

## Abstract

We evaluate whether common prompt-injection defenses for tool-using LLM agents
(prompt-level hardening, Spotlighting, [optionally a classifier guardrail]) hold
under an **adaptive** attacker, using an objective tool-state oracle on a real
open-weight model. Across `[FILL: K]` tasks × `[FILL: S]` seeds on `[FILL:
model(s)]`, static ASR was `[FILL]` and adaptive ASR was `[FILL]`
(Δ = `[FILL] pp`). H1 was `[FILL: SUPPORTED / NOT supported]`.

## 1. Setup

- **Model(s):** `[FILL]` (Ollama `[version]`, digests `[FILL]`).
- **Tasks:** `[FILL: K]` agent tasks, each a benign objective + an injected canary
  action, oracle-checked. (`src/environment.py` / AgentDojo adapter.)
- **Defenses:** none, prompt_level, spotlighting`[, classifier]`.
- **Attacks:** static library (`[FILL: size]`) vs. adaptive best-first search,
  budget N = `[FILL]`, `[FILL: S]` seeds/cell.
- **Primary metric:** injection ASR from the tool-state oracle. **Secondary:**
  text-leak rate (reported only if κ ≥ 0.6, see §5).

## 2. Reproduction anchor

Undefended static ASR = `[FILL]%` — `[in / not in]` the expected (clearly > 0)
range, so the harness is `[validated / suspect]`. (PREREGISTRATION §7.)

## 3. Headline result (paste from analyze.py)

```
[FILL: the Static vs. adaptive ASR table]
```

- **H1 (adaptive > static for some defense):** `[FILL]`.
- **H2 (defense ranking changes under adaptation):** `[FILL]`.
- **ASR@N:** `[FILL: curves]` — `[monotone? where does budget stop helping?]`

## 4. Utility / over-refusal

`[FILL: benign-task success and over-refusal per defense]`. Interpretation:
`[does the defense that most cuts ASR also cost the most utility? — H3]`.

## 5. Judge calibration

Text judge vs. `[FILL: #]` human labels: Cohen's κ = `[FILL]`
(`[substantial / moderate / ...]`). Decision: `[report / drop]` the text metric.

## 6. Discussion

`[FILL: what this means. If adaptive >> static: static evaluations overstate
defense robustness; name which defense degraded most and the operator cost. If
null: these defenses held against this attacker at this budget on this model —
and say why that's a real (if narrower) finding.]`

## 7. Limitations

Single/few models; a small task set; the adaptive attacker is one search strategy
among many (a stronger attacker could raise ASR further — so reported adaptive ASR
is a **lower bound** on what's achievable); mock environment unless the AgentDojo
adapter was used. `[FILL: any run-specific caveats]`.

## 8. External-validation checklist (PREREGISTRATION §9)

- [ ] Third party reproduced the headline within CI
- [ ] Model/tool/seed pinned and logged
- [ ] Every episode transcript saved
- [ ] Reproduction anchor in range
- [ ] Judge κ reported; text metric dropped if κ < 0.6
- [ ] Primary metric oracle-based
- [ ] ≥ 2 models, or single-model scope stated

## Appendix

Config, model digests, and the first few transcripts for each cell.
