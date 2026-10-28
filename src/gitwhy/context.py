"""Read-only git queries collected into a single Context object.

This module NEVER modifies the repository. Every command added here must be
read-only: if a command could change the repo, it does not belong in this file.
`tests/test_safety.py` enforces that by scanning this source.

The primary signal is repository state, not error text. Git changes its error
messages between versions, but the --porcelain=v2 output format is stable.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

# Paths inside .git whose presence means an operation was left half-finished.
IN_PROGRESS_PATHS = (
    "MERGE_HEAD",
    "rebase-merge",
    "rebase-apply",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
)


def _env() -> dict:
    """LC_ALL=C keeps OUR queries' output language fixed. It does not affect
    the error the user saw; we did not produce that one.
    GIT_OPTIONAL_LOCKS=0 removes even the chance of writing to the index.
    """
    return dict(
        os.environ,
        LC_ALL="C",
        GIT_OPTIONAL_LOCKS="0",
        GIT_PAGER="cat",
        GIT_TERMINAL_PROMPT="0",
    )


def _git(repo: str, *args: str) -> Tuple[str, str, int]:
    """Run git inside `repo`; return (stdout, stderr, exit code)."""
    try:
        p = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            env=_env(),
        )
    except FileNotFoundError:
        return "", "git not found", 127
    return (
        p.stdout.decode("utf-8", "replace"),
        p.stderr.decode("utf-8", "replace"),
        p.returncode,
    )


@dataclass
class Context:
    """The repository's current state. rules.match() sees only this and the
    error text."""

    repo: str
    is_repo: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None          # None when detached
    detached: bool = False
    oid: Optional[str] = None             # HEAD commit; None before first commit
    upstream: Optional[str] = None
    ahead: int = 0                        # commits ahead of upstream
    behind: int = 0                       # commits behind upstream
    conflicted: List[str] = field(default_factory=list)
    in_progress: List[str] = field(default_factory=list)
    staged: List[str] = field(default_factory=list)
    # Changed on disk but not staged. Scenario 11 counts these.
    unstaged: List[str] = field(default_factory=list)
    # (sha, commit subject, the reflog entry that followed it)
    lost: List[Tuple[str, str, str]] = field(default_factory=list)
    has_remote: bool = False
    remotes: List[str] = field(default_factory=list)
    # Staged paths that .gitignore rules match. A non-empty list means
    # "a rule exists and the file was staged anyway" (git add -f, or the
    # rule was written after the file was added).
    ignored_staged: List[str] = field(default_factory=list)
    last_subject: Optional[str] = None
    user_email: Optional[str] = None

    @property
    def short_oid(self) -> str:
        return (self.oid or "")[:7] or "none"


def _parse_status(ctx: Context, out: str) -> None:
    """Parse `git status --porcelain=v2 --branch` into the Context.

    Lines we care about:
      # branch.oid <sha> | (initial)
      # branch.head <name> | (detached)
      # branch.upstream <name>        -- absent entirely when there is none
      # branch.ab +<ahead> -<behind>  -- absent entirely when there is none
      u <xy> ... <path>               -- conflicted file
      1/2 <xy> ... <path>             -- changed file; xy[1] != '.' means the
                                         change is not staged
    """
    for line in out.splitlines():
        if line.startswith("# branch.oid "):
            value = line[len("# branch.oid "):].strip()
            ctx.oid = None if value == "(initial)" else value
        elif line.startswith("# branch.head "):
            value = line[len("# branch.head "):].strip()
            if value == "(detached)":
                ctx.detached = True
                ctx.branch = None
            else:
                ctx.branch = value
        elif line.startswith("# branch.upstream "):
            ctx.upstream = line[len("# branch.upstream "):].strip()
        elif line.startswith("# branch.ab "):
            for part in line[len("# branch.ab "):].split():
                if part.startswith("+"):
                    ctx.ahead = int(part[1:] or 0)
                elif part.startswith("-"):
                    ctx.behind = int(part[1:] or 0)
        elif line.startswith("u "):
            # u <xy> <sub> <m1> <m2> <m3> <mW> <h1> <h2> <h3> <path>
            fields = line.split(" ", 10)
            if len(fields) == 11:
                ctx.conflicted.append(fields[10])
        elif line.startswith("1 ") or line.startswith("2 "):
            # 1 <xy> <sub> <mH> <mI> <mW> <hH> <hI> <path>
            fields = line.split(" ", 8)
            if len(fields) == 9 and len(fields[1]) == 2 and fields[1][1] != ".":
                # On a "2 " (renamed/copied) line the path is "new\told"
                ctx.unstaged.append(fields[8].split("\t")[0])


def collect(repo: str = ".") -> Context:
    """Collect the repository's state into one Context. Read-only."""
    ctx = Context(repo=os.path.abspath(repo))

    git_dir, _, rc = _git(repo, "rev-parse", "--absolute-git-dir")
    if rc != 0:
        return ctx  # not a git repository; is_repo stays False
    ctx.is_repo = True
    ctx.git_dir = git_dir.strip()

    status, _, _ = _git(repo, "status", "--porcelain=v2", "--branch")
    _parse_status(ctx, status)

    ctx.in_progress = [
        name for name in IN_PROGRESS_PATHS
        if os.path.exists(os.path.join(ctx.git_dir, name))
    ]

    staged, _, _ = _git(repo, "diff", "--cached", "--name-only")
    ctx.staged = [p for p in staged.splitlines() if p.strip()]
    # 200-path cap: a huge first commit can hold thousands of paths and there
    # is nothing to gain from inflating the single check-ignore call.
    ctx.ignored_staged = ignored_paths(repo, ctx.staged[:200])

    remotes, _, _ = _git(repo, "remote")
    ctx.remotes = [r for r in remotes.splitlines() if r.strip()]
    ctx.has_remote = bool(ctx.remotes)

    subject, _, rc = _git(repo, "log", "-1", "--format=%s")
    ctx.last_subject = subject.strip() if rc == 0 else None

    email, _, rc = _git(repo, "config", "user.email")
    ctx.user_email = email.strip() if rc == 0 and email.strip() else None

    ctx.lost = lost_commits(repo)

    return ctx


