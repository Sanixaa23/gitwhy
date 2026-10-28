"""Context + error text -> scenario id.

A pure function: no I/O, no network, no LLM. The whole testability of this
project comes from this file; do not add subprocess calls or file reads here.
"""
from __future__ import annotations

import os
from typing import List, Optional

from .context import Context

# The complete list of 12 scenarios. Scope stops here: do not add more.
SCENARIOS = [
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
]

# Scenarios that are actually matched and have a template written.
# When adding one: fixture -> rule -> template, in that order.
IMPLEMENTED = tuple(SCENARIOS)

# Scenario 9: directory names that should never be staged. Matched as a path
# component, so "src/node_modules/x" is caught too.
DEPENDENCY_DIRS = frozenset({
    "node_modules", "bower_components", "vendor", "venv", ".venv", "env",
    "__pycache__", "site-packages", "dist", "build", "target", ".next",
    ".nuxt", "out", "pods", ".gradle", ".dart_tool", ".terraform",
})

# Scenario 10: file names and extensions that carry secrets.
SECRET_NAMES = frozenset({
    ".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json",
    "serviceaccount.json", "service-account.json", "secrets.json",
    ".netrc", ".npmrc", ".pypirc", "terraform.tfvars",
})
SECRET_EXTENSIONS = (".pem", ".p12", ".pfx", ".key", ".keystore", ".jks", ".ppk")

# These exist in order to be committed, so they must not warn. `.env.example`
# is a template, not a secret. The fixture stages this file too, as a
# false-positive test.
SECRET_EXEMPT_SUFFIXES = (
    ".example", ".sample", ".template", ".dist", ".tpl", ".default",
)

# Verified by fixture test: git's first output line may not be the real error.
# In a merge conflict the first line is "Auto-merging a.txt"; CONFLICT comes
# further down. So we scan EVERY line instead of taking the first.
#
# CAREFUL: this list is a GATE. A line carrying none of these markers is
# dropped by error_lines() and match() never sees it. Markers must therefore
# be the loosest possible fragment, while scenario patterns stay narrow.
# This bit twice: the protected-branch rejection line is "! [remote rejected]",
# which matches neither "! [rejected]" nor "[rejected]" because "remote " sits
# in between. Hence the marker is just "rejected".
ERROR_MARKERS = (
    "CONFLICT", "error:", "fatal:", "rejected", "declined",
    "warning:", "remote:",
)

GIT_GLOBAL_FLAGS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace")


def error_lines(error_text: Optional[str]) -> List[str]:
    """Keep only the lines of the error text a decision can rest on."""
    if not error_text:
        return []
    return [
        line.strip()
        for line in error_text.splitlines()
        if any(marker in line for marker in ERROR_MARKERS)
    ]


def _in_text(error_text: Optional[str], *fragments: str) -> bool:
    """Does any decision line of the error text carry one of the fragments?"""
    lines = error_lines(error_text)
    return any(fragment in line for fragment in fragments for line in lines)


def _parts(path: str) -> List[str]:
    return [p for p in path.replace("\\", "/").split("/") if p]


def dependency_paths(ctx: Context) -> List[str]:
    """Dependency directories among the staged paths.

    Returns directories, not files: "node_modules" instead of 400 entries.
    The suggested command works on the directory as well.
    """
    found: List[str] = []
    for path in ctx.staged:
        parts = _parts(path)
        for i, part in enumerate(parts):
            if part.lower() in DEPENDENCY_DIRS:
                prefix = "/".join(parts[:i + 1])
                if prefix not in found:
                    found.append(prefix)
                break
    return found


def is_secret(path: str) -> bool:
    """Is this path a secret-bearing file? Templates like `.env.example` are not."""
    parts = _parts(path)
    if not parts:
        return False
    name = parts[-1].lower()
    if any(name.endswith(suffix) for suffix in SECRET_EXEMPT_SUFFIXES):
        return False
    if name in SECRET_NAMES:
        return True
    if name.startswith(".env."):          # .env.local, .env.production
        return True
    return any(name.endswith(ext) for ext in SECRET_EXTENSIONS)


def secret_paths(ctx: Context) -> List[str]:
    """Secret-bearing files among the staged paths."""
    return [p for p in ctx.staged if is_secret(p)]


