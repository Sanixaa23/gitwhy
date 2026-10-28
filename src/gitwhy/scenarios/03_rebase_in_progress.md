## What happened

A rebase stopped halfway. Git was moving your commits one by one onto a new base and got
stuck on one of them. While this lasts you appear to be on no branch — `git status` says
"detached", but that is not the real problem; the unfinished rebase is.

## Where you are

- Repository: `{{repo}}`
- Operation in progress: {{in_progress}}
- Conflicted files ({{conflicted_count}}): {{conflicted}}
- HEAD: `{{short_oid}}`

## What to do

To finish the rebase: fix the conflicted files, then

    git add .
    git rebase --continue

To skip this one commit:

    git rebase --skip

To undo the whole rebase and go back where you started:

    git rebase --abort

> WARNING: `git rebase --skip` drops the changes of the commit it skips, and
> `git rebase --abort` PERMANENTLY deletes the conflict fixes you made during the
> rebase. Neither can be undone. gitwhy never runs these for you.
