# Cue sheet — read this while recording

`VIDEO.md` is the shot list and the reasoning. This is the operator's card:
what to type, what you will see, what to say, in order, nothing else.

Every command here was run on the real repositories and the line counts are
measured, not estimated. If what you see does not match, stop and fix it
rather than recording around it.

---

## Set up once

```bash
cd /c/Users/Dorsay/Desktop/unturnedplugıns/gitwhy
pip install -e .
gitwhy --version                      # must print: gitwhy 0.1.0
python tools/video_setup.py --reset   # rebuilds all three repos
```

Open the recording shell — **Git Bash, WSL or zsh. Not PowerShell.** Then, in
that shell:

```bash
eval "$(gitwhy shell-init bash)"
```

Terminal **96 columns x 48 rows**. In Git Bash (mintty), either:

```bash
printf '\033[8;48;96t'      # resizes the window; then confirm:
echo "$(tput cols)x$(tput lines)"   # must print 96x48
```

or right-click the title bar → Options → Window → Columns 96, Rows 48. Confirm
with `tput` either way; do not trust the window looking about right.

Clear before each take (`clear`).

**Shorten your prompt first.** The default Git Bash prompt carries the full path
and the git branch, which on these repositories wraps and eats rows you have
measured for. For the recording shell:

```bash
PS1='\[\e[32m\]$ \[\e[0m\]'
```

That also keeps your username and directory tree out of the frame.

---

## Recording settings

OBS is already installed at `C:\Program Files\obs-studio`. Use it rather than
Game Bar: takes 4, 5 and 7 are not terminal-only — take 4 is a code editor and
take 5 cuts to GitHub Actions in a browser — and Game Bar cannot reliably hold a
specific window across an app switch.

- **Canvas and output 2560x1440** if your display allows, else 1920x1080. At
  1440p the 48-row terminal gives ≈30px lines; at 1080p ≈22px, legible but tight.
- **Display Capture**, not Window Capture. You are switching between terminal,
  editor and browser, and Window Capture follows one window only.
- **30fps.** This is static text. 60fps doubles the file for nothing.
- **Audio: one source only.** Mic in, desktop audio muted — otherwise a
  notification lands in the middle of a take and you re-record it.
- Record each take as its own file. Seven short files are far easier to reorder
  and re-shoot than one long one with a bad segment in the middle.

Before the first real take, record ten seconds and play it back. Check the text
is sharp at the output resolution and that your mic is not clipping. Finding
either problem after seven takes costs the whole session.

**Turn off notifications** (Windows Focus Assist, and quit chat apps). A toast
in frame on a public submission video shows whatever its sender wrote.

---

## Take 1 — 0:00–0:20 — the problem and the answer

**Type:**

```bash
cd ~/gitwhy-video/01-first-push
git push
```

**You will see** 37 lines, one frame, no scrolling: git's `fatal: No configured
push destination.` and its five lines of advice, then gitwhy's four headed
sections underneath. You type nothing in between.

**Landmarks:** `fatal:` row 1 · `## What happened` row 10 · `Remotes
configured: none` row 20 · `## What to do` row 23.

**Say, over the git error:**

> This is what git says when a beginner's first push fails. It is correct, and
> it is useless if you do not already know what a remote is.

**Say, as gitwhy's output appears:**

> We did not type anything. The wrapper noticed git failed, and gitwhy read the
> repository: no remote is configured. So it says that in plain words and gives
> the two commands for this repository, with the branch name already filled in.

Do not describe the project before the error. Show the pain first.

---

## Take 2 — 0:20–0:42 — the state, not the text

**Type:**

```bash
cd ~/gitwhy-video/02-rebase
git rebase main
```

**You will see** 41 lines, one frame. Git's `CONFLICT (content): Merge conflict
in a.txt` and `error: could not apply`, four `hint:` lines — then gitwhy, again
with no typing, because the rebase failed.

**Landmarks:** `CONFLICT` row 2 · `error: could not apply` row 3 ·
`Operation in progress: rebase-merge` row 20 · warning rows 39–41.

**Say:**

> Here is the part other tools get wrong. During a rebase conflict git reports
> that you are in detached HEAD **and** that a rebase is running, at the same
> time. A tool that checks detached HEAD first tells you to create a branch —
> exactly the wrong move. We check the in-progress operation first, and a test
> enforces that order.

---

## Take 3 — 0:42–1:00 — the expensive mistake

**Type:**

```bash
cd ~/gitwhy-video/03-secret
git add .
gitwhy
```

`git add .` succeeds, so the wrapper stays quiet. This is the one take where you
type `gitwhy` yourself.

**You will see** 45 lines, one frame. `A secret-bearing file got staged:
**.env**`, then the revoke-first ordering, then the `filter-repo` warning last.

**Landmarks:** `## What happened` row 1 · `## Where you are` row 13 ·
`## What to do` row 20 · `> WARNING:` rows 42–44.

