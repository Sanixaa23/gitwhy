"""The `gitwhy doctor` screenshot for the README: docs/doctor.svg + docs/doctor.png

The screenshot is not taken by hand: this tool builds a genuinely unhealthy
repository, runs `gitwhy doctor`, and draws the output itself. Every line in
the image is the program's real output.

An SVG is produced because GitHub renders it crisply in a README and its text
stays selectable; the PNG is for pasting elsewhere.

Usage:
    python tools/doctor_image.py
"""
from __future__ import annotations

import os
import sys
import shutil
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

from demo import (  # noqa: E402
    DOCS, GITWHY, GIF_COLOURS, FOREGROUND, BACKGROUND, _font, _write, run,
)


def unhealthy_repo():
    """Build a repository doctor will really have findings about.

    Four separate problems: a staged .env, no .gitignore, no user.email, and a
    commit dropped by reset --hard.
    """
    root = tempfile.mkdtemp(prefix="gitwhy_doctor_")
    repo = os.path.join(root, "project")
    os.makedirs(repo)
    run(repo, ["git", "init", "-q", "-b", "main"])
    _write(repo, "app.py", "print('hello')\n")
    run(repo, ["git", "add", "app.py"])
    run(repo, ["git", "commit", "-qm", "first version"])

    # a commit dropped by reset --hard
    _write(repo, "report.md", "the report written overnight\n")
    run(repo, ["git", "add", "report.md"])
    run(repo, ["git", "commit", "-qm", "the report written overnight"])
    run(repo, ["git", "reset", "--hard", "-q", "HEAD~1"])

    # a staged .env and an unstaged change
    _write(repo, ".env", "OPENAI_API_KEY=fake-demo-value\n")
    run(repo, ["git", "add", ".env"])
    _write(repo, "app.py", "print('hello world')\n")
    return root, repo


def _line_colour(line: str) -> str:
    s = line.strip()
    if s.startswith("# gitwhy"):
        return "heading"
    if "NOT SET" in line or ": MISSING" in line:
        return "error"
    label, _, value = line.partition(":")
    if label.strip() in ("staged secrets", "unreachable commits"):
        return "text" if value.strip() == "none" else "error"
    return "text"


def write_svg(lines, path):
    cw, ch, pad = 8.4, 20.0, 16.0
    width = int(max(len(s) for s in lines) * cw + pad * 2)
    height = int(len(lines) * ch + pad * 2)

    def escape(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    colours = {"heading": "#79c0ff", "error": "#f85149", "text": "#c9d1d9"}
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="gitwhy doctor output">'
        % (width, height, width, height),
        '<rect width="%d" height="%d" rx="8" fill="#0d1117"/>' % (width, height),
        '<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        'font-size="14">',
    ]
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = pad + (i + 1) * ch - 6
        parts.append(
            '<text x="%.1f" y="%.1f" fill="%s" xml:space="preserve">%s</text>'
            % (pad, y, colours[_line_colour(line)], escape(line)))
    parts.append("</g></svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts) + "\n")
    return width, height


def write_png(lines, path):
    from PIL import Image, ImageDraw
    font = _font(15)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cw = probe.textlength("M", font=font)
    ch, pad = 20, 16
    width = int(max(len(s) for s in lines) * cw + pad * 2)
    height = len(lines) * ch + pad * 2
    colours = {
        "heading": GIF_COLOURS["heading"],
        "error": GIF_COLOURS["error"],
        "text": FOREGROUND,
    }
    img = Image.new("RGB", (width, height), BACKGROUND)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((pad, pad + i * ch), line, font=font,
               fill=colours[_line_colour(line)])
    img.save(path)
    return width, height


def main():
    os.makedirs(DOCS, exist_ok=True)
    root, repo = unhealthy_repo()
    try:
        output, code = run(repo, GITWHY + ["doctor"])
    finally:
        shutil.rmtree(root, ignore_errors=True)

    lines = output.split("\n")
    print(output)
    print("\ndoctor exit =", code)

    svg = os.path.join(DOCS, "doctor.svg")
    png = os.path.join(DOCS, "doctor.png")
    print("doctor.svg  %dx%d  %s" % (*write_svg(lines, svg), svg))
    print("doctor.png  %dx%d  %s" % (*write_png(lines, png), png))
    return 0


if __name__ == "__main__":
    sys.exit(main())
