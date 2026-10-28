# 90-second demo video — shot list

One take per segment, no cuts inside a segment. Record the terminal at 96x36,
same as the GIF. Speak over it; do not read the screen aloud.

Only 16% of the award-winning projects we sampled had a video at all, so this
is close to free marks — but only if it is short and shows the thing working.

**Before recording:** `pip install -e .`, check `gitwhy --version`, and set
`GIT_CONFIG_GLOBAL` to a non-existent path so your own git config stays out of
the frame. Three temporary repositories, built ahead of time, one per scenario.

---

## 0:00–0:08 — The problem, in one real error

**Screen:** a terminal. Run `git push` in a fresh repo. Git prints
`fatal: No configured push destination.` followed by five lines of advice.

**Say:** "This is what git says when a beginner's first push fails. It is
correct, and it is useless if you do not already know what a remote is."

Do not explain the project yet. Show the pain first.

---

## 0:08–0:20 — What gitwhy answers

**Screen:** type `gitwhy`. The scenario-5 explanation fills the screen: what
happened, where you are, the two commands to run.

**Say:** "gitwhy reads the repository, not the error message. No remote is
configured, so it tells you that in plain words and gives you the two commands
for this repository, with your branch name already in them."

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

**Screen:** `pipx install git+https://github.com/<user>/gitwhy`, then
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
