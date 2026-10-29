#!/usr/bin/env bash
# Capture the real output of every take, for tools/video_render.py to draw.
#
# Nothing here is typed by hand into a transcript: each take runs the actual
# command against the actual repository, and the renderer only draws what
# landed in these files. That is what keeps "do not fake a terminal" true
# even though the final video is rendered rather than screen-captured.
#
#   bash tools/video_capture.sh
#
# Writes to docs/takes/. Run tools/video_setup.py --reset first; this script
# does it for you, because every take consumes the state it demonstrates.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/docs/takes"
VIDEO_REPOS="$HOME/gitwhy-video"

export PYTHONIOENCODING=utf-8   # capture the real UTF-8, not a codepage

mkdir -p "$OUT"
rm -f "$OUT"/*.txt

echo "resetting the demo repositories"
python "$ROOT/tools/video_setup.py" --reset >/dev/null 2>&1

# The wrapper is what makes takes 1 and 2 answer without anyone typing.
eval "$(gitwhy shell-init bash)"

echo "take 1: a first push with no remote"
cd "$VIDEO_REPOS/01-first-push"
git push > "$OUT/01_push.txt" 2>&1

echo "take 2: a rebase that stops on a conflict"
cd "$VIDEO_REPOS/02-rebase"
git rebase main > "$OUT/02_rebase.txt" 2>&1

echo "take 3: a staged .env"
cd "$VIDEO_REPOS/03-secret"
git add . > "$OUT/03_add.txt" 2>&1
gitwhy > "$OUT/03_gitwhy.txt" 2>&1

echo "take 7: doctor, in repo 3 so the email on screen is the fixture's"
gitwhy doctor > "$OUT/07_doctor.txt" 2>&1

echo "take 5: the confusion matrix"
cd "$ROOT"
python tests/test_rules.py > "$OUT/05_matrix.txt" 2>&1

echo "take 6: the safety tests"
python -m pytest tests/test_safety.py tests/test_ai.py -q > "$OUT/06_safety.txt" 2>&1

# Take 7's install line, run for real against the public repository rather
# than typed into a transcript. It also demonstrates the dependency claim:
# the venv ends up holding gitwhy and pip, and nothing else.
echo "take 7: a real install from the public repo"
TMP="$(mktemp -d)"
python -m venv "$TMP/venv" >/dev/null 2>&1
"$TMP/venv/Scripts/python.exe" -m pip install --disable-pip-version-check   "git+https://github.com/Sanixaa23/gitwhy" 2>&1 | tail -3 > "$OUT/07_install.txt"
rm -rf "$TMP"

echo
echo "captured:"
for f in "$OUT"/*.txt; do
  printf '  %-22s %3s lines  %3s cols\n' \
    "$(basename "$f")" \
    "$(wc -l < "$f")" \
    "$(awk '{ if (length > m) m = length } END { print m+0 }' "$f")"
done

echo
echo "leaving the repositories reset, ready to record or re-capture"
python "$ROOT/tools/video_setup.py" --reset >/dev/null 2>&1