def git_subcommand(command: Optional[str]) -> Optional[str]:
    """"git -c x=y push -u origin main" -> "push". None when unknown.

    Pure string handling; the command is NEVER executed.
    """
    if not command:
        return None
    parts = command.split()
    if not parts or os.path.basename(parts[0]).replace(".exe", "") != "git":
        return None
    i = 1
    while i < len(parts):
        part = parts[i]
        if part in GIT_GLOBAL_FLAGS:
            i += 2
            continue
        if part.startswith("-"):
            i += 1
            continue
        return part
    return None


def match(
    ctx: Context,
    error_text: Optional[str] = None,
    command: Optional[str] = None,
) -> Optional[str]:
    """Derive a scenario id from state, error text and the failed command.

    ORDERING RULE (verified by a fixture test, do not change):
    In the middle of a rebase conflict, `git status` reports
    `# branch.head (detached)` AND `rebase-merge` AT THE SAME TIME. Check
    detached HEAD first and you tell a user mid-rebase "you are in detached
    HEAD" and suggest entirely wrong commands.
    Correct order: in-progress operation -> conflict -> error text -> failed
    command -> state (secret -> dependency -> detached -> lost commit).
    """
    if not ctx.is_repo:
        return None

    # 1) Half-finished operations. The most urgent state, and it masks detached.
    if "rebase-merge" in ctx.in_progress or "rebase-apply" in ctx.in_progress:
        return "03_rebase_in_progress"
    if "CHERRY_PICK_HEAD" in ctx.in_progress or "REVERT_HEAD" in ctx.in_progress:
        return "04_cherry_pick_in_progress"

    # 2) Conflict. MERGE_HEAD also exists during a rebase, hence after step 1.
    if ctx.conflicted or "MERGE_HEAD" in ctx.in_progress:
        return "02_merge_conflict"

    # 3) The error text itself says which operation was attempted, so it comes
    #    before the detached check: if the user ran push, telling them they
    #    are detached does not answer their question.
    if _in_text(error_text, "No configured push destination"):
        return "05_no_remote"
    if _in_text(error_text, "has no upstream branch", "no upstream configured"):
        return "06_no_upstream"
    # 08 before 07: both carry "failed to push some refs". What separates them
    # is the remote's own refusal (`! [remote rejected]`) versus git's
    # fast-forward refusal (`! [rejected]`).
    if _in_text(
        error_text,
        "[remote rejected]",
        "pre-receive hook declined",
        "protected branch",
        "GH006",
    ):
        return "08_wrong_branch"
    # ctx.behind is NOT TRUSTWORTHY after a rejected push: git does not update
    # the remote-tracking ref, so `branch.ab` still reads +N -0. The real
    # behind count only appears after `git fetch`, and context.py cannot fetch
    # (read-only). Hence this decision comes from the text.
    if _in_text(error_text, "! [rejected]", "non-fast-forward", "fetch first"):
        return "07_push_rejected"
    if _in_text(error_text, "would be overwritten"):
        return "11_local_changes_block"

    # 3b) No error TEXT, but a failed COMMAND plus repository state.
    #
    # The shell wrapper leaves the error on screen, so it can record only the
    # command and the exit code. Without this block, scenarios 5, 6 and 11
    # never matched through the wrapper: the user saw "fatal: No configured
    # push destination." on screen while gitwhy said "no matching scenario".
    # Measured in a real repository.
    #
    # `command` is only ever passed for a FAILED command (capture.write is
    # called on failure only), so no exit code is needed here.
    sub = git_subcommand(command)
    if sub in ("push",):
        if not ctx.has_remote:
            return "05_no_remote"
        if ctx.upstream is None:
            return "06_no_upstream"
    if sub in ("checkout", "switch", "merge", "pull", "rebase", "restore", "stash"):
        if ctx.unstaged:
            return "11_local_changes_block"

    # 4) State-only situations, independent of any command.
    #    Secrets first: committing .env is the most expensive mistake to undo.
    #    This block comes AFTER the text block: if the user asked why a command
    #    failed, the answer should be about that command.
    if secret_paths(ctx):
        return "10_secret_staged"
    if dependency_paths(ctx):
        return "09_dependency_staged"
    if ctx.detached:
        return "01_detached_head"
    # Lost commits last: this rule reads the last 10 reflog entries and is the
    # noisiest one, able to find something in almost any repository. If any
    # other scenario matches, that one is reported instead.
    if ctx.lost:
        return "12_lost_commit"

    # There is DELIBERATELY no state-based form of scenario 8. The signal
    # "main has unpushed commits" cannot be told apart from the perfectly
    # normal state of someone working alone (see the neg_main_ahead fixture).
    # So scenario 8 is detected only by the remote's refusal.
    return None
