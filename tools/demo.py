"""Produces the README recording: docs/demo.gif and docs/demo.cast.

Why a recording program instead of a hand-made take:

- asciinema has no Windows build. This repository is developed on Windows.
- A hand-made take brings typos, pauses and retakes. Here the flow is fixed:
  the same GIF comes out on every run.
- Every byte of the output is REAL. This tool creates a temporary repository,
  actually runs the commands, and draws exactly what it captured. No line is
  written by hand; otherwise the GIF would be a picture, not a claim.

Usage:
    python tools/demo.py                # docs/demo.gif + docs/demo.cast
    python tools/demo.py --cast-only    # the .cast without producing a GIF

The GIF needs Pillow (`pip install pillow`). The .cast is produced either way
and can be turned into a GIF with `agg demo.cast demo.gif`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
DOCS = os.path.join(ROOT, "docs")

COLS, ROWS = 96, 36
PROMPT = "student@hackathon ~/project (feature) $ "

BASE_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="student",
    GIT_AUTHOR_EMAIL="student@school.edu",
    GIT_COMMITTER_NAME="student",
    GIT_COMMITTER_EMAIL="student@school.edu",
    GIT_CONFIG_GLOBAL=os.path.join(tempfile.gettempdir(), "gitwhy_demo_no_config"),
    GIT_CONFIG_SYSTEM=os.path.join(tempfile.gettempdir(), "gitwhy_demo_no_config"),
    LC_ALL="C",
    GIT_TERMINAL_PROMPT="0",
    PYTHONPATH=SRC,
    PYTHONIOENCODING="utf-8",
    # `rebase --continue` normally opens an editor; there is none in a recording.
    GIT_EDITOR="true",
)


def run(repo, argv):
    """Run the command and return its output in terminal order.

    In a real terminal git writes to stdout first (Auto-merging, CONFLICT) and
    then to stderr (error:, hint:). This approximation follows that order.
    """
    p = subprocess.run(argv, cwd=repo, capture_output=True, env=BASE_ENV)
    out = _clean(p.stdout.decode("utf-8", "replace"))
    err = _clean(p.stderr.decode("utf-8", "replace"))
    # Insert a newline when stdout does not end with one: git writes its
    # progress line ("Rebasing (1/1)") without a line break and stderr sticks
    # to it otherwise.
    if out and err and not out.endswith("\n"):
        out += "\n"
    return (out + err).rstrip("\n"), p.returncode


def _clean(text):
    """Flatten CR-overwritten progress output the way a terminal shows it."""
    text = text.replace("\r\n", "\n")
    return "\n".join(line.split("\r")[-1] for line in text.split("\n"))


def _write(repo, name, text):
    with open(os.path.join(repo, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_repo():
    """Build a real repository heading into a rebase conflict. Not recorded."""
    root = tempfile.mkdtemp(prefix="gitwhy_demo_")
    repo = os.path.join(root, "project")
    os.makedirs(repo)
    run(repo, ["git", "init", "-q", "-b", "main"])
    _write(repo, "a.txt", "title\n")
    run(repo, ["git", "add", "a.txt"])
    run(repo, ["git", "commit", "-qm", "first commit"])
    _write(repo, "a.txt", "title\nwritten on main\n")
    run(repo, ["git", "commit", "-qam", "keep going on main"])
    run(repo, ["git", "checkout", "-q", "-b", "feature", "HEAD~1"])
    _write(repo, "a.txt", "title\nwritten on the feature branch\n")
    run(repo, ["git", "commit", "-qam", "add feature"])
    return root, repo


def resolve_conflict(repo):
    """Resolve the conflict on the user's behalf: keep both sides."""
    _write(repo, "a.txt",
           "title\nwritten on main\nwritten on the feature branch\n")
    return "", 0


PY = sys.executable
GITWHY = [PY, "-m", "gitwhy.cli"]

# (what appears on screen, what gets run, seconds to hold after the output)
STEPS = [
    ("git rebase main", ["git", "rebase", "main"], 3.4),
    ("gitwhy", GITWHY, 9.5),
    ("nano a.txt   # resolve the conflict", resolve_conflict, 1.4),
    ("git add a.txt", ["git", "add", "a.txt"], 0.8),
    ("git rebase --continue", ["git", "rebase", "--continue"], 3.0),
    ("gitwhy doctor", GITWHY + ["doctor"], 4.5),
]

TYPING_SPEED = 0.045    # seconds per character, for the .cast
PROMPT_PAUSE = 0.75     # between the command appearing and the output


def record():
    """Run the steps; return (prompt+command, output) pairs and the holds."""
    root, repo = build_repo()
    script = []
    try:
        for shown, action, hold in STEPS:
            if callable(action):
                output, _ = action(repo)
            else:
                output, _ = run(repo, action)
            script.append({"command": shown, "output": output, "hold": hold})
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return script


# --- asciicast v2 ---------------------------------------------------------

ANSI = {
    "prompt": "\x1b[32m",
    "command": "\x1b[97m",
    "error": "\x1b[31m",
    "hint": "\x1b[90m",
    "warning": "\x1b[33m",
    "heading": "\x1b[96m",
    "reset": "\x1b[0m",
}