**Say:**

> A staged `.env`. gitwhy tells you to revoke the key first and clean history
> second, because a pushed key is already out of your hands. And note what it
> does not do: it prints `git filter-repo`, it does not run it.

Stop moving on the warning for a full second. It is the last output, so it is
already at the bottom of the frame.

---

## Take 4 — 1:00–1:25 — how it decides

**Screen:** two files, cut or split.

1. `src/gitwhy/context.py`, scrolled to `_parse_status`
2. `src/gitwhy/rules.py`, scrolled to `match`

**Say:**

> Four layers, and the boundary between them is the whole design. The collector
> asks git for state — almost all of it from one call, `git status
> --porcelain=v2 --branch`, which gives the branch, the detached flag, the
> upstream, the ahead and behind counts, the conflicted files and the unstaged
> files at once. That output format is stable across git versions. Error
> messages are not. Then `match` is a pure function: state in, scenario id out.
> No I/O, no network, no model. The explanation is a markdown template a human
> wrote.

Land on the ordering comment in `match`, or `ERROR_MARKERS` — whichever reads
better on camera.

---

## Take 5 — 1:25–1:50 — the claim nobody else makes

**Type:**

```bash
cd /c/Users/Dorsay/Desktop/unturnedplugıns/gitwhy
python tests/test_rules.py
```

**You will see** the 13x13 confusion matrix, ending:

```
12 scenarios, 18 fixtures, 18/18 correct (100%)
```

**Say:**

> Every scenario is measured. For each one we build a real repository, put it
> into that broken state, and check what the engine predicts. Twelve scenarios,
> eighteen fixtures, a hundred percent. The last row is three healthy
> repositories — those must match nothing, and they do. A tool like this is
> judged by its false positives, not its coverage, which is why the negative
> controls are in the same number. This runs on every pull request, on Linux
> and Windows.

**Then cut to** the green GitHub Actions check for two seconds.

---

## Take 6 — 1:50–2:08 — safety, guaranteed by a test

**Type:**

```bash
python -m pytest tests/test_safety.py tests/test_ai.py -q
```

Green, 18 tests across the two files. `test_safety.py` is 7 of them, up from 5:
two were added after a crash found while rehearsing this video, and they are
worth a clause if you have room:

> and two of these exist because rehearsing this video found gitwhy crashing on
> a Windows console that could not print one of its own characters.

**Say:**

> The tool suggests commands that can destroy work, so the safety rules are
> tests, not promises. Every template containing a destructive command must
> carry a warning that says what it deletes. The context collector is checked to
> contain no git command that writes. And the optional AI mode cannot sneak one
> in: it rewrites the wording, it never picks the scenario, and if the model adds
> `git reset --hard` or waters a warning down, the answer is thrown away and you
> get the template.

---

## Take 7 — 2:08–2:20 — close

**Screen:**

```bash
pipx install git+https://github.com/Sanixaa23/gitwhy
cd ~/gitwhy-video/03-secret
gitwhy doctor
```

**Run `doctor` in repo 3, not in the gitwhy checkout.** Two reasons, and the
second one matters more.

It is the better demo: repo 3 reports `remote: none`, `.gitignore: MISSING` and
`staged secrets: .env` — three real findings in one frame. The gitwhy checkout
reports a clean repository with one unstaged file, which shows nothing.

And `doctor` prints `user.email`. In repo 3 that is `student@school.edu`, which
`video_setup.py` set deliberately. In your own checkout it is your real address,
and this video is going on a public submission page. Recording the checkout puts
your email on screen in a file you cannot edit afterwards. Use repo 3.

**Say:**

> One line to install, no dependencies, works offline, no account. Twelve
> scenarios — and we tell you exactly which twelve.

---

## Rules while recording

- **Never say "AI-powered".** The whole argument is that the decision is not an
  LLM.
- **Do not fake a terminal.** If a take goes wrong, `--reset` and run it again
  rather than editing the frame.
- **Do not read the screen aloud.** The viewer can read. Say what it means.
- **Reset between takes.** Each take consumes the state it demonstrates.
- **Total 2:20.** The two-minute minimum is a submission requirement and five
  minutes is the ceiling. If a take runs long, that is fine. Do not trim below
  2:00 to tighten pacing — if a segment drags, say less over it.
- **If you must cut**, cut take 3. It is the most memorable segment, but takes 5
  and 6 are the two nobody else can show, and take 4 is the Technical Excellence
  criterion in twenty-five seconds.
