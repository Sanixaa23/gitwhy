"""Render the demo video's picture track from the captured take output.

    bash tools/video_capture.sh      # run the real commands, save the output
    python tools/video_render.py     # draw it, write docs/gitwhy-demo.mp4

This draws a terminal rather than recording one. The distinction that matters
is not how the pixels were made, it is whether the text is real: every
character this draws came out of `video_capture.sh` running the actual
command against the actual repository. Nothing is typed into a transcript by
hand, which is why the shot list's "do not fake a terminal" survives.

What this cannot do is speak. The narration in docs/CUE-SHEET.md still has to
be read by a person over the finished file, and the segment timings here are
taken from that cue sheet so the words land where they were written to land.

Font size is chosen per take, not once for the video. A take whose output is
45 lines has to fit 45 lines; a take whose output is two lines should not be
drawn in the same small type just for consistency. So each segment gets the
largest size that fits its own content, which also happens to put the biggest
type on the two segments that are the punchlines -- the accuracy matrix and
the safety suite.
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Rendering needs Pillow:\n\n    pip install Pillow\n")

try:
    import imageio_ffmpeg
except ImportError:
    raise SystemExit(
        "Writing the mp4 needs a bundled ffmpeg:\n\n"
        "    pip install imageio-ffmpeg\n")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAKES = os.path.join(ROOT, "docs", "takes")
OUT = os.path.join(ROOT, "docs", "gitwhy-demo.mp4")

WIDTH, HEIGHT = 1920, 1080
FPS = 30
MARGIN_X, MARGIN_Y = 44, 40
COLS = 96

# A terminal that reads on a projector: near-black rather than black, so the
# compressor has somewhere to put gradient, and no pure-white text.
BG = (18, 20, 24)
FG = (214, 218, 224)
DIM = (120, 128, 138)
RED = (232, 106, 96)
AMBER = (226, 176, 92)
GREEN = (134, 204, 132)
CYAN = (122, 194, 214)
BOLD_FG = (242, 245, 250)
PROMPT = (134, 204, 132)
CURSOR = (214, 218, 224)

FONT_CANDIDATES = (
    r"C:\Windows\Fonts\CascadiaMono.ttf",
    r"C:\Windows\Fonts\CascadiaCode.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)


def _font_path() -> str:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise SystemExit("No monospace font found. Tried:\n  " +
                     "\n  ".join(FONT_CANDIDATES))


FONT_PATH = _font_path()
_FONT_CACHE: Dict[int, ImageFont.FreeTypeFont] = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size)
    return _FONT_CACHE[size]


def cell(size: int) -> Tuple[float, int]:
    """Advance width and line height for a font size, measured not assumed."""
    f = font(size)
    advance = f.getlength("M")
    ascent, descent = f.getmetrics()
    return advance, int(round((ascent + descent) * 1.18))


def fit_size(rows: int, cols: int = COLS) -> int:
    """The largest size whose grid fits the frame. Binary search on measured cells."""
    usable_w = WIDTH - 2 * MARGIN_X
    usable_h = HEIGHT - 2 * MARGIN_Y
    lo, hi, best = 8, 96, 8
    while lo <= hi:
        mid = (lo + hi) // 2
        advance, line_h = cell(mid)
        if advance * cols <= usable_w and line_h * rows <= usable_h:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


# --- what each kind of line looks like ------------------------------------

_INLINE_CODE = re.compile(r"`([^`]+)`")


_KEYWORD = re.compile(
    r"\b(def|return|if|elif|else|for|in|not|and|or|is|None|True|False|"
    r"import|from|while|try|except|raise|with|as|continue|break|lambda)\b")


def classify_code(line: str) -> Tuple[Tuple[int, int, int], bool]:
    """Colouring for the architecture segment, which shows source not output.

    The terminal classifier cannot be reused here: it paints any four-space
    indent green, because in gitwhy's output an indented block is a command
    to copy. In Python an indent is just an indent, and everything would be
    green.
    """
    stripped = line.strip()
    if stripped.startswith("#"):
        return DIM, False
    if stripped.startswith(('"""', "'''")) or stripped.startswith('"'):
        return AMBER, False
    if stripped.startswith("def "):
        return CYAN, True
    return FG, False


