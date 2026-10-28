## What happened

The reflog holds {{lost_count}} commit(s) that no branch can reach. They are still inside
git, but no branch points at them, so they do not show up in `git log`. This usually
follows a `git reset --hard` or a deleted branch.

**The commits are not deleted.** Git keeps unreachable objects for a while (90 days by
default), and within that window they can be recovered.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Unreachable commits:

{{lost_list}}

Only the last 10 reflog entries are examined, so a commit dropped months ago will not
appear here. `gitwhy doctor` and `git reflog` show the full list.

## What to do

Look at the contents first and make sure it is the right commit:

    git show {{first_lost_sha}}

The safest way to get your work back is to give that commit a new branch. It leaves the
branch you are on untouched:

    git switch -c rescue-{{first_lost_sha}} {{first_lost_sha}}

If you only want that commit's changes on your current branch:

    git cherry-pick {{first_lost_sha}}

If these commits really are unwanted, do nothing; git cleans them up in time.

> WARNING: `git gc --prune=now` and `git reflog expire --expire=now --all` delete
> unreachable commits without waiting; past that point there is no way back and the work
> is PERMANENTLY gone. Do not run them while something here is worth recovering. gitwhy
> never runs either for you.
