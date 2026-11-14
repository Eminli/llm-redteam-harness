"""
targets.py — the model under test.

The whole point of the deep version: the TARGET is a real model, so an injection
either works or it doesn't — the harness cannot rig the outcome.

Backends (all talk through one interface, `Target.chat(messages) -> str`):
  - OllamaTarget   : real local model on the operator's Mac, over stdlib urllib
                     (no pip needed). This is the evaluation target.
  - ReplayTarget   : replays a logged transcript, for offline re-scoring/analysis
                     without re-querying the model.
  - ScriptedStub   : a deterministic test double used ONLY by tests/ — never in a
                     real evaluation. It exists so the attack/defense/judge logic
                     can be unit-tested offline; it is not a model.

No third-party dependencies. Python 3.9+.
"""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Protocol


class Target(Protocol):
    name: str
    def chat(self, messages: list[dict], **kw) -> str: ...


@dataclass
class OllamaTarget:
    """Calls a local Ollama server (default http://localhost:11434). Runs on the
    operator's machine; requires `ollama serve` and `ollama pull <model>`.
    Deterministic when `seed` is set and temperature=0."""
    model: str = "llama3.1:8b"
    host: str = "http://localhost:11434"
    temperature: float = 0.0
    seed: int | None = 0
    timeout: int = 120
    # Cap generated tokens. At temperature 0 some payloads (e.g. the base64
    # operator) send the model into an endless repetition loop; without a cap
    # Ollama generates until the socket times out and the run crashes.
    max_tokens: int = 512
    name: str = ""
    # True if the most recent reply was cut off at max_tokens (degenerate output).
    last_truncated: bool = False
    truncated_calls: int = 0   # running count, so the runner can attribute per episode

    def __post_init__(self):
        self.name = self.name or f"ollama:{self.model}"

    def chat(self, messages: list[dict], seed: int | None = None, **kw) -> str:
        self.last_truncated = False
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "seed": self.seed if seed is None else seed,
                "num_predict": self.max_tokens,
            },
        }
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=data,
            headers={"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    out = json.loads(resp.read())
                self.last_truncated = out.get("done_reason") == "length"
                self.truncated_calls += int(self.last_truncated)
                return out["message"]["content"]
            except (urllib.error.URLError, KeyError, TimeoutError) as e:
                # A read timeout is deterministic at temperature 0 (same prompt ->
                # same runaway generation), so retrying only multiplies the wait.
                timed_out = isinstance(e, TimeoutError) or isinstance(
                    getattr(e, "reason", None), TimeoutError)
                if timed_out:
                    raise RuntimeError(
                        f"Ollama call timed out after {self.timeout}s "
                        f"(model={self.model}); not retrying.") from e
                if attempt == 2:
                    raise RuntimeError(
                        f"Ollama call failed ({e}). Is `ollama serve` running and "
                        f"`ollama pull {self.model}` done?") from e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError("unreachable")


@dataclass
class ReplayTarget:
    """Replays recorded (episode_id -> response) pairs for offline re-scoring."""
    path: str
    name: str = "replay"
    _by_id: dict = field(default_factory=dict)

    def __post_init__(self):
        with open(self.path) as fh:
            for row in json.load(fh):
                self._by_id[row["episode_id"]] = row["response"]

    def chat(self, messages: list[dict], episode_id: str = "", **kw) -> str:
        return self._by_id.get(episode_id, "")


@dataclass
class ScriptedStub:
    """TEST DOUBLE ONLY. Deterministic fake used by tests/ to exercise harness
    logic offline. A real evaluation must use OllamaTarget. `rule` maps a
    substring found in the last user/tool message to a canned reply, so tests can
    simulate 'the model complied' or 'the model refused' without a model."""
    rules: list = field(default_factory=list)   # list of (needle, reply)
    default: str = "Okay, how can I help with your order?"
    name: str = "scripted-stub(TEST ONLY)"

    def chat(self, messages: list[dict], **kw) -> str:
        blob = " ".join(m.get("content", "") for m in messages).lower()
        for needle, reply in self.rules:
            if needle.lower() in blob:
                return reply
        return self.default