def classify(line: str) -> Tuple[Tuple[int, int, int], bool]:
    """A colour and a bold flag for one line of terminal text.

    Deliberately pattern-based rather than a real ANSI parser: gitwhy prints
    plain text, so there are no escape codes to honour, and the point of the
    colour here is to make the structure legible on a 1080p frame to someone
    watching for twenty seconds.
    """
    stripped = line.strip()
    if not stripped:
        return FG, False
    if stripped.startswith("> WARNING") or stripped.startswith(">"):
        return AMBER, True
    if stripped.startswith("##") or stripped.startswith("# "):
        return CYAN, True
    if re.match(r"^(fatal|error|CONFLICT|FAILED|Could not apply)", stripped):
        return RED, True
    if stripped.startswith("hint:"):
        return DIM, False
    if line.startswith("    ") and stripped:
        # Indented block: a command the reader is meant to be able to copy.
        return GREEN, False
    if re.match(r"^- [\w .]+:", stripped) or re.match(r"^\w[\w .\-/]*\s+:", stripped):
        return FG, False
    if "passed" in stripped or re.search(r"\(100%\)|18/18", stripped):
        return GREEN, True
    if "MISSING" in stripped or re.search(r"\.env\b", stripped):
        return AMBER, False
    return FG, False


def draw_line(d: ImageDraw.ImageDraw, x: int, y: int, text: str, size: int,
              code: bool = False) -> None:
    """Draw one line, giving `inline code` its own colour inside the line."""
    colour, bold = (classify_code if code else classify)(text)
    f = font(size)
    advance, _ = cell(size)

    pieces: List[Tuple[str, Tuple[int, int, int]]] = []
    last = 0
    for m in _INLINE_CODE.finditer(text):
        if m.start() > last:
            pieces.append((text[last:m.start()], colour))
        pieces.append((m.group(1), BOLD_FG if colour is FG else colour))
        last = m.end()
    if last < len(text):
        pieces.append((text[last:], colour))
    if not pieces:
        pieces = [(text, colour)]

    col = 0
    for piece, piece_colour in pieces:
        for ch in piece:
            if ch != " ":
                d.text((x + col * advance, y), ch, font=f, fill=piece_colour)
                if bold:
                    d.text((x + col * advance + 0.6, y), ch, font=f, fill=piece_colour)
            col += 1


def origin(lines_count: int, size: int, content_cols: int = COLS) -> Tuple[int, int]:
    """Top-left of the text block, centred.

    A take that needs many rows is limited by height, not width, so its 96
    columns use only about half the frame. Left-aligned that reads as a
    mistake, with the picture weighted into one corner. Centring the whole
    grid -- as a terminal window sits centred on a desktop -- costs nothing
    and looks deliberate, which it now is.
    """
    advance, line_h = cell(size)
    block_w = advance * content_cols
    block_h = line_h * lines_count
    x = max(MARGIN_X, int((WIDTH - block_w) / 2))
    y = max(MARGIN_Y, int((HEIGHT - block_h) / 2))
    return x, y


def frame(lines: Sequence[str], size: int, cursor_at: Optional[int] = None,
          cursor_col: int = 0, rows: int = 0, cols: int = COLS,
          code: bool = False) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    advance, line_h = cell(size)
    # Lay the block out for the take's full height and width from the first
    # frame, so the text neither drifts upward as lines arrive nor shifts
    # sideways between takes.
    ox, oy = origin(rows or len(lines), size, cols)
    for i, line in enumerate(lines):
        y = oy + i * line_h
        if y + line_h > HEIGHT:
            break
        draw_line(d, ox, y, line, size, code=code)
    if cursor_at is not None:
        y = oy + cursor_at * line_h
        x = ox + cursor_col * advance
        if y + line_h <= HEIGHT:
            d.rectangle([x, y + 2, x + advance * 0.85, y + line_h - 4],
                        fill=CURSOR)
    return img


# --- a take is a list of steps, each with a duration ----------------------

class Take:
    """One segment: a screen that builds up, then holds."""

    def __init__(self, name: str, seconds: float, code: bool = False):
        self.name = name
        self.seconds = seconds
        self.code = code
        self.steps: List[Tuple[str, object, float]] = []
        self._rows = 0
        self._cols = 0

    def type(self, text: str, seconds: float = None) -> "Take":
        line = "$ " + text
        self.steps.append(("type", line, seconds or 0.045 * len(text)))
        self._rows += 1
        self._cols = max(self._cols, len(line))
        return self

    def output(self, lines: Sequence[str], seconds: float = 0.35) -> "Take":
        self.steps.append(("output", list(lines), seconds))
        self._rows += len(lines)
        for line in lines:
            self._cols = max(self._cols, len(line))
        return self

    def pause(self, seconds: float) -> "Take":
        self.steps.append(("pause", None, seconds))
        return self

    def blank(self, n: int = 1) -> "Take":
        self.steps.append(("output", [""] * n, 0.0))
        self._rows += n
        return self

    def rows(self) -> int:
        # +1 for the trailing prompt that sits under the last line.
        return self._rows + 1

    def cols(self) -> int:
        return max(1, self._cols)


