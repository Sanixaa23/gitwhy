"""Builds the three repositories the 90-second video is recorded in.

Recording a demo is hard enough without setting up broken repositories on
camera. This builds all three ahead of time and leaves each one exactly one
command away from the failure you want to show, so during the take you type
only the line the audience should see.

    python tools/video_setup.py            # ~/gitwhy-video/
    python tools/video_setup.py --base D:\\demo
    python tools/video_setup.py --reset    # rebuild from scratch

Shot list: docs/VIDEO.md

Safety: --reset deletes the target directory, so it refuses unless that
directory carries the .gitwhy-video marker this script wrote. It will not
remove a directory it did not create.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys

MARKER = ".gitwhy-video"


def _force_remove(func, path, _exc):
    """Clear the read-only bit and retry: loose git objects are read-only.

    shutil.rmtree cannot delete them on Windows. With ignore_errors=True that
    failure was silent, and since the marker is deleted first, the directory
    ended up half-removed AND unresettable -- the next --reset refused it.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="student",
    GIT_AUTHOR_EMAIL="student@school.edu",
    GIT_COMMITTER_NAME="student",
    GIT_COMMITTER_EMAIL="student@school.edu",
    LC_ALL="C",
    GIT_TERMINAL_PROMPT="0",
)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=ENV)
    return p.stdout.decode("utf-8", "replace"), p.returncode


def write(repo, name, text):
    path = os.path.join(repo, name)
    if os.path.dirname(name):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def new_repo(base, name):
    repo = os.path.join(base, name)
    os.makedirs(repo, exist_ok=True)
    git(repo, "init", "-q", "-b", "main")
    # Keep the recording free of the host's own git settings: no autocrlf
    # warnings, no signing prompt, no unrelated hooks.
    git(repo, "config", "user.name", "student")
    git(repo, "config", "user.email", "student@school.edu")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "commit.gpgsign", "false")
    return repo


# --- the three takes -------------------------------------------------------

def build_push(base):
    """0:00-0:20 — scenario 5. Ready for `git push` to fail.

    This take NEEDS the shell wrapper. Scenario 5 is found from the failed
    command, and a bare `gitwhy` typed afterwards has no way to know you ran
    push: there is no record and no error text. "No remote configured" is not
    a scenario on its own either — a local-only repository is a perfectly
    normal thing to have, which is why the neg_clean fixture must not match.
    With the wrapper installed, `git push` itself fires the explanation.
    """
    repo = new_repo(base, "01-first-push")
    write(repo, "app.py", "print('my first project')\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-qm", "first version")
    return repo, ["git push"]


def build_rebase(base):
    """0:20-0:38 — scenario 3. On `feature`, ready for `git rebase main`."""
    repo = new_repo(base, "02-rebase")
    write(repo, "a.txt", "title\n")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-qm", "first commit")
    write(repo, "a.txt", "title\nwritten on main\n")
    git(repo, "commit", "-qam", "keep going on main")
    git(repo, "checkout", "-q", "-b", "feature", "HEAD~1")
    write(repo, "a.txt", "title\nwritten on the feature branch\n")
    git(repo, "commit", "-qam", "add feature")
    return repo, ["git rebase main", "gitwhy"]


def build_secret(base):
    """0:38-0:52 — scenario 10. The .env exists but is NOT staged yet, so the
    `git add .` in the shot list is a real command and not a prop."""
    repo = new_repo(base, "03-secret")
    write(repo, "app.py", "import os\nkey = os.environ['OPENAI_API_KEY']\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-qm", "read the key from the environment")
    # Obviously fake value: this file is on camera.
    write(repo, ".env", "OPENAI_API_KEY=sk-demo-this-is-not-a-real-key\n")
    write(repo, ".env.example", "OPENAI_API_KEY=\n")
    return repo, ["git add .", "gitwhy"]


BUILDERS = (build_push, build_rebase, build_secret)


def main():
    ap = argparse.ArgumentParser(description="Set up the video demo repositories")
    ap.add_argument("--base", default=os.path.join(os.path.expanduser("~"),
                                                   "gitwhy-video"),
                    help="where to build them (default: ~/gitwhy-video)")
    ap.add_argument("--reset", action="store_true",
                    help="delete and rebuild (only a directory this script made)")
    arg = ap.parse_args()
    base = os.path.abspath(arg.base)

    if arg.reset and os.path.isdir(base):
        if not os.path.exists(os.path.join(base, MARKER)):
            print("Refusing to delete %s: no %s marker, so this script did not "
                  "create it. Remove it yourself, or pass another --base."
                  % (base, MARKER))
            return 1
        shutil.rmtree(base, onerror=_force_remove)

    if os.path.isdir(base) and os.listdir(base):
        print("%s already exists. Use --reset to rebuild it." % base)
        return 1

    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, MARKER), "w", encoding="utf-8") as f:
        f.write("Built by tools/video_setup.py. Safe to delete.\n")

    print("Video repositories in %s\n" % base)
    print("Record in Git Bash, WSL or a zsh terminal, NOT PowerShell: the")
    print("wrapper only supports bash and zsh. Install it once per shell:\n")
    print('    eval "$(gitwhy shell-init bash)"\n')
    for build in BUILDERS:
        repo, commands = build(base)
        print("  %s" % repo)
        print("     cd %s" % repo)
        for c in commands:
            print("     %s" % c)
        print()

    print("Before recording:")
    print("  - check `gitwhy --version` (pip install -e .)")
    print("  - 96x48 terminal, NOT the GIF's 96x36: the takes need 38-46 rows")
    print("  - shot list: docs/VIDEO.md, operator card: docs/CUE-SHEET.md")
    print("  - take 1 needs the wrapper; takes 2 and 3 work either way,")
    print("    because a half-finished rebase and a staged .env are visible")
    print("    in the repository's state. Without the wrapper, take 1 is")
    print("    `gitwhy capture -- git push` instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
