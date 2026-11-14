# Your prompt-injection defense passed the test it was graded on. Did it pass the one that matters?

*Draft — pitched for GitHub/LinkedIn, a hiring audience in AI security. Fill the
`[FILL]` numbers from a real run before publishing. Keep the honest framing; if the
result is null, publish the null — "I tried to break these defenses and couldn't,
here's how hard I tried" is also a strong post.*

---

Most published prompt-injection defenses report a number like "reduces attack
success from 80% to 5%." That number is almost always measured against a **fixed
set of attack strings**. But an attacker isn't a fixed set of strings — an attacker
*adapts*. So I asked a narrower, more honest question:

**Do these defenses still work when the attacker gets to iterate against them?**

## The setup

I built a small, reproducible harness that attacks a **real** tool-using agent
(an open-weight model via Ollama — no API, runs on a laptop) and measures success
**objectively**: the agent's environment records every tool call, and an attack
"succeeds" only if the agent actually fires the injected action with a planted
canary. No string matching, no LLM grading the headline number, no mock rigged to
fail — the model either falls for it or it doesn't.

Then I ran two attackers against three defenses (no defense, prompt-level
hardening, and Microsoft-style Spotlighting):

- a **static** attacker — a fixed library of injection payloads, like the
  evaluations defenses are usually tuned against; and
- an **adaptive** attacker — a best-first search that mutates the payload
  (encoding, delimiter-breaking, authority framing, payload-splitting) and keeps
  what moves the model toward compliance, within a fixed query budget.

Everything is pre-registered: I wrote down the hypothesis and the metric before
collecting a single data point.

## The result

`[FILL: the one-paragraph headline. e.g. "Under static probes, Spotlighting cut
ASR to 8%. Under the adaptive attacker at a budget of 16, it rose to 58% — a 50-
point gap, with non-overlapping confidence intervals. And the defense that looked
best under static probes was not the most robust under adaptation."]`

`[FILL: drop the static-vs-adaptive table and the ASR@N curve here.]`

`[IF NULL: "The defenses held. At a budget of 16 against this model, the adaptive
attacker did not move ASR beyond the static baseline's confidence interval. That's
a real result too — and here's exactly how hard the attacker tried, so you can
judge whether it's hard enough."]`

## Why you can trust the number (or check it yourself)

- The primary metric is read from the agent's **tool-call log**, not from anyone's
  judgment.
- The secondary text judge is only reported if it agreed with **human labels**
  (Cohen's κ `[FILL]`).
- Model, tool version, and seeds are **pinned**; every episode's transcript is
  **logged**; the whole thing **reproduces** from one command.
- I checked a **reproduction anchor** first — an undefended baseline that should be
  easy to attack — so a broken harness couldn't quietly produce a flattering result.

Repo: `[FILL: github.com/Eminli/agent-injection-eval]`. Clone it, point it at your
own model, and see if you get my numbers.

## What I take from it

`[FILL: 2–3 sentences. The honest lesson is usually: "static ASR is an optimistic
number; report adaptive ASR at a stated budget, or you're measuring the attacker's
patience, not the defense." Tie to why this matters for anyone shipping an agent
with tools.]`

---

*Built as a focused piece of AI-security evaluation work. Methods and full
write-up in the repo; happy to discuss.*