def read_take(name: str) -> List[str]:
    path = os.path.join(TAKES, name)
    if not os.path.exists(path):
        raise SystemExit(
            "Missing %s.\nRun: bash tools/video_capture.sh" % path)
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").rstrip("\n").split("\n")


def source_lines(relpath: str, first: int, last: int) -> List[str]:
    """A real slice of a real source file, for the architecture segment.

    Read from the repository at render time rather than pasted in here, so
    the frames cannot drift away from the code they claim to show. If the
    line numbers stop pointing at the right function, the fix is to move
    them, not to edit a copy of the source kept in this script.
    """
    path = os.path.join(ROOT, relpath.replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        body = f.read().replace("\r\n", "\n").split("\n")
    chunk = body[first - 1:last]
    # Drop a trailing blank run: it only pushes the font size down.
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return [line.rstrip() for line in chunk]


def split_at_gitwhy(lines: Sequence[str]) -> Tuple[List[str], List[str]]:
    """Git's own output, then gitwhy's, so the pause between them can be real."""
    for i, line in enumerate(lines):
        if line.startswith("## "):
            return list(lines[:i]), list(lines[i:])
    return list(lines), []


def render(take: Take, writer, size: int) -> int:
    """Play one take into the writer. Returns the frames written."""
    screen: List[str] = []
    written = 0

    rows, cols = take.rows(), take.cols()

    def emit(n: int, cursor_at=None, cursor_col=0):
        nonlocal written
        img = frame(screen, size, cursor_at, cursor_col, rows=rows,
                    cols=cols, code=take.code)
        raw = img.tobytes()
        for _ in range(max(1, n)):
            writer.send(raw)
        written += max(1, n)

    spent = 0.0
    for kind, payload, seconds in take.steps:
        if kind == "type":
            text = str(payload)
            screen.append("")
            per_char = seconds / max(1, len(text))
            for i in range(1, len(text) + 1):
                screen[-1] = text[:i]
                emit(max(1, int(round(per_char * FPS))),
                     cursor_at=len(screen) - 1, cursor_col=i)
            spent += seconds
        elif kind == "output":
            for line in payload:          # type: ignore[union-attr]
                screen.append(line)
            emit(max(1, int(round(seconds * FPS))))
            spent += seconds
        elif kind == "pause":
            emit(int(round(seconds * FPS)),
                 cursor_at=len(screen), cursor_col=0)
            spent += seconds

    hold = take.seconds - spent
    if hold > 0:
        emit(int(round(hold * FPS)), cursor_at=len(screen), cursor_col=0)
    elif hold < -0.5:
        print("  ! %s overruns its slot by %.1fs" % (take.name, -hold))
    return written


def build_takes() -> List[Take]:
    """The seven segments, with the cue sheet's timings."""
    takes: List[Take] = []

    # 1 -- 0:00-0:20. The git error, a beat, then the answer with no typing.
    git_part, why_part = split_at_gitwhy(read_take("01_push.txt"))
    t = Take("1 first push", 20.0)
    t.type("cd ~/gitwhy-video/01-first-push", 1.4)
    t.type("git push", 0.9)
    t.output(git_part, 0.5)
    t.pause(1.6)                      # the beat the shot list asks for
    t.output(why_part, 0.9)
    takes.append(t)

    # 2 -- 0:20-0:42. Same shape: the wrapper answers a failed rebase.
    git_part, why_part = split_at_gitwhy(read_take("02_rebase.txt"))
    t = Take("2 rebase conflict", 22.0)
    t.type("cd ~/gitwhy-video/02-rebase", 1.3)
    t.type("git rebase main", 1.1)
    t.output(git_part, 0.5)
    t.pause(1.4)
    t.output(why_part, 0.9)
    takes.append(t)

    # 3 -- 0:42-1:00. `git add .` succeeds, so this one is asked, not offered.
    t = Take("3 staged secret", 18.0)
    t.type("cd ~/gitwhy-video/03-secret", 1.3)
    t.type("git add .", 0.8)
    t.blank(1)
    t.type("gitwhy", 0.7)
    t.output(read_take("03_gitwhy.txt"), 0.9)
    takes.append(t)

    # 4 -- 1:00-1:25. The architecture, shown as the two files that are the
    # argument: one call to git, then a pure function over its result. Code
    # rather than a diagram, because the claim is about the code.
    t = Take("4a the collector", 13.0, code=True)
    t.type("sed -n '93,118p' src/gitwhy/context.py", 1.6)
    t.output(source_lines("src/gitwhy/context.py", 93, 118), 1.0)
    takes.append(t)

    t = Take("4b the pure function", 12.0, code=True)
    t.type("sed -n '174,190p' src/gitwhy/rules.py", 1.6)
    t.output(source_lines("src/gitwhy/rules.py", 174, 190), 1.0)
    takes.append(t)

    # 5 -- 1:25-1:50. The matrix. Big type: this is a punchline.
    t = Take("5 accuracy matrix", 25.0)
    t.type("python tests/test_rules.py", 1.5)
    t.output(read_take("05_matrix.txt"), 1.2)
    takes.append(t)

    # 6 -- 1:50-2:08. Two lines, so they get the largest type in the video.
    t = Take("6 safety suite", 18.0)
    t.type("python -m pytest tests/test_safety.py tests/test_ai.py -q", 2.4)
    t.output(read_take("06_safety.txt"), 1.0)
    takes.append(t)

    # 7 -- 2:08-2:20. Install, then doctor in repo 3 (fixture email on screen).
    # 7 -- 2:08-2:20. The install is captured from a real run against the
    # public repository, not typed in here. An earlier draft of this take
    # had invented pipx output, which is exactly the thing the shot list
    # forbids, in the project whose whole argument is that it does not
    # make things up.
    t = Take("7 close", 12.0)
    t.type("pip install git+https://github.com/Sanixaa23/gitwhy", 2.0)
    t.output(read_take("07_install.txt"), 0.8)
    t.blank(1)
    t.type("gitwhy doctor", 0.9)
    t.output(read_take("07_doctor.txt"), 0.9)
    takes.append(t)

    return takes


def card(lines: Sequence[Tuple[str, Tuple[int, int, int], int]],
         seconds: float, writer) -> int:
    """A title or end card: centred text, no terminal chrome.

    The video has no narration baked in, so a viewer who opens the file
    cold needs the name of the thing and where to get it on screen. That is
    titling, not a faked terminal: nothing here claims to be command output.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    heights = [cell(size)[1] for _, _, size in lines]
    total = sum(heights) + 18 * (len(lines) - 1)
    y = (HEIGHT - total) / 2
    for (text, colour, size), line_h in zip(lines, heights):
        f = font(size)
        w = f.getlength(text)
        d.text(((WIDTH - w) / 2, y), text, font=f, fill=colour)
        y += line_h + 18
    raw = img.tobytes()
    n = int(round(seconds * FPS))
    for _ in range(n):
        writer.send(raw)
    return n


def main(argv: Sequence[str] = ()) -> int:
    only = argv[0] if argv else None
    takes = build_takes()
    if only:
        takes = [t for t in takes if t.name.startswith(only)]
        if not takes:
            raise SystemExit("No take starts with %r" % only)

    total = sum(t.seconds for t in takes)
    print("rendering %d takes, %.0fs, %dx%d @%dfps" %
          (len(takes), total, WIDTH, HEIGHT, FPS))
    print("font: %s" % FONT_PATH)

    writer = imageio_ffmpeg.write_frames(
        OUT, (WIDTH, HEIGHT), fps=FPS, codec="libx264", quality=7,
        macro_block_size=1, ffmpeg_log_level="error",
        output_params=["-pix_fmt", "yuv420p"])
    writer.send(None)

    frames = 0
    try:
        if not only:
            frames += card([
                ("gitwhy", BOLD_FG, 96),
                ("explains a git error by reading your repository,", FG, 34),
                ("not by translating the message", FG, 34),
                ("", FG, 20),
                ("twelve scenarios  ·  18/18 on the accuracy matrix"
                 "  ·  no model in the decision", DIM, 26),
            ], 4.0, writer)

        for take in takes:
            size = fit_size(take.rows())
            advance, line_h = cell(size)
            print("  %-20s %4.1fs  %2d rows  font %2dpx  grid %dx%d" % (
                take.name, take.seconds, take.rows(), size,
                int((WIDTH - 2 * MARGIN_X) / advance),
                int((HEIGHT - 2 * MARGIN_Y) / line_h)))
            frames += render(take, writer, size)

        if not only:
            frames += card([
                ("github.com/Sanixaa23/gitwhy", BOLD_FG, 60),
                ("", FG, 16),
                ("MIT  ·  no dependencies  ·  works offline"
                 "  ·  no account", DIM, 28),
            ], 4.0, writer)
    finally:
        writer.close()

    print("\n%s" % OUT)
    print("%d frames, %.1fs, %.1f MB" % (
        frames, frames / FPS, os.path.getsize(OUT) / 1e6))
    print("\nPicture only. Read docs/CUE-SHEET.md over it for the narration.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
