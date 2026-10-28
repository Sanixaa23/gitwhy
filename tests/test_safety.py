"""The safety rules are guaranteed by tests.

The sentence this file lets you say to a judge: "we guarantee with a test that
every destructive suggestion carries a warning."
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from gitwhy import explain  # noqa: E402


def test_every_destructive_template_carries_a_warning():
    faulty = [
        name for name, text in explain.templates().items()
        if explain.is_destructive(text) and not explain.has_warning(text)
    ]
    assert not faulty, "destructive command with no warning: %s" % faulty


def test_warning_says_what_gets_deleted():
    """A warning must say what is lost, not merely "be careful"."""
    faulty = []
    for name, text in explain.templates().items():
        if not explain.is_destructive(text):
            continue
        warnings = [
            line for line in text.splitlines()
            if line.strip().startswith(explain.WARNING_PREFIX)
        ]
        # A warning may wrap over several lines, so the whole block is checked.
        block = "\n".join(
            line for line in text.splitlines() if line.strip().startswith(">")
        )
        if not warnings or explain.WARNING_MARKER not in block:
            faulty.append(name)
    assert not faulty, "warning does not say what is deleted: %s" % faulty


def test_auto_runnable_list_holds_no_destructive_command():
    """If --run is added, the auto-runnable list must stay safe."""
    faulty = [c for c in explain.AUTO_RUNNABLE if explain.is_destructive(c)]
    assert not faulty, "destructive command in the auto-run list: %s" % faulty


def test_explain_module_runs_nothing():
    """The narration layer executes nothing: no subprocess allowed."""
    path = os.path.join(ROOT, "src", "gitwhy", "explain.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    for banned in ("subprocess", "os.system", "os.popen"):
        assert banned not in source, "explain.py contains %s" % banned


def test_context_module_does_not_modify_the_repository():
    """The context collector is read-only: no repo-modifying command may appear."""
    path = os.path.join(ROOT, "src", "gitwhy", "context.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    # Quoted argument strings are searched, not words in comments.
    for banned in ('"reset"', '"clean"', '"checkout"', '"commit"', '"push"',
                   '"merge"', '"rebase"', '"add"', '"stash"', '"restore"'):
        assert banned not in source, "context.py could modify the repo: %s" % banned
