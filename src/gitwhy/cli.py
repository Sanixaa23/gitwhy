"""gitwhy command line interface.

    gitwhy                           explain the last failed git command
    gitwhy explain --stderr FILE     explain the given error output (- = stdin)
    gitwhy capture -- git push       run the command, record it if it fails
    gitwhy doctor                    repository health
    gitwhy shell-init [bash|zsh]     print the wrapper shell code

No subcommand modifies the repository. `capture` runs exactly the command the
user gave it; it never invents one.
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

from . import __version__, capture, context, explain, rules

# The wrapper does the same job in both shells; the only difference is how the
# pipeline's exit code is read: ${PIPESTATUS[0]} in bash, ${pipestatus[1]} in
# zsh (zsh arrays are 1-based).
_WRAPPER_BODY = """# gitwhy shell wrapper - add this to {file}
# To remove it: unset -f git
#
# Default: git's output is untouched, only the command and exit code are
# recorded. In this mode 10 of the 12 scenarios can still be found.
# GITWHY_TEE=1: stderr is also copied to a file, which additionally finds
# push rejections (scenarios 7 and 8). The cost: stderr is no longer attached
# to the terminal, so git stops printing progress bars ("Writing objects:
# ..."). Turn it on if you want it; off by default.
git() {{
  command -v gitwhy >/dev/null 2>&1 || {{ command git "$@"; return $?; }}
  local code
  if [ "${{GITWHY_TEE:-0}}" = "1" ]; then
    local gw_err="${{TMPDIR:-/tmp}}/gitwhy-stderr.$$"
    {{ command git "$@" 2>&1 1>&3 | tee "$gw_err" >&2; }} 3>&1
    code={pipestatus}
    command gitwhy capture-exit "$code" "git $*" \\
        --stderr-file "$gw_err" >/dev/null 2>&1
    rm -f "$gw_err"
  else
    command git "$@"
    code=$?
    command gitwhy capture-exit "$code" "git $*" >/dev/null 2>&1
  fi
  # 130 = Ctrl-C. The user stopped it themselves; there is no error to explain.
  if [ "$code" -ne 0 ] && [ "$code" -ne 130 ]; then
    command gitwhy
  fi
  return $code
}}
"""

WRAPPER = {
    "bash": _WRAPPER_BODY.format(file="~/.bashrc", pipestatus="${PIPESTATUS[0]}"),
    "zsh": _WRAPPER_BODY.format(file="~/.zshrc", pipestatus="${pipestatus[1]}"),
}


def _out(text: str) -> None:
    """Print without blowing up on a Windows console that is not UTF-8."""
    try:
        sys.stdout.write(text + "\n")
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.write(text.encode(encoding, "replace").decode(encoding) + "\n")


def _explain(repo: str, error_text: str, command: str = None) -> int:
    ctx = context.collect(repo)
    scenario = rules.match(ctx, error_text, command)
    _out(explain.explain(scenario, ctx))
    return 0 if scenario else 1


def cmd_last_error(arg) -> int:
    ctx = context.collect(arg.repo)
    record = capture.read()
    # A record from another repository, or a stale one, is not used.
    if not capture.is_valid(record, ctx.repo):
        record = None
    scenario = rules.match(ctx, capture.error_text(record), capture.command(record))
    # Only announce the missing record when we genuinely have nothing: if the
    # repository state alone matched a scenario there is nothing to apologise for.
    if scenario is None and record is None:
        _out(
            "No recorded error. Looking at the repository's current state.\n"
            "To explain a specific error:  gitwhy explain --stderr -\n"
        )
    _out(explain.explain(scenario, ctx))
    return 0 if scenario else 1


def cmd_explain(arg) -> int:
    if arg.stderr == "-":
        text = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace").read()
    else:
        with open(arg.stderr, encoding="utf-8", errors="replace") as f:
            text = f.read()
    return _explain(arg.repo, text)


def cmd_capture(arg) -> int:
    """Run the given command; if it fails, record and explain it."""
    if not arg.command:
        _out("Usage: gitwhy capture -- git push")
        return 2
    p = subprocess.run(arg.command, capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    sys.stdout.write(out)
    sys.stderr.write(err)
    if p.returncode == 0:
        return 0
    capture.write(" ".join(arg.command), p.returncode, out, err, arg.repo)
    _out("")
    _explain(arg.repo, err + "\n" + out, " ".join(arg.command))
    return p.returncode


def cmd_capture_exit(arg) -> int:
    """Record for the shell wrapper.

    By default the output is already on screen, so only the command and exit
    code are stored; the rules can still find scenarios 5, 6 and 11 without
    any text. With GITWHY_TEE=1 the wrapper also writes stderr to a file and
    passes it here; only then do scenarios 7 and 8 match.
    """
    text = ""
    if arg.stderr_file:
        try:
            with open(arg.stderr_file, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            text = ""
    capture.write(arg.command_text, arg.code, "", text, arg.repo)
    return 0


_RISKY = (".env", "id_rsa", "credentials.json", ".pem", ".p12", ".keystore")


def _is_risky(path: str) -> bool:
    name = path.replace("\\", "/").split("/")[-1].lower()
    return any(name == r or name.endswith(r) for r in _RISKY)


def cmd_doctor(arg) -> int:
    ctx = context.collect(arg.repo)
    if not ctx.is_repo:
        _out("Not a git repository: %s" % ctx.repo)
        return 1
    lines = ["# gitwhy doctor — %s" % ctx.repo, ""]
    lines.append("branch             : %s" % (ctx.branch or "(detached)"))
    lines.append("upstream           : %s" % (ctx.upstream or "none"))
    lines.append("ahead / behind     : +%d / -%d" % (ctx.ahead, ctx.behind))
    lines.append("remote             : %s" % (", ".join(ctx.remotes) or "none"))
    lines.append("operation running  : %s" % (", ".join(ctx.in_progress) or "none"))
    lines.append("conflicted files   : %d" % len(ctx.conflicted))
    lines.append("unstaged changes   : %d" % len(ctx.unstaged))
    lines.append("unreachable commits: %s" % (
        ", ".join("%s (%s)" % (sha[:8], subject) for sha, subject, _ in ctx.lost)
        or "none"))
    lines.append("user.email         : %s" % (ctx.user_email or "NOT SET"))
    gitignore = os.path.exists(os.path.join(ctx.repo, ".gitignore"))
    lines.append(".gitignore         : %s" % ("present" if gitignore else "MISSING"))
    risky = [p for p in ctx.staged if _is_risky(p)]
    lines.append("staged secrets     : %s" % (", ".join(risky) or "none"))
    _out("\n".join(lines))
    return 0


def cmd_shell_init(arg) -> int:
    code = WRAPPER.get(arg.shell)
    if code is None:
        _out("Supported shells: bash, zsh. PowerShell is out of scope.")
        return 2
    sys.stdout.write(code)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="gitwhy",
        description="Explains git errors by reading your repository's state.",
    )
    parser.add_argument("--version", action="version", version="gitwhy " + __version__)
    parser.add_argument("--repo", default=".", help="repository to inspect (default: .)")
    sub = parser.add_subparsers(dest="subcommand")

    p = sub.add_parser("explain", help="explain the given error output")
    p.add_argument("--stderr", required=True, help="error output file, - = stdin")
    p.add_argument("--repo", default=".")
    p.set_defaults(func=cmd_explain)

    p = sub.add_parser("capture", help="run a command and explain it if it fails")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.add_argument("--repo", default=".")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("capture-exit", help="record written by the shell wrapper")
    p.add_argument("code", type=int)
    p.add_argument("command_text")
    p.add_argument("--stderr-file", dest="stderr_file", default=None,
                   help="error file written by the wrapper under GITWHY_TEE=1")
    p.add_argument("--repo", default=".")
    p.set_defaults(func=cmd_capture_exit)

    p = sub.add_parser("doctor", help="repository health")
    p.add_argument("--repo", default=".")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("shell-init", help="print the wrapper shell code")
    p.add_argument("shell", nargs="?", default="bash", choices=["bash", "zsh"])
    p.set_defaults(func=cmd_shell_init)

    arg = parser.parse_args(argv)
    func = getattr(arg, "func", cmd_last_error)
    return func(arg)


if __name__ == "__main__":
    sys.exit(main())
