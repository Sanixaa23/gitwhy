"""Builds broken git repositories programmatically.

For every scenario: a real repository, a real broken state, and the REAL error
text of the command that produced it. Measured scenario accuracy comes from
here — we do not describe a scenario, we build it.

Everything lives under tempfile; `cleanup()` removes it all.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

# Keep the user's global git config out of the tests: point at a file that
# does not exist. os.devnull ("nul") is not accepted by git on Windows.
_NO_CONFIG = os.path.join(tempfile.gettempdir(), "gitwhy_no_config")

ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="gitwhy test",
    GIT_AUTHOR_EMAIL="test@gitwhy.invalid",
    GIT_COMMITTER_NAME="gitwhy test",
    GIT_COMMITTER_EMAIL="test@gitwhy.invalid",
    GIT_CONFIG_GLOBAL=_NO_CONFIG,
    GIT_CONFIG_SYSTEM=_NO_CONFIG,
    LC_ALL="C",
    GIT_TERMINAL_PROMPT="0",
)

_ROOTS: List[str] = []


@dataclass
class Fixture:
    scenario_id: str
    repo: str
    error_text: str     # the command's real output (stderr + stdout)
    exit_code: int


def g(repo: str, *args: str) -> Tuple[str, str, int]:
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=ENV)
    return (
        p.stdout.decode("utf-8", "replace"),
        p.stderr.decode("utf-8", "replace"),
        p.returncode,
    )


def _write(repo: str, name: str, text: str) -> None:
    path = os.path.join(repo, name)
    if os.path.dirname(name):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _new_repo() -> str:
    root = tempfile.mkdtemp(prefix="gitwhy_fix_")
    _ROOTS.append(root)
    repo = os.path.join(root, "repo")
    os.makedirs(repo)
    g(repo, "init", "-q", "-b", "main")
    g(repo, "config", "commit.gpgsign", "false")
    _write(repo, "a.txt", "line1\n")
    g(repo, "add", "a.txt")
    g(repo, "commit", "-qm", "first commit")
    _write(repo, "a.txt", "line1\nline2\n")
    g(repo, "commit", "-qam", "second commit")
    return repo


def _combine(out: str, err: str) -> str:
    """git writes the CONFLICT line to stdout; return both together."""
    return "\n".join(x for x in (err.strip(), out.strip()) if x)


def _add_remote(repo: str) -> str:
    """Attach a real bare remote; return the bare repository's path."""
    parent = os.path.dirname(repo)
    # -b main is REQUIRED: if the bare repo's HEAD stays on master the clone
    # comes out empty and fixture 07 never produces a rejected push (this
    # actually happened once).
    g(parent, "init", "--bare", "-q", "-b", "main", "remote.git")
    bare = os.path.join(parent, "remote.git")
    g(repo, "remote", "add", "origin", bare)
    return bare


# --- scenario builders -----------------------------------------------------

def _build_detached() -> Fixture:
    repo = _new_repo()
    sha, _, _ = g(repo, "rev-parse", "HEAD~1")
    out, err, rc = g(repo, "checkout", "-q", sha.strip())
    # Here the command succeeds; the user notices the problem afterwards.
    return Fixture("01_detached_head", repo, _combine(out, err), rc)


def _build_merge_conflict() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "a.txt", "line1\nFEATURE\n")
    g(repo, "commit", "-qam", "feature side")
    g(repo, "checkout", "-q", "main")
    _write(repo, "a.txt", "line1\nMAIN\n")
    g(repo, "commit", "-qam", "main side")
    out, err, rc = g(repo, "merge", "feature")
    return Fixture("02_merge_conflict", repo, _combine(out, err), rc)


def _build_rebase_in_progress() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature", "HEAD~1")
    _write(repo, "a.txt", "line1\nFEATURE\n")
    g(repo, "commit", "-qam", "feature side")
    out, err, rc = g(repo, "rebase", "main")
    return Fixture("03_rebase_in_progress", repo, _combine(out, err), rc)


def _build_cherry_pick_in_progress() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "a.txt", "line1\nFEATURE\n")
    g(repo, "commit", "-qam", "feature side")
    sha, _, _ = g(repo, "rev-parse", "HEAD")
    g(repo, "checkout", "-q", "main")
    _write(repo, "a.txt", "line1\nMAIN\n")
    g(repo, "commit", "-qam", "main side")
    out, err, rc = g(repo, "cherry-pick", sha.strip())
    return Fixture("04_cherry_pick_in_progress", repo, _combine(out, err), rc)


