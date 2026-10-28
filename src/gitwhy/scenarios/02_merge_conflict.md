## What happened

Two sides changed the same lines differently, so git could not finish the merge. It
stopped halfway: the conflicting files now contain `<<<<<<<`, `=======` and `>>>>>>>`
markers, and you have to decide which side stays.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Conflicted files ({{conflicted_count}}): {{conflicted}}
- Operation in progress: {{in_progress}}

## What to do

Open each conflicted file, fix the marked blocks by hand, delete the marker lines. Then:

    git add {{first_conflicted}}
    git commit

To see which files are still conflicted:

    git diff --name-only --diff-filter=U

If you want to give up on the merge entirely:

    git merge --abort

> WARNING: `git merge --abort` undoes the merge and PERMANENTLY deletes the conflict
> fixes you made by hand after the merge started. gitwhy never runs this for you.
