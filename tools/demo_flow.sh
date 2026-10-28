#!/usr/bin/env bash
# The flow for taking a real terminal recording with asciinema.
# There is no asciinema on Windows; `python tools/demo.py` produces the same
# flow there.
#
# Usage (Linux / macOS / WSL):
#   asciinema rec docs/demo.cast --cols 96 --rows 36 --overwrite \
#       --idle-time-limit 2 -c "bash tools/demo_flow.sh"
#   agg --font-size 15 --theme github-dark docs/demo.cast docs/demo.gif
#
# The repository is built in a temporary directory; your own repo is untouched.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src"
export PYTHONIOENCODING=utf-8
export GIT_AUTHOR_NAME=student GIT_AUTHOR_EMAIL=student@school.edu
export GIT_COMMITTER_NAME=student GIT_COMMITTER_EMAIL=student@school.edu
export GIT_EDITOR=true
export LC_ALL=C
# Keep the user's global git config out of the recording (core.autocrlf
# warnings, for instance). Point at a file that does not exist.
export GIT_CONFIG_GLOBAL="${TMPDIR:-/tmp}/gitwhy_demo_no_config"
export GIT_CONFIG_SYSTEM="$GIT_CONFIG_GLOBAL"

PROMPT='student@hackathon ~/project (feature) $ '
gitwhy() { python -m gitwhy.cli "$@"; }

# Types the command out character by character, then runs it.
type_out() {
  printf '%s' "$PROMPT"
  local text="$1"
  for ((i = 0; i < ${#text}; i++)); do
    printf '%s' "${text:i:1}"
    sleep 0.045
  done
  printf '\n'
  sleep 0.5
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK" || exit 1

# --- setup, not part of the recording: a repo heading into a rebase conflict
git init -q -b main project
cd project || exit 1
printf 'title\n' > a.txt
git add a.txt && git commit -qm "first commit"
printf 'title\nwritten on main\n' > a.txt
git commit -qam "keep going on main"
git checkout -q -b feature HEAD~1
printf 'title\nwritten on the feature branch\n' > a.txt
git commit -qam "add feature"
clear

# --- the recording ---------------------------------------------------------
type_out 'git rebase main'
git rebase main
sleep 3.4

type_out 'gitwhy'
gitwhy
sleep 9.5

type_out 'nano a.txt   # resolve the conflict'
printf 'title\nwritten on main\nwritten on the feature branch\n' > a.txt
sleep 1.4

type_out 'git add a.txt'
git add a.txt
sleep 0.8

type_out 'git rebase --continue'
git rebase --continue
sleep 3.0

type_out 'gitwhy doctor'
gitwhy doctor
sleep 4.5

printf '%s' "$PROMPT"
sleep 2
