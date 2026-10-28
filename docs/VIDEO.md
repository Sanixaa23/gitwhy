# 90-second demo video — shot list

One take per segment, no cuts inside a segment. Record the terminal at 96x36,
same as the GIF. Speak over it; do not read the screen aloud.

Only 16% of the award-winning projects we sampled had a video at all, so this
is close to free marks — but only if it is short and shows the thing working.

**Before recording:** run `python tools/video_setup.py`, which builds the three
repositories in `~/gitwhy-video/` and leaves each one a single command away
from the failure you want on camera. Check `gitwhy --version` first
(`pip install -e .`).

**Record in Git Bash, WSL or zsh — not PowerShell.** The shell wrapper supports
bash and zsh only, and take 1 needs it. Install it once in the recording shell:

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

## 0:20–0:38 — Scenario 2: the state, not the text

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

## 0:38–0:52 — Scenario 10: the expensive mistake

**Screen:** third repo. `git add .` with a `.env` present. Type `gitwhy`.

**Say:** "A staged `.env`. gitwhy tells you to revoke the key first and clean
history second, because a pushed key is already out of your hands. And note
what it does not do: it prints `git filter-repo`, it does not run it."

**Screen:** stay on the `> WARNING:` line for a full second.

---

## 0:52–1:08 — The claim nobody else makes

**Screen:** run `python tests/test_rules.py`. The 13x13 confusion matrix prints.

**Say:** "Every scenario is measured. For each one we build a real repository,
put it into that broken state, and check what the engine predicts. Twelve
scenarios, eighteen fixtures, a hundred percent. The last row is three healthy
repositories — those must match nothing, and they do. This runs on every pull
request."

**Screen:** cut to the green GitHub Actions check for two seconds.

---

## 1:08–1:22 — Safety, guaranteed by a test

**Screen:** run `python -m pytest tests/test_safety.py -v`. Five green lines.

**Say:** "The tool suggests commands that can destroy work, so the safety rules
are tests, not promises. Every template containing a destructive command must
carry a warning that says what it deletes. The context collector may not contain
a single git command that writes. And the optional AI mode cannot sneak one in:
if the model adds `git reset --hard` or drops a warning, the answer is thrown
away and you get the template."

---

## 1:22–1:30 — Close

**Screen:** `pipx install git+https://github.com/Sanixaa23/gitwhy`, then
`gitwhy doctor` on a repository with findings.

**Say:** "One line to install, no dependencies, works offline. Twelve scenarios,
and we say exactly which twelve."

---

## Notes

- Total 90 seconds. If you overrun, cut 0:38–0:52 (scenario 10) — it is the
  strongest segment but the two measurement segments are what nobody else has.
- Never say "AI-powered". The whole argument is that the decision is not an LLM.
- Do not fake a terminal. Everything above is a real command with real output;
  if a take goes wrong, run it again rather than editing the frame.
