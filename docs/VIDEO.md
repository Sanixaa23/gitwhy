# Demo video — 2:20 shot list

**The video must be between two and five minutes.** That is a submission
requirement, not a style note: see `SOURCEHACKS.md`. An earlier version of
this file was a 90-second cut, which would have been rejected. Do not trim
below 2:00 to tighten the pacing — if a segment drags, say less over it.

One take per segment, no cuts inside a segment. Record the terminal at 96x36,
same as the GIF. Speak over it; do not read the screen aloud.

Only 16% of the award-winning projects we sampled had a video at all, so the
video is close to free marks — but only if it shows the thing working.

**Before recording:** run `python tools/video_setup.py`, which builds the
three repositories in `~/gitwhy-video/` and leaves each one a single command
away from the failure you want on camera. Check `gitwhy --version` first
(`pip install -e .`).

**Record in Git Bash, WSL or zsh — not PowerShell.** The shell wrapper
supports bash and zsh only, and take 1 needs it. Install it once in the
recording shell:

```bash
eval "$(gitwhy shell-init bash)"
```

Take 1 depends on the wrapper because scenario 5 is found from the *failed
command*. A bare `gitwhy` typed after a failed push has no way to know you ran
push: there is no record and no error text, and "no remote configured" is not a
scenario by itself — a local-only repository is a normal thing to have, which
is exactly why the `neg_clean` fixture must not match. Without the wrapper,
take 1 becomes `gitwhy capture -- git push`. Takes 2 and 3 work either way: a
half-finished rebase and a staged `.env` are visible in the repository's state.

---

## 0:00–0:20 — The problem and the answer, in one take

**Screen:** `cd ~/gitwhy-video/01-first-push`, then `git push`. Git prints
`fatal: No configured push destination.` and five lines of advice — then, with
no further typing, gitwhy's explanation appears underneath it.

**Say, over the git error:** "This is what git says when a beginner's first
push fails. It is correct, and it is useless if you do not already know what a
remote is."

**Say, as gitwhy's output appears:** "We did not type anything. The wrapper
noticed git failed, and gitwhy read the repository: no remote is configured. So
it says that in plain words and gives the two commands for this repository,
with the branch name already filled in."

Do not describe the project before the error. Show the pain first.

---

## 0:20–0:42 — Scenario 3: the state, not the text

**Screen:** second repo. `git rebase main` fails with
`error: could not apply` and `CONFLICT`. Type `gitwhy`.

**Say:** "Here is the part other tools get wrong. During a rebase conflict git
reports that you are in detached HEAD **and** that a rebase is running, at the
same time. A tool that checks detached HEAD first tells you to create a branch —
exactly the wrong move. We check the in-progress operation first, and a test
enforces that order."

**Screen while talking:** scroll to the `## Where you are` block so
`Operation in progress: rebase-merge` is visible.

---

## 0:42–1:00 — Scenario 10: the expensive mistake

**Screen:** third repo. `git add .` with a `.env` present. Type `gitwhy`.

**Say:** "A staged `.env`. gitwhy tells you to revoke the key first and clean
history second, because a pushed key is already out of your hands. And note
what it does not do: it prints `git filter-repo`, it does not run it."

**Screen:** stay on the `> WARNING:` line for a full second.

---

## 1:00–1:25 — How it decides

**Screen:** split or cut between two files. First `src/gitwhy/context.py`,
scrolled to `_parse_status`. Then `src/gitwhy/rules.py`, scrolled to `match`.

**Say:** "Four layers, and the boundary between them is the whole design. The
collector asks git for state — almost all of it from one call,
`git status --porcelain=v2 --branch`, which gives the branch, the detached
flag, the upstream, the ahead and behind counts, the conflicted files and the
unstaged files at once. That output format is stable across git versions.
Error messages are not. Then `match` is a pure function: state in, scenario id
out. No I/O, no network, no model. The explanation is a markdown template a
human wrote."

**Screen while talking:** land on the `ERROR_MARKERS` block or the ordering
comment in `match`, whichever reads better on camera.

---

## 1:25–1:50 — The claim nobody else makes

**Screen:** run `python tests/test_rules.py`. The 13x13 confusion matrix prints.

**Say:** "Every scenario is measured. For each one we build a real repository,
put it into that broken state, and check what the engine predicts. Twelve
scenarios, eighteen fixtures, a hundred percent. The last row is three healthy
repositories — those must match nothing, and they do. A tool like this is
judged by its false positives, not its coverage, which is why the negative
controls are in the same number. This runs on every pull request, on Linux and
Windows."

**Screen:** cut to the green GitHub Actions check for two seconds.

---

## 1:50–2:08 — Safety, guaranteed by a test

**Screen:** run `python -m pytest tests/test_safety.py tests/test_ai.py -q`.
Green.

**Say:** "The tool suggests commands that can destroy work, so the safety rules
are tests, not promises. Every template containing a destructive command must
carry a warning that says what it deletes. The context collector is checked to
contain no git command that writes. And the optional AI mode cannot sneak one
in: it rewrites the wording, it never picks the scenario, and if the model adds
`git reset --hard` or waters a warning down, the answer is thrown away and you
get the template."

---

## 2:08–2:20 — Close

**Screen:** `pipx install git+https://github.com/Sanixaa23/gitwhy`, then
`gitwhy doctor` on a repository with findings.

**Say:** "One line to install, no dependencies, works offline, no account.
Twelve scenarios — and we tell you exactly which twelve."

---

## Notes

- Total 2:20, which clears the two-minute minimum with 20 seconds of margin.
  If a take runs long, that is fine: five minutes is the ceiling.
- If you must cut, cut 0:42–1:00 (scenario 10). It is the most memorable
  segment, but 1:25–1:50 and 1:50–2:08 are the two nobody else can show, and
  1:00–1:25 is the Technical Excellence criterion in twenty-five seconds.
- Never say "AI-powered". The whole argument is that the decision is not an LLM.
- Do not fake a terminal. Everything above is a real command with real output;
  if a take goes wrong, run it again rather than editing the frame.
- The five judging criteria map onto the cut like this: Impact 0:00–0:20,
  Innovation 0:20–0:42, Technical Excellence 1:00–1:50, and Presentation is
  how you speak over all of it. Design & UX is the one the terminal has to
  carry on its own — which is why the output is short, headed and copyable.
