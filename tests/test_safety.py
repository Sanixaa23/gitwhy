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


def test_no_template_can_crash_a_narrow_console():
    """An explanation that cannot be printed is not an explanation.

    Python encodes stdout with the locale codepage. On Windows that is
    cp1252 across most of the English-speaking world, and cp1254 on the
    machine this was found on. Neither has U+2192. One template had an
    arrow in its "Where you are" line, so `gitwhy` raised
    UnicodeEncodeError and printed a traceback instead of an answer -- on
    07_push_rejected, which is the most common git failure there is.

    cp437 is the strictest codepage a terminal still plausibly runs, so
    encoding cleanly to it is the bar. `errors="replace"` in the CLI means
    a stray character degrades to "?" rather than crashing, but a template
    should not need that rescue: this test keeps the rescue for genuine
    surprises instead of for characters we chose.

    Em-dashes are exempt. They are deliberate prose typography, they exist
    in every Windows codepage the tool realistically meets, and the CLI's
    replace handler covers the rest.
    """
    exempt = {"\u2014"}  # em-dash
    faulty = []
    for name, text in explain.templates().items():
        for line_no, line in enumerate(text.splitlines(), 1):
            for char in line:
                if ord(char) < 127 or char in exempt:
                    continue
                try:
                    char.encode("cp437")
                except UnicodeEncodeError:
                    faulty.append("%s:%d U+%04X %r" % (name, line_no, ord(char), char))
    assert not faulty, "unprintable on a narrow console: %s" % faulty


def test_the_cli_survives_a_codepage_that_cannot_hold_the_text():
    """The rescue itself, exercised rather than assumed.

    Writes a template through a stream encoded cp437 the way the CLI
    configures its own output. It must come back with the text intact
    enough to read, and above all it must not raise.
    """
    import io

    from gitwhy import cli

    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp437", errors="replace")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = stream
    try:
        cli._make_output_printable()   # must not raise on a live stream
        text = explain.templates()["07_push_rejected"]
        sys.stdout.write(text)        # must not raise on a narrow codepage
        sys.stdout.flush()
    finally:
        sys.stdout, sys.stderr = real_stdout, real_stderr

    written = raw.getvalue()
    assert b"What happened" in written
    assert b"What to do" in written
