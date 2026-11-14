"""
agent.py — a minimal, real tool-using agent loop.

The agent is a system prompt + a tool schema + a parse-act loop over a real model
(targets.OllamaTarget). It asks the model for a JSON tool call, executes it
against the Env (which records the call for the oracle), feeds the tool output
back, and repeats up to `max_steps`. This is the surface the indirect injection
attacks: poisoned tool output comes back into the model's context.

Tool-call protocol: the model is asked to reply with a single JSON object
{"tool": name, "args": {...}} or {"final": "text"}. We parse leniently (models
wrap JSON in prose), which is realistic.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field

from environment import Env, ToolCall


def _balanced_objects(text: str) -> list[str]:
    """Extract top-level balanced {...} blocks (handles nested objects like
    args), tracking string literals so braces inside strings don't confuse it.
    Real models wrap nested JSON in prose, so the parser must handle nesting."""
    out, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(text[start:i + 1])
                    start = None
    return out


def _parse_action(text: str) -> dict | None:
    """Return the last JSON object carrying a 'tool' or 'final' key, nesting-aware."""
    for b in reversed(_balanced_objects(text)):
        try:
            obj = json.loads(b)
        except Exception:
            continue
        if isinstance(obj, dict) and ("tool" in obj or "final" in obj):
            return obj
    return None


@dataclass
class Transcript:
    episode_id: str
    messages: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    final: str = ""
    truncated: bool = False   # some model reply hit the token cap (degenerate output)


def run_episode(target, env: Env, system_prompt: str, injection_text: str,
                episode_id: str, max_steps: int = 4, seed: int = 0) -> Transcript:
    """Drive one agent episode against a real target. `injection_text` is the
    attacker payload that will be spliced into poisoned tool output by the Env."""
    tools_desc = "\n".join(
        f"- {t['name']}({', '.join(t['args'])}): {t['desc']}" for t in env.tools_spec())
    sys = (f"{system_prompt}\n\nYou can call tools. Available tools:\n{tools_desc}\n\n"
           "Reply with ONE JSON object only: {\"tool\": \"<name>\", \"args\": {...}} "
           "to call a tool, or {\"final\": \"<answer to the user>\"} when done.")
    msgs = [{"role": "system", "content": sys},
            {"role": "user", "content": env.user_goal}]
    tr = Transcript(episode_id=episode_id, messages=list(msgs))

    for _step in range(max_steps):
        reply = target.chat(msgs, seed=seed, episode_id=episode_id)
        if getattr(target, "last_truncated", False):
            tr.truncated = True
        msgs.append({"role": "assistant", "content": reply})
        tr.messages.append({"role": "assistant", "content": reply})
        action = _parse_action(reply)
        if action is None:
            tr.final = reply
            break
        if "final" in action:
            tr.final = str(action["final"])
            break
        call = ToolCall(name=str(action.get("tool", "")),
                        args=action.get("args", {}) if isinstance(action.get("args"), dict) else {})
        tr.actions.append({"tool": call.name, "args": call.args})
        tool_out = env.run_tool(call, injection_text)
        msgs.append({"role": "tool", "content": tool_out})
        tr.messages.append({"role": "tool", "content": tool_out})
    return tr