def _build_revert_in_progress() -> Fixture:
    repo = _new_repo()
    _write(repo, "a.txt", "line1\nSOMETHING ELSE\n")
    g(repo, "commit", "-qam", "third commit")
    out, err, rc = g(repo, "revert", "HEAD~1")
    return Fixture("04_cherry_pick_in_progress", repo, _combine(out, err), rc)


def _build_no_remote() -> Fixture:
    repo = _new_repo()
    out, err, rc = g(repo, "push")
    return Fixture("05_no_remote", repo, _combine(out, err), rc)


def _build_no_upstream() -> Fixture:
    repo = _new_repo()
    _add_remote(repo)
    out, err, rc = g(repo, "push")
    return Fixture("06_no_upstream", repo, _combine(out, err), rc)


def _build_push_rejected() -> Fixture:
    repo = _new_repo()
    bare = _add_remote(repo)
    g(repo, "push", "-q", "-u", "origin", "main")
    # Someone else commits to the same branch and pushes.
    parent = os.path.dirname(repo)
    g(parent, "clone", "-q", bare, "clone")
    clone = os.path.join(parent, "clone")
    _write(clone, "a.txt", "someone else's change\n")
    g(clone, "commit", "-qam", "their commit")
    g(clone, "push", "-q")
    # Our repo, unaware, changes the same file and tries to push.
    _write(repo, "a.txt", "my change\n")
    g(repo, "commit", "-qam", "my commit")
    out, err, rc = g(repo, "push")
    return Fixture("07_push_rejected", repo, _combine(out, err), rc)


def _build_protected_branch() -> Fixture:
    """Scenario 8: pushing straight to main, the remote refuses.

    A pre-receive hook is placed in the bare repository, producing the same
    message a protected branch on GitHub does.
    """
    repo = _new_repo()
    bare = _add_remote(repo)
    g(repo, "push", "-q", "-u", "origin", "main")
    hook = os.path.join(bare, "hooks", "pre-receive")
    with open(hook, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "#!/bin/sh\n"
            'echo "main is a protected branch; open a feature branch and a PR" >&2\n'
            "exit 1\n"
        )
    os.chmod(hook, 0o755)
    _write(repo, "b.txt", "new feature\n")
    g(repo, "add", "b.txt")
    g(repo, "commit", "-qm", "feature went straight to main")
    out, err, rc = g(repo, "push")
    return Fixture("08_wrong_branch", repo, _combine(out, err), rc)


def _build_dependency_staged() -> Fixture:
    repo = _new_repo()
    _write(repo, "node_modules/package/index.js", "module.exports = 1\n")
    _write(repo, "node_modules/package/package.json", '{"name":"package"}\n')
    out, err, rc = g(repo, "add", "-A")
    # No failing command: the user comes here after reading `git status`.
    return Fixture("09_dependency_staged", repo, _combine(out, err), rc)


def _build_secret_staged() -> Fixture:
    repo = _new_repo()
    _write(repo, ".env", "API_KEY=fake-test-value\n")
    _write(repo, ".env.example", "API_KEY=\n")  # must be committable, no warning
    out, err, rc = g(repo, "add", "-A")
    return Fixture("10_secret_staged", repo, _combine(out, err), rc)


def _build_checkout_blocked() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "a.txt", "line1\nFEATURE\n")
    g(repo, "commit", "-qam", "feature side")
    g(repo, "checkout", "-q", "main")
    _write(repo, "a.txt", "line1\nuncommitted work\n")   # never committed
    out, err, rc = g(repo, "checkout", "feature")
    return Fixture("11_local_changes_block", repo, _combine(out, err), rc)


def _build_merge_blocked() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "a.txt", "line1\nFEATURE\n")
    g(repo, "commit", "-qam", "feature side")
    g(repo, "checkout", "-q", "main")
    _write(repo, "a.txt", "line1\nuncommitted work\n")
    out, err, rc = g(repo, "merge", "feature")
    return Fixture("11_local_changes_block", repo, _combine(out, err), rc)


