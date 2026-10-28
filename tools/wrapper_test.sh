#!/usr/bin/env bash
# End-to-end test of the `gitwhy shell-init` wrapper.
#
# Unit tests cannot cover the wrapper: there is no shell there. Here the
# wrapper is genuinely installed, real git commands are made to fail, and we
# check that gitwhy finds the right scenario.
#
# Usage:
#   bash tools/wrapper_test.sh              # default mode
#   GITWHY_TEE=1 bash tools/wrapper_test.sh
#   zsh tools/wrapper_test.sh               # same tests under zsh
#
# gitwhy must be on PATH (`pip install -e .`).
set -u

export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@e
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@e
export GIT_CONFIG_GLOBAL="${TMPDIR:-/tmp}/gitwhy_no_config"
export GIT_CONFIG_SYSTEM="$GIT_CONFIG_GLOBAL"
export LC_ALL=C GIT_TERMINAL_PROMPT=0

PASSED=0; FAILED=0
ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT
export GITWHY_CACHE="$ROOT/cache"

if ! command -v gitwhy >/dev/null 2>&1; then
  echo "SKIPPED: gitwhy is not on PATH. Run: pip install -e ."
  exit 0
fi

# The same script runs under bash and zsh; the wrapper is generated for
# whichever is in use. The only difference is how the pipeline's exit code is
# read: ${pipestatus[1]} in zsh.
if [ -n "${ZSH_VERSION:-}" ]; then
  SHELL_NAME=zsh
else
  SHELL_NAME=bash
fi
eval "$(gitwhy shell-init "$SHELL_NAME")"
# `type -t` is bash-only; `typeset -f` works in both.
if ! typeset -f git >/dev/null 2>&1; then
  echo "FAILED: could not install the wrapper for $SHELL_NAME"
  exit 1
fi

# One case: name, expected substring, repo setup, failing command.
check() {
  local name="$1" expected="$2"
  local d="$ROOT/$name"; mkdir -p "$d"; cd "$d" || return 1
  "setup_$name" >/dev/null 2>&1
  local output; output="$("run_$name" 2>&1)"
  local code=$?
  if printf '%s' "$output" | grep -qF "$expected"; then
    echo "PASS   $name  (exit=$code)  -> $expected"
    PASSED=$((PASSED + 1))
  else
    echo "FAIL   $name  (exit=$code)  '$expected' not found"
    printf '%s\n' "$output" | sed -n '1,12p' | sed 's/^/       | /'
    FAILED=$((FAILED + 1))
  fi
}

base_repo() {
  command git init -q -b main
  printf 'a\n' > a.txt
  command git add a.txt
  command git commit -qm first
}

add_remote() {
  command git init --bare -q -b main ../remote.git
  command git remote add origin ../remote.git
}

# 05 - no remote at all
setup_05() { base_repo; }
run_05() { git push; }

# 06 - remote exists, no upstream
setup_06() { base_repo; add_remote; }
run_06() { git push; }

# 07 - push rejected
setup_07() {
  base_repo; add_remote
  command git push -q -u origin main
  command git clone -q ../remote.git ../clone07
  ( cd ../clone07 && printf 'theirs\n' > a.txt \
    && command git commit -qam theirs && command git push -q )
  printf 'mine\n' > a.txt
  command git commit -qam mine
}
run_07() { git push; }

# 03 - mid-rebase (found from state, no text needed)
setup_03() {
  base_repo
  printf 'a\nmain\n' > a.txt
  command git commit -qam main-side
  command git checkout -q -b feature HEAD~1
  printf 'a\nfeature\n' > a.txt
  command git commit -qam feature-side
}
run_03() { git rebase main; }

# 11 - uncommitted change blocks the checkout
setup_11() {
  base_repo
  command git checkout -q -b feature
  printf 'a\nfeature\n' > a.txt
  command git commit -qam feature-side
  command git checkout -q main
  printf 'a\nuncommitted\n' > a.txt
}
run_11() { git checkout feature; }

# a successful command: the wrapper must stay out of the way
setup_ok() { base_repo; }
run_ok() { git status --short --branch; }

echo "=== shell=$SHELL_NAME  GITWHY_TEE=${GITWHY_TEE:-0} ==="
check 05 "git remote add origin"
check 06 "push.autoSetupRemote"
if [ "${GITWHY_TEE:-0}" = "1" ]; then
  check 07 "git pull --rebase"
else
  echo "SKIP   07  (needs the error text; run with GITWHY_TEE=1)"
fi
check 03 "git rebase --continue"
check 11 "git stash push"
check ok "## main"

echo
echo "passed $PASSED, failed $FAILED"
[ "$FAILED" -eq 0 ]