def is_ignored(repo: str, path: str) -> bool:
    """Ask `git check-ignore` whether a single path is ignored.

    Exit 0 = ignored, 1 = not ignored.
    """
    _, _, rc = _git(repo, "check-ignore", "-q", "--no-index", path)
    return rc == 0


def ignored_paths(repo: str, paths: List[str]) -> List[str]:
    """Return those paths that .gitignore rules match.

    --no-index is REQUIRED: by default check-ignore consults the index and
    reports a path that is in it (i.e. staged) as "not ignored" even when a
    rule matches. Scenarios 9 and 10 ask about exactly the staged paths, so
    without this flag the answer is always empty.

    One call, via --stdin. Read-only.
    """
    paths = [p for p in paths if p.strip()]
    if not paths:
        return []
    try:
        p = subprocess.run(
            ["git", "-C", repo, "check-ignore", "--no-index", "--stdin"],
            input="\n".join(paths).encode("utf-8"),
            capture_output=True,
            env=_env(),
        )
    except FileNotFoundError:
        return []
    if p.returncode not in (0, 1):   # 128 = error; stay quiet
        return []
    out = p.stdout.decode("utf-8", "replace")
    return [p for p in out.splitlines() if p.strip()]


def reflog(repo: str, count: int = 30) -> List[str]:
    """Human-readable reflog lines. Read-only."""
    out, _, rc = _git(repo, "reflog", "--date=relative", "-%d" % count)
    if rc != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]


def unreachable(repo: str, shas: List[str]) -> Set[str]:
    """Return those commits that no ref can reach.

    `rev-list --no-walk <shas> --not --all`: --no-walk does not descend into
    ancestors, and `--not --all` excludes everything reachable from any ref.
    What remains is exactly the commits no branch, tag or HEAD points at.
    One call, no cap. Read-only.
    """
    if not shas:
        return set()
    out, _, rc = _git(repo, "rev-list", "--no-walk", *(list(shas) + ["--not", "--all"]))
    if rc != 0:
        return set()
    return {s.strip() for s in out.splitlines() if s.strip()}


def lost_commits(repo: str, count: int = 10) -> List[Tuple[str, str, str]]:
    """Commits in the last `count` reflog entries that no ref can reach.

    Two limits, both deliberate:

    1. Only the last 10 entries. A reflog holds hundreds, and reporting a
       commit dropped months ago as "you lost this" is noise. `gitwhy doctor`
       exists to show the full reflog.
    2. Skipped when the entry above (the newer one) is `commit (amend)`:
       amending leaves the old commit unreachable, but that is deliberate,
       not a loss. Verified by the neg_amend fixture.
    """
    out, _, rc = _git(repo, "reflog", "--format=%H%x09%gs%x09%s", "-%d" % count)
    if rc != 0:
        return []
    entries: List[Tuple[str, str, str]] = []
    for line in out.splitlines():
        fields = line.split("\t")
        if len(fields) >= 3 and fields[0].strip():
            entries.append((fields[0].strip(), fields[1], fields[2]))

    candidates: List[Tuple[str, str, str]] = []
    seen = set()
    for i, (sha, _reflog_subject, subject) in enumerate(entries):
        if i > 0 and entries[i - 1][1].startswith("commit (amend)"):
            continue
        if sha in seen:
            continue
        seen.add(sha)
        next_op = entries[i - 1][1] if i > 0 else "(most recent operation)"
        candidates.append((sha, subject, next_op))

    lost = unreachable(repo, [c[0] for c in candidates])
    return [c for c in candidates if c[0] in lost]
