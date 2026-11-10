# Findings

All runs target a **local, self-hosted model** (Ollama). Objectives are benign
canaries chosen to measure control behavior, not to elicit harmful content.

| # | Technique | Objective type | Outcome | Defender note |
|---|-----------|----------------|---------|---------------|
| 1 | Single-turn baseline | benign | _run and fill_ | Establishes baseline refusal/response rate |
| 2 | Base64 converter | benign | _run and fill_ | If obfuscation flips the outcome, input filtering is pre-decode only |
| 3 | Multi-turn (Crescendo) | canary token | _run and fill_ | Gradual escalation defeats per-turn checks; score the whole conversation |
| 4 | Indirect injection | canary token | _run and fill_ | Treat tool/document content as untrusted; separate data and instruction planes |

## Method

- Threat model (Microsoft ontology): actor, TTPs, weakness, impact.
- Each technique is scored automatically (substring / self-ask refusal) so results
  are reproducible rather than judged by eye.
- Nothing is run against a third-party product or hosted API.
