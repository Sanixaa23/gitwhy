## What happened

The remote `{{upstream}}` branch has commits you do not have. Your commit does not sit
directly on top of theirs, so git refused to send it. Usually this means a teammate
pushed to the same branch before you did.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}` → `{{upstream}}`
- Waiting to be sent: {{ahead}} commit(s)
- Behind: {{behind}} commit(s)

> That "behind" count reads **0** right after a rejected push: git does not update the
> remote-tracking ref when a push is rejected. The real number only appears after
> `git fetch`. gitwhy does not run fetch, so it decides from the error text instead.

## What to do

Take their work on top of yours first, then send:

    git pull --rebase {{first_remote}} {{branch}}
    git push

`--rebase` moves your commits on top of theirs, with no pointless merge commit. If a
conflict comes up during this, run `gitwhy` again: scenario 2 takes over.

If you want to see what happened first:

    git fetch {{first_remote}}
    git log --oneline --graph HEAD...{{upstream}}

> WARNING: `git push --force` silences this error but PERMANENTLY deletes the remote's
> commits — your teammate's work disappears. gitwhy never runs this for you and does not
> suggest it on a shared branch.
