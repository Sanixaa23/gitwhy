# Devpost submission draft

Paste each section into the matching Devpost field. Replace `Sanixaa23` with your
GitHub username before submitting, and check the event's prize list for a
developer-tools or education track to enter as well.

---

## Tagline

Explains why your git command failed by reading your repository, not the error
message.

---

## Inspiration

Every beginner hits the same wall. You run `git push`, git answers
`fatal: The current branch main has no upstream branch`, and the next move is
to paste that line into a search engine and hope the top answer applies to your
repository. It usually does not, because the fix depends on state the error
message does not mention: whether a remote exists, whether a rebase is half
finished, whether the conflict is in a file you were not editing.

The tools that exist either repeat the error in friendlier words or ask a
language model to guess. Neither looks at the repository.

## What it does

When a git command fails, gitwhy answers three questions:

1. **What happened** — the error in a beginner's words, one sentence.
2. **Where you are** — the repository's actual state: branch, how far ahead or
   behind, conflicted files, any half-finished operation.
3. **What to do** — a copyable command for *this* state, with your branch name
   already in it.

It covers 12 scenarios and says so plainly; there is no claim that it solves
every git error. It works with no network and no account. Destructive commands
are printed, never run.

## How we built it

Four layers, and the boundary between them is the whole design:

- `context.py` collects repository state with read-only git queries. Most of it
  comes from one call: `git status --porcelain=v2 --branch` yields the branch,
  the detached flag, the upstream, the ahead/behind counts, the conflicted
  files and the unstaged files at once. That output format is stable across git
  versions; error messages are not.
- `rules.py` maps (state, error text, failed command) to a scenario id. It is a
  pure function — no I/O, no network, no LLM.
- `explain.py` fills a hand-written markdown template per scenario.
- `cli.py` wires up five subcommands, plus an optional shell wrapper that fires
  automatically when git fails.

An `--ai` mode exists and is off by default. It never makes the decision; it
only rewrites the already-chosen explanation for the reader's level, and the
answer is vetted before it is shown.

## Measured scenario accuracy

This is the part we care about most. `tests/fixtures.py` builds a **real** git
repository per scenario and puts it into that broken state — a real rebase
conflict, a real rejected push against a real bare remote, a real protected
branch refusing a push through a pre-receive hook. The rule engine then reads
that repository and predicts.

```
12 scenarios, 18 fixtures, 18/18 correct (100%)
```

Three of those fixtures are **negative controls**: a clean repository, a
repository after `commit --amend`, and main with an unpushed commit. None may
match anything, and none does. That is the number we trust, because it is the
one that can fail.

GitHub Actions re-measures the matrix on every pull request, on Linux and
Windows, on Python 3.9 and 3.12.

## Challenges we ran into

**Ordering.** During a rebase conflict `git status` reports detached HEAD *and*
a running rebase simultaneously. Checking detached HEAD first produces advice
that is confidently wrong. A fixture caught it; a test now locks the order.

**A rejected push gives no "you are behind" signal.** We assumed `branch.ab`
would show it. It does not: git leaves the remote-tracking ref untouched after
a rejected push, so the count still reads `+1 -0`. The real number only appears
after a fetch, and our context collector is not allowed to fetch. Scenario 7 is
the single rule that decides from the error text instead, and a test records
why.

**Our own error-marker list was a gate we could not see through.** We filter
error output down to decision lines. The protected-branch rejection reads
`! [remote rejected]`, which matches neither `"! [rejected]"` nor
`"[rejected]"` — the word `remote` sits in between. The rule was right, the
pattern was right, and the scenario silently matched nothing. Twice. There is a
test for that class of bug now.

**The shell wrapper could not record the error text,** because the text was
already on the user's screen. The result: five scenarios matched nothing
through the wrapper. Piping stderr would have fixed it and silenced git's
progress bars, so instead we fed the *failed command* to the rules — `git push`
plus no remote is scenario 5 without reading a single character of the error.
Coverage went from 7/12 to 10/12 with no trade-off.

## Accomplishments we're proud of

- A number we can defend: 18/18, with the negative controls included.
- Safety that is tested rather than promised. Every template containing a
  destructive command must carry a warning saying what it deletes; the context
  collector is checked to contain no git command that writes; the AI mode's
  output is rejected if it introduces `git reset --hard` or waters a warning
  down.
- Zero runtime dependencies, offline by default.
- A demo recording that is generated from real program output, so it cannot
  drift from what the tool actually does.

## What we learned

Reading state beats parsing messages, and the only way to know whether a rule
works is to build the broken repository and ask it. Every significant design
decision here came from a fixture contradicting an assumption, not from
reasoning about git.

We also learned to leave a scenario out on purpose. "Main has unpushed commits"
cannot be distinguished from the normal state of someone working alone, so the
state-based form of that scenario does not exist. Not producing false positives
came before widening coverage.

## What's next

The four scenarios we did not build (stash conflicts, submodule drift, LFS
pointers, shallow-clone failures), a fish wrapper, and localisation of the
templates. The rule engine needs no changes for any of it — a new scenario is a
fixture, a rule and a template, in that order.

## Built With

python, git, github-actions, pytest, pillow, asciinema, anthropic-api

## Try it out

```
pipx install git+https://github.com/Sanixaa23/gitwhy
gitwhy doctor
```
