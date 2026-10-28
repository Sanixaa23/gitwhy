## What happened

A `git {{in_progress_command}}` stopped halfway. Git tried to bring one commit's changes
over here, but the same lines had changed on this side too, so it could not decide and
stopped. Git's first line is `error: could not apply`; the useful information is in the
`CONFLICT` line further down.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Operation in progress: {{in_progress}}
- Conflicted files ({{conflicted_count}}): {{conflicted}}

## What to do

Open the conflicted files, decide which of the two versions between `<<<<<<<` and
`>>>>>>>` stays, delete the marker lines. Then:

    git add {{first_conflicted}}
    git {{in_progress_command}} --continue

If you changed your mind about this commit, skip just it:

    git {{in_progress_command}} --skip

To abandon the operation and return to where you started:

    git {{in_progress_command}} --abort

To see where you stand:

    git status --short

> WARNING: `git {{in_progress_command}} --abort` undoes the operation and PERMANENTLY
> deletes the conflict fixes you made by hand. `--skip` means you never take that
> commit's changes at all. gitwhy never runs these for you.
