"""AI mode tests. No network: the gate is what matters, not the model.

The point of these tests is the claim we make to a judge: an LLM may rewrite
the prose, but it cannot introduce a destructive command, and it cannot drop
the warning that says what gets deleted. If it tries, the template is shown
instead.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from gitwhy import ai, explain  # noqa: E402

SAFE_ORIGINAL = """## What happened

A rebase stopped halfway.

## What to do

    git rebase --continue

> WARNING: `git rebase --abort` PERMANENTLY deletes the conflict fixes you made.
"""


def test_faithful_rewrite_is_accepted():
    rewritten = SAFE_ORIGINAL.replace("A rebase stopped halfway.",
                                      "Your rebase paused in the middle.")
    assert ai.vet(SAFE_ORIGINAL, rewritten) is None


def test_new_destructive_command_is_rejected():
    """The model must not invent a command that destroys work."""
    rewritten = SAFE_ORIGINAL.replace(
        "    git rebase --continue",
        "    git reset --hard HEAD\n    git rebase --continue")
    reason = ai.vet(SAFE_ORIGINAL, rewritten)
    assert reason is not None and "git reset --hard" in reason


def test_dropping_the_warning_is_rejected():
    rewritten = "\n".join(
        line for line in SAFE_ORIGINAL.splitlines()
        if not line.startswith("> WARNING")
    )
    assert ai.vet(SAFE_ORIGINAL, rewritten) is not None


def test_watering_down_the_warning_is_rejected():
    """A warning that no longer says what is deleted does not count."""
    rewritten = SAFE_ORIGINAL.replace(
        "> WARNING: `git rebase --abort` PERMANENTLY deletes the conflict fixes you made.",
        "> WARNING: `git rebase --abort` is a little risky, be careful.")
    assert ai.vet(SAFE_ORIGINAL, rewritten) is not None


def test_empty_answer_is_rejected():
    assert ai.vet(SAFE_ORIGINAL, "") is not None
    assert ai.vet(SAFE_ORIGINAL, "ok") is not None


def test_every_destructive_command_is_covered_by_the_gate():
    """The gate reads the same list the templates are checked against."""
    for cmd in explain.DESTRUCTIVE_COMMANDS:
        injected = SAFE_ORIGINAL + "\n    " + cmd + "\n"
        if cmd in SAFE_ORIGINAL:
            continue
        assert ai.vet(SAFE_ORIGINAL, injected) is not None, (
            "%s got past the gate" % cmd
        )


def test_falls_back_to_the_template_without_a_key(monkeypatch=None):
    """No API key, no network call: the original text comes straight back."""
    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        assert not ai.available()
        text, note = ai.rewrite(SAFE_ORIGINAL)
        assert text == SAFE_ORIGINAL
        assert note and "ANTHROPIC_API_KEY" in note
    finally:
        if old is not None:
            os.environ["ANTHROPIC_API_KEY"] = old


def test_rewrite_returns_the_template_when_the_request_fails():
    """Any API failure degrades to the template instead of raising."""
    original_request = ai._request
    ai._request = lambda text, level: (None, "could not reach the API (test)")
    try:
        text, note = ai.rewrite(SAFE_ORIGINAL)
        assert text == SAFE_ORIGINAL
        assert note and "showing the template" in note
    finally:
        ai._request = original_request


def test_rewrite_returns_the_template_when_the_answer_is_unsafe():
    unsafe = SAFE_ORIGINAL + "\n    git push --force\n"
    original_request = ai._request
    ai._request = lambda text, level: (unsafe, None)
    try:
        text, note = ai.rewrite(SAFE_ORIGINAL)
        assert text == SAFE_ORIGINAL, "an unsafe answer was shown"
        assert note and "rejected" in note
    finally:
        ai._request = original_request


def test_accepted_answer_is_shown_with_no_note():
    good = SAFE_ORIGINAL.replace("A rebase stopped halfway.", "Rebase paused.")
    original_request = ai._request
    ai._request = lambda text, level: (good, None)
    try:
        text, note = ai.rewrite(SAFE_ORIGINAL)
        assert text == good
        assert note is None
    finally:
        ai._request = original_request


def test_ai_module_sends_nothing_by_itself():
    """Importing or vetting must never open a connection; only _request does."""
    path = os.path.join(ROOT, "src", "gitwhy", "ai.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    before, _, after = source.partition("def _request(")
    assert "urlopen" not in before, "a call outside _request opens a connection"
    # Exactly one call site, inside _request.
    assert after.count("urlopen") == 1
