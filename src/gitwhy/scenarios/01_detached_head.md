## What happened

You are not on any branch. Git calls this "detached HEAD": you are looking straight at
commit `{{short_oid}}`. Commits you make from here belong to no branch, and once you
switch away they are hard to find again.

## Where you are

- Repository: `{{repo}}`
- HEAD: `{{short_oid}}` — not attached to a branch
- Last commit: {{last_subject}}
- Staged files: {{staged_count}}

## What to do

If you did work here, give it a branch first:

    git switch -c rescue-{{short_oid}}

If you changed nothing and just want to go back:

    git switch -

> WARNING: git blocks `git switch -` when you have uncommitted changes. Forcing past
> that with `--discard-changes` deletes every uncommitted change PERMANENTLY. gitwhy
> never runs this for you; the call is yours.
