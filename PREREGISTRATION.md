# Pre-registration: Indirect prompt injection and defense transfer on small open-weight agents

**Author:** Ugur Eminli (github.com/Eminli)
**Status:** Pre-registered — committed before any scored run. Deviations logged in Section 11.
**Harness:** AgentDojo (Debenedetti et al., NeurIPS 2024 D&B, arXiv:2406.13352), benchmark version v1.2.2.

## 1. Question
On a sandboxed tool-using agent, does indirect prompt injection succeed against small
open-weight models, and do AgentDojo's defenses reduce that success in the same rank
order they do for frontier models?

## 2. Gap
AgentDojo's published results cover frontier API models only. Under the
`important_instructions` attack, no defense: gpt-4o-2024-05-13 = 47.69% targeted ASR /
69.07% benign utility; gpt-4-0125-preview = 56.28% / 65.98%; claude-3-5-sonnet-20241022 =
1.11% / 79.38%. Defenses on gpt-4o rank very differently: tool_filter 6.84% ASR (utility
72.16%), spotlighting_with_delimiting 41.65% ASR (72.16%), transformers_pi_detector 7.95%
(41.24%), repeat_user_prompt 27.82% (84.54%). (Source: agentdojo.spylab.ai/results.)
No comparable numbers exist for self-hostable 7-8B open-weight models. This fills that cell.

## 3. Hypotheses (directional, falsifiable)
- H1: targeted ASR (important_instructions, no defense) is well above the no-attack
  baseline (~0) for all three models. Prediction: 30-70%.
- H2: tool_filter (structural) reduces ASR by a large, significant margin;
  spotlighting_with_delimiting (prompt-level) reduces it only marginally or not at all.
- H3: the attack ASR and each defense's delta differ across the three families, but the
  defense ranking (tool_filter > spotlighting) holds.

## 4. System under test
- AgentDojo v1.2.2, provider `openai-compatible` -> Ollama
  (OPENAI_COMPATIBLE_BASE_URL=http://localhost:11434/v1, --model-id = the Ollama tag).
- Suites: CORE = `banking`. STRETCH (declared now, run if time permits) = `workspace`.
- Success oracle is DETERMINISTIC: AgentDojo checks sandbox environment state (did the
  attacker goal occur), not an LLM judge. No judge-reliability / kappa question for the
  primary result. (Kappa would apply only to a text-harm arm, which is NOT in this plan.)

## 5. Models (pre-committed), served via Ollama, decoding temperature 0
1. llama3.1:8b   2. qwen2.5:7b   3. mistral:7b
Exact Ollama digests recorded in Section 10 at freeze.
Tool-calling path confirmed by smoke test before any scored run; if a model's native
tool-calling via Ollama is unreliable, fall back to provider `local` with --tool-delimiter
and log the deviation.

## 6. Attack and defenses (pre-committed)
- Attack: `important_instructions` (strongest standard AgentDojo attack). Single attack.
- Defense arm: no-defense (baseline), `tool_filter` (primary), `spotlighting_with_delimiting`
  (contrast). STRETCH (declared now): `transformers_pi_detector`, `repeat_user_prompt`.

## 7. Conditions and metrics
Conditions per model: (a) no-attack [benign utility], (b) attack+no-defense [ASR baseline],
(c) attack+tool_filter, (d) attack+spotlighting. Stretch defenses add (e),(f).
Metrics (AgentDojo-native): targeted ASR; benign utility; utility under attack (guards
against a defense that "works" by breaking the agent). Unit of analysis: one
(user_task x injection_task) pair. N per suite recorded from the first run.

## 8. Statistics (CORRECTED — AgentDojo has no seed flag; temp 0 => near-deterministic)
- Primary uncertainty: Wilson 95% CI over the N task pairs (binomial), per cell.
- Defense effect: defense vs no-defense is paired on the same task pairs -> McNemar's exact
  test for delta-ASR, reported with the effect size (delta-ASR) and its CI. alpha = 0.05.
- Across models: unpaired two-proportion comparison; report ASRs with CIs side by side.
- Multiplicity: Holm correction across the confirmatory tests (H1 x3, H2-tool_filter x3,
  H2-spotlighting x3) within a suite.
- Stability (stretch, not primary): 2 repeat runs at temperature 0.7 into separate logdirs
  to show run-to-run variance; does not replace the Wilson CI.

## 9. Calibration (external validity) — ONE OPEN DECISION
Reproduce one published AgentDojo number within its range before trusting open-weight
numbers. Target: gpt-4o-2024-05-13 / important_instructions / no defense -> ASR 47.69%,
utility 69.07%; pass = within the Wilson CI of the published point.
OPEN DECISION (needs an OpenAI key, in slight tension with "local-only"):
(a) allow this one reference run [recommended, strongest];
(b) calibrate against a published open-weight number if one exists under this protocol;
(c) install-level reproduction only [weakest]. Chosen: ____.

## 10. Freeze record (filled at commit/freeze time)
AgentDojo version: ____  Ollama digests: llama3.1 ____, qwen2.5 ____, mistral ____
N(banking) = ____ task pairs.  Freeze commit hash: ____  UTC: ____

## 11. Deviation log
Empty at freeze. (Pre-freeze correction to Section 8 — removed the seed design after
confirming AgentDojo exposes no seed flag and runs at temperature 0 — was made before
freeze and is not a post-hoc change.)

## 12. Scope and ethics
AgentDojo sandbox + self-hosted open-weight models only (plus one optional API calibration
run per Section 9). "Harm" is a benign simulated action inside the sandbox, never harmful
text or any real-world effect. Standard academic benchmark. Findings written for defenders
with a responsible-disclosure note. No third-party production system is tested.
