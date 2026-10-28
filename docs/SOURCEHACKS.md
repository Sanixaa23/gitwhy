# SourceHacks V1 — the verified rules

Read from the official Devpost listing on 2026-10-28:
<https://sourcehacksv1.devpost.com/> (site: <https://sourcehacks.xyz/>).
Everything below is quoted or paraphrased from that page, not from an
aggregator. Earlier planning notes in `../fikirler.md` and
`../fikir5-plan.md` were based on a secondary source; where they disagree
with this file, this file is right.

## Event

- **Dates:** Dec 11–12, 2026. 24 hours, online.
- **Theme:** none. "Build anything, from AI applications and developer tools
  to mobile apps, games, hardware, or startup ideas."
- **Tracks:** there are none. Do not plan around a developer-tools or
  education track; the only awards are 1st, 2nd and 3rd overall.

## Prizes

| Place | Award |
|---|---|
| 1st | $250 USD cash, split among the team, plus the title SourceHacks Champion |
| 2nd | Honorable Mention certificate |
| 3rd | Honorable Mention certificate |

1st place is "awarded to the team that demonstrates the strongest combination
of innovation, technical excellence, impact, and presentation" — four of the
five criteria named explicitly, with Design & UX the one left out of that
sentence.

## Judging criteria

Five, unweighted as far as the listing says:

1. **Innovation** — originality, technical ambition, and how effectively the
   solution stands out from existing alternatives.
2. **Technical Excellence** — code quality, technical difficulty, effective
   use of technologies and APIs; "thoughtful architecture".
3. **Impact** — significance of the problem, potential reach, overall
   usefulness.
4. **Design & User Experience** — "intuitive, polished, and enjoyable to
   use": interface design, usability, accessibility, the overall user journey.
5. **Presentation & Execution** — demo quality, storytelling, and the team's
   ability to answer questions.

## Submission requirements

All four are mandatory before the deadline:

- A completed Devpost submission.
- A GitHub repository.
- A project description explaining what you built and why.
- **A demo video between two and five minutes long.**

Live link if deployed. Installation instructions and documentation
encouraged "if judges need them to run your project".

## Two rules that change our plans

**1. The video must be at least two minutes.** The shot list was written for
90 seconds, which would have been rejected as incomplete. `VIDEO.md` is now a
2:20 cut. Do not trim it back under 2:00 to tighten the pacing.

**2. "Your project should be built primarily during the 24-hour event."**
The full sentence: "You are welcome to use existing frameworks, APIs,
libraries, and open source software, but the main idea and implementation
should be completed during SourceHacks." AI use is explicitly allowed.

gitwhy as it stands was built before the event. Submitting this repository
as-is does not satisfy that rule. The honest options:

- **Rebuild during the event.** Everything here then counts as what it is:
  research. The 12 scenarios, the fixture method, the eight findings and the
  ordering rule are knowledge, not code you are reusing — and knowing the
  design in advance is exactly what makes a 24-hour build of this size
  possible. Start from an empty repository on Dec 11.
- **Submit it to a hackathon with no such rule,** or to one that accepts
  existing projects. Many do; this listing does not.

Decide before Dec 11, not after. A judge who checks the commit dates on a
public repository will find them, and the repository is public.