def _build_lost_commit_reset() -> Fixture:
    repo = _new_repo()
    _write(repo, "c.txt", "hours of work\n")
    g(repo, "add", "c.txt")
    g(repo, "commit", "-qm", "hours of work")
    out, err, rc = g(repo, "reset", "--hard", "HEAD~1")
    return Fixture("12_lost_commit", repo, _combine(out, err), rc)


def _build_lost_commit_branch_deleted() -> Fixture:
    repo = _new_repo()
    g(repo, "checkout", "-q", "-b", "feature")
    _write(repo, "c.txt", "work that went with the branch\n")
    g(repo, "add", "c.txt")
    g(repo, "commit", "-qm", "work that went with the branch")
    g(repo, "checkout", "-q", "main")
    out, err, rc = g(repo, "branch", "-D", "feature")
    return Fixture("12_lost_commit", repo, _combine(out, err), rc)


# --- negative controls: these must match no scenario ----------------------

def _build_clean() -> Fixture:
    """A healthy repository. A match here is a false positive."""
    repo = _new_repo()
    return Fixture("(no match)", repo, "", 0)


def _build_after_amend() -> Fixture:
    """`git commit --amend` leaves the old commit unreachable, but that is a
    deliberate operation, not a loss. Scenario 12 must not count it."""
    repo = _new_repo()
    _write(repo, "a.txt", "line1\nline2\nline3\n")
    out, err, rc = g(repo, "commit", "-qam", "second commit, fixed", "--amend")
    return Fixture("(no match)", repo, _combine(out, err), rc)


def _build_main_ahead() -> Fixture:
    """One unpushed commit on main. The perfectly normal state of someone
    working alone: scenario 8 must not call this a wrong branch."""
    repo = _new_repo()
    _add_remote(repo)
    g(repo, "push", "-q", "-u", "origin", "main")
    _write(repo, "d.txt", "normal work\n")
    g(repo, "add", "d.txt")
    g(repo, "commit", "-qm", "normal work")
    return Fixture("(no match)", repo, "", 0)


# Variant key -> builder. A scenario may have several fixtures: every variant
# returning the same scenario id lands on the same row of the matrix.
BUILDERS: Dict[str, Callable[[], Fixture]] = {
    "01_detached_head": _build_detached,
    "02_merge_conflict": _build_merge_conflict,
    "03_rebase_in_progress": _build_rebase_in_progress,
    "04_cherry_pick": _build_cherry_pick_in_progress,
    "04_revert": _build_revert_in_progress,
    "05_no_remote": _build_no_remote,
    "06_no_upstream": _build_no_upstream,
    "07_push_rejected": _build_push_rejected,
    "08_protected_branch": _build_protected_branch,
    "09_dependency_staged": _build_dependency_staged,
    "10_secret_staged": _build_secret_staged,
    "11_checkout_blocked": _build_checkout_blocked,
    "11_merge_blocked": _build_merge_blocked,
    "12_reset_hard": _build_lost_commit_reset,
    "12_branch_deleted": _build_lost_commit_branch_deleted,
    "neg_clean": _build_clean,
    "neg_amend": _build_after_amend,
    "neg_main_ahead": _build_main_ahead,
}

VARIANTS = tuple(BUILDERS)

# Matrix rows: each scenario id once, in variant order.
SCENARIOS = (
    "01_detached_head",
    "02_merge_conflict",
    "03_rebase_in_progress",
    "04_cherry_pick_in_progress",
    "05_no_remote",
    "06_no_upstream",
    "07_push_rejected",
    "08_wrong_branch",
    "09_dependency_staged",
    "10_secret_staged",
    "11_local_changes_block",
    "12_lost_commit",
    "(no match)",
)


def build(variant: str) -> Fixture:
    """Build the variant in a real repository.

    A scenario id is accepted too: its first variant gets built.
    """
    if variant in BUILDERS:
        return BUILDERS[variant]()
    for name, func in BUILDERS.items():
        if name.split("_")[0] == variant.split("_")[0]:
            return func()
    raise KeyError("no such fixture: " + variant)


def all_fixtures() -> List[Fixture]:
    return [BUILDERS[v]() for v in VARIANTS]


def cleanup() -> None:
    """Remove every temporary repository built so far."""
    while _ROOTS:
        shutil.rmtree(_ROOTS.pop(), ignore_errors=True)
