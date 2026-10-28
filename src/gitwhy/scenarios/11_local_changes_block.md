## What happened

You have uncommitted changes, and the operation you asked for would have written over
those files. Git did not do it — so you have lost nothing. This is a guard, not a
failure: git refuses to silently discard work you have not saved.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Uncommitted changes ({{unstaged_count}}): {{unstaged}}
- Staged files: {{staged_count}}

## What to do

Pick one of three paths.

If the changes are worth keeping, commit them, then retry the operation:

    git add {{first_unstaged}}
    git commit -m "work in progress"

If you do not want to commit yet, set them aside and bring them back afterwards:

    git stash push -m "before switching branches"
    git stash pop

If you want to see what changed first:

    git diff {{first_unstaged}}

> WARNING: the third path would be to throw the changes away (`git checkout -- <file>`
> or `git restore <file>`). That returns the file to its last committed state and
> PERMANENTLY deletes your uncommitted work — there is no way back unless you stashed it.
> gitwhy never runs this for you, and does not suggest it while `git stash push` exists.