def _line_colour(line):
    s = line.lstrip()
    if s.startswith(("error:", "fatal:", "CONFLICT")):
        return "error"
    if s.startswith("hint:"):
        return "hint"
    if s.startswith("> WARNING"):
        return "warning"
    if s.startswith("##") or s.startswith("# gitwhy"):
        return "heading"
    return None


def write_cast(script, path):
    events = []
    t = 0.3
    for step in script:
        events.append([round(t, 3), "o", ANSI["prompt"] + PROMPT + ANSI["reset"]])
        for ch in step["command"]:
            t += TYPING_SPEED
            events.append([round(t, 3), "o", ANSI["command"] + ch + ANSI["reset"]])
        t += PROMPT_PAUSE
        events.append([round(t, 3), "o", "\r\n"])
        if step["output"]:
            for line in step["output"].split("\n"):
                colour = _line_colour(line)
                text = (ANSI[colour] + line + ANSI["reset"]) if colour else line
                t += 0.03
                events.append([round(t, 3), "o", text + "\r\n"])
        t += step["hold"]
    events.append([round(t, 3), "o", ANSI["prompt"] + PROMPT + ANSI["reset"]])

    header = {
        "version": 2,
        "width": COLS,
        "height": ROWS,
        "timestamp": int(time.time()),
        "title": "gitwhy — rebase conflict",
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(header, ensure_ascii=False) + "\n")
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return t


# --- GIF ------------------------------------------------------------------

BACKGROUND = (13, 17, 23)
FOREGROUND = (201, 209, 217)
GIF_COLOURS = {
    "prompt": (63, 185, 80),
    "command": (230, 237, 243),
    "error": (248, 81, 73),
    "hint": (110, 118, 129),
    "warning": (210, 153, 34),
    "heading": (121, 192, 255),
}

FONT_PATHS = (
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Menlo.ttc",
)


def _font(size=15):
    from PIL import ImageFont
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        "No monospaced font found. Provide one of these paths:\n  "
        + "\n  ".join(FONT_PATHS)
    )


def _wrap(line, width):
    """Wrap a long line the way a terminal would."""
    if len(line) <= width:
        return [line]
    parts = []
    while line:
        parts.append(line[:width])
        line = line[width:]
    return parts


def write_gif(script, path):
    """Two frames per step: the command appears, then its output. Holds are
    expressed as frame durations, which keeps the GIF under 20 frames."""
    from PIL import Image, ImageDraw

    font = _font(15)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cw = probe.textlength("M", font=font)
    ch = 20
    pad = 14
    width = int(COLS * cw) + pad * 2
    height = ROWS * ch + pad * 2

    screen = []   # (text, colour name | None)
    frames, durations = [], []

    def frame(seconds, cursor=False):
        visible = screen[-ROWS:]
        img = Image.new("RGB", (width, height), BACKGROUND)
        d = ImageDraw.Draw(img)
        for i, (text, colour) in enumerate(visible):
            y = pad + i * ch
            if colour == "prompt_command":
                d.text((pad, y), PROMPT, font=font, fill=GIF_COLOURS["prompt"])
                d.text((pad + cw * len(PROMPT), y), text, font=font,
                       fill=GIF_COLOURS["command"])
                if cursor and i == len(visible) - 1:
                    x = pad + cw * (len(PROMPT) + len(text))
                    d.rectangle([x, y + 2, x + cw, y + ch - 4],
                                fill=GIF_COLOURS["command"])
            else:
                d.text((pad, y), text, font=font,
                       fill=GIF_COLOURS.get(colour, FOREGROUND))
        frames.append(img)
        durations.append(int(seconds * 1000))

    frame(0.6)
    for step in script:
        screen.append((step["command"], "prompt_command"))
        frame(PROMPT_PAUSE, cursor=True)
        if step["output"]:
            for line in step["output"].split("\n"):
                colour = _line_colour(line)
                for part in _wrap(line, COLS):
                    screen.append((part, colour))
        screen.append(("", None))
        frame(step["hold"])
    frame(2.0)

    frames[0].save(
        path, save_all=True, append_images=frames[1:],
        duration=durations, loop=0, optimize=True, disposal=2,
    )
    return sum(durations) / 1000.0, len(frames)


def main():
    ap = argparse.ArgumentParser(description="Produces the README recording")
    ap.add_argument("--cast-only", action="store_true")
    arg = ap.parse_args()

    os.makedirs(DOCS, exist_ok=True)
    script = record()

    cast_path = os.path.join(DOCS, "demo.cast")
    seconds = write_cast(script, cast_path)
    print("demo.cast  %6.1f s  %s" % (seconds, cast_path))

    if arg.cast_only:
        return 0
    gif_path = os.path.join(DOCS, "demo.gif")
    gif_seconds, frame_count = write_gif(script, gif_path)
    print("demo.gif   %6.1f s  %d frames  %.0f KB  %s" % (
        gif_seconds, frame_count, os.path.getsize(gif_path) / 1024, gif_path))
    if not 20 <= gif_seconds <= 30:
        print("WARNING: target is 20-30 s, currently %.1f s. Adjust the holds in STEPS."
              % gif_seconds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
