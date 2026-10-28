"""Optional LLM mode: rewrites an already-chosen explanation for the reader.

The decision is NOT made here. By the time this module runs, rules.match() has
already picked the scenario deterministically and explain.explain() has already
produced the text. All the LLM does is rewrite that text for a given level.
That separation is the point: if the network is down, or no API key is set, or
the model returns something unsafe, gitwhy falls back to the template and keeps
working.

No third-party packages: the HTTP call uses urllib from the standard library,
so `dependencies` in pyproject.toml stays empty.

Set up with:
    export ANTHROPIC_API_KEY=sk-...
    gitwhy --ai
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional, Tuple

from . import explain

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-5-5"
TIMEOUT = 20.0
MAX_TOKENS = 1500

LEVELS = {
    "beginner": (
        "The reader has used git for a few weeks. Avoid jargon; when a term "
        "like HEAD or upstream is unavoidable, explain it in half a sentence."
    ),
    "normal": (
        "The reader uses git daily but does not know this particular state. "
        "Be brief and skip the basics."
    ),
}

PROMPT = """You are rewriting one explanation produced by gitwhy, a tool that
explains why a git command failed. The repository state below was measured, and
the scenario was already identified deterministically. Do not re-diagnose it and
do not change the conclusion.

{level}

Rules you must follow:
- Keep every git command EXACTLY as written, byte for byte. Do not add commands
  that are not already in the text. Do not remove any.
- Keep every line starting with "> WARNING:" and keep what it says is deleted.
- Keep the three "##" sections and their order.
- Output markdown only, no preamble, no code fences around the whole answer.

The explanation to rewrite:

{text}
"""


def model() -> str:
    return os.environ.get("GITWHY_MODEL", DEFAULT_MODEL)


def api_key() -> Optional[str]:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return key or None


def available() -> bool:
    """Can AI mode even be attempted? (Does not prove the network works.)"""
    return api_key() is not None


def vet(original: str, rewritten: str) -> Optional[str]:
    """Is the rewrite safe to show? Returns the reason to reject it, or None.

    This gate is why AI mode can exist in a tool that suggests irreversible
    commands. An LLM that invents `git reset --hard`, or drops the warning
    from a command that deletes work, would do real damage. Instead of trusting
    the model, we check the output and fall back to the template on any doubt.
    """
    if not rewritten or len(rewritten.strip()) < 40:
        return "the answer is empty or too short"

    # 1. No destructive command that was not already there.
    for cmd in explain.DESTRUCTIVE_COMMANDS:
        if cmd in rewritten and cmd not in original:
            return "introduced a new destructive command: %s" % cmd

    # 2. Every destructive command that stayed must still carry a warning.
    if explain.is_destructive(rewritten) and not explain.has_warning(rewritten):
        return "dropped the warning from a destructive command"

    # 3. No command may be silently lost: if the original warned about what is
    #    deleted, the rewrite must still say it.
    if explain.is_destructive(original):
        block = "\n".join(
            line for line in rewritten.splitlines() if line.strip().startswith(">")
        )
        if explain.WARNING_MARKER not in block:
            return "the warning no longer says what gets deleted"

    return None


def _request(text: str, level: str) -> Tuple[Optional[str], Optional[str]]:
    """One API call. Returns (answer, error message); never raises."""
    key = api_key()
    if key is None:
        return None, "ANTHROPIC_API_KEY is not set"

    body = json.dumps({
        "model": model(),
        "max_tokens": MAX_TOKENS,
        "messages": [{
            "role": "user",
            "content": PROMPT.format(
                level=LEVELS.get(level, LEVELS["beginner"]), text=text),
        }],
    }).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": API_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, "API error %s" % e.code
    except urllib.error.URLError as e:
        return None, "could not reach the API (%s)" % e.reason
    except (OSError, ValueError) as e:
        return None, "request failed (%s)" % e

    try:
        parts = [b.get("text", "") for b in payload.get("content", [])
                 if b.get("type") == "text"]
    except AttributeError:
        return None, "unexpected response shape"
    answer = "".join(parts).strip()
    return (answer, None) if answer else (None, "the answer was empty")


def rewrite(text: str, level: str = "beginner") -> Tuple[str, Optional[str]]:
    """Rewrite the explanation. Returns (text to show, note).

    The note is non-empty when the template was used instead; the caller
    prints it so the user knows which mode they actually got.
    """
    answer, error = _request(text, level)
    if error:
        return text, "AI mode unavailable (%s); showing the template." % error
    reason = vet(text, answer)
    if reason:
        return text, (
            "The AI answer was rejected (%s); showing the template." % reason
        )
    return answer, None
