# agent-injection-eval

**Do prompt-injection defenses for tool-using LLM agents survive an *adaptive*
attacker — or only the static probes their authors test?**

A small, reproducible evaluation harness that measures it against a **real model**
(open-weight, via Ollama) with an **objective, oracle-based** success metric — not
a mock, not a string match, not self-graded.

This is the deep counterpart to a set of teaching PoCs: instead of simulating an
attack against a mock rigged to leak, it runs the attack against a model that
genuinely does or doesn't fall for it, and reports a number a third party can
reproduce.

## The claim being tested

Defense papers usually report Attack Success Rate (ASR) against a **fixed** set of
injection probes. A real adversary **adapts**. The hypothesis (pre-registered in
`PREREGISTRATION.md`): adaptive ASR is materially higher than static ASR, and the
*ranking* of defenses can flip under adaptation — so static evaluations overstate
how well a defense holds. A clean null result (adaptive ≈ static) is reported as
such, not buried.

## Why this design is honest

- **Objective primary metric.** Success = the agent actually invoked the injected
  (fake, canary) tool action, read from the environment's **tool-call log** (an
  AgentDojo-style state oracle). No LLM judge in the headline number; nothing the
  harness can rig.
- **Real target.** The model under test is a real open-weight model you run; the
  harness only talks to it.
- **Adaptive attacker that isn't handed the answer.** Mutation operators are
  generic obfuscation/framing transforms with no defense-specific secret.
- **Calibrated secondary judge.** The text-based judge is reported only if it
  agrees with human labels (Cohen's κ ≥ 0.6); otherwise it's dropped.
- **Pre-registered + reproducible.** Hypothesis and metrics fixed before data;
  every episode's transcript + verdict logged; seeds/versions pinned.

## Layout

```
PREREGISTRATION.md     hypothesis, threat model, metrics, falsification, checklist
RUNBOOK.md             exact steps to run it on your Mac (Ollama) and send results
src/
  targets.py           OllamaTarget (real, stdlib urllib) · ReplayTarget · test stub
  environment.py       tool-using tasks + STATE ORACLE + canary (AgentDojo-shaped)
  agent.py             minimal real agent loop (nesting-aware tool-call parser)
  attacks.py           static library + ADAPTIVE best-first attacker (the core)
  defenses.py          none · prompt_level · spotlighting · classifier(stub)
  judges.py            secondary text judge + Cohen's kappa
  metrics.py           ASR, Wilson 95% CIs, ASR@N, static-vs-adaptive headline
  run.py               experiment runner (logs transcripts + summary)
  analyze.py           tables, H1/H2 verdicts, ASR@N curves (+ optional plot)
calibration/           human-labeling template + protocol + kappa scorer
tests/                 offline tests of the harness logic (use a TEST DOUBLE)
config/experiment.json run configuration
report/                findings report scaffold (+ a clearly-labeled SAMPLE table)
blog/                  public write-up draft
```

## Run it

Core needs only **Python 3.9+ and Ollama** (no pip). See `RUNBOOK.md`:

```bash
python3 tests/test_harness.py                       # verify harness logic (no model)
ollama serve &  ; ollama pull llama3.1:8b
python3 src/run.py --smoke                           # wiring check vs real model
python3 src/run.py --model llama3.1:8b --seeds 20 --budget 16
python3 src/analyze.py "results/summary-*.json" --md report/results_table.md
```

## What makes a result here trustworthy (not my word or yours)

Third-party reproduction within CI · pinned model/tool/seed · saved transcripts ·
a reproduction anchor in the expected range · oracle-based primary metric ·
judge κ reported vs humans · ideally ≥ 2 models. Full checklist in
`PREREGISTRATION.md §9`.

## Scope / responsible use

Legitimate AI-security evaluation only. The target is an open-weight model you run
and are authorized to test; the injected objective is a **benign canary action** in
a sandboxed environment; no harmful content is produced. The adaptive attacker
exists to measure defense robustness, which is how you improve it.
