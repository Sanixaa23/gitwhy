"""Scenario id + context -> readable text.

Two modes:
  - Template mode (default): the scenarios/*.md files with context values
    filled in. Offline, deterministic, instant.
  - LLM mode (--ai, not built yet): rewrites the same template for the
    reader's level. The DECISION is not made by the LLM; the LLM only
    rewrites the prose.

Safety: this module RUNS NOTHING. It only produces text.
"""
from __future__ import annotations

import os
import re
from typing import Dict, Optional

from . import rules
from .context import Context

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios")

# Commands that can cause irreversible data loss. If a template contains one
# of these, it must carry a warning; test_safety.py enforces that.
DESTRUCTIVE_COMMANDS = (
    "git reset --hard",
    "git clean -f",
    "git checkout --",
    "git push --force",
    "git push -f",
    "git rebase --abort",
    "git rebase --skip",
    "git merge --abort",
    "git stash drop",
    "git stash clear",
    "git branch -D",
    "git reflog expire",
    "git gc --prune",
    "git filter-repo",
    "git filter-branch",
    "--discard-changes",
)

# If a --run option is ever added, ONLY these may run automatically.
# All of them are reversible. No destructive command may join this list.
AUTO_RUNNABLE = (
    "git switch",
    "git stash push",
    "git branch",
    "git remote -v",
    "git status",
    "git diff",
    "git log",
)

# A warning line in a template starts with this prefix and carries the word
# PERMANENTLY.
WARNING_PREFIX = "> WARNING:"
WARNING_MARKER = "PERMANENTLY"

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def values(ctx: Context) -> Dict[str, str]:
    """The placeholders available inside templates."""
    dependencies = rules.dependency_paths(ctx)
    secrets = rules.secret_paths(ctx)
    lost = ctx.lost
    return {
        "repo": ctx.repo,
        "branch": ctx.branch or "(no branch)",
        "upstream": ctx.upstream or "(not set)",
        "ahead": str(ctx.ahead),
        "behind": str(ctx.behind),
        "short_oid": ctx.short_oid,
        "last_subject": ctx.last_subject or "(no commit yet)",
        "conflicted": ", ".join(ctx.conflicted) or "(none)",
        "first_conflicted": ctx.conflicted[0] if ctx.conflicted else "<file>",
        "conflicted_count": str(len(ctx.conflicted)),
        "staged": ", ".join(ctx.staged) or "(none)",
        "staged_count": str(len(ctx.staged)),
        "unstaged": ", ".join(ctx.unstaged) or "(none)",
        "first_unstaged": ctx.unstaged[0] if ctx.unstaged else "<file>",
        "unstaged_count": str(len(ctx.unstaged)),
        "in_progress": ", ".join(ctx.in_progress) or "(none)",
        "in_progress_command": _in_progress_command(ctx),
        "remotes": ", ".join(ctx.remotes) or "(none)",
        "first_remote": ctx.remotes[0] if ctx.remotes else "origin",
        "user_email": ctx.user_email or "(not set)",
        "dependencies": ", ".join(dependencies) or "(none)",
        "first_dependency": dependencies[0] if dependencies else "<directory>",
        "dependency_count": str(len(dependencies)),
        "secrets": ", ".join(secrets) or "(none)",
        "first_secret": secrets[0] if secrets else "<file>",
        "secret_count": str(len(secrets)),
        "lost_count": str(len(lost)),
        "lost_list": "\n".join(
            "- `%s` — %s  (reflog: %s)" % (sha[:8], subject, next_op)
            for sha, subject, next_op in lost
        ) or "- (none)",
        "first_lost_sha": lost[0][0][:8] if lost else "<sha>",
        "first_lost_subject": lost[0][1] if lost else "(unknown)",
        "ignore_status": _ignore_status(ctx, dependencies + secrets),
    }


def _in_progress_command(ctx: Context) -> str:
    """The git command name of the half-finished operation; scenario 4 uses it.

    `git cherry-pick --continue` and `git revert --continue` are different
    commands; rather than showing a beginner both, we give the right one.
    """
    if "REVERT_HEAD" in ctx.in_progress:
        return "revert"
    if "CHERRY_PICK_HEAD" in ctx.in_progress:
        return "cherry-pick"
    if "rebase-merge" in ctx.in_progress or "rebase-apply" in ctx.in_progress:
        return "rebase"
    if "MERGE_HEAD" in ctx.in_progress:
        return "merge"
    return "cherry-pick"


def _ignore_status(ctx: Context, paths) -> str:
    """Does .gitignore cover these paths? If it does, that is a different problem."""
    if not paths:
        return "no problematic staged path"
    covered = [p for p in ctx.ignored_staged if any(p.startswith(x) for x in paths)]
    if covered:
        return (
            ".gitignore already covers this path (%s) — the file was staged "
            "anyway. Either `git add -f` was used, or the rule was written "
            "after the file was added; an ignore rule does not untrack a file "
            "that is already tracked." % ", ".join(covered[:3])
        )
    return ".gitignore does not cover this path"


def read_template(scenario_id: str) -> str:
    path = os.path.join(TEMPLATE_DIR, scenario_id + ".md")
    with open(path, encoding="utf-8") as f:
        return f.read()


def templates() -> Dict[str, str]:
    """All templates as {scenario_id: text} (used by test_safety)."""
    if not os.path.isdir(TEMPLATE_DIR):
        return {}
    return {
        name[:-3]: read_template(name[:-3])
        for name in sorted(os.listdir(TEMPLATE_DIR))
        if name.endswith(".md")
    }


def fill(template: str, ctx: Context) -> str:
    """Replace {{key}} placeholders with context values.

    An unknown key is left as-is so that a typo in a template shows up in the
    output instead of disappearing silently.
    """
    v = values(ctx)
    return _PLACEHOLDER.sub(lambda m: v.get(m.group(1), m.group(0)), template)


def explain(scenario_id: Optional[str], ctx: Context) -> str:
    """Produce the scenario text. Falls back to a state dump when nothing matched."""
    if scenario_id is None:
        return _no_match(ctx)
    try:
        template = read_template(scenario_id)
    except FileNotFoundError:
        return (
            "Scenario matched but its template is missing: %s\n"
            "Write src/gitwhy/scenarios/%s.md\n" % (scenario_id, scenario_id)
        )
    return fill(template, ctx)


def _no_match(ctx: Context) -> str:
    if not ctx.is_repo:
        return (
            "## What happened\n\n"
            "This is not a git repository: %s\n\n"
            "## What to do\n\n"
            "    git init\n" % ctx.repo
        )
    v = values(ctx)
    return (
        "## No matching scenario\n\n"
        "gitwhy knows %d of %d scenarios; this state is not one of them.\n\n"
        % (len(rules.IMPLEMENTED), len(rules.SCENARIOS)) +
        "## Where you are\n\n"
        "- Repository: %(repo)s\n"
        "- Branch: %(branch)s\n"
        "- Upstream: %(upstream)s (ahead %(ahead)s / behind %(behind)s)\n"
        "- Conflicted files: %(conflicted)s\n"
        "- Operation in progress: %(in_progress)s\n"
        "- Staged files: %(staged_count)s\n" % v
    )


def is_destructive(text: str) -> bool:
    """Does this text contain an irreversible command?"""
    return any(cmd in text for cmd in DESTRUCTIVE_COMMANDS)


def has_warning(text: str) -> bool:
    """Does this text carry a properly formed warning line?"""
    for line in text.splitlines():
        if line.strip().startswith(WARNING_PREFIX):
            return True
    return False
